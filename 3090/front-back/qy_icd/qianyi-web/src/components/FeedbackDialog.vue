<template>
    <el-dialog v-model="visible" :title="dialogTitle" width="500px" center class="custom-feedback-dialog"
        :close-on-click-modal="false" modal-penetrable :modal="false" append-to-body draggable>
        <div class="feedback-dialog-content">
            <!-- 1. 反馈类型区域（优化：预设标签 + 自定义输入） -->
            <div class="feedback-section">
                <div class="section-title">反馈类型 (必选)</div>
                <div class="feedback-tags-container">
                    <el-tag v-for="(tag, index) in currentFeedbackOptions" :key="index" class="option-tag"
                        :class="{ 'active-tag': selectedFeedbackTag === tag && !customTagText }"
                        :effect="selectedFeedbackTag === tag && !customTagText ? 'dark' : 'plain'" type="primary"
                        @click="selectFeedbackType(tag)">
                        {{ tag }}
                    </el-tag>
                </div>
                <!-- 自定义标签输入框 -->
                <div class="custom-tag-input">
                    <el-input 
                        v-model="customTagText" 
                        placeholder="自定义反馈类型" 
                        maxlength="50"
                        @input="clearSelectedTag"
                        clearable
                    />
                </div>
            </div>

            <!-- 2. 解决方法区域 -->
            <div class="feedback-section">
                <div class="section-title">{{ resolveTitle }}</div>
                <el-input v-model="remarkText" type="textarea" :rows="4" placeholder="请输入具体的解决方法或您的建议..."
                    maxlength="300" show-word-limit />
            </div>

            <div class="dialog-tips">您的反馈将帮助我们改进AI编码准确性</div>
        </div>

        <template #footer>
            <el-button @click="closeDialog">取消</el-button>
            <el-button type="danger" @click="handleDelete" :disabled="!isExistingFeedback">
                删除反馈
            </el-button>
            <el-button type="primary" @click="handleConfirm" :disabled="!getFinalFeedbackTag">
                {{ isExistingFeedback ? '更新反馈' : '提交反馈' }}
            </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
    apiGetRemarkChatMessageFeedback,
    apiSubmitChatMessageFeedback,
    apiDeleteChatMessageFeedback,
} from '@/api/chat'

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    feedbackData: {
        type: Object,
        required: true,
        // Expected structure: { message_id, type ('like'/'dislike'), row_id, category, sessionId }
    },
    // Passing the map to check if feedback exists purely for UI state initialization if needed,
    // though the API call inside open is better.
    existingStatus: {
        type: String,
        default: ''
    }
})

const emit = defineEmits(['update:modelValue', 'feedback-success', 'feedback-deleted'])

// Constants - 保留原有预设标签
const LIKE_OPTIONS = ['考虑了合并编码', '添加了手术另编码', '发现潜在诊断', '发现潜在手术操作']
const DISLIKE_OPTIONS = ['主要诊断选择错误', '主要手术选择错误', '顺序需要调整', '多编', '漏编', '编码需更精细化']
const OVERALL_OPTIONS = ['优秀', '一般', '错误', '错误严重']

// State - 新增自定义标签变量
const visible = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
})

const selectedFeedbackTag = ref('')
const customTagText = ref('') // 自定义标签输入内容
const remarkText = ref('')
const isExistingFeedback = ref(false)

// Computed
const dialogTitle = computed(() => {
    return props.feedbackData.type === 'like' ? '点赞反馈' : props.feedbackData.type === 'comment' ? '整体反馈' : '点踩反馈'
})

const resolveTitle = computed(() => {
    return props.feedbackData.type === 'like' ? '解决方法（可选）' : props.feedbackData.type === 'comment' ? '正确结果（填写疾病/手术名称，名称之间用分号隔开）' : '解决方法（必填）'
})

const currentFeedbackOptions = computed(() => {
    return props.feedbackData.type === 'like' ? LIKE_OPTIONS : props.feedbackData.type === 'comment' ? OVERALL_OPTIONS : DISLIKE_OPTIONS
})

// 计算最终的反馈类型（优先自定义，其次预设）
const getFinalFeedbackTag = computed(() => {
    return customTagText.value.trim() || selectedFeedbackTag.value.trim()
})

// Methods
// 选择预设标签（清空自定义输入）
const selectFeedbackType = (tag) => {
    customTagText.value = '' // 选预设标签时清空自定义输入
    if (selectedFeedbackTag.value === tag) {
        selectedFeedbackTag.value = ''
    } else {
        selectedFeedbackTag.value = tag
    }
}

// 输入自定义标签时清空选中的预设标签
const clearSelectedTag = () => {
    if (customTagText.value.trim()) {
        selectedFeedbackTag.value = ''
    }
}

const closeDialog = () => {
    visible.value = false
}

// 初始化弹窗状态（优化：增加自定义标签重置，兼容回显自定义标签）
const initDialog = async () => {
    remarkText.value = ''
    selectedFeedbackTag.value = ''
    customTagText.value = '' // 重置自定义标签
    isExistingFeedback.value = false

    const { message_id, category, type, row_id, sessionId } = props.feedbackData

    // Logic: If the parent tells us the saved status matches the current action (like vs like), fetch details
    if (props.existingStatus && props.existingStatus === type) {
        isExistingFeedback.value = true
        try {
            const res = await apiGetRemarkChatMessageFeedback({
                session_id: sessionId,
                message_id: message_id,
                category: category,
                row_id: row_id
            })
            if (res.data.code == 200) {
                remarkText.value = res.data.data || ''
                const savedTag = res.data.tag || ''
                // 回显逻辑：如果保存的标签在预设列表中，选中预设；否则显示在自定义输入框
                if (currentFeedbackOptions.value.includes(savedTag)) {
                    selectedFeedbackTag.value = savedTag
                } else {
                    customTagText.value = savedTag
                }
            }
        } catch (error) {
            ElMessage.error('获取反馈内容失败，请重试')
        }
    }
}

// Watch for dialog opening
watch(() => props.modelValue, (newVal) => {
    if (newVal) {
        initDialog()
    }
})

const handleConfirm = async () => {
    // 验证：必须有反馈类型（预设或自定义）
    const finalTag = getFinalFeedbackTag.value
    if (!finalTag) {
        ElMessage.warning('请选择或输入反馈类型')
        return
    }
    if (props.feedbackData.type === 'dislike' && !remarkText.value.trim()) {
        ElMessage.warning('请输入反馈内容')
        return
    }

    const { message_id, category, type, row_id, sessionId } = props.feedbackData

    try {
        const res = await apiSubmitChatMessageFeedback({
            session_id: sessionId,
            message_id: message_id,
            category: category,
            type: type,
            reason: finalTag, // 使用最终的反馈类型（自定义/预设）
            remark: remarkText.value,
            row_id: row_id,
        })

        if (res.data.code == 200) {
            ElMessage.success('反馈已提交！')
            emit('feedback-success', { message_id, category, row_id, type })
            closeDialog()
        }
    } catch (error) {
        ElMessage.error('提交失败，请重试')
    }
}

const handleDelete = async () => {
    try {
        const { message_id, category, row_id, sessionId } = props.feedbackData

        const res = await apiDeleteChatMessageFeedback({
            session_id: sessionId,
            message_id: message_id,
            category: category,
            row_id: row_id,
        })

        if (res.data.code == 200) {
            ElMessage.success('反馈已删除！')
            emit('feedback-deleted', { message_id, category, row_id })
            closeDialog()
        } else {
            ElMessage.error('反馈删除失败！')
        }
    } catch (error) {
        ElMessage.error('删除失败，请重试')
    }
}
</script>

<style scoped>
.feedback-dialog-content {
    padding: 0 10px;
}

.feedback-section {
    margin-bottom: 20px;
}

.section-title {
    font-weight: bold;
    margin-bottom: 10px;
    color: #333;
    font-size: 14px;
}

.feedback-tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 12px; /* 给自定义输入框留间距 */
}

.option-tag {
    cursor: pointer;
    padding: 8px 15px;
    font-size: 13px;
    height: auto;
    transition: all 0.3s;
    border: 1px solid #dcdfe6;
}

.option-tag.active-tag {
    border-color: var(--el-color-primary);
    font-weight: bold;
}

.option-tag:hover {
    opacity: 0.8;
    transform: translateY(-1px);
}

/* 自定义输入框样式 */
.custom-tag-input {
    margin-top: 8px;
}

.dialog-tips {
    font-size: 12px;
    color: #909399;
    margin-top: -5px;
}
</style>