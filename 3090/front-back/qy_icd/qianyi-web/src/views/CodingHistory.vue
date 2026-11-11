<!-- views/CodingHistory.vue -->
<template>
  <div class="coding-history-container">
    <div class="page-header">
      <h2>编码历史</h2>
      <p>查看和管理历史编码记录</p>
    </div>

    <div class="history-content">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>历史记录</span>
            <!-- <el-button type="primary" @click="exportHistory">导出历史</el-button> -->
          </div>
        </template>

        <el-table :data="historyList" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="createTime" label="创建时间" width="180" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTypeTag(row.type)">{{
                getTypeText(row.type)
              }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="viewDetail(row)"
                >查看</el-button
              >
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const historyList = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 模拟数据
const mockData = [
  {
    id: 1,
    title: '编码案例1',
    createTime: '2024-01-15 10:30:00',
    type: 'text',
  },
  {
    id: 2,
    title: 'PDF识别案例1',
    createTime: '2024-01-15 11:20:00',
    type: 'pdf',
  },
  {
    id: 3,
    title: '结构化数据案例1',
    createTime: '2024-01-14 09:15:00',
    type: 'structured',
  },
]

const getTypeTag = (type) => {
  const typeMap = {
    text: '',
    pdf: 'success',
    structured: 'warning',
  }
  return typeMap[type] || ''
}

const getTypeText = (type) => {
  const typeMap = {
    text: '文本输入',
    pdf: 'PDF上传',
    structured: '结构化数据',
  }
  return typeMap[type] || '未知'
}

const viewDetail = (row) => {
  ElMessage.info(`查看详情: ${row.title}`)
}

const exportHistory = () => {
  ElMessage.success('导出功能开发中...')
}

onMounted(() => {
  historyList.value = mockData
  total.value = mockData.length
})
</script>

<style scoped>
.coding-history-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.history-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
