<template>
  <div class="version-trend">
    <!-- 顶部：编码类型 Tab -->
    <el-card shadow="never" class="card">
      <div class="toolbar">
        <el-radio-group v-model="query.type" size="default" @change="loadTrend">
          <el-radio-button label="disease">疾病编码</el-radio-button>
          <el-radio-button label="surgery">手术编码</el-radio-button>
        </el-radio-group>

        <div class="filters">
          <span class="filter-label">时间维度</span>
          <el-select v-model="query.period" style="width: 120px" @change="loadTrend">
            <el-option label="年" value="year" />
            <el-option label="季度" value="quarter" />
            <el-option label="月" value="month" />
            <el-option label="周" value="week" />
          </el-select>

          <span class="filter-label">科室</span>
          <el-select
            v-model="query.dept"
            style="width: 180px"
            filterable
            clearable
            placeholder="全部科室"
            @change="loadTrend"
          >
            <el-option label="全部科室" value="" />
            <el-option v-for="d in depts" :key="d.name" :label="d.name" :value="d.name" />
          </el-select>

          <el-button type="primary" plain @click="handleExport" :loading="exporting">
            <el-icon><Download /></el-icon>
            <span>导出 Excel</span>
          </el-button>
          <el-button @click="openReviewDialog">
            <el-icon><EditPen /></el-icon>
            <span>录入抽检数据</span>
          </el-button>
          <el-button @click="openVersionDialog">
            <el-icon><Plus /></el-icon>
            <span>版本登记</span>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 汇总指标 -->
    <div class="stat-row">
      <div class="stat-card model">
        <div class="stat-label">模型生成 · 平均正确率</div>
        <div class="stat-value">{{ summary.model.rate }}%</div>
        <div class="stat-foot">抽检 {{ summary.model.total }} 例 / 正确 {{ summary.model.correct }} 例</div>
      </div>
      <div class="stat-card doctor">
        <div class="stat-label">医生提交 · 平均正确率</div>
        <div class="stat-value">{{ summary.doctor.rate }}%</div>
        <div class="stat-foot">抽检 {{ summary.doctor.total }} 例 / 正确 {{ summary.doctor.correct }} 例</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">数据点</div>
        <div class="stat-value">{{ trend.pointCount || 0 }}</div>
        <div class="stat-foot">{{ query.period === 'year' ? '每个编码版本一个点' : '当前周期粒度聚合' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">提升幅度（模型）</div>
        <div class="stat-value">{{ deltaText }}</div>
        <div class="stat-foot">首末数据点对比</div>
      </div>
    </div>

    <!-- 趋势图 -->
    <el-card shadow="never" class="card">
      <template #header>
        <div class="card-header">
          <span>准确率趋势（{{ trend.typeName }}）</span>
          <span class="hint">
            {{ trend.periodName }}{{ query.dept ? ' · ' + query.dept : ' · 全部科室' }}
          </span>
        </div>
      </template>
      <div v-loading="loading" class="chart-wrap">
        <div ref="chartRef" class="chart"></div>
        <el-empty
          v-if="!loading && (!trend.points || trend.points.length === 0)"
          description="暂无抽检标注数据，请先「录入抽检数据」或「版本登记」"
          class="chart-empty"
        />
      </div>
    </el-card>

    <!-- 明细表 -->
    <el-card shadow="never" class="card">
      <template #header>
        <div class="card-header">
          <span>数据明细</span>
          <el-button link type="primary" @click="loadTrend">刷新</el-button>
        </div>
      </template>
      <el-table :data="trend.points || []" border size="small" v-loading="loading">
        <el-table-column prop="label" label="数据点" min-width="150" />
        <el-table-column prop="versionNo" label="对应版本" min-width="130" />
        <el-table-column prop="releaseDate" label="发布时间" width="110" />
        <el-table-column prop="versionCount" label="版本数" width="80" align="center" />
        <el-table-column label="模型生成" align="center">
          <el-table-column label="测试例数" width="90" align="center">
            <template #default="{ row }">{{ row.model.total }}</template>
          </el-table-column>
          <el-table-column label="正确例数" width="90" align="center">
            <template #default="{ row }">{{ row.model.correct }}</template>
          </el-table-column>
          <el-table-column label="正确率" width="90" align="center">
            <template #default="{ row }">
              <span class="rate model-text">{{ formatRate(row.model.rate) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="医生提交" align="center">
          <el-table-column label="测试例数" width="90" align="center">
            <template #default="{ row }">{{ row.doctor.total }}</template>
          </el-table-column>
          <el-table-column label="正确例数" width="90" align="center">
            <template #default="{ row }">{{ row.doctor.correct }}</template>
          </el-table-column>
          <el-table-column label="正确率" width="90" align="center">
            <template #default="{ row }">
              <span class="rate doctor-text">{{ formatRate(row.doctor.rate) }}</span>
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>
      <div class="table-foot">
        说明：一期采用严格口径——「完全正确」计 1，「部分正确 / 错误」计 0；正确率 = 正确例数 / 测试例数。
      </div>
    </el-card>

    <!-- 抽检录入弹窗 -->
    <el-dialog v-model="reviewDialog" title="抽检标注录入" width="680px">
      <el-form :model="reviewForm" label-width="96px">
        <el-form-item label="编码版本" required>
          <el-select v-model="reviewForm.versionId" filterable style="width: 100%">
            <el-option
              v-for="v in versionOptions"
              :key="v.id"
              :label="`${v.versionNo}（${v.releaseDate}）`"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据序列">
          <el-radio-group v-model="reviewForm.sequence">
            <el-radio label="model">模型生成</el-radio>
            <el-radio label="doctor">医生提交</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="判定日期">
          <el-date-picker
            v-model="reviewForm.reviewDate"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="批量录入">
          <el-input
            v-model="reviewForm.bulk"
            type="textarea"
            :rows="8"
            placeholder="每行一条：病案标识,判定,科室（可省略科室）&#10;判定：1=完全正确，2=部分正确，3=错误&#10;示例：&#10;25010001,1,心血管内科&#10;25010002,3&#10;25010003,2,骨科"
          />
          <div class="form-tip">
            也支持只填判定结果（如一行「1」），此时病案标识留空。提交后立即计入趋势统计。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReviews">
          提交录入
        </el-button>
      </template>
    </el-dialog>

    <!-- 版本登记弹窗 -->
    <el-dialog v-model="versionDialog" title="编码版本登记" width="520px">
      <el-form :model="versionForm" label-width="96px">
        <el-form-item label="版本号" required>
          <el-input v-model="versionForm.versionNo" placeholder="如 V2609011120" />
        </el-form-item>
        <el-form-item label="版本类型">
          <el-radio-group v-model="versionForm.versionType">
            <el-radio label="disease">疾病编码</el-radio>
            <el-radio label="surgery">手术编码</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="发布时间" required>
          <el-date-picker
            v-model="versionForm.releaseDate"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="关联模型">
          <el-input v-model="versionForm.modelName" placeholder="如 disease_agent_v20260901" />
        </el-form-item>
        <el-form-item label="版本说明">
          <el-input v-model="versionForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitVersion">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  apiAdminAccuracyExport,
  apiAdminAccuracyTrend,
  apiAdminCreateReviews,
  apiAdminCreateVersion,
  apiAdminDepartments,
  apiAdminVersions,
} from '@/api/admin'

const chartRef = ref(null)
let chart = null

const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const reviewDialog = ref(false)
const versionDialog = ref(false)
const depts = ref([])
const versionOptions = ref([])

const query = reactive({ type: 'disease', period: 'year', dept: '' })
const trend = ref({ points: [], summary: { model: {}, doctor: {} }, pointCount: 0 })
const summary = computed(() => ({
  model: { rate: 0, total: 0, correct: 0, ...(trend.value.summary?.model || {}) },
  doctor: { rate: 0, total: 0, correct: 0, ...(trend.value.summary?.doctor || {}) },
}))

const deltaText = computed(() => {
  const pts = (trend.value.points || []).filter((p) => p.model.rate !== null)
  if (pts.length < 2) return '—'
  const diff = pts[pts.length - 1].model.rate - pts[0].model.rate
  return `${diff >= 0 ? '+' : ''}${diff.toFixed(1)} pt`
})

const reviewForm = reactive({
  versionId: null,
  sequence: 'model',
  reviewDate: new Date().toISOString().slice(0, 10),
  bulk: '',
})
const versionForm = reactive({
  versionNo: '',
  versionType: 'disease',
  releaseDate: new Date().toISOString().slice(0, 10),
  modelName: '',
  remark: '',
})

const formatRate = (rate) => (rate === null || rate === undefined ? '—' : `${rate}%`)

const buildOption = () => {
  const points = trend.value.points || []
  const labels = points.map((p) => p.axisLabel)
  const modelData = points.map((p) => p.model.rate)
  const doctorData = points.map((p) => p.doctor.rate)
  const pointMap = {}
  points.forEach((p) => {
    pointMap[p.axisLabel] = p
  })

  return {
    color: ['#c0392b', '#1565c0'],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line' },
      formatter: (params) => {
        if (!params || !params.length) return ''
        const p = pointMap[params[0].axisValue]
        if (!p) return ''
        const line = (name, s, color) => {
          const rate = s.rate === null || s.rate === undefined ? '—' : `${s.rate}%`
          return `<div style="display:flex;justify-content:space-between;gap:16px">
            <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};margin-right:6px"></span>${name}</span>
            <b>${rate}</b></div>
            <div style="color:#909399;font-size:12px;margin-left:14px">测试例数 ${s.total} 例 · 正确 ${s.correct} 例</div>`
        }
        return `<div style="min-width:210px">
          <div style="font-weight:600;margin-bottom:6px">${p.label}</div>
          <div style="color:#606266;font-size:12px;margin-bottom:6px">
            规划版本号：${p.versionNo}<br/>
            发布时间：${p.releaseDate}${p.versionCount > 1 ? `<br/>周期内版本数：${p.versionCount}` : ''}
          </div>
          ${line('模型生成', p.model, '#c0392b')}
          <div style="height:4px"></div>
          ${line('医生提交', p.doctor, '#1565c0')}
        </div>`
      },
    },
    legend: { data: ['模型生成', '医生提交'], top: 4, itemGap: 24 },
    grid: { left: 56, right: 32, top: 48, bottom: 64 },
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: false,
      axisLabel: { rotate: labels.length > 8 ? 32 : 0, fontSize: 11, color: '#606266' },
      axisLine: { lineStyle: { color: '#dcdfe6' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '正确率',
      nameTextStyle: { color: '#909399' },
      axisLabel: { formatter: '{value}%', color: '#606266' },
      splitLine: { lineStyle: { type: 'dashed', color: '#eef1f5' } },
    },
    series: [
      {
        name: '模型生成',
        type: 'line',
        smooth: true,
        connectNulls: true,
        symbolSize: 8,
        data: modelData,
        lineStyle: { width: 3 },
        itemStyle: { color: '#c0392b' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(192,57,43,0.18)' },
              { offset: 1, color: 'rgba(192,57,43,0.01)' },
            ],
          },
        },
      },
      {
        name: '医生提交',
        type: 'line',
        smooth: true,
        connectNulls: true,
        symbolSize: 8,
        data: doctorData,
        lineStyle: { width: 3 },
        itemStyle: { color: '#1565c0' },
      },
    ],
  }
}

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(), true)
  chart.resize()
}

const loadDepts = async () => {
  try {
    const { data } = await apiAdminDepartments()
    if (data.code === 200) depts.value = data.data.list || []
  } catch (e) {
    /* 忽略：过滤项加载失败不阻塞页面 */
  }
}

const loadTrend = async () => {
  loading.value = true
  try {
    const { data } = await apiAdminAccuracyTrend({
      type: query.type,
      period: query.period,
      dept: query.dept,
    })
    if (data.code === 200) {
      trend.value = data.data
      await renderChart()
    } else {
      ElMessage.error(data.msg || '加载趋势数据失败')
    }
  } catch (e) {
    ElMessage.error('加载趋势数据失败')
  } finally {
    loading.value = false
  }
}

const loadVersions = async () => {
  const { data } = await apiAdminVersions({ type: query.type })
  if (data.code === 200) versionOptions.value = data.data.list || []
}

const handleExport = async () => {
  exporting.value = true
  try {
    const res = await apiAdminAccuracyExport({
      type: query.type,
      period: query.period,
      dept: query.dept,
    })
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const typeName = query.type === 'disease' ? '疾病编码' : '手术编码'
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `编码准确率_${typeName}_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const openReviewDialog = async () => {
  reviewForm.bulk = ''
  reviewForm.sequence = 'model'
  reviewForm.reviewDate = new Date().toISOString().slice(0, 10)
  await loadVersions()
  reviewForm.versionId = versionOptions.value.length
    ? versionOptions.value[versionOptions.value.length - 1].id
    : null
  reviewDialog.value = true
}

const parseBulk = () => {
  const records = []
  reviewForm.bulk
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .forEach((line) => {
      const parts = line
        .replace(/[，、\t]/g, ',')
        .split(/[\s,]+/)
        .filter(Boolean)
      if (!parts.length) return
      let caseIdentifier = ''
      let result = 1
      let dept = ''
      if (parts.length === 1 && /^[123]$/.test(parts[0])) {
        result = Number(parts[0])
      } else {
        caseIdentifier = /^[123]$/.test(parts[0]) ? '' : parts[0]
        const resultToken = /^[123]$/.test(parts[0]) ? parts[0] : parts[1]
        result = /^[123]$/.test(resultToken || '') ? Number(resultToken) : 1
        dept = parts[2] || ''
      }
      records.push({ caseIdentifier, result, dept })
    })
  return records
}

const submitReviews = async () => {
  if (!reviewForm.versionId) {
    ElMessage.warning('请选择编码版本')
    return
  }
  const records = parseBulk()
  if (!records.length) {
    ElMessage.warning('请至少录入一条抽检结果')
    return
  }
  submitting.value = true
  try {
    const { data } = await apiAdminCreateReviews({
      versionId: reviewForm.versionId,
      sequence: reviewForm.sequence,
      reviewDate: reviewForm.reviewDate,
      records,
    })
    if (data.code === 200) {
      ElMessage.success(data.msg || '录入成功')
      reviewDialog.value = false
      await loadTrend()
      await loadDepts()
    } else {
      ElMessage.error(data.msg || '录入失败')
    }
  } catch (e) {
    ElMessage.error('录入失败')
  } finally {
    submitting.value = false
  }
}

const openVersionDialog = () => {
  versionForm.versionNo = ''
  versionForm.versionType = query.type
  versionForm.releaseDate = new Date().toISOString().slice(0, 10)
  versionForm.modelName = ''
  versionForm.remark = ''
  versionDialog.value = true
}

const submitVersion = async () => {
  if (!versionForm.versionNo.trim()) {
    ElMessage.warning('请填写版本号')
    return
  }
  submitting.value = true
  try {
    const { data } = await apiAdminCreateVersion({
      versionNo: versionForm.versionNo.trim(),
      versionType: versionForm.versionType,
      releaseDate: versionForm.releaseDate,
      modelName: versionForm.modelName,
      remark: versionForm.remark,
    })
    if (data.code === 200) {
      ElMessage.success('版本登记成功')
      versionDialog.value = false
      if (versionForm.versionType === query.type) await loadTrend()
    } else {
      ElMessage.error(data.msg || '登记失败')
    }
  } catch (e) {
    ElMessage.error('登记失败')
  } finally {
    submitting.value = false
  }
}

const handleResize = () => chart && chart.resize()

onMounted(async () => {
  await loadDepts()
  await loadTrend()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.version-trend {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card {
  border: 1px solid #e6eaf0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 13px;
  color: #606266;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e6eaf0;
  border-radius: 8px;
  padding: 14px 16px;
}

.stat-label {
  font-size: 13px;
  color: #7a8699;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
  margin: 6px 0 4px;
}

.stat-card.model .stat-value {
  color: #c0392b;
}

.stat-card.doctor .stat-value {
  color: #1565c0;
}

.stat-foot {
  font-size: 12px;
  color: #909399;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #1f2d3d;
}

.hint {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}

.chart-wrap {
  position: relative;
  min-height: 380px;
}

.chart {
  width: 100%;
  height: 380px;
}

.chart-empty {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
}

.rate {
  font-weight: 600;
}

.model-text {
  color: #c0392b;
}

.doctor-text {
  color: #1565c0;
}

.table-foot {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
  line-height: 1.6;
}
</style>
