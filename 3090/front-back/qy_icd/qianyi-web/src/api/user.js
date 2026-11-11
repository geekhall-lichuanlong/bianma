import http from './http'

// 获取用户列表
export const apiGetUsers = (params) => http.get('/qy/users/', { params })

// 创建用户
export const apiCreateUser = (data) => http.post('/qy/users/', data)

// 编辑用户信息
export const apiUpdateUser = (id, data) => http.patch(`/qy/users/${id}/`, data)

// 更新用户状态
export const apiUpdateUserStatus = (id, status) =>
  http.patch(`/qy/users/${id}/status/`, { status })

// 删除用户
export const apiDeleteUser = (id) => http.delete(`/qy/users/${id}/delete/`)

// 修改密码
export const apiChangePassword = (data) =>
  http.post('/qy/users/change-password/', data)
