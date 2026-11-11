from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import V_Patient_Diagnosis, V_Patient_Surgery


def _clean_text(value, max_len=None):
    if value is None:
        return ""
    text = str(value).strip()
    if max_len is not None:
        text = text[:max_len]
    return text


def _parse_positive_int(value, default=1):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_response_time(value):
    if not value:
        return None
    if hasattr(value, "tzinfo"):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    parsed = parse_datetime(str(value))
    if parsed is None:
        return None
    return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_icd_codes(request):
    data = request.data
    if not isinstance(data, list):
        return JsonResponse({"code": 400, "msg": "Data format error, list expected"}, status=400)

    surgery_list = []
    diagnosis_list = []
    invalid_count = 0

    for entry in data:
        if not isinstance(entry, dict):
            invalid_count += 1
            continue

        answer_type = _clean_text(entry.get("answerType"))
        case_id = _clean_text(entry.get("case_id"), 50)
        name = _clean_text(entry.get("name"), 200)
        code = _clean_text(entry.get("code"), 50)
        seq = _parse_positive_int(entry.get("seq"), 1)
        response_time = _parse_response_time(entry.get("model_response_time"))

        if not all([answer_type, case_id, name, code]):
            invalid_count += 1
            continue

        if answer_type == "surgery":
            surgery_list.append(V_Patient_Surgery(
                case_id=case_id,
                surgery_seq=seq,
                surgery_code=code,
                surgery_name=name,
                model_response_time=response_time,
            ))
        elif answer_type == "diagnosis":
            diag_type = _clean_text(entry.get("diag_type") or V_Patient_Diagnosis.DiagnosisType.DISCHARGE, 20)
            if diag_type not in V_Patient_Diagnosis.DiagnosisType.values:
                diag_type = V_Patient_Diagnosis.DiagnosisType.DISCHARGE
            diagnosis_list.append(V_Patient_Diagnosis(
                case_id=case_id,
                diag_type=diag_type,
                diag_seq=seq,
                diag_code=code,
                diag_name=name,
                model_response_time=response_time,
            ))
        else:
            invalid_count += 1

    if not diagnosis_list and not surgery_list:
        return JsonResponse({"code": 400, "msg": "No valid data to save"}, status=400)

    try:
        with transaction.atomic():
            if surgery_list:
                V_Patient_Surgery.objects.bulk_create(surgery_list, batch_size=1000)
            if diagnosis_list:
                V_Patient_Diagnosis.objects.bulk_create(diagnosis_list, batch_size=1000)
    except Exception:
        return JsonResponse({"code": 500, "msg": "保存失败，服务器内部错误"}, status=500)

    return JsonResponse({
        "code": 200,
        "msg": f"保存成功! 诊断: {len(diagnosis_list)} 条, 手术: {len(surgery_list)} 条",
        "data": {
            "diagnosis_count": len(diagnosis_list),
            "surgery_count": len(surgery_list),
            "invalid_count": invalid_count,
        },
    })
