<template>
  <div class="drgGrouping">
    <div class="drgGrouping_main">
      <div class="drgGrouping_header" style="display: flex">
        <el-select
          v-model="drgValue"
          placeholder="DRG版本"
          clearable
          size="large"
          style="width: 240px; margin-right: 20px"
        >
          <el-option
            v-for="item in drgOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select
          v-model="codeValue"
          clearable
          placeholder="编码版本"
          size="large"
          style="width: 240px; margin-right: 20px"
        >
          <el-option
            v-for="item in codeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-upload
          action=""
          :auto-upload="false"
          :show-file-list="false"
          style="width: 240px; margin-right: 20px"
          :on-change="handleFileChange"
          accept=".jpg,.jpeg,.png,.pdf"
        >
          <el-button type="danger" size="large">导入病案 </el-button>
        </el-upload>
        <!-- <el-select
            v-model="exValue"
            clearable
            placeholder="导入病案"
            size="large"
            style="width: 240px;"
          >
            <el-option
              v-for="item in exOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select> -->
      </div>

      <!-- 主要诊断部分 -->
      <div class="form-section diagnosis-section">
        <h3>主要诊断</h3>
        <div class="form-container">
          <el-form :model="diagnosisForm" ref="diagnosisFormRef">
            <div
              v-for="(row, index) in diagnosisForm.rows"
              :key="'diagnosis-' + index"
              class="input-row"
            >
              <div class="input-group">
                <el-form-item
                  :label="index == '0' ? '主要诊断' : '其他诊断' + index"
                  :prop="`rows.${index}.diagnosis`"
                  :rules="[
                    {
                      required: true,
                      message: '请输入主要诊断',
                      trigger: 'blur',
                    },
                    { validator: validateDiagnosis, trigger: 'blur' },
                  ]"
                >
                  <el-input
                    v-model="row.diagnosis"
                    placeholder="请输入主要诊断"
                    @input="autoFillDiagnosisCode(index)"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="诊断编码">
                  <el-input
                    v-model="row.code"
                    placeholder="自动识别"
                    disabled
                  />
                </el-form-item>
              </div>
              <div class="button-group">
                <el-button
                  v-if="index === 0"
                  type="primary"
                  @click="addDiagnosisRow"
                  :disabled="!canAddDiagnosisRow"
                >
                  <el-icon><Plus /></el-icon>添加
                </el-button>
                <el-button
                  v-else
                  type="danger"
                  @click="removeDiagnosisRow(index)"
                >
                  <el-icon><delete /></el-icon>删除
                </el-button>
              </div>
            </div>
          </el-form>
        </div>
      </div>

      <!-- 主要手术操作部分 -->
      <div class="form-section operation-section">
        <h3>主要手术操作</h3>
        <div class="form-container">
          <el-form :model="operationForm" ref="operationFormRef">
            <div
              v-for="(row, index) in operationForm.rows"
              :key="'operation-' + index"
              class="input-row"
            >
              <div class="input-group">
                <el-form-item
                  :label="index == '0' ? '主要手术' : '其他手术' + index"
                  :prop="`rows.${index}.operation`"
                  :rules="[
                    {
                      required: true,
                      message: '请输入手术操作',
                      trigger: 'blur',
                    },
                    { validator: validateOperation, trigger: 'blur' },
                  ]"
                >
                  <el-input
                    v-model="row.operation"
                    placeholder="请输入手术操作"
                    @input="autoFillOperationCode(index)"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="操作编码">
                  <el-input
                    v-model="row.code"
                    placeholder="自动识别"
                    disabled
                  />
                </el-form-item>
              </div>
              <div class="button-group">
                <el-button
                  v-if="index === 0"
                  type="success"
                  @click="addOperationRow"
                  :disabled="!canAddOperationRow"
                >
                  <el-icon><Plus /></el-icon>添加
                </el-button>
                <el-button
                  v-else
                  type="danger"
                  @click="removeOperationRow(index)"
                >
                  <el-icon><delete /></el-icon>删除
                </el-button>
              </div>
            </div>
          </el-form>
        </div>
      </div>

      <!-- 患者信息部分 -->
      <div class="form-section patient-section">
        <h3>患者信息</h3>
        <div class="form-container">
          <el-form :model="patientInfo" ref="patientInfoRef">
            <div class="input-row">
              <div class="input-group">
                <el-form-item label="年龄">
                  <el-input
                    v-model="patientInfo.age"
                    placeholder="请输入年龄"
                    type="number"
                    min="0"
                  >
                    <template #append>岁</template>
                  </el-input>
                </el-form-item>
                <el-form-item label="性别">
                  <el-select
                    v-model="patientInfo.gender"
                    placeholder="请选择性别"
                    clearable
                  >
                    <el-option label="男" value="male" />
                    <el-option label="女" value="female" />
                    <el-option label="未知" value="unknown" />
                  </el-select>
                </el-form-item>
              </div>
            </div>
            <div class="input-row">
              <div class="input-group">
                <el-form-item label="新生儿年龄">
                  <el-input
                    v-model="patientInfo.newbornAge"
                    placeholder="请输入新生儿年龄"
                    type="number"
                    min="0"
                  >
                    <template #append>天</template>
                  </el-input>
                </el-form-item>
                <el-form-item label="住院天数">
                  <el-input
                    v-model="patientInfo.hospitalDays"
                    placeholder="请输入住院天数"
                    type="number"
                    min="0"
                  >
                    <template #append>天</template>
                  </el-input>
                </el-form-item>
              </div>
            </div>
            <div class="input-row">
              <div class="input-group">
                <el-form-item label="离院方式">
                  <el-select
                    v-model="patientInfo.dischargeWay"
                    placeholder="请选择离院方式"
                    clearable
                  >
                    <el-option label="医嘱离院" value="1" />
                    <el-option label="医嘱转院" value="2" />
                    <el-option label="医嘱转社区卫生服务机构" value="3" />
                    <el-option label="非医嘱离院" value="4" />
                    <el-option label="死亡" value="5" />
                    <el-option label="其他" value="9" />
                  </el-select>
                </el-form-item>
                <el-form-item label="住院总费用">
                  <el-input
                    v-model="patientInfo.totalCost"
                    placeholder="请输入住院总费用"
                    type="number"
                    min="0"
                  >
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </div>
            </div>
          </el-form>
        </div>
      </div>
      <el-button type="primary" @click="showImageModal">DRG分组查询</el-button>
    </div>
    <div v-if="showModal" class="image-modal">
      <div class="modal-overlay" @click="closeModal"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>DRG分组结果</h3>
          <el-icon class="close-icon" @click="closeModal"><Close /></el-icon>
        </div>
        <div class="modal-body">
          <img src="../assets/drg.png" alt="DRG分组结果" class="result-image" />
        </div>
        <div class="modal-footer">
          <el-button type="primary" @click="closeModal">关闭</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Delete, Plus, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 诊断与编码的映射关系
const diagnosisMap = {
  不稳定型心绞痛: 'I20.000',
  冠状动脉粥样硬化性心脏病: 'I25.103',
  '高血压病3级(极高危)': 'I10.x00x032',
  '2 型糖尿病': 'E11.900',
  肺诊断性影像异常: 'R91.x00x003',
  脂肪肝: 'K76.000',
  单纯性肾囊肿: 'N28.101',
  颈动脉硬化: 'I70.806',
  下肢动脉粥样硬化: 'I70.203',
}

// 手术操作与编码的映射关系
const operationMap = {
  药物洗脱冠状动脉支架置入: '36.0700',
  经皮冠状动脉球囊扩张成形术: '00.6600x004',
  单根导管的冠状动脉造影术: '88.5500',
  置入一根血管的支架: '00.4500',
  单根血管操作: '00.4000',
}

// 离院方式选项
const dischargeOptions = [
  { value: '1', label: '医嘱离院' },
  { value: '2', label: '医嘱转院' },
  { value: '3', label: '测试001' },
  { value: '4', label: '测试002' },
  { value: '5', label: '测试003' },
  { value: '9', label: '测试004' },
]

const drgValue = ref('')
const drgOptions = [
  { value: '01', label: 'CHS-DRG 1.0版' },
  { value: '02', label: 'CHS-DRG 2.0版' },
  { value: '03', label: 'CN-DRG' },
]

const codeValue = ref('')
const codeOptions = [
  { value: '01', label: '国家临床版2.0' },
  { value: '02', label: '医保编码2.0版' },
]

const exValue = ref('')
const exOptions = []

// 诊断表单数据
const diagnosisForm = ref({
  rows: [{ diagnosis: '', code: '' }],
})

// 手术操作表单数据
const operationForm = ref({
  rows: [{ operation: '', code: '' }],
})

// 患者信息数据
const patientInfo = ref({
  age: '',
  gender: '',
  newbornAge: '',
  hospitalDays: '',
  dischargeWay: '',
  totalCost: '',
})

const diagnosisFormRef = ref(null)
const operationFormRef = ref(null)
const patientInfoRef = ref(null)

// 验证诊断是否有效
const validateDiagnosis = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入主要诊断'))
  } else if (!Object.keys(diagnosisMap).includes(value)) {
    callback(new Error('没有匹配的诊断数据'))
  } else {
    callback()
  }
}

// 验证手术操作
const validateOperation = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入手术操作'))
  } else if (!Object.keys(operationMap).includes(value)) {
    callback(new Error('没有匹配的手术操作数据'))
  } else {
    callback()
  }
}

// 检查所有诊断行是否填写
const canAddDiagnosisRow = computed(() => {
  return diagnosisForm.value.rows.every(
    (row) =>
      row.diagnosis.trim() !== '' &&
      Object.keys(diagnosisMap).includes(row.diagnosis)
  )
})

// 检查所有手术行是否填写
const canAddOperationRow = computed(() => {
  return operationForm.value.rows.every(
    (row) =>
      row.operation.trim() !== '' &&
      Object.keys(operationMap).includes(row.operation)
  )
})

// 填充诊断编码
const autoFillDiagnosisCode = (index) => {
  const diagnosis = diagnosisForm.value.rows[index].diagnosis
  diagnosisForm.value.rows[index].code = diagnosisMap[diagnosis] || ''
}

// 填充手术编码
const autoFillOperationCode = (index) => {
  const operation = operationForm.value.rows[index].operation
  operationForm.value.rows[index].code = operationMap[operation] || ''
}

// 诊断 添加 删除
const addDiagnosisRow = async () => {
  try {
    await diagnosisFormRef.value.validate()
    if (canAddDiagnosisRow.value) {
      diagnosisForm.value.rows.push({ diagnosis: '', code: '' })
    }
  } catch (error) {
    console.log('诊断表单验证失败', error)
  }
}
const removeDiagnosisRow = (index) => {
  if (diagnosisForm.value.rows.length > 1) {
    diagnosisForm.value.rows.splice(index, 1)
  }
}

// 手术 添加 删除
const addOperationRow = async () => {
  try {
    await operationFormRef.value.validate()
    if (canAddOperationRow.value) {
      operationForm.value.rows.push({ operation: '', code: '' })
    }
  } catch (error) {
    console.log('手术表单验证失败', error)
  }
}
const removeOperationRow = (index) => {
  if (operationForm.value.rows.length > 1) {
    operationForm.value.rows.splice(index, 1)
  }
}
// 弹窗
const showModal = ref(false)
// 显示弹窗
const showImageModal = () => {
  showModal.value = true
}
// 关闭弹窗
const closeModal = () => {
  showModal.value = false
}
// 导入病案
const handleFileChange = (file) => {
  // Validate file type
  const validTypes = ['image/jpeg', 'image/png', 'application/pdf']
  if (!validTypes.includes(file.raw.type)) {
    ElMessage.error('请上传 JPG/PNG/PDF 格式的文件')
    return
  }

  // Check file size based on type
  if (file.raw.type === 'application/pdf') {
    if (file.size > 13 * 1024 * 1024) {
      ElMessage.error('PDF 文件大小不能超过 13MB')
      return
    }
  } else {
    if (file.size > 100 * 1024 * 1024) {
      ElMessage.error('图片文件大小不能超过 100MB')
      return
    }
  }

  // If validation passes, populate the form with sample data
  diagnosisForm.value.rows = [
    { diagnosis: '不稳定型心绞痛', code: 'I20.000' },
    { diagnosis: '冠状动脉粥样硬化性心脏病', code: 'I25.103' },
    { diagnosis: '高血压病3级(极高危)', code: 'I10.x00x032' },
    { diagnosis: '2 型糖尿病', code: 'E11.900' },
    { diagnosis: '肺诊断性影像异常', code: 'R91.x00x003' },
    { diagnosis: '脂肪肝', code: 'K76.000' },
    { diagnosis: '单纯性肾囊肿', code: 'N28.101' },
    { diagnosis: '颈动脉硬化', code: 'I70.806' },
    { diagnosis: '下肢动脉粥样硬化', code: 'I70.203' },
  ]
  operationForm.value.rows = [
    { operation: '药物洗脱冠状动脉支架置入', code: '36.0700' },
    { operation: '经皮冠状动脉球囊扩张成形术', code: '00.6600x004' },
    { operation: '单根导管的冠状动脉造影术', code: '88.5500' },
    { operation: '置入一根血管的支架', code: '00.4500' },
    { operation: '单根血管操作', code: '00.4000' },
  ]
}
</script>

<style scoped>
.drgGrouping {
  min-height: calc(100vh - 100px);
  padding: 20px;
}
.drgGrouping_main {
  background-color: #fff;
  padding: 20px;
  border-radius: 20px;
  /* width: 60%; */
}
.drgGrouping_header {
  margin-bottom: 20px;
}

.form-section {
  margin-bottom: 30px;
}

.form-section h3 {
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;
  font-weight: bold;
}

/* 诊断部分样式 */
.diagnosis-section .form-container {
  background-color: #f0f9ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
}

.diagnosis-section .input-row {
  background-color: #f0f9ff;
}

/* 手术操作部分样式 */
.operation-section .form-container {
  background-color: #f0f2f5;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.operation-section .input-row {
  background-color: #f0f2f5;
}

/* 患者信息部分样式 */
.patient-section .form-container {
  background-color: #fdf6ec;
  border: 1px solid #faecd8;
  border-radius: 4px;
}

.patient-section .input-row {
  background-color: #fdf6ec;
}

.form-container {
  max-width: 800px;
  margin-top: 10px;
}

.input-row {
  display: flex;
  align-items: flex-start;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.input-group {
  display: flex;
  flex: 1;
  gap: 20px;
}

.button-group {
  margin-left: 20px;
  width: 100px;
}

.el-form-item {
  flex: 1;
  margin-bottom: 0;
}

.el-input {
  width: 100%;
}

/* 按钮样式调整 */
.diagnosis-section .el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
}

.operation-section .el-button--success {
  background-color: #67c23a;
  border-color: #67c23a;
}

/* 患者信息部分输入框样式 */
.patient-section .el-input-group__append {
  padding: 0 10px;
  background-color: #fff;
  color: #666;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .input-group {
    flex-direction: column;
    gap: 10px;
  }

  .button-group {
    margin-left: 0;
    margin-top: 10px;
    width: 100%;
  }
}
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background-color: white;
  border-radius: 8px;
  width: 70%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  z-index: 2001;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-icon {
  cursor: pointer;
  font-size: 20px;
  color: #999;
}

.close-icon:hover {
  color: #666;
}

.modal-body {
  padding: 20px;
  overflow: auto;
  flex-grow: 1;
}

.result-image {
  width: 100%;
  height: auto;
  display: block;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  text-align: right;
}
</style>
