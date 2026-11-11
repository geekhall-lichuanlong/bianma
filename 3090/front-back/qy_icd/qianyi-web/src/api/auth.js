// src/api/auth.js
import http from './http'
import { ElMessage } from 'element-plus'

export const apiLogin = (payload) => {
  return http
    .post('/qy/auth/login/', payload)
    .then((response) => {
      // 登录成功时保存 token 到 localStorage
      if (response.data.code === 200 && response.data.data.access_token) {
        localStorage.setItem('access_token', response.data.data.access_token)
      }
      return response
    })
    .catch((error) => {
      // 如果是401错误，显示特定的错误信息
      if (error.response && error.response.status === 401) {
        ElMessage.error('用户名或密码错误')
      } else if (
        error.response &&
        error.response.data &&
        error.response.data.msg
      ) {
        ElMessage.error(error.response.data.msg)
      } else {
        ElMessage.error('登录失败，请检查网络连接')
      }
      throw error
    })
}

export const apiLogout = () => {
  return http
    .post('/qy/auth/logout/')
    .then(() => {
      localStorage.removeItem('access_token')
      ElMessage.success('已退出登录')
    })
    .catch((error) => {
      localStorage.removeItem('access_token')
      ElMessage.error('退出登录失败')
      throw error
    })
}

export const apiRegister = (payload) => http.post('/qy/auth/register/', payload)
export const apiMe = () => http.get('/qy/auth/me/')
