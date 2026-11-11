<template>
  <div class="page-box">
    <!-- 欢迎界面 -->
    <div class="welcome-container" v-if="showWelcome && !conversationLoading">
      <img src="@/assets/logoOne.png" class="welcome-logo" alt="Logo" />
      <div class="welcome-text">
        Hi~千医·牍智AiCode智能编码助手已就位，请输入关键词/上传病历 →
        获取病案编码！ICDCoding
      </div>
    </div>

    <!-- 对话内容区域 -->
    <div class="ques-box" ref="answerBox">
      <!-- 加载状态 -->
      <div v-if="conversationLoading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 对话内容 -->
      <template v-else>
        <template v-for="(item, index) in conversationData" :key="item.no">
          <!-- 用户提问 -->
          <div class="ques-ddd">
            <div class="right ques-item">
              <img src="@/assets/user.jpg" class="avatar" alt="" />
              <span class="ques-text">{{ item.question }}</span>
            </div>

            <!-- AI回答 -->
            <div class="left ques-item">
              <img :src="getAvatarByIndex(index)" class="avatar" alt="" />

              <!-- 思考过程 -->
              <div v-if="item.think" class="sk-content">
                {{ item.think }}
              </div>

              <!-- 回答内容 -->
              <span class="ques-text">
                <span v-if="item.name" class="name-str">{{ item.name }}:</span>
                {{ item.content }}
              </span>

              <!-- 评论/备注 -->
              <div v-if="item.comment" class="comment-box">
                <el-icon><Comment /></el-icon>
                <span>{{ item.comment }}</span>
              </div>

              <!-- 表格结果展示 -->
              <div
                v-if="item.resultTable"
                class="final-result-table"
                v-html="item.resultTable"
              ></div>
            </div>
          </div>
        </template>
      </template>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <div class="ci-content">
        <el-input
          class="input-text"
          v-model.trim="inputVal"
          @keyup.enter="submitQuestion"
          :autosize="{ minRows: 1, maxRows: 4 }"
          type="textarea"
          placeholder="我是千医.牍智大模型,快来让我帮你病案编码吧~"
          :disabled="conversationLoading"
        />

        <div class="bottom-box flex-align">
          <div class="btn-box">
            <el-button
              type="primary"
              :icon="MessageBox"
              :loading="conversationLoading"
              @click="handleMedicalRecord"
            >
              病案首页填报
            </el-button>
            <el-button
              type="success"
              :icon="Document"
              :loading="conversationLoading"
              @click="handleInsuranceSettlement"
            >
              医保结算清单
            </el-button>
          </div>

          <div class="flex-align">
            <el-button
              type="primary"
              :icon="Position"
              :loading="conversationLoading"
              @click="submitQuestion"
            >
              发送
            </el-button>

            <el-upload
              class="ml10"
              action=""
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              accept=".jpg,.jpeg,.png,.pdf"
              :disabled="conversationLoading"
            >
              <el-button type="danger" :icon="Upload">上传文件</el-button>
            </el-upload>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件上传处理弹窗 -->
    <UploadProgressDialog
      v-model="showUploadModal"
      :current-step="currentStep"
      :progress-percentage="progressPercentage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
import {
  MessageBox,
  Document,
  Position,
  Upload,
  Comment,
} from '@element-plus/icons-vue'
// import UploadProgressDialog from '@/components/UploadProgressDialog.vue'
// import { fetchConversation, submitQuestion as apiSubmitQuestion } from '@/api/chat'

// 添加模拟API函数
const mockApi = {
  // 模拟获取对话历史
  fetchConversation: () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: [
            {
              no: 1,
              question: '如何诊断冠状动脉粥样硬化性心脏病？',
              name: 'AI助手',
              think: '分析患者症状、病史和检查结果...',
              content:
                '冠状动脉粥样硬化性心脏病的诊断需要结合临床症状、心电图、心脏超声和冠脉造影等检查结果综合判断。',
              comment: '建议进一步做冠脉CTA检查',
              resultTable: '',
            },
            {
              no: 2,
              question: '',
              name: '编码专家',
              think: '根据ICD-10编码规则...',
              content: '冠状动脉粥样硬化性心脏病的ICD编码为I25.10',
              comment: '注意区分不同类型',
              resultTable: generateMockTable(),
            },
          ],
        })
      }, 800) // 模拟网络延迟
    })
  },

  // 模拟提交问题
  submitQuestion: (data) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockResponses = [
          {
            no: Date.now(),
            question: '',
            name: '病案编码AI',
            think:
              '正在分析您的问题...\n根据病历描述，患者主要诊断为不稳定型心绞痛...',
            content: '根据ICD-10标准，您提供的病例主要诊断编码为I20.000',
            comment: '请注意核对主要诊断的选择',
            resultTable: generateMockTable(),
          },
          {
            no: Date.now() + 1,
            question: '',
            name: 'DRG分组助手',
            think: '正在计算DRG分组...\n根据主要诊断和手术操作...',
            content:
              '预分组结果为：FQ15 冠状动脉支架置入，伴重要合并症与伴随病',
            comment: '最终分组需以医保审核为准',
            resultTable: '',
          },
        ]
        resolve({ data: mockResponses })
      }, 1200) // 模拟处理时间
    })
  },
}

// 生成模拟表格数据
const generateMockTable = () => {
  return `
    <table class="final-result-table">
      <tbody>
        <tr class="header-row">
          <th colspan="6">病案编码结果</th>
        </tr>
        <tr class="sub-header-row">
          <td colspan="3" class="diagnosis-header">诊断信息</td>
          <td colspan="3" class="surgery-header">手术信息</td>
        </tr>
        <tr class="column-header">
          <th width="18%">序号</th>
          <th width="22%">名称</th>
          <th width="15%">ICD编码</th>
          <th width="18%">序号</th>
          <th width="22%">名称</th>
          <th width="15%">ICD编码</th>
        </tr>
        <tr class="main-row">
          <td class="index-cell">主要诊断</td>
          <td><strong>不稳定型心绞痛</strong></td>
          <td>I20.000</td>
          <td class="index-cell">主要手术</td>
          <td><strong>药物洗脱冠状动脉支架置入</strong></td>
          <td>36.0700</td>
        </tr>
        <tr class="data-row even-row">
          <td class="index-cell">其他诊断1</td>
          <td>冠状动脉粥样硬化性心脏病</td>
          <td>I25.103</td>
          <td class="index-cell">其他手术1</td>
          <td>经皮冠状动脉球囊扩张成形术</td>
          <td>00.6600x004</td>
        </tr>
      </tbody>
    </table>
  `
}

// 数据状态
const inputVal = ref('')
const showWelcome = ref(true)
const conversationData = ref([])
const conversationLoading = ref(false)
const useMockData = ref(true) // 控制是否使用模拟数据

// 获取对话历史 - 修改为支持模拟和真实API
const fetchConversation = async () => {
  if (useMockData.value) {
    return mockApi.fetchConversation()
  } else {
    // 这里保留原有的真实API调用
    // return await apiFetchConversation()
  }
}

// 上传相关状态
const showUploadModal = ref(false)
const currentStep = ref(1)
const progressPercentage = ref(0)

// 获取头像根据索引
const getAvatarByIndex = (index) => {
  const avatars = [
    '@/assets/touxiang/t1.jpg',
    '@/assets/touxiang/t2.jpg',
    '@/assets/touxiang/t3.jpg',
    '@/assets/touxiang/t4.jpg',
    '@/assets/touxiang/t5.jpg',
    '@/assets/touxiang/t6.jpg',
    '@/assets/touxiang/t7.jpg',
    '@/assets/touxiang/t8.jpg',
    '@/assets/touxiang/t9.jpg',
    '@/assets/touxiang/t10.jpg',
    '@/assets/logoOne.png',
  ]
  return avatars[Math.min(index, avatars.length - 1)]
}

// 提交问题 - 修改为支持模拟和真实API
const submitQuestion = async () => {
  if (!inputVal.value.trim() || conversationLoading.value) return

  const question = inputVal.value
  inputVal.value = ''
  showWelcome.value = false

  // 添加用户问题到对话列表
  conversationData.value.push({
    no: Date.now(),
    question,
    name: '',
    think: '',
    content: '',
    comment: '',
  })

  try {
    conversationLoading.value = true
    scrollToBottom()

    // 调用API获取回答
    const response = useMockData.value
      ? await mockApi.submitQuestion({ question })
      : await apiSubmitQuestion({ question }) // 保留真实API调用

    // 处理返回的数据
    if (response.data && Array.isArray(response.data)) {
      response.data.forEach((item) => {
        conversationData.value.push({
          no: item.no || Date.now(),
          question: '',
          name: item.name || '',
          think: item.think || '',
          content: item.content || '',
          comment: item.comment || '',
          resultTable: item.resultTable || '',
        })
      })
    }
  } catch (error) {
    ElMessage.error('获取回答失败: ' + (error.message || '网络错误'))
  } finally {
    conversationLoading.value = false
    scrollToBottom()
  }
}

// 处理病案首页填报
const handleMedicalRecord = async () => {
  // 实现病案首页填报逻辑
}

// 处理医保结算清单
const handleInsuranceSettlement = async () => {
  // 实现医保结算清单逻辑
}

// 处理文件上传
const handleFileChange = async (file) => {
  const validTypes = ['image/jpeg', 'image/png', 'application/pdf']
  if (!validTypes.includes(file.raw.type)) {
    ElMessage.error('请上传 JPG/PNG/PDF 格式的文件')
    return
  }

  // Check file size based on type
  if (file.raw.type === 'application/pdf') {
    if (file.size > 13 * 1024 * 1024) {
      ElMessage.error('PDF 文件大小不能超过 13MB')
      return
    }
  } else {
    if (file.size > 100 * 1024 * 1024) {
      ElMessage.error('图片文件大小不能超过 100MB')
      return
    }
  }

  // 开始上传处理流程
  startUploadProcess(file)
}

// 开始上传处理流程
const startUploadProcess = (file) => {
  showUploadModal.value = true
  currentStep.value = 1
  progressPercentage.value = 0

  // 模拟上传过程
  const timer = setInterval(() => {
    progressPercentage.value += 5

    if (progressPercentage.value >= 25 && currentStep.value === 1) {
      currentStep.value = 2
    } else if (progressPercentage.value >= 50 && currentStep.value === 2) {
      currentStep.value = 3
    } else if (progressPercentage.value >= 75 && currentStep.value === 3) {
      currentStep.value = 4
    }

    // 处理完成
    if (progressPercentage.value >= 100) {
      clearInterval(timer)
      setTimeout(() => {
        showUploadModal.value = false
        // 将处理后的文本填入输入框
        inputVal.value =
          '病案标识号：EXAMPLE_CASE 出院诊断：1.冠状动脉粥样硬化性心脏病不稳定型心绞痛2.高血压病（3级，很高危）3.2型糖尿病4.双肺微小结节5.脂肪肝6.右肾囊肿...'
        nextTick(() => {
          if (inputVal.value.trim()) {
            submitQuestion()
          }
        })
      }, 1000)
    }
  }, 200)
}

// 滚动到底部
const answerBox = ref(null)
const scrollToBottom = () => {
  nextTick(() => {
    if (answerBox.value) {
      answerBox.value.scrollTop = answerBox.value.scrollHeight
    }
  })
}

// 初始化加载对话历史
onMounted(async () => {
  try {
    conversationLoading.value = true
    const response = await fetchConversation()
    if (response.data && Array.isArray(response.data)) {
      conversationData.value = response.data
      showWelcome.value = conversationData.value.length === 0
    }
  } catch (error) {
    ElMessage.error('加载对话历史失败: ' + error.message)
  } finally {
    conversationLoading.value = false
    scrollToBottom()
  }
})
</script>

<style lang="scss" scoped>
.page-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 87vh;
  padding-bottom: 20px;
}

.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 200px);
  text-align: center;
  margin-bottom: -100px;
}

.welcome-logo {
  width: 120px;
  height: 120px;
  margin-bottom: 20px;
}

.welcome-text {
  font-size: 18px;
  color: #666;
  margin-top: 15px;
  max-width: 600px;
}

.chat-input {
  width: 100%;
  max-width: 800px;
  padding: 0 20px;
  margin-top: auto;

  .ci-content {
    border: 1px solid rgba(65, 77, 96, 0.3);
    border-radius: 15px;
    background: #ffffff;
    padding: 12px;
    box-shadow: 0px 2px 9px 0px rgba(0, 0, 0, 0.05);
  }
}

.flex-align {
  display: flex;
  align-items: center;
}

.input-text {
  border-width: 0;
  outline: none;
  margin-bottom: 12px;

  :deep(.el-textarea__inner) {
    box-shadow: none;
    resize: none;
    max-height: 120px;
  }
}

.ques-box {
  flex: 1;
  width: 100%;
  max-width: 860px;
  padding: 20px 30px 0;
  overflow-y: auto;
  margin-bottom: 20px;
}

.ques-ddd {
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-bottom: 24px;
}

.ques-item {
  position: relative;
  border-radius: 12px;
  background: #fff;
  margin-bottom: 16px;
  width: fit-content;
  padding: 16px;
  line-height: 1.6;
  font-size: 15px;
  max-width: 700px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  .avatar {
    position: absolute;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }

  &.right {
    align-self: flex-end;
    background-color: #f0f7ff;
    border-radius: 12px 2px 12px 12px;

    .avatar {
      right: -25px;
      top: -20px;
    }
  }

  &.left {
    border-radius: 2px 12px 12px 12px;

    .avatar {
      left: -25px;
      top: -20px;
    }

    .ques-text {
      color: #333;
    }
  }
}

.sk-content {
  border-left: 2px solid #eaeaea;
  padding-left: 12px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.6);
  text-align: justify;
  margin-bottom: 12px;
  white-space: pre-wrap;
}

.name-str {
  font-weight: 600;
  font-size: 16px;
  display: block;
  margin-bottom: 6px;
}

.comment-box {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #f8f8f8;
  border-radius: 6px;
  font-size: 13px;
  color: #666;

  .el-icon {
    margin-right: 6px;
    color: #2468f2;
  }
}

.final-result-table {
  margin-top: 16px;
  width: 100%;
  overflow-x: auto;

  table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

    th,
    td {
      padding: 12px 15px;
      border: 1px solid #e0e0e0;
      text-align: left;
    }

    th {
      background-color: #f5f5f5;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background-color: #fafafa;
    }

    tr:hover {
      background-color: #f0f7ff;
    }
  }
}

.loading-container {
  width: 100%;
  padding: 20px;

  :deep(.el-skeleton__item) {
    margin-bottom: 12px;
  }
}

.ml10 {
  margin-left: 10px;
}

.bottom-box {
  justify-content: space-between;
}

.btn-box {
  display: flex;
  gap: 10px;
}

@media (max-width: 768px) {
  .ques-box {
    padding: 15px;
  }

  .ques-item {
    max-width: 85%;
    padding: 12px;

    .avatar {
      width: 32px;
      height: 32px;
      top: -16px;

      &.right {
        right: -16px;
      }

      &.left {
        left: -16px;
      }
    }
  }

  .chat-input {
    padding: 0 15px;

    .ci-content {
      padding: 10px;
    }
  }

  .bottom-box {
    flex-direction: column;
    gap: 10px;

    .btn-box {
      width: 100%;
      justify-content: space-between;
    }
  }
}
</style>
