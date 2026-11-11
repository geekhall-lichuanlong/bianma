<template>
  <div class="user-management-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>

      <!-- 搜索和分页 -->
      <div class="table-toolbar">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>

      <!-- 用户列表 -->
      <el-table :data="userList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="180" />
        <el-table-column prop="realName" label="真实姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.role === 0 ? 'danger' : 'primary'">
              {{ scope.row.role === 0 ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column prop="createTime" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.createTime) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="1"
              :inactive-value="0"
              :active-text="scope.row.status === 1 ? '启用' : '禁用'"
              :inactive-text="scope.row.status === 0 ? '禁用' : '启用'"
              @change="handleStatusChange(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)"
              >编辑</el-button
            >
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <!-- 新增/编辑用户弹窗 -->
      <el-dialog
        v-model="showDialog"
        :title="dialogTitle"
        width="500px"
        :before-close="handleCloseDialog"
      >
        <el-form
          ref="userFormRef"
          :model="userForm"
          :rules="userRules"
          label-width="100px"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="userForm.username"
              placeholder="请输入用户名"
              :disabled="isEdit"
            />
          </el-form-item>

          <el-form-item label="真实姓名" prop="realName">
            <el-input
              v-model="userForm.realName"
              placeholder="请输入真实姓名"
            />
          </el-form-item>

          <el-form-item v-if="!isEdit" label="密码" prop="password">
            <el-input
              v-model="userForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
            <div class="form-tip">不填则默认密码为123456</div>
          </el-form-item>

          <el-form-item
            v-if="!isEdit && userForm.password"
            label="确认密码"
            prop="confirmPassword"
          >
            <el-input
              v-model="userForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="角色" prop="role">
            <el-radio-group v-model="userForm.role">
              <el-radio :label="0">管理员</el-radio>
              <el-radio :label="1">普通用户</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="userForm.phone"
              placeholder="请输入手机号"
              maxlength="11"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleCloseDialog">取消</el-button>
            <el-button
              type="primary"
              @click="handleSubmit"
              :loading="submitLoading"
            >
              {{ isEdit ? '更新' : '确定' }}
            </el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiGetUsers,
  apiCreateUser,
  apiUpdateUser,
  apiUpdateUserStatus,
  apiDeleteUser,
} from '@/api/user'

const userList = ref([])
const showDialog = ref(false)
const loading = ref(false)
const submitLoading = ref(false)
const userFormRef = ref()
const isEdit = ref(false)
const editingUserId = ref(null)

// 分页参数
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
})

// 用户表单
const userForm = reactive({
  username: '',
  realName: '',
  password: '',
  confirmPassword: '',
  role: 1, // 默认普通用户
  phone: '',
})

// 计算对话框标题
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑用户' : '新增用户'
})

// 表单验证规则
const validateUsername = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入用户名'))
  } else {
    callback()
  }
}

const validatePhone = (rule, value, callback) => {
  if (value && !/^\d+$/.test(value)) {
    callback(new Error('手机号只能为数字'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule, value, callback) => {
  if (userForm.password && value !== userForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const userRules = {
  username: [{ required: true, validator: validateUsername, trigger: 'blur' }],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  phone: [{ validator: validatePhone, trigger: 'blur' }],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN')
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await apiGetUsers({
      page: pagination.page,
      page_size: pagination.page_size,
    })

    if (response.data.code === 200) {
      userList.value = response.data.data.userList
      pagination.total = response.data.data.total
      pagination.page = response.data.data.page
      pagination.page_size = response.data.data.page_size
    } else {
      ElMessage.error(response.data.msg || '获取用户列表失败')
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchUsers()
}

// 当前页变化
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchUsers()
}

// 新增用户
const handleAdd = () => {
  isEdit.value = false
  editingUserId.value = null
  resetForm()
  showDialog.value = true
}

// 编辑用户
const handleEdit = (user) => {
  isEdit.value = true
  editingUserId.value = user.id

  Object.keys(userForm).forEach((key) => {
    if (key in user) {
      userForm[key] = user[key]
    }
  })

  userForm.password = ''
  userForm.confirmPassword = ''

  showDialog.value = true
}

// 关闭弹窗
const handleCloseDialog = () => {
  showDialog.value = false
  resetForm()
}

// 重置表单
const resetForm = () => {
  nextTick(() => {
    userFormRef.value?.resetFields()
    Object.keys(userForm).forEach((key) => {
      if (key === 'role') {
        userForm[key] = 1
      } else {
        userForm[key] = ''
      }
    })
  })
}

// 提交表单（新增/编辑）
const handleSubmit = async () => {
  const valid = await userFormRef.value.validate()
  if (!valid) {
    ElMessage.error('请完善表单信息')
    return
  }

  submitLoading.value = true

  try {
    const requestData = {
      username: userForm.username,
      realName: userForm.realName,
      role: Number(userForm.role),
      phone: userForm.phone || '',
    }

    if (!isEdit.value && userForm.password) {
      requestData.password = userForm.password
      requestData.confirmPassword = userForm.confirmPassword
    }

    if (isEdit.value) {
      // 编辑用户
      const response = await apiUpdateUser(editingUserId.value, requestData)
      if (response.data.code === 200) {
        ElMessage.success('用户更新成功')
        showDialog.value = false
        fetchUsers()
      } else {
        ElMessage.error(response.data.msg || '更新失败')
      }
    } else {
      // 新增用户
      const response = await apiCreateUser(requestData)
      if (response.data.code === 200) {
        ElMessage.success('用户创建成功')
        showDialog.value = false
        fetchUsers()
      } else {
        ElMessage.error(response.data.msg || '创建失败')
      }
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

// 删除用户
const handleDelete = (user) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${user.realName || user.username}" 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const response = await apiDeleteUser(user.id)
        if (response.data.code === 200) {
          ElMessage.success('删除成功')
          fetchUsers()
        } else {
          ElMessage.error(response.data.msg || '删除失败')
        }
      } catch (error) {
        console.error('删除失败:', error)
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {
      // 用户取消删除
    })
}

// 状态变更
const handleStatusChange = async (user) => {
  try {
    const response = await apiUpdateUserStatus(user.id, user.status)
    if (response.data.code === 200) {
      const action = user.status === 1 ? '启用' : '禁用'
      ElMessage.success(`已${action}用户`)
    } else {
      // 如果请求失败，回滚状态
      user.status = user.status === 1 ? 0 : 1
      ElMessage.error(response.data.msg || '操作失败')
    }
  } catch (error) {
    console.error('状态更新失败:', error)
    // 回滚状态
    user.status = user.status === 1 ? 0 : 1
    ElMessage.error('状态更新失败')
  }
}
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

.box-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 20px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

:deep(.el-table) {
  margin-top: 20px;
}
</style>
