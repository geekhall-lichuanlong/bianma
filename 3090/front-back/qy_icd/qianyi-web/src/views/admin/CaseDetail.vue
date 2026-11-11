<template>
  <div class="case-detail" v-loading="loading">
    <div class="detail-head">
      <el-button link @click="$router.push('/admin/difficult-cases')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回列表</span>
      </el-button>
      <div class="head-main">
        <span class="patient">{{ detail.patientNo || '—' }}</span>
        <el-tag :type="statusType(detail.status)" size="small">{{ detail.statusName }}</el-tag>
        <span class="muted">提交于 {{ detail.submittedAt || '—' }}</span>
      </div>
      <div class="head-actions">
        <el-button size="small" @click="openAssign">指派 / 改派</el-button>
        <el-button size="small" :disabled="detail.status === 'closed'" @click="remind">
          催办（{{ detail.remindCount || 0 }}）
        </el-button>
        <el-button
          v-if="detail.status !== 'closed'"
          size="small"
          type="primary"
          plain
          @click="closeCase"
          >关闭病例</el-button
        >
        <el-button v-else size="small" @click="reopenCase">重新打开</el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :span="14">
        <el-card shadow="never" class="card">
          <template #header><span class="card-title">病例基本信息</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="患者ID">{{ detail.patientNo || '—' }}</el-descriptions-item>
            <el-descriptions-item label="患者姓名">{{ detail.patientName || '—' }}</el-descriptions-item>
            <el-descriptions-item label="病案标识">{{ detail.caseIdentifier || '—' }}</el-descriptions-item>
            <el-descriptions-item label="提交科室">{{ detail.dept || '—' }}</el-descriptions-item>
            <el-descriptions-item label="提交医师">{{ detail.doctor || '—' }}</el-descriptions-item>
            <el-descriptions-item label="提交人">
              {{ detail.submitterName || detail.submitter || '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="分配专家">
              <span v-if="detail.expertName">
                {{ detail.expertName }}（{{ detail.expertTitle }}）
              </span>
              <span v-else class="muted">待分配</span>
            </el-descriptions-item>
            <el-descriptions-item label="分配时间">{{ detail.assignedAt || '—' }}</el-descriptions-item>
            <el-descriptions-item label="反馈时间">{{ detail.feedbackAt || '—' }}</el-descriptions-item>
            <el-descriptions-item label="关闭时间">{{ detail.closedAt || '—' }}</el-descriptions-item>
          </el-descriptions>

          <div class="block">
            <div class="block-title">疑难描述</div>
            <div class="question">{{ detail.question || '—' }}</div>
          </div>

          <div class="block">
            <div class="block-title">原始编码结果快照</div>
            <pre class="snapshot">{{
              prettySnapshot(detail.diagnosisSnapshot) || '暂无编码快照'
            }}</pre>
            <pre v-if="detail.surgerySnapshot" class="snapshot">{{
              prettySnapshot(detail.surgerySnapshot)
            }}</pre>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="card">
          <template #header><span class="card-title">专家讨论与反馈</span></template>
          <div class="feedback-list">
            <div v-if="!feedbacks.length" class="muted empty">暂无反馈，可在下方录入</div>
            <div v-for="f in feedbacks" :key="f.id" class="feedback-item">
              <div class="feedback-head">
                <span class="who">{{ f.expertName || '专家' }}</span>
                <span class="muted">{{ f.feedbackAt || f.assignedAt }}</span>
                <el-tag v-if="f.isAuto" size="small" type="info" effect="plain">自动分配</el-tag>
              </div>
              <div class="feedback-body">{{ f.feedback }}</div>
            </div>
          </div>

          <el-divider content-position="left">录入反馈</el-divider>
          <el-input
            v-model="feedbackText"
            type="textarea"
            :rows="4"
            placeholder="填写专家讨论意见（可多轮追加）"
          />
          <div class="feedback-foot">
            <el-button type="primary" :loading="submitting" @click="submitFeedback">
              提交反馈
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="card">
      <template #header><span class="card-title">流转日志</span></template>
      <el-timeline>
        <el-timeline-item
          v-for="lg in detail.logs || []"
          :key="lg.id"
          :timestamp="lg.createdAt"
          placement="top"
          :type="logType(lg.action)"
        >
          <div class="log-line">
            <b>{{ lg.action }}</b>
            <span class="muted">· {{ lg.actorName || '系统' }}</span>
          </div>
          <div v-if="lg.detail" class="log-detail">{{ lg.detail }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-dialog v-model="assignVisible" title="指派专家" width="480px">
      <el-form label-width="90px">
        <el-form-item label="选择专家" required>
          <el-select v-model="assignExpertId" filterable style="width: 100%">
            <el-option
              v-for="e in experts"
              :key="e.id"
              :label="`${e.name}（${e.title}）${e.deptTags.length ? ' · ' + e.deptTags.join('/') : ''}`"
              :value="e.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="指派说明">
          <el-input v-model="assignRemark" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAssign">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiAdminCaseAction,
  apiAdminCaseAssign,
  apiAdminCaseDetail,
  apiAdminCaseFilterOptions,
  apiAdminCaseFeedback,
  apiAdminCaseRemind,
} from '@/api/admin'

const route = useRoute()
const loading = ref(false)
const submitting = ref(false)
const assignVisible = ref(false)
const detail = ref({})
const experts = ref([])
const feedbackText = ref('')
const assignExpertId = ref(null)
const assignRemark = ref('')

const feedbacks = ref([])

const statusType = (s) =>
  ({ pending: 'info', processing: 'warning', feedback: 'primary', closed: 'success' })[s] || 'info'

const logType = (action) =>
  ({ 提交病例: 'primary', 自动分配: 'success', 指派专家: 'success', 录入反馈: 'warning', 关闭病例: 'info' })[
    action
  ] || ''

const prettySnapshot = (raw) => {
  if (!raw) return ''
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch (e) {
    return raw
  }
}

const loadDetail = async () => {
  loading.value = true
  try {
    const { data } = await apiAdminCaseDetail(route.params.id)
    if (data.code === 200) {
      detail.value = data.data
      feedbacks.value = (data.data.assignments || []).filter((a) => a.feedback)
    } else {
      ElMessage.error(data.msg || '加载失败')
    }
  } finally {
    loading.value = false
  }
}

const loadExperts = async () => {
  const { data } = await apiAdminCaseFilterOptions()
  if (data.code === 200) experts.value = data.data.experts || []
}

const openAssign = () => {
  assignExpertId.value = detail.value.expertId || null
  assignRemark.value = ''
  assignVisible.value = true
}

const submitAssign = async () => {
  if (!assignExpertId.value) {
    ElMessage.warning('请选择专家')
    return
  }
  submitting.value = true
  try {
    const { data } = await apiAdminCaseAssign(detail.value.id, {
      expertId: assignExpertId.value,
      remark: assignRemark.value,
    })
    if (data.code === 200) {
      ElMessage.success(data.msg || '指派成功')
      assignVisible.value = false
      await loadDetail()
    } else {
      ElMessage.error(data.msg || '指派失败')
    }
  } finally {
    submitting.value = false
  }
}

const submitFeedback = async () => {
  if (!feedbackText.value.trim()) {
    ElMessage.warning('请填写反馈内容')
    return
  }
  submitting.value = true
  try {
    const { data } = await apiAdminCaseFeedback(detail.value.id, {
      content: feedbackText.value.trim(),
    })
    if (data.code === 200) {
      ElMessage.success('反馈已录入')
      feedbackText.value = ''
      await loadDetail()
    } else {
      ElMessage.error(data.msg || '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

const closeCase = () => {
  ElMessageBox.confirm('确认关闭该病例？关闭后流程结束并归档。', '关闭确认', {
    type: 'warning',
    confirmButtonText: '确定关闭',
    cancelButtonText: '取消',
  })
    .then(async () => {
      const { data } = await apiAdminCaseAction(detail.value.id, { action: 'close' })
      if (data.code === 200) {
        ElMessage.success('病例已关闭')
        await loadDetail()
      }
    })
    .catch(() => {})
}

const reopenCase = async () => {
  const { data } = await apiAdminCaseAction(detail.value.id, { action: 'reopen' })
  if (data.code === 200) {
    ElMessage.success('已重新打开')
    await loadDetail()
  }
}

const remind = async () => {
  const { data } = await apiAdminCaseRemind(detail.value.id)
  if (data.code === 200) {
    ElMessage.success(data.msg || '已催办')
    await loadDetail()
  }
}

onMounted(async () => {
  await Promise.all([loadDetail(), loadExperts()])
})
</script>

<style scoped>
.case-detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-head {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border: 1px solid #e6eaf0;
  border-radius: 8px;
  padding: 12px 16px;
}

.head-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.patient {
  font-size: 17px;
  font-weight: 600;
  color: #1f2d3d;
}

.head-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.card {
  border: 1px solid #e6eaf0;
  margin-bottom: 14px;
}

.card-title {
  font-weight: 600;
  color: #1f2d3d;
}

.block {
  margin-top: 16px;
}

.block-title {
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #1565c0;
}

.question {
  font-size: 14px;
  color: #303133;
  line-height: 1.8;
  background: #f7f9fc;
  border-radius: 6px;
  padding: 12px 14px;
}

.snapshot {
  background: #1f2d3d;
  color: #d7e2f1;
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 12.5px;
  line-height: 1.7;
  overflow-x: auto;
  margin-top: 8px;
}

.feedback-list {
  max-height: 320px;
  overflow-y: auto;
}

.feedback-item {
  padding: 10px 0;
  border-bottom: 1px dashed #eef1f5;
}

.feedback-item:last-child {
  border-bottom: none;
}

.feedback-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.who {
  font-weight: 600;
  color: #1565c0;
  font-size: 13px;
}

.feedback-body {
  font-size: 13.5px;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}

.feedback-foot {
  margin-top: 10px;
  text-align: right;
}

.log-line {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.log-detail {
  font-size: 13px;
  color: #606266;
  margin-top: 4px;
  line-height: 1.7;
}

.muted {
  color: #909399;
  font-size: 12px;
}

.empty {
  font-size: 13px;
  padding: 8px 0;
}
</style>
