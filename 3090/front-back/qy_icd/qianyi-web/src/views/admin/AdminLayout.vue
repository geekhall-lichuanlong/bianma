<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside width="212px" class="admin-aside">
      <div class="brand">
        <div class="brand-title">病案编码管理后台</div>
        <div class="brand-sub">千医 · 牍智 AIcode</div>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="admin-menu"
        background-color="#1e2a3a"
        text-color="#c7d2e0"
        active-text-color="#ffffff"
        @select="handleMenuSelect"
      >
        <el-menu-item
          v-for="item in menus"
          :key="item.path"
          :index="item.path"
          :disabled="item.disabled"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
          <el-tag v-if="item.phase" size="small" class="phase-tag" effect="plain">
            {{ item.phase }}
          </el-tag>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header height="56px" class="admin-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
          <el-tag v-if="pageSubTitle" size="small" type="info" effect="plain">
            {{ pageSubTitle }}
          </el-tag>
        </div>
        <div class="header-right">
          <el-tag size="small" effect="dark" type="primary">{{ me.roleName || '—' }}</el-tag>
          <span class="user-name">{{ me.realName || me.username }}</span>
          <el-button link @click="goHome">
            <el-icon><HomeFilled /></el-icon>
            <span>返回工作台</span>
          </el-button>
          <el-button link type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiAdminMe } from '@/api/admin'
import { apiLogout } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const me = ref({})

const menus = [
  { path: '/admin/version-trend', title: '版本迭代', icon: 'TrendCharts', disabled: false },
  { path: '/admin/difficult-cases', title: '疑难病例讨论', icon: 'ChatDotSquare', disabled: false },
  { path: '/admin/coding-detail', title: '编码详情', icon: 'Document', disabled: true, phase: '二期' },
  { path: '/admin/dashboard', title: '编码看板', icon: 'DataAnalysis', disabled: true, phase: '二期' },
  { path: '/admin/map', title: '编码地图', icon: 'MapLocation', disabled: true, phase: '三期' },
  { path: '/admin/school', title: '编码小课堂', icon: 'Reading', disabled: true, phase: '三期' },
]

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/cases')) return '/admin/difficult-cases'
  return route.path
})

const pageTitle = computed(() => {
  const titles = {
    '/admin/version-trend': '版本迭代 · 准确率优化效果',
    '/admin/difficult-cases': '疑难病例讨论',
  }
  if (route.path.startsWith('/admin/cases')) return '疑难病例详情'
  return titles[route.path] || '病案编码管理后台'
})

const pageSubTitle = computed(() => (route.path === '/admin/version-trend' ? '一期功能' : ''))

const handleMenuSelect = (path) => {
  if (path !== route.path) router.push(path)
}

const goHome = () => router.push('/homeIndex')

const handleLogout = () => {
  ElMessageBox.confirm('确认退出登录？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await apiLogout()
      } catch (e) {
        localStorage.removeItem('access_token')
      }
      router.push('/login')
    })
    .catch(() => {})
}

onMounted(async () => {
  try {
    const { data } = await apiAdminMe()
    if (data.code === 200) {
      me.value = data.data || {}
      if (!me.value.isBackend) {
        ElMessage.error('当前账号无管理后台权限')
        router.replace('/homeIndex')
      }
    }
  } catch (e) {
    ElMessage.error('获取账号信息失败')
  }
})
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background: #f4f6f9;
}

.admin-aside {
  background: #1e2a3a;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.brand {
  padding: 18px 16px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-title {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.brand-sub {
  color: #7f8fa6;
  font-size: 12px;
  margin-top: 4px;
}

.admin-menu {
  border-right: none;
  flex: 1;
}

.admin-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  font-size: 14px;
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: #1565c0 !important;
}

.phase-tag {
  margin-left: 6px;
  transform: scale(0.85);
  border-color: #5b6b7f;
  color: #9fb0c4;
}

.admin-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6eaf0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 14px;
  color: #4a5568;
}

.admin-main {
  padding: 16px;
  overflow-y: auto;
}
</style>
