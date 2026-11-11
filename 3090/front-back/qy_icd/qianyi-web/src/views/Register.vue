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
        class="register-form"
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

        <el-form-item prop="password2" class="full-width-item">
          <div class="input-with-icon">
            <el-icon class="input-icon"><Lock /></el-icon>
            <el-input
              v-model="form.password2"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              show-password
            />
          </div>
        </el-form-item>

        <el-form-item class="full-width-item">
          <el-button
            type="success"
            :loading="auth.loading"
            @click="onRegister"
            class="register-btn"
            size="large"
          >
            {{ auth.loading ? '注册中...' : '注册账号' }}
          </el-button>
        </el-form-item>

        <div class="auth-footer">
          <span>已有账号?</span>
          <el-button
            link
            type="primary"
            @click="goLogin"
            class="login-link"
            style="margin-bottom: 3px"
            >立即登录</el-button
          >
        </div>
      </el-form>
    </el-card>

    <!-- 底部信息 -->
    <div class="footer-info">
      <p>© 2025 千医·牍智 · 赋能医疗健康未来</p>
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
  password2: '',
})

const validatePassword2 = (rule, value, callback) => {
  if (!value) return callback(new Error('请再次输入密码'))
  if (value !== form.password) return callback(new Error('两次输入密码不一致'))
  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度至少3个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' },
  ],
  password2: [{ validator: validatePassword2, trigger: 'blur' }],
}

const onRegister = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    const ok = await auth.register(form.username, form.password, form.password2)
    if (ok) {
      ElMessage.success('注册成功，请登录')
      const to = route.query.redirect || '/login'
      router.replace(String(to))
    }
  })
}

const goLogin = () => {
  router.push({
    name: 'login',
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
  background: rgba(103, 194, 58, 0.1);
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
  background: #67c23a;
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
  box-shadow: 0 10px 30px rgba(103, 194, 58, 0.15);
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

.register-form {
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
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.register-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  background: linear-gradient(90deg, #67c23a, #85ce61);
  border: none;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(103, 194, 58, 0.4);
}

.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #8c8c8c;
}

.login-link {
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
