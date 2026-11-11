// Suppress waiting/completion placeholders while preserving model output/errors.
export const isAgentStatusPlaceholder = (answer) => {
  if (!answer) return false
  const status = String(answer.agent_status || answer.status || '').toLowerCase()
  if (answer.isAgentError || answer.isModelError || ['failed', 'error'].includes(status)) {
    return false
  }
  if (answer.isAgentStatus || answer.type === 'agent_status') return true
  if (answer.isJsonResponse || answer.isMarkdownTable || answer.reasoning || answer.think) {
    return false
  }

  // Older saved records may contain the waiting text without its status flag.
  const content = String(answer.content || '').replace(/\s+/g, '')
  if (/^正在调用智能体\d*[。.!！…]*$/.test(content)) return true
  const name = String(answer.name || answer.agent_name || '').replace(/\s+/g, '')
  return Boolean(name && content === `正在调用${name}`)
}
