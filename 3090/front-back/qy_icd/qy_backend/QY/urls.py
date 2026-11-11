from django.urls import include, path


from . import views

from . import views_chat as vc

# TODO: Surgery and Diagnosis views
from . import views_sur_diag as vsd

# TODO: User Management views
from . import views_user_mgmt as vum

# 病案编码管理后台（一期）
from . import views_admin as vad  # noqa: F401

urlpatterns = [
    path("", views.index, name="index"),

    # Auth APIs
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/me/", views.me, name="me"),

    # path("chat-history/", vc.chat_history_list_create, name="chat_history_list_create"), 
    path("chat-sessions/", vc.chat_sessions, name="chat_sessions"),
    path('chat-sessions/create/', vc.chat_sessions_create, name='chat_sessions_create'),
    path('chat-sessions/<uuid:pk>/delete/', vc.delete_session, name='delete_session'),
    path('chat-sessions/<uuid:pk>/update/', vc.update_session, name='update_session'),

    path('chat-messages/', vc.chat_messages, name='chat_messages'),
    path('chat-messages-update-status/', vc.chat_messages_update_status, name='chat_messages_update_status'),
    path('chat-messages-all/', vc.chat_messages_all, name='chat_messages_all'),
    path('chat-messages-all-all/', vc.chat_messages_all_all, name='chat_messages_all_all'),
    path('chat-messages/create/', vc.chat_messages_create, name='chat_messages_create'),

    path('chat-messages/feedback/', vc.feedback_create, name='feedback_create'),
    path('chat-messages/feedback/list/', vc.feedback_list, name='feedback_list'),
    path('chat-messages/feedback/list-all/', vc.feedback_list_all, name='feedback_list_all'),
    path('chat-messages/feedback/list-all-all/', vc.feedbacks_list_all_all, name='feedbacks_list_all_all'),
    
    path('chat-messages/feedback/delete/', vc.feedback_delete, name='feedback_delete'),
    path('chat-messages/feedback/remark/', vc.feedback_remark, name='feedback_remark'),

    path('chat-messages/feedback/export/', vc.export_feedback, name='export_feedback'),
    # path("chat-history/<uuid:pk>/", vc.chat_history_detail, name="chat_history_detail"),  
    # path('chat-history/<str:pk>/', vc.chat_history_detail, name='chat_history_detail'),

    # Feedback API
    # path('api/feedback/submit/', vf.submit_feedback, name='submit_feedback'),

    # OCR Data CRUD
    path("ocr/records/", views.ocr_records, name="ocr_records"),
    path("ocr/records/<int:pk>/", views.ocr_record_detail, name="ocr_record_detail"),

    # Surgrey
    path('save-icd-codes/', vsd.save_icd_codes, name='save_icd_codes'),

    # User Management
    # 用户管理
    path("users/", vum.user_list_create, name="user_list_create"),                # GET 列表 / POST 创建
    path("users/<int:pk>/", vum.user_edit, name="user_edit"),                     # PUT/PATCH 编辑
    path("users/<int:pk>/status/", vum.user_status_edit, name="user_status_edit"),# PUT/PATCH 状态修改
    path("users/<int:pk>/delete/", vum.user_delete, name="user_delete"),          # DELETE 删除
    path("users/change-password/", vum.change_password, name="change_password"),

    # 病案编码管理后台（一期）：/qy/admin/...
    path("admin/", include("QY.urls_admin")),
]   