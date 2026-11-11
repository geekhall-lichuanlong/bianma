from rest_framework.permissions import AllowAny, IsAuthenticated
# Create your views here.
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
import json
from .models import PDFOCRData, UserProfile
import os
import uuid


def index(request):
    return JsonResponse({"code": 200, "msg": "ok"})


def _get_body_data(request):
    """Return dict from form or JSON body."""
    if hasattr(request, "data") and isinstance(request.data, dict):
        return request.data
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.POST:
            return request.POST
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return {}
    return {}


def _get_authenticated_user(request):
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        return request.user
    try:
        authenticator = JWTAuthentication()
        header = authenticator.get_header(request)
        if header is None:
            return None
        raw_token = authenticator.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = authenticator.get_validated_token(raw_token)
        return authenticator.get_user(validated_token)
    except Exception:
        return None


def _auth_required_response(request):
    user = _get_authenticated_user(request)
    if user is None:
        return JsonResponse({"code": 401, "msg": "unauthenticated"}, status=401)
    request.user = user
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
    return max(page, 1), min(max(page_size, 1), max_size)


@csrf_exempt
def register(request):
    return JsonResponse({"code": 405, "msg": "暂时不支持注册"}, status=405)
    
    if request.method != "POST":
        return JsonResponse({"code": 405, "msg": "Method Not Allowed"}, status=405)

    data = _get_body_data(request)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password2") or data.get("confirmPassword") or None
    email = (data.get("email") or "").strip()

    if not username or not password or not email:
        return JsonResponse({"code": 400, "msg": "username, password and email are required"}, status=400)

    if password2 is not None and password != password2:
        return JsonResponse({"code": 400, "msg": "passwords do not match"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"code": 409, "msg": "username already exists"}, status=409)

    user = User.objects.create_user(username=username, password=password, email=email)
    return JsonResponse({"code": 200, "msg": "registered", "data": {"username": user.username, "email": user.email}})


# @csrf_exempt
@api_view(['POST']) # 使用 DRF 的装饰器，不再需要 @csrf_exempt
@permission_classes([AllowAny]) # 登录接口允许任何人访问
def login_view(request):
    # if request.method != "POST":
    #     return JsonResponse({"code": 405, "msg": "Method Not Allowed"}, status=405)

    # # DRF 会自动处理 json 解析，数据在 request.data 中
    # data = _get_body_data(request)
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""

    if not username or not password:
        return JsonResponse({"code": 400, "msg": "username and password are required"}, status=400)

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({"code": 401, "msg": "invalid credentials"}, status=401)

    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_ADMIN if user.is_superuser else UserProfile.ROLE_USER,
        )

    if not user.is_active or profile.status != UserProfile.STATUS_ENABLED:
        return JsonResponse({"code": 403, "msg": "user disabled"}, status=403)

    refresh = RefreshToken.for_user(user)

    auth_login(request, user)
    return JsonResponse({
        "code": 200,
        "msg": "logged in",
        "data": {
            "username": user.username,
            "id": user.id,
            "role": profile.role,
            "status": profile.status,
            "access_token": str(refresh.access_token),
    }})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    auth_logout(request)
    return JsonResponse({"code": 200, "msg": "logged out"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user,
            role=UserProfile.ROLE_ADMIN if request.user.is_superuser else UserProfile.ROLE_USER,
        )
    return JsonResponse({
        "code": 200,
        "data": {
            "id": request.user.id,
            "username": request.user.username,
            "role": profile.role,
            "status": profile.status,
        },
    })


# ------------ PDF OCR Data CRUD ------------

def _ocr_to_dict(obj: PDFOCRData):
    return {
        "id": obj.id,
        "filename": obj.filename,
        "file_path": obj.file_path,
        "raw_text": obj.raw_text,
        "personal_history": obj.personal_history,
        "chief_complaint": obj.chief_complaint,
        "inpatient_no": obj.inpatient_no,
        "admission_status": obj.admission_status,
        "admission_diagnosis": obj.admission_diagnosis,
        "discharge_diagnosis": obj.discharge_diagnosis,
        "marital_history": obj.marital_history,
        "family_history": obj.family_history,
        "imaging_opinion": obj.imaging_opinion,
        "operation_name": obj.operation_name,
        "operation_course": obj.operation_course,
        "past_history": obj.past_history,
        "intraoperative_diagnosis": obj.intraoperative_diagnosis,
        "present_illness": obj.present_illness,
        "case_identifier": obj.case_identifier,
        "course_record": obj.course_record,
        "treatment_course": obj.treatment_course,
        "ultrasound_impression": obj.ultrasound_impression,
        "ultrasound_hint": obj.ultrasound_hint,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
    }

OCR_MUTABLE_FIELDS = [
    "filename",
    "file_path",
    "raw_text",
    "personal_history",
    "chief_complaint",
    "inpatient_no",
    "admission_status",
    "admission_diagnosis",
    "discharge_diagnosis",
    "marital_history",
    "family_history",
    "imaging_opinion",
    "operation_name",
    "operation_course",
    "past_history",
    "intraoperative_diagnosis",
    "present_illness",
    "case_identifier",
    "course_record",
    "treatment_course",
    "ultrasound_impression",
    "ultrasound_hint",
]


@csrf_exempt
def ocr_records(request):
    """GET: list with pagination and optional search; POST: create a record."""
    denied = _auth_required_response(request)
    if denied:
        return denied

    if request.method == "GET":
        qs = PDFOCRData.objects.all().order_by("-created_at")
        # optional query params
        keyword = request.GET.get("q")
        if keyword:
            qs = qs.filter(filename__icontains=keyword)

        page, page_size = _parse_page_params(request)
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        data = [_ocr_to_dict(x) for x in qs[start:end]]
        return JsonResponse({"code": 200, "data": {"items": data, "total": total, "page": page, "page_size": page_size}})

    if request.method == "POST":
        data = _get_body_data(request)

        # handle optional file upload
        uploaded = request.FILES.get("file") if hasattr(request, "FILES") else None
        saved_media_url = None
        if uploaded:
            # ensure media/uploads exists
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            ext = os.path.splitext(uploaded.name)[1]
            safe_name = f"{uuid.uuid4().hex}{ext}"
            dest_path = os.path.join(upload_dir, safe_name)
            with open(dest_path, "wb+") as dest:
                for chunk in uploaded.chunks():
                    dest.write(chunk)
            # url path for client
            saved_media_url = f"{settings.MEDIA_URL}uploads/{safe_name}"

        # basic required fields
        filename = (data.get("filename") or "").strip()
        if not filename and uploaded:
            filename = uploaded.name
        if not filename:
            return JsonResponse({"code": 400, "msg": "filename is required"}, status=400)

        obj = PDFOCRData()
        # assign mutable fields from data
        for field in OCR_MUTABLE_FIELDS:
            if field in data:
                setattr(obj, field, data.get(field))
        # override file_path if we actually saved a file
        if saved_media_url:
            obj.file_path = saved_media_url
        obj.filename = filename
        obj.save()
        return JsonResponse({"code": 200, "msg": "created", "data": _ocr_to_dict(obj)})

    return JsonResponse({"code": 405, "msg": "Method Not Allowed"}, status=405)


@csrf_exempt
def ocr_record_detail(request, pk: int):
    """GET: retrieve; PUT/PATCH: update; DELETE: delete."""
    denied = _auth_required_response(request)
    if denied:
        return denied

    try:
        obj = PDFOCRData.objects.get(pk=pk)
    except PDFOCRData.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({"code": 200, "data": _ocr_to_dict(obj)})

    if request.method in ("PUT", "PATCH"):
        data = _get_body_data(request)
        for field in OCR_MUTABLE_FIELDS:
            if field in data:
                setattr(obj, field, data.get(field))
        obj.save()
        return JsonResponse({"code": 200, "msg": "updated", "data": _ocr_to_dict(obj)})

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"code": 200, "msg": "deleted"})

    return JsonResponse({"code": 405, "msg": "Method Not Allowed"}, status=405)
