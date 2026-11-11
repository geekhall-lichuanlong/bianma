<template>
  <el-dialog
    :model-value="modelValue"
    title="轮值安排"
    width="900px"
    top="6vh"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @open="handleOpen"
  >
    <el-tabs v-model="activeTab">
      <!-- ============ A. 医院轮值配置 ============ -->
      <el-tab-pane label="医院轮值配置" name="rotation">
        <el-alert
          v-if="!canManage"
          type="info"
          :closable="false"
          show-icon
          title="当前角色为只读：仅系统管理员可修改轮值配置与专家目录"
          style="margin-bottom: 12px"
        />
        <el-form :model="rotationForm" label-width="96px" class="rotation-form">
          <el-form-item label="轮值医院" required>
            <el-input
              v-model="rotationForm.hospital"
              placeholder="如 主院区 / 东院区"
              style="width: 240px"
              :disabled="!canManage"
            />
          </el-form-item>
          <el-form-item label="轮值排班" required>
            <el-checkbox-group v-model="rotationForm.weekdays" :disabled="!canManage">
              <el-checkbox-button v-for="w in weekdays" :key="w.value" :label="w.value">
                {{ w.label }}
              </el-checkbox-button>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="生效时间" required>
            <el-date-picker
              v-model="rotationForm.range"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :disabled="!canManage"
            />
          </el-form-item>
          <el-form-item>
            <el-button v-if="canManage" type="primary" :loading="saving" @click="submitRotation">
              {{ rotationForm.id ? '更新配置' : '新增配置' }}
            </el-button>
            <el-button v-if="rotationForm.id" @click="resetRotationForm">取消编辑</el-button>
            <el-button type="success" plain :loading="assigning" @click="runAutoAssign">
              立即执行自动分配
            </el-button>
          </el-form-item>
        </el-form>

        <el-divider content-position="left">已配置的轮值期</el-divider>
        <el-table :data="rotations" border size="small" v-loading="loading">
          <el-table-column prop="hospital" label="轮值医院" width="140" />
          <el-table-column label="轮值排班" min-width="200">
            <template #default="{ row }">
              <el-tag
                v-for="n in row.weekdayNames"
                :key="n"
                size="small"
                effect="plain"
                style="margin-right: 6px"
              >
                {{ n }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="生效时间" width="220">
            <template #default="{ row }">{{ row.startDate }} 至 {{ row.endDate }}</template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
                {{ row.isActive ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canManage" size="small" @click="editRotation(row)">编辑</el-button>
              <el-button
                v-if="canManage"
                size="small"
                type="danger"
                @click="removeRotation(row)"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
        <div class="tip">
          规则：病例提交当日命中轮值排班时，在「参加排班 + 擅长领域与病例科室匹配」的专家中，按上次分配时间最早者优先分配 1 名；无匹配时在全体参班专家中轮转；非轮值日提交的病例进入待分配队列。
        </div>
      </el-tab-pane>

      <!-- ============ B. 专家目录维护 ============ -->
      <el-tab-pane :label="`专家目录（${experts.length}）`" name="experts">
        <div class="expert-toolbar">
          <el-button v-if="canManage" type="primary" @click="openExpertDialog()">
            <el-icon><Plus /></el-icon>
            <span>新增专家</span>
          </el-button>
        </div>
        <el-table :data="experts" border size="small" v-loading="loading">
          <el-table-column prop="name" label="姓名" width="110" />
          <el-table-column prop="title" label="职称" width="130" />
          <el-table-column label="擅长领域" min-width="240">
            <template #default="{ row }">
              <el-tag
                v-for="t in row.deptTags"
                :key="t"
                size="small"
                effect="plain"
                type="success"
                style="margin-right: 6px"
              >
                {{ t }}
              </el-tag>
              <span v-if="!row.deptTags.length" class="muted">未设置</span>
            </template>
          </el-table-column>
          <el-table-column label="是否参加排班" width="130" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.joinRotation"
                :disabled="!canManage"
                @change="(val) => toggleJoinRotation(row, val)"
              />
            </template>
          </el-table-column>
          <el-table-column label="在办病例" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.processingCount ? 'warning' : 'info'" effect="plain">
                {{ row.processingCount }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="上次分配" width="160">
            <template #default="{ row }">
              <span class="muted">{{ row.lastAssignedAt || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canManage" size="small" @click="openExpertDialog(row)">编辑</el-button>
              <el-button
                v-if="canManage"
                size="small"
                type="danger"
                @click="removeExpert(row)"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑专家 -->
    <el-dialog
      v-model="expertDialog"
      :title="expertForm.id ? '编辑专家' : '新增专家'"
      width="520px"
      append-to-body
    >
      <el-form :model="expertForm" label-width="96px">
        <el-form-item label="姓名" required>
          <el-input v-model="expertForm.name" placeholder="请输入专家姓名" />
        </el-form-item>
        <el-form-item label="职称">
          <el-select v-model="expertForm.title" style="width: 200px">
            <el-option v-for="t in titles" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="擅长领域">
          <el-select
            v-model="expertForm.deptTags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入科室/病种，用于分配匹配"
            style="width: 100%"
          >
            <el-option v-for="d in deptOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否参加排班">
          <el-switch v-model="expertForm.joinRotation" />
        </el-form-item>
        <el-form-item label="关联账号">
          <el-input v-model="expertForm.user" placeholder="可选，填用户名（如 yuleoo）" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="expertForm.phone" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="expertDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitExpert">确定</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiAdminCaseAutoAssign,
  apiAdminCreateExpert,
  apiAdminDeleteExpert,
  apiAdminDeleteRotationConfig,
  apiAdminDepartments,
  apiAdminExperts,
  apiAdminRotationConfig,
  apiAdminSaveRotationConfig,
  apiAdminUpdateExpert,
} from '@/api/admin'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  canManage: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'updated'])

const activeTab = ref('rotation')
const loading = ref(false)
const saving = ref(false)
const assigning = ref(false)

const rotations = ref([])
const experts = ref([])
const deptOptions = ref([])

const weekdays = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]
const titles = ['主任医师', '副主任医师', '主治医师', '住院医师']

const rotationForm = reactive({
  id: null,
  hospital: '主院区',
  weekdays: [],
  range: [],
})
const expertForm = reactive({
  id: null,
  name: '',
  title: '副主任医师',
  deptTags: [],
  joinRotation: true,
  user: '',
  phone: '',
})
const expertDialog = ref(false)

const handleOpen = async () => {
  await Promise.all([loadRotations(), loadExperts(), loadDepts()])
}

const loadRotations = async () => {
  loading.value = true
  try {
    const { data } = await apiAdminRotationConfig()
    if (data.code === 200) rotations.value = data.data.list || []
  } finally {
    loading.value = false
  }
}

const loadExperts = async () => {
  const { data } = await apiAdminExperts()
  if (data.code === 200) experts.value = data.data.list || []
}

const loadDepts = async () => {
  const { data } = await apiAdminDepartments()
  if (data.code === 200) deptOptions.value = (data.data.list || []).map((d) => d.name)
}

const resetRotationForm = () => {
  rotationForm.id = null
  rotationForm.hospital = '主院区'
  rotationForm.weekdays = []
  rotationForm.range = []
}

const editRotation = (row) => {
  rotationForm.id = row.id
  rotationForm.hospital = row.hospital
  rotationForm.weekdays = [...row.weekdays]
  rotationForm.range = [row.startDate, row.endDate]
}

const submitRotation = async () => {
  if (!rotationForm.weekdays.length) {
    ElMessage.warning('请选择轮值排班日')
    return
  }
  if (!rotationForm.range || rotationForm.range.length !== 2) {
    ElMessage.warning('请选择生效时间区间')
    return
  }
  saving.value = true
  try {
    const { data } = await apiAdminSaveRotationConfig({
      id: rotationForm.id,
      hospital: rotationForm.hospital,
      weekdays: rotationForm.weekdays,
      startDate: rotationForm.range[0],
      endDate: rotationForm.range[1],
      isActive: true,
    })
    if (data.code === 200) {
      ElMessage.success(data.msg || '保存成功')
      resetRotationForm()
      await loadRotations()
      emit('updated')
    } else {
      ElMessage.error(data.msg || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const removeRotation = (row) => {
  ElMessageBox.confirm(`确认删除「${row.hospital}」的轮值配置？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  })
    .then(async () => {
      const { data } = await apiAdminDeleteRotationConfig(row.id)
      if (data.code === 200) {
        ElMessage.success('已删除')
        await loadRotations()
      } else {
        ElMessage.error(data.msg || '删除失败')
      }
    })
    .catch(() => {})
}

const runAutoAssign = async () => {
  assigning.value = true
  try {
    const { data } = await apiAdminCaseAutoAssign({})
    if (data.code === 200) {
      ElMessage.success(data.msg || '已执行')
      emit('updated')
    } else {
      ElMessage.warning(data.msg || '未分配')
    }
  } finally {
    assigning.value = false
  }
}

const openExpertDialog = (row) => {
  expertForm.id = row ? row.id : null
  expertForm.name = row ? row.name : ''
  expertForm.title = row ? row.title : '副主任医师'
  expertForm.deptTags = row ? [...row.deptTags] : []
  expertForm.joinRotation = row ? row.joinRotation : true
  expertForm.user = row ? row.user : ''
  expertForm.phone = row ? row.phone : ''
  expertDialog.value = true
}

const submitExpert = async () => {
  if (!expertForm.name.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: expertForm.name.trim(),
      title: expertForm.title,
      deptTags: expertForm.deptTags,
      joinRotation: expertForm.joinRotation,
      user: expertForm.user,
      phone: expertForm.phone,
    }
    const { data } = expertForm.id
      ? await apiAdminUpdateExpert(expertForm.id, payload)
      : await apiAdminCreateExpert(payload)
    if (data.code === 200) {
      ElMessage.success(data.msg || '保存成功')
      expertDialog.value = false
      await loadExperts()
    } else {
      ElMessage.error(data.msg || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const toggleJoinRotation = async (row, val) => {
  const { data } = await apiAdminUpdateExpert(row.id, { joinRotation: val })
  if (data.code === 200) {
    ElMessage.success(val ? '已加入排班' : '已退出排班')
  } else {
    row.joinRotation = !val
    ElMessage.error(data.msg || '操作失败')
  }
}

const removeExpert = (row) => {
  ElMessageBox.confirm(
    `确认删除专家「${row.name}」？若已有病例记录将改为停用（保留历史数据）。`,
    '删除确认',
    { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
  )
    .then(async () => {
      const { data } = await apiAdminDeleteExpert(row.id)
      if (data.code === 200) {
        ElMessage.success(data.msg || '已删除')
        await loadExperts()
      } else {
        ElMessage.error(data.msg || '删除失败')
      }
    })
    .catch(() => {})
}

watch(
  () => props.modelValue,
  (v) => {
    if (!v) resetRotationForm()
  }
)

onMounted(() => {})
</script>

<style scoped>
.rotation-form {
  margin-bottom: 6px;
}

.expert-toolbar {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.tip {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
  line-height: 1.7;
}

.muted {
  color: #909399;
  font-size: 12px;
}
</style>
