// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiLogin, apiLogout, apiRegister, apiMe } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const fetchMe = async () => {
    try {
      const { data } = await apiMe()
      if (data && data.code === 200 && data.data) {
        user.value = data.data
        localStorage.setItem('user_info', JSON.stringify(data.data))
      } else {
        user.value = null
      }
    } catch (e) {
      user.value = null
    }
    return user.value
  }

  const login = async (username, password) => {
    loading.value = true
    try {
      const { data } = await apiLogin({ username, password })
      if (data.code === 200) {
        // 保存用户基本信息到 localStorage
        if (data.data) {
          const userInfo = {
            username: data.data.username,
            id: data.data.id,
            role: data.data.role,
          }
          localStorage.setItem('user_info', JSON.stringify(userInfo))
          user.value = userInfo
        }
        return true
      }
      return false
    } finally {
      loading.value = false
    }
  }

  const register = async (username, password, email, password2) => {
    loading.value = true
    try {
      const payload = { username, password }
      if (email) payload.email = email
      if (password2) payload.password2 = password2
      const { data } = await apiRegister(payload)
      return data.code === 200
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    await apiLogout()
    user.value = null
    localStorage.removeItem('user_info')
  }

  // 从 localStorage 恢复用户信息
  const restoreUser = () => {
    const userInfo = localStorage.getItem('user_info')
    if (userInfo) {
      try {
        user.value = JSON.parse(userInfo)
      } catch (e) {
        user.value = null
      }
    }
  }

  // 检查是否是管理员 (role === 0)
  const isAdmin = () => {
    return user.value && user.value.role === 0
  }

  // 获取当前用户角色
  const getUserRole = () => {
    return user.value?.role
  }

  // 初始化时恢复用户信息
  restoreUser()

  return {
    user,
    loading,
    fetchMe,
    login,
    logout,
    register,
    restoreUser,
    isAdmin,
    getUserRole,
  }
})
