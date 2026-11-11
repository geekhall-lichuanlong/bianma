from django.http import JsonResponse
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import ChatSessions, ChatMessages, Feedback, UserProfile
import json
import re

def _chat_session_to_dict(session):
    return {
        "id": str(session.id),
        "user_id": session.user_id,
        "title": session.title,
        "chat_mode": session.chat_mode,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }

def _chat_message_to_dict(message):
    return {
        "id": str(message.id),
        "session_id": str(message.session_id),
        "message_order": message.message_order,
        "message": message.message,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_sessions_create(request):
    """
    POST: 创建新的聊天记录会话
    """
    # @api_view 已经帮我们解析了 request.data
    user = request.user
    data = request.data
    title = data.get('title', '新对话')
    chat_mode = data.get('chat_mode')
    # chat_data = data.get('data', {})

    if not chat_mode:
            return JsonResponse({"code": 400, "msg": "chat_mode is required"}, status=400)

    # 1. 查找属于当前用户、指定模式、且消息数量为0的会话
    empty_session = ChatSessions.objects.filter(
        user=user, 
        chat_mode=chat_mode
    ).annotate(
        num_messages=Count('messages')
    ).filter(
        num_messages=0
    ).order_by('-updated_at').first()

    if empty_session:
        # 2. 如果找到了空会话，直接复用
        # 可选：如果前端传了新标题，可以在这里更新一下标题
        if 'title' in data and data['title'] != empty_session.title:
             empty_session.title = title
             empty_session.save(update_fields=['title']) # 仅更新标题，不更新 updated_at 以免干扰排序逻辑（或者视需求更新）

        return JsonResponse({
            "code": 201, 
            "msg": "复用已存在的空会话成功！", 
            "data": _chat_session_to_dict(empty_session)
        })

    # 创建记录
    chat_history = ChatSessions.objects.create(
        user=user,
        chat_mode=chat_mode,
        title=title
    )

    return JsonResponse({
        "code": 200, 
        "msg": "为当前用户创建聊天记录会话成功！", 
        "data": _chat_session_to_dict(chat_history)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    GET: 获取当前用户的所有会话，按照chat_mode过滤
    """
    user = request.user

    chat_mode = request.GET.get('chat_mode')
    
    # 基础查询：仅限当前用户
    qs = ChatSessions.objects.filter(user=user).order_by('-updated_at')
    
    # 过滤类型
    if chat_mode:
        qs = qs.filter(chat_mode=chat_mode)
        
    # 获取当前用户的所有会话id
    sessions_list = [_chat_session_to_dict(item) for item in qs]
    
    # print(f"chat_mode={chat_mode}, sessions_id_list={sessions_id_list}")

    return JsonResponse({
        "code": 200,
        "data": sessions_list,
        "msg": "获取当前用户的所有会话成功！"
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_session(request, pk):
    """
    DELETE: 删除聊天记录
    """
    try:
        session = ChatSessions.objects.get(id=pk, user=request.user)
    except (ChatSessions.DoesNotExist, ValueError):
        return JsonResponse({"code": 404, "msg": "Session not found"}, status=404)

    session.delete()
    # TODO 删除其所有的Messages


    return JsonResponse({
        "code": 200, 
        "msg": "历史会话及其关联消息已删除成功"
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_session(request, pk):
    """
    pk: 这里接收的是 UUID 字符串
    PUT/PATCH: 更新聊天记录 (标题或内容)
    """
    try:
        # 尝试通过 uuid 查找
        session = ChatSessions.objects.get(id=pk, user=request.user)
    except (ChatSessions.DoesNotExist, ValueError):
        return JsonResponse({"code": 404, "msg": "Session not found"}, status=404)

    data = request.data
    
    # 更新字段
    if 'title' in data:
        session.title = data['title']
        
    session.save()
    
    return JsonResponse({
        "code": 200, 
        "msg": "Updated successfully", 
        "data": _chat_session_to_dict(session)
    })


# --------------------- Messages --------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_messages_create(request):
    """
    POST: 在一个会话中创建新的消息
    """
    user = request.user
    data = request.data
    
    session_id = data.get('session_id')
    messages_list = data.get('messages') # 这是一个列表，包含具体的 json 消息体

    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)
    
    if not messages_list or not isinstance(messages_list, list):
        return JsonResponse({"code": 400, "msg": "messages list is required"}, status=400)

    # 1. 获取 Session 并校验权限 (必须是当前用户的会话)
    try:
        session = ChatSessions.objects.get(id=session_id, user=user)
    except (ChatSessions.DoesNotExist, ValueError):
        return JsonResponse({"code": 404, "msg": "Session not found"}, status=404)

    # 2. 计算起始 message_order
    # 获取当前会话中最大的 order，如果没有则从 1 开始
    max_order = ChatMessages.objects.filter(session=session).aggregate(Max('message_order'))['message_order__max']
    current_order = (max_order or 0) + 1

    # 3. 准备批量创建的对象
    new_messages_objs = []
    for msg_content in messages_list:
        new_messages_objs.append(ChatMessages(
            session=session,
            message=msg_content, # 直接存储 JSON 数据
            message_order=current_order
        ))
        current_order += 1

    # 4. 执行批量创建
    if new_messages_objs:
        ChatMessages.objects.bulk_create(new_messages_objs)
        
        # 5. 更新 Session 的 updated_at 时间
        # 调用 save() 会触发 auto_now=True 更新时间
        session.save()

    return JsonResponse({
        "code": 200, 
        "msg": "消息添加成功",
        "data": {
            "message_id": [str(msg.id) for msg in new_messages_objs],
            "session_id": session_id,
            "added_count": len(new_messages_objs)
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages(request):
    """
    GET: 根据 session_id 获取该会话的所有消息
    Query Param: session_id
    """
    session_id = request.GET.get('session_id')

    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)

    # 1. 查找 Session，并确保归属于当前用户
    try:
        session = ChatSessions.objects.get(id=session_id, user=request.user)
    except (ChatSessions.DoesNotExist, ValueError):
        return JsonResponse({"code": 404, "msg": "Session not found"}, status=404)

    # 2. 查询该 Session 下的所有 Messages，按 message_order 正序排列
    messages_qs = ChatMessages.objects.filter(session=session).order_by('message_order')

    # 3. 构造返回数据
    messages_list = []
    for msg in messages_qs:
        messages_list.append(_chat_message_to_dict(msg))

    return JsonResponse({
        "code": 200,
        "msg": "获取会话中的所有消息成功",
        "data": messages_list
    })

# models: ChatSessions, ChatMessages imported from your app
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages_all(request):
    """
    GET: 获取当前用户所有会话的消息
    返回 data: 当 group=true -> {"<session_id>": [ messages... ], ...}
                 当 group=false -> [ {id, session_id, message_order, message, created_at}, ... ]
    """
    user = request.user

    session_ids = request.GET.get('session_ids')
    group = request.GET.get('group', 'true').lower() == 'true'

    qs = ChatMessages.objects.filter(session__user=user).select_related('session').order_by('session_id', 'message_order')

    if session_ids:
        ids = [s.strip() for s in session_ids.split(',') if s.strip()]
        if ids:
            qs = qs.filter(session_id__in=ids)

    values = qs.values('id', 'session_id', 'message_order', 'message', 'created_at')
    rows = list(values)

    if group:
        grouped = {}
        for r in rows:
            sid = str(r['session_id'])
            grouped.setdefault(sid, []).append(r)
        data = grouped
    else:
        data = rows

    return JsonResponse({"code": 200, "msg": "success", "data": data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages_all_all(request):
    """
    GET: 管理员导出所有非管理员用户的所有会话消息（简洁版）
    仅当当前请求用户为管理员 (UserProfile.ROLE_ADMIN) 时允许导出，否则返回 403。
    """
    # 权限检查
    try:
        if request.user.profile.role != UserProfile.ROLE_ADMIN:
            return JsonResponse({"code": 403, "msg": "permission denied"}, status=403)
    except Exception:
        return JsonResponse({"code": 403, "msg": "permission denied"}, status=403)


    # 基本 queryset：仅包含 role == ROLE_USER 的用户的消息
    qs = ChatMessages.objects.filter(session__user__profile__role=UserProfile.ROLE_USER) \
        .select_related('session', 'session__user') \
        .order_by('session_id', 'message_order')

    # 取出需要的字段
    values = qs.values(
        'id',
        'session_id',
        'message_order',
        'message',
        'created_at',
        'session__user_id',
        'session__user__username',
        'session__title'
    )
    rows = list(values)

    data = []
    for r in rows:
        data.append({
            "id": r['id'],
            "session_id": str(r['session_id']),
            "message_order": r['message_order'],
            "message": r['message'],
            "created_at": r['created_at'],

            # 区分用户
            "user_id": r['session__user_id'],
            "username": r['session__user__username'],
            "session_title": r['session__title'],
        })

    return JsonResponse({"code": 200, "msg": "success", "data": data})

# --------------------- FeedBack --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_list(request):
    """
    GET: 获取当前用户指定会话中所有消息的反馈列表
    """
    user = request.user
    session_id = request.GET.get("session_id")

    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)

    # 验证 session 属于当前用户
    session = get_object_or_404(ChatSessions, id=session_id, user=user)

    # 一次性获取该 session 下所有消息的所有反馈（优化查询次数）
    feedbacks = Feedback.objects.filter(
        message__session=session
    ).values(
        'message_id',
        'category',
        'row_id',
        'type',
        'remark'
    )

    data = list(feedbacks)

    return JsonResponse({
        "code": 200,
        "msg": "success",
        "data": data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_list_all(request):
    """
    GET: 获取当前用户所有会话中所有消息的反馈列表
    """
    user = request.user

    # 一次性获取该用户所有会话下所有消息的所有反馈（优化查询次数）
    feedbacks = Feedback.objects.filter(
        message__session__user=user
    ).values(
        'message_id',
        'category',
        'row_id',
        'type',
        'remark'
    )

    data = list(feedbacks)

    return JsonResponse({
        "code": 200,
        "msg": "success",
        "data": data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedbacks_list_all_all(request):
    """
    GET: 管理员获取所有普通用户（role == UserProfile.ROLE_USER）所有会话的所有消息的反馈列表
    仅当当前请求用户为管理员 (UserProfile.ROLE_ADMIN) 时允许访问，否则返回 403。
    返回字段与 feedback_list_all 类似，并附带反馈时间与来源用户/会话信息以便区分。
    """
    # 权限检查：仅管理员可调用
    try:
        if request.user.profile.role != UserProfile.ROLE_ADMIN:
            return JsonResponse({"code": 403, "msg": "permission denied"}, status=403)
    except Exception:
        return JsonResponse({"code": 403, "msg": "permission denied"}, status=403)

    # 获取所有普通用户的所有会话的所有消息的反馈
    feedbacks_qs = Feedback.objects.filter(
        message__session__user__profile__role=UserProfile.ROLE_USER
    ).select_related('message__session__user', 'message__session') \
     .values(
        'id',
        'message_id',
        'category',
        'row_id',
        'type',
        'reason',
        'remark',
        'timestamp',
        'message__session_id',
        'message__session__user_id',
        'message__session__user__username',
    )

    data = list(feedbacks_qs)

    return JsonResponse({
        "code": 200,
        "msg": "success",
        "data": data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_remark(request):
    """
    POST: 获取某一个反馈的remark内容
    """
    data = request.data
    user = request.user

    # 1. 获取参数
    session_id = data.get("session_id")
    message_id = int(data.get('message_id', -1)) # 转化为int
    category = data.get('category') # diagnosis or surgery
    row_id = data.get('row_id') # int


    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)

    if not all(x is not None for x in [message_id, row_id, category]):
        return JsonResponse({"code": 400, "msg": "Missing required fields"}, status=400)

    session = get_object_or_404(ChatSessions, id=session_id, user=user)
    message = get_object_or_404(ChatMessages, id=message_id, session=session)
    feedback = get_object_or_404(
        Feedback,
        message=message,
        category=category,
        row_id=row_id
    )

    return JsonResponse({
        "code": 200, 
        "msg": "获取反馈的内容成功",
        "data": feedback.remark or "",
        "tag": feedback.reason or ""
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_create(request):
    """
    POST: 提交消息反馈 (点赞/点踩)
    """
    data = request.data
    user = request.user

    # 1. 获取参数
    session_id = data.get("session_id")
    message_id = data.get('message_id', -1) # 转化为int
    category = data.get('category') # diagnosis or surgery
    feedback_type = data.get('type') # like or dislike
    row_id = data.get('row_id') # int
    tag = data.get('reason', '')
    remark = data.get('remark', '')

    # 2. 基础校验
    if not all(x is not None for x in [message_id, feedback_type, row_id, category]):
        return JsonResponse({"code": 400, "msg": "Missing required fields (message_id, type, row_id, category)"}, status=400)

    if feedback_type not in Feedback.FeedbackType.values:
        return JsonResponse({"code": 400, "msg": "Invalid feedback type"}, status=400)

    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)
    
    try:
        message_id = int(message_id)
        row_id = int(row_id)
    except (ValueError, TypeError):
        return JsonResponse({"code": 400, "msg": "message_id and row_id must be integers"}, status=400)

    session = get_object_or_404(ChatSessions, id=session_id, user=user)
    message = get_object_or_404(ChatMessages, id=message_id, session=session)
    
    feedback, created = Feedback.objects.update_or_create(
        message=message,
        category=category,
        row_id=row_id,
        defaults={
            "type": feedback_type,
            "reason": tag, 
            "remark": remark,
        }
    )

    status_text = "created" if created else "updated"
    msg = "反馈提交成功" if created else "反馈已更新"

    return JsonResponse({
        "code": 200,
        "msg": msg,
        "data": {
            "status": status_text,
            "type": feedback_type
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_delete(request):
    """
    POST: 删除指定反馈
    """
    user = request.user
    data = request.data

    session_id = data.get("session_id")
    message_id = data.get("message_id")
    category = data.get("category")
    row_id = data.get("row_id")

    if not session_id:
        return JsonResponse({"code": 400, "msg": "session_id is required"}, status=400)

    if not all(x is not None for x in [message_id, row_id, category]):
        return JsonResponse({"code": 400, "msg": "Missing required fields"}, status=400)

    try:
        message_id = int(message_id)
        row_id = int(row_id)
    except (ValueError, TypeError):
        return JsonResponse({"code": 400, "msg": "Invalid message_id or row_id"}, status=400)

    session = get_object_or_404(ChatSessions, id=session_id, user=user)
    message = get_object_or_404(ChatMessages, id=message_id, session=session)

    try:
        feedback = Feedback.objects.get(
            message=message,
            category=category,
            row_id=row_id
        )
        feedback.delete()
    except Feedback.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "Feedback not found"}, status=404)

    return JsonResponse({
        "code": 200,
        "msg": "反馈已删除",
        "data": {"status": "deleted"}
    })

# def export_feedback(request):
#     """
#     导出所有带有反馈的消息，格式如下：
#     {
#     "id": "msg_uuid_1",
#     "instruction": "请对以下病历进行ICD编码...",
#     "input": "患者主诉胸痛3天...",
#     "output": "{
#         "disease": [(name, code, feed_type, tag, remark),(...),(...),(...)]
#         "surgery": [(...),(...),(...),(...)]
#     }",
#     "comment": "对这个编码结果的整体评价",
#     }
#     """
#     messages_with_feedback = ChatMessages.objects.filter(
#         feedbacks__isnull=False
#     ).prefetch_related('feedbacks').distinct()


#     for msg_obj in messages_with_feedback:
#         message_id = int(msg_obj.id)  # int -> 1124
#         msg_content = msg_obj.message
#         '''
#         {
#         "question": "1",
#         "answers": {
#             "diagnosis": {
#                 "answerList": []
#             },
#             "surgery": {
#                 "answerList": []
#             }
#         },
#         "questionSource": "INPUT",
#         "createdAt": "2025-12-16T09:16:06.581Z",
#         "createdBy": "当前用户"
#         }
#         '''
#         msg_content = json.loads(msg_obj.message)
#         input = msg_content.get("question", "")


#         # 获取编码结果
#         allEntries = []
#         for answerType in ["diagnosis", "surgery"]:
#             tableData = msg_content["answers"][answerType]["answerList"][-1].get("tableData", None)
#             if (tableData is None or len(tableData) < 2):
#                 continue
            
#             for i in range(1, len(tableData)):
#                 row = tableData[i]

#                 if len(row) < 3:
#                     continue  # 至少要有 case_id, name, code

#                 rawName = row[1] or ''
#                 cleanName = rawName.replace("/^\*+|\*+$/g", '').trim()

#                 rawCode = row[2] or ''
#                 cleanCode = rawCode.replace("/^\*+|\*+$/g", '').trim()
#                 cleanCode = cleanCode.replace("/^['\"\[]+|['\"\]]+$/g", '').trim()

#                 entry = (cleanName, cleanCode, feed_type, tag, remark)
#                 allEntries.append(entry)
#         output = 

@api_view(['GET'])  # 通常导出是GET请求，或者POST看具体需求，这里假设加上装饰器
@permission_classes([IsAuthenticated])
def export_feedback(request):
    """
    导出所有用户的所有带反馈的消息，格式如下：
    {
        "id": "msg_uuid_1",
        "instruction": "请对以下病历进行ICD编码...",
        "input": "患者主诉胸痛3天...",
        "output": "{ 'disease': [...], 'surgery': [...] }",
        "comment": "对这个编码结果的整体评价",
    }
    """
    # 筛选出至少含有一条反馈的消息
    messages_with_feedback = ChatMessages.objects.filter(
        feedbacks__isnull=False
    ).prefetch_related('feedbacks').distinct()

    export_list = []

    for msg_obj in messages_with_feedback:
        # 处理 JSONField，Django高版本可能自动转为dict，低版本或者是存的str需要loads
        raw_msg = msg_obj.message
        if isinstance(raw_msg, str):
            try:
                msg_content = json.loads(raw_msg)
            except json.JSONDecodeError:
                continue
        else:
            msg_content = raw_msg

        # 获取该消息下的所有反馈，构建查找表 {(category, row_id): feedback_obj}
        # Category: 0=Diagnosis, 1=Surgery
        # FeedbackType: COMMENT 用于整条消息的评价，通常不绑定特定row_id或特定约定
        feedbacks = msg_obj.feedbacks.all()
        feedback_map = {}
        overall_comment = ""

        for fb in feedbacks:
            if fb.type == Feedback.FeedbackType.COMMENT:
                overall_comment = fb.remark
            else:
                feedback_map[(fb.category, fb.row_id)] = fb

        # 准备输出数据容器
        output_data = {
            "disease": [],
            "surgery": []
        }

        # 定义处理映射：key in json -> (category_id, output_key)
        type_mapping = {
            "diagnosis": (Feedback.CategoryType.DIAGNOSIS, "disease"),
            "surgery": (Feedback.CategoryType.SURGERY, "surgery")
        }

        answers = msg_content.get("answers", {})
        
        for json_key, (cat_id, out_key) in type_mapping.items():
            if json_key not in answers:
                continue
                
            answer_node = answers[json_key].get("answerList", [])
            if not answer_node:
                continue
            
            # 取最后一次生成的答案（假设逻辑）
            last_answer = answer_node[-1]
            table_data = last_answer.get("tableData", [])

            # tableData通常第0行是表头，从第1行开始是数据
            if not table_data or len(table_data) < 2:
                continue

            for i in range(1, len(table_data)):
                row = table_data[i]
                current_row_id = i - 1 # 从 0 开始

                # 简单校验行长度
                if len(row) < 3:
                    continue

                # 数据清洗 (对应 JS: .replace(/^\*+|\*+$/g, '').trim())
                raw_name = str(row[1]) if row[1] else ""
                clean_name = re.sub(r"^\*+|\*+$", "", raw_name).strip()

                raw_code = str(row[2]) if row[2] else ""
                # 对应 JS: .replace(/^['"\[]+|['"\]]+$/g, '')
                clean_code = re.sub(r"^['\"\[]+|['\"\]]+$", "", raw_code).strip()
                # 再次清洗星号
                clean_code = re.sub(r"^\*+|\*+$", "", clean_code).strip()

                # 查找是否有反馈
                fb_obj = feedback_map.get((cat_id, current_row_id))
                
                feed_type = fb_obj.type if fb_obj else None
                tag = fb_obj.reason if fb_obj else None
                remark = fb_obj.remark if fb_obj else None

                # 构建元组 entry
                entry = (clean_name, clean_code, feed_type, tag, remark)
                output_data[out_key].append(entry)

        # 构建最终导出对象
        export_item = {
            "id": str(msg_obj.id),
            # "instruction": "请根据病历内容进行ICD编码和手术编码提取。", # 默认指令，或者根据业务逻辑生成
            "input": msg_content.get("question", ""),
            "output": json.dumps(output_data, ensure_ascii=False), # 将结果序列化为字符串
            "comment": overall_comment,
        }
        
        export_list.append(export_item)

    return JsonResponse({
        "code": 200,
        "msg": "Export successful",
        "data": export_list
    })