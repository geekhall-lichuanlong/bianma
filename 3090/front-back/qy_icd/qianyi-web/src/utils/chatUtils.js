// 辅助函数：从文本提取诊断信息
export const extractDiagnoses = (text) => {
    const matches = text.match(/诊断: (.+?) \(代码: (\w+\.\w+)\)/g)
    return matches
        ? matches.map((m) => {
            const [, name, code] = m.match(/诊断: (.+?) \(代码: (\w+\.\w+)\)/)
            return { name, code }
        })
        : []
}

// 辅助函数：判断问题是否为JSON格式
export const isJsonQuestion = (question) => {
    try {
        const parsed = JSON.parse(question)
        return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
    } catch (error) {
        return false
    }
}

// 辅助函数：解析JSON格式的问题
export const parseJsonQuestion = (question) => {
    try {
        return JSON.parse(question)
    } catch (error) {
        return {}
    }
}

// 辅助函数：从文本提取手术信息
export const extractProcedures = (text) => {
    const matches = text.match(/手术: (.+?) \(代码: (\w+\.\w+)\)/g)
    return matches
        ? matches.map((m) => {
            const [, name, code] = m.match(/手术: (.+?) \(代码: (\w+\.\w+)\)/)
            return { name, code }
        })
        : []
}

// 格式化Markdown单元格内容的函数
export const formatCellContent = (content) => {
    if (!content) return ''

    let formatted = content.toString()

    // 处理加粗 **text** 或 __text__
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>')

    // 处理斜体 *text* 或 _text_
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
    formatted = formatted.replace(/_(.*?)_/g, '<em>$1</em>')

    // 处理行内代码 `code`
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>')

    // 处理换行
    formatted = formatted.replace(/\n/g, '<br>')

    return formatted
}
