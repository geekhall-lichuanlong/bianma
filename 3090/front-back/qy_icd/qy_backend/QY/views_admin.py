# -*- coding: utf-8 -*-
"""病案编码管理后台 —— 接口实现（一期）

挂载点：``/qy/admin/...``（前端经 Vite 代理访问 ``/api/qy/admin/...``）
鉴权：JWT（复用既有 rest_framework_simplejwt）+ 角色二次校验。
"""

import json
from datetime import date, datetime, timedelta
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import UserProfile
from .models_admin import (
    BACKEND_ROLES,
    ROLE_ADMIN,
    ROLE_LABELS,
    ROLE_LEADER,
    AccuracyReview,
    CaseAssignment,
    CaseLog,
    CodingVersion,
    Department,
    DifficultCase,
    Expert,
    RotationConfig,
)

# ==========================================================================
# 通用工具
# ==========================================================================

STATUS_LABELS = dict(DifficultCase.STATUS_CHOICES)
SEQ_LABELS = dict(AccuracyReview.SEQ_CHOICES)
PERIOD_LABELS = {"year": "按年", "quarter": "按季度", "month": "按月", "week": "按周"}


def _ok(data=None, msg="ok"):
    return JsonResponse({"code": 200, "msg": msg, "data": data})


def _err(msg, code=400, http_status=None):
    return JsonResponse({"code": code, "msg": msg}, status=http_status or code)


def _body(request):
    if hasattr(request, "data"):
        data = request.data
        return data if isinstance(data, dict) else {}
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _role_of(user):
    try:
        return user.profile.role
    except Exception:
        return None


def _role_name(user):
    if getattr(user, "is_superuser", False):
        return "超级管理员"
    role = _role_of(user)
    return ROLE_LABELS.get(role, "普通用户")


def _require_backend(request):
    """后台访问权：系统管理员 / 编码组长（或 Django 超管）"""
    if getattr(request.user, "is_superuser", False):
        return None
    if _role_of(request.user) in BACKEND_ROLES:
        return None
    return _err("permission denied", 403, 403)


def _require_super_admin(request):
    """配置类写操作：仅系统管理员"""
    if getattr(request.user, "is_superuser", False):
        return None
    if _role_of(request.user) == ROLE_ADMIN:
        return None
    return _err("permission denied", 403, 403)


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


def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value)[:19], fmt).date()
        except ValueError:
            continue
    return None


def _split_tags(raw):
    return [t.strip() for t in str(raw or "").replace("，", ",").replace(";", ",").split(",") if t.strip()]


def _mask_name(name):
    """姓名脱敏：张三 → 张*；欧阳娜娜 → 欧***"""
    if not name:
        return ""
    name = name.strip()
    if len(name) <= 1:
        return name
    return name[0] + "*" * (len(name) - 1)


def _log(case, actor, action, detail=""):
    actor = actor if isinstance(actor, User) else None
    CaseLog.objects.create(
        case=case,
        actor=actor,
        actor_name=(getattr(actor, "profile", None) and actor.profile.real_name) or getattr(actor, "username", "") or "系统",
        action=action,
        detail=detail or "",
    )


def _fmt_dt(dt):
    return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None


def _fmt_d(d):
    return d.strftime("%Y-%m-%d") if d else None


# ==========================================================================
# 元信息
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_me(request):
    role = _role_of(request.user)
    is_backend = getattr(request.user, "is_superuser", False) or role in BACKEND_ROLES
    return _ok(
        {
            "id": request.user.id,
            "username": request.user.username,
            "realName": (getattr(request.user, "profile", None) and request.user.profile.real_name) or "",
            "role": role,
            "roleName": _role_name(request.user),
            "isBackend": bool(is_backend),
            "permissions": {
                "canManageRotation": getattr(request.user, "is_superuser", False) or role == ROLE_ADMIN,
                "canExport": bool(is_backend),
                "canAssign": bool(is_backend),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def department_list(request):
    guard = _require_backend(request)
    if guard:
        return guard
    names = list(Department.objects.filter(is_active=True).values_list("name", flat=True))
    extra = set()
    extra.update(x for x in AccuracyReview.objects.values_list("dept", flat=True).distinct() if x)
    extra.update(x for x in DifficultCase.objects.values_list("dept", flat=True).distinct() if x)
    merged = sorted(set(names) | extra)
    return _ok({"list": [{"name": n, "fromDict": n in names} for n in merged]})


# ==========================================================================
# 一、版本迭代
# ==========================================================================
def _version_to_dict(v, stats=None):
    return {
        "id": v.id,
        "versionNo": v.version_no,
        "versionType": v.version_type,
        "versionTypeName": v.get_version_type_display(),
        "releaseDate": _fmt_d(v.release_date),
        "modelName": v.model_name or "",
        "remark": v.remark or "",
        "isActive": v.is_active,
        "createdAt": _fmt_dt(v.created_at),
        "stats": stats or {},
    }


def _version_stats(version_ids):
    rows = (
        AccuracyReview.objects.filter(version_id__in=version_ids)
        .values("version_id", "sequence")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
    )
    result = {}
    for r in rows:
        bucket = result.setdefault(r["version_id"], {})
        bucket[r["sequence"]] = {
            "total": r["total"],
            "correct": r["correct"],
            "rate": round(r["correct"] * 100.0 / r["total"], 2) if r["total"] else 0.0,
        }
    return result


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def versions(request):
    guard = _require_backend(request)
    if guard:
        return guard

    if request.method == "GET":
        vtype = request.GET.get("type")
        qs = CodingVersion.objects.all()
        if vtype:
            qs = qs.filter(version_type=vtype)
        items = list(qs.order_by("release_date", "id"))
        stats = _version_stats([v.id for v in items])
        data = [_version_to_dict(v, stats.get(v.id, {})) for v in items]
        return _ok({"list": data, "total": len(data)})

    # POST 登记版本（管理员/组长均可登记）
    body = _body(request)
    version_no = (body.get("versionNo") or "").strip()
    version_type = body.get("versionType") or CodingVersion.TYPE_DISEASE
    release_date = _to_date(body.get("releaseDate")) or timezone.localdate()
    if not version_no:
        return _err("版本号不能为空", 400, 400)
    if version_type not in dict(CodingVersion.TYPE_CHOICES):
        return _err("版本类型不合法", 400, 400)
    if CodingVersion.objects.filter(version_no=version_no, version_type=version_type).exists():
        return _err("该版本号已存在", 409, 409)
    v = CodingVersion.objects.create(
        version_no=version_no,
        version_type=version_type,
        release_date=release_date,
        model_name=(body.get("modelName") or "").strip() or None,
        remark=(body.get("remark") or "").strip() or None,
    )
    return _ok(_version_to_dict(v), "版本登记成功")


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def version_detail(request, pk):
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        v = CodingVersion.objects.get(pk=pk)
    except CodingVersion.DoesNotExist:
        return _err("版本不存在", 404, 404)

    if request.method == "DELETE":
        guard = _require_super_admin(request)
        if guard:
            return guard
        v.delete()
        return _ok(msg="版本已删除")

    body = _body(request)
    if "versionNo" in body and (body.get("versionNo") or "").strip():
        v.version_no = body["versionNo"].strip()
    if "releaseDate" in body:
        d = _to_date(body.get("releaseDate"))
        if d:
            v.release_date = d
    if "modelName" in body:
        v.model_name = (body.get("modelName") or "").strip() or None
    if "remark" in body:
        v.remark = (body.get("remark") or "").strip() or None
    if "isActive" in body:
        v.is_active = bool(body.get("isActive"))
    v.save()
    return _ok(_version_to_dict(v), "版本已更新")


def _bucket_key_and_label(d, period):
    if period == "quarter":
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}", f"{d.year}Q{q}", f"{d.year} 年 Q{q}"
    if period == "month":
        return f"{d.year}-{d.month:02d}", f"{d.year}-{d.month:02d}", f"{d.year} 年 {d.month} 月"
    if period == "week":
        iso = d.isocalendar()
        return (
            f"{iso[0]}-W{iso[1]:02d}",
            f"{iso[0]}-W{iso[1]:02d}",
            f"{iso[0]} 年第 {iso[1]} 周",
        )
    return f"{d.year}", str(d.year), f"{d.year} 年"


def _build_trend(vtype, period, dept):
    versions_qs = CodingVersion.objects.filter(version_type=vtype, is_active=True).order_by("release_date", "id")
    versions = list(versions_qs)
    if not versions:
        return {
            "points": [],
            "summary": {"model": {"total": 0, "correct": 0, "rate": 0.0}, "doctor": {"total": 0, "correct": 0, "rate": 0.0}},
            "pointCount": 0,
        }

    review_qs = AccuracyReview.objects.filter(version__in=versions)
    if dept:
        review_qs = review_qs.filter(dept=dept)

    rows = (
        review_qs.values("version_id", "sequence")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
    )
    per_version = {}
    for r in rows:
        per_version.setdefault(r["version_id"], {})[r["sequence"]] = r

    version_map = {v.id: v for v in versions}

    def _series(seq, stats):
        row = stats.get(seq)
        total = row["total"] if row else 0
        correct = row["correct"] if row else 0
        return {
            "total": total,
            "correct": correct,
            "rate": round(correct * 100.0 / total, 2) if total else None,
        }

    points = []
    if period == "year":
        # 按年视图：逐版本展开（对应“按年展示全部版本”）
        for v in versions:
            stats = per_version.get(v.id, {})
            points.append(
                {
                    "key": str(v.id),
                    "label": v.version_no,
                    "axisLabel": v.version_no,
                    "versionNo": v.version_no,
                    "versionCount": 1,
                    "releaseDate": _fmt_d(v.release_date),
                    "model": _series(AccuracyReview.SEQ_MODEL, stats),
                    "doctor": _series(AccuracyReview.SEQ_DOCTOR, stats),
                }
            )
    else:
        # 周/月/季度视图：周期内多版本聚合为一个数据点
        buckets = {}
        for v in versions:
            key, axis, name = _bucket_key_and_label(v.release_date, period)
            b = buckets.setdefault(
                key, {"axis": axis, "name": name, "versions": [], "model": {"total": 0, "correct": 0}, "doctor": {"total": 0, "correct": 0}}
            )
            b["versions"].append(v)
            stats = per_version.get(v.id, {})
            for seq in (AccuracyReview.SEQ_MODEL, AccuracyReview.SEQ_DOCTOR):
                row = stats.get(seq)
                if row:
                    b[seq]["total"] += row["total"]
                    b[seq]["correct"] += row["correct"]
        ordered = [buckets[k] for k in sorted(buckets.keys())]
        ordered = ordered[-12:]  # 最多展示最近 12 个周期
        for b in ordered:
            last_v = sorted(b["versions"], key=lambda x: (x.release_date, x.id))[-1]
            points.append(
                {
                    "key": b["axis"],
                    "label": b["name"],
                    "axisLabel": b["axis"],
                    "versionNo": last_v.version_no,
                    "versionCount": len(b["versions"]),
                    "releaseDate": _fmt_d(last_v.release_date),
                    "model": {
                        "total": b["model"]["total"],
                        "correct": b["model"]["correct"],
                        "rate": round(b["model"]["correct"] * 100.0 / b["model"]["total"], 2) if b["model"]["total"] else None,
                    },
                    "doctor": {
                        "total": b["doctor"]["total"],
                        "correct": b["doctor"]["correct"],
                        "rate": round(b["doctor"]["correct"] * 100.0 / b["doctor"]["total"], 2) if b["doctor"]["total"] else None,
                    },
                }
            )

    # 汇总（加权平均）
    summary = {}
    for seq in (AccuracyReview.SEQ_MODEL, AccuracyReview.SEQ_DOCTOR):
        total = sum(p[seq]["total"] for p in points)
        correct = sum(p[seq]["correct"] for p in points)
        summary[seq] = {"total": total, "correct": correct, "rate": round(correct * 100.0 / total, 2) if total else 0.0}

    return {"points": points, "summary": summary, "pointCount": len(points)}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accuracy_trend(request):
    guard = _require_backend(request)
    if guard:
        return guard
    vtype = request.GET.get("type") or CodingVersion.TYPE_DISEASE
    period = request.GET.get("period") or "year"
    dept = (request.GET.get("dept") or "").strip()
    if period not in PERIOD_LABELS:
        period = "year"
    data = _build_trend(vtype, period, dept)
    data.update(
        {
            "type": vtype,
            "typeName": dict(CodingVersion.TYPE_CHOICES).get(vtype, vtype),
            "period": period,
            "periodName": PERIOD_LABELS[period],
            "dept": dept,
        }
    )
    return _ok(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accuracy_export(request):
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
    except ImportError:
        return _err("服务器缺少 openpyxl，无法导出", 500, 500)

    vtype = request.GET.get("type") or CodingVersion.TYPE_DISEASE
    period = request.GET.get("period") or "year"
    dept = (request.GET.get("dept") or "").strip()
    trend = _build_trend(vtype, period, dept)
    type_name = dict(CodingVersion.TYPE_CHOICES).get(vtype, vtype)

    wb = Workbook()
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1565C0")

    # --- Sheet1 汇总 ---
    ws = wb.active
    ws.title = "准确率汇总"
    ws.append([f"{type_name}准确率统计（{PERIOD_LABELS[period]}{'，科室：' + dept if dept else '，全部科室'}）"])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([])
    ws.append(["数据点", "对应版本", "版本数", "发布时间", "模型测试例数", "模型正确例数", "模型正确率", "医生测试例数", "医生正确例数", "医生正确率"])
    for c in ws[3]:
        c.font = head_font
        c.fill = head_fill
        c.alignment = Alignment(horizontal="center")
    for p in trend["points"]:
        ws.append(
            [
                p["label"],
                p["versionNo"],
                p["versionCount"],
                p["releaseDate"],
                p["model"]["total"],
                p["model"]["correct"],
                (p["model"]["rate"] if p["model"]["rate"] is not None else "—"),
                p["doctor"]["total"],
                p["doctor"]["correct"],
                (p["doctor"]["rate"] if p["doctor"]["rate"] is not None else "—"),
            ]
        )
    ws.append([])
    ws.append(["平均正确率", "", "", "", trend["summary"]["model"]["total"], trend["summary"]["model"]["correct"], trend["summary"]["model"]["rate"], trend["summary"]["doctor"]["total"], trend["summary"]["doctor"]["correct"], trend["summary"]["doctor"]["rate"]])
    ws.append(["内部数据，请勿外传", "", "", "", "", "", "", "", "", ""])
    for col, width in zip("ABCDEFGHIJ", (24, 18, 8, 12, 14, 14, 12, 14, 14, 12)):
        ws.column_dimensions[col].width = width

    # --- Sheet2 明细 ---
    ws2 = wb.create_sheet("抽检明细")
    ws2.append(["版本号", "版本类型", "发布时间", "数据序列", "病案标识", "科室", "判定结果", "是否计入正确", "判定日期", "判定人", "数据来源"])
    for c in ws2[1]:
        c.font = head_font
        c.fill = head_fill
    qs = AccuracyReview.objects.filter(version__version_type=vtype, version__is_active=True).select_related("version", "reviewer")
    if dept:
        qs = qs.filter(dept=dept)
    for r in qs.order_by("version__release_date", "sequence", "id"):
        ws2.append(
            [
                r.version.version_no,
                r.version.get_version_type_display(),
                _fmt_d(r.version.release_date),
                SEQ_LABELS.get(r.sequence, r.sequence),
                r.case_identifier or "",
                r.dept or "",
                r.get_result_display(),
                "是" if r.is_correct else "否",
                _fmt_d(r.review_date),
                (getattr(r.reviewer, "username", "") if r.reviewer else ""),
                r.source,
            ]
        )
    for col, width in zip("ABCDEFGHIJK", (18, 10, 12, 10, 18, 14, 10, 12, 12, 12, 10)):
        ws2.column_dimensions[col].width = width

    filename = f"编码准确率_{type_name}_{timezone.localdate().strftime('%Y%m%d')}.xlsx"
    resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = "attachment; filename*=UTF-8''" + quote(filename)
    wb.save(resp)
    return resp


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def accuracy_reviews(request):
    """抽检标注：录入 / 查询 / 清除（一期用最简单的表单录入 + 批量粘贴）"""
    guard = _require_backend(request)
    if guard:
        return guard

    if request.method == "GET":
        version_id = _to_int(request.GET.get("versionId"))
        page, page_size = _parse_page_params(request, 20, 200)
        qs = AccuracyReview.objects.select_related("version", "reviewer").all()
        if version_id:
            qs = qs.filter(version_id=version_id)
        if request.GET.get("sequence"):
            qs = qs.filter(sequence=request.GET["sequence"])
        if request.GET.get("dept"):
            qs = qs.filter(dept=request.GET["dept"])
        total = qs.count()
        rows = qs.order_by("-id")[(page - 1) * page_size : page * page_size]
        data = [
            {
                "id": r.id,
                "versionId": r.version_id,
                "versionNo": r.version.version_no,
                "sequence": r.sequence,
                "sequenceName": SEQ_LABELS.get(r.sequence, r.sequence),
                "caseIdentifier": r.case_identifier or "",
                "dept": r.dept or "",
                "result": r.result,
                "resultName": r.get_result_display(),
                "isCorrect": r.is_correct,
                "reviewDate": _fmt_d(r.review_date),
                "reviewer": getattr(r.reviewer, "username", "") if r.reviewer else "",
                "source": r.source,
            }
            for r in rows
        ]
        return _ok({"list": data, "total": total, "page": page, "page_size": page_size})

    if request.method == "DELETE":
        guard = _require_super_admin(request)
        if guard:
            return guard
        version_id = _to_int(request.GET.get("versionId"))
        source = request.GET.get("source")
        qs = AccuracyReview.objects.all()
        if version_id:
            qs = qs.filter(version_id=version_id)
        if source:
            qs = qs.filter(source=source)
        n = qs.count()
        qs.delete()
        return _ok({"deleted": n}, f"已删除 {n} 条抽检记录")

    # POST 录入（支持单条 records 数组批量）
    body = _body(request)
    version_id = _to_int(body.get("versionId"))
    try:
        version = CodingVersion.objects.get(pk=version_id)
    except CodingVersion.DoesNotExist:
        return _err("编码版本不存在", 404, 404)

    records = body.get("records")
    if not isinstance(records, list) or not records:
        records = [
            {
                "caseIdentifier": body.get("caseIdentifier"),
                "dept": body.get("dept"),
                "result": body.get("result"),
                "reviewDate": body.get("reviewDate"),
            }
        ]

    default_seq = body.get("sequence") or AccuracyReview.SEQ_MODEL
    default_dept = (body.get("dept") or "").strip() or None
    default_date = _to_date(body.get("reviewDate")) or timezone.localdate()
    created = 0
    with transaction.atomic():
        for rec in records:
            if not isinstance(rec, dict):
                continue
            seq = rec.get("sequence") or default_seq
            if seq not in SEQ_LABELS:
                seq = AccuracyReview.SEQ_MODEL
            result = _to_int(rec.get("result"), AccuracyReview.RESULT_CORRECT)
            if result not in dict(AccuracyReview.RESULT_CHOICES):
                result = AccuracyReview.RESULT_CORRECT
            AccuracyReview.objects.create(
                version=version,
                sequence=seq,
                case_identifier=(str(rec.get("caseIdentifier") or "").strip() or None),
                dept=(str(rec.get("dept") or "").strip() or default_dept),
                result=result,
                reviewer=request.user,
                review_date=_to_date(rec.get("reviewDate")) or default_date,
                source=AccuracyReview.SOURCE_MANUAL,
                remark=(str(rec.get("remark") or "").strip() or None),
            )
            created += 1
    return _ok({"created": created}, f"已录入 {created} 条抽检记录")


# ==========================================================================
# 二、疑难病例讨论
# ==========================================================================
def _case_to_dict(c, detail=False, show_name=False):
    return {
        "id": c.id,
        "caseIdentifier": c.case_identifier or "",
        "patientNo": c.patient_no or "",
        "patientName": (c.patient_name or "") if (detail or show_name) else _mask_name(c.patient_name),
        "dept": c.dept or "",
        "doctor": c.doctor or "",
        "question": c.question or "",
        "status": c.status,
        "statusName": STATUS_LABELS.get(c.status, c.status),
        "submitter": getattr(c.submitter, "username", "") if c.submitter else "",
        "submitterName": (getattr(c.submitter, "profile", None) and c.submitter.profile.real_name) or "",
        "submittedAt": _fmt_dt(c.submitted_at),
        "expertId": c.expert_id,
        "expertName": c.expert.name if c.expert else "",
        "expertTitle": c.expert.title if c.expert else "",
        "assignee": getattr(c.assignee, "username", "") if c.assignee else "",
        "assignedAt": _fmt_dt(c.assigned_at),
        "feedbackAt": _fmt_dt(c.feedback_at),
        "closedAt": _fmt_dt(c.closed_at),
        "remindCount": c.remind_count,
        "lastRemindAt": _fmt_dt(c.last_remind_at),
        "diagnosisSnapshot": c.diagnosis_snapshot or "",
        "surgerySnapshot": c.surgery_snapshot or "",
        "canClose": c.status in (DifficultCase.STATUS_FEEDBACK, DifficultCase.STATUS_PROCESSING),
    }


def _pick_expert(dept):
    """自动分配规则：命中轮值日 → 擅长领域匹配 → 上次分配时间最早者优先"""
    today = timezone.localdate()
    configs = RotationConfig.objects.filter(is_active=True, start_date__lte=today, end_date__gte=today)
    weekday = today.isoweekday()
    on_duty = [c for c in configs if weekday in c.weekday_list]
    if not on_duty:
        return None, "今日非轮值日，已进入待分配队列"
    pool = list(Expert.objects.filter(is_active=True, join_rotation=True))
    if not pool:
        return None, "没有参加排班的专家"
    matched = [e for e in pool if dept and dept in e.tag_list]
    if not matched:
        matched = pool
    matched.sort(key=lambda e: (e.last_assigned_at.timestamp() if e.last_assigned_at else 0, e.id))
    return matched[0], None


def _assign_case(case, expert, actor, is_auto=False, reason=""):
    now = timezone.now()
    case.expert = expert
    case.assignee = expert.user if expert else None
    case.assigned_at = now
    if case.status == DifficultCase.STATUS_PENDING:
        case.status = DifficultCase.STATUS_PROCESSING
    case.save()
    if expert:
        expert.last_assigned_at = now
        expert.save(update_fields=["last_assigned_at"])
    assignment = CaseAssignment.objects.create(
        case=case,
        expert=expert,
        assignee=case.assignee,
        assigned_by=actor if isinstance(actor, User) else None,
        is_auto=is_auto,
        status=CaseAssignment.STATUS_ASSIGNED,
    )
    _log(case, actor, "自动分配" if is_auto else "指派专家", f"{expert.name if expert else '—'} {reason}".strip())
    return assignment


def _case_filters_qs(request):
    qs = DifficultCase.objects.select_related("submitter", "expert", "assignee")
    patient = (request.GET.get("patientNo") or "").strip()
    if patient:
        qs = qs.filter(Q(patient_no__icontains=patient) | Q(case_identifier__icontains=patient) | Q(patient_name__icontains=patient))
    dept = (request.GET.get("dept") or "").strip()
    if dept:
        qs = qs.filter(dept=dept)
    doctor = (request.GET.get("doctor") or "").strip()
    if doctor:
        qs = qs.filter(doctor__icontains=doctor)
    submitter = (request.GET.get("submitter") or "").strip()
    if submitter:
        qs = qs.filter(Q(submitter__username__icontains=submitter) | Q(submitter__profile__real_name__icontains=submitter))
    status = (request.GET.get("status") or "").strip()
    if status:
        qs = qs.filter(status=status)
    start = _to_date(request.GET.get("startDate"))
    if start:
        qs = qs.filter(submitted_at__date__gte=start)
    end = _to_date(request.GET.get("endDate"))
    if end:
        qs = qs.filter(submitted_at__date__lte=end)
    return qs


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cases(request):
    if request.method == "GET":
        guard = _require_backend(request)
        if guard:
            return guard
        page, page_size = _parse_page_params(request, 10, 100)
        qs = _case_filters_qs(request)
        total = qs.count()
        rows = qs.order_by("-submitted_at", "-id")[(page - 1) * page_size : page * page_size]
        counts = dict(DifficultCase.objects.values_list("status").annotate(n=Count("id")))
        return _ok(
            {
                "list": [_case_to_dict(c) for c in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
                "statusCounts": {
                    "pending": counts.get(DifficultCase.STATUS_PENDING, 0),
                    "processing": counts.get(DifficultCase.STATUS_PROCESSING, 0),
                    "feedback": counts.get(DifficultCase.STATUS_FEEDBACK, 0),
                    "closed": counts.get(DifficultCase.STATUS_CLOSED, 0),
                },
            }
        )

    # POST 提交疑难病例（编码员即可提交）
    body = _body(request)
    case = DifficultCase.objects.create(
        case_identifier=(str(body.get("caseIdentifier") or "").strip() or None),
        patient_no=(str(body.get("patientNo") or "").strip() or None),
        patient_name=(str(body.get("patientName") or "").strip() or None),
        dept=(str(body.get("dept") or "").strip() or None),
        doctor=(str(body.get("doctor") or "").strip() or None),
        question=(str(body.get("question") or "").strip() or None),
        diagnosis_snapshot=body.get("diagnosisSnapshot") or None,
        surgery_snapshot=body.get("surgerySnapshot") or None,
        source_record_id=_to_int(body.get("sourceRecordId")),
        submitter=request.user,
    )
    _log(case, request.user, "提交病例", f"科室：{case.dept or '—'}，提交医师：{case.doctor or '—'}")
    expert, reason = _pick_expert(case.dept)
    if expert:
        _assign_case(case, expert, request.user, is_auto=True, reason=reason or "轮值自动分配")
    else:
        _log(case, request.user, "进入待分配", reason)
    case.refresh_from_db()
    return _ok(_case_to_dict(case, detail=True), "病例提交成功")


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def case_detail(request, pk):
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        case = DifficultCase.objects.select_related("submitter", "expert", "assignee").get(pk=pk)
    except DifficultCase.DoesNotExist:
        return _err("病例不存在", 404, 404)

    if request.method == "GET":
        data = _case_to_dict(case, detail=True)
        data["assignments"] = [
            {
                "id": a.id,
                "expertName": a.expert.name if a.expert else "",
                "expertTitle": a.expert.title if a.expert else "",
                "assignedBy": getattr(a.assigned_by, "username", "") if a.assigned_by else "",
                "assignedAt": _fmt_dt(a.assigned_at),
                "feedback": a.feedback or "",
                "feedbackAt": _fmt_dt(a.feedback_at),
                "isAuto": a.is_auto,
                "status": a.status,
                "statusName": a.get_status_display(),
            }
            for a in case.assignments.select_related("expert", "assigned_by").order_by("assigned_at")
        ]
        data["logs"] = [
            {
                "id": lg.id,
                "actorName": lg.actor_name or "",
                "action": lg.action,
                "detail": lg.detail or "",
                "createdAt": _fmt_dt(lg.created_at),
            }
            for lg in case.logs.order_by("created_at")
        ]
        return _ok(data)

    # PATCH 状态流转
    body = _body(request)
    action = (body.get("action") or "").strip()
    if action == "close":
        case.status = DifficultCase.STATUS_CLOSED
        case.closed_at = timezone.now()
        case.save()
        case.assignments.filter(status=CaseAssignment.STATUS_FEEDBACK).update(status=CaseAssignment.STATUS_CLOSED)
        _log(case, request.user, "关闭病例", (body.get("remark") or "").strip())
        return _ok(_case_to_dict(case, detail=True), "病例已关闭")
    if action == "reopen":
        case.status = DifficultCase.STATUS_PROCESSING if case.expert else DifficultCase.STATUS_PENDING
        case.closed_at = None
        case.save()
        _log(case, request.user, "重新打开", "")
        return _ok(_case_to_dict(case, detail=True), "病例已重新打开")
    return _err("不支持的操作", 400, 400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def case_assign(request, pk):
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        case = DifficultCase.objects.get(pk=pk)
    except DifficultCase.DoesNotExist:
        return _err("病例不存在", 404, 404)
    body = _body(request)
    expert_id = _to_int(body.get("expertId"))
    try:
        expert = Expert.objects.get(pk=expert_id, is_active=True)
    except Expert.DoesNotExist:
        return _err("专家不存在或已停用", 404, 404)
    _assign_case(case, expert, request.user, is_auto=False, reason=(body.get("remark") or "").strip())
    case.refresh_from_db()
    return _ok(_case_to_dict(case, detail=True), f"已指派给 {expert.name}")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def case_feedback(request, pk):
    """专家反馈（支持多轮追加）"""
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        case = DifficultCase.objects.select_related("expert").get(pk=pk)
    except DifficultCase.DoesNotExist:
        return _err("病例不存在", 404, 404)
    body = _body(request)
    content = (body.get("content") or "").strip()
    if not content:
        return _err("反馈内容不能为空", 400, 400)
    now = timezone.now()
    assignment = case.assignments.order_by("-assigned_at").first()
    if assignment:
        assignment.feedback = (assignment.feedback + "\n" + content) if assignment.feedback else content
        assignment.feedback_at = now
        assignment.status = CaseAssignment.STATUS_FEEDBACK
        assignment.save()
    else:
        CaseAssignment.objects.create(
            case=case, expert=case.expert, assignee=case.assignee, assigned_by=request.user,
            feedback=content, feedback_at=now, status=CaseAssignment.STATUS_FEEDBACK,
        )
    case.feedback_at = now
    case.status = DifficultCase.STATUS_FEEDBACK
    case.save()
    _log(case, request.user, "录入反馈", content[:200])
    case.refresh_from_db()
    return _ok(_case_to_dict(case, detail=True), "反馈已录入")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def case_remind(request, pk):
    guard = _require_backend(request)
    if guard:
        return guard
    try:
        case = DifficultCase.objects.get(pk=pk)
    except DifficultCase.DoesNotExist:
        return _err("病例不存在", 404, 404)
    case.remind_count += 1
    case.last_remind_at = timezone.now()
    case.save(update_fields=["remind_count", "last_remind_at"])
    _log(case, request.user, "催办", f"第 {case.remind_count} 次催办")
    return _ok({"remindCount": case.remind_count}, "已记录催办")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def case_auto_assign(request):
    """批量自动分配（兜底：非轮值日堆积的待分配病例）"""
    guard = _require_backend(request)
    if guard:
        return guard
    body = _body(request)
    ids = body.get("caseIds")
    qs = DifficultCase.objects.filter(status=DifficultCase.STATUS_PENDING)
    if isinstance(ids, list) and ids:
        qs = qs.filter(id__in=[i for i in ids if isinstance(i, int)])
    assigned, skipped = 0, 0
    for case in qs.order_by("submitted_at"):
        expert, reason = _pick_expert(case.dept)
        if expert:
            _assign_case(case, expert, request.user, is_auto=True, reason=reason or "人工触发自动分配")
            assigned += 1
        else:
            skipped += 1
    msg = f"自动分配 {assigned} 例" + (f"，{skipped} 例未分配（{reason}）" if skipped else "")
    return _ok({"assigned": assigned, "skipped": skipped}, msg)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def case_filter_options(request):
    guard = _require_backend(request)
    if guard:
        return guard
    depts = sorted({x for x in DifficultCase.objects.values_list("dept", flat=True).distinct() if x})
    doctors = sorted({x for x in DifficultCase.objects.values_list("doctor", flat=True).distinct() if x})
    submitters = []
    for u in User.objects.filter(submitted_cases__isnull=False).distinct().select_related("profile")[:200]:
        submitters.append(
            {
                "username": u.username,
                "name": (getattr(u, "profile", None) and u.profile.real_name) or u.username,
            }
        )
    experts = [
        {"id": e.id, "name": e.name, "title": e.title, "deptTags": e.tag_list, "joinRotation": e.join_rotation}
        for e in Expert.objects.filter(is_active=True)
    ]
    return _ok(
        {
            "depts": depts,
            "doctors": doctors,
            "submitters": submitters,
            "experts": experts,
            "statuses": [{"value": k, "label": v} for k, v in DifficultCase.STATUS_CHOICES],
        }
    )


# ==========================================================================
# 三、轮值安排（轮值配置 + 专家目录）
# ==========================================================================
def _rotation_to_dict(c):
    return {
        "id": c.id,
        "hospital": c.hospital,
        "weekdays": c.weekday_list,
        "weekdayNames": [dict(RotationConfig.WEEKDAY_CHOICES).get(d, d) for d in c.weekday_list],
        "startDate": _fmt_d(c.start_date),
        "endDate": _fmt_d(c.end_date),
        "isActive": c.is_active,
    }


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def rotation_config(request):
    guard = _require_backend(request)
    if guard:
        return guard

    if request.method == "GET":
        items = [_rotation_to_dict(c) for c in RotationConfig.objects.all().order_by("-start_date", "-id")]
        today = timezone.localdate()
        active = [c for c in items if c["isActive"] and c["startDate"] <= _fmt_d(today) <= c["endDate"]]
        return _ok({"list": items, "todayWeekday": today.isoweekday(), "activeCount": len(active)})

    if request.method == "DELETE":
        guard = _require_super_admin(request)
        if guard:
            return guard
        rid = _to_int(request.GET.get("id"))
        RotationConfig.objects.filter(pk=rid).delete()
        return _ok(msg="轮值配置已删除")

    guard = _require_super_admin(request)
    if guard:
        return guard
    body = _body(request)
    weekdays = body.get("weekdays") or []
    if isinstance(weekdays, str):
        weekdays = [w for w in weekdays.replace("，", ",").split(",") if w.strip()]
    weekdays = sorted({_to_int(w) for w in weekdays if _to_int(w) in range(1, 8)})
    if not weekdays:
        return _err("请至少选择一个轮值日", 400, 400)
    start = _to_date(body.get("startDate"))
    end = _to_date(body.get("endDate"))
    if not start or not end:
        return _err("请填写生效时间起止", 400, 400)
    if end < start:
        return _err("结束日期不能早于开始日期", 400, 400)
    rid = _to_int(body.get("id"))
    values = {
        "hospital": (body.get("hospital") or "主院区").strip(),
        "weekdays": ",".join(str(w) for w in weekdays),
        "start_date": start,
        "end_date": end,
        "is_active": bool(body.get("isActive", True)),
    }
    if rid:
        updated = RotationConfig.objects.filter(pk=rid).update(**values)
        if not updated:
            return _err("轮值配置不存在", 404, 404)
        return _ok(_rotation_to_dict(RotationConfig.objects.get(pk=rid)), "轮值配置已更新")
    cfg = RotationConfig.objects.create(**values)
    return _ok(_rotation_to_dict(cfg), "轮值配置已创建")


def _expert_to_dict(e, with_stats=False):
    data = {
        "id": e.id,
        "name": e.name,
        "title": e.title,
        "deptTags": e.tag_list,
        "joinRotation": e.join_rotation,
        "phone": e.phone or "",
        "user": getattr(e.user, "username", "") if e.user else "",
        "isActive": e.is_active,
        "lastAssignedAt": _fmt_dt(e.last_assigned_at),
    }
    if with_stats:
        data["processingCount"] = e.cases.filter(
            status__in=[DifficultCase.STATUS_PROCESSING, DifficultCase.STATUS_FEEDBACK]
        ).count()
        data["totalCount"] = e.cases.count()
    return data


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def experts(request):
    guard = _require_backend(request)
    if guard:
        return guard
    if request.method == "GET":
        items = [_expert_to_dict(e, with_stats=True) for e in Expert.objects.filter(is_active=True)]
        return _ok({"list": items, "total": len(items)})

    guard = _require_super_admin(request)
    if guard:
        return guard
    body = _body(request)
    name = (body.get("name") or "").strip()
    if not name:
        return _err("姓名不能为空", 400, 400)
    user = None
    username = (body.get("user") or "").strip()
    if username:
        user = User.objects.filter(username=username).first()
    expert = Expert.objects.create(
        name=name,
        title=(body.get("title") or "副主任医师").strip(),
        dept_tags=",".join(_split_tags(body.get("deptTags"))),
        join_rotation=bool(body.get("joinRotation", True)),
        user=user,
        phone=(str(body.get("phone") or "").strip() or None),
    )
    return _ok(_expert_to_dict(expert, with_stats=True), "专家已新增")


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def expert_detail(request, pk):
    guard = _require_super_admin(request)
    if guard:
        return guard
    try:
        expert = Expert.objects.get(pk=pk)
    except Expert.DoesNotExist:
        return _err("专家不存在", 404, 404)

    if request.method == "DELETE":
        if expert.cases.exists():
            expert.is_active = False
            expert.save(update_fields=["is_active"])
            return _ok(msg="该专家已有病例记录，已停用（历史数据保留）")
        expert.delete()
        return _ok(msg="专家已删除")

    body = _body(request)
    if "name" in body and (body.get("name") or "").strip():
        expert.name = body["name"].strip()
    if "title" in body:
        expert.title = (body.get("title") or expert.title).strip()
    if "deptTags" in body:
        expert.dept_tags = ",".join(_split_tags(body.get("deptTags")))
    if "joinRotation" in body:
        expert.join_rotation = bool(body.get("joinRotation"))
    if "phone" in body:
        expert.phone = (str(body.get("phone") or "").strip() or None)
    if "user" in body:
        expert.user = User.objects.filter(username=(body.get("user") or "").strip()).first()
    expert.save()
    return _ok(_expert_to_dict(expert, with_stats=True), "专家已更新")
