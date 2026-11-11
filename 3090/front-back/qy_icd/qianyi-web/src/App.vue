<template>
  <div class="app-container" v-if="!isAuthPage">
    <el-container>
      <!-- 头部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <!-- 左侧Logo -->
          <div class="header-logo">
            <img src="@/assets/logo_02.png" alt="医院Logo" class="logo-image" />
          </div>

          <!-- 主菜单 -->
          <el-menu
            :default-active="activeMenu"
            class="main-menu"
            mode="horizontal"
            @select="handleMenuSelect"
          >
            <el-menu-item index="dashboard">
              <template #title>
                <el-icon><Monitor /></el-icon>
                <span>工作台</span>
              </template>
            </el-menu-item>
            <el-menu-item index="coding">
              <template #title>
                <el-icon><Document /></el-icon>
                <span>智能病案编码</span>
              </template>
            </el-menu-item>
            <el-menu-item index="his-coding">
              <template #title>
                <el-icon><OfficeBuilding /></el-icon>
                <span>HIS 智能编码</span>
              </template>
            </el-menu-item>
            <el-menu-item index="drg">
              <template #title>
                <el-icon><PieChart /></el-icon>
                <span>DRG预分组</span>
              </template>
            </el-menu-item>
            <el-menu-item index="knowledge">
              <template #title>
                <el-icon><Reading /></el-icon>
                <span>疾病手术知识查询</span>
              </template>
            </el-menu-item>
            <el-menu-item index="admin-console" v-if="userRole === 0 || userRole === 2">
              <template #title>
                <el-icon><DataBoard /></el-icon>
                <span>编码管理后台</span>
              </template>
            </el-menu-item>
            <el-sub-menu index="system" v-if="userRole === 0">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span style="font-size: 16px; font-weight: 500">系统设置</span>
              </template>
              <el-menu-item index="user-management">
                <el-icon><User /></el-icon>
                <span>用户管理</span>
              </el-menu-item>
              <el-menu-item index="change-password">
                <el-icon><Lock /></el-icon>
                <span>修改密码</span>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>

          <!-- 右侧Logo -->
          <div class="header-right-section">
            <div class="partner-logos">
              <img
                src="@/assets/qfsLogo.png"
                alt="合作伙伴Logo"
                class="partner-logo"
                style="height: 50px"
              />
              <img
                src="@/assets/chaosuanLogo.png"
                alt="合作伙伴Logo"
                class="partner-logo"
                style="height: 40px"
              />
            </div>
            <el-button
              chat_type="danger"
              plain
              size="small"
              @click="logout"
              class="logout-button"
            >
              <el-icon><SwitchButton /></el-icon>
              <span>退出</span>
            </el-button>
          </div>
        </div>
      </el-header>


      <el-container class="app-body">
        <!-- 侧边栏（仅LLM功能页面显示） -->
        <el-aside
          v-if="showHistorySidebar"
          :width="sidebarWidth"
          class="history-sidebar"
        >
          <!-- 侧边栏头部 -->
          <div class="sidebar-header">
            <h3 v-show="!sidebarCollapsed">对话历史</h3>
            <el-tooltip
              :content="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
              placement="bottom"
            >
              <el-button
                circle
                size="small"
                @click="toggleSidebar"
                class="collapse-button"
              >
                <el-icon>
                  <component :is="sidebarCollapsed ? 'Expand' : 'Fold'" />
                </el-icon>
              </el-button>
            </el-tooltip>
          </div>

          <!-- 历史记录列表 -->
          <div class="history-list-container">
            <el-scrollbar>
              <!-- 加载状态 -->
              <div v-if="isLoading" class="loading-state">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载历史记录中...</span>
              </div>

              <!-- 错误状态 -->
              <div v-else-if="error" class="error-state">
                <el-icon><Warning /></el-icon>
                <span>{{ error }}</span>
              </div>
              <!-- 正常状态 -->
              <el-menu
                :default-active="activeSession"
                class="history-menu"
                :class="{ 'is-switching': isHistorySwitching }"
                @select="handleHistorySelect"
              >
                <el-menu-item
                  v-for="item in sessionList"
                  :key="item.id"
                  :index="String(item.id)"
                  :disabled="isHistorySwitching"
                >
                  <template #title>
                    <el-icon><ChatLineRound /></el-icon>
                    <span class="history-title">
                      {{ item.title }}
                    </span>
                    <span class="history-date">
                      {{ formatDate(item.updated_at || item.time) }}
                    </span>
                    <el-icon
                      v-if="
                        isHistorySwitching &&
                        String(item.id) === String(activeSession)
                      "
                      class="history-switching-icon is-loading"
                    >
                      <Loading />
                    </el-icon>
                    <!-- 编辑按钮 -->
                    <el-button
                      link
                      chat_type="primary"
                      size="small"
                      :disabled="isHistorySwitching"
                      @click.stop="showEditDialog(item)"
                      class="edit-button"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <!-- 删除按钮 -->
                    <el-button
                      link
                      chat_type="danger"
                      size="small"
                      :disabled="isHistorySwitching"
                      @click.stop="confirmDelete(item.id)"
                      class="delete-button"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-menu-item>
              </el-menu>
            </el-scrollbar>
          </div>

          <!-- 新对话按钮 -->
          <div class="new-chat-container">
            <el-tooltip
              :content="
                isHistorySwitching
                  ? '正在切换对话，请稍候'
                  : canCreateNewChat
                  ? '开始新对话'
                  : '请先完成当前对话后再创建新对话'
              "
              placement="top"
              :disabled="sidebarCollapsed"
            >
              <el-button
                chat_type="primary"
                @click="startNewChat"
                :icon="Plus"
                :circle="sidebarCollapsed"
                :disabled="!canCreateNewChat || isHistorySwitching"
                class="new-chat-button"
              >
                <span v-if="!sidebarCollapsed">
                  {{
                    isHistorySwitching
                      ? '切换中...'
                      : canCreateNewChat
                      ? '开始新对话'
                      : '当前对话为空'
                  }}
                </span>
              </el-button>
            </el-tooltip>
          </div>
        </el-aside>
        <!-- 拖动条 -->
        <div
          v-if="showHistorySidebar"
          class="sidebar-resizer"
          @mousedown="startDragging"
        ></div>

        <!-- 固定背景容器 -->
        <div class="background-container">
          <img
            src="@/assets/index_beijing.jpg"
            alt="背景图"
            class="background-image"
          />
        </div>

        <!-- 主内容区 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    <!-- 在模板底部添加编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="修改标题" width="30%">
      <el-input
        v-model="editingTitle"
        placeholder="请输入新的标题"
        maxlength="50"
        show-word-limit
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button chat_type="primary" @click="saveTitle">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
  <router-view v-else />
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Monitor,
  Document,
  PieChart,
  Reading,
  ChatLineRound,
  Plus,
  Delete,
  Edit,
  SwitchButton,
  Setting,
  User,
  Lock,
  Loading,
  Warning,
  OfficeBuilding,
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  apiGetUserChatSessions,
  apiCreateUserChatSession,
  apiUpdateUserChatSession,
  apiDeleteUserChatSession,
  apiCreateUserChatMessages,
} from '@/api/chat'

// 使用 auth store
const authStore = useAuthStore()

// const userName = computed(() => authStore.user?.username || '')
const userRole = computed(() => authStore.user?.role)

onMounted(() => {
  authStore.restoreUser()
})

// 添加以下变量
const editDialogVisible = ref(false)
const editingTitle = ref('')
const editingId = ref('')

// 添加以下方法
// TODO
const showEditDialog = (item) => {
  editingId.value = item.id
  editingTitle.value =
    item.title ||
    defaultHistoryTitle(
      sessionList.value.findIndex((i) => String(i.id) === String(item.id))
    )
  editDialogVisible.value = true
}

const saveTitle = async () => {
  if (!editingId.value) return

  try {
    // 调用 API 更新标题
    await apiUpdateUserChatSession(editingId.value, {
      title: editingTitle.value,
    })

    // 更新本地列表
    const chat_mode = activeMenu.value
    const sessions_list = sessionData.value[chat_mode]
    const index = sessions_list.findIndex(
      (item) => String(item.id) === String(editingId.value)
    )

    if (index !== -1) {
      sessions_list[index].title = editingTitle.value
      editDialogVisible.value = false
      ElMessage.success('标题修改成功')
    }
  } catch (err) {
    console.error('修改标题失败:', err)
    ElMessage.error('修改标题失败')
  }
}

// 侧边栏宽度（默认为 '15vw' 展开时）
const defaultExpandedWidth = 360
const collapsedWidth = 50

const sidebarWidth = computed(() => {
  return sidebarCollapsed.value
    ? `${collapsedWidth}px`
    : `${resizableWidth.value}px`
})

const resizableWidth = ref(defaultExpandedWidth)

let isDragging = false

const startDragging = () => {
  if (sidebarCollapsed.value) {
    sidebarCollapsed.value = false // 拖动时强制展开
  }

  isDragging = true
  document.addEventListener('mousemove', handleDragging)
  document.addEventListener('mouseup', stopDragging)
}

const handleDragging = (e) => {
  if (!isDragging) return
  const min = 120
  const max = 600
  const newWidth = Math.min(Math.max(e.clientX, min), max)
  resizableWidth.value = newWidth
}

const stopDragging = () => {
  isDragging = false
  document.removeEventListener('mousemove', handleDragging)
  document.removeEventListener('mouseup', stopDragging)
}

onUnmounted(() => {
  stopDragging()
  if (historySwitchTimer) {
    clearTimeout(historySwitchTimer)
    historySwitchTimer = null
  }
})

// 路由相关
const route = useRoute()
const router = useRouter()
const isAuthPage = computed(
  () =>
    route.name === 'login' ||
    route.name === 'register' ||
    route.meta.standalone === true
)
// 当前激活的菜单项
const activeMenu = ref('dashboard')
const isLoading = ref(false)
const error = ref(null)
const isHistorySwitching = ref(false)
const HISTORY_SWITCH_FALLBACK_MS = 8000
const HISTORY_SWITCH_RELEASE_DELAY_MS = 150
let historySwitchTimer = null

const setHistorySwitching = (switching) => {
  if (historySwitchTimer) {
    clearTimeout(historySwitchTimer)
    historySwitchTimer = null
  }

  if (switching) {
    isHistorySwitching.value = true
    historySwitchTimer = setTimeout(() => {
      isHistorySwitching.value = false
      historySwitchTimer = null
    }, HISTORY_SWITCH_FALLBACK_MS)
    return
  }

  historySwitchTimer = setTimeout(() => {
    isHistorySwitching.value = false
    historySwitchTimer = null
  }, HISTORY_SWITCH_RELEASE_DELAY_MS)
}

const releaseHistorySwitchLock = () => {
  setHistorySwitching(false)
}

// 添加退出方法
const logout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    chat_type: 'warning',
  })
    .then(() => {
      try {
        document.cookie =
          'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax'
        document.cookie =
          'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax'

        ElMessage.success('已退出登录')
        router.push('/login')
      } catch (error) {
        console.error('Logout state clearing error:', error)
        ElMessage.error('退出时发生错误')
      }
    })
    .catch(() => {
      // 用户取消退出，无需额外处理
    })
}

//------------------------------------------------------
//------------------------------------------------------
//------------------------------------------------------
//------------------------------------------------------
//------------------------------------------------------
// 设置激活菜单的逻辑
const setActiveMenu = () => {
  const path = route.path
  const menuMap = {
    '/bigModel': 'coding',
    '/coding-pdf': 'coding',
    '/coding-structured': 'coding',
    '/coding-history': 'coding',
    '/his-coding': 'his-coding',
    '/drgGrouping': 'drg',
    '/query': 'knowledge',
    '/homeIndex': 'dashboard',
    // 系统设置
    '/user-management': 'system',
    '/change-password': 'system',
  }

  const newMenu = route.meta.menuType || menuMap[path]

  if (newMenu && newMenu !== activeMenu.value) {
    activeMenu.value = newMenu
    // 这里不再调用 loadHistory() 否则会执行两次
  }
}

// 菜单选择处理
const handleMenuSelect = (index) => {
  const routeMap = {
    coding: '/bigModel',
    'his-coding': '/his-coding',
    drg: '/drgGrouping',
    knowledge: '/query',
    dashboard: '/homeIndex',
    'admin-console': '/admin',
    'user-management': '/user-management',
    'change-password': '/change-password',
  }

  if (route.path !== routeMap[index]) {
    router.push(routeMap[index])
  }
}

// 初始化时设置激活菜单
onMounted(() => {
  router.isReady().then(() => {
    setActiveMenu()
  })
})

watch(
  () => route.path,
  () => {
    setActiveMenu()
  }
)

// 历史记录数据结构
const sessionData = ref({
  coding: [],
  knowledge: [],
})
// 当前显示的历史记录 ID
const activeSession = ref('')

// 当前显示的历史记录列表
const sessionList = computed(() => {
  return sessionData.value[activeMenu.value] || []
})

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 是否显示历史记录侧边栏
const showHistorySidebar = computed(() => {
  if (route.path === '/coding-history') return false
  return ['coding', 'knowledge'].includes(activeMenu.value)
})

// 是否可以创建新对话
const canCreateNewChat = computed(() => {
  if (!activeSession.value) return true

  const session = getCurrentSessionData()

  if (!session) {
    return true
  }

  try {
    // 兼容 JSON 字符串和对象 (API 返回的 data 可能是对象)
    const dataObj =
      typeof session.data === 'string' ? JSON.parse(session.data) : session.data

    return dataObj.length > 0 //dataObj.questList && dataObj.questList.length > 0
  } catch (e) {
    return true
  }
})

// --- 核心修改：从 API 加载历史记录 ---
const loadHistory = async () => {
  if (!showHistorySidebar.value) return

  isLoading.value = true
  error.value = null

  try {
    // 调用后端 API 获取所有列表
    // 假设后端支持按 chat_type 过滤: GET /api/chat-history/?chat_type=coding
    const chat_mode = activeMenu.value // coding or knowledge
    // 发一个query，"chat_type": chat_type / knowledge
    const res = await apiGetUserChatSessions({ chat_mode })
    // 后端数据映射到前端结构
    // 确保 data 字段被正确处理
    sessionData.value[chat_mode] = res.data.data // sessions_list 当前用户的所有会话
    // 如果当前有列表但没有选中项，默认选中第一项
    if (sessionData.value[chat_mode].length > 0 && !activeSession.value) {
      activeSession.value = String(sessionData.value[chat_mode][0].id) // first item's ID
    }
    // 如果列表为空，自动创建新对话
    else if (sessionData.value[chat_mode].length === 0) {
      //else
      createNewChat(chat_mode)
    }
  } catch (err) {
    console.error('获取历史记录失败:', err)
    error.value = '获取历史记录失败，请检查网络'
  } finally {
    isLoading.value = false //加载完毕
  }
}

// 切换菜单时更新历史记录
watch(
  () => activeMenu.value,
  () => {
    if (showHistorySidebar.value) {
      // 切换菜单时，先清空当前选中，等待加载
      activeSession.value = ''
      loadHistory()
    }
  },
  { immediate: false }
)

// 切换侧边栏状态
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 开始新对话
const startNewChat = () => {
  if (isHistorySwitching.value || !canCreateNewChat.value) {
    return
  }
  const chat_type = activeMenu.value
  createNewChat(chat_type)
}

// --- 核心修改：通过 API 创建新对话 ---
const createNewChat = async (chat_mode) => {
  try {
    const newItem = {
      chat_mode: chat_mode,
      title: '新对话', //defaultHistoryTitle(sessionData.value[chat_mode] ? sessionData.value[chat_mode].length : 0) //'新对话', // 后端可设默认值
    }

    const res = await apiCreateUserChatSession(newItem)

    const createdSessions = res.data.data //返回新创建的会话
    activeSession.value = String(createdSessions.id) // uuid
    // 导航到目标
    if (chat_mode === 'coding') {
      router.push({
        path: '/bigModel',
        query: { historyId: createdSessions.id },
      })
    }

    if (res.data.code == 201) {
      //已经存在为空的了
      return
    }

    //如果是新创建的，则加入到列表中
    if (!sessionData.value[chat_mode]) {
      sessionData.value[chat_mode] = []
    }
    sessionData.value[chat_mode].unshift(createdSessions)
  } catch (err) {
    console.error('创建新对话失败:', err)
    ElMessage.error('无法创建新对话')
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${d
    .getMinutes()
    .toString()
    .padStart(2, '0')}`
}

// 默认历史记录标题
const defaultHistoryTitle = (index) => {
  return activeMenu.value === 'coding'
    ? `编码案例 ${index + 1}`
    : `知识查询 ${index + 1}`
}

// --- 核心修改：保存聊天内容到后端 ---
// ---------- ChatMessages ----------
const saveChatContent = async (id, content, old_content) => {
  const chat_mode = activeMenu.value // coding or knowledge
  const sessions_list = sessionData.value[chat_mode] // questList
  const item = sessions_list.find((item) => String(item.id) === String(id))

  if (item) {
    // 更新本地状态（为了UI即时响应）
    item.data = content

    // 如果没有标题，自动生成标题逻辑 (保持原有逻辑)
    let newTitle = item.title
    if (!item.title) {
      const caseCount =
        sessions_list.filter(
          (i) =>
            String(i.id) !== String(id) &&
            i.title &&
            i.title.startsWith(chat_mode === 'coding' ? '编码案例' : '知识查询')
        ).length + 1

      newTitle =
        chat_mode === 'coding' ? `编码案例${caseCount}` : `知识查询${caseCount}`
      item.title = newTitle
    }

    try {
      let addedItems = []
      if (content.length > old_content.length) {
        addedItems = content.slice(old_content.length)
      }
      if (addedItems.length === 0) {
        return []
      }
      //只更新新增的内容
      const new_data_list =
        typeof addedItems === 'string' ? JSON.parse(addedItems) : addedItems

      const resp = await apiCreateUserChatMessages({
        session_id: id, //会话id
        messages: new_data_list, //消息
      })

      // 更新时间
      item.updated_at = new Date().toISOString()
      //前端根据更新时间实时排序
      sessions_list.sort((a, b) => {
        // 将时间字符串转换为时间戳进行比较
        return (
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )
      })

      const created_message_id = resp.data?.data?.message_id || []
      return created_message_id
    } catch (err) {
      console.error('保存聊天记录失败:', err)
      // 可以选择静默失败或提示用户
    }
  }
}

// 处理历史记录选择
const handleHistorySelect = async (id) => {
  if (isHistorySwitching.value || String(id) === String(activeSession.value)) {
    return
  }

  const chat_mode = activeMenu.value
  const sessions_list = sessionData.value[chat_mode] || []
  const selectedItem = sessions_list.find(
    (item) => String(item.id) === String(id)
  )

  if (!selectedItem) {
    return
  }

  setHistorySwitching(true)
  activeSession.value = String(id)

  try {
    if (chat_mode === 'coding') {
      await router.push({ path: '/bigModel', query: { historyId: id } })
    }
  } catch (err) {
    console.error('切换历史会话失败:', err)
    ElMessage.error('切换对话失败，请稍后重试')
    releaseHistorySwitchLock()
  } finally {
    if (chat_mode !== 'coding') {
      releaseHistorySwitchLock()
    }
  }
}

// 获取当前选中的历史记录数据
const getCurrentSessionData = () => {
  const chat_mode = activeMenu.value
  const sessions_list = sessionData.value[chat_mode] || []
  return sessions_list.find(
    (item) => String(item.id) === String(activeSession.value)
  )
}

// 确认删除历史记录
const confirmDelete = (id) => {
  ElMessageBox.confirm('确定要删除这条历史记录吗?', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    chat_type: 'warning',
  })
    .then(() => {
      deleteHistory(id)
    })
    .catch(() => {})
}

// --- 核心修改：通过 API 删除 ---
const deleteHistory = async (id) => {
  try {
    await apiDeleteUserChatSession(id)

    const chat_mode = activeMenu.value
    const sessions_list = sessionData.value[chat_mode]

    // 前端移除
    sessionData.value[chat_mode] = sessions_list.filter(
      (item) => String(item.id) !== String(id)
    )

    ElMessage.success('删除成功')

    // 如果删除的是当前选中的记录，自动选择最近的记录
    if (String(activeSession.value) === String(id)) {
      const nextItem = sessionData.value[chat_mode][0]
      if (nextItem) {
        setHistorySwitching(true)
        activeSession.value = String(nextItem.id)
        if (chat_mode === 'coding') {
          router.push({ path: '/bigModel', query: { historyId: nextItem.id } })
        } else {
          releaseHistorySwitchLock()
        }
      } else {
        // 如果删完了，创建新的
        createNewChat(chat_mode)
      }
    }
  } catch (err) {
    console.error('删除失败:', err)
    ElMessage.error('删除失败')
  }
}

// 向祖孙们传递数据和方法
provide('historyMethods', {
  saveChatContent,
  getCurrentSessionData,
  activeSession: computed(() => activeSession.value),
  setHistorySwitching,
})

defineExpose({
  saveChatContent,
  getCurrentSessionData,
  activeSession,
})
</script>

<style lang="scss" scoped>
.sidebar-resizer {
  width: 4px;
  cursor: col-resize;
  background-color: #dcdfe6;
  transition: background-color 0.3s;
  position: relative;
  z-index: 2;
}

.sidebar-resizer:hover {
  background-color: #409eff;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;

  .app-header {
    height: 90px;
    border-bottom: 1px solid #e6e6e6;
    background-color: #fff;
    padding: 0;

    .header-content {
      display: flex;
      align-items: center;
      height: 100%;
      padding: 0 20px;
      justify-content: space-between; // 关键：让内容分布在两端
      align-items: center; // 垂直居中

      .header-logo {
        margin-right: 30px;

        .logo-image {
          height: 70px;
          object-fit: contain;
        }
      }

      .main-menu {
        flex: 1;
        border-bottom: none;

        .el-menu-item {
          font-size: 16px;
          padding: 0 20px;
          height: 60px;
          display: flex;
          align-items: center;

          .el-icon {
            margin-right: 8px;
          }
        }
      }
      // 新增：右侧部分样式
      .header-right-section {
        display: flex;
        align-items: center;
        gap: 10px; // 按钮和 logo 之间的间距

        .partner-logos {
          display: flex;
          align-items: center;
          gap: 15px;
          margin-right: 10px; // Logo 和按钮之间的间距

          .partner-logo {
            height: 30px;
            object-fit: contain;
          }
        }
        .logout-button {
          min-height: 32px;
          .el-icon {
            font-size: 16px;
          }
        }
      }
    }
  }

  .app-body {
    height: calc(100vh - 90px);
    position: relative; // 为背景图容器定位
    .history-sidebar {
      border-right: 1px solid #e6e6e6;
      background-color: #fff;
      display: flex;
      flex-direction: column;
      transition: width 0.3s ease;
      z-index: 1;
      .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;

        h3 {
          margin: 0;
          font-size: 16px;
          color: #333;
        }

        .collapse-button {
          background-color: #f5f7fa;
          border: none;
        }
      }

      .history-list-container {
        flex: 1;
        overflow: hidden;

        .history-menu {
          border-right: none;

          .el-menu-item {
            height: 60px;
            margin: 4px 0px;
            border-radius: 4px;

            .history-title {
              flex: 1;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }

            .history-date {
              font-size: 12px;
              color: #999;
              margin-left: 8px;
            }
          }
        }
      }

      .new-chat-container {
        padding: 16px;
        border-top: 1px solid #faf4f4;

        .new-chat-button {
          width: 100%;
        }
      }
    }

    .sidebar-resizer {
      width: 1px;
      cursor: col-resize;
      background-color: #fff;
      transition: background-color 0.3s;
      position: relative;
      z-index: 1;
      display: v-bind('showHistorySidebar ? "block" : "none"');
    }

    // 固定背景容器
    .background-container {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 0;
      overflow: hidden;
      pointer-events: none;
      .background-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.3;
        transition: opacity 0.3s ease;
      }
    }

    .main-content {
      background-color: transparent;
      flex: 1;
      padding: 20px 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      overflow-x: auto;
      position: relative;
      z-index: 1;
      pointer-events: auto;
    }
  }
}
.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--el-text-color-secondary);

  .el-icon {
    margin-right: 8px;
    font-size: 18px;
  }
}

.error-state {
  color: var(--el-color-error);
}

.history-menu {
  .el-menu-item {
    position: relative;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-right: 70px; // 为两个按钮留出更多空间

    .history-switching-icon {
      margin-left: 8px;
      color: var(--el-color-primary);
      flex-shrink: 0;
    }

    .edit-button,
    .delete-button {
      position: absolute;
      opacity: 0;
      transition: opacity 0.3s;
    }

    .edit-button {
      right: 40px; // 编辑按钮在删除按钮左侧
    }

    .delete-button {
      right: 8px;
    }

    &:hover .edit-button,
    &:hover .delete-button {
      opacity: 1;
    }
  }

  &.is-switching {
    cursor: wait;

    .el-menu-item {
      opacity: 0.72;
    }
  }
}
.el-menu-item span {
  font-weight: 500 !important;
}
</style>
