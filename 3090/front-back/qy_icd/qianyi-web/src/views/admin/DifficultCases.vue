<template>
  <div class="difficult-cases">
    <!-- 状态概览 -->
    <div class="status-row">
      <div
        v-for="s in statusCards"
        :key="s.value"
        class="status-card"
        :class="[s.value, { active: query.status === s.value }]"
        @click="toggleStatus(s.value)"
      >
        <div class="status-name">{{ s.label }}</div>
        <div class="status-num">{{ statusCounts[s.value] || 0 }}</div>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card shadow="never" class="card">
      <el-form :model="query" inline class="filter-form">
        <el-form-item label="患者ID">
          <el-input
            v-model="query.patientNo"
            placeholder="住院号 / 病案标识"
            clearable
            style="width: 170px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="科室">
          <el-select v-model="query.dept" clearable filterable placeholder="全部" style="width: 170px">
            <el-option v-for="d in options.depts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交医师">
          <el-select v-model="query.doctor" clearable filterable placeholder="全部" style="width: 140px">
            <el-option v-for="d in options.doctors" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交人">
          <el-select v-model="query.submitter" clearable filterable placeholder="全部" style="width: 140px">
            <el-option
              v-for="s in options.submitters"
              :key="s.username"
              :label="s.name"
              :value="s.username"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="提交时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width: 130px">
            <el-option
              v-for="s in options.statuses"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="action-bar">
        <el-button type="primary" plain @click="openCaseDialog">
          <el-icon><Plus /></el-icon>
          <span>提交疑难病例</span>
        </el-button>
        <el-button @click="runAutoAssign" :loading="assigning">
          <el-icon><MagicStick /></el-icon>
          <span>自动分配待处理</span>
        </el-button>
        <el-button @click="rotationVisible = true">
          <el-icon><Calendar /></el-icon>
          <span>轮值安排</span>
        </el-button>
        <span class="total-tip">共 {{ total }} 条数据</span>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never" class="card">
      <el-table :data="list" border v-loading="loading" @row-dblclick="goDetail">
        <el-table-column prop="patientNo" label="患者ID" width="120" />
        <el-table-column label="患者摘要" width="130">
          <template #default="{ row }">
            <span>{{ row.patientName || '—' }}</span>
            <el-tag v-if="row.patientName" size="small" type="info" effect="plain" class="mask-tag">
              已脱敏
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dept" label="提交科室" width="150" />
        <el-table-column prop="doctor" label="提交医师" width="100" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.statusName }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="170" />
        <el-table-column label="分配专家" width="140">
          <template #default="{ row }">
            <span v-if="row.expertName">{{ row.expertName }}（{{ row.expertTitle }}）</span>
            <span v-else class="muted">待分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="submitterName" label="提交人" width="110">
          <template #default="{ row }">{{ row.submitterName || row.submitter }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="goDetail(row)">查看详情</el-button>
            <el-button size="small" link @click="openAssignDialog(row)">指派</el-button>
            <el-button
              size="small"
              link
              :disabled="row.status === 'closed'"
              @click="remind(row)"
              >催办</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- 指派弹窗 -->
    <el-dialog v-model="assignVisible" title="指派专家" width="480px">
      <el-form label-width="90px">
        <el-form-item label="病例">
          <span>{{ currentCase.patientNo }} · {{ currentCase.dept }}</span>
        </el-form-item>
        <el-form-item label="选择专家" required>
          <el-select v-model="assignExpertId" filterable style="width: 100%">
            <el-option
              v-for="e in options.experts"
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
        <el-button type="primary" :loading="assigning" @click="submitAssign">确定指派</el-button>
      </template>
    </el-dialog>

    <!-- 提交疑难病例 -->
    <el-dialog v-model="caseDialog" title="提交疑难病例" width="620px">
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="患者ID" required>
          <el-input v-model="caseForm.patientNo" placeholder="住院号" />
        </el-form-item>
        <el-form-item label="患者姓名">
          <el-input v-model="caseForm.patientName" placeholder="列表页将自动脱敏展示" />
        </el-form-item>
        <el-form-item label="提交科室" required>
          <el-select v-model="caseForm.dept" filterable style="width: 100%">
            <el-option v-for="d in options.depts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交医师">
          <el-input v-model="caseForm.doctor" />
        </el-form-item>
        <el-form-item label="病案标识">
          <el-input v-model="caseForm.caseIdentifier" placeholder="如 396183_2026090" />
        </el-form-item>
        <el-form-item label="疑难描述" required>
          <el-input v-model="caseForm.question" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="编码快照">
          <el-input
            v-model="caseForm.diagnosisSnapshot"
            type="textarea"
            :rows="3"
            placeholder='可选，JSON 文本，如 {"主诊断":"C20.x00 直肠恶性肿瘤"}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCase">提交</el-button>
      </template>
    </el-dialog>

    <RotationDialog
      v-model="rotationVisible"
      :can-manage="canManage"
      @updated="loadList"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  apiAdminCaseAssign,
  apiAdminCaseAutoAssign,
  apiAdminCaseFilterOptions,
  apiAdminCaseRemind,
  apiAdminCases,
  apiAdminCreateCase,
  apiAdminMe,
} from '@/api/admin'
import RotationDialog from './components/RotationDialog.vue'

const router = useRouter()

const loading = ref(false)
const assigning = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const statusCounts = ref({})
const rotationVisible = ref(false)
const assignVisible = ref(false)
const caseDialog = ref(false)
const canManage = ref(false)
const dateRange = ref([])

const currentCase = reactive({})
const assignExpertId = ref(null)
const assignRemark = ref('')

const query = reactive({
  patientNo: '',
  dept: '',
  doctor: '',
  submitter: '',
  status: '',
  page: 1,
  pageSize: 10,
})

const options = reactive({ depts: [], doctors: [], submitters: [], experts: [], statuses: [] })

const statusCards = [
  { value: 'pending', label: '待分配' },
  { value: 'processing', label: '处理中' },
  { value: 'feedback', label: '已反馈' },
  { value: 'closed', label: '已关闭' },
]

const caseForm = reactive({
  patientNo: '',
  patientName: '',
  dept: '',
  doctor: '',
  caseIdentifier: '',
  question: '',
  diagnosisSnapshot: '',
})

const statusType = (s) =>
  ({ pending: 'info', processing: 'warning', feedback: 'primary', closed: 'success' })[s] || 'info'

const loadList = async () => {
  loading.value = true
  try {
    const params = {
      patientNo: query.patientNo,
      dept: query.dept,
      doctor: query.doctor,
      submitter: query.submitter,
      status: query.status,
      page: query.page,
      page_size: query.pageSize,
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    const { data } = await apiAdminCases(params)
    if (data.code === 200) {
      list.value = data.data.list || []
      total.value = data.data.total || 0
      statusCounts.value = data.data.statusCounts || {}
    } else {
      ElMessage.error(data.msg || '加载失败')
    }
  } catch (e) {
    ElMessage.error('加载疑难病例失败')
  } finally {
    loading.value = false
  }
}

const loadOptions = async () => {
  const { data } = await apiAdminCaseFilterOptions()
  if (data.code === 200) {
    options.depts = data.data.depts || []
    options.doctors = data.data.doctors || []
    options.submitters = data.data.submitters || []
    options.experts = data.data.experts || []
    options.statuses = data.data.statuses || []
  }
}

const handleSearch = () => {
  query.page = 1
  loadList()
}

const handleReset = () => {
  query.patientNo = ''
  query.dept = ''
  query.doctor = ''
  query.submitter = ''
  query.status = ''
  query.page = 1
  dateRange.value = []
  loadList()
}

const toggleStatus = (s) => {
  query.status = query.status === s ? '' : s
  handleSearch()
}

const goDetail = (row) => router.push(`/admin/cases/${row.id}`)

const openAssignDialog = (row) => {
  Object.assign(currentCase, row)
  assignExpertId.value = row.expertId || null
  assignRemark.value = ''
  assignVisible.value = true
}

const submitAssign = async () => {
  if (!assignExpertId.value) {
    ElMessage.warning('请选择专家')
    return
  }
  assigning.value = true
  try {
    const { data } = await apiAdminCaseAssign(currentCase.id, {
      expertId: assignExpertId.value,
      remark: assignRemark.value,
    })
    if (data.code === 200) {
      ElMessage.success(data.msg || '指派成功')
      assignVisible.value = false
      await loadList()
    } else {
      ElMessage.error(data.msg || '指派失败')
    }
  } finally {
    assigning.value = false
  }
}

const runAutoAssign = async () => {
  assigning.value = true
  try {
    const { data } = await apiAdminCaseAutoAssign({})
    if (data.code === 200) {
      if (data.data.assigned) ElMessage.success(data.msg)
      else ElMessage.warning(data.msg)
      await loadList()
    }
  } finally {
    assigning.value = false
  }
}

const remind = async (row) => {
  const { data } = await apiAdminCaseRemind(row.id)
  if (data.code === 200) {
    ElMessage.success(data.msg || '已催办')
    await loadList()
  }
}

const openCaseDialog = () => {
  Object.assign(caseForm, {
    patientNo: '',
    patientName: '',
    dept: '',
    doctor: '',
    caseIdentifier: '',
    question: '',
    diagnosisSnapshot: '',
  })
  caseDialog.value = true
}

const submitCase = async () => {
  if (!caseForm.patientNo.trim()) {
    ElMessage.warning('请填写患者ID')
    return
  }
  if (!caseForm.dept) {
    ElMessage.warning('请选择提交科室')
    return
  }
  if (!caseForm.question.trim()) {
    ElMessage.warning('请填写疑难描述')
    return
  }
  submitting.value = true
  try {
    const { data } = await apiAdminCreateCase({ ...caseForm })
    if (data.code === 200) {
      ElMessage.success(data.msg || '提交成功')
      caseDialog.value = false
      await loadList()
    } else {
      ElMessage.error(data.msg || '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

watch(dateRange, () => {
  query.page = 1
})

onMounted(async () => {
  try {
    const { data } = await apiAdminMe()
    if (data.code === 200) canManage.value = !!data.data.permissions?.canManageRotation
  } catch (e) {
    /* ignore */
  }
  await Promise.all([loadOptions(), loadList()])
})
</script>

<style scoped>
.difficult-cases {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.status-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.status-card {
  background: #fff;
  border: 1px solid #e6eaf0;
  border-radius: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.status-card:hover {
  border-color: #b6c6dd;
}

.status-card.active {
  border-color: #1565c0;
  box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.12);
}

.status-name {
  font-size: 13px;
  color: #7a8699;
}

.status-num {
  font-size: 24px;
  font-weight: 700;
  color: #1f2d3d;
  margin-top: 4px;
}

.status-card.pending .status-num {
  color: #909399;
}
.status-card.processing .status-num {
  color: #e6a23c;
}
.status-card.feedback .status-num {
  color: #1565c0;
}
.status-card.closed .status-num {
  color: #2e9e5b;
}

.card {
  border: 1px solid #e6eaf0;
}

.filter-form {
  row-gap: 4px;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  padding-top: 12px;
  border-top: 1px dashed #e6eaf0;
}

.total-tip {
  margin-left: auto;
  font-size: 13px;
  color: #909399;
}

.pagination {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.muted {
  color: #909399;
  font-size: 12px;
}

.mask-tag {
  margin-left: 4px;
  transform: scale(0.85);
}
</style>
