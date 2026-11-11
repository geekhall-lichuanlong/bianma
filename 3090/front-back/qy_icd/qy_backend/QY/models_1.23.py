from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime
import uuid

# Create your models here.

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


# 创建一个特定PDF的OCR数据识别的数据保存
class PDFOCRData(models.Model):
    # 基础
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 文档信息
    filename = models.CharField("文件名", max_length=255)
    file_path = models.CharField("文件地址", max_length=1024)
    raw_text = models.TextField("原始文本", blank=True, null=True)

    # 结构化字段
    personal_history = models.TextField("个人史", blank=True, null=True)
    chief_complaint = models.TextField("主诉", blank=True, null=True)
    inpatient_no = models.CharField("住院号", max_length=100, blank=True, null=True)
    admission_status = models.TextField("入院情况", blank=True, null=True)
    admission_diagnosis = models.TextField("入院诊断", blank=True, null=True)
    discharge_diagnosis = models.TextField("出院诊断", blank=True, null=True)
    marital_history = models.TextField("婚姻史", blank=True, null=True)
    family_history = models.TextField("家族史", blank=True, null=True)
    imaging_opinion = models.TextField("影像学意见", blank=True, null=True)
    operation_name = models.CharField("手术名称", max_length=255, blank=True, null=True)
    operation_course = models.TextField("手术经过", blank=True, null=True)
    past_history = models.TextField("既往史", blank=True, null=True)
    intraoperative_diagnosis = models.TextField("术中诊断", blank=True, null=True)
    present_illness = models.TextField("现病史", blank=True, null=True)
    case_identifier = models.CharField("病案标识", max_length=255, blank=True, null=True)
    course_record = models.TextField("病程记录", blank=True, null=True)
    treatment_course = models.TextField("诊疗经过", blank=True, null=True)
    ultrasound_impression = models.TextField("超声印象", blank=True, null=True)
    ultrasound_hint = models.TextField("超声提示", blank=True, null=True)

    class Meta:
        verbose_name = "PDF OCR 数据"
        verbose_name_plural = "PDF OCR 数据"

    def __str__(self):
        return f"{self.filename}"

class V_Patient_Surgery(models.Model):
    """
    手术表 Surgery
    对应表结构：
    - id            主键ID，自增
    - case_id       病案标识号，varchar(50)
    - surgery_seq   手术序号，主手术为1
    - surgery_code  手术编码，varchar(50)
    - surgery_name  手术名称，varchar(200)
    """

    # id 字段 Django 会自动生成：AutoField(primary_key=True)

    case_id = models.CharField(
        max_length=50,
        verbose_name="病案标识号",
        help_text="住院号/病案号",
    )
    surgery_seq = models.IntegerField(
        verbose_name="手术序号",
        help_text="手术顺序号，主手术为1",
    )
    surgery_code = models.CharField(
        max_length=50,
        verbose_name="手术编码",
        help_text="关联手术编码字典库",
    )
    surgery_name = models.CharField(
        max_length=200,
        verbose_name="手术名称",
        help_text="关联手术名称字典库",
    )

    # 新增字段：模型回复生成时间
    model_response_time = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="模型回复时间",
        help_text="记录模型生成该回复的时间点"
    )

    class Meta:
        verbose_name = "手术"
        verbose_name_plural = "手术"
        ordering = ["case_id", "surgery_seq", "id"]

    def __str__(self):
        # 带上编码信息，方便区分
        return f"{self.case_id}-{self.surgery_seq}-{self.surgery_code}-{self.surgery_name}"

class V_Patient_Diagnosis(models.Model):
    """
    诊断表 Diagnosis
    对应表结构：
    - id         主键ID，自增
    - case_id    病案标识号，varchar(50)
    - diag_type  诊断类型，varchar(20)，枚举：出院诊断 / 损伤中毒 / 病理诊断
    - diag_seq   诊断序号，int，主诊断=1
    - diag_code  诊断编码，varchar(50)
    - diag_name  诊断名称，varchar(200)
    """

    class DiagnosisType(models.TextChoices):
        DISCHARGE = "出院诊断", "出院诊断"
        INJURY_POISON = "损伤中毒", "损伤中毒"
        PATHOLOGICAL = "病理诊断", "病理诊断"
    
    case_id = models.CharField(
        max_length=50,
        verbose_name="病案标识号",
        help_text="住院号/病案号",
    )
    diag_type = models.CharField(
        max_length=20,
        choices=DiagnosisType.choices,
        verbose_name="诊断类型",
        help_text="枚举：出院诊断 / 损伤中毒 / 病理诊断",
    )
    diag_seq = models.IntegerField(
        verbose_name="诊断序号",
        help_text="诊断顺序号，主诊断=1",
    )
    diag_code = models.CharField(
        max_length=50,
        verbose_name="诊断编码",
        help_text="关联诊断编码字典库",
    )
    diag_name = models.CharField(
        max_length=200,
        verbose_name="诊断名称",
        help_text="关联诊断名称字典库",
    )

    model_response_time = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="模型回复时间",
        help_text="记录模型生成该回复的时间点"
    )

    class Meta:
        verbose_name = "诊断"
        verbose_name_plural = "诊断"
        ordering = ["case_id", "diag_type", "diag_seq"]

    def __str__(self):
        return f"{self.case_id}-{self.diag_type}-{self.diag_seq}-{self.diag_code}-{self.diag_name}"
    
# 用户信息
class UserProfile(models.Model):
    """
    千医用户扩展信息：
    - role: 管理员0 / 普通用户1
    - real_name: 真实姓名
    - phone: 手机号
    - status: 0 禁用 / 1 启用
    """
    ROLE_ADMIN = 0
    ROLE_USER = 1
    ROLE_CHOICES = (
        (ROLE_ADMIN, "管理员"),
        (ROLE_USER, "普通用户"),
    )

    STATUS_DISABLED = 0
    STATUS_ENABLED = 1
    STATUS_CHOICES = (
        (STATUS_DISABLED, "禁用"),
        (STATUS_ENABLED, "启用"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.IntegerField(choices=ROLE_CHOICES, default=ROLE_USER)
    real_name = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.real_name or self.user.username

# ==========================================
# 大模型聊天记录相关表
# ==========================================
class ChatSessions(models.Model):
    """
    会话表 ChatSessions
    存储用户与大模型的会话上下文容器
    """
    class ChatMode(models.TextChoices):
        CODING = "coding", "Coding"
        KNOWLEDGE = "knowledge", "Knowledge"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="chat_sessions",
        verbose_name="用户",
        db_index=True
    )
    title = models.CharField(
        "会话标题", 
        max_length=255, 
        blank=True, 
        null=True,
        help_text="侧边栏标题 (支持自动生成或手动修改)"
    )
    chat_mode = models.CharField(
        "消息类型",
        max_length=20,
        choices=ChatMode.choices,
        default=ChatMode.KNOWLEDGE,
        help_text="消息类型：coding 或者 knowledge"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("最后活跃时间", auto_now=True)

    class Meta:
        verbose_name = "聊天会话"
        verbose_name_plural = "聊天会话"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or str(self.id)


class ChatMessages(models.Model):
    """
    消息表 ChatMessages
    存储会话中的每一条具体的问答记录
    """
    session = models.ForeignKey(
        ChatSessions, 
        on_delete=models.CASCADE, 
        related_name="messages",
        verbose_name="所属会话",
        db_index=True
    )
    message_order = models.IntegerField(
        "消息序号", 
        help_text="一次会话中的所有消息序号"
    )
    # 注意：使用 JSONField 需要数据库支持（如 PostgreSQL, MySQL 5.7+, SQLite 3.9+）
    message = models.JSONField(
        "消息正文", 
        help_text="消息正文，一个content表示一个完整的消息"
    )
    created_at = models.DateTimeField("发送时间", auto_now_add=True)

    class Meta:
        verbose_name = "会话消息"
        verbose_name_plural = "会话消息"
        ordering = ["session", "message_order"]

    def __str__(self):
        return f"Session: {self.session_id} - Order: {self.message_order}"


class Feedback(models.Model):
    """
    消息反馈表 Feedback
    用户对大模型生成的数据（诊断、手术等）的点赞或点踩反馈
    """
    class FeedbackType(models.TextChoices):
        LIKE = "like", "点赞"
        DISLIKE = "dislike", "点踩"
        COMMENT = "comment", "总体评价"

    class CategoryType(models.IntegerChoices):
        DIAGNOSIS = 0, "诊断"
        SURGERY = 1, "手术"

    message = models.ForeignKey(
        ChatMessages, 
        on_delete=models.CASCADE, 
        related_name="feedbacks",
        verbose_name="关联消息"
    )
    category = models.IntegerField(
        "目标类型",
        choices=CategoryType.choices,
        default=CategoryType.DIAGNOSIS,
        help_text="0表示诊断、1表示手术"
    )
    row_id = models.IntegerField(
        "数据行ID", 
        help_text="某条消息中的诊断、手术数据行id"
    )
    type = models.CharField(
        "反馈类型",
        max_length=20,
        choices=FeedbackType.choices,
        help_text="对于此数据行的反馈类型：like 或者 dislike"
    )
    reason = models.TextField("反馈标签",blank=True,null=True,)
    remark = models.TextField("反馈内容", blank=True, null=True)
    timestamp = models.DateTimeField("反馈时间", auto_now_add=True)

    class Meta:
        verbose_name = "消息反馈"
        verbose_name_plural = "消息反馈"
        ordering = ["-timestamp"]
        # [新增] 联合唯一索引，确保同一条消息的同一行数据，同一类型（诊断/手术）下只能有一条记录
        # 注意：这里假设 message 已经隐含了 user 信息。如果不隐含，需要确保业务逻辑控制权限。
        unique_together = [("message", "category", "row_id")] 

    def __str__(self):
        return f"Msg: {self.message_id} - Row: {self.row_id} - {self.type}"