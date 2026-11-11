import http from './http'

//apiGetUserChatSessions
//apiCreateUserChatSession
//apiUpdateUserChatSession
//apiDeleteUserChatSession
//apiCreateUserChatMessages

// 获取会话列表
export const apiGetUserChatSessions = (params) =>
  http.get('/qy/chat-sessions/', { params })

// 创建会话
export const apiCreateUserChatSession = (data) =>
  http.post('/qy/chat-sessions/create/', data)

// 编辑会话信息
export const apiUpdateUserChatSession = (id, data) =>
  http.patch(`/qy/chat-sessions/${id}/update/`, data)

// 删除会话
export const apiDeleteUserChatSession = (id) =>
  http.delete(`/qy/chat-sessions/${id}/delete/`)

// 获取消息
export const apiGetUserChatMessages = (params) =>
  http.get('/qy/chat-messages/', { params })

// 更新消息处理状态
export const apiUpdateUserChatMessagesStatus = (data) =>
  http.post('/qy/chat-messages-update-status/', data)

// 获取所有会话的所有消息
export const apiGetUserChatMessagesAll = (params) =>
  http.get('/qy/chat-messages-all/', { params })

// 获取所有非管理员用户的所有会话的所有消息
export const apiGetUserChatMessagesAllAll = (params) =>
  http.get('/qy/chat-messages-all-all/', { params })

// 创建消息
export const apiCreateUserChatMessages = (data) =>
  http.post('/qy/chat-messages/create/', data)

// 获取某会话的所有反馈
export const apiGetAllChatMessageFeedback = (params) =>
  http.get('/qy/chat-messages/feedback/list/', { params })

// 获取所有会话的所有反馈
export const apiGetAllChatMessageFeedbackAll = () =>
  http.get('/qy/chat-messages/feedback/list-all/')

// 获取所有普通用户的所有会话的所有反馈
export const apiGetAllChatMessageFeedbackAllAll = () =>
  http.get('/qy/chat-messages/feedback/list-all-all/')

// 获取某条反馈内容
export const apiGetRemarkChatMessageFeedback = (data) =>
  http.post('/qy/chat-messages/feedback/remark/', data)

// 提交反馈
export const apiSubmitChatMessageFeedback = (data) =>
  http.post('/qy/chat-messages/feedback/', data)

// 删除反馈
export const apiDeleteChatMessageFeedback = (data) =>
  http.post('/qy/chat-messages/feedback/delete/', data)

// ---------- 导出所有反馈 ------------
export const apiExportFeedback = () => 
  http.get('/qy/chat-messages/feedback/export/')

// 保存编码结果到数据库
export const apiSaveIcdCodes = (data) =>
  http.post('/qy/save-icd-codes/', data)
