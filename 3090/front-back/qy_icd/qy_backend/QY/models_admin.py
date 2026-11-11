# -*- coding: utf-8 -*-
"""病案编码管理后台 —— 数据模型（一期）

设计原则：
1. 只新增表，不改动任何既有业务表，迁移风险仅限 CREATE TABLE；
2. 新表统一命名前缀 ``QY_admin_``，与既有 ``QY_`` 业务表区分；
3. 角色沿用 ``QY_userprofile.role`` 整型字段（不改其 choices，零迁移风险）：
   0 系统管理员 / 1 编码员（既有“普通用户”） / 2 编码组长 / 3 轮值专家。

依据《病案编码管理后台需求方案 V1.0》第 7.2 节表设计。
"""

from django.contrib.auth.models import User
from django.db import models

# --------------------------------------------------------------------------
# 角色常量（与 QY.models.UserProfile.role 对应，仅新增取值，不改既有模型）
# --------------------------------------------------------------------------
ROLE_ADMIN = 0  # 系统管理员：全部功能，含轮值配置、专家目录维护
ROLE_CODER = 1  # 编码员（既有 role=1 普通用户）：可提交疑难病例
ROLE_LEADER = 2  # 编码组长：查看全部统计、导出、疑难病例分配与管理
ROLE_EXPERT = 3  # 轮值专家：查看/处理分配给自己的疑难病例

ROLE_LABELS = {
    ROLE_ADMIN: "系统管理员",
    ROLE_CODER: "编码员",
    ROLE_LEADER: "编码组长",
    ROLE_EXPERT: "轮值专家",
}

# 可进入编码管理后台的角色
BACKEND_ROLES = (ROLE_ADMIN, ROLE_LEADER)


# --------------------------------------------------------------------------
# 一、版本迭代（准确率优化效果）
# --------------------------------------------------------------------------
class CodingVersion(models.Model):
    """编码版本 —— 每次模型或规则集更新登记一个版本"""

    TYPE_DISEASE = "disease"
    TYPE_SURGERY = "surgery"
    TYPE_CHOICES = (
        (TYPE_DISEASE, "疾病编码"),
        (TYPE_SURGERY, "手术编码"),
    )

    version_no = models.CharField(max_length=64, verbose_name="规划版本号")
    version_type = models.CharField(
        max_length=16, choices=TYPE_CHOICES, default=TYPE_DISEASE, verbose_name="版本类型"
    )
    release_date = models.DateField(verbose_name="发布时间")
    model_name = models.CharField(max_length=128, blank=True, null=True, verbose_name="关联模型")
    remark = models.CharField(max_length=255, blank=True, null=True, verbose_name="版本说明")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登记时间")

    class Meta:
        db_table = "QY_admin_coding_version"
        verbose_name = "编码版本"
        verbose_name_plural = verbose_name
        unique_together = ("version_no", "version_type")
        ordering = ["release_date", "id"]

    def __str__(self):
        return f"{self.version_no}({self.get_version_type_display()})"


class AccuracyReview(models.Model):
    """抽检标注 —— 准确率统计的唯一数据来源

    判定口径（一期，严格口径）：完全正确 is_correct=True，部分正确/错误均计 0。
    """

    SEQ_MODEL = "model"
    SEQ_DOCTOR = "doctor"
    SEQ_CHOICES = (
        (SEQ_MODEL, "模型生成"),
        (SEQ_DOCTOR, "医生提交"),
    )

    RESULT_CORRECT = 1
    RESULT_PARTIAL = 2
    RESULT_WRONG = 3
    RESULT_CHOICES = (
        (RESULT_CORRECT, "完全正确"),
        (RESULT_PARTIAL, "部分正确"),
        (RESULT_WRONG, "错误"),
    )

    SOURCE_MANUAL = "manual"
    SOURCE_IMPORT = "import"
    SOURCE_DEMO = "demo"

    version = models.ForeignKey(
        CodingVersion, on_delete=models.CASCADE, related_name="reviews", verbose_name="编码版本"
    )
    sequence = models.CharField(max_length=16, choices=SEQ_CHOICES, verbose_name="数据序列")
    case_identifier = models.CharField(max_length=64, blank=True, null=True, verbose_name="抽检病案标识")
    dept = models.CharField(max_length=64, blank=True, null=True, verbose_name="科室")
    result = models.IntegerField(choices=RESULT_CHOICES, default=RESULT_CORRECT, verbose_name="判定结果")
    is_correct = models.BooleanField(default=True, verbose_name="是否完全正确")
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="accuracy_reviews",
        verbose_name="判定人",
    )
    review_date = models.DateField(verbose_name="判定日期")
    source = models.CharField(max_length=16, default=SOURCE_MANUAL, verbose_name="数据来源")
    remark = models.CharField(max_length=255, blank=True, null=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="录入时间")

    class Meta:
        db_table = "QY_admin_accuracy_review"
        verbose_name = "抽检标注"
        verbose_name_plural = verbose_name
        ordering = ["review_date", "id"]
        indexes = [
            models.Index(fields=["version", "sequence"], name="idx_acc_ver_seq"),
            models.Index(fields=["dept", "review_date"], name="idx_acc_dept_date"),
        ]

    def save(self, *args, **kwargs):
        self.is_correct = self.result == self.RESULT_CORRECT
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.version.version_no}-{self.sequence}-{self.result}"


# --------------------------------------------------------------------------
# 二、疑难病例讨论
# --------------------------------------------------------------------------
class Department(models.Model):
    """科室字典（用于筛选项与专家擅长领域匹配）"""

    name = models.CharField(max_length=64, unique=True, verbose_name="科室名称")
    code = models.CharField(max_length=32, blank=True, null=True, verbose_name="科室编码")
    sort = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "QY_admin_department"
        verbose_name = "科室字典"
        verbose_name_plural = verbose_name
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name


class Expert(models.Model):
    """专家目录 —— 轮值排班与病例分配的候选池"""

    TITLE_CHOICES = (
        ("主任医师", "主任医师"),
        ("副主任医师", "副主任医师"),
        ("主治医师", "主治医师"),
        ("住院医师", "住院医师"),
    )

    name = models.CharField(max_length=64, verbose_name="姓名")
    title = models.CharField(max_length=32, choices=TITLE_CHOICES, default="副主任医师", verbose_name="职称")
    dept_tags = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="擅长领域",
        help_text="多个领域用中文逗号或英文逗号分隔，如：心内科,创伤骨科",
    )
    join_rotation = models.BooleanField(default=True, verbose_name="是否参加排班")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="expert_profiles",
        verbose_name="关联账号",
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="联系电话")
    last_assigned_at = models.DateTimeField(null=True, blank=True, verbose_name="上次分配时间")
    is_active = models.BooleanField(default=True, verbose_name="是否在职")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "QY_admin_expert"
        verbose_name = "专家目录"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    @property
    def tag_list(self):
        raw = (self.dept_tags or "").replace("，", ",")
        return [t.strip() for t in raw.split(",") if t.strip()]

    def __str__(self):
        return f"{self.name}({self.title})"


class RotationConfig(models.Model):
    """轮值配置 —— 医院 + 每周排班日 + 生效区间"""

    WEEKDAY_CHOICES = (
        (1, "周一"), (2, "周二"), (3, "周三"), (4, "周四"),
        (5, "周五"), (6, "周六"), (7, "周日"),
    )

    hospital = models.CharField(max_length=128, default="主院区", verbose_name="轮值医院")
    weekdays = models.CharField(
        max_length=32, verbose_name="轮值排班",
        help_text="每周轮值日，如 1,3,5 表示每周一、周三、周五",
    )
    start_date = models.DateField(verbose_name="生效开始")
    end_date = models.DateField(verbose_name="生效结束")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "QY_admin_rotation_config"
        verbose_name = "轮值配置"
        verbose_name_plural = verbose_name
        ordering = ["-start_date", "-id"]

    @property
    def weekday_list(self):
        return [int(x) for x in (self.weekdays or "").split(",") if x.strip().isdigit()]

    def __str__(self):
        return f"{self.hospital} {self.weekdays} {self.start_date}~{self.end_date}"


class DifficultCase(models.Model):
    """疑难病例"""

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_FEEDBACK = "feedback"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "待分配"),
        (STATUS_PROCESSING, "处理中"),
        (STATUS_FEEDBACK, "已反馈"),
        (STATUS_CLOSED, "已关闭"),
    )

    case_identifier = models.CharField(max_length=64, blank=True, null=True, verbose_name="病案标识号")
    patient_no = models.CharField(max_length=32, blank=True, null=True, verbose_name="患者ID/住院号")
    patient_name = models.CharField(max_length=64, blank=True, null=True, verbose_name="患者姓名")
    dept = models.CharField(max_length=64, blank=True, null=True, verbose_name="提交科室")
    doctor = models.CharField(max_length=64, blank=True, null=True, verbose_name="提交医师")
    question = models.TextField(blank=True, null=True, verbose_name="疑难描述")
    diagnosis_snapshot = models.TextField(blank=True, null=True, verbose_name="诊断编码快照(JSON)")
    surgery_snapshot = models.TextField(blank=True, null=True, verbose_name="手术编码快照(JSON)")
    source_record_id = models.IntegerField(null=True, blank=True, verbose_name="关联病案记录ID")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="状态"
    )
    submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_cases",
        verbose_name="提交人",
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    expert = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases",
        verbose_name="分配专家",
    )
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_cases",
        verbose_name="受理账号",
    )
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name="分配时间")
    feedback_at = models.DateTimeField(null=True, blank=True, verbose_name="反馈时间")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="关闭时间")
    remind_count = models.IntegerField(default=0, verbose_name="催办次数")
    last_remind_at = models.DateTimeField(null=True, blank=True, verbose_name="最近催办时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "QY_admin_difficult_case"
        verbose_name = "疑难病例"
        verbose_name_plural = verbose_name
        ordering = ["-submitted_at", "-id"]
        indexes = [
            models.Index(fields=["status", "submitted_at"], name="idx_case_status_time"),
            models.Index(fields=["dept"], name="idx_case_dept"),
            models.Index(fields=["patient_no"], name="idx_case_patient"),
        ]

    def __str__(self):
        return f"#{self.pk} {self.patient_no or ''} {self.get_status_display()}"


class CaseAssignment(models.Model):
    """病例分配与反馈记录"""

    STATUS_ASSIGNED = "assigned"
    STATUS_FEEDBACK = "feedback"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_ASSIGNED, "已分配"),
        (STATUS_FEEDBACK, "已反馈"),
        (STATUS_CLOSED, "已关闭"),
    )

    case = models.ForeignKey(
        DifficultCase, on_delete=models.CASCADE, related_name="assignments", verbose_name="病例"
    )
    expert = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments",
        verbose_name="专家",
    )
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="case_assignments",
        verbose_name="受理账号",
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="指派人"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="分配时间")
    feedback = models.TextField(blank=True, null=True, verbose_name="反馈内容")
    feedback_at = models.DateTimeField(null=True, blank=True, verbose_name="反馈时间")
    is_auto = models.BooleanField(default=False, verbose_name="是否自动分配")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ASSIGNED, verbose_name="状态")

    class Meta:
        db_table = "QY_admin_case_assignment"
        verbose_name = "病例分配"
        verbose_name_plural = verbose_name
        ordering = ["-assigned_at", "-id"]

    def __str__(self):
        return f"case={self.case_id} expert={self.expert_id}"


class CaseLog(models.Model):
    """病例流转日志（谁在何时做了什么，全程可追溯）"""

    case = models.ForeignKey(
        DifficultCase, on_delete=models.CASCADE, related_name="logs", verbose_name="病例"
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="case_logs",
        verbose_name="操作人",
    )
    actor_name = models.CharField(max_length=64, blank=True, null=True, verbose_name="操作人姓名")
    action = models.CharField(max_length=32, verbose_name="动作")
    detail = models.TextField(blank=True, null=True, verbose_name="详情")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="时间")

    class Meta:
        db_table = "QY_admin_case_log"
        verbose_name = "病例流转日志"
        verbose_name_plural = verbose_name
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"case={self.case_id} {self.action}"
