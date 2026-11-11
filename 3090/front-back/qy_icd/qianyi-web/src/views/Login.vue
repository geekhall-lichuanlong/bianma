<template>
  <div class="auth-wrapper">
    <div class="background-elements">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="pulse-dot"></div>
    </div>

    <el-card class="auth-card">
      <div class="medical-header">
        <div class="medical-icon">
          <img :src="logoUrl" alt="千医·牍智" class="logo-image" />
        </div>
      </div>
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="0"
        class="login-form"
      >
        <el-form-item prop="username" class="full-width-item">
          <div class="input-with-icon">
            <el-icon class="input-icon"><User /></el-icon>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
            />
          </div>
        </el-form-item>

        <el-form-item prop="password" class="full-width-item">
          <div class="input-with-icon">
            <el-icon class="input-icon"><Lock /></el-icon>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
            />
          </div>
        </el-form-item>

        <el-form-item class="full-width-item">
          <el-button
            type="primary"
            :loading="auth.loading"
            @click="onLogin"
            class="login-btn"
            size="large"
          >
            {{ auth.loading ? '登录中...' : '登录系统' }}
          </el-button>
        </el-form-item>

        <!-- <div class="auth-footer">
          <span>还没有账号?</span>
          <el-button link type="primary" @click="goRegister" class="register-link" style="margin-bottom: 3px;">立即注册</el-button>
        </div> -->
      </el-form>
    </el-card>

    <!-- 底部信息 -->
    <div class="footer-info">
      <p>2025 千医·牍智 智能助力 精准高效</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import logoUrl from '../assets/logo_02.png'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度至少3个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' },
  ],
}

const redirect = () => {
  const to = route.query.redirect || '/homeIndex'
  router.replace(String(to))
}

const onLogin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const ok = await auth.login(form.username, form.password)
      if (ok) {
        ElMessage.success('登录成功')
        redirect()
      } else {
      }
    } catch (error) {
      console.error('登录异常:', error)
    }
  })
}

const goRegister = () => {
  router.push({
    name: 'register',
    query: { redirect: route.query.redirect || '/homeIndex' },
  })
}
</script>

<style scoped>
.auth-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%);
  position: relative;
  overflow: hidden;
}

.background-elements {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(24, 144, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 120px;
  height: 120px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 80px;
  height: 80px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.circle-3 {
  width: 60px;
  height: 60px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

.pulse-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #1890ff;
  border-radius: 50%;
  top: 30%;
  right: 20%;
  animation: pulse 2s infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(0.8);
    opacity: 1;
  }
}

.auth-card {
  width: 420px;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(24, 144, 255, 0.15);
  border: none;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.medical-header {
  text-align: center;
  margin-bottom: 30px;
}

.medical-icon {
  margin-bottom: 15px;
}

.logo-image {
  max-width: 180px;
  height: auto;
}

.system-title {
  font-size: 22px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 5px;
}

.system-subtitle {
  font-size: 12px;
  color: #8c8c8c;
  letter-spacing: 1px;
}

.title {
  text-align: center;
  margin-bottom: 30px;
  font-size: 20px;
  font-weight: 500;
  color: #262626;
  position: relative;
}

.title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 3px;
  background: linear-gradient(90deg, #1890ff, #36cfc9);
  border-radius: 2px;
}

.login-form {
  margin-top: 10px;
  width: 100%;
}

/* 修复输入框宽度问题 */
.full-width-item {
  width: 100%;
}

:deep(.full-width-item .el-form-item__content) {
  width: 100%;
  margin-left: 0 !important;
}

.input-with-icon {
  position: relative;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  color: #8c8c8c;
}

/* 确保输入框占满宽度 */
:deep(.el-input) {
  width: 100%;
}

:deep(.el-input__wrapper) {
  width: 100%;
  padding-left: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.remember-forgot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.forgot-password {
  padding: 0;
  font-size: 13px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  background: linear-gradient(90deg, #1890ff, #36cfc9);
  border: none;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(24, 144, 255, 0.4);
}

.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #8c8c8c;
}

.register-link {
  font-weight: 500;
  margin-left: 5px;
}

.footer-info {
  position: absolute;
  bottom: 20px;
  width: 100%;
  text-align: center;
  font-size: 12px;
  color: #8c8c8c;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .auth-card {
    width: 90%;
    margin: 0 auto;
    padding: 20px;
  }

  .auth-wrapper {
    padding: 20px;
  }
}
</style>
