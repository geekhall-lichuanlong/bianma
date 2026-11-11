# -*- coding: utf-8 -*-
"""病案编码管理后台路由

挂载于 ``QY/urls.py`` 的 ``admin/`` 前缀下，最终地址为 ``/qy/admin/...``。
（注意：不能挂到项目根 ``/admin/``，那里已被 Django Admin 占用）
"""

from django.urls import path

from . import views_admin as va

urlpatterns = [
    # 元信息
    path("me/", va.admin_me, name="admin_me"),
    path("departments/", va.department_list, name="admin_departments"),

    # 版本迭代
    path("versions/", va.versions, name="admin_versions"),
    path("versions/<int:pk>/", va.version_detail, name="admin_version_detail"),
    path("accuracy/trend/", va.accuracy_trend, name="admin_accuracy_trend"),
    path("accuracy/export/", va.accuracy_export, name="admin_accuracy_export"),
    path("accuracy/reviews/", va.accuracy_reviews, name="admin_accuracy_reviews"),

    # 疑难病例讨论
    path("cases/", va.cases, name="admin_cases"),
    path("cases/filter-options/", va.case_filter_options, name="admin_case_filter_options"),
    path("cases/auto-assign/", va.case_auto_assign, name="admin_case_auto_assign"),
    path("cases/<int:pk>/", va.case_detail, name="admin_case_detail"),
    path("cases/<int:pk>/assign/", va.case_assign, name="admin_case_assign"),
    path("cases/<int:pk>/feedback/", va.case_feedback, name="admin_case_feedback"),
    path("cases/<int:pk>/remind/", va.case_remind, name="admin_case_remind"),

    # 轮值安排
    path("rotation/config/", va.rotation_config, name="admin_rotation_config"),
    path("experts/", va.experts, name="admin_experts"),
    path("experts/<int:pk>/", va.expert_detail, name="admin_expert_detail"),
]
