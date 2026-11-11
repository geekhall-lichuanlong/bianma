// src/api/admin.js
// 病案编码管理后台接口层（后端挂载于 /qy/admin/，经 Vite 代理 /api → Django :8088）
import http from './http'

// ---------- 元信息 ----------
export const apiAdminMe = () => http.get('/qy/admin/me/')
export const apiAdminDepartments = () => http.get('/qy/admin/departments/')

// ---------- 版本迭代 ----------
export const apiAdminVersions = (params) => http.get('/qy/admin/versions/', { params })
export const apiAdminCreateVersion = (data) => http.post('/qy/admin/versions/', data)
export const apiAdminUpdateVersion = (id, data) =>
  http.patch(`/qy/admin/versions/${id}/`, data)
export const apiAdminDeleteVersion = (id) => http.delete(`/qy/admin/versions/${id}/`)
export const apiAdminAccuracyTrend = (params) =>
  http.get('/qy/admin/accuracy/trend/', { params })
export const apiAdminAccuracyExport = (params) =>
  http.get('/qy/admin/accuracy/export/', { params, responseType: 'blob' })
export const apiAdminAccuracyReviews = (params) =>
  http.get('/qy/admin/accuracy/reviews/', { params })
export const apiAdminCreateReviews = (data) =>
  http.post('/qy/admin/accuracy/reviews/', data)
export const apiAdminClearReviews = (params) =>
  http.delete('/qy/admin/accuracy/reviews/', { params })

// ---------- 疑难病例讨论 ----------
export const apiAdminCases = (params) => http.get('/qy/admin/cases/', { params })
export const apiAdminCreateCase = (data) => http.post('/qy/admin/cases/', data)
export const apiAdminCaseDetail = (id) => http.get(`/qy/admin/cases/${id}/`)
export const apiAdminCaseAction = (id, data) =>
  http.patch(`/qy/admin/cases/${id}/`, data)
export const apiAdminCaseAssign = (id, data) =>
  http.post(`/qy/admin/cases/${id}/assign/`, data)
export const apiAdminCaseFeedback = (id, data) =>
  http.post(`/qy/admin/cases/${id}/feedback/`, data)
export const apiAdminCaseRemind = (id) => http.post(`/qy/admin/cases/${id}/remind/`)
export const apiAdminCaseAutoAssign = (data) =>
  http.post('/qy/admin/cases/auto-assign/', data || {})
export const apiAdminCaseFilterOptions = () =>
  http.get('/qy/admin/cases/filter-options/')

// ---------- 轮值安排 ----------
export const apiAdminRotationConfig = (params) =>
  http.get('/qy/admin/rotation/config/', { params })
export const apiAdminSaveRotationConfig = (data) =>
  http.post('/qy/admin/rotation/config/', data)
export const apiAdminDeleteRotationConfig = (id) =>
  http.delete('/qy/admin/rotation/config/', { params: { id } })
export const apiAdminExperts = () => http.get('/qy/admin/experts/')
export const apiAdminCreateExpert = (data) => http.post('/qy/admin/experts/', data)
export const apiAdminUpdateExpert = (id, data) =>
  http.patch(`/qy/admin/experts/${id}/`, data)
export const apiAdminDeleteExpert = (id) => http.delete(`/qy/admin/experts/${id}/`)
