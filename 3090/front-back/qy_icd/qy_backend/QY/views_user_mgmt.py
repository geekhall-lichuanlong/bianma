import os
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import UserProfile


def index(request):
    return JsonResponse({"code": 200, "msg": "ok"})


def _get_body_data(request):
    if hasattr(request, "data"):
        data = request.data
        return data if isinstance(data, dict) else {}
    return {}


def _get_user_profile(user: User) -> UserProfile:
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created and user.is_superuser and profile.role != UserProfile.ROLE_ADMIN:
        profile.role = UserProfile.ROLE_ADMIN
        profile.save(update_fields=["role"])
    return profile


def _is_admin(user: User) -> bool:
    try:
        return user.is_authenticated and user.profile.role == UserProfile.ROLE_ADMIN
    except UserProfile.DoesNotExist:
        return False


def _admin_required(request):
    if not _is_admin(request.user):
        return JsonResponse({"code": 403, "msg": "permission denied"}, status=403)
    return None


def _parse_page_params(request, default_size=10, max_size=100):
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page = max(page, 1)
    page_size = min(max(page_size, 1), max_size)
    return page, page_size


def _enabled_admin_count():
    return UserProfile.objects.filter(
        role=UserProfile.ROLE_ADMIN,
        status=UserProfile.STATUS_ENABLED,
        user__is_active=True,
    ).count()


def _user_to_dict(user: User):
    profile = _get_user_profile(user)
    return {
        "id": user.id,
        "username": user.username,
        "realName": profile.real_name or "",
        "role": profile.role,
        "phone": profile.phone or "",
        "createTime": profile.created_at.isoformat() if profile.created_at else None,
        "status": profile.status,
    }


def _validate_phone(phone):
    return not phone or phone.isdigit()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    profile = _get_user_profile(request.user)
    return JsonResponse({
        "code": 200,
        "data": {
            "id": request.user.id,
            "username": request.user.username,
            "role": profile.role,
            "status": profile.status,
        },
    })


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def user_list_create(request):
    denied = _admin_required(request)
    if denied:
        return denied

    if request.method == "GET":
        qs = User.objects.select_related("profile").order_by("id")
        page, page_size = _parse_page_params(request)
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        users = [_user_to_dict(u) for u in qs[start:end]]
        return JsonResponse({
            "code": 200,
            "data": {
                "userList": users,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        })

    data = _get_body_data(request)
    username = (data.get("username") or "").strip()
    real_name = (data.get("realName") or "").strip()
    phone = (data.get("phone") or "").strip()
    role = data.get("role")
    password = data.get("password") or ""
    confirm_password = data.get("confirmPassword") or ""

    if not username or not real_name or role is None:
        return JsonResponse({"code": 400, "msg": "username, realName and role are required"}, status=400)

    try:
        role = int(role)
    except (TypeError, ValueError):
        return JsonResponse({"code": 400, "msg": "role must be 0 or 1"}, status=400)

    if role not in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_USER):
        return JsonResponse({"code": 400, "msg": "role must be 0 or 1"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"code": 409, "msg": "username already exists"}, status=409)

    if password or confirm_password:
        if password != confirm_password:
            return JsonResponse({"code": 400, "msg": "passwords do not match"}, status=400)
    else:
        password = os.environ.get('SERVICE_PASSWORD', "")

    if not _validate_phone(phone):
        return JsonResponse({"code": 400, "msg": "phone must be digits only"}, status=400)

    with transaction.atomic():
        user = User.objects.create_user(username=username, password=password)
        profile = _get_user_profile(user)
        profile.real_name = real_name
        profile.phone = phone
        profile.role = role
        profile.status = UserProfile.STATUS_ENABLED
        profile.save()

    return JsonResponse({"code": 200, "msg": "User created successfully!", "data": _user_to_dict(user)})


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def user_edit(request, pk: int):
    denied = _admin_required(request)
    if denied:
        return denied

    try:
        user = User.objects.select_related("profile").get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "User not found."}, status=404)

    data = _get_body_data(request)
    username = (data.get("username") or user.username).strip()
    real_name = data.get("realName")
    phone = (data.get("phone") or "").strip()
    role = data.get("role")

    if not username:
        return JsonResponse({"code": 400, "msg": "username is required"}, status=400)

    if username != user.username and User.objects.filter(username=username).exists():
        return JsonResponse({"code": 409, "msg": "username already exists"}, status=409)

    if not _validate_phone(phone):
        return JsonResponse({"code": 400, "msg": "phone must be digits only"}, status=400)

    profile = _get_user_profile(user)
    if role is not None:
        try:
            role = int(role)
        except (TypeError, ValueError):
            return JsonResponse({"code": 400, "msg": "role must be 0 or 1"}, status=400)
        if role not in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_USER):
            return JsonResponse({"code": 400, "msg": "role must be 0 or 1"}, status=400)
        if (
            profile.role == UserProfile.ROLE_ADMIN
            and role != UserProfile.ROLE_ADMIN
            and _enabled_admin_count() <= 1
        ):
            return JsonResponse({"code": 400, "msg": "at least one enabled admin is required"}, status=400)
        profile.role = role

    user.username = username
    user.save(update_fields=["username"])

    if real_name is not None:
        profile.real_name = str(real_name).strip()
    profile.phone = phone
    profile.save()

    return JsonResponse({"code": 200, "msg": "User updated successfully!", "data": _user_to_dict(user)})


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def user_status_edit(request, pk: int):
    denied = _admin_required(request)
    if denied:
        return denied

    try:
        user = User.objects.select_related("profile").get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "user not found"}, status=404)

    data = _get_body_data(request)
    status_val = data.get("status")
    if status_val is None:
        return JsonResponse({"code": 400, "msg": "status is required"}, status=400)

    try:
        status_val = int(status_val)
    except (TypeError, ValueError):
        return JsonResponse({"code": 400, "msg": "status must be 0 or 1"}, status=400)

    if status_val not in (UserProfile.STATUS_DISABLED, UserProfile.STATUS_ENABLED):
        return JsonResponse({"code": 400, "msg": "status must be 0 or 1"}, status=400)

    profile = _get_user_profile(user)
    if (
        profile.role == UserProfile.ROLE_ADMIN
        and status_val == UserProfile.STATUS_DISABLED
        and _enabled_admin_count() <= 1
    ):
        return JsonResponse({"code": 400, "msg": "at least one enabled admin is required"}, status=400)

    profile.status = status_val
    profile.save(update_fields=["status"])
    user.is_active = status_val == UserProfile.STATUS_ENABLED
    user.save(update_fields=["is_active"])
    return JsonResponse({"code": 200, "msg": "User status updated successfully!", "data": _user_to_dict(user)})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def user_delete(request, pk: int):
    denied = _admin_required(request)
    if denied:
        return denied

    try:
        user = User.objects.select_related("profile").get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "user not found"}, status=404)

    if user.pk == request.user.pk:
        return JsonResponse({"code": 400, "msg": "cannot delete current user"}, status=400)

    profile = _get_user_profile(user)
    if profile.role == UserProfile.ROLE_ADMIN and _enabled_admin_count() <= 1:
        return JsonResponse({"code": 400, "msg": "at least one enabled admin is required"}, status=400)

    user.delete()
    return JsonResponse({"code": 200, "msg": "User deleted successfully!"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get("oldPassword")
    new_password = request.data.get("newPassword")
    confirm_password = request.data.get("confirmPassword")

    if not all([old_password, new_password, confirm_password]):
        return JsonResponse({"code": 400, "msg": "oldPassword, newPassword and confirmPassword are required"}, status=400)

    if not user.check_password(old_password):
        return JsonResponse({"code": 400, "msg": "old password is incorrect"}, status=400)

    if new_password != confirm_password:
        return JsonResponse({"code": 400, "msg": "passwords do not match"}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)

    return JsonResponse({"code": 200, "msg": "User password changed successfully!"})
