<template>
  <div 
    class="page-box"
    v-loading.fullscreen.lock="isModelProcessing"
    element-loading-text="模型正在处理中，请稍后...."
  >
    <div class="welcome-container" v-if="showWelcome">
      <img src="@/assets/logoOne.png" class="welcome-logo" alt="Logo" />
      <div class="welcome-text">
        Hi~千医·牍智AiCode智能编码助手已就位，请输入关键词/上传病历 →
        获取病案编码！(测试版)
      </div>
    </div>

    <div class="chat-scroll-wrapper">
      <!-- 使用el来替代原始滚动 -->
      <el-scrollbar ref="scrollbarRef" @scroll="handleScroll">
        <div class="ques-content">
          <template v-for="(item, index) in messageList" :key="index">
            <div class="ques-ddd">
              <!-- 用户问题 -->
              <div class="right ques-item">
                <img src="@/assets/user.jpg" class="avatar" alt="" />

                  <!-- 🟢 修改开始：包裹内容的容器，添加控制逻辑 -->
                  <div class="text-question-wrapper">
                    
                    <!-- 2. 具体内容区域，根据状态显示/隐藏 -->
                    <!-- 使用 v-show 仅仅是界面隐藏，不破坏 DOM 结构 -->
                    <div v-show="!isQuestionCollapsed(index)" style="width: 100%; display: flex; justify-content: flex-end;">
                        <!-- 检查是否为JSON格式的问题 -->
                        <div
                          v-if="isJsonQuestion(item.question)"
                          class="json-question-container"
                        >
                          <div class="json-question-header">
                            <span class="json-indicator">📋 文本解析数据</span>
                          </div>
                          <div class="json-question-display">
                            <div
                              v-for="[key, value] in Object.entries(
                                parseJsonQuestion(item.question)
                              )"
                              :key="key"
                              class="json-question-item"
                            >
                              <span class="json-key">{{ key }}:</span>
                              <span class="json-value">{{ value }}</span>
                            </div>
                          </div>
                        </div>
                        <!-- 普通文本问题 -->
                        <span v-else class="ques-text">{{ item.question }}</span>
                    </div>

                    <!-- 3. (可选) 折叠后的占位提示 -->
                    <div v-show="isQuestionCollapsed(index)" class="collapsed-placeholder" style="color: #ccc; font-style: italic;">
                      [用户输入已折叠]
                    </div>

                    <!-- 1. 折叠/展开 控制栏 -->
                    <div 
                      class="collapse-toggle-btn" 
                      @click="toggleQuestionCollapse(index)"
                    >
                      <span>{{ isQuestionCollapsed(index) ? '展开问题' : '收起问题' }}</span>
                      <el-icon :style="{ transform: isQuestionCollapsed(index) ? 'rotate(-90deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }">
                        <ArrowDown />
                      </el-icon>
                    </div>

                  </div>      
              </div>

              <!-- AI回答 -->
              <div class="ai-responses-row" style="display: flex; gap: 32px">
                <!-- 诊断区域 -->
                <div
                  class="ai-diagnosis"
                  style="flex: 1; border-right: 1px solid #eee"
                >
                  <div
                    style="
                      font-weight: bold;
                      color: #3087cf;
                      cursor: pointer;
                      display: flex;
                      align-items: center;
                      gap: 8px;
                    "
                    @click="toggleSection('diagnosis', index)"
                  >
                    诊断
                    <el-icon
                      :style="{
                        transform: getSectionState('diagnosis', index)
                          ? 'rotate(180deg)'
                          : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }"
                    >
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <!-- 文本内容 - 可以收起，使用对话框样式 -->
                  <div
                    class="text-content"
                    :class="{ collapsed: !getSectionState('diagnosis', index) }"
                  >
                    <!-- 直接过滤出有内容的项 -->
                    <div
                      v-for="(answer, aIndex) in filterTextAnswers(
                        item.answers.diagnosis.answerList
                      )"
                      :key="'diag-text-' + aIndex"
                      class="left ques-item"
                    >
                      <div class="text-answer-item">
                        <img
                          src="@/assets/touxiang/t1.jpg"
                          v-if="aIndex == 0"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t2.jpg"
                          v-else-if="aIndex == 1"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t3.jpg"
                          v-else-if="aIndex == 2"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t4.jpg"
                          v-else-if="aIndex == 3"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t5.jpg"
                          v-else-if="aIndex == 4"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t6.jpg"
                          v-else-if="aIndex == 5"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t7.jpg"
                          v-else-if="aIndex == 6"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t8.jpg"
                          v-else-if="aIndex == 7"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t9.jpg"
                          v-else-if="aIndex == 8"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t10.jpg"
                          v-else-if="aIndex == 9"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/logoOne.png"
                          v-else-if="aIndex == 10"
                          class="avatar"
                          alt=""
                        />

                        <div class="sk-content" v-if="answer.think">
                          {{ answer.think }}
                        </div>

                        <div class="thinking-content" v-if="answer.reasoning">
                          <div class="thinking-header">思考过程</div>
                          <div class="thinking-text">
                            {{ answer.reasoning }}
                          </div>
                        </div>

                        <span class="ques-text" v-if="answer.content">
                          <span class="name-str">{{ answer.name }}:</span>
                          {{ answer.content }}
                        </span>
                      </div>
                    </div>
                    <div
                      v-if="
                        filterTextAnswers(item.answers.diagnosis.answerList)
                          .length === 0
                      "
                      class="no-content-hint"
                    >
                      暂无文本内容
                    </div>
                  </div>
                  <!-- 表格内容 - 始终显示 -->
                  <div class="table-content">
                    <!-- 表格内容保持不变 -->
                    <div
                      v-for="(answer, aIndex) in item.answers.diagnosis
                        .answerList"
                      :key="'diag-table-' + aIndex"
                    >
                      <!-- JSON表格 -->
                      <div
                        v-if="answer.isJsonResponse && answer.jsonData"
                        class="json-response-container"
                      >
                        <div class="json-response-header">
                          <span class="name-str">{{ answer.name }}:</span>
                          <span class="json-indicator">📊 结构化数据</span>
                        </div>

                        <div class="json-table-display">
                          <el-table
                            :data="Object.entries(answer.jsonData)"
                            stripe
                            border
                            style="width: 100%; margin-top: 10px"
                          >
                            <el-table-column
                              prop="0"
                              label="字段名"
                              width="200"
                              align="center"
                            >
                              <template #default="{ row }">
                                <strong>{{ row[0] }}</strong>
                              </template>
                            </el-table-column>
                            <el-table-column prop="1" label="内容" align="left">
                              <template #default="{ row }">
                                <div class="json-field-content">
                                  {{ row[1] }}
                                </div>
                              </template>
                            </el-table-column>
                          </el-table>
                        </div>

                        <el-collapse
                          class="json-raw-display"
                          style="margin-top: 15px"
                        >
                          <el-collapse-item
                            title="查看原始JSON数据"
                            name="raw-json"
                          >
                            <pre class="json-raw-content">{{
                              JSON.stringify(answer.jsonData, null, 2)
                            }}</pre>
                          </el-collapse-item>
                        </el-collapse>
                      </div>

                      <!-- Markdown表格 -->
                      <div
                        v-else-if="answer.isMarkdownTable && answer.tableData"
                        class="markdown-table-container"
                      >
                        <div class="markdown-table-header">
                          <span class="name-str">{{ answer.name }}:</span>
                          <!-- 表格展示 -->
                          <span class="markdown-indicator"
                            >📋 Markdown表格</span
                          >
                        </div>
                        <!-- TODO 整体反馈按钮 -->
                        <el-button 
                          type="primary" 
                          link 
                          size="small" 
                          @click="openFeedback('comment', item.message_id, -1, 0)"
                        >
                          <el-icon class="mr-1"><ChatLineSquare /></el-icon>
                          整体反馈
                        </el-button>
                          <!-- 
                            注意参数说明：
                            type: 'comment' (或者复用 'like'/'dislike'，或者传入空让用户在弹窗里选)
                            message_id: 当前消息ID
                            row_id: -1 (约定 -1 代表整体)
                            category: 0 代表诊断, 1 代表手术 (这里假设外部传入或根据上下文判断，下文会详细说明)
                          -->

                        <div class="markdown-table-display">
                          <el-table
                            :data="answer.tableData.slice(1)"
                            stripe
                            border
                            style="width: 100%; margin-top: 10px"
                          >
                            <el-table-column
                              v-for="(header, index) in answer.tableData[0]"
                              :key="index"
                              :prop="index.toString()"
                              :label="header"
                              align="center"
                              :width="undefined"
                              show-overflow-tooltip
                            >
                              <template #default="{ row }">
                                <div
                                  class="markdown-cell-content"
                                  v-html="formatCellContent(row[index])"
                                ></div>
                              </template>
                            </el-table-column>
                            <el-table-column
                              label="反馈"
                              width="70"
                              align="center"
                            >
                              <template #default="{ row, $index }">
                                <div class="feedback-buttons">
                                  <img
                                    :src="getFeedbackIcon('like', item.message_id, $index, 0)"
                                    style="width: 15px; height: 15px"
                                    @click="
                                      openFeedback(
                                        'like',
                                        item.message_id,
                                        $index,
                                        0
                                      )
                                    "
                                    alt=""
                                  />
                                  <img
                                    :src="getFeedbackIcon('dislike', item.message_id, $index, 0)"
                                    style="
                                      width: 15px;
                                      height: 15px;
                                      margin-left: 10px;
                                    "
                                    @click="
                                      openFeedback(
                                        'dislike',
                                        item.message_id,
                                        $index,
                                        0
                                      )
                                    "
                                    alt=""
                                  />
                                </div>
                              </template>
                            </el-table-column>
                          </el-table>
                        </div>

                        <el-collapse
                          class="markdown-raw-display"
                          style="margin-top: 15px"
                        >
                          <el-collapse-item
                            title="查看原始Markdown表格"
                            name="raw-markdown"
                          >
                            <pre class="markdown-raw-content">{{
                              answer.content
                            }}</pre>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 手术区域 -->
                <div
                  class="ai-surgery"
                  style="flex: 1; border-right: 1px solid #eee"
                >
                  <div
                    style="
                      font-weight: bold;
                      color: #3087cf;
                      cursor: pointer;
                      display: flex;
                      align-items: center;
                      gap: 8px;
                    "
                    @click="toggleSection('surgery', index)"
                  >
                    手术
                    <el-icon
                      :style="{
                        transform: getSectionState('surgery', index)
                          ? 'rotate(180deg)'
                          : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }"
                    >
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <div
                    class="text-content"
                    :class="{ collapsed: !getSectionState('surgery', index) }"
                  >
                    <!-- 直接过滤出有内容的项 -->
                    <div
                      v-for="(answer, aIndex) in filterTextAnswers(
                        item.answers.surgery.answerList
                      )"
                      :key="'surg-text-' + aIndex"
                      class="left ques-item"
                    >
                      <div class="text-answer-item">
                        <img
                          src="@/assets/touxiang/t1.jpg"
                          v-if="aIndex == 0"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t2.jpg"
                          v-else-if="aIndex == 1"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t3.jpg"
                          v-else-if="aIndex == 2"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t4.jpg"
                          v-else-if="aIndex == 3"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t5.jpg"
                          v-else-if="aIndex == 4"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t6.jpg"
                          v-else-if="aIndex == 5"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t7.jpg"
                          v-else-if="aIndex == 6"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t8.jpg"
                          v-else-if="aIndex == 7"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t9.jpg"
                          v-else-if="aIndex == 8"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/touxiang/t10.jpg"
                          v-else-if="aIndex == 9"
                          class="avatar"
                          alt=""
                        />
                        <img
                          src="@/assets/logoOne.png"
                          v-else-if="aIndex == 10"
                          class="avatar"
                          alt=""
                        />

                        <div class="sk-content" v-if="answer.think">
                          {{ answer.think }}
                        </div>

                        <div class="thinking-content" v-if="answer.reasoning">
                          <div class="thinking-header">思考过程</div>
                          <div class="thinking-text">
                            {{ answer.reasoning }}
                          </div>
                        </div>

                        <span class="ques-text" v-if="answer.content">
                          <span class="name-str">{{ answer.name }}:</span>
                          {{ answer.content }}
                        </span>
                      </div>
                    </div>
                    <div
                      v-if="
                        filterTextAnswers(item.answers.surgery.answerList)
                          .length === 0
                      "
                      class="no-content-hint"
                    >
                      暂无文本内容
                    </div>
                  </div>
                  <div class="table-content">
                    <!-- 表格内容保持不变 -->
                    <div
                      v-for="(answer, aIndex) in item.answers.surgery
                        .answerList"
                      :key="'surg-table-' + aIndex"
                    >
                      <!-- JSON表格 -->
                      <div
                        v-if="answer.isJsonResponse && answer.jsonData"
                        class="json-response-container"
                      >
                        <div class="json-response-header">
                          <span class="name-str">{{ answer.name }}:</span>
                          <span class="json-indicator">📊 结构化数据</span>
                        </div>

                        <div class="json-table-display">
                          <el-table
                            :data="Object.entries(answer.jsonData)"
                            stripe
                            border
                            style="width: 100%; margin-top: 10px"
                          >
                            <el-table-column
                              prop="0"
                              label="字段名"
                              width="200"
                              align="center"
                            >
                              <template #default="{ row }">
                                <strong>{{ row[0] }}</strong>
                              </template>
                            </el-table-column>
                            <el-table-column prop="1" label="内容" align="left">
                              <template #default="{ row }">
                                <div class="json-field-content">
                                  {{ row[1] }}
                                </div>
                              </template>
                            </el-table-column>
                          </el-table>
                        </div>

                        <el-collapse
                          class="json-raw-display"
                          style="margin-top: 15px"
                        >
                          <el-collapse-item
                            title="查看原始JSON数据"
                            name="raw-json"
                          >
                            <pre class="json-raw-content">{{
                              JSON.stringify(answer.jsonData, null, 2)
                            }}</pre>
                          </el-collapse-item>
                        </el-collapse>
                      </div>

                      <!-- Markdown表格 -->
                      <div
                        v-else-if="answer.isMarkdownTable && answer.tableData"
                        class="markdown-table-container"
                      >
                        <div class="markdown-table-header">
                          <span class="name-str">{{ answer.name }}:</span>
                          <span class="markdown-indicator"
                            >📋 Markdown表格</span
                          >
                        </div>

                        <el-button 
                          type="primary" 
                          link 
                          size="small" 
                          @click="openFeedback('comment', item.message_id, -1, 1)"
                        >
                          <el-icon class="mr-1"><ChatLineSquare /></el-icon>
                          整体反馈
                        </el-button>

                        <div class="markdown-table-display">
                          <el-table
                            :data="answer.tableData.slice(1)"
                            stripe
                            border
                            style="width: 100%; margin-top: 10px"
                          >
                            <el-table-column
                              v-for="(header, index) in answer.tableData[0]"
                              :key="index"
                              :prop="index.toString()"
                              :label="header"
                              align="center"
                              :width="undefined"
                              show-overflow-tooltip
                            >
                              <template #default="{ row }">
                                <div
                                  class="markdown-cell-content"
                                  v-html="formatCellContent(row[index])"
                                ></div>
                              </template>
                            </el-table-column>
                            <el-table-column
                              label="反馈"
                              width="70"
                              align="center"
                            >
                              <template #default="{ row, $index }">
                                <div class="feedback-buttons">
                                  <img
                                    :src="getFeedbackIcon('like', item.message_id, $index, 1)"
                                    style="width: 15px; height: 15px"
                                    @click="
                                      openFeedback(
                                        'like',
                                        item.message_id,
                                        $index,
                                        1
                                      )
                                    "
                                    alt=""
                                  />
                                  <img
                                    :src="getFeedbackIcon('dislike', item.message_id, $index, 1)"
                                    style="
                                      width: 15px;
                                      height: 15px;
                                      margin-left: 10px;
                                    "
                                    @click="
                                      openFeedback(
                                        'dislike',
                                        item.message_id,
                                        $index,
                                        1
                                      )
                                    "
                                    alt=""
                                  />
                                </div>
                              </template>
                            </el-table-column>
                          </el-table>
                        </div>

                        <el-collapse
                          class="markdown-raw-display"
                          style="margin-top: 15px"
                        >
                          <el-collapse-item
                            title="查看原始Markdown表格"
                            name="raw-markdown"
                          >
                            <pre class="markdown-raw-content">{{
                              answer.content
                            }}</pre>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
          </template>
        </div>
      </el-scrollbar>
    </div>

    <!-- 反馈对话框 -->
    <FeedbackDialog
      v-model="showFeedbackDialog"
      :feedback-data="currentFeedback"
      :existing-status="currentFeedbackStatus"
      @feedback-success="handleFeedbackSuccess"
      @feedback-deleted="handleFeedbackDeleted"
    />

    <!-- 功能按钮 -->
    <div class="chat-input">
      <div class="ci-content">
        <el-input
          class="input-text"
          v-model.trim="inputVal"
          @keyup.enter="submit"
          :autosize="{ minRows: 1, maxRows: 4 }"
          type="textarea"
          placeholder="我是千医.牍智大模型,快来让我帮你病案编码吧~"
          disabled
        />
        <div class="bottom-box flex-align">
          <!-- 思考 + 导出表格 -->
          <div class="btn-box">
            <div
              class="btn btn3"
              :class="{
                active: isThinking,
              }"
              @click="isThinking = !isThinking"
            >
              <el-icon>
                <View />
              </el-icon>
              思考
            </div>
            <div class="btn btn3" @click="exportCodingExcel">
              <el-icon>
                <Download />
              </el-icon>
              导出表格
            </div>
            <div class="btn btn3" @click="exportFeedback">
              <el-icon>
                <Download />
              </el-icon>
              导出全部反馈
            </div>
          </div>
          <!-- 提交 + 上传文件 + 批量上传 + Excel -->
          <div class="flex-align">
            <!-- <el-tooltip content="提交内容" placement="top" effect="dark">
              <div class="fs-box" @click="() => submit()">
                <el-icon>
                  <Position />
                </el-icon>
              </div>
            </el-tooltip> -->
            <!-- 文件上传组件 -->
            <el-upload
              class="ml10"
              action=""
              v-if="showButtons.singleUpload"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              accept=".jpg,.jpeg,.png,.pdf"
              :multiple="true"
            >
              <!-- 在这里添加 el-tooltip 包裹按钮 div -->
              <el-tooltip
                content="上传单个PDF文件"
                placement="top"
                effect="dark"
              >
                <div
                  class="fs-box"
                  style="background-color: #f56c6c"
                  :style="{ width: currentPageType === 'main' ? '' : '100px' }"
                >
                  <el-icon v-if="currentPageType === 'main'"
                    ><Upload
                  /></el-icon>
                  <span
                    v-else
                    style="font-size: 14px; line-height: 28px; display: block"
                  >
                    {{ currentPageType === 'pdf' ? '上传PDF' : '单PDF上传' }}
                  </span>
                </div>
              </el-tooltip>
            </el-upload>

            <!-- 批量上传按钮 -->
            <el-upload
              ref="batchUploadRef"
              v-if="showButtons.batchUpload"
              class="ml10"
              action=""
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleBatchFileChange"
              accept=".pdf"
              :multiple="true"
            >
              <el-tooltip
                content="批量上传PDF文件"
                placement="top"
                effect="dark"
              >
                <div
                  class="fs-box"
                  style="background-color: #67c23a"
                  :style="{ width: currentPageType === 'main' ? '' : '100px' }"
                  @click="resetBatchUploader"
                >
                  <el-icon v-if="currentPageType === 'main'"><Files /></el-icon>
                  <span
                    v-else
                    style="font-size: 14px; line-height: 28px; display: block"
                  >
                    多PDF上传
                  </span>
                </div>
              </el-tooltip>
            </el-upload>

            <!-- <el-button class="ml10" type="danger" round>文件上传</el-button> -->
            <!-- Excel 批量上传按钮 -->
            <el-upload
              class="ml10"
              v-if="showButtons.excelUpload"
              action=""
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleExcelChange"
              accept=".xlsx,.xls,.csv"
              :multiple="false"
            >
              <el-tooltip
                content="上传Excel并批量提交"
                placement="top"
                effect="dark"
              >
                <div
                  class="fs-box"
                  style="background-color: #10b981"
                  :style="{ width: currentPageType === 'main' ? '' : '80px' }"
                >
                  <el-icon v-if="currentPageType === 'main'"
                    ><Upload
                  /></el-icon>
                  <span
                    v-else
                    style="font-size: 14px; line-height: 28px; display: block"
                  >
                    Excel上传
                  </span>
                </div>
              </el-tooltip>
            </el-upload>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传文件脱敏处理提示 -->
    <!-- 文件处理弹窗 -->
    <el-dialog
      v-model="showUploadModal"
      title="文件处理中"
      width="30%"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="upload-process">
        <!-- 处理步骤指示器 -->
        <div class="process-steps">
          <!-- 第一步：文件上传 -->
          <div class="step" :class="{ active: currentStep >= 1 }">
            <div class="step-icon">1</div>
            <div class="step-text">文件上传</div>
          </div>
          <!-- 第二步：文本识别 -->
          <div class="step" :class="{ active: currentStep >= 2 }">
            <div class="step-icon">2</div>
            <div class="step-text">文本识别</div>
          </div>
          <!-- 第三步：信息脱敏 -->
          <div class="step" :class="{ active: currentStep >= 3 }">
            <div class="step-icon">3</div>
            <div class="step-text">信息脱敏</div>
          </div>
          <!-- 第四步：标准化处理 -->
          <div class="step" :class="{ active: currentStep >= 4 }">
            <div class="step-icon">4</div>
            <div class="step-text">标准化处理</div>
          </div>
        </div>

        <!-- 图片预览区域（过渡效果） -->
        <div class="image-preview">
          <transition-group name="fade">
            <!-- 第一步显示的图片 -->
            <img
              v-if="currentStep === 1"
              key="1"
              src="../assets/wenjianshangchuan.png"
              style="width: 150px; height: 150px"
              alt="上传中"
            />
            <!-- 第二步显示的图片 -->
            <img
              v-if="currentStep === 2"
              key="2"
              src="../assets/ocr.png"
              style="width: 150px; height: 150px"
              alt="识别中"
            />
            <!-- 第三步显示的图片 -->
            <img
              v-if="currentStep === 3"
              key="3"
              src="../assets/tuomin.png"
              style="width: 150px; height: 150px"
              alt="脱敏中"
            />
            <!-- 第四步显示的图片 -->
            <img
              v-if="currentStep === 4"
              key="4"
              src="../assets/biaozhunhua.png"
              style="width: 150px; height: 150px"
              alt="处理中"
            />
          </transition-group>
        </div>

        <!-- 当前步骤的文本描述 -->
        <div class="process-text">
          {{ processTexts[currentStep - 1] || '正在处理中...' }}
        </div>

        <!-- 进度条 -->
        <el-progress
          :percentage="progressPercentage"
          :status="progressStatus"
          :stroke-width="12"
        />

        <!-- 取消按钮 -->
        <div class="upload-actions" v-if="progressStatus !== 'success'">
          <el-button @click="cancelUpload" type="danger" plain>
            <el-icon><Close /></el-icon>
            取消处理
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑内容弹窗 -->
    <el-dialog
      v-model="showEditModal"
      title="编辑提取内容"
      width="60%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      center
    >
      <div class="edit-content-container">
        <div class="edit-description">
          <el-icon><Edit /></el-icon>
          <span>请确认或编辑从文件中提取的内容：</span>
        </div>
        <el-input
          v-model="editContent"
          type="textarea"
          :rows="8"
          placeholder="请输入或编辑内容..."
          class="edit-textarea"
          show-word-limit
          :maxlength="10000"
          @keydown="handleKeydown"
        />
        <div class="edit-tips">
          <el-icon><InfoFilled /></el-icon>
          <span
            >您可以对提取的内容进行编辑，确认后将自动提交至AI进行病案编码。</span
          >
          <div class="keyboard-shortcuts">
            <span>快捷键：Ctrl+Enter 提交 | Esc 取消</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="edit-footer">
          <el-button @click="cancelEdit" size="large">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          <el-button
            type="primary"
            @click="confirmEdit"
            size="large"
            :disabled="!editContent"
          >
            <el-icon><Check /></el-icon>
            确认并提交
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- JSON数据编辑弹窗 -->
    <el-dialog
      v-model="showJsonEditModal"
      title="编辑OCR识别的结构化数据"
      width="80%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      center
    >
      <div class="json-edit-container">
        <div class="json-edit-description">
          <el-icon><Edit /></el-icon>
          <span>OCR识别返回的结构化数据，请确认或编辑后提交：</span>
        </div>

        <!-- 可编辑的JSON表格 -->
        <div class="json-edit-table">
          <el-table
            :data="Object.entries(editJsonData)"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="0" label="字段名" width="200" align="center">
              <template #default="{ row, $index }">
                <el-input
                  v-model="row[0]"
                  placeholder="字段名"
                  @input="updateJsonKey($index, row[0], row[1])"
                />
              </template>
            </el-table-column>
            <el-table-column prop="1" label="内容" align="left">
              <template #default="{ row }">
                <el-input
                  v-model="row[1]"
                  type="textarea"
                  :rows="2"
                  placeholder="内容"
                  @input="updateJsonValue(row[0], row[1])"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeJsonField($index)"
                  :icon="Delete"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 添加新字段 -->
          <div class="add-field-section" style="margin-top: 15px">
            <el-button type="primary" @click="addJsonField" size="small">
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
          </div>
        </div>

        <div class="json-edit-tips">
          <el-icon><InfoFilled /></el-icon>
          <span
            >您可以编辑、添加或删除字段，确认后将以JSON格式提交至AI进行分析。</span
          >
        </div>
      </div>

      <template #footer>
        <div class="json-edit-footer">
          <el-button @click="cancelJsonEdit" size="large">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          <el-button
            type="primary"
            @click="confirmJsonEdit"
            size="large"
            :disabled="Object.keys(editJsonData).length === 0"
          >
            <el-icon><Check /></el-icon>
            确认并提交
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量文件JSON数据编辑弹窗 -->
    <el-dialog
      v-model="showBatchFileJsonEditModal"
      :title="`编辑文件: ${
        currentEditingFileIndex >= 0
          ? batchFiles[currentEditingFileIndex]?.name
          : ''
      }`"
      width="80%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      center
    >
      <div class="json-edit-container">
        <div class="json-edit-description">
          <el-icon><Edit /></el-icon>
          <span>编辑当前文件的结构化数据：</span>
        </div>

        <!-- 可编辑的JSON表格 -->
        <div class="json-edit-table">
          <el-table
            :data="Object.entries(batchFileJsonData)"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="0" label="字段名" width="200" align="center">
              <template #default="{ row, $index }">
                <el-input
                  v-model="row[0]"
                  placeholder="字段名"
                  @input="updateBatchFileJsonKey($index, row[0], row[1])"
                />
              </template>
            </el-table-column>
            <el-table-column prop="1" label="内容" align="left">
              <template #default="{ row }">
                <el-input
                  v-model="row[1]"
                  type="textarea"
                  :rows="2"
                  placeholder="内容"
                  @input="updateBatchFileJsonValue(row[0], row[1])"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeBatchFileJsonField($index)"
                  :icon="Delete"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 添加新字段 -->
          <div class="add-field-section" style="margin-top: 15px">
            <el-button
              type="primary"
              @click="addBatchFileJsonField"
              size="small"
            >
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
          </div>
        </div>

        <div class="json-edit-tips">
          <el-icon><InfoFilled /></el-icon>
          <span>编辑完成后，数据将同步回文件内容框中。</span>
        </div>
      </div>

      <template #footer>
        <div class="json-edit-footer">
          <el-button @click="cancelBatchFileJsonEdit" size="large">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          <el-button
            type="primary"
            @click="confirmBatchFileJsonEdit"
            size="large"
            :disabled="Object.keys(batchFileJsonData).length === 0"
          >
            <el-icon><Check /></el-icon>
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量编辑弹窗 -->
    <el-dialog
      v-model="showBatchEditModal"
      title="批量编辑文件内容"
      width="80%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      center
    >
      <div class="batch-edit-container">
        <div class="batch-edit-header">
          <el-icon><Files /></el-icon>
          <span
            >共选择了
            {{ batchFiles.length }} 个文件，请确认或编辑提取的内容：</span
          >
        </div>

        <div class="batch-files-list">
          <div
            v-for="(fileItem, index) in batchFiles"
            :key="index"
            class="batch-file-item"
            :class="{
              processing: fileItem.processing,
              completed: fileItem.completed,
              error: fileItem.error,
            }"
          >
            <div class="file-header">
              <div class="file-info">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ fileItem.name }}</span>
                <el-tag v-if="fileItem.processing" type="info" size="small">
                  <el-icon><Loading /></el-icon>
                  处理中...
                </el-tag>
                <el-tag
                  v-else-if="fileItem.completed"
                  type="success"
                  size="small"
                >
                  <el-icon><Check /></el-icon>
                  已完成
                </el-tag>
                <el-tag v-else-if="fileItem.error" type="danger" size="small">
                  <el-icon><Close /></el-icon>
                  处理失败
                </el-tag>
                <el-tag v-else type="warning" size="small">
                  <el-icon><Clock /></el-icon>
                  等待处理
                </el-tag>
              </div>
              <div class="file-actions">
                <el-button
                  v-if="
                    !fileItem.processing &&
                    fileItem.completed &&
                    isJsonContent(fileItem.content)
                  "
                  @click="editFileJson(index)"
                  type="primary"
                  size="small"
                  text
                >
                  <el-icon><Edit /></el-icon>
                  编辑表格
                </el-button>
                <el-button
                  v-if="!fileItem.processing"
                  @click="removeFile(index)"
                  type="danger"
                  size="small"
                  text
                >
                  <el-icon><Delete /></el-icon>
                  移除
                </el-button>
              </div>
            </div>

            <div class="file-content">
              <el-input
                v-model="fileItem.content"
                type="textarea"
                :rows="4"
                :placeholder="
                  fileItem.processing
                    ? '正在处理文件...'
                    : '文件内容将在处理后显示'
                "
                :disabled="fileItem.processing"
                show-word-limit
                :maxlength="50000"
              />
              <div v-if="fileItem.error" class="error-message">
                <el-icon><Warning /></el-icon>
                <span>{{ fileItem.errorMessage }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="batch-progress" v-if="batchProcessing">
          <div class="progress-info">
            <span
              >正在处理文件 {{ currentProcessingIndex + 1 }} /
              {{ batchFiles.length }}</span
            >
            <span class="progress-text">{{ batchProgressText }}</span>
          </div>
          <el-progress
            :percentage="batchProgressPercentage"
            :status="batchProgressStatus"
            :stroke-width="8"
          />
        </div>

        <div class="batch-tips">
          <el-icon><InfoFilled /></el-icon>
          <span
            >系统将按顺序处理每个文件，您可以在处理过程中编辑已完成的文件内容。</span
          >
        </div>
      </div>

      <template #footer>
        <div class="batch-footer">
          <el-button
            @click="cancelBatchEdit"
            size="large"
            :disabled="batchProcessing"
          >
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          <el-button
            v-if="!batchProcessing"
            type="warning"
            @click="startBatchProcessing"
            size="large"
          >
            <el-icon><VideoPlay /></el-icon>
            开始处理
          </el-button>
          <el-button
            type="info"
            @click="continueUpload"
            size="large"
            :disabled="batchProcessing"
          >
            <el-icon><Upload /></el-icon>
            继续上传
          </el-button>
          <el-button
            v-if="batchProcessing"
            type="danger"
            @click="stopBatchProcessing"
            size="large"
          >
            <el-icon><VideoPause /></el-icon>
            停止处理
          </el-button>
          <el-button
            v-if="allFilesProcessed"
            type="primary"
            @click="createTaskQueue"
            size="large"
            :disabled="!hasValidContent"
          >
            <el-icon><List /></el-icon>
            创建任务队列 ({{ validFileCount }} 个文件)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 任务队列浮窗 -->
    <el-dialog
      v-model="showTaskModal"
      :title="taskMinimized ? '' : '批量处理任务队列'"
      :width="taskMinimized ? '300px' : '70%'"
      :top="taskMinimized ? 'auto' : '10vh'"
      :class="{
        'task-minimized': taskMinimized,
        'task-floating': taskMinimized,
      }"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="!taskMinimized"
      :modal="!taskMinimized"
      :append-to-body="true"
      draggable
    >
      <!-- 最小化状态 -->
      <div v-if="taskMinimized" class="task-minimized-content">
        <div class="task-mini-header">
          <div class="task-mini-info">
            <el-icon v-if="taskProcessing" class="spinning"
              ><Loading
            /></el-icon>
            <el-icon v-else><List /></el-icon>
            <span>任务队列 {{ completedTasks }}/{{ totalTasks }}</span>
          </div>
          <div class="task-mini-actions">
            <el-button
              @click="taskMinimized = false"
              type="primary"
              text
              size="small"
            >
              <el-icon><ArrowUp /></el-icon>
            </el-button>
            <el-button @click="stopAllTasks" type="danger" text size="small">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        <el-progress
          :percentage="taskProgress"
          :stroke-width="4"
          :show-text="false"
        />
      </div>

      <!-- 完整状态 -->
      <div v-else class="task-full-content">
        <div class="task-header">
          <div class="task-info">
            <el-icon><List /></el-icon>
            <span
              >共 {{ totalTasks }} 个任务，已完成 {{ completedTasks }} 个，失败
              {{ failedTasks }} 个</span
            >
          </div>
          <div class="task-actions">
            <el-button
              @click="taskMinimized = true"
              type="info"
              text
              size="small"
            >
              <el-icon><Minus /></el-icon>
              最小化
            </el-button>
            <el-button
              @click="pauseAllTasks"
              type="warning"
              text
              size="small"
              v-if="taskProcessing"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button
              @click="resumeAllTasks"
              type="success"
              text
              size="small"
              v-else-if="currentTaskIndex < totalTasks"
            >
              <el-icon><VideoPlay /></el-icon>
              继续
            </el-button>
            <el-button @click="stopAllTasks" type="danger" text size="small">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button
              @click="exportExcel_no_diag_surg"
              type="success"
              text
              size="small"
            >
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
        </div>

        <div class="task-progress-info">
          <div class="progress-text">
            <span v-if="taskProcessing"
              >正在处理第 {{ currentTaskIndex + 1 }} 个任务...</span
            >
            <span v-else-if="completedTasks === totalTasks && totalTasks > 0"
              >所有任务已完成</span
            >
            <span v-else>任务队列暂停中</span>
          </div>
          <el-progress :percentage="taskProgress" :stroke-width="8" />
        </div>

        <div class="task-list">
          <div
            v-for="(task, index) in taskQueue"
            :key="index"
            class="task-item"
            :class="{
              current: index === currentTaskIndex && taskProcessing,
              completed: task.completed,
              failed: task.failed,
              waiting:
                !task.completed && !task.failed && index > currentTaskIndex,
            }"
          >
            <div class="task-item-header">
              <div class="task-item-info">
                <el-icon><Document /></el-icon>
                <span class="task-name">{{ task.fileName }}</span>
                <el-tag
                  v-if="index === currentTaskIndex && taskProcessing"
                  type="info"
                  size="small"
                >
                  <el-icon><Loading /></el-icon>
                  处理中
                </el-tag>
                <el-tag v-else-if="task.completed" type="success" size="small">
                  <el-icon><Check /></el-icon>
                  已完成
                </el-tag>
                <el-tag v-else-if="task.failed" type="danger" size="small">
                  <el-icon><Close /></el-icon>
                  失败
                </el-tag>
                <el-tag v-else type="warning" size="small">
                  <el-icon><Clock /></el-icon>
                  等待中
                </el-tag>
              </div>
              <div class="task-item-actions">
                <el-button
                  v-if="!taskProcessing && !task.completed && !task.failed"
                  @click="removeTask(index)"
                  type="danger"
                  text
                  size="small"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <div class="task-item-content">
              <div class="task-content-preview">
                {{ task.content.substring(0, 100)
                }}{{ task.content.length > 100 ? '...' : '' }}
              </div>
              <div v-if="task.failed" class="task-error">
                <el-icon><Warning /></el-icon>
                <span>{{ task.errorMessage }}</span>
              </div>
              <div v-if="task.completed && task.result" class="task-result">
                <el-icon><Check /></el-icon>
                <span>AI处理完成，已添加到对话历史</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer v-if="!taskMinimized">
        <div class="task-footer">
          <el-button @click="showTaskModal = false" size="large">
            <el-icon><Close /></el-icon>
            关闭
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 悬浮按钮 -->
    <div
      v-if="taskQueue.length > 0 && !showTaskModal"
      class="floating-task-button"
      @click="showTaskModal = true"
    >
      <el-badge :value="taskQueue.length" :max="99" class="task-badge">
        <el-button type="primary" size="large" circle>
          <el-icon><List /></el-icon>
        </el-button>
      </el-badge>
    </div>
    <!-- 悬浮导出按钮 -->
    <!-- <div class="floating-task-button" style="right: 180px;" @click="openExportModal">
      <el-badge :value="0" class="task-badge">
        <el-button type="success" size="large" circle>
          <el-icon><Download /></el-icon>
        </el-button>
      </el-badge>
    </div> -->

    <!-- 导出筛选与预览弹窗 -->
    <el-dialog
      v-model="showExportModal"
      title="导出筛选与预览"
      width="90%"
      top="8vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="export-panel">
        <!-- 筛选区 -->
        <el-form :inline="true" label-width="110px" class="export-filter">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="exportFilters.dateRange"
              type="datetimerange"
              start-placeholder="开始"
              end-placeholder="结束"
              :default-time="[
                new Date(2000, 0, 1, 0, 0, 0),
                new Date(2000, 0, 1, 23, 59, 59),
              ]"
              format="YYYY年MM月DD日 HH:mm:ss"
              unlink-panels
            />
          </el-form-item>

          <el-form-item label="诊断/手术筛选">
            <el-input
              v-model.trim="exportFilters.diagSurgKeyword"
              placeholder="输入编码或名称关键字"
              style="width: 240px"
              clearable
            />
            <el-select
              v-model="exportFilters.diagSurgType"
              style="width: 140px; margin-left: 8px"
            >
              <el-option label="全部" value="all" />
              <el-option label="仅诊断" value="diag" />
              <el-option label="仅手术" value="surg" />
            </el-select>
          </el-form-item>

          <el-form-item label="用户">
            <el-input
              v-model.trim="exportFilters.user"
              placeholder="创建者（模糊匹配）"
              style="width: 200px"
              clearable
            />
          </el-form-item>

          <el-form-item label="住院号">
            <el-input
              v-model.trim="exportFilters.inpatientNo"
              placeholder="单个住院号（精确匹配）"
              style="width: 220px"
              clearable
            />
          </el-form-item>

          <el-form-item label="导出字段">
            <div class="field-chooser">
              <div class="field-ops">
                <el-button size="small" @click="selectAllFields(true)"
                  >全选</el-button
                >
                <el-button size="small" @click="selectAllFields(false)"
                  >全不选</el-button
                >
                <el-button size="small" @click="resetFieldsToDefault"
                  >重置默认</el-button
                >
              </div>
              <el-checkbox-group
                v-model="selectedExportFields"
                class="fields-grid"
              >
                <el-checkbox
                  v-for="f in exportFieldOptions"
                  :key="f"
                  :label="f"
                  >{{ f }}</el-checkbox
                >
              </el-checkbox-group>
              <div class="hint">
                提示：诊断/手术的“名称N/编码N”为可变长列，预览时会自动扩展到最大项数。
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="buildPreview">预览</el-button>
            <el-button
              @click="clearPreview"
              :disabled="previewRows.length === 0"
              >清空预览</el-button
            >
          </el-form-item>
          
          <el-divider content-position="left">高级选项</el-divider>
          <el-form-item label="">
            <div class="advanced-options" style="display:flex; align-items:center; gap:16px;">
              <el-checkbox v-model="exportFilters.exportAllConversations">全部对话历史记录</el-checkbox>
              <el-checkbox v-model="exportFilters.exportAllUsers">全部普通用户</el-checkbox>
            </div>
          </el-form-item>
        </el-form>

        <!-- 预览区 -->
        <div class="preview-wrap" v-if="previewRows.length">
          <el-alert
            type="info"
            show-icon
            :closable="false"
            style="margin-bottom: 10px"
            :title="`预览 ${previewRows.length} 条记录；导出列数：${previewHeaders.length}`"
          />
          <el-table :data="previewRows" border stripe height="420">
            <el-table-column
              v-for="(h, idx) in previewHeaders"
              :key="idx"
              :prop="h"
              :label="h"
              :min-width="120"
              show-overflow-tooltip
            />
          </el-table>
        </div>
      </div>

      <template #footer>
        <div style="text-align: right">
          <el-button @click="showExportModal = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="previewRows.length === 0"
            @click="exportExcelWithFilters"
          >
            导出Excel
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="bigModel">
import {
  ref,
  onMounted,
  onUnmounted,
  nextTick,
  watch,
  inject,
  computed,
} from 'vue'
import { 
  parseJsonQuestion, 
  isJsonQuestion, 
  extractProcedures, 
  extractDiagnoses,
  formatCellContent 
} from '@/utils/chatUtils'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Edit,
  InfoFilled,
  Check,
  Close,
  Files,
  Document,
  Loading,
  Clock,
  Delete,
  Warning,
  VideoPlay,
  VideoPause,
  List,
  ArrowUp,
  Minus,
  Upload,
  View,
  CloseBold,
  Plus,
  Download,
  ArrowDown,
} from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'

import FeedbackDialog from '@/components/FeedbackDialog.vue'

import zanA from '@/assets/zan_a.png'    // 空心赞
import dzanA from '@/assets/dzan_a.png'  // 实心赞
import zanB from '@/assets/zan_b.png'    // 空心踩
import dzanB from '@/assets/dzan_b.png'  // 实心踩

// 依赖注入
const { saveChatContent, getCurrentSessionData, activeSession } = inject('historyMethods')
const route = useRoute()

// 组件挂载时也初始化一次
onMounted(() => {
  console.log('🚀 组件挂载，初始化按钮状态')
  updateButtonVisibility()

  const innerView =
    scrollbarRef.value?.wrapRef?.firstElementChild ||
    document.querySelector('.ques-content')

  if (innerView) {
    scrollObserver.observe(innerView, { childList: true, subtree: true })
  }

  loadHistoryData()
})

onUnmounted(() => {
  scrollObserver.disconnect()
})

// 【Feature 1： 消息折叠】
// -------------------------- 查询消息折叠 ----------------------------------
// 用来存储折叠状态的对象，key 为 index，value 为 boolean (true表示折叠/隐藏，false表示展开/显示)
// 默认不折叠，如果想默认折叠，初始化逻辑反过来即可
const questionCollapsedState = ref({});

// 切换折叠状态的方法
const toggleQuestionCollapse = (index) => {
  // 取反当前状态，如果未定义则默认为 false (即展开)，点击后变 true (折叠)
  questionCollapsedState.value[index] = !questionCollapsedState.value[index];
};

// 获取当前是否折叠
const isQuestionCollapsed = (index) => {
  return !!questionCollapsedState.value[index];
};


// 添加响应式状态管理展开/收起
const sectionStates = ref({})

// 获取章节状态
const getSectionState = (sectionType, index) => {
  const key = `${sectionType}_${index}`
  return sectionStates.value[key] || false
}

// 切换章节展开状态
const toggleSection = (sectionType, index) => {
  const key = `${sectionType}_${index}`
  sectionStates.value[key] = !sectionStates.value[key]
}
// 过滤出真正的文本内容（非表格且有实际内容）
const filterTextAnswers = (answerList) => {
  if (!answerList || !Array.isArray(answerList)) return []

  return answerList.filter(
    (answer) =>
      !answer.isJsonResponse &&
      !answer.isMarkdownTable &&
      (answer.content || answer.reasoning || answer.think)
  )
}
// --------------------------------------------------------------------------


// 【Feature 2：消息反馈】
// ------------------------- 反馈逻辑重构 ------------------------------------
const showFeedbackDialog = ref(false)

const currentFeedback = ref({
  message_id: null,
  type: '', 
  row_id: null,
  category: 0,
  sessionId: '' // 传给子组件用于API调用
})

// 存储点击某个诊断/手术反馈后，存储的反馈信息
const currentFeedbackStatus = ref('')

// 结构: { "messageId_category_rowId": "like" | "dislike" }
const feedbackStatusMap = ref({})

const getFeedbackKey = (msgId, category, rowIdx) => {
    return `${msgId}_${category}_${rowIdx}`
}

// 获取图标逻辑
const getFeedbackIcon = (type, msgId, rowIdx, category) => {
    const key = getFeedbackKey(msgId, category, rowIdx)
    const currentStatus = feedbackStatusMap.value[key]

    if (type === 'like') {
        return currentStatus === 'like' ? dzanA : zanA
    } else {
        return currentStatus === 'dislike' ? dzanB : zanB
    }
}

const openFeedback = async (type, message_id, row_id, category) => {
  // 1. 设置基础数据
  currentFeedback.value = { 
    message_id, 
    type, 
    row_id, 
    category,
    sessionId: activeSession.value 
  }

  // 2. 获取当前已保存的状态，传递给子组件用于判断是否回显
  const key = getFeedbackKey(message_id, category, row_id)
  currentFeedbackStatus.value = feedbackStatusMap.value[key] || ''

  // 3. 打开弹窗
  showFeedbackDialog.value = true
}

// 子组件事件处理：提交成功
const handleFeedbackSuccess = ({ message_id, category, row_id, type }) => {
  const key = getFeedbackKey(message_id, category, row_id)
  feedbackStatusMap.value[key] = type
}

// 子组件事件处理：删除成功
const handleFeedbackDeleted = ({ message_id, category, row_id }) => {
  const key = getFeedbackKey(message_id, category, row_id)
  feedbackStatusMap.value[key] = '' // 清空状态
}
// --------------------------------------------------------------------------




// 根据当前路由路径判断页面类型
const currentPageType = computed(() => {
  const path = route.path
  if (path === '/coding-pdf') return 'pdf'
  if (path === '/coding-structured') return 'structured'
  return 'main' // 默认是病案编码主页面
})

// 使用 ref 来管理按钮显示状态，避免计算属性重复计算
const showButtons = ref({
  singleUpload: false,
  batchUpload: false,
  excelUpload: false,
})

// 更新按钮显示状态的函数
const updateButtonVisibility = () => {
  const type = currentPageType.value
  console.log('🔄 更新按钮显示状态，页面类型:', type)

  showButtons.value = {
    singleUpload: type === 'main' || type === 'pdf',
    batchUpload: type === 'main' || type === 'pdf',
    excelUpload: type === 'main' || type === 'structured',
  }

  console.log('✅ 按钮显示状态:', showButtons.value)
}

// 监听路由变化
watch(
  () => route.path,
  () => {
    console.log('🔄 路由变化，当前路径:', route.path)
    nextTick(() => {
      updateButtonVisibility()
    })
  },
  { immediate: true }
)



// 响应式状态
const inputVal = ref('') // 输入框内容
const isThinking = ref(false) // 是否开启思考模式
const messageList = ref([]) // 对话列表
const isModelProcessing = ref(false) // 新增：控制模型处理中的全屏遮罩状态

const isLoadingHistory = ref(false)

const scrollbarRef = ref(null) // 新增 scrollbar 引用
const autoScrollEnabled = ref(true)
const SCROLL_BOTTOM_THRESHOLD = 80

const scrollToBottom = (force = false) => {
  if (!scrollbarRef.value) return

  if (force) {
    autoScrollEnabled.value = true
  }
  if (!autoScrollEnabled.value && !force) return

  // 获取内部 wrap 元素的滚动高度
  const wrap = scrollbarRef.value.wrapRef
  if (wrap) {
    scrollbarRef.value.setScrollTop(wrap.scrollHeight)
  }
}

const handleScroll = ({ scrollTop }) => {
  if (!scrollbarRef.value) return
  const wrap = scrollbarRef.value.wrapRef
  if (!wrap) return

  const { scrollHeight, clientHeight } = wrap
  const distanceToBottom = scrollHeight - (scrollTop + clientHeight)
  autoScrollEnabled.value = distanceToBottom <= SCROLL_BOTTOM_THRESHOLD
}

const showWelcome = ref(true) // 是否显示欢迎界面

// 上传相关状态
const showUploadModal = ref(false) // 上传弹窗显示
const currentStep = ref(1) // 当前处理步骤
const progressPercentage = ref(0) // 进度百分比
const progressStatus = ref('')

// 编辑弹窗相关状态
const showEditModal = ref(false) // 编辑弹窗显示
const editContent = ref('') // 编辑内容

// JSON编辑弹窗相关状态
const showJsonEditModal = ref(false) // JSON编辑弹窗显示
const editJsonData = ref({}) // 可编辑的JSON数据

// 批量文件JSON编辑状态
const showBatchFileJsonEditModal = ref(false) // 批量文件JSON编辑弹窗显示
const currentEditingFileIndex = ref(-1) // 当前编辑的文件索引
const batchFileJsonData = ref({}) // 当前编辑文件的JSON数据

// 批量上传相关状态
const showBatchEditModal = ref(false) // 批量编辑弹窗显示
const batchFiles = ref([]) // 批量文件列表
const batchProcessing = ref(false) // 批量处理状态
const currentProcessingIndex = ref(0) // 当前处理的文件索引
const batchProgressPercentage = ref(0) // 批量处理进度百分比
const batchProgressStatus = ref('') // 批量处理状态
const batchProgressText = ref('') // 批量处理进度文本
const batchController = ref(null) // 批量处理控制器

// 批量上传组件实例，用于重置内部文件列表
const batchUploadRef = ref(null)
const resetBatchUploader = () => {
  try {
    batchUploadRef.value &&
      batchUploadRef.value.clearFiles &&
      batchUploadRef.value.clearFiles()
  } catch (_) {}
}

// 任务队列相关状态
const showTaskModal = ref(false) // 任务浮窗显示
const taskMinimized = ref(false) // 任务浮窗是否最小化
const taskQueue = ref([]) // 任务队列
const currentTaskIndex = ref(0) // 当前执行的任务索引
const taskProcessing = ref(false) // 是否正在处理任务
const taskController = ref(null) // 任务控制器

// 导出表格
const showExportModal = ref(false)

const openExportModal = () => {
  showExportModal.value = true
  // 默认构建一次预览（可注释掉）
  // buildPreview()
}
// 时间、诊断/手术、用户、住院号、字段选择
const exportFilters = ref({
  dateRange: null, // [startISO, endISO]
  diagSurgKeyword: '', // 名称或编码关键字
  diagSurgType: 'all', // all | diag | surg
  user: '', // 创建者模糊
  inpatientNo: '', // 精确住院号
  exportAllConversations: false, // 是否导出全部对话记录
  exportAllUsers: false, // 是否导出全部用户
})

// 静态基础字段（你给的模板的前19列）
const BASE_COLUMNS = [
  '序号',
  '编码用户',
  '病案标识',
  '住院号',
  '主诉',
  '现病史',
  '既往史',
  '个人史',
  '婚姻史',
  '家族史',
  '入院情况',
  '入院诊断',
  '诊疗经过',
  '病程记录',
  '手术名称',
  '手术经过',
  '术中诊断',
  '影像学意见',
  '超声提示',
  '超声印象',
  '出院诊断',
  '编码反馈',
]

// 诊断/手术动态列的“前缀”
const DIAG_NAME_PREFIX = '诊断名称'
const DIAG_CODE_PREFIX = '诊断编码'
const DIAG_CODE_FEED = '诊断编码反馈'
const SURG_NAME_PREFIX = '手术名称'
const SURG_CODE_PREFIX = '手术编码'
const SURG_CODE_FEED = '手术编码反馈'

// 导出字段候选（默认选中全部基础列；动态列会自动扩展，不在这里列出）
const exportFieldOptions = BASE_COLUMNS.slice(0) // 拷贝
const selectedExportFields = ref(BASE_COLUMNS.slice(0)) // 默认全选基础列

const selectAllFields = (checked) => {
  selectedExportFields.value = checked ? exportFieldOptions.slice(0) : []
}
const resetFieldsToDefault = () => {
  selectedExportFields.value = BASE_COLUMNS.slice(0)
}

// 上传取消控制
const uploadController = ref(null) // 上传控制器

// 常量配置
const UPLOAD_CONFIG = {
  maxSize: 100 * 1024 * 1024, // 100MB for images
  pdfMaxSize: 13 * 1024 * 1024, // 13MB for PDF files
  validTypes: ['image/jpeg', 'image/png', 'application/pdf'],
  acceptTypes: '.jpg,.jpeg,.png,.pdf',
}

// OCR服务配置
const OCR_CONFIG = {
  endpoint: '/ocr/ocr', // 使用代理路径
  timeout: 60000 * 4, // 60秒超时
}

// 进度条平滑动画：缓动函数和动画推进
const easeInOutQuad = (t) =>
  t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2
const animateProgress = (to, duration = 500) => {
  const start = performance.now()
  const from = progressPercentage.value
  const delta = to - from
  return new Promise((resolve) => {
    const frame = (now) => {
      const elapsed = now - start
      const p = Math.min(1, elapsed / duration)
      const eased = easeInOutQuad(p)
      progressPercentage.value = Math.round(from + delta * eased)
      if (p < 1) {
        requestAnimationFrame(frame)
      } else {
        resolve()
      }
    }
    requestAnimationFrame(frame)
  })
}

// OCR 字段名映射：将中文键映射为后端模型字段
const OCR_FIELD_MAP = {
  个人史: 'personal_history',
  主诉: 'chief_complaint',
  住院号: 'inpatient_no',
  入院情况: 'admission_status',
  入院诊断: 'admission_diagnosis',
  出院诊断: 'discharge_diagnosis',
  婚姻史: 'marital_history',
  家族史: 'family_history',
  影像学意见: 'imaging_opinion',
  影像意见: 'imaging_opinion',
  影像学结论: 'imaging_opinion',
  手术名称: 'operation_name',
  手术经过: 'operation_course',
  手术记录: 'operation_course',
  既往史: 'past_history',
  术中诊断: 'intraoperative_diagnosis',
  现病史: 'present_illness',
  病案标识: 'case_identifier',
  病程记录: 'course_record',
  诊疗经过: 'treatment_course',
  超声印象: 'ultrasound_impression',
  超声提示: 'ultrasound_hint',
}

// 保存OCR结果到后端（会话已登录时通过凭证携带 Cookie）。可选传入文件对象
const saveOCRResult = async (filename, rawText, fileObj = null) => {
  try {
    let res
    const tryParse = (v) => {
      if (typeof v === 'string') {
        try {
          const o = JSON.parse(v)
          return o && typeof o === 'object' ? o : null
        } catch {
          return null
        }
      }
      return v && typeof v === 'object' ? v : null
    }
    const rawObj = tryParse(rawText)
    const rawTextStr =
      typeof rawText === 'string' ? rawText : JSON.stringify(rawText)

    if (fileObj) {
      // 使用 multipart/form-data 携带文件与字段
      const fd = new FormData()
      const finalName = filename || (fileObj && fileObj.name) || 'unknown'
      fd.append('filename', finalName)
      // 保留完整原始JSON
      fd.append('raw_text', rawTextStr)
      // 映射并展开字段
      if (rawObj) {
        Object.entries(rawObj).forEach(([k, v]) => {
          const mapped = OCR_FIELD_MAP[k]
          if (mapped) {
            fd.append(mapped, typeof v === 'string' ? v : JSON.stringify(v))
          }
        })
      }
      fd.append('file', fileObj)
      res = await fetch('/api/qy/ocr/records/', {
        method: 'POST',
        credentials: 'include',
        body: fd,
      })
    } else {
      // 兼容无文件时的 JSON 写入，展开已映射字段
      const payload = { filename, raw_text: rawTextStr }
      if (rawObj) {
        Object.entries(rawObj).forEach(([k, v]) => {
          const mapped = OCR_FIELD_MAP[k]
          if (mapped) {
            payload[mapped] = typeof v === 'string' ? v : JSON.stringify(v)
          }
        })
      }
      res = await fetch('/api/qy/ocr/records/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      })
    }
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      console.warn('保存OCR结果失败:', res.status, text)
      return
    }
    console.log('已保存OCR结果:', filename)
  } catch (e) {
    console.warn('保存OCR结果异常:', e)
  }
}

// 必填Excel字段（按你提供的顺序/名称）
const REQUIRED_EXCEL_FIELDS = [
  '病案标识',
  '住院号',
  '主诉',
  '现病史',
  '既往史',
  '个人史',
  '婚姻史',
  '家族史',
  '入院情况',
  '入院诊断',
  '诊疗经过',
  '病程记录',
  '手术名称',
  '手术经过',
  '术中诊断',
  '影像学意见',
  '超声提示',
  '超声印象',
  '出院诊断',
]

// 可选：扩充允许的MIME（不会影响既有图片/PDF上传）
UPLOAD_CONFIG.validTypes.push(
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv'
)

/** 将Excel标题做规格化（去空白、全角转半角） */
const normalizeHeader = (h = '') => {
  if (!h) return ''
  // 全角转半角 + 去除前后空白
  return String(h)
    .replace(/[\u3000]/g, ' ')
    .replace(/[　]/g, ' ')
    .replace(/\s+/g, '')
    .trim()
}

/** 校验Excel表头 */
const validateExcelHeaders = (headersRaw = []) => {
  const normalized = headersRaw.map(normalizeHeader)
  const miss = REQUIRED_EXCEL_FIELDS.filter(
    (f) => !normalized.includes(normalizeHeader(f))
  )
  return { ok: miss.length === 0, missing: miss }
}

/** 把一行Excel数据映射为JSON（保留中文键，兼容你现有 OCR_FIELD_MAP 的存储逻辑） */
const mapExcelRowToJson = (row, headerMap) => {
  const obj = {}
  REQUIRED_EXCEL_FIELDS.forEach((cnKey) => {
    const idx = headerMap.get(normalizeHeader(cnKey))
    obj[cnKey] = idx != null ? row[idx] ?? '' : ''
  })
  return obj
}

/** 读取File为ArrayBuffer */
const readFileAsArrayBuffer = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsArrayBuffer(file.raw || file)
  })

/** 读取File为文本（用于CSV） */
const readFileAsText = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file.raw || file, 'utf-8')
  })

/** 解析CSV为二维数组 */
const parseCSV = (text) => {
  // 简单CSV解析（支持逗号，带引号单元格）
  const rows = []
  let i = 0,
    field = '',
    row = [],
    inQuotes = false
  const pushField = () => {
    row.push(field)
    field = ''
  }
  const pushRow = () => {
    rows.push(row)
    row = []
  }

  while (i < text.length) {
    const c = text[i]
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i++
        } // 转义引号
        else inQuotes = false
      } else field += c
    } else {
      if (c === '"') inQuotes = true
      else if (c === ',') pushField()
      else if (c === '\n') {
        pushField()
        pushRow()
      } else if (c === '\r') {
        /* ignore */
      } else field += c
    }
    i++
  }
  // last field/row
  pushField()
  if (row.length) pushRow()
  return rows.filter(
    (r) => r.length && r.some((v) => String(v || '').trim() !== '')
  )
}

/** Excel 上传入口 */
const handleExcelChange = async (file) => {
  try {
    // 1) 识别类型：xlsx/xls 用 XLSX，csv 走文本解析
    let rowsAoA = [] // [][]: [ [header...], [row...], ... ]
    if (file.name.endsWith('.csv')) {
      const text = await readFileAsText(file)
      rowsAoA = parseCSV(text)
      if (!rowsAoA.length) throw new Error('CSV 内容为空')
    } else {
      const buf = await readFileAsArrayBuffer(file)
      const wb = XLSX.read(buf, { type: 'array' })
      const sheet = wb.Sheets[wb.SheetNames[0]]
      // 使用原始值，避免把数字转科学计数法；defval让空单元格为 ''
      rowsAoA = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
      if (!rowsAoA.length) throw new Error('Excel 内容为空')
    }

    // 2) 表头校验
    const [headerRow, ...dataRows] = rowsAoA
    if (!headerRow || headerRow.length === 0) {
      ElMessage.error('未检测到表头行')
      return
    }
    const { ok, missing } = validateExcelHeaders(headerRow)
    if (!ok) {
      ElMessage.error(`表头缺失字段：${missing.join('、')}`)
      return
    }

    // 3) 构建 header 索引映射
    const headerMap = new Map()
    headerRow.forEach((h, idx) => headerMap.set(normalizeHeader(h), idx))

    // 4) 行数据 → JSON；过滤掉全空行
    const payloads = []
    for (const r of dataRows) {
      const obj = mapExcelRowToJson(r, headerMap)
      const nonEmpty = Object.values(obj).some(
        (v) => String(v || '').trim() !== ''
      )
      if (!nonEmpty) continue
      payloads.push(obj)
    }

    if (!payloads.length) {
      ElMessage.warning('没有可提交的数据行（全部为空）')
      return
    }

    // 5) 生成任务队列并开跑（与现有批量任务完全复用）
    taskQueue.value = payloads.map((o, i) => ({
      fileName: file.name.replace(/\.(xlsx|xls|csv)$/i, '') + `#${i + 1}`,
      content: JSON.stringify(o), // 关键：按JSON字符串放入，submit()会识别为OCR JSON路径
      completed: false,
      failed: false,
      processing: false,
      errorMessage: '',
      result: null,
      createTime: new Date().toLocaleString(),
    }))

    // 可选：也把这些数据塞进批量编辑弹窗供二次编辑
    // 若你想“先预览再提交”，把下面 autoStart = false，并打开 showBatchEditModal。
    const autoStart = false
    if (!autoStart) {
      batchFiles.value = payloads.map((o, i) => ({
        name: `${file.name}#${i + 1}`,
        file: null,
        content: JSON.stringify(o, null, 2),
        processing: false,
        completed: true,
        error: false,
        errorMessage: '',
      }))
      showBatchEditModal.value = true
      ElMessage.success(
        `已导入 ${payloads.length} 行数据，可审阅后创建任务队列`
      )
      return
    }

    // 直接开始任务
    currentTaskIndex.value = 0
    taskProcessing.value = false
    showTaskModal.value = true
    taskMinimized.value = false
    startTaskQueue()
    ElMessage.success(`已读取 ${payloads.length} 行，开始批量提交`)
  } catch (err) {
    console.error(err)
    ElMessage.error(`Excel 处理失败：${err.message || err}`)
  }
}

const PROCESS_STEPS = [
  '正在上传文件...',
  '正在进行文本识别...',
  '正在进行信息脱敏处理...',
  '正在进行标准化处理...',
]

// 计算属性：进度文本
const processTexts = PROCESS_STEPS

// 批量处理计算属性
const allFilesProcessed = computed(() => {
  return (
    batchFiles.value.length > 0 &&
    batchFiles.value.every((file) => file.completed || file.error)
  )
})

const hasValidContent = computed(() => {
  return batchFiles.value.some(
    (file) => file.completed && file.content && file.content
  )
})

const validFileCount = computed(() => {
  return batchFiles.value.filter(
    (file) => file.completed && file.content && file.content
  ).length
})

// 任务队列计算属性
const totalTasks = computed(() => taskQueue.value.length)
const completedTasks = computed(
  () => taskQueue.value.filter((task) => task.completed).length
)
const failedTasks = computed(
  () => taskQueue.value.filter((task) => task.failed).length
)
const taskProgress = computed(() => {
  if (totalTasks.value === 0) return 0
  return Math.floor((completedTasks.value / totalTasks.value) * 100)
})

// 滚动监听器
const scrollObserver = new MutationObserver(() => {
  scrollToBottom()
})

// 监听路由变化
watch(
  () => route.query.historyId,
  (newId) => {
    if (newId) {
      //
      //loadHistoryData()
    }
  }
)

watch(
  () => exportFilters.value.exportAllUsers,
  (newVal) => {
    if (newVal) {
      exportFilters.value.exportAllConversations = true
    }
  },
  { immediate: true } // 可选：若初始值为 true，则挂载时立即同步
)

// Markdown表格解析函数
const parseMarkdownTable = (content) => {
  try {
    console.log('🔍 开始解析Markdown表格...')

    // 移除前后空白并按行分割
    const lines = content
      .trim()
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line)

    if (lines.length < 2) {
      console.log('❌ 内容行数不足，不是有效的Markdown表格')
      return null
    }

    const tableData = []
    let headerProcessed = false

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]

      // 跳过分隔符行（如：|---|---|）
      if (line.match(/^\s*\|[\s\-\|]*\|\s*$/)) {
        console.log(`⏭️ 跳过分隔符行: ${line}`)
        continue
      }

      // 检查是否为表格行（包含 | 分隔符）
      if (line.includes('|')) {
        // 解析表格行
        const cells = line
          .replace('\\\\n', '') // 移除HTML标签
          .split('|')
          .map((cell) => cell.trim())
          .filter((cell) => cell !== '') // 移除空的首尾单元格

        if (cells.length >= 2) {
          if (!headerProcessed) {
            console.log(`📋 处理表头: ${cells}`)
            headerProcessed = true
          }

          tableData.push(cells)
          console.log(`📝 添加行数据: ${cells}`)
        }
      }
    }

    if (tableData.length > 0) {
      console.log('✅ Markdown表格解析成功，共', tableData.length, '行')
      return tableData
    } else {
      console.log('❌ 未找到有效的表格数据')
      return null
    }
  } catch (error) {
    console.error('❌ Markdown表格解析出错:', error)
    return null
  }
}



const cleanMarkdownText = (text = '') => {
  return text
    .toString()
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/\\n/g, '\n')
    .trim()
}

const parseStructuredMarkdown = (content = '', type = 'diagnosis') => {
  const table = parseMarkdownTable(content)
  if (!table || table.length < 2) return { ids: [], entries: [] }

  const headerRow = table[0].map((cell) => cleanMarkdownText(cell))
  const idIndex = headerRow.findIndex((h) => h.includes('唯一标识'))
  const nameLabel = type === 'diagnosis' ? '诊断名称' : '手术名称'
  const codeLabel = type === 'diagnosis' ? '诊断编码' : '手术编码'
  const nameIndex = headerRow.findIndex((h) => h.includes(nameLabel))
  const codeIndex = headerRow.findIndex((h) => h.includes(codeLabel))

  if (nameIndex === -1 || codeIndex === -1) {
    return { ids: [], entries: [] }
  }

  const ids = []
  const entries = []

  for (const row of table.slice(1)) {
    const cells = row.map((cell) => cleanMarkdownText(cell))
    if (idIndex !== -1 && cells[idIndex]) ids.push(cells[idIndex])
    const name = cells[nameIndex] || ''
    let code = cells[codeIndex] || ''
    if (code) {
      const normalized = code
        .replace(/\[/g, '')
        .replace(/\]/g, '')
        .replace(/'/g, '')
        .trim()
      code = normalized
    }
    entries.push({ name, code })
  }

  return {
    ids: Array.from(new Set(ids.filter(Boolean))),
    entries: entries.filter((entry) => entry.name || entry.code),
  }
}

watch(activeSession, (newId) => {
  if (newId) {
    // 加载对应会话的消息数据
    //
    loadHistoryData()
  }
})

import {
  apiGetUserChatSessions,
  apiGetUserChatMessages,
  apiGetUserChatMessagesAll,
  apiGetUserChatMessagesAllAll,
  apiGetAllChatMessageFeedback,
  apiGetAllChatMessageFeedbackAll,
  apiGetAllChatMessageFeedbackAllAll,
  apiGetRemarkChatMessageFeedback,
  apiSubmitChatMessageFeedback,
  apiDeleteChatMessageFeedback,
  apiExportFeedback,
  apiSaveIcdCodes,
} from '@/api/chat'


const feedbackList = ref([]) // 反馈列表

const loadHistoryData = async () => {
  // 1. 设置加载锁：防止 watcher 触发保存
  isLoadingHistory.value = true
  //
  const session = getCurrentSessionData()

  if (!session) {
    isLoadingHistory.value = false
    return
  }

  try {
    const session_id = session.id
    const res = await apiGetUserChatMessages({ session_id })
    const messages_list = res.data.data // 会返回Message对应的id
    if (messages_list && messages_list.length > 0) {
      const t_data = messages_list.map((item) => {
        let msg = item.message
        msg = typeof msg === 'string' ? JSON.parse(msg) : msg
        msg['message_id'] = item.id // 保存 Message 的 ID 以便反馈使用
        return msg
      })

      // 2. 赋值操作：这确实会触发 watch，但因为 isLoadingHistory 为 true，saveChatData 会被拦截
      messageList.value = t_data

      showWelcome.value = false
      console.log('历史记录加载成功')

      // 3. 使用 nextTick 确保在 DOM 更新、watch 回调执行完毕后，再释放锁
      nextTick(() => {
        scrollToBottom(true)
        // 关键点：一定要在 nextTick 里释放，保证之前的 watch 周期已经跑完
        isLoadingHistory.value = false
      })

      // 获取对应反馈
      const feedbackRes = await apiGetAllChatMessageFeedback({ session_id })
      feedbackList.value = feedbackRes.data.data //message_id category row_id type

      // TODO 处理反馈数据，更新反馈状态映射 
      feedbackList.value.forEach((feedback) => {
        const key = getFeedbackKey(feedback.message_id, feedback.category, feedback.row_id)
        feedbackStatusMap.value[key] = feedback.type
      })
    } else {
      // 处理空数据的情况
      messageList.value = []
      showWelcome.value = true

      nextTick(() => {
        isLoadingHistory.value = false
      })
    }
  } catch (e) {
    console.error('加载或解析历史记录失败:', e)
    messageList.value = []
    showWelcome.value = true
    isLoadingHistory.value = false
  }
}

const isAIResponding = ref(false)

const saveChatData = (newVal, oldVal) => {
  // [ADD] Block saving if we are currently loading history
  if (isLoadingHistory.value) {
    return
  }

  // 如果 AI 正在回答中，跳过保存。
  if (isAIResponding.value) {
    return
  }

  const oldList = Array.isArray(oldVal) ? oldVal : []
  const newList = Array.isArray(newVal) ? newVal : []

  // 假设你要处理增量数据：
  return saveChatContent(activeSession.value, newList, oldList)
}

watch(
  () => [...messageList.value],
  (newVal, oldVal) => {
    saveChatData(newVal, oldVal)
  }
)
watch(
  messageList,
  (newList) => {
    // 清空旧状态
    questionCollapsedState.value = {};

    // 为每一项创建默认折叠状态（例如默认全部展开：false，或全部折叠：true）
    newList.forEach((_, index) => {
      // 推荐用 index 作为 key（因为列表顺序可能变化）
      questionCollapsedState.value[index] = false;
    });
  },
  { immediate: true } // 组件创建时立即执行一次
);

// API 调用相关
// const callLLMAPI = async (prompt, onStream) => {
const callLLMAPI = async (prompt, onStream, mytype = 'diagnosis') => {
  try {
    // 根据思考模式选择不同的API端点和模型
    const modelName = isThinking.value ? 'deepseek-r1' : 'my_model'
    let apiEndpoint = ''
    if (mytype === 'diagnosis') {
      apiEndpoint = isThinking.value
        ? '/llm/deepseek/diagnosis_qwen'
        : '/diag/qwen3/diagnosis_qwen'
    } else {
      apiEndpoint = isThinking.value
        ? '/llm/deepseek/surger_qwen'
        : '/sur/qwen3/surgeries_diagnosis'
    }

    // 处理prompt格式 - 统一格式化为JSON格式
    let formattedPrompt = prompt
    try {
      const parsedJson = JSON.parse(prompt)
      if (parsedJson && typeof parsedJson === 'object') {
        // 已经是JSON格式，格式化为更好的提示
        formattedPrompt = JSON.stringify(parsedJson, null, 2)
      } else {
        // 不是JSON对象，包装成JSON格式
        formattedPrompt = JSON.stringify({ data: prompt }, null, 2)
      }
    } catch (error) {
      // 不是JSON格式，包装成JSON格式
      formattedPrompt = JSON.stringify({ data: prompt }, null, 2)
    }
    console.log('*****************')
    console.log('🔍 调用API，使用模型:', modelName)
    // console.log('📜 格式化后的提示:', formattedPrompt)
    console.log('*****************')
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: modelName,
        token: '',
        messages: [{ role: 'user', content: formattedPrompt }],
        history: messageList.value,
      }),
    })
    console.log('*****************')
    console.log(isThinking.value)
    console.log('*****************')

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`)
    }
    console.log(response)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentAnswer = {
      type: 'reasoning',
      encounter_type: mytype,
      reasoning: '',
      content: '',
      next_agent: false,
      next_agent_url: '',
      agent_name: '',
    }

    // 用于检测是否需要非流式处理
    let isTableDisplayMode = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // console.log('接收到数据块:', buffer)
      const messages = buffer.split('\n')
      buffer = messages.pop() || ''

      // console.log('接收到buffer:', buffer)
      console.log('接收到messages:', messages)
      for (const message of messages) {
        // console.log(message)
        if (!message.trim()) continue

        try {
          const data = JSON.parse(message)
          currentAnswer.new_role = false

          if (currentAnswer.agent_name !== data.agent_name) {
            currentAnswer.new_role = true
            if (currentAnswer.agent_name === '') {
              currentAnswer.new_role = false
            }
            currentAnswer.agent_name = data.agent_name

            // 检测是否为表格展示模式
            if (data.agent_name.includes('表格展示')) {
              isTableDisplayMode = true
              console.log('🔍 检测到表格展示模式，将使用非流式处理')
            }

            currentAnswer.type = 'reasoning'
            currentAnswer.reasoning = ''
            currentAnswer.content = ''
          }

          // if (data.message?.reasoning_content) {
          //   currentAnswer.type = 'reasoning'
          //   currentAnswer.reasoning += data.message.reasoning_content
          //   if (onStream && !isTableDisplayMode) onStream(currentAnswer)
          // }

          if (data.message?.content) {
            console.log('接收到内容:', data.message.content)
            // if (currentAnswer.type === 'reasoning' && data.message.content.includes('<think>')) {
            //   const tempContent = data.message.content
            //   // console.log('💡 解析到思考标记，提取推理内容:', tempContent)
            //   // tempContent = tempContent.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
            //   // currentAnswer.reasoning += '无'
            //   if (onStream && !isTableDisplayMode) onStream(currentAnswer)

            // }
            currentAnswer.type = 'content'

            currentAnswer.content += data.message.content
            // 移除 <think> </think> 标记
            currentAnswer.content = currentAnswer.content
              .replace(/<think>/g, '')
              .replace(/<\/think>/g, '')

            // 如果是表格展示模式，先缓存内容，不立即流式输出
            if (isTableDisplayMode) {
              console.log('📊 表格模式：缓存内容中...')
            } else if (onStream) {
              onStream(currentAnswer)
            }
          }
        } catch (e) {
          console.error('解析JSON失败:', e, '原始数据:', message)
        }
      }
    }
    console.log('*****************')
    console.log(isTableDisplayMode)
    console.log(currentAnswer.content)
    console.log('*****************')
    // 如果是表格展示模式，尝试解析最终内容
    if (isTableDisplayMode && currentAnswer.content) {
      console.log('🔄 表格模式：开始解析内容')
      console.log('📝 原始内容:', currentAnswer.content)

      // 首先尝试解析为JSON
      try {
        const jsonContent = JSON.parse(currentAnswer.content)
        console.log('✅ 表格模式：JSON解析成功', jsonContent)

        // 标记这是一个特殊的JSON响应
        currentAnswer.isJsonResponse = true
        currentAnswer.jsonData = jsonContent
        console.log(
          '📊 表格模式：将JSON数据添加到当前回答中',
          currentAnswer.jsonData
        )

        // 一次性返回完整内容
        if (onStream) {
          onStream(currentAnswer)
        }
      } catch (jsonError) {
        console.log('⚠️ JSON解析失败，尝试Markdown表格解析')

        // 尝试解析为Markdown表格
        const markdownTable = parseMarkdownTable(currentAnswer.content)
        if (markdownTable && markdownTable.length > 0) {
          console.log('✅ 表格模式：Markdown表格解析成功', markdownTable)

          // 标记为Markdown表格响应
          currentAnswer.isMarkdownTable = true
          currentAnswer.tableData = markdownTable
          currentAnswer.isJsonResponse = false // 明确标记不是JSON

          console.log('📊 表格模式：将Markdown表格数据添加到当前回答中')

          // 一次性返回完整内容
          if (onStream) {
            onStream(currentAnswer)
          }
        } else {
          console.log('❌ 表格模式：Markdown表格解析也失败，降级为普通文本模式')
          // 解析失败时降级为普通流式处理
          if (onStream) {
            onStream(currentAnswer)
          }
        }
      }
    }

    return currentAnswer
  } catch (error) {
    console.error('调用API出错:', error)
    throw error
  }
}

const callBothLLMAPI = async (prompt, onStream) => {
  return Promise.all([
    callLLMAPI(prompt, (resp) => onStream('diagnosis', resp), 'diagnosis'),
    callLLMAPI(prompt, (resp) => onStream('surgery', resp), 'surgery'),
  ])
  // 这里onStream回调第二个参数用于区分类型
}

// 主要功能实现
const submit = async (customQuestion = null) => {
  // 验证customQuestion参数，排除事件对象
  if (
    customQuestion &&
    typeof customQuestion === 'object' &&
    customQuestion.isTrusted !== undefined
  ) {
    console.warn('❌ 检测到事件对象被传入submit函数，忽略该参数')
    customQuestion = null
  }

  // 区分两种提交方式
  let question = null
  let questionSource = ''

  if (customQuestion && typeof customQuestion === 'string') {
    // 方式1: OCR识别的JSON数据提交
    // const jsonString = JSON.stringify(customQuestion);
    // console.log('转换后的字符串:', jsonString);
    question = customQuestion
    // question = customQuestion
    questionSource = 'OCR'
    console.log('🔍 OCR JSON数据提交:', customQuestion)
  } else {
    // 方式2: 对话框输入提交
    question = inputVal.value?.trim()
    questionSource = 'INPUT'
    console.log('🔍 对话框输入提交:', question) //Excel表格形式会经过这里，question是json数据，表示病人的住院信息

    if (!question) {
      console.warn('❌ 对话框输入为空，取消提交')
      return Promise.resolve()
    }

    // 清空输入框
    inputVal.value = ''
  }

  if (!question) {
    console.warn('❌ 没有有效的问题内容，取消提交')
    return Promise.resolve()
  }

  showWelcome.value = false

  // [关键步骤 1] 在 push 之前，先捕获当前的列表作为“旧数据”快照
  // 使用浅拷贝即可，因为 saveChatContent 只关心长度
  const oldListSnapshot = [...messageList.value]

  // [关键步骤 2] 开启标记，阻止 watch 自动保存不完整的数据
  isAIResponding.value = true

  // 新增：如果不是批量任务队列处理中，则显示全屏加载遮罩
  // 这样用户在单次上传文件或提问时会看到“处理中”提示，避免面对空白内容
  if (!taskProcessing.value) {
    isModelProcessing.value = true
  }

  // 添加问题到聊天列表： json列表，每个json表示一条查询的病人信息
  messageList.value.push({
    message_id: null,
    question,
    answers: {
      diagnosis: { answerList: [] },
      surgery: { answerList: [] },
    },
    questionSource, // 记录问题来源，便于调试
    createdAt: new Date().toISOString(), // ✅ 导出-时间筛选
    createdBy: JSON.parse(localStorage.getItem("user_info"))?.username || '当前用户', // ✅ 导出-用户筛选（你可改成真实登录用户名注入）
  })
  autoScrollEnabled.value = true
  nextTick(() => {
    scrollToBottom(true)
  })
  const idx = messageList.value.length - 1 // 取当前条查询

  // 辅助函数：当收到有效内容时停止加载遮罩
  // const stopLoading = () => {
  //   if (isModelProcessing.value) {
  //     isModelProcessing.value = false
  //   }
  // }

  const diagPromise = callLLMAPI(
    question,
    (res) => {
      //stopLoading()

      const answerArr = messageList.value[idx].answers.diagnosis.answerList
      // 是否是新agent，标准1（有 new_role 标记）
      const isNewAgent = res.new_role
      // 标准2，看 agent_name 是否切换
      const curAgentName = answerArr.length
        ? answerArr[answerArr.length - 1].name
        : null
      const agentChanged = !!res.agent_name && res.agent_name !== curAgentName

      if (!answerArr.length || isNewAgent || agentChanged) {
        // 新agent流开始，新建answer
        answerArr.push({
          reasoning: res.reasoning || '',
          content: res.content || '',
          name: res.agent_name || '表格展示',
          isStreaming: true,
          isJsonResponse: res.isJsonResponse,
          jsonData: res.isJsonResponse ? res.jsonData : undefined,
          isMarkdownTable: res.isMarkdownTable,
          tableData: res.isMarkdownTable ? res.tableData : undefined,
          encounter_type: 'diagnosis',
        })
      } else {
        // 继续原来的流，merge内容
        const last = answerArr[answerArr.length - 1]
        // 逐项合并
        if (res.reasoning) last.reasoning = res.reasoning
        if (res.content) last.content = res.content
        if (res.agent_name) last.name = res.agent_name
        if (res.isJsonResponse && res.jsonData) {
          last.isJsonResponse = true
          last.jsonData = res.jsonData
          last.isStreaming = false
        }
        if (res.isMarkdownTable && res.tableData) {
          last.isMarkdownTable = true
          last.tableData = res.tableData
          last.isStreaming = false
        }
        // 其他状态字段合并...
      }
    },
    'diagnosis'
  )

  const surgPromise = callLLMAPI(
    question,
    (res) => {
      //stopLoading()

      const answerArr = messageList.value[idx].answers.surgery.answerList
      // 是否是新agent，标准1（有 new_role 标记）
      const isNewAgent = res.new_role
      // 标准2，看 agent_name 是否切换
      const curAgentName = answerArr.length
        ? answerArr[answerArr.length - 1].name
        : null
      const agentChanged = !!res.agent_name && res.agent_name !== curAgentName

      if (!answerArr.length || isNewAgent || agentChanged) {
        // 新agent流开始，新建answer
        answerArr.push({
          reasoning: res.reasoning || '',
          content: res.content || '',
          name: res.agent_name || 'AI助手',
          isStreaming: true,
          isJsonResponse: res.isJsonResponse,
          jsonData: res.isJsonResponse ? res.jsonData : undefined,
          isMarkdownTable: res.isMarkdownTable,
          tableData: res.isMarkdownTable ? res.tableData : undefined,
          encounter_type: 'surgery',
        })
      } else {
        // 继续原来的流，merge内容
        const last = answerArr[answerArr.length - 1]
        // 逐项合并
        if (res.reasoning) last.reasoning = res.reasoning
        if (res.content) last.content = res.content
        if (res.agent_name) last.name = res.agent_name
        if (res.isJsonResponse && res.jsonData) {
          last.isJsonResponse = true
          last.jsonData = res.jsonData
          last.isStreaming = false
        }
        if (res.isMarkdownTable && res.tableData) {
          last.isMarkdownTable = true
          last.tableData = res.tableData
          last.isStreaming = false
        }
        // 其他状态字段合并...
      }
    },
    'surgery'
  )
  //await Promise.allSettled([diagPromise, surgPromise])
  await Promise.all([diagPromise, surgPromise])
  // 确保在请求结束后关闭遮罩（防止接口报错或无响应导致遮罩一直存在）
  isModelProcessing.value = false

  // 关闭标记，允许保存
  isAIResponding.value = false

  // 当前编码结果
  const currentMessageSnapshot = messageList.value[messageList.value.length - 1];

  // 手动触发保存，显式传入 新列表 和 步骤1中捕获的旧列表
  const message_ids = await saveChatData(messageList.value, oldListSnapshot)
  // 更新当前消息的 message_id（假设只有一条新增消息）
  if (message_ids && message_ids.length > 0) {
    messageList.value[messageList.value.length - 1].message_id = message_ids[0]
  }

  //console.log("✅ 问答结束，正在同步后端真实ID...")
  //await loadHistoryData()

  //模型回复完成后，将本次编码结果保存到数据库中
  const allEntries = [];
  const responseTime = new Date().toISOString();
  for (const answerType of ['diagnosis', 'surgery']) { // TODO 别忘了加 'diagnosis'
    const tableData = currentMessageSnapshot?.answers?.[answerType]?.answerList?.at(-1)?.tableData;
    if (!tableData || tableData.length < 2) continue;

    // 从第 1 行开始（跳过标题行）
    for (let i = 1; i < tableData.length; i++) {
      const row = tableData[i];

      if (row.length < 3) continue; // 至少要有 case_id, name, code

      const rawName = row[1] || '';
      const cleanName = rawName.replace(/^\*+|\*+$/g, '').trim();

      const rawCode = row[2] || '';
      let cleanCode = rawCode.replace(/^\*+|\*+$/g, '').trim();
      cleanCode = cleanCode.replace(/^['"\[]+|['"\]]+$/g, '').trim();

      const entry = {
        answerType,           // 'diagnosis' | 'surgery'
        case_id: row[0],      // "0000509863"
        // 注意：这里用 row 索引并不代表真实的 seq，如果是前端生成 seq 需要小心，
        // 这里暂时保留原逻辑 surgery_id / diag_seq 的处理逻辑需要在后端或此处明确
        seq: i,               //  作为序号传递
        name: cleanName,      // "药物洗脱冠状动脉支架置入"
        code: cleanCode,      // '36.0700'
        model_response_time: responseTime, // 新增字段
      };

      if (answerType === 'diagnosis') {
           // 假设前端能区分或者默认 "出院诊断"，具体逻辑根据业务需求调整
           // 这里简单示例传个默认值，或者从 row 数据中获取（如果 row 里有的话）
          entry.diag_type = '出院诊断'; 
      }

      allEntries.push(entry);
    }
  }

  try {
      const response = await apiSaveIcdCodes(allEntries);

      if (response.data.code === 200) {
          ElMessage.success('编码结果已保存到数据库！');
      }
    } catch (err) {
      ElMessage.error('编码结果保存到数据库失败！')
    }

}



// 文件上传处理
const handleFileChange = (file) => {
  if (!UPLOAD_CONFIG.validTypes.includes(file.raw.type)) {
    ElMessage.error('请上传 JPG/PNG/PDF 格式的文件')
    return
  }

  // Check file size based on type
  if (file.raw.type === 'application/pdf') {
    if (file.size > UPLOAD_CONFIG.pdfMaxSize) {
      ElMessage.error('PDF 文件大小不能超过 13MB')
      return
    }
  } else {
    if (file.size > UPLOAD_CONFIG.maxSize) {
      ElMessage.error('图片文件大小不能超过 100MB')
      return
    }
  }

  // 清空输入框，避免与OCR数据混淆
  inputVal.value = ''
  console.log('🧹 已清空输入框，开始OCR处理')

  // 开始上传处理流程
  console.log('开始上传文件:', file)
  startUploadProcess(file)
}

// 批量文件上传处理
const handleBatchFileChange = (file, fileList) => {
  const invalidFiles = fileList.filter((f) => {
    if (!UPLOAD_CONFIG.validTypes.includes(f.raw.type)) {
      return true
    }
    // Check size based on file type
    if (f.raw.type === 'application/pdf') {
      return f.size > UPLOAD_CONFIG.pdfMaxSize
    } else {
      return f.size > UPLOAD_CONFIG.maxSize
    }
  })

  if (invalidFiles.length > 0) {
    ElMessage.error(
      `有 ${invalidFiles.length} 个文件不符合要求，请上传 JPG/PNG/PDF 格式，PDF 文件小于 13MB，图片文件小于 100MB`
    )
    return
  }

  // 清空输入框，避免与批量OCR数据混淆
  inputVal.value = ''
  // console.log('🧹 已清空输入框，开始批量OCR处理')

  // 创建批量文件对象
  const newBatchFiles = fileList.map((f) => ({
    name: f.name,
    file: f.raw,
    content: '',
    processing: false,
    completed: false,
    error: false,
    errorMessage: '',
  }))

  batchFiles.value = newBatchFiles
  showBatchEditModal.value = true

  // console.log('批量选择文件:', newBatchFiles.length, '个')
  // console.log('批量文件列表:', newBatchFiles)

  // 清空组件内的历史选择，避免下一次 on-change 带上旧文件
  nextTick(() => {
    resetBatchUploader()
  })
}

// 开始上传处理流程
const startUploadProcess = async (file) => {
  showUploadModal.value = true
  currentStep.value = 1
  progressPercentage.value = 0
  progressStatus.value = ''

  // 创建新的控制器
  uploadController.value = new AbortController()

  try {
    // 第一步：文件上传
    currentStep.value = 1
    await animateProgress(24, 100)
    await new Promise((resolve) => setTimeout(resolve, 200))

    // 创建FormData对象
    const formData = new FormData()
    formData.append('file', file.raw)

    // 第二步：文本识别
    currentStep.value = 2
    await animateProgress(49, 100)

    // 创建超时控制器
    const timeoutId = setTimeout(() => {
      if (uploadController.value) {
        uploadController.value.abort()
      }
    }, OCR_CONFIG.timeout)

    // 调用后端OCR API
    console.log('开始调用OCR服务...')
    console.log('上传的文件:', file.raw)
    const response = await fetch(OCR_CONFIG.endpoint, {
      method: 'POST',
      body: formData,
      signal: uploadController.value.signal,
    })

    // 清除超时定时器
    clearTimeout(timeoutId)

    // 第三步：信息脱敏
    currentStep.value = 3
    await animateProgress(59, 100)
    await new Promise((resolve) => setTimeout(resolve, 600))
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`服务器错误 ${response.status}: ${errorText}`)
    }
    const result = await response.json()
    // 第四步：标准化处理
    currentStep.value = 4
    await animateProgress(98, 100)
    await new Promise((resolve) => setTimeout(resolve, 1000))
    // 检查响应格式
    if (result.error) {
      throw new Error(result.error)
    }
    if (!result.data || !result.data.content) {
      throw new Error('服务器返回数据格式错误')
    }
    // 处理完成
    await animateProgress(100, 600)
    progressStatus.value = 'success'
    setTimeout(() => {
      showUploadModal.value = false
      console.log('OCR处理完成:', result.data.content)
      // 成功返回后，先保存到数据库（非阻塞）
      try {
        const rawTextForSave =
          typeof result.data.content === 'string'
            ? result.data.content
            : JSON.stringify(result.data.content)
        // 随记录一并上传源文件
        saveOCRResult(file.raw?.name || 'unknown', rawTextForSave, file.raw)
      } catch (e) {
        console.warn('准备保存OCR结果时出错:', e)
      }
      // 尝试解析OCR返回的content为JSON格式
      try {
        const parsedContent = JSON.parse(result.data.content)
        if (parsedContent && typeof parsedContent === 'object') {
          // 是JSON格式，显示JSON编辑弹窗让用户编辑
          editJsonData.value = { ...parsedContent } // 深拷贝数据
          showJsonEditModal.value = true
        } else {
          // 不是JSON格式，显示普通文本编辑弹窗
          editContent.value = result.data.content
          showEditModal.value = true
        }
      } catch (error) {
        // 解析失败，尝试直接检查是否是对象
        if (result.data.content && typeof result.data.content === 'object') {
          // 直接是对象格式，显示JSON编辑弹窗
          editJsonData.value = { ...result.data.content }
          showJsonEditModal.value = true
        } else {
          // 按普通文本处理
          editContent.value = result.data.content
          showEditModal.value = true
        }
      }
    }, 1000)
  } catch (error) {
    console.error('OCR处理失败:', error)

    // 如果是用户取消，不显示错误
    if (error.name === 'AbortError') {
      console.log('用户取消了上传')
      return
    }

    progressStatus.value = 'exception'

    // 根据错误类型显示不同的错误信息
    let errorMessage = '文件处理失败'

    if (error.message.includes('Failed to fetch')) {
      errorMessage = '无法连接到服务器，请检查服务是否正常运行'
    } else if (error.message.includes('服务器错误')) {
      errorMessage = error.message
    } else {
      errorMessage = `处理失败: ${error.message}`
    }

    ElMessage.error(errorMessage)

    setTimeout(() => {
      showUploadModal.value = false
    }, 2000)
  } finally {
    // 清理控制器
    uploadController.value = null
  }
}

// 取消上传
const cancelUpload = () => {
  if (uploadController.value) {
    uploadController.value.abort()
    uploadController.value = null
  }
  showUploadModal.value = false
}

// 编辑弹窗相关方法
const confirmEdit = () => {
  if (editContent.value.trim()) {
    inputVal.value = editContent.value
    showEditModal.value = false
    nextTick(() => {
      submit()
    })
  }
}

const cancelEdit = () => {
  showEditModal.value = false
  editContent.value = ''
}

// JSON编辑弹窗相关方法
const confirmJsonEdit = () => {
  if (Object.keys(editJsonData.value).length > 0) {
    // 将JSON数据转换为字符串
    const jsonString = JSON.stringify(editJsonData.value)

    // 关闭弹窗并清理数据
    showJsonEditModal.value = false
    editJsonData.value = {}

    // 滚动到底部并提交给LLM（submit函数会自动添加到聊天列表）
    nextTick(() => {
      submit(jsonString) // 直接传入JSON字符串
    })
  }
}

const cancelJsonEdit = () => {
  showJsonEditModal.value = false
  editJsonData.value = {}
}

// 更新JSON键名
const updateJsonKey = (index, newKey, value) => {
  const entries = Object.entries(editJsonData.value)
  if (entries[index]) {
    const oldKey = entries[index][0]
    if (oldKey !== newKey) {
      // 删除旧键，添加新键
      delete editJsonData.value[oldKey]
      editJsonData.value[newKey] = value
    }
  }
}

// 更新JSON值
const updateJsonValue = (key, newValue) => {
  if (key in editJsonData.value) {
    editJsonData.value[key] = newValue
  }
}

// 删除JSON字段
const removeJsonField = (index) => {
  const entries = Object.entries(editJsonData.value)
  if (entries[index]) {
    const keyToRemove = entries[index][0]
    delete editJsonData.value[keyToRemove]
  }
}

// 添加JSON字段
const addJsonField = () => {
  const newKey = `新字段${Object.keys(editJsonData.value).length + 1}`
  editJsonData.value[newKey] = ''
}

// 批量文件JSON编辑相关方法
const isJsonContent = (content) => {
  if (!content || typeof content !== 'string') return false
  try {
    const parsed = JSON.parse(content)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
  } catch (error) {
    return false
  }
}

const editFileJson = (fileIndex) => {
  const fileItem = batchFiles.value[fileIndex]
  if (!fileItem || !fileItem.content) return

  try {
    const parsedContent = JSON.parse(fileItem.content)
    if (parsedContent && typeof parsedContent === 'object') {
      currentEditingFileIndex.value = fileIndex
      batchFileJsonData.value = { ...parsedContent }
      showBatchFileJsonEditModal.value = true
    }
  } catch (error) {
    ElMessage.error('文件内容不是有效的JSON格式')
  }
}

const confirmBatchFileJsonEdit = () => {
  if (
    currentEditingFileIndex.value >= 0 &&
    Object.keys(batchFileJsonData.value).length > 0
  ) {
    // 更新对应文件的内容
    const jsonString = JSON.stringify(batchFileJsonData.value, null, 2)
    batchFiles.value[currentEditingFileIndex.value].content = jsonString

    // 关闭弹窗并清理状态
    showBatchFileJsonEditModal.value = false
    currentEditingFileIndex.value = -1
    batchFileJsonData.value = {}

    ElMessage.success('文件内容已更新')
  }
}

const cancelBatchFileJsonEdit = () => {
  showBatchFileJsonEditModal.value = false
  currentEditingFileIndex.value = -1
  batchFileJsonData.value = {}
}

// 更新批量文件JSON键名
const updateBatchFileJsonKey = (index, newKey, value) => {
  const entries = Object.entries(batchFileJsonData.value)
  if (entries[index]) {
    const oldKey = entries[index][0]
    if (oldKey !== newKey) {
      // 删除旧键，添加新键
      delete batchFileJsonData.value[oldKey]
      batchFileJsonData.value[newKey] = value
    }
  }
}

// 更新批量文件JSON值
const updateBatchFileJsonValue = (key, newValue) => {
  if (key in batchFileJsonData.value) {
    batchFileJsonData.value[key] = newValue
  }
}

// 删除批量文件JSON字段
const removeBatchFileJsonField = (index) => {
  const entries = Object.entries(batchFileJsonData.value)
  if (entries[index]) {
    const keyToRemove = entries[index][0]
    delete batchFileJsonData.value[keyToRemove]
  }
}

// 添加批量文件JSON字段
const addBatchFileJsonField = () => {
  const newKey = `新字段${Object.keys(batchFileJsonData.value).length + 1}`
  batchFileJsonData.value[newKey] = ''
}

// 批量处理相关方法
const startBatchProcessing = async () => {
  batchProcessing.value = true
  currentProcessingIndex.value = 0
  batchProgressPercentage.value = 0
  batchProgressStatus.value = ''
  batchController.value = new AbortController()

  try {
    for (let i = 0; i < batchFiles.value.length; i++) {
      if (batchController.value.signal.aborted) {
        break
      }

      const fileItem = batchFiles.value[i]
      currentProcessingIndex.value = i

      // 更新进度
      batchProgressPercentage.value = Math.floor(
        (i / batchFiles.value.length) * 100
      )
      batchProgressText.value = `正在处理: ${fileItem.name}`

      // 标记当前文件为处理中
      fileItem.processing = true
      fileItem.error = false
      fileItem.errorMessage = ''

      try {
        await processSingleFile(fileItem)
        fileItem.completed = true
        fileItem.processing = false
      } catch (error) {
        console.error(`处理文件 ${fileItem.name} 失败:`, error)
        fileItem.error = true
        fileItem.processing = false
        fileItem.errorMessage = error.message || '处理失败'
      }
    }

    // 完成所有处理
    batchProgressPercentage.value = 100
    batchProgressStatus.value = 'success'
    batchProgressText.value = '所有文件处理完成'

    const successCount = batchFiles.value.filter((f) => f.completed).length
    const errorCount = batchFiles.value.filter((f) => f.error).length

    ElMessage.success(
      `批量处理完成！成功: ${successCount} 个，失败: ${errorCount} 个`
    )
  } catch (error) {
    console.error('批量处理出错:', error)
    batchProgressStatus.value = 'exception'
    batchProgressText.value = '批量处理中断'
    ElMessage.error('批量处理出错: ' + error.message)
  } finally {
    batchProcessing.value = false
    batchController.value = null
  }
}

const processSingleFile = async (fileItem) => {
  const formData = new FormData()
  formData.append('file', fileItem.file)

  const response = await fetch(OCR_CONFIG.endpoint, {
    method: 'POST',
    body: formData,
    signal: batchController.value.signal,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`服务器错误 ${response.status}: ${errorText}`)
  }

  const result = await response.json()
  console.log('处理结果:', result)

  if (result.error) {
    throw new Error(result.error)
  }

  if (!result.data || !result.data.content) {
    throw new Error('服务器返回数据格式错误')
  }

  // 处理返回的内容，如果是对象则转换为JSON字符串
  let processedContent = result.data.content
  if (typeof processedContent === 'object') {
    processedContent = JSON.stringify(processedContent, null, 2)
  } else if (typeof processedContent === 'string') {
    // 尝试解析字符串是否为JSON
    try {
      const parsed = JSON.parse(processedContent)
      if (parsed && typeof parsed === 'object') {
        processedContent = JSON.stringify(parsed, null, 2)
      }
    } catch (error) {
      // 不是JSON字符串，保持原样
    }
  }

  fileItem.content = processedContent
  // 每个批量文件处理完成后保存到数据库（非阻塞）
  try {
    await saveOCRResult(fileItem.name, processedContent, fileItem.file)
  } catch (e) {
    // 已在 saveOCRResult 内处理异常，这里静默
  }
}

const stopBatchProcessing = () => {
  if (batchController.value) {
    batchController.value.abort()
    batchController.value = null
  }
  batchProcessing.value = false
  batchProgressStatus.value = 'exception'
  batchProgressText.value = '用户取消处理'
  ElMessage.info('已停止批量处理')
}

const removeFile = (index) => {
  batchFiles.value.splice(index, 1)
  if (batchFiles.value.length === 0) {
    showBatchEditModal.value = false
  }
}

const confirmBatchEdit = () => {
  const validFiles = batchFiles.value.filter(
    (file) => file.completed && file.content && file.content.trim()
  )

  if (validFiles.length === 0) {
    ElMessage.warning('没有有效的文件内容可以提交')
    return
  }

  // 将所有有效文件内容合并，特别处理JSON格式
  const combinedContent = validFiles
    .map((file, index) => {
      let content = file.content

      // 检查内容是否为JSON格式
      try {
        const parsed = JSON.parse(content)
        if (parsed && typeof parsed === 'object') {
          // 是JSON格式，保持格式化的JSON字符串
          content = JSON.stringify(parsed, null, 2)
        }
      } catch (error) {
        // 不是JSON格式，保持原样
      }

      return `=== 文件 ${index + 1}: ${file.name} ===\n${content}`
    })
    .join('\n\n')

  inputVal.value = combinedContent
  showBatchEditModal.value = false

  // 清空批量文件列表
  batchFiles.value = []
  nextTick(() => {
    resetBatchUploader()
  })

  nextTick(() => {
    submit()
  })
}

const cancelBatchEdit = () => {
  if (batchProcessing.value) {
    stopBatchProcessing()
  }
  showBatchEditModal.value = false
  batchFiles.value = []
  nextTick(() => {
    resetBatchUploader()
  })
}

// 继续上传功能
const continueUpload = () => {
  // 创建一个隐藏的文件输入元素
  const fileInput = document.createElement('input')
  fileInput.type = 'file'
  fileInput.accept = '.pdf'
  fileInput.multiple = true
  fileInput.style.display = 'none'

  fileInput.onchange = (event) => {
    const files = Array.from(event.target.files)
    if (files.length === 0) return

    // 验证文件
    const invalidFiles = files.filter((f) => {
      if (!UPLOAD_CONFIG.validTypes.includes(f.type)) {
        return true
      }
      // Check size based on file type
      if (f.type === 'application/pdf') {
        return f.size > UPLOAD_CONFIG.pdfMaxSize
      } else {
        return f.size > UPLOAD_CONFIG.maxSize
      }
    })

    if (invalidFiles.length > 0) {
      ElMessage.error(
        `有 ${invalidFiles.length} 个文件不符合要求，请上传 PDF 格式且小于 13MB 的文件`
      )
      return
    }

    // 添加到现有的批量文件列表
    const newFiles = files.map((f) => ({
      name: f.name,
      file: f,
      content: '',
      processing: false,
      completed: false,
      error: false,
      errorMessage: '',
    }))

    batchFiles.value.push(...newFiles)

    ElMessage.success(`已添加 ${files.length} 个文件到批量处理列表`)

    // 清理临时元素
    document.body.removeChild(fileInput)
  }

  // 触发文件选择
  document.body.appendChild(fileInput)
  fileInput.click()
}

// 创建任务队列
const createTaskQueue = () => {
  const validFiles = batchFiles.value.filter(
    (file) => file.completed && file.content && file.content.trim()
  )

  if (validFiles.length === 0) {
    ElMessage.warning('没有有效的文件内容可以创建任务队列')
    return
  }

  // 创建任务队列
  taskQueue.value = validFiles.map((file, index) => ({
    fileName: file.name,
    content: file.content,
    completed: false,
    failed: false,
    processing: false,
    errorMessage: '',
    result: null,
    createTime: new Date().toLocaleString(),
  }))

  // 重置任务状态
  currentTaskIndex.value = 0
  taskProcessing.value = false

  // 显示任务浮窗
  showTaskModal.value = true
  taskMinimized.value = false

  // 关闭批量编辑弹窗
  showBatchEditModal.value = false
  batchFiles.value = []

  // 自动开始处理任务
  startTaskQueue()

  ElMessage.success(`已创建 ${validFiles.length} 个任务，开始自动处理`)
}

// 任务队列处理方法
const startTaskQueue = async () => {
  if (taskQueue.value.length === 0 || taskProcessing.value) {
    return
  }

  taskProcessing.value = true
  taskController.value = new AbortController()

  try {
    while (currentTaskIndex.value < taskQueue.value.length) {
      if (taskController.value.signal.aborted) {
        break
      }

      const currentTask = taskQueue.value[currentTaskIndex.value]

      // 跳过已完成或失败的任务
      if (currentTask.completed || currentTask.failed) {
        currentTaskIndex.value++
        continue
      }

      currentTask.processing = true

      try {
        // 提交当前任务到大模型
        await submitTaskToLLM(currentTask)

        currentTask.completed = true
        currentTask.processing = false

        // 短暂等待，确保界面更新
        await new Promise((resolve) => setTimeout(resolve, 1000))
      } catch (error) {
        console.error(`任务 ${currentTask.fileName} 处理失败:`, error)
        currentTask.failed = true
        currentTask.processing = false
        currentTask.errorMessage = error.message || '处理失败'
      }

      currentTaskIndex.value++
    }

    // 所有任务完成
    ElMessage.success('所有任务处理完成！')

    // 自动清理完成的任务队列和上传文件
    setTimeout(() => {
      if (completedTasks.value === totalTasks.value && totalTasks.value > 0) {
        // 清空任务队列
        taskQueue.value = []
        currentTaskIndex.value = 0

        // 清空批量上传的文件
        batchFiles.value = []
        showBatchEditModal.value = false

        // 关闭任务浮窗
        showTaskModal.value = false
        taskMinimized.value = false

        ElMessage.success('所有任务已完成，文件已清空')
      }
    }, 3000)
  } catch (error) {
    console.error('任务队列处理出错:', error)
    ElMessage.error('任务队列处理出错: ' + error.message)
  } finally {
    taskProcessing.value = false
    taskController.value = null
  }
}

// 等待上一个对话完成
const waitForPreviousConversation = async () => {
  // 检查是否有正在进行的对话
  if (messageList.value.length === 0) return

  const lastQuestion = messageList.value[messageList.value.length - 1]
  if (
    !lastQuestion ||
    !lastQuestion.answerList ||
    lastQuestion.answerList.length === 0
  )
    return

  const lastAnswer = lastQuestion.answerList[lastQuestion.answerList.length - 1]
  if (!lastAnswer || !lastAnswer.isStreaming) return

  // 等待对话完成
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      const currentLastQuestion =
        messageList.value[messageList.value.length - 1]
      if (
        !currentLastQuestion ||
        !currentLastQuestion.answerList ||
        currentLastQuestion.answerList.length === 0
      ) {
        clearInterval(checkInterval)
        resolve()
        return
      }

      const currentLastAnswer =
        currentLastQuestion.answerList[
          currentLastQuestion.answerList.length - 1
        ]
      if (!currentLastAnswer || !currentLastAnswer.isStreaming) {
        clearInterval(checkInterval)
        resolve()
      }
    }, 100) // 更频繁的检查，100ms

    // 设置超时，避免无限等待
    setTimeout(() => {
      clearInterval(checkInterval)
      resolve()
    }, 30000) // 30秒超时
  })
}

// 提交任务到大模型
const submitTaskToLLM = async (task) => {
  // 设置输入内容
  inputVal.value = task.content

  // 等待任何正在进行的对话完成
  await waitForPreviousConversation()

  // 调用submit方法并等待完成
  await submit()

  // 标记任务完成
  task.result = '处理完成'

  // 等待一小段时间确保界面更新
  await new Promise((resolve) => setTimeout(resolve, 500))
}

// 暂停所有任务
const pauseAllTasks = () => {
  if (taskController.value) {
    taskController.value.abort()
    taskController.value = null
  }
  taskProcessing.value = false
  ElMessage.info('任务队列已暂停')
}

// 恢复所有任务
const resumeAllTasks = () => {
  if (currentTaskIndex.value < taskQueue.value.length) {
    startTaskQueue()
    ElMessage.info('任务队列已恢复')
  }
}

// 停止并清空所有任务
const stopAllTasks = () => {
  if (taskController.value) {
    taskController.value.abort()
    taskController.value = null
  }
  taskProcessing.value = false
  taskQueue.value = []
  currentTaskIndex.value = 0
  showTaskModal.value = false
  taskMinimized.value = false

  // 清空批量上传的文件
  batchFiles.value = []
  showBatchEditModal.value = false

  ElMessage.info('任务队列已清空')
}

// 导出Excel：将每个有效的结构化识别数据作为一行
const exportExcel_no_diag_surg = () => {
  try {
    // 收集数据来源：优先从任务队列，其次从批量文件（已完成的）
    const rows = []

    const pushRowFromJson = (obj, sourceName) => {
      // 映射键到后端字段名
      const row = { 文件名: sourceName }
      Object.entries(obj || {}).forEach(([k, v]) => {
        const mapped = OCR_FIELD_MAP[k] || k
        row[mapped] = typeof v === 'string' ? v : JSON.stringify(v)
      })
      rows.push(row)
    }

    // 从任务队列里解析（taskQueue 每条的 content 可能是 JSON 字符串）
    taskQueue.value.forEach((t) => {
      if (t && t.content) {
        try {
          const parsed = JSON.parse(t.content)
          if (parsed && typeof parsed === 'object') {
            pushRowFromJson(parsed, t.fileName || 'unknown')
          } else {
            // 不是对象，作为原文放到 raw_text
            rows.push({
              文件名: t.fileName || 'unknown',
              raw_text: String(t.content),
            })
          }
        } catch {
          rows.push({
            文件名: t.fileName || 'unknown',
            raw_text: String(t.content),
          })
        }
      }
    })

    // 如果任务队列为空，则从批量文件里取
    if (rows.length === 0) {
      batchFiles.value
        .filter((f) => f.completed && f.content)
        .forEach((f) => {
          try {
            const parsed = JSON.parse(f.content)
            if (parsed && typeof parsed === 'object') {
              pushRowFromJson(parsed, f.name || 'unknown')
            } else {
              rows.push({
                文件名: f.name || 'unknown',
                raw_text: String(f.content),
              })
            }
          } catch {
            rows.push({
              文件名: f.name || 'unknown',
              raw_text: String(f.content),
            })
          }
        })
    }

    if (rows.length === 0) {
      ElMessage.warning('没有可导出的数据')
      return
    }

    // 生成工作簿
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'OCR数据')
    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    XLSX.writeFile(wb, `ocr_export_${ts}.xlsx`)
    ElMessage.success('Excel 已导出')
  } catch (e) {
    console.error('导出Excel失败:', e)
    ElMessage.error('导出失败')
  }
}

const exportCodingExcel = () => {
  openExportModal()
}

const exportFeedback = async () => {
  try {
    // 1. Call the backend API
    const res = await apiExportFeedback()
    const ress = res.data

    // 2. Validate response
    if (ress && ress.code === 200) {
      const dataToSave = ress.data;

      // 3. Convert data to JSON string (formatted with 2 spaces indentation)
      const jsonString = JSON.stringify(dataToSave, null, 2);

      // 4. Create a Blob object representing the data as a JSON file
      const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8' });

      // 5. Create a download link and trigger it
      // Strategy: Create an invisible <a> tag, set the URL, click it, then remove it.
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate a filename with the current timestamp
      const date = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
      link.setAttribute('download', `feedback_export_${date}.json`);
      
      document.body.appendChild(link);
      link.click();
      
      // 6. Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url); // Free up memory

      console.log('Export successful');
    } else {
      console.error('Export failed:', res.msg || 'Unknown error');
      // Optional: Show UI notification here (e.g., Message.error('Export failed'))
    }

  } catch (error) {
    console.error('Network or parsing error during export:', error);
    // Optional: Show UI notification here
  }
}

// 移除单个任务
const removeTask = (index) => {
  taskQueue.value.splice(index, 1)
  if (index < currentTaskIndex.value) {
    currentTaskIndex.value--
  }
  if (taskQueue.value.length === 0) {
    stopAllTasks()
  }
}

// 键盘事件处理
const handleKeydown = (event) => {
  if (event.ctrlKey && event.key === 'Enter') {
    // Ctrl+Enter 确认并提交
    event.preventDefault()
    confirmEdit()
  } else if (event.key === 'Escape') {
    // Esc 取消
    event.preventDefault()
    cancelEdit()
  }
}



// ========= 工具：从 item 中解析诊断/手术（沿用你现有解析器）=========
const extractDiagSurgPairs = (item) => {
  const diagAnswers = item.answers?.diagnosis?.answerList || []
  const surgAnswers = item.answers?.surgery?.answerList || []

  const diagLast = diagAnswers[diagAnswers.length - 1]
  const surgLast = surgAnswers[surgAnswers.length - 1]

  const diags = []
  const surgs = []

  if (diagLast?.content) {
    const d = parseStructuredMarkdown(diagLast.content, 'diagnosis')
    d.entries.forEach(({ name, code }) =>
      diags.push({ name: name || '', code: code || '' })
    )
  }
  if (surgLast?.content) {
    const s = parseStructuredMarkdown(surgLast.content, 'surgery')
    s.entries.forEach(({ name, code }) =>
      surgs.push({ name: name || '', code: code || '' })
    )
  }
  return { diags, surgs }
}

// ========= 工具：取住院号 =========
const getInpatientNoFromItem = (item) => {
  // 如果 question 是JSON，优先取 JSON.住院号
  try {
    if (typeof item.question === 'string') {
      const q = JSON.parse(item.question)
      if (q && q['住院号']) return String(q['住院号'])
    } else if (item.question && typeof item.question === 'object') {
      if (item.question['住院号']) return String(item.question['住院号'])
    }
  } catch (_) {}
  return '' // 未提供
}

// ========= 工具：把 item 构造成导出的一行（动态扩展 诊断/手术N）=========
const buildRowFromItem = (item, idx, maxDiag, maxSurg, all_feedback) => {
  // question 转对象（基础字段）
  let q = {}
  if (typeof item.question === 'string') {
    try {
      q = JSON.parse(item.question) || {}
    } catch {
      q = {}
    }
  } else if (item.question && typeof item.question === 'object') {
    q = { ...item.question }
  }

  const { diags, surgs } = extractDiagSurgPairs(item)

  // 基础列
  const row = {
    序号: idx + 1,
    编码用户: item.createdBy || '',
    病案标识: q['病案标识'] || '',
    住院号: q['住院号'] || '',
    主诉: q['主诉'] || '',
    现病史: q['现病史'] || '',
    既往史: q['既往史'] || '',
    个人史: q['个人史'] || '',
    婚姻史: q['婚姻史'] || '',
    家族史: q['家族史'] || '',
    入院情况: q['入院情况'] || '',
    入院诊断: q['入院诊断'] || '',
    诊疗经过: q['诊疗经过'] || '',
    病程记录: q['病程记录'] || '',
    手术名称: q['手术名称'] || '',
    手术经过: q['手术经过'] || '',
    术中诊断: q['术中诊断'] || '',
    影像学意见: q['影像学意见'] || '',
    超声提示: q['超声提示'] || '',
    超声印象: q['超声印象'] || '',
    出院诊断: q['出院诊断'] || '',
  }
  
  // 得到每个消息的message_id
  const message_id = item.message_id
  const commentsSurgery = Array(maxSurg).fill('')
  const commentsDisease = Array(maxDiag).fill('')

  all_feedback.forEach((feedback) => {
    if (feedback.message_id === parseInt(message_id)) {
      if (feedback.category === 0)
        commentsDisease[feedback.row_id] = feedback.type + ":" + feedback.remark
      else if (feedback.category === 1)
        commentsSurgery[feedback.row_id] = feedback.type + ":" + feedback.remark
    }
  })


  // 诊断可变长
  for (let i = 0; i < maxDiag; i++) {
    row[`${DIAG_NAME_PREFIX}${i + 1}`] = diags[i]?.name || ''
    row[`${DIAG_CODE_PREFIX}${i + 1}`] = diags[i]?.code || ''
    row[`${DIAG_CODE_FEED}${i + 1}`] = commentsDisease[i] || ''
  }
  // 手术可变长
  for (let i = 0; i < maxSurg; i++) {
    row[`${SURG_NAME_PREFIX}${i + 1}`] = surgs[i]?.name || ''
    row[`${SURG_CODE_PREFIX}${i + 1}`] = surgs[i]?.code || ''
    row[`${SURG_CODE_FEED}${i + 1}`] = commentsSurgery[i] || ''
  }

  // 只保留被选中的基础列 + 全部动态列（动态列不受“字段勾选”限制，避免漏掉可变长）
  const selected = {}
  const hasCodeFeedback = Array.isArray(selectedExportFields.value) ? selectedExportFields.value.includes('编码反馈') : false  

  for (const k of selectedExportFields.value) selected[k] = row[k] ?? ''
  // 然后把动态列拼上
  for (let i = 0; i < maxDiag; i++) {
    const nameKey = `${DIAG_NAME_PREFIX}${i + 1}`
    const codeKey = `${DIAG_CODE_PREFIX}${i + 1}`
    const feedKey = `${DIAG_CODE_FEED}${i + 1}`

    selected[nameKey] = row[nameKey]
    selected[codeKey] = row[codeKey]
    if (hasCodeFeedback) {
      selected[feedKey] = row[feedKey]
    }
  }
  for (let i = 0; i < maxSurg; i++) {
    const nameKey = `${SURG_NAME_PREFIX}${i + 1}`
    const codeKey = `${SURG_CODE_PREFIX}${i + 1}`
    const feedKey = `${SURG_CODE_FEED}${i + 1}`

    selected[nameKey] = row[nameKey]
    selected[codeKey] = row[codeKey]
    if (hasCodeFeedback) {
      selected[feedKey] = row[feedKey]
    }
  }

  return selected
}

const filterItemsForExport = async () => {
  const { dateRange, diagSurgKeyword, diagSurgType, user, inpatientNo, exportAllConversations, exportAllUsers } = exportFilters.value

  const All_messages = [] // 全局 messageList

  if (exportAllUsers){
    // 导出全部普通用户的全部对话记录的全部消息
    const res = await apiGetUserChatMessagesAllAll({ group: false });
    if (res && res.data && res.data.data) {
      const all_messages = res.data.data

      all_messages.forEach(msg => { 
        All_messages.push( msg.message ) 
        All_messages[All_messages.length -1 ].message_id = msg.id // 保存 message_id 供后续反馈匹配
      })
    }
  }
  else if (exportAllConversations) {
    // 导出当前用户的全部对话记录的全部消息
    const res = await apiGetUserChatMessagesAll({ group: false });
    
    if (res && res.data && res.data.data) {
      const all_messages = res.data.data

      all_messages.forEach(msg => { 
        All_messages.push( msg.message ) 
        All_messages[All_messages.length -1 ].message_id = msg.id // 保存 message_id 供后续反馈匹配
      })
    }
  }else{
    // 导出当前用户的当前对话记录的全部消息
    messageList.value.forEach(msg => { 
      All_messages.push( msg ) 
      All_messages[All_messages.length -1 ].message_id = msg.message_id // 保存 message_id 供后续反馈匹配
    })
  }
  console.log("All_messages length:", All_messages.length)
  

  // dateRange 现在是 [Date, Date] 或 null
  const startMs =
    Array.isArray(dateRange) && dateRange[0] instanceof Date
      ? dateRange[0].getTime()
      : null
  const endMs =
    Array.isArray(dateRange) && dateRange[1] instanceof Date
      ? dateRange[1].getTime()
      : null

  const kw = (diagSurgKeyword || '').trim()
  const userKw = (user || '').trim()
  const ipNo = (inpatientNo || '').trim()

  return All_messages.filter((item) => {
    // 时间
    if (startMs != null && endMs != null && item.createdAt) {
      const t = new Date(item.createdAt).getTime()
      if (Number.isFinite(t)) {
        if (t < startMs || t > endMs) return false
      }
    }

    // 用户
    if (userKw) {
      const who = item.createdBy || ''
      if (!String(who).includes(userKw)) return false
    }

    // 住院号（单个精确）
    if (ipNo) {
      const got = getInpatientNoFromItem(item)
      if (String(got) !== ipNo) return false
    }

    // 诊断/手术关键字（编码或名称）
    if (kw) {
      const { diags, surgs } = extractDiagSurgPairs(item)
      const hitDiag = diags.some(
        (d) => d.name?.includes(kw) || d.code?.includes(kw)
      )
      const hitSurg = surgs.some(
        (s) => s.name?.includes(kw) || s.code?.includes(kw)
      )
      if (diagSurgType === 'diag' && !hitDiag) return false
      if (diagSurgType === 'surg' && !hitSurg) return false
      if (diagSurgType === 'all' && !(hitDiag || hitSurg)) return false
    }

    return true
  })
}

// ========= 预览 / 导出 =========
const previewRows = ref([])
const previewHeaders = ref([])

const loadingPreview = ref(false)
const buildPreview = async () => {
  try {
    loadingPreview.value = true
    const items = await filterItemsForExport() // 等待完成
    debugger

    let res = []
    if (exportFilters.value.exportAllUsers){
      res = await apiGetAllChatMessageFeedbackAllAll()
    }else{
      res = await apiGetAllChatMessageFeedbackAll()
    }
    const all_feedback = res.data.data


    // 统计本次最大诊断/手术长度
  // 统计本次最大诊断/手术长度
  let maxDiag = 0,
    maxSurg = 0
  for (const it of items) {
    const { diags, surgs } = extractDiagSurgPairs(it)
    maxDiag = Math.max(maxDiag, diags.length)
    maxSurg = Math.max(maxSurg, surgs.length)
  }
  // ★ 如果你想“至少导出 诊断N 到 6、手术N 到 5”，可解开下面两行的最小值：
  // maxDiag = Math.max(maxDiag, 6)
  // maxSurg = Math.max(maxSurg, 5)

  // 组装行
  const rows = items.map((it, i) => buildRowFromItem(it, i, maxDiag, maxSurg, all_feedback))
  previewRows.value = rows

    const hasCodeFeedback = Array.isArray(selectedExportFields.value) ? selectedExportFields.value.includes('编码反馈') : false

    // 生成表头：选中基础列 + 动态列 (排除编码反馈)
    const fields = Array.isArray(selectedExportFields.value) ? selectedExportFields.value : []
    const headers = fields.filter(f => f !== '编码反馈')

    for (let i = 0; i < maxDiag; i++) {
      headers.push(`${DIAG_NAME_PREFIX}${i + 1}`, `${DIAG_CODE_PREFIX}${i + 1}`)

      const feedKey = `${DIAG_CODE_FEED}${i + 1}` // 选中了最后一个动态列，才加这个反馈列
      if (hasCodeFeedback) {
          headers.push(`${feedKey}`)
      }
    }
    for (let i = 0; i < maxSurg; i++) {
      headers.push(`${SURG_NAME_PREFIX}${i + 1}`, `${SURG_CODE_PREFIX}${i + 1}`)

      const feedKey = `${SURG_CODE_FEED}${i + 1}` // 选中了最后一个动态列，才加这个反馈列
      if (hasCodeFeedback) {
          headers.push(`${feedKey}`)
      }
    }
    previewHeaders.value = headers
  } catch (err) {
      console.error('导出过滤失败', err)
      // 可显示错误提示：this.$message.error(...) 或其他逻辑
    } finally {
      loadingPreview.value = false
    }
}

const clearPreview = () => {
  previewRows.value = []
  previewHeaders.value = []
}

const exportExcelWithFilters = () => {
  if (!previewRows.value.length) {
    ElMessage.warning('请先点击“预览”生成数据')
    return
  }
  const ws = XLSX.utils.json_to_sheet(previewRows.value, {
    header: previewHeaders.value,
  })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '病案编码')

  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  const fname = `coding_export_filtered_${ts}.xlsx`
  XLSX.writeFile(wb, fname)
  ElMessage.success('导出成功')
  showExportModal.value = false
}
</script>
<style lang="scss" scoped>

/* 用户问题区域的包装器 */
.text-question-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end; /* 靠右对齐，因为是用户问题 */
  max-width: 100%;
}

/* 文本区域样式 */
.ques-text {
  /* 保持原有的样式，例如背景色、圆角等 */
  display: inline-block;
  white-space: pre-wrap; /* 保留换行 */
  transition: all 0.3s ease; /* 添加平滑过渡 */
}

/* 折叠状态的特定样式 */
.ques-text.collapsed-text {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3; /* 限制显示3行，你可以根据需要改为 4 或 5 */
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 4.5em; /* 这里的高度大致等于 line-height * line-clamp */
}

/* 展开/收起 按钮样式 */
.collapse-toggle-btn {
  font-size: 12px;
  color: #3087cf;
  cursor: pointer;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  user-select: none;
}

.collapse-toggle-btn:hover {
  color: #1e6bb8;
}

.collapse-toggle-btn .el-icon {
  transition: transform 0.3s;
}

.collapse-toggle-btn .el-icon.is-active {
  transform: rotate(180deg);
}

.chat-input {
  display: flex;
  justify-content: center;
  flex: 0 0 auto;

  //   position: absolute;
  //   bottom: 20px;
  //   left: 50%;
  .ci-content {
    border: 1px solid rgba(65, 77, 96, 0.3);
    box-sizing: border-box;
    height: auto;
    width: 1140px; /* 从800px增加到1140px，比聊天窗口稍窄一些 */
    max-width: 90%; /* 添加最大宽度限制，保持响应式 */
    border-radius: 15px;
    position: relative;
    box-sizing: border-box;
    padding: 4px 2px 8px;
    background: #ffffff;
    border-radius: 6px;
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
  margin-bottom: 8px;
  position: relative;

  &::after {
    position: absolute;
    bottom: 0;
    content: '';
    display: block;
    right: 0;
    width: 10px;
    height: 10px;
    background: #ffffff;
    z-index: 2;
  }

  textarea {
    resize: none;
  }
}

.fs-box {
  cursor: pointer;
  background-color: #2468f2;
  color: #ffffff;
  height: 28px;
  width: 55px;
  text-align: center;
  line-height: 32px;
  font-size: 18px;
  border-radius: 14px;
}

.input-text {
  --el-input-border-color: transparent;
  --el-input-focus-border-color: transparent;
  --el-border-color-hover: transparent;
  color: #333;
}

.bottom-box {
  justify-content: space-between;
  padding-right: 10px;
}

.btn-box {
  display: flex;
  align-items: center;

  i {
    margin-right: 4px;
    margin-top: 2px;
  }
}

.btn {
  cursor: pointer;
  padding-left: 8px;
  padding-right: 8px;
  height: 24px;
  flex-shrink: 0;
  margin-left: 10px;
  transition: 0.2s;
  border: 1px solid rgba(0, 0, 0, 0.27);
  line-height: 24px;
  color: #333;
  border-radius: 6px;
  font-size: 12px;
  display: flex;
  align-items: center;

  &.active {
    background: #2468f2;
    border-color: transparent;
    color: #fff;
  }

  &.btn3.active {
    background: #67c23a;
    border-color: transparent;
    color: #fff;
  }
}

// .ques-box {
//   flex: 1 1 0;
//   width: 1200px;  /* 从860px增加到1200px */
//   max-width: 95%;  /* 添加最大宽度限制，保持响应式 */
//   padding: 20px 30px 0;
//   //   position: absolute;
//   //   bottom: 20px;
//   //   left: 50%;
//   box-sizing: border-box;
//   display: flex;
//   flex-direction: column;
//   max-height: calc(100% - 100px);
//   overflow-y: auto;

// }

.page-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  width: 100%;
  overflow: hidden; /* 防止页面级滚动 */
}

.chat-scroll-wrapper {
  flex: 1; /* 占据剩余高度 */
  width: 100%;
  min-height: 0; /* 关键：防止 flex 子项溢出 */
  position: relative;
}

.ques-content {
  width: 1200px; /* 保持原有的宽度设计 */
  max-width: 95%;
  margin: 0 auto; /* 居中显示 */
  padding: 20px 30px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.ques-ddd {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.ques-item {
  position: relative;
  border-radius: 12px 2px 12px 12px;
  background: #fff;
  margin-bottom: 12px;
  // width: fit-content;
  padding: 14px;
  line-height: 21px;
  font-size: 14px;
  max-width: 1000px; /* 从700px增加到1000px，让内容有更多空间 */

  .avatar {
    position: absolute;
    width: 40px;
    height: 40px;
    right: -25px;
    top: -20px;
    border-radius: 50%;
  }

  &.right {
    // text-align: right;
    align-self: flex-end;
    // background-color: #2468f2;
    // color: #ffffff;
  }

  &.left {
    border-radius: 2px 12px 12px 12px;

    .avatar {
      left: -25px;
    }

    .ques-text {
      text-align: left;
      font-size: 14px;
      color: #333;
    }
  }
}

/* JSON响应样式 */
.json-response-container {
  .json-response-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;

    .json-indicator {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
  }

  .json-table-display {
    .el-table {
      border-radius: 8px;
      overflow: hidden;

      .el-table__cell {
        padding: 12px 8px;
      }

      th.el-table__cell {
        background-color: #f8f9fa;
        color: #495057;
        font-weight: 600;
      }

      .json-field-content {
        line-height: 1.6;
        word-break: break-word;
        max-height: 200px;
        overflow-y: auto;
      }
    }
  }

  .json-raw-display {
    .el-collapse-item__header {
      background-color: #f8f9fa;
      border-radius: 4px;
      padding: 8px 12px;
      font-size: 13px;
      color: #6c757d;
    }

    .json-raw-content {
      background-color: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      padding: 12px;
      font-size: 12px;
      color: #495057;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}

/* Markdown表格响应样式 */
.markdown-table-container {
  .markdown-table-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;

    .markdown-indicator {
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
      color: white;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
  }

  .markdown-table-display {
    width: 100%;
    max-width: 100%;
    overflow-x: auto;

    .el-table {
      border-radius: 8px;
      overflow: hidden;
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100%;
      table-layout: auto !important; // 自动列宽
      // min-width: 1000px;  /* 增加最小宽度让表格更长 */

      .el-table__cell {
        padding: 12px 16px; /* 增加内边距 */
        min-width: 150px; /* 增加每列最小宽度 */
      }

      th.el-table__cell {
        background-color: #f8f9fa;
        color: #495057;
        font-weight: 600;
        min-width: 150px; /* 表头也增加最小宽度 */
      }

      .markdown-cell-content {
        line-height: 1.6;
        word-break: break-word;
        max-height: 200px;
        overflow-y: auto;
        min-width: 120px; /* 单元格内容最小宽度 */

        strong {
          font-weight: 700;
          color: #dc3545;
        }

        em {
          font-style: italic;
          color: #6f42c1;
        }

        code {
          background-color: #f8f9fa;
          padding: 2px 4px;
          border-radius: 3px;
          font-family: 'Monaco', 'Consolas', monospace;
          font-size: 0.9em;
          color: #e83e8c;
        }
      }
    }
  }

  .markdown-raw-display {
    .el-collapse-item__header {
      background-color: #f8f9fa;
      border-radius: 4px;
      padding: 8px 12px;
      font-size: 13px;
      color: #6c757d;
    }

    .markdown-raw-content {
      background-color: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      padding: 12px;
      font-size: 12px;
      color: #495057;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}

/* JSON问题样式 */
.json-question-container {
  width: 100%;

  .json-question-header {
    margin-bottom: 10px;

    .json-indicator {
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
      color: white;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
  }

  .json-question-display {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;

    .json-question-item {
      display: flex;
      margin-bottom: 8px;
      text-align: left;

      &:last-child {
        margin-bottom: 0;
      }

      .json-key {
        font-weight: 600;
        color: #495057;
        min-width: 100px;
        margin-right: 10px;
        flex-shrink: 0;
      }

      .json-value {
        color: #333;
        word-break: break-word;
        line-height: 1.5;
      }
    }
  }
}

.sk-content {
  border-left: 1px solid #eaeaea;
  padding-left: 12px;
  font-weight: 400;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  text-align: justify;
  margin-bottom: 10px;
  white-space: wrap;
}

.name-str {
  font-weight: 600;
  font-size: 16px;
}

.ml10 {
  margin-left: 10px;
}

.mr10 {
  margin-right: 10px;
}

.final-result-table {
  width: 100%;
  margin-top: 15px;
  font-size: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.final-result-table table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.final-result-table th,
.final-result-table td {
  padding: 12px 15px;
  border-right: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  text-align: left;
}

.final-result-table th {
  font-weight: 600;
}

.final-result-table .header-row th {
  background-color: #2468f2;
  color: white;
  text-align: center;
  font-size: 16px;
  font-weight: 500;
  border-right: 1px solid #1a5cd4;
}

.final-result-table .sub-header-row td {
  text-align: center;
  font-weight: 600;
  padding: 10px 15px;
}

.final-result-table .diagnosis-header {
  background-color: #e6f0ff;
  color: #2468f2;
  border-right: 1px solid #d0dffc;
}

.final-result-table .surgery-header {
  background-color: #fff2e6;
  color: #ff7b00;
  border-right: 1px solid #ffe0cc;
}

.final-result-table .column-header th {
  background-color: #f8f8f8;
  color: #555;
  border-bottom: 2px solid #e0e0e0;
}

.final-result-table .main-row {
  background-color: #f0f7ff;
  font-weight: 500;
}

.final-result-table .main-row td {
  border-bottom: 2px solid #d0e3ff;
}

.final-result-table .type-cell {
  font-weight: 600;
  color: #333;
  background-color: #f5f5f5;
}

.final-result-table .data-row:hover {
  background-color: #f5f5f5 !important;
}

.final-result-table .even-row {
  background-color: #fff;
}

.final-result-table .odd-row {
  background-color: #fafafa;
}

.final-result-table tr td:last-child,
.final-result-table tr th:last-child {
  border-right: none;
}

.final-result-table tr:last-child td {
  border-bottom: none;
}

/* 上传处理样式 */
.upload-process {
  text-align: center;
  padding: 20px;

  .process-steps {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;

    .step {
      flex: 1;
      position: relative;
      text-align: center;

      &::after {
        content: '';
        position: absolute;
        top: 15px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: #e0e0e0;
        z-index: 1;
        transition: background-color 1s ease;
      }

      &:last-child::after {
        display: none;
      }

      &.active {
        .step-icon {
          background: #2468f2;
          color: white;
          border-color: #2468f2;
        }

        .step-text {
          color: #2468f2;
          font-weight: 500;
        }

        &::after {
          background: #2468f2;
        }
      }
    }

    .step-icon {
      width: 30px;
      height: 30px;
      line-height: 30px;
      border-radius: 50%;
      border: 2px solid #e0e0e0;
      display: inline-block;
      background: white;
      position: relative;
      z-index: 2;
      transition: all 1s ease;
    }

    .step-text {
      margin-top: 8px;
      font-size: 12px;
      color: #999;
      transition: all 1s ease;
    }
  }

  .image-preview {
    height: 220px;
    margin: 20px 0;
    position: relative;

    img {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
    }
  }

  .process-text {
    margin: 15px 0;
    font-size: 16px;
    color: #333;
  }

  .upload-actions {
    margin-top: 20px;
    text-align: center;

    .el-button {
      .el-icon {
        margin-right: 6px;
      }
    }
  }
}

.feedback-dialog {
  display: flex;
  flex-direction: column;
  gap: 10px;
}


.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}
.welcome-container {
  // display: flex;
  // flex-direction: column;
  // align-items: center;
  // justify-content: center;
  // height: calc(100vh - 200px);
  // text-align: center;
  // margin-bottom: -100px; /* Adjust this to position properly */

  /* 可以保持绝对定位或 flex 居中，根据需求调整 */
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  pointer-events: none; /* 防止遮挡点击 */
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
}

.thinking-content {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border-left: 3px solid #2468f2;
}

.thinking-header {
  font-weight: bold;
  color: #2468f2;
  margin-bottom: 5px;
  font-size: 14px;
}

.thinking-text {
  color: #666;
  font-size: 13px;
  white-space: pre-wrap;
  line-height: 1.5;
}

// .page-box {
//   height: 100%;
//   display: flex;
//   flex-direction: column;
// }

// .ques-box {
//   flex: 1;
//   overflow-y: auto;
//   padding: 20px;
// }

// .chat-input {
//   padding: 15px;
//   background-color: #f5f7fa;
//   border-top: 1px solid #e4e7ed;
// }

// .ques-box {
//   overflow-y: auto;
//   height: calc(100vh - 200px); /* 根据实际布局调整 */
//   padding-bottom: 20px;
// }

/* 编辑弹窗样式 */
.edit-content-container {
  padding: 20px 0;

  .edit-description {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    color: #606266;
    font-size: 14px;

    .el-icon {
      margin-right: 8px;
      color: #409eff;
    }
  }

  .edit-textarea {
    margin-bottom: 16px;

    .el-textarea__inner {
      border-radius: 8px;
      border: 2px solid #e4e7ed;
      transition: border-color 0.2s;

      &:focus {
        border-color: #409eff;
      }
    }
  }

  .edit-tips {
    display: flex;
    align-items: flex-start;
    flex-direction: column;
    padding: 12px 16px;
    background-color: #f0f9ff;
    border: 1px solid #b3d8ff;
    border-radius: 6px;
    color: #0066cc;
    font-size: 13px;
    line-height: 1.5;

    > span {
      display: flex;
      align-items: center;
      margin-bottom: 8px;

      .el-icon {
        margin-right: 8px;
        flex-shrink: 0;
      }
    }

    .keyboard-shortcuts {
      font-size: 12px;
      color: #666;
      font-style: italic;

      span {
        background-color: rgba(255, 255, 255, 0.6);
        padding: 2px 6px;
        border-radius: 4px;
      }
    }
  }
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .el-button {
    min-width: 100px;

    .el-icon {
      margin-right: 6px;
    }
  }
}

/* 批量编辑弹窗样式 */
.batch-edit-container {
  .batch-edit-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px 16px;
    background-color: #f0f9ff;
    border: 1px solid #b3d8ff;
    border-radius: 6px;
    color: #0066cc;
    font-size: 14px;

    .el-icon {
      margin-right: 8px;
      font-size: 16px;
    }
  }

  .batch-files-list {
    max-height: 400px;
    overflow-y: auto;
    margin-bottom: 20px;

    .batch-file-item {
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 16px;
      background-color: #fff;
      transition: all 0.2s;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
      }

      &.processing {
        border-color: #e6a23c;
        background-color: #fdf6ec;
      }

      &.completed {
        border-color: #67c23a;
        background-color: #f0f9ff;
      }

      &.error {
        border-color: #f56c6c;
        background-color: #fef0f0;
      }

      .file-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .file-info {
          display: flex;
          align-items: center;
          gap: 8px;

          .file-name {
            font-weight: 500;
            font-size: 14px;
            color: #333;
          }

          .el-icon {
            color: #666;
          }
        }
      }

      .file-content {
        .el-textarea {
          .el-textarea__inner {
            border-radius: 6px;
            border: 1px solid #e4e7ed;

            &:focus {
              border-color: #409eff;
            }
          }
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 8px;
          color: #f56c6c;
          font-size: 12px;

          .el-icon {
            font-size: 14px;
          }
        }
      }
    }
  }

  .batch-progress {
    margin-bottom: 20px;
    padding: 16px;
    background-color: #f8f9fa;
    border-radius: 6px;

    .progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 13px;
      color: #666;

      .progress-text {
        font-weight: 500;
        color: #333;
      }
    }
  }

  .batch-tips {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background-color: #fff7e6;
    border: 1px solid #ffd666;
    border-radius: 6px;
    color: #d46b08;
    font-size: 13px;

    .el-icon {
      margin-right: 8px;
      flex-shrink: 0;
    }
  }
}

.batch-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .el-button {
    min-width: 120px;

    .el-icon {
      margin-right: 6px;
    }
  }
}

/* 任务浮窗样式 */
.task-minimized {
  .el-dialog__header {
    display: none;
  }

  .el-dialog__body {
    padding: 12px;
  }

  .el-dialog__footer {
    display: none;
  }
}

.task-floating {
  position: fixed !important;
  bottom: 20px !important;
  right: 20px !important;
  top: auto !important;
  z-index: 2000 !important;
  // pointer-events: none !important;

  .el-dialog {
    margin: 0 !important;
    position: fixed !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    border-radius: 8px !important;
    // pointer-events: auto !important;
  }

  .el-overlay {
    display: none !important;
  }
}

.task-minimized-content {
  .task-mini-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .task-mini-info {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: #333;

      .el-icon {
        font-size: 16px;

        &.spinning {
          animation: spin 1s linear infinite;
        }
      }
    }

    .task-mini-actions {
      display: flex;
      gap: 4px;
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.task-full-content {
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px 16px;
    background-color: #f0f9ff;
    border: 1px solid #b3d8ff;
    border-radius: 6px;

    .task-info {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #0066cc;
      font-size: 14px;

      .el-icon {
        font-size: 16px;
      }
    }

    .task-actions {
      display: flex;
      gap: 8px;
    }
  }

  .task-progress-info {
    margin-bottom: 20px;

    .progress-text {
      margin-bottom: 8px;
      font-size: 14px;
      color: #666;
      text-align: center;
    }
  }

  .task-list {
    max-height: 400px;
    overflow-y: auto;

    .task-item {
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 16px;
      background-color: #fff;
      transition: all 0.2s;

      &:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      &.current {
        border-color: #e6a23c;
        background-color: #fdf6ec;
      }

      &.completed {
        border-color: #67c23a;
        background-color: #f0f9ff;
      }

      &.failed {
        border-color: #f56c6c;
        background-color: #fef0f0;
      }

      &.waiting {
        border-color: #d3d4d6;
        background-color: #f8f9fa;
      }

      .task-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .task-item-info {
          display: flex;
          align-items: center;
          gap: 8px;

          .task-name {
            font-weight: 500;
            font-size: 14px;
            color: #333;
          }

          .el-icon {
            color: #666;
          }
        }
      }

      .task-item-content {
        .task-content-preview {
          background-color: #f8f9fa;
          padding: 8px 12px;
          border-radius: 4px;
          font-size: 12px;
          color: #666;
          line-height: 1.4;
          margin-bottom: 8px;
        }

        .task-error {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #f56c6c;
          font-size: 12px;

          .el-icon {
            font-size: 14px;
          }
        }

        .task-result {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #67c23a;
          font-size: 12px;

          .el-icon {
            font-size: 14px;
          }
        }
      }
    }
  }
}

.task-footer {
  display: flex;
  justify-content: center;

  .el-button {
    min-width: 120px;

    .el-icon {
      margin-right: 6px;
    }
  }
}

/* 悬浮按钮样式 */
.floating-task-button {
  position: fixed;
  bottom: 20px;
  right: 100px;
  z-index: 1500;

  .task-badge {
    .el-button {
      width: 60px;
      height: 60px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

      .el-icon {
        font-size: 24px;
      }

      &:hover {
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
        transition: all 0.3s;
      }
    }
  }
}

/* JSON编辑弹窗样式 */
.json-edit-container {
  .json-edit-description {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    color: #495057;
    font-size: 14px;
  }

  .json-edit-table {
    .el-table {
      border-radius: 8px;
      overflow: hidden;
    }

    .el-table__cell {
      padding: 8px;
    }

    .el-input__wrapper {
      border-radius: 4px;
    }

    .add-field-section {
      text-align: center;
      padding: 15px;
      background-color: #f8f9fa;
      border-radius: 8px;
    }
  }

  .json-edit-tips {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 15px;
    padding: 10px;
    background-color: #e3f2fd;
    border-radius: 8px;
    color: #1565c0;
    font-size: 13px;
  }
}

.json-edit-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.ai-responses-row {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin: 28px 0 16px 0;
  background: #f8fafb;
  border-radius: 18px;
  box-shadow: 0 2px 16px rgba(56, 100, 168, 0.07);
  padding: 28px 16px 24px;
  min-height: 240px; // 保证内容不空时有高度
  align-items: flex-start;
}

.ai-diagnosis,
.ai-surgery {
  min-width: 0;
  flex: none !important;
  width: 100%;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(80, 100, 150, 0.055);
  padding: 20px 18px 10px 18px;
  min-height: 180px;
  margin-right: 0;
  border: 1px solid #eef2f5;
  // 让卡片与右侧间隔
  &:not(:last-child) {
    // margin-right: 24px;
    // border-right: 2px solid #e7ebef;
  }

  > div:first-child {
    font-weight: bold;
    color: #3c6;
    font-size: 16px;
    margin-bottom: 16px;
    letter-spacing: 2px;
  }

  .ques-item {
    background: #fafdff;
    box-shadow: 0 1px 2px rgba(130, 180, 220, 0.045);
    border-radius: 10px;
    margin-bottom: 12px;
    padding: 14px 20px 14px 64px; // 空出头像位
    position: relative;
    min-height: 56px;
    border: 1px solid #e8edf2;
    transition: box-shadow 0.15s;
    &:hover {
      box-shadow: 0 4px 16px rgba(40, 150, 240, 0.07);
    }
    .avatar {
      position: absolute;
      left: 14px;
      top: 14px;
      width: 36px;
      height: 36px;
      box-shadow: 0 0 0 2px #fff, 0 1px 6px rgba(140, 170, 210, 0.1);
      border-radius: 50%;
      border: 2px solid #fff;
      z-index: 1;
      background: #f5f6fa;
    }
  }
}

// 针对 .ai-surgery 做色调微调
.ai-surgery {
  > div:first-child {
    color: #ea791a;
  }
}

@media (max-width: 900px) {
  .ai-responses-row {
    flex-direction: column;
    gap: 20px;
    padding: 14px 6px;
  }
  .ai-diagnosis,
  .ai-surgery {
    min-width: 200px;
    padding: 12px 8px 10px 8px;
    border-radius: 10px;
    margin-right: 0;
    &:not(:last-child) {
      margin-right: 0;
      border-right: none;
      margin-bottom: 12px;
    }
  }
}

.markdown-table-display .el-table__cell,
.markdown-table-display th.el-table__cell {
  white-space: normal;
  word-break: break-word;
  min-width: 60px;
  max-width: 400px; // 单列最多多宽
}

.export-panel {
  padding: 6px 2px;
}
.export-filter {
  margin-bottom: 12px;
}
.field-chooser {
  max-width: 860px;
}
.field-ops {
  margin-bottom: 8px;
  display: flex;
  gap: 8px;
}
.fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 6px 12px;
  max-height: 180px;
  overflow-y: auto;
  padding: 8px;
  border: 1px dashed #e5e7eb;
  border-radius: 8px;
  background: #fafbfc;
}
.preview-wrap {
  margin-top: 10px;
}
// 添加新的样式
.text-content.collapsed {
  .avatar,
  .sk-content,
  .thinking-content,
  .ques-text:not(.name-str) {
    display: none;
  }

  .name-str {
    display: inline;
    font-weight: 600;
    color: #666;
  }
}

// 确保表格内容始终显示
.json-response-container,
.markdown-table-container {
  display: block !important;
}
// 文本内容 - 可收起，使用对话框样式
.text-content {
  transition: all 0.3s ease;
  margin-bottom: 16px; // 添加底部间距，与表格分开

  &.collapsed {
    .ques-item {
      display: none;
    }

    // 收起时显示一个简短的提示
    &::before {
      content: '内容已收起，点击标题展开查看详细内容';
      display: block;
      text-align: center;
      color: #999;
      font-size: 12px;
      padding: 8px;
      background: #f5f5f5;
      border-radius: 6px;
      margin: 8px 0;
    }
  }

  .ques-item {
    margin-bottom: 12px;
    background: #fafdff;
    border-radius: 10px;
    padding: 14px 20px 14px 64px;
    position: relative;
    border: 1px solid #e8edf2;

    .avatar {
      position: absolute;
      left: 14px;
      top: 14px;
      width: 36px;
      height: 36px;
      border-radius: 50%;
    }
  }
}

// 表格内容 - 始终显示，不使用对话框样式
.table-content {
  display: block !important;

  .json-response-container,
  .markdown-table-container {
    margin-bottom: 20px;
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid #e8edf2;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
}

// 确保表格容器始终可见
.json-response-container,
.markdown-table-container {
  display: block !important;
}

// 调整布局
.ai-diagnosis,
.ai-surgery {
  .text-content:not(.collapsed) {
    border-bottom: 1px solid #eee;
    padding-bottom: 16px;
  }
}
</style>
