<template>
  <div class="his-page">
    <header class="his-header">
      <div class="brand-block">
        <div class="brand-mark">H</div>
        <div>
          <div class="brand-name">千佛山医院</div>
          <div class="brand-system">住院医生工作站</div>
        </div>
      </div>
      <nav class="his-nav" aria-label="HIS 主导航">
        <button
          type="button"
          :class="{ active: activeHisView === 'patients' }"
          @click="switchHisView('patients')"
        >
          患者列表
        </button>
        <button
          type="button"
          :class="{ active: activeHisView === 'record' }"
          @click="switchHisView('record')"
        >
          电子病历
        </button>
      </nav>
      <div class="header-user">
        <el-icon><User /></el-icon>
        <span>编码演示账号</span>
      </div>
    </header>

    <section v-if="activeHisView === 'patients'" class="patient-list-page">
      <div class="patient-list-heading">
        <div>
          <span class="page-eyebrow">住院病历管理</span>
          <h1>患者列表</h1>
          <p>管理已暂存的患者病历，打开后可继续编辑、编码和回写。</p>
        </div>
        <div class="patient-list-actions">
          <el-input
            v-model="patientSearchText"
            class="patient-list-search"
            clearable
            placeholder="搜索姓名、住院号、科室或床位"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" :icon="Plus" @click="createNewPatientRecord">
            新建病历
          </el-button>
        </div>
      </div>

      <div class="patient-list-panel">
        <div class="patient-list-summary">
          <div>
            <strong>{{ savedPatientRecords.length }}</strong>
            <span>份已暂存病历</span>
          </div>
          <span v-if="patientSearchText">当前筛选 {{ filteredPatientRecords.length }} 份</span>
        </div>

        <el-table
          v-if="filteredPatientRecords.length"
          :data="filteredPatientRecords"
          border
          stripe
          class="patient-management-table"
        >
          <el-table-column label="患者" min-width="150">
            <template #default="{ row }">
              <div class="patient-table-name">
                <span>{{ row.record['姓名'] }}</span>
                <small>{{ row.record['性别'] }} · {{ row.record['年龄'] }}</small>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="住院号" min-width="150">
            <template #default="{ row }">
              <span class="patient-record-number">{{ row.record['住院号'] }}</span>
            </template>
          </el-table-column>
          <el-table-column label="科室 / 床位" min-width="150">
            <template #default="{ row }">
              {{ row.record['科室'] }} / {{ row.record['床位'] }}
            </template>
          </el-table-column>
          <el-table-column label="住院日期" min-width="190">
            <template #default="{ row }">
              {{ row.record['入院日期'] }} 至 {{ row.record['出院日期'] }}
            </template>
          </el-table-column>
          <el-table-column label="编码状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getSavedRecordStatus(row).type" effect="plain">
                {{ getSavedRecordStatus(row).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="编码数量" width="105" align="center">
            <template #default="{ row }">
              {{ getSavedRecordCodeCount(row) }} 条
            </template>
          </el-table-column>
          <el-table-column label="最近暂存" min-width="160">
            <template #default="{ row }">
              {{ formatSavedTime(row.savedAt) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" :icon="EditPen" @click="openSavedPatientRecord(row)">
                打开病历
              </el-button>
              <el-button link type="danger" :icon="Delete" @click="deleteSavedPatientRecord(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty
          v-else
          :description="patientSearchText ? '没有找到匹配的患者病历' : '暂未保存患者病历'"
        >
          <el-button v-if="!patientSearchText" type="primary" :icon="Plus" @click="createNewPatientRecord">
            新建第一份病历
          </el-button>
        </el-empty>
      </div>
    </section>

    <div v-if="activeHisView === 'record'" class="patient-strip">
      <div class="patient-primary">
        <span class="patient-name">{{ record['姓名'] || '未命名患者' }}</span>
        <span>{{ record['性别'] }}</span>
        <span>{{ record['年龄'] }}</span>
        <el-tag size="small" type="success" effect="plain">在院</el-tag>
      </div>
      <div class="patient-meta">
        <span>住院号：{{ record['住院号'] }}</span>
        <span>科室：{{ record['科室'] }}</span>
        <span>床位：{{ record['床位'] }}</span>
        <span>入院日期：{{ record['入院日期'] }}</span>
      </div>
      <div class="patient-actions">
        <el-upload
          ref="pdfUploadRef"
          accept=".pdf,application/pdf"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handlePdfSelected"
          :disabled="ocrProcessing"
        >
          <el-button :loading="ocrProcessing" :icon="UploadFilled">
            上传病历 PDF
          </el-button>
        </el-upload>
        <el-button
          type="primary"
          class="coding-button"
          :loading="isCoding"
          :disabled="ocrProcessing"
          @click="handleCodingButtonClick"
        >
          <el-icon><MagicStick /></el-icon>
          AI 智能编码
        </el-button>
      </div>
    </div>

    <div v-if="activeHisView === 'record' && acceptedResultCount" class="writeback-notice">
      <el-icon><CircleCheck /></el-icon>
      <span>AiCode 已将 {{ acceptedResultCount }} 条选中编码回写到当前患者页面</span>
      <button type="button" @click="acceptedResultCount = 0">知道了</button>
    </div>

    <main v-if="activeHisView === 'record'" class="his-workspace">
      <aside class="patient-panel">
        <div class="panel-title">患者信息</div>
        <el-form label-position="top" size="small">
          <div class="two-column-fields">
            <el-form-item label="姓名">
              <el-input v-model="record['姓名']" />
            </el-form-item>
            <el-form-item label="性别">
              <el-select v-model="record['性别']">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
            <el-form-item label="年龄">
              <el-input v-model="record['年龄']" />
            </el-form-item>
            <el-form-item label="床位">
              <el-input v-model="record['床位']" />
            </el-form-item>
          </div>
          <el-form-item label="病案标识号">
            <el-input v-model="record['病案标识号']" />
          </el-form-item>
          <el-form-item label="住院号">
            <el-input v-model="record['住院号']" />
          </el-form-item>
          <el-form-item label="科室">
            <el-select v-model="record['科室']">
              <el-option label="胃肠外科" value="胃肠外科" />
              <el-option label="心内科" value="心内科" />
              <el-option label="血液科" value="血液科" />
              <el-option label="创伤骨科" value="创伤骨科" />
              <el-option label="肛肠科" value="肛肠科" />
              <el-option label="骨脊柱科" value="骨脊柱科" />
              <el-option label="肿瘤科" value="肿瘤科" />
              <el-option label="肝病科" value="肝病科" />
              <el-option label="神经外科" value="神经外科" />
              <el-option label="内分泌科" value="内分泌科" />
            </el-select>
          </el-form-item>
          <el-form-item label="入院日期">
            <el-date-picker
              v-model="record['入院日期']"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
            />
          </el-form-item>
          <el-form-item label="出院日期">
            <el-date-picker
              v-model="record['出院日期']"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
            />
          </el-form-item>
        </el-form>
      </aside>

      <section class="record-panel">
        <div class="record-toolbar">
          <div>
            <h1>住院病历</h1>
            <span>当前版本：住院病案首页编码资料</span>
          </div>
          <div class="record-actions">
            <el-button :icon="RefreshLeft" @click="resetDemo">恢复示例</el-button>
            <el-button type="primary" :icon="DocumentChecked" @click="saveCurrentPatientRecord">
              暂存病历
            </el-button>
          </div>
        </div>

        <el-tabs v-model="activeRecordTab" class="record-tabs">
          <el-tab-pane label="病历摘要" name="summary">
            <div class="record-form-grid">
              <div class="record-field full-width">
                <label>主诉</label>
                <el-input v-model="record['主诉']" type="textarea" :rows="2" />
              </div>
              <div class="record-field full-width">
                <label>现病史</label>
                <el-input v-model="record['现病史']" type="textarea" :rows="4" />
              </div>
              <div class="record-field">
                <label>既往史</label>
                <el-input v-model="record['既往史']" type="textarea" :rows="4" />
              </div>
              <div class="record-field">
                <label>入院情况</label>
                <el-input v-model="record['入院情况']" type="textarea" :rows="4" />
              </div>
              <div class="record-field">
                <label>入院诊断</label>
                <el-input v-model="record['入院诊断']" type="textarea" :rows="3" />
              </div>
              <div class="record-field">
                <label>出院诊断</label>
                <el-input v-model="record['出院诊断']" type="textarea" :rows="3" />
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="诊疗与手术" name="treatment">
            <div class="record-form-grid">
              <div class="record-field full-width">
                <label>诊疗经过</label>
                <el-input v-model="record['诊疗经过']" type="textarea" :rows="5" />
              </div>
              <div class="record-field">
                <label>手术名称</label>
                <el-input v-model="record['手术名称']" type="textarea" :rows="3" />
              </div>
              <div class="record-field">
                <label>术中诊断</label>
                <el-input v-model="record['术中诊断']" type="textarea" :rows="3" />
              </div>
              <div class="record-field full-width">
                <label>手术经过</label>
                <el-input v-model="record['手术经过']" type="textarea" :rows="7" />
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="辅助检查" name="examination">
            <div class="record-form-grid">
              <div class="record-field full-width">
                <label>影像学意见</label>
                <el-input v-model="record['影像学意见']" type="textarea" :rows="5" />
              </div>
              <div class="record-field full-width">
                <label>病理结果</label>
                <el-input v-model="record['病理结果']" type="textarea" :rows="5" />
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane name="coding-results">
            <template #label>
              <span class="writeback-tab-label">
                编码结果填写
                <strong v-if="writebackTotal">{{ writebackTotal }}</strong>
              </span>
            </template>
            <div class="writeback-workspace">
              <div class="writeback-heading">
                <div>
                  <h2>病案首页编码填写</h2>
                  <p>展示从 AiCode 采纳并回写到当前 HIS 页面的编码结果，可继续人工修改。</p>
                </div>
                <el-button
                  v-if="writebackTotal"
                  type="danger"
                  plain
                  size="small"
                  @click="clearWritebackResults"
                >
                  清空填写结果
                </el-button>
              </div>

              <div v-if="!writebackTotal" class="writeback-empty">
                <el-icon><DocumentChecked /></el-icon>
                <strong>暂未写入编码</strong>
                <span>完成智能编码后，勾选所需编码并点击“全部采纳”或“部分采纳”写入此处。</span>
              </div>

              <section v-if="writebackResults.diagnosis.length" class="writeback-section">
                <div class="writeback-section-title">
                  <span>疾病诊断编码</span>
                  <strong>{{ writebackResults.diagnosis.length }} 条</strong>
                </div>
                <el-table :data="writebackResults.diagnosis" border size="small">
                  <el-table-column type="index" label="序号" width="58" align="center" />
                  <el-table-column label="编码类型" min-width="140">
                    <template #default="{ row }">
                      <el-input v-model="row['编码类型']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="诊断名称" min-width="210">
                    <template #default="{ row }">
                      <el-input v-model="row['诊断名称']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="诊断编码" min-width="170">
                    <template #default="{ row }">
                      <el-input v-model="row['诊断编码']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="MCC/CC" width="100" align="center">
                    <template #default="{ row }">
                      <el-input v-model="row['是否并发症']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="76" align="center">
                    <template #default="{ $index }">
                      <el-button link type="danger" @click="removeWritebackItem('diagnosis', $index)">
                        移除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </section>

              <section v-if="writebackResults.surgery.length" class="writeback-section">
                <div class="writeback-section-title">
                  <span>手术操作编码</span>
                  <strong>{{ writebackResults.surgery.length }} 条</strong>
                </div>
                <el-table :data="writebackResults.surgery" border size="small">
                  <el-table-column type="index" label="序号" width="58" align="center" />
                  <el-table-column label="编码类型" min-width="140">
                    <template #default="{ row }">
                      <el-input v-model="row['编码类型']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="手术名称" min-width="220">
                    <template #default="{ row }">
                      <el-input v-model="row['手术名称']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="手术编码" min-width="170">
                    <template #default="{ row }">
                      <el-input v-model="row['手术编码']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="是否四级" width="100" align="center">
                    <template #default="{ row }">
                      <el-input v-model="row['是否四级']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="是否微创" width="100" align="center">
                    <template #default="{ row }">
                      <el-input v-model="row['是否微创']" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="76" align="center">
                    <template #default="{ $index }">
                      <el-button link type="danger" @click="removeWritebackItem('surgery', $index)">
                        移除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </section>
            </div>
          </el-tab-pane>
        </el-tabs>
      </section>
    </main>

    <button
      v-if="activeHisView === 'record' && dialogMinimized"
      type="button"
      class="coding-mini-window"
      @click="restoreCodingDialog"
    >
      <span class="mini-window-icon"><el-icon><MagicStick /></el-icon></span>
      <span>
        <strong>AiCode 智能辅助编码</strong>
        <small>{{ isCoding ? '编码处理中' : `已生成 ${resultTotal} 条编码` }}</small>
      </span>
      <span class="mini-window-action">恢复窗口</span>
    </button>

    <el-dialog
      v-model="ocrDialogVisible"
      class="ocr-dialog"
      width="min(520px, 92vw)"
      :close-on-click-modal="!ocrProcessing"
      :close-on-press-escape="!ocrProcessing"
      :show-close="!ocrProcessing"
    >
      <template #header>
        <div class="ocr-dialog-heading">
          <div class="ocr-dialog-icon"><Document /></div>
          <div>
            <h2>病历 PDF 识别</h2>
            <p>{{ ocrFileName }}</p>
          </div>
        </div>
      </template>
      <div class="ocr-progress-area">
        <div class="ocr-progress-status">
          <span>{{ ocrStepText }}</span>
          <strong>{{ ocrProgress }}%</strong>
        </div>
        <el-progress
          :percentage="ocrProgress"
          :status="ocrProgressStatus"
          :stroke-width="9"
          :show-text="false"
        />
        <div class="ocr-steps">
          <div
            v-for="(step, index) in ocrSteps"
            :key="step"
            class="ocr-step"
            :class="{
              active: index === ocrStepIndex && ocrProcessing,
              completed: index < ocrStepIndex || ocrSuccess,
              failed: ocrError && index === ocrStepIndex,
            }"
          >
            <span>{{ index + 1 }}</span>
            <label>{{ step }}</label>
          </div>
        </div>
        <div v-if="ocrSuccess" class="ocr-success-message">
          <el-icon><CircleCheck /></el-icon>
          <div>
            <strong>识别完成</strong>
            <span>已自动填写 {{ ocrFilledCount }} 个病历字段</span>
          </div>
        </div>
        <div v-if="ocrError" class="ocr-error-message">
          <el-icon><WarningFilled /></el-icon>
          <span>{{ ocrError }}</span>
        </div>
      </div>
      <template #footer>
        <el-button v-if="ocrProcessing" @click="cancelOcr">取消识别</el-button>
        <el-button v-else type="primary" @click="ocrDialogVisible = false">完成</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="dialogVisible"
      class="coding-dialog"
      :width="dialogWidth"
      :fullscreen="dialogFullscreen"
      :close-on-click-modal="false"
      :close-on-press-escape="!isCoding"
      :show-close="false"
      draggable
      overflow
      destroy-on-close
      @opened="restoreDialogGeometry"
    >
      <template #header>
        <div class="dialog-heading" @dblclick="toggleDialogFullscreen">
          <img
            class="dialog-brand-logo"
            :src="qianyiLogo"
            alt="千医牍智 AiCode"
          />
          <div class="dialog-patient-summary">
            <strong>{{ record['姓名'] || '未命名患者' }}</strong>
            <span>{{ record['性别'] || '-' }} · {{ record['年龄'] || '-' }}</span>
            <span>住院号：{{ record['住院号'] || '-' }}</span>
            <span>出院日期：{{ record['出院日期'] || '-' }}</span>
          </div>
          <el-tag :type="dialogStatusType" effect="plain">{{ dialogStatusText }}</el-tag>
          <div class="dialog-window-actions" @dblclick.stop>
            <el-tooltip content="最小化" placement="bottom">
              <button
                type="button"
                class="window-control"
                aria-label="最小化"
                @click.stop="minimizeCodingDialog"
              >
                <span class="window-icon window-icon-minimize" aria-hidden="true"></span>
              </button>
            </el-tooltip>
            <el-tooltip :content="dialogFullscreen ? '还原窗口' : '最大化'" placement="bottom">
              <button
                type="button"
                class="window-control"
                :aria-label="dialogFullscreen ? '还原窗口' : '最大化'"
                @click.stop="toggleDialogFullscreen"
              >
                <span class="window-icon window-icon-maximize" aria-hidden="true"></span>
              </button>
            </el-tooltip>
            <el-tooltip content="忽略并关闭" placement="bottom">
              <button
                type="button"
                class="window-control close-window"
                aria-label="忽略并关闭"
                @click.stop="ignoreRecommendations"
              >
                <span class="window-icon window-icon-close" aria-hidden="true"></span>
              </button>
            </el-tooltip>
          </div>
        </div>
      </template>

      <div class="coding-progress" v-if="isCoding || !hasResults">
        <div class="progress-summary">
          <span>编码进度</span>
          <strong>{{ completedAgentCount }}/{{ Math.max(agentLogs.length, 2) }}</strong>
        </div>
        <el-progress
          :percentage="progressPercentage"
          :status="hasFailedAgent ? 'exception' : undefined"
          :stroke-width="8"
        />
        <div class="agent-columns">
          <section v-for="source in modelSources" :key="source.key" class="agent-column">
            <div class="agent-column-title">
              <el-icon><component :is="source.icon" /></el-icon>
              {{ source.label }}
            </div>
            <div v-if="logsFor(source.key).length" class="agent-list">
              <div
                v-for="log in logsFor(source.key)"
                :key="log.key"
                class="agent-row"
              >
                <span class="status-dot" :class="log.status"></span>
                <span class="agent-name">{{ log.displayName }}</span>
                <span class="agent-state">{{ statusLabel(log.status) }}</span>
              </div>
            </div>
            <div v-else class="agent-empty">
              <el-icon class="is-loading"><Loading /></el-icon>
              正在连接模型服务
            </div>
          </section>
        </div>
      </div>

      <div v-if="hasResults" class="result-area">
        <div class="result-success-band">
          <div class="result-success-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="result-success-copy">
            <h3>智能编码完成</h3>
            <span>已生成 {{ resultTotal }} 条编码 · {{ finishedAt }}</span>
          </div>
          <div class="result-actions">
            <el-button :icon="List" @click="showProcessDetails = !showProcessDetails">
              {{ showProcessDetails ? '收起编码过程' : '查看编码过程详情' }}
            </el-button>
            <el-button :icon="CopyDocument" @click="copyResultCodes">复制编码</el-button>
            <el-button text :icon="RefreshRight" :loading="isCoding" @click="startCoding">
              重新编码
            </el-button>
          </div>
        </div>

        <div class="result-overview">
          <div class="overview-item">
            <span class="overview-label">疾病诊断</span>
            <strong>{{ diagnosisResult.rows.length }}</strong>
            <span class="overview-unit">条</span>
          </div>
          <div class="overview-divider"></div>
          <div class="overview-item">
            <span class="overview-label">手术操作</span>
            <strong>{{ surgeryResult.rows.length }}</strong>
            <span class="overview-unit">条</span>
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="showProcessDetails" class="process-detail-panel">
            <div class="process-detail-heading">
              <div>
                <h4>编码过程详情</h4>
                <span>各智能体本次构建的候选列表</span>
              </div>
              <span class="process-agent-count">共调用 {{ processDetails.length }} 个智能体</span>
            </div>
            <div v-if="processDetails.length" class="process-source-columns">
              <section
                v-for="source in modelSources"
                :key="`detail-${source.key}`"
                class="process-source"
              >
                <div class="process-source-title">
                  <el-icon><component :is="source.icon" /></el-icon>
                  <span>{{ source.label }}</span>
                  <strong>{{ detailsFor(source.key).length }}</strong>
                </div>
                <div v-if="detailsFor(source.key).length" class="process-agent-list">
                  <article
                    v-for="(detail, detailIndex) in detailsFor(source.key)"
                    :key="detail.key"
                    class="process-agent-item"
                  >
                    <div class="process-agent-heading">
                      <span class="process-index">{{ detailIndex + 1 }}</span>
                      <span>{{ getAnonymousProcessAgentName(detail) }}</span>
                    </div>
                    <div v-if="detail.items.length" class="constructed-list">
                      <span class="list-bracket">[</span>
                      <template v-for="(item, itemIndex) in detail.items" :key="itemIndex">
                        <span class="constructed-item">{{ item }}</span>
                        <span v-if="itemIndex < detail.items.length - 1" class="list-separator">,</span>
                      </template>
                      <span class="list-bracket">]</span>
                    </div>
                    <div v-else class="constructed-empty">该智能体未返回可展示列表</div>
                  </article>
                </div>
                <div v-else class="process-source-empty">本次未调用该类智能体</div>
              </section>
            </div>
            <div v-else class="process-source-empty">本次没有可展示的智能体过程数据</div>
          </div>
        </el-collapse-transition>

        <el-tabs v-model="activeResultTab" class="result-tabs">
          <el-tab-pane name="diagnosis">
            <template #label>
              <span class="result-tab-label">
                <el-icon><FirstAidKit /></el-icon>
                <span>疾病诊断</span>
                <strong>{{ diagnosisResult.rows.length }}</strong>
              </span>
            </template>
            <result-table
              :result="diagnosisResult"
              mode="diagnosis"
              :selected-rows="selectedRows.diagnosis"
              empty-text="未生成疾病诊断编码"
              @toggle-row="toggleResultRow('diagnosis', $event)"
              @toggle-all="toggleAllRows('diagnosis', $event)"
              @move-row="moveResultRow('diagnosis', $event)"
            />
          </el-tab-pane>
          <el-tab-pane name="surgery">
            <template #label>
              <span class="result-tab-label">
                <el-icon><Operation /></el-icon>
                <span>手术操作</span>
                <strong>{{ surgeryResult.rows.length }}</strong>
              </span>
            </template>
            <result-table
              :result="surgeryResult"
              mode="surgery"
              :selected-rows="selectedRows.surgery"
              empty-text="未生成手术操作编码"
              @toggle-row="toggleResultRow('surgery', $event)"
              @toggle-all="toggleAllRows('surgery', $event)"
              @move-row="moveResultRow('surgery', $event)"
            />
          </el-tab-pane>
        </el-tabs>
      </div>

      <div v-if="requestError && !isCoding" class="request-error">
        <el-icon><WarningFilled /></el-icon>
        <span>{{ requestError }}</span>
      </div>

      <template #footer>
        <div class="coding-dialog-footer">
          <div class="selection-summary" v-if="hasResults && !isCoding">
            已选择 <strong>{{ selectedResultCount }}</strong> / {{ resultTotal }} 条编码
            <span v-if="acceptedResultCount">· 已回写 {{ acceptedResultCount }} 条</span>
          </div>
          <div class="footer-actions">
            <el-button v-if="isCoding" @click="cancelCoding">停止编码</el-button>
            <template v-else-if="hasResults">
              <el-button @click="ignoreRecommendations">忽略推荐</el-button>
              <el-button
                type="primary"
                :disabled="!selectedResultCount"
                @click="applyCurrentSelection"
              >
                <el-icon><CircleCheck /></el-icon>
                {{ allResultsSelected ? '全部采纳' : '部分采纳' }}
              </el-button>
            </template>
            <el-button v-else @click="closeCodingDialog">关闭</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  CircleCheck,
  CopyDocument,
  Delete,
  Document,
  DocumentChecked,
  EditPen,
  FirstAidKit,
  List,
  Loading,
  MagicStick,
  Operation,
  Plus,
  RefreshLeft,
  RefreshRight,
  Search,
  UploadFilled,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import qianyiLogo from '../assets/logo_02.png'
import hisCodingGroundTruth from '../data/his-coding-ground-truth.json'

const pickRandom = (items) => items[Math.floor(Math.random() * items.length)]

// 仅供指定演示病例使用的预置结果。命中时保留完整的前端进度与结果展示流程，
// 但不会请求模型服务；控制台和操作日志会明确记录 preset_demo 来源。
const HIS_CODING_PRESET_RESULTS = hisCodingGroundTruth

const normalizePresetRecordNumber = (value = '') =>
  String(value).trim().replace(/[^0-9]/g, '')

const findPresetCase = (patientRecord) => {
  const candidates = [patientRecord['住院号'], patientRecord['病案标识号']]
    .map(normalizePresetRecordNumber)
    .filter(Boolean)
  const matchedKey = Object.keys(HIS_CODING_PRESET_RESULTS).find((key) => {
    const normalizedKey = normalizePresetRecordNumber(key)
    return candidates.some(
      (candidate) =>
        candidate === normalizedKey ||
        candidate.replace(/^0+/, '') === normalizedKey.replace(/^0+/, '')
    )
  })
  return matchedKey
    ? { inpatientNo: matchedKey, presetCase: HIS_CODING_PRESET_RESULTS[matchedKey] }
    : null
}

const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const shiftDate = (dateText, days) => {
  const date = new Date(`${dateText}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  date.setDate(date.getDate() + days)
  return formatDate(date)
}

const createRandomPatientInfo = () => {
  const gender = pickRandom(['男', '女'])
  const names = gender === '男'
    ? ['王建国', '李志强', '张伟', '刘国栋', '陈海峰', '赵明远', '孙文博', '周立新', '吴志刚', '徐海涛']
    : ['李秀兰', '王静', '张晓梅', '刘芳', '陈丽华', '赵雅琴', '孙慧敏', '周雨晴', '吴桂英', '徐晓燕']
  const admissionDate = pickRandom([
    '2026-06-12',
    '2026-06-21',
    '2026-07-03',
    '2026-07-15',
    '2026-07-26',
    '2026-08-02',
  ])
  const stayDays = pickRandom([3, 4, 5, 6, 7, 9])

  return {
    姓名: pickRandom(names),
    性别: gender,
    年龄: `${pickRandom([26, 32, 39, 45, 51, 56, 63, 68, 72, 79])}岁`,
    科室: pickRandom([
      '胃肠外科',
      '心内科',
      '血液科',
      '创伤骨科',
      '肛肠科',
      '骨脊柱科',
      '肿瘤科',
      '肝病科',
      '神经外科',
      '内分泌科',
    ]),
    床位: pickRandom(['03床', '06床', '08床', '12床', '16床', '21床', '25床', '32床']),
    入院日期: admissionDate,
    出院日期: shiftDate(admissionDate, stayDays),
  }
}

const fillMissingPatientInfo = (targetRecord) => {
  const fallback = createRandomPatientInfo()
  const basicFields = ['姓名', '性别', '年龄', '床位', '科室']
  basicFields.forEach((field) => {
    if (!String(targetRecord[field] || '').trim()) targetRecord[field] = fallback[field]
  })

  const admissionDate = String(targetRecord['入院日期'] || '').trim()
  const dischargeDate = String(targetRecord['出院日期'] || '').trim()
  const stayDays = pickRandom([3, 4, 5, 6, 7, 9])
  if (!admissionDate && !dischargeDate) {
    targetRecord['入院日期'] = fallback['入院日期']
    targetRecord['出院日期'] = fallback['出院日期']
  } else if (!admissionDate) {
    targetRecord['入院日期'] = shiftDate(dischargeDate, -stayDays) || fallback['入院日期']
  } else if (!dischargeDate) {
    targetRecord['出院日期'] = shiftDate(admissionDate, stayDays) || fallback['出院日期']
  }
  return targetRecord
}

const createDemoRecord = () => ({
  ...createRandomPatientInfo(),
  病案标识号: 'ZY-DEMO-0001',
  住院号: 'ZY-DEMO-0001',
  主诉: '转移性右下腹痛1天。',
  现病史:
    '患者1天前无明显诱因出现上腹部疼痛，后转移并固定于右下腹，伴恶心，无呕吐。急诊腹部CT提示阑尾增粗，周围脂肪间隙模糊。',
  既往史: '高血压病史5年，口服药物控制。否认糖尿病、冠心病病史。',
  入院情况:
    '体温37.8℃，右下腹压痛、反跳痛，麦氏点压痛阳性。白细胞计数及中性粒细胞比例升高。',
  入院诊断: '急性阑尾炎；高血压。',
  出院诊断: '急性化脓性阑尾炎；高血压。',
  诊疗经过:
    '入院后完善血常规、凝血功能及腹部影像检查，给予抗感染、补液治疗。排除手术禁忌后，在全身麻醉下行腹腔镜阑尾切除术，术后恢复良好。',
  手术名称: '腹腔镜阑尾切除术',
  术中诊断: '急性化脓性阑尾炎',
  手术经过:
    '全身麻醉成功后，建立气腹，置入腹腔镜。探查见阑尾充血肿胀，表面覆脓苔。分离并离断阑尾系膜，于阑尾根部结扎后完整切除阑尾，冲洗腹腔，检查无活动性出血后关闭切口。',
  影像学意见: '阑尾增粗，直径约12mm，周围脂肪间隙模糊，考虑急性阑尾炎。',
  病理结果: '阑尾急性化脓性炎。',
})

const ResultTable = defineComponent({
  name: 'ResultTable',
  props: {
    result: { type: Object, required: true },
    mode: { type: String, default: 'diagnosis' },
    selectedRows: { type: Array, default: () => [] },
    emptyText: { type: String, default: '暂无数据' },
  },
  emits: ['toggle-row', 'toggle-all', 'move-row'],
  setup(props, { emit }) {
    const expandedEvidence = ref(new Set())
    const draggingRowIndex = ref(null)
    const dragOverRowIndex = ref(null)
    let dragMoveHandler = null
    let dragEndHandler = null

    const stopPointerDrag = () => {
      if (dragMoveHandler) window.removeEventListener('mousemove', dragMoveHandler)
      if (dragEndHandler) window.removeEventListener('mouseup', dragEndHandler)
      dragMoveHandler = null
      dragEndHandler = null
      document.body.classList.remove('is-sorting-codes')
    }

    const startPointerDrag = (rowIndex, event) => {
      event.preventDefault()
      event.stopPropagation()
      stopPointerDrag()
      draggingRowIndex.value = rowIndex
      dragOverRowIndex.value = rowIndex
      document.body.classList.add('is-sorting-codes')

      dragMoveHandler = (moveEvent) => {
        const targetRow = document
          .elementFromPoint(moveEvent.clientX, moveEvent.clientY)
          ?.closest('tr[data-row-index]')
        if (!targetRow) return
        const targetIndex = Number(targetRow.dataset.rowIndex)
        if (Number.isInteger(targetIndex)) dragOverRowIndex.value = targetIndex
      }
      dragEndHandler = () => {
        const fromIndex = draggingRowIndex.value
        const toIndex = dragOverRowIndex.value
        if (fromIndex !== null && toIndex !== null && fromIndex !== toIndex) {
          emit('move-row', { fromIndex, toIndex })
        }
        draggingRowIndex.value = null
        dragOverRowIndex.value = null
        stopPointerDrag()
      }
      window.addEventListener('mousemove', dragMoveHandler)
      window.addEventListener('mouseup', dragEndHandler)
    }
    onBeforeUnmount(stopPointerDrag)
    const currentPage = ref(1)
    const tableWrapRef = ref(null)
    const fontSizeStorageKey = `his-coding-${props.mode}-table-font-size`
    const storedFontSize = Number(localStorage.getItem(fontSizeStorageKey))
    const tableFontSize = ref(
      storedFontSize >= 10 && storedFontSize <= 18 ? storedFontSize : 12
    )
    const pageSize = 6
    const pageCount = computed(() => Math.max(1, Math.ceil(props.result.rows.length / pageSize)))
    const pagedRows = computed(() => {
      if (currentPage.value > pageCount.value) currentPage.value = pageCount.value
      const start = (currentPage.value - 1) * pageSize
      return props.result.rows.slice(start, start + pageSize).map((row, offset) => ({
        row,
        rowIndex: start + offset,
      }))
    })
    const goToPage = (targetPage) => {
      currentPage.value = Math.min(pageCount.value, Math.max(1, targetPage))
      nextTick(() => {
        if (tableWrapRef.value) tableWrapRef.value.scrollTop = 0
      })
    }
    const normalizedHeader = (header = '') => String(header).replace(/\*\*/g, '').trim()
    const columnKind = (header = '') => {
      const name = normalizedHeader(header)
      if (/^(诊断编码|手术编码)$/.test(name)) return 'code'
      if (name === '编码类型') return 'type'
      if (name === '是否并发症') return 'complication'
      if (name === '是否四级') return 'level4'
      if (name === '是否微创') return 'minimally-invasive'
      if (name === '依据') return 'evidence'
      if (/^(诊断名称|手术名称)$/.test(name)) return 'name'
      if (name === '病案标识号') return 'record'
      return 'default'
    }
    const visibleColumns = computed(() => {
      const columns = props.result.headers
        .map((header, columnIndex) => ({ header, columnIndex }))
        .filter(({ header }) => columnKind(header) !== 'record')
      const typePosition = columns.findIndex(({ header }) => columnKind(header) === 'type')
      if (typePosition < 0) return columns

      const [typeColumn] = columns.splice(typePosition, 1)
      const namePosition = columns.findIndex(({ header }) => columnKind(header) === 'name')
      columns.splice(namePosition < 0 ? 0 : namePosition, 0, typeColumn)
      return columns
    })
    const setTableFontSize = (nextSize) => {
      const normalizedSize = Math.min(18, Math.max(10, nextSize))
      tableFontSize.value = normalizedSize
      localStorage.setItem(fontSizeStorageKey, String(normalizedSize))
    }
    const scrollTable = (direction) => {
      tableWrapRef.value?.scrollBy({
        left: direction * Math.max(280, tableWrapRef.value.clientWidth * 0.65),
        behavior: 'smooth',
      })
    }
    const typeClass = (value = '') => {
      const text = String(value)
      if (/主诊断|主手术/.test(text)) return 'primary'
      if (/病理/.test(text)) return 'pathology'
      if (/外因/.test(text)) return 'external'
      if (/另编码/.test(text)) return 'additional'
      return 'other'
    }
    const cellContent = (header, value, isPrimary, rowIndex) => {
      const kind = columnKind(header)
      const text = value || '-'
      if (kind === 'code') {
        return h('span', { class: ['code-token', { primary: isPrimary }] }, text)
      }
      if (kind === 'type') {
        return h('span', { class: ['type-badge', typeClass(text)] }, text)
      }
      if (kind === 'complication') {
        const isComplication = /^(MCC|CC)$/i.test(text)
        return h(
          'span',
          { class: ['complication-badge', { active: isComplication }] },
          text
        )
      }
      if (kind === 'evidence') {
        const isExpanded = expandedEvidence.value.has(rowIndex)
        return h('div', { class: 'evidence-content' }, [
          h(
            'div',
            { class: ['evidence-cell', { expanded: isExpanded }], title: text },
            text
          ),
          text !== '-' && text.length > 36
            ? h(
                'button',
                {
                  type: 'button',
                  class: 'evidence-toggle',
                  onClick: () => {
                    const next = new Set(expandedEvidence.value)
                    if (next.has(rowIndex)) next.delete(rowIndex)
                    else next.add(rowIndex)
                    expandedEvidence.value = next
                  },
                },
                isExpanded ? '收起依据' : '展开依据'
              )
            : null,
        ])
      }
      if (kind === 'record') {
        return h('span', { class: 'record-token', title: text }, text)
      }
      if (kind === 'name') {
        return h(
          'span',
          { class: ['result-name', { primary: isPrimary }], title: text },
          text
        )
      }
      return text
    }
    return () =>
      h(
        'div',
        {
          class: 'result-table-shell',
          style: {
            '--result-table-font-size': `${tableFontSize.value}px`,
            '--result-table-small-font-size': `${Math.max(9, tableFontSize.value - 1)}px`,
          },
        },
        props.result.rows.length
          ? [
              h('div', { class: 'table-legend' }, [
                h(
                  'strong',
                  { class: 'table-section-name' },
                  props.mode === 'diagnosis' ? '疾病诊断编码明细' : '手术操作编码明细'
                ),
                h('span', { class: 'legend-main' }, '主要编码'),
                h('span', { class: 'legend-other' }, '其他编码'),
                h('div', { class: 'table-view-tools' }, [
                  h('span', { class: 'table-count' }, `共 ${props.result.rows.length} 条`),
                  h('div', { class: 'table-tool-group font-size-tools' }, [
                    h(
                      'button',
                      {
                        type: 'button',
                        class: 'table-tool-button',
                        disabled: tableFontSize.value <= 10,
                        title: '缩小表格字体',
                        'aria-label': '缩小表格字体',
                        onClick: () => setTableFontSize(tableFontSize.value - 1),
                      },
                      'A−'
                    ),
                    h('span', { class: 'font-size-value' }, `${tableFontSize.value}px`),
                    h(
                      'button',
                      {
                        type: 'button',
                        class: 'table-tool-button reset-font-button',
                        title: '恢复默认字体大小',
                        'aria-label': '恢复默认字体大小',
                        onClick: () => setTableFontSize(12),
                      },
                      '默认'
                    ),
                    h(
                      'button',
                      {
                        type: 'button',
                        class: 'table-tool-button',
                        disabled: tableFontSize.value >= 18,
                        title: '放大表格字体',
                        'aria-label': '放大表格字体',
                        onClick: () => setTableFontSize(tableFontSize.value + 1),
                      },
                      'A+'
                    ),
                  ]),
                  h('div', { class: 'table-tool-group scroll-tools' }, [
                    h(
                      'button',
                      {
                        type: 'button',
                        class: 'table-tool-button scroll-button',
                        title: '表格向左滑动',
                        'aria-label': '表格向左滑动',
                        onClick: () => scrollTable(-1),
                      },
                      '← 左移'
                    ),
                    h(
                      'button',
                      {
                        type: 'button',
                        class: 'table-tool-button scroll-button',
                        title: '表格向右滑动',
                        'aria-label': '表格向右滑动',
                        onClick: () => scrollTable(1),
                      },
                      '右移 →'
                    ),
                  ]),
                ]),
              ]),
              h(
                'div',
                {
                  key: 'result-table-content',
                  class: 'result-table-wrap',
                  ref: tableWrapRef,
                },
                [
                  h(
                    'table',
                    { class: ['coding-result-table', `${props.mode}-result-table`] },
                    [
                      h(
                        'thead',
                        h(
                          'tr',
                          [
                            h('th', { class: 'column-selection' }, [
                              h('input', {
                                type: 'checkbox',
                                checked:
                                  props.result.rows.length > 0 &&
                                  props.selectedRows.length === props.result.rows.length,
                                'aria-label': '全选当前页编码',
                                onChange: (event) => emit('toggle-all', event.target.checked),
                              }),
                            ]),
                            h('th', { class: 'column-order' }, '拖动'),
                            ...visibleColumns.value.map(({ header }) =>
                              h('th', { class: `column-${columnKind(header)}` }, header)
                            ),
                          ]
                        )
                      ),
                      h(
                        'tbody',
                        pagedRows.value.map(({ row, rowIndex }) => {
                          const typeIndex = props.result.headers.findIndex(
                            (header) => columnKind(header) === 'type'
                          )
                          const isPrimary = /主诊断|主手术/.test(row[typeIndex] || '')
                          return h(
                            'tr',
                            {
                              key: rowIndex,
                              class: {
                                'primary-result-row': isPrimary,
                                'selected-result-row': props.selectedRows.includes(rowIndex),
                                'dragging-result-row': draggingRowIndex.value === rowIndex,
                                'drag-over-result-row': dragOverRowIndex.value === rowIndex,
                              },
                              'data-row-index': rowIndex,
                            },
                            [
                              h('td', { class: 'column-selection' }, [
                                h('input', {
                                  type: 'checkbox',
                                  checked: props.selectedRows.includes(rowIndex),
                                  'aria-label': `选择第 ${rowIndex + 1} 条编码`,
                                  onChange: (event) =>
                                    emit('toggle-row', { index: rowIndex, checked: event.target.checked }),
                                }),
                              ]),
                              h('td', { class: 'column-order' }, [
                                h(
                                  'span',
                                  {
                                    class: 'drag-handle',
                                    title: '按住并拖动此行排序',
                                    'aria-label': '拖动排序',
                                    onMousedown: (event) => startPointerDrag(rowIndex, event),
                                  },
                                  Array.from({ length: 6 }, (_, dotIndex) =>
                                    h('i', { key: dotIndex })
                                  )
                                ),
                              ]),
                              ...visibleColumns.value.map(({ header, columnIndex }) =>
                                h(
                                  'td',
                                  { class: `column-${columnKind(header)}` },
                                  cellContent(header, row[columnIndex], isPrimary, rowIndex)
                                )
                              ),
                            ]
                          )
                        })
                      ),
                    ]
                  ),
                ]
              ),
              props.result.rows.length > pageSize
                ? h('div', { key: 'result-pagination', class: 'result-pagination' }, [
                    h('span', `第 ${currentPage.value} / ${pageCount.value} 页`),
                    h(
                      'button',
                      {
                        type: 'button',
                        disabled: currentPage.value === 1,
                        onClick: () => goToPage(currentPage.value - 1),
                      },
                      '上一页'
                    ),
                    h(
                      'button',
                      {
                        type: 'button',
                        disabled: currentPage.value === pageCount.value,
                        onClick: () => goToPage(currentPage.value + 1),
                      },
                      '下一页'
                    ),
                  ])
                : null,
            ]
          : [h('div', { class: 'empty-result' }, props.emptyText)]
      )
  },
})

const record = ref(createDemoRecord())
const createEmptyRecord = () =>
  Object.fromEntries(Object.keys(createDemoRecord()).map((key) => [key, '']))
const SAVED_PATIENT_RECORDS_KEY = 'his-aicode-saved-patient-records'
const loadSavedPatientRecords = () => {
  try {
    const stored = JSON.parse(localStorage.getItem(SAVED_PATIENT_RECORDS_KEY) || '[]')
    return Array.isArray(stored) ? stored.filter((item) => item?.id && item?.record) : []
  } catch (_) {
    return []
  }
}
const activeHisView = ref('record')
const patientSearchText = ref('')
const savedPatientRecords = ref(loadSavedPatientRecords())
const activeRecordTab = ref('summary')
const activeResultTab = ref('diagnosis')
const dialogVisible = ref(false)
const dialogMinimized = ref(false)
const dialogFullscreen = ref(false)
const dialogWidth = ref(localStorage.getItem('his-aicode-dialog-width') || 'min(1180px, 96vw)')
const isCoding = ref(false)
const requestError = ref('')
const finishedAt = ref('')
const agentLogs = ref([])
const processDetails = ref([])
const showProcessDetails = ref(false)
const diagnosisResult = ref({ headers: [], rows: [] })
const surgeryResult = ref({ headers: [], rows: [] })
const selectedRows = ref({ diagnosis: [], surgery: [] })
const acceptedResultCount = ref(0)
const writebackResults = ref({ diagnosis: [], surgery: [] })
let activeController = null

const pdfUploadRef = ref(null)
const ocrDialogVisible = ref(false)
const ocrProcessing = ref(false)
const ocrProgress = ref(0)
const ocrStepIndex = ref(0)
const ocrFileName = ref('')
const ocrError = ref('')
const ocrSuccess = ref(false)
const ocrFilledCount = ref(0)
let ocrController = null
let ocrProgressTimer = null
const ocrSteps = ['上传文件', '识别病历文本', '解析结构化字段', '填写病历']

const OCR_FIELD_ALIASES = {
  姓名: ['姓名', '患者姓名', 'patient_name', 'patientname', 'name'],
  性别: ['性别', 'gender', 'sex'],
  年龄: ['年龄', 'age'],
  科室: ['科室', '临床科室', '临床专业', 'department', 'linchuang_zhuanye'],
  床位: ['床位', '床号', 'bed', 'bed_no'],
  病案标识号: [
    '病案标识号',
    '病案标识',
    '病案号',
    'case_identifier',
    'case_id',
    'med_record_id',
  ],
  住院号: ['住院号', 'inpatient_no', 'admission_no'],
  入院日期: ['入院日期', '入院时间', 'admission_date', 'admission_time'],
  出院日期: ['出院日期', '出院时间', 'discharge_date', 'discharge_time'],
  主诉: ['主诉', 'chief_complaint'],
  现病史: ['现病史', 'present_illness'],
  既往史: ['既往史', 'past_history'],
  入院情况: ['入院情况', 'admission_status'],
  入院诊断: ['入院诊断', 'admission_diagnosis'],
  出院诊断: ['出院诊断', 'discharge_diagnosis'],
  诊疗经过: ['诊疗经过', '治疗经过', 'treatment_course'],
  手术名称: ['手术名称', 'operation_name', 'surgery_name'],
  术中诊断: ['术中诊断', 'intraoperative_diagnosis'],
  手术经过: ['手术经过', '手术记录', 'operation_course', 'surgery_course'],
  影像学意见: [
    '影像学意见',
    '影像意见',
    '影像学结论',
    'imaging_opinion',
  ],
  病理结果: ['病理结果', '病理诊断', 'pathological_results', 'pathology_result'],
}

const modelSources = [
  { key: 'diagnosis', label: '疾病诊断编码', icon: FirstAidKit },
  { key: 'surgery', label: '手术操作编码', icon: Operation },
]

const ocrStepText = computed(() => {
  if (ocrError.value) return '病历识别失败'
  if (ocrSuccess.value) return '字段已填写到 HIS 病历'
  return ocrSteps[ocrStepIndex.value] || '正在处理'
})
const ocrProgressStatus = computed(() => {
  if (ocrError.value) return 'exception'
  if (ocrSuccess.value) return 'success'
  return undefined
})

const hasResults = computed(
  () => diagnosisResult.value.rows.length > 0 || surgeryResult.value.rows.length > 0
)
const resultTotal = computed(
  () => diagnosisResult.value.rows.length + surgeryResult.value.rows.length
)
const selectedResultCount = computed(
  () => selectedRows.value.diagnosis.length + selectedRows.value.surgery.length
)
const allResultsSelected = computed(
  () => resultTotal.value > 0 && selectedResultCount.value === resultTotal.value
)
const writebackTotal = computed(
  () => writebackResults.value.diagnosis.length + writebackResults.value.surgery.length
)
const filteredPatientRecords = computed(() => {
  const keyword = patientSearchText.value.trim().toLowerCase()
  return [...savedPatientRecords.value]
    .sort((left, right) => String(right.savedAt || '').localeCompare(String(left.savedAt || '')))
    .filter((item) => {
      if (!keyword) return true
      const patient = item.record || {}
      return ['姓名', '住院号', '病案标识号', '科室', '床位'].some((field) =>
        String(patient[field] || '').toLowerCase().includes(keyword)
      )
    })
})
const completedAgentCount = computed(
  () => agentLogs.value.filter((item) => ['completed', 'skipped'].includes(item.status)).length
)
const hasFailedAgent = computed(() =>
  agentLogs.value.some((item) => item.status === 'failed')
)
const progressPercentage = computed(() => {
  if (!agentLogs.value.length) return 4
  const resolved = agentLogs.value.filter((item) =>
    ['completed', 'skipped', 'failed'].includes(item.status)
  ).length
  if (isCoding.value) return Math.min(96, Math.max(8, Math.round((resolved / agentLogs.value.length) * 100)))
  return 100
})
const dialogStatusText = computed(() => {
  if (isCoding.value) return '处理中'
  if (requestError.value && !hasResults.value) return '处理失败'
  return '已完成'
})
const dialogStatusType = computed(() => {
  if (isCoding.value) return 'warning'
  if (requestError.value && !hasResults.value) return 'danger'
  return 'success'
})

const cloneStoredValue = (value) => JSON.parse(JSON.stringify(value))

const persistSavedPatientRecords = () => {
  try {
    localStorage.setItem(
      SAVED_PATIENT_RECORDS_KEY,
      JSON.stringify(savedPatientRecords.value)
    )
    return true
  } catch (_) {
    ElMessage.error('病历暂存失败，浏览器存储空间可能不足')
    return false
  }
}

const createPatientRecordId = () =>
  `ZY${formatDate(new Date()).replace(/-/g, '')}${String(Date.now()).slice(-6)}`

const ensurePatientRecordIdentity = (patientRecord) => {
  let recordId = String(
    patientRecord['病案标识号'] || patientRecord['住院号'] || ''
  ).trim()
  if (!recordId) recordId = createPatientRecordId()
  if (!String(patientRecord['病案标识号'] || '').trim()) {
    patientRecord['病案标识号'] = recordId
  }
  if (!String(patientRecord['住院号'] || '').trim()) patientRecord['住院号'] = recordId
  return recordId
}

const getSavedRecordCodeCount = (item) => {
  const writtenCount =
    (item.writebackResults?.diagnosis?.length || 0) +
    (item.writebackResults?.surgery?.length || 0)
  if (writtenCount) return writtenCount
  return (
    (item.diagnosisResult?.rows?.length || 0) +
    (item.surgeryResult?.rows?.length || 0)
  )
}

const getSavedRecordStatus = (item) => {
  const writtenCount =
    (item.writebackResults?.diagnosis?.length || 0) +
    (item.writebackResults?.surgery?.length || 0)
  if (writtenCount) return { label: '已回写', type: 'success' }
  if (getSavedRecordCodeCount(item)) return { label: '已编码', type: 'warning' }
  return { label: '待编码', type: 'info' }
}

const formatSavedTime = (value) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${formatDate(date)} ${hours}:${minutes}`
}

const saveCurrentPatientRecord = () => {
  fillMissingPatientInfo(record.value)
  const recordId = ensurePatientRecordIdentity(record.value)
  const existingRecord = savedPatientRecords.value.find((item) => item.id === recordId)
  const snapshot = {
    id: recordId,
    record: cloneStoredValue(record.value),
    diagnosisResult: cloneStoredValue(diagnosisResult.value),
    surgeryResult: cloneStoredValue(surgeryResult.value),
    selectedRows: cloneStoredValue(selectedRows.value),
    writebackResults: cloneStoredValue(writebackResults.value),
    finishedAt: finishedAt.value,
    createdAt: existingRecord?.createdAt || new Date().toISOString(),
    savedAt: new Date().toISOString(),
  }
  savedPatientRecords.value = [
    snapshot,
    ...savedPatientRecords.value.filter((item) => item.id !== recordId),
  ]
  if (persistSavedPatientRecords()) {
    ElMessage.success(existingRecord ? '病历已更新暂存' : '病历已暂存到患者列表')
  }
}

const switchHisView = (view) => {
  if (view === 'patients' && dialogVisible.value) {
    persistDialogGeometry()
    dialogVisible.value = false
    dialogMinimized.value = isCoding.value || hasResults.value
  }
  activeHisView.value = view
}

const createNewPatientRecord = () => {
  resetCodingSessionForNewRecord()
  const nextRecord = createEmptyRecord()
  fillMissingPatientInfo(nextRecord)
  const recordId = createPatientRecordId()
  nextRecord['病案标识号'] = recordId
  nextRecord['住院号'] = recordId
  record.value = nextRecord
  activeRecordTab.value = 'summary'
  activeHisView.value = 'record'
  patientSearchText.value = ''
  ElMessage.success('已新建患者病历')
}

const openSavedPatientRecord = (item) => {
  resetCodingSessionForNewRecord()
  record.value = cloneStoredValue(item.record)
  diagnosisResult.value = cloneStoredValue(item.diagnosisResult || { headers: [], rows: [] })
  surgeryResult.value = cloneStoredValue(item.surgeryResult || { headers: [], rows: [] })
  selectedRows.value = cloneStoredValue(item.selectedRows || { diagnosis: [], surgery: [] })
  writebackResults.value = cloneStoredValue(
    item.writebackResults || { diagnosis: [], surgery: [] }
  )
  acceptedResultCount.value =
    writebackResults.value.diagnosis.length + writebackResults.value.surgery.length
  finishedAt.value = item.finishedAt || ''
  activeRecordTab.value = 'summary'
  activeHisView.value = 'record'
  patientSearchText.value = ''
  ElMessage.success(`已打开 ${record.value['姓名']} 的病历`)
}

const deleteSavedPatientRecord = async (item) => {
  try {
    await ElMessageBox.confirm(
      `确定删除 ${item.record?.['姓名'] || '该患者'} 的暂存病历吗？`,
      '删除病历',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch (_) {
    return
  }
  savedPatientRecords.value = savedPatientRecords.value.filter(
    (recordItem) => recordItem.id !== item.id
  )
  if (persistSavedPatientRecords()) ElMessage.success('暂存病历已删除')
}

const cleanCell = (value = '') =>
  String(value)
    .replace(/^\s*\*\*|\*\*\s*$/g, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/\\n/g, '\n')
    .trim()

const parseMarkdownTable = (content = '') => {
  const lines = String(content)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith('|') && line.endsWith('|'))

  for (let index = 0; index < lines.length - 1; index += 1) {
    const divider = lines[index + 1]
    if (!/^\|(?:\s*:?-{3,}:?\s*\|)+$/.test(divider)) continue
    const parseLine = (line) => line.slice(1, -1).split('|').map(cleanCell)
    const headers = parseLine(lines[index])
    const rows = []
    for (let rowIndex = index + 2; rowIndex < lines.length; rowIndex += 1) {
      const cells = parseLine(lines[rowIndex])
      if (cells.length !== headers.length) break
      rows.push(cells)
    }
    if (headers.length && rows.length) return { headers, rows }
  }
  return { headers: [], rows: [] }
}

const logsFor = (source) => agentLogs.value.filter((item) => item.source === source)
const detailsFor = (source) => processDetails.value.filter((item) => item.source === source)
const getAnonymousProcessAgentName = (detail) => {
  const key = `${detail.source}:${detail.name}`
  const index = agentLogs.value.findIndex((item) => item.key === key)
  if (index >= 0) return agentLogs.value[index].displayName
  const detailIndex = processDetails.value.findIndex((item) => item.key === detail.key)
  return `智能体${agentLogs.value.length + Math.max(0, detailIndex) + 1}`
}
const statusLabel = (status) =>
  ({ pending: '等待中', running: '正在调用', completed: '已完成', skipped: '已跳过', retrying: '重试中', failed: '失败' }[status] || status)

const upsertAgent = (source, name, status = 'running') => {
  const safeName = name || (source === 'diagnosis' ? '诊断编码服务' : '手术编码服务')
  const key = `${source}:${safeName}`
  const existing = agentLogs.value.find((item) => item.key === key)
  if (existing) {
    if (existing.status !== 'failed') existing.status = status
    return existing
  }
  const entry = {
    key,
    source,
    name: safeName,
    displayName: safeName.includes('(无手术记录)') || safeName.includes('溯源') ? safeName : `智能体${agentLogs.value.length + 1}`,
    status,
  }
  agentLogs.value.push(entry)
  return entry
}

const completeRunningAgent = (source, exceptName = '') => {
  agentLogs.value.forEach((item) => {
    if (item.source === source && item.status === 'running' && item.name !== exceptName) {
      item.status = 'completed'
    }
  })
}

const findTableValue = (data) => {
  if (!data || typeof data !== 'object') return ''
  if (typeof data.table_md === 'string') return data.table_md
  if (typeof data.tableMd === 'string') return data.tableMd
  for (const key of ['result', 'message', 'data']) {
    const nested = data[key]
    if (nested && typeof nested === 'object') {
      const found = findTableValue(nested)
      if (found) return found
    }
  }
  return ''
}

const cleanAgentOutput = (content = '') =>
  String(content)
    .replace(/<think>[\s\S]*?<\/think>/g, '')
    .replace(/```(?:json)?|```/gi, '')
    .trim()

const parseAgentOutput = (content = '') => {
  const cleaned = cleanAgentOutput(content)
  if (!cleaned) return null
  try {
    return JSON.parse(cleaned)
  } catch (_) {
    const objectStart = cleaned.indexOf('{')
    const objectEnd = cleaned.lastIndexOf('}')
    if (objectStart >= 0 && objectEnd > objectStart) {
      try {
        return JSON.parse(cleaned.slice(objectStart, objectEnd + 1))
      } catch (_) {}
    }
    const arrayStart = cleaned.indexOf('[')
    const arrayEnd = cleaned.lastIndexOf(']')
    if (arrayStart >= 0 && arrayEnd > arrayStart) {
      try {
        return JSON.parse(cleaned.slice(arrayStart, arrayEnd + 1))
      } catch (_) {}
    }
  }
  return cleaned
}

const extractAgentItems = (content = '') => {
  const parsed = parseAgentOutput(content)
  const items = []
  const pushItem = (value) => {
    const text = String(value ?? '').trim()
    if (text && !items.includes(text)) items.push(text)
  }
  const walk = (value, label = '') => {
    if (items.length >= 40 || value === null || value === undefined) return
    if (Array.isArray(value)) {
      if (value.every((item) => ['string', 'number', 'boolean'].includes(typeof item))) {
        if (value.length === 2 && label && /编码|名称|诊断|手术|病理|损伤|中毒/.test(label)) {
          pushItem(`${label}：${value.join(' / ')}`)
          return
        }
        value.forEach((item) => pushItem(label ? `${label}：${item}` : item))
        return
      }
      value.forEach((item) => walk(item, label))
      return
    }
    if (typeof value === 'object') {
      Object.entries(value).forEach(([key, nested]) => walk(nested, key))
      return
    }
    if (typeof value === 'string' && !label) {
      value
        .split(/\r?\n/)
        .map((line) => line.replace(/^[-*\d.、\s]+/, '').trim())
        .filter(Boolean)
        .forEach(pushItem)
      return
    }
    pushItem(label ? `${label}：${value}` : value)
  }
  walk(parsed)
  return items.slice(0, 40)
}

const createAbortError = () => {
  const error = new Error('请求已取消')
  error.name = 'AbortError'
  return error
}

const waitForPresetStage = (signal, minDelay = 700, maxDelay = 1400) =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(createAbortError())
      return
    }
    const delay = Math.round(minDelay + Math.random() * (maxDelay - minDelay))
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', handleAbort)
      resolve()
    }, delay)
    const handleAbort = () => {
      window.clearTimeout(timer)
      signal?.removeEventListener('abort', handleAbort)
      reject(createAbortError())
    }
    signal?.addEventListener('abort', handleAbort, { once: true })
  })

const runPresetStageWithTimeout = (signal) =>
  new Promise((resolve, reject) => {
    let settled = false
    const timeout = window.setTimeout(() => {
      if (settled) return
      settled = true
      reject(new Error('预置智能体阶段超时'))
    }, 3000)

    waitForPresetStage(signal).then(
      () => {
        if (settled) return
        settled = true
        window.clearTimeout(timeout)
        resolve()
      },
      (error) => {
        if (settled) return
        settled = true
        window.clearTimeout(timeout)
        reject(error)
      }
    )
  })

const presetCodePairs = (names = [], codes = []) =>
  names.map((name, index) => `${name}（${codes[index] || '无编码'}）`)

const buildPresetTable = (source, preset, caseId) => {
  if (source === 'diagnosis') {
    const evidenceMap = preset.disease_evidence_map || {}
    const rows = [
      [
        caseId,
        preset.main_diagnosis_name,
        preset.main_diagnosis_icd,
        '-',
        evidenceMap[preset.main_diagnosis_name] || '',
        '主诊断编码',
      ],
      ...(preset.other_diagnosis_names || []).map((name, index) => [
        caseId,
        name,
        preset.other_diagnosis_icds?.[index] || '',
        '-',
        evidenceMap[name] || '',
        '其他诊断编码',
      ]),
    ]
    if (preset.disease_bingli_name || preset.disease_bingli_icd) {
      const code = preset.disease_bingli_icd || ''
      rows.push([
        caseId,
        preset.disease_bingli_name || '',
        code,
        '-',
        evidenceMap[preset.disease_bingli_name] || '',
        /^[M]/i.test(code) ? '病理诊断编码' : '其他编码',
      ])
    }
    return {
      headers: ['病案标识号', '诊断名称', '诊断编码', '是否并发症', '依据', '编码类型'],
      rows,
    }
  }

  const evidenceMap = preset.surgery_evidence_map || {}
  return {
    headers: ['病案标识号', '手术名称', '手术编码', '是否四级', '是否微创', '依据', '编码类型'],
    rows: [
      [
        caseId,
        preset.main_surgery_name,
        preset.main_surgery_icd,
        '-',
        '-',
        evidenceMap[preset.main_surgery_name] || '',
        '主手术编码',
      ],
      ...(preset.other_surgery_names || []).map((name, index) => [
        caseId,
        name,
        preset.other_surgery_icds?.[index] || '',
        '-',
        '-',
        evidenceMap[name] || '',
        '其他手术编码',
      ]),
    ],
  }
}

const buildPresetStages = (source, preset) => {
  if (source === 'diagnosis') {
    const names = [preset.main_diagnosis_name, ...(preset.other_diagnosis_names || [])]
    const pairs = presetCodePairs(
      names,
      [preset.main_diagnosis_icd, ...(preset.other_diagnosis_icds || [])]
    )
    return [
      { name: '疾病信息抽取智能体', items: names },
      { name: '疾病标准化智能体', items: names },
      { name: '疾病编码检索智能体', items: pairs },
      {
        name: '主要诊断排序智能体',
        items: [`主要诊断：${preset.main_diagnosis_name}`, ...names.slice(1).map((name) => `其他诊断：${name}`)],
      },
      { name: '疾病筛查智能体', items: names.map((name) => `保留：${name}`) },
      { name: '疾病溯源智能体', items: pairs },
    ]
  }

  const names = [preset.main_surgery_name, ...(preset.other_surgery_names || [])]
  const pairs = presetCodePairs(
    names,
    [preset.main_surgery_icd, ...(preset.other_surgery_icds || [])]
  )
  return [
    { name: '手术信息抽取智能体', items: names },
    { name: '手术标准化智能体', items: names },
    { name: '手术补充智能体', items: names.map((name) => `识别：${name}`) },
    { name: '主要手术排序智能体', items: [`主要手术：${preset.main_surgery_name}`, ...names.slice(1).map((name) => `其他手术：${name}`)] },
    { name: '手术筛查智能体', items: names.map((name) => `保留：${name}`) },
    { name: '手术编码与溯源智能体', items: pairs },
  ]
}

const requestPresetModel = async (source, preset, caseId, signal) => {
  const stages = buildPresetStages(source, preset)
  stages.forEach((stage) => upsertAgent(source, stage.name, 'pending'))

  try {
    for (const stage of stages) {
      if (signal?.aborted) throw createAbortError()
      const entry = upsertAgent(source, stage.name, 'running')
      try {
        await runPresetStageWithTimeout(signal)
        entry.status = 'completed'
      } catch (error) {
        entry.status = error?.name === 'AbortError' ? 'pending' : 'failed'
        throw error
      }
    }
  } finally {
    if (!signal?.aborted) completeRunningAgent(source)
  }

  return {
    table: buildPresetTable(source, preset, caseId),
    details: stages.map((stage) => ({
      key: `${source}:${stage.name}`,
      source,
      name: stage.name,
      items: stage.items,
    })),
    resultSource: 'preset_demo',
  }
}

const requestModel = async (source, prompt, signal) => {
  const endpoint =
    source === 'diagnosis'
      ? '/diag/qwen3/diagnosis_qwen'
      : '/sur/qwen3/surgeries_diagnosis'
  const buffers = new Map()
  const agentOrder = []
  let currentAgent = ''
  let streamFailure = ''

  const rememberAgent = (name) => {
    if (name && !agentOrder.includes(name)) agentOrder.push(name)
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      model: 'my_model',
      token: '',
      messages: [{ role: 'user', content: prompt }],
      history: [],
    }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`${source === 'diagnosis' ? '诊断' : '手术'}模型服务返回 ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''

  const handleEvent = (data) => {
    if (data.type === 'agent_status') {
      completeRunningAgent(source, data.agent_name)
      currentAgent = data.agent_name || currentAgent
      rememberAgent(currentAgent)
      upsertAgent(source, currentAgent, data.status || 'running')
      return
    }
    if (data.error || data.type === 'error') {
      upsertAgent(source, data.agent_name || currentAgent, 'failed')
      streamFailure = data.error || (typeof data.message === 'string' ? data.message : '模型处理失败')
      return
    }

    const agentName = data.agent_name || currentAgent || `${source === 'diagnosis' ? '诊断' : '手术'}编码服务`
    if (agentName !== currentAgent) {
      completeRunningAgent(source, agentName)
      currentAgent = agentName
    }
    rememberAgent(agentName)
    upsertAgent(source, agentName, 'running')

    const directTable = findTableValue(data)
    if (directTable) buffers.set(`${agentName}:table`, directTable)
    const content = data.message?.content
    if (content) buffers.set(agentName, (buffers.get(agentName) || '') + content)
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    pending += decoder.decode(value, { stream: true })
    const lines = pending.split('\n')
    pending = lines.pop() || ''
    for (const rawLine of lines) {
      const line = rawLine.trim().replace(/^data:\s*/, '')
      if (!line || line === '[DONE]') continue
      try {
        handleEvent(JSON.parse(line))
      } catch (_) {
        // A partial stream line remains in pending and is retried with the next chunk.
      }
    }
  }
  if (pending.trim()) {
    try {
      handleEvent(JSON.parse(pending.trim().replace(/^data:\s*/, '')))
    } catch (_) {}
  }

  if (streamFailure) throw new Error(streamFailure)
  completeRunningAgent(source)
  const details = agentOrder
    .filter((agentName) => !/表格展示/.test(agentName))
    .map((agentName) => ({
      key: `${source}:${agentName}`,
      source,
      name: agentName,
      items: extractAgentItems(buffers.get(agentName) || ''),
    }))
  const candidates = Array.from(buffers.values()).reverse()
  for (const candidate of candidates) {
    const table = parseMarkdownTable(candidate)
    if (table.rows.length) return { table, details }
  }
  return { table: { headers: [], rows: [] }, details }
}

const placePrimaryCodesFirst = (result) => {
  if (!result?.rows?.length) return result
  const typeIndex = result.headers.findIndex(
    (header) => cleanCell(header) === '编码类型'
  )
  if (typeIndex < 0) return result
  const primaryRows = []
  const otherRows = []
  result.rows.forEach((row) => {
    if (/主诊断|主手术/.test(row[typeIndex] || '')) primaryRows.push(row)
    else otherRows.push(row)
  })
  return { ...result, rows: [...primaryRows, ...otherRows] }
}

const startCoding = async () => {
  if (!record.value['病案标识号'] && !record.value['住院号']) {
    ElMessage.warning('请先填写病案标识号或住院号')
    return
  }

  activeController?.abort()
  activeController = new AbortController()
  const controller = activeController
  dialogVisible.value = true
  isCoding.value = true
  requestError.value = ''
  finishedAt.value = ''
  agentLogs.value = []
  processDetails.value = []
  showProcessDetails.value = false
  diagnosisResult.value = { headers: [], rows: [] }
  surgeryResult.value = { headers: [], rows: [] }
  selectedRows.value = { diagnosis: [], surgery: [] }
  acceptedResultCount.value = 0
  activeResultTab.value = 'diagnosis'

  const prompt = JSON.stringify(record.value, null, 2)
  const presetMatch = findPresetCase(record.value)
  const inpatientNo = presetMatch?.inpatientNo || String(record.value['住院号'] || '').trim()
  const presetCase = presetMatch?.presetCase
  const caseId = String(record.value['病案标识号'] || inpatientNo).trim()
  const requests = [
    presetCase
      ? requestPresetModel('diagnosis', presetCase.disease, caseId, controller.signal)
      : requestModel('diagnosis', prompt, controller.signal),
    requestModel('surgery', prompt, controller.signal),
  ]

  if (presetCase) {
    console.info(`[HIS preset_demo] 住院号 ${inpatientNo} 使用预置编码结果`)
    appendOperationLog('preset_coding_started', {
      case_id: caseId,
      inpatient_no: inpatientNo,
      result_source: 'preset_demo',
    })
  }

  const [diagnosis, surgery] = await Promise.allSettled(requests)
  if (diagnosis.status === 'fulfilled') {
    diagnosisResult.value = placePrimaryCodesFirst(diagnosis.value.table)
    processDetails.value.push(...diagnosis.value.details)
  }
  if (surgery.status === 'fulfilled') {
    surgeryResult.value = placePrimaryCodesFirst(surgery.value.table)
    processDetails.value.push(...surgery.value.details)
  }
  selectedRows.value = {
    diagnosis: diagnosisResult.value.rows.map((_, index) => index),
    surgery: surgeryResult.value.rows.map((_, index) => index),
  }

  const errors = [diagnosis, surgery]
    .filter((item) => item.status === 'rejected' && item.reason?.name !== 'AbortError')
    .map((item) => item.reason?.message || '模型调用失败')
  if (errors.length) requestError.value = errors.join('；')
  if (!hasResults.value && !errors.length && !controller.signal.aborted) {
    requestError.value = '模型调用完成，但未解析到最终编码表格。'
  }

  if (!controller.signal.aborted) {
    finishedAt.value = new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date())
  }
  isCoding.value = false
  if (activeController === controller) activeController = null
}

const handleCodingButtonClick = () => {
  if (dialogMinimized.value) {
    restoreCodingDialog()
    return
  }
  startCoding()
}

const cancelCoding = () => {
  activeController?.abort()
  activeController = null
  isCoding.value = false
  requestError.value = '本次智能编码已停止。'
}

const appendOperationLog = (action, details = {}) => {
  const storageKey = 'his-aicode-operation-logs'
  let logs = []
  try {
    logs = JSON.parse(localStorage.getItem(storageKey) || '[]')
    if (!Array.isArray(logs)) logs = []
  } catch (_) {
    logs = []
  }
  logs.push({
    action,
    medRecordId: record.value['病案标识号'] || record.value['住院号'] || '',
    operator: '编码演示账号',
    timestamp: new Date().toISOString(),
    ...details,
  })
  localStorage.setItem(storageKey, JSON.stringify(logs.slice(-200)))
}

const getResultByMode = (mode) =>
  mode === 'diagnosis' ? diagnosisResult.value : surgeryResult.value

const toggleResultRow = (mode, { index, checked }) => {
  const next = new Set(selectedRows.value[mode])
  if (checked) next.add(index)
  else next.delete(index)
  selectedRows.value[mode] = [...next].sort((a, b) => a - b)
}

const toggleAllRows = (mode, checked) => {
  const rows = getResultByMode(mode).rows
  selectedRows.value[mode] = checked ? rows.map((_, index) => index) : []
}

const primaryTypeConfig = {
  diagnosis: {
    primary: '主诊断编码',
    other: '其他诊断编码',
    eligible: /^(主诊断编码|其他诊断编码)$/,
  },
  surgery: {
    primary: '主手术编码',
    other: '其他手术编码',
    eligible: /^(主手术编码|其他手术编码)$/,
  },
}

const updatePrimaryCodeByFirstRow = (mode, result, rows) => {
  const typeIndex = result.headers.findIndex((header) => cleanCell(header) === '编码类型')
  if (typeIndex < 0 || !rows.length) return true
  const config = primaryTypeConfig[mode]
  const firstType = cleanCell(rows[0][typeIndex])
  if (!config.eligible.test(firstType)) {
    ElMessage.warning(
      mode === 'diagnosis'
        ? '病理或外因编码不能设置为主要诊断'
        : '另编码不能设置为主要手术'
    )
    return false
  }
  rows.forEach((row, index) => {
    const type = cleanCell(row[typeIndex])
    if (config.eligible.test(type)) {
      row[typeIndex] = index === 0 ? config.primary : config.other
    }
  })
  return true
}

const moveResultRow = (mode, { fromIndex, toIndex }) => {
  const result = getResultByMode(mode)
  if (
    fromIndex === toIndex ||
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= result.rows.length ||
    toIndex >= result.rows.length
  ) return

  const rows = [...result.rows]
  const selectedRowObjects = selectedRows.value[mode]
    .map((index) => result.rows[index])
    .filter(Boolean)
  const [movedRow] = rows.splice(fromIndex, 1)
  rows.splice(toIndex, 0, movedRow)
  if (!updatePrimaryCodeByFirstRow(mode, result, rows)) return
  result.rows = rows
  selectedRows.value[mode] = rows
    .map((row, index) => (selectedRowObjects.includes(row) ? index : -1))
    .filter((index) => index >= 0)
  appendOperationLog('拖动排序', {
    category: mode,
    from: fromIndex + 1,
    to: toIndex + 1,
  })
}

const collectSelectedResults = () => {
  const collect = (mode) => {
    const result = getResultByMode(mode)
    return selectedRows.value[mode].map((index) => {
      const row = result.rows[index]
      return Object.fromEntries(result.headers.map((header, column) => [cleanCell(header), row[column]]))
    })
  }
  return {
    diagnosis: collect('diagnosis'),
    surgery: collect('surgery'),
  }
}

const dispatchHisWriteback = (scope) => {
  const selected = collectSelectedResults()
  const count = selected.diagnosis.length + selected.surgery.length
  const payload = {
    type: 'AICODE_APPLY_RESULTS',
    scope,
    medRecordId: record.value['病案标识号'] || record.value['住院号'],
    selected,
    timestamp: new Date().toISOString(),
  }

  window.dispatchEvent(new CustomEvent('aicode:apply-results', { detail: payload }))
  if (window.parent && window.parent !== window) {
    window.parent.postMessage(payload, '*')
  }
  writebackResults.value = {
    diagnosis: selected.diagnosis.map((item) => ({ ...item })),
    surgery: selected.surgery.map((item) => ({ ...item })),
  }
  activeRecordTab.value = 'coding-results'
  acceptedResultCount.value = count
  appendOperationLog(scope === 'all' ? '全部采纳' : '部分采纳', {
    diagnosisCount: selected.diagnosis.length,
    surgeryCount: selected.surgery.length,
  })
  ElMessage.success(`已采纳并回写 ${count} 条编码`)
}

const removeWritebackItem = (mode, index) => {
  writebackResults.value[mode].splice(index, 1)
  acceptedResultCount.value = writebackTotal.value
  appendOperationLog('移除已写回编码', { category: mode, index: index + 1 })
}

const clearWritebackResults = () => {
  writebackResults.value = { diagnosis: [], surgery: [] }
  acceptedResultCount.value = 0
  appendOperationLog('清空已写回编码')
  ElMessage.success('已清空编码填写结果')
}

const applyCurrentSelection = () => {
  if (!selectedResultCount.value) {
    ElMessage.warning('请先选择需要采纳的编码')
    return
  }
  dispatchHisWriteback(allResultsSelected.value ? 'all' : 'selected')
}

const persistDialogGeometry = () => {
  if (dialogFullscreen.value) return
  const element = document.querySelector('.coding-dialog')
  if (!element) return
  const geometry = {
    width: element.style.width || `${element.getBoundingClientRect().width}px`,
    height: element.style.height || `${element.getBoundingClientRect().height}px`,
    transform: element.style.transform || '',
  }
  localStorage.setItem('his-aicode-dialog-geometry', JSON.stringify(geometry))
  localStorage.setItem('his-aicode-dialog-width', geometry.width)
}

const restoreDialogGeometry = async () => {
  await nextTick()
  const element = document.querySelector('.coding-dialog')
  if (!element || dialogFullscreen.value) return
  try {
    const geometry = JSON.parse(localStorage.getItem('his-aicode-dialog-geometry') || '{}')
    if (geometry.width) element.style.width = geometry.width
    if (geometry.height) element.style.height = geometry.height
    if (geometry.transform) element.style.transform = geometry.transform
  } catch (_) {}
  element.onmouseup = persistDialogGeometry
}

const toggleDialogFullscreen = async () => {
  const enteringFullscreen = !dialogFullscreen.value
  if (enteringFullscreen) persistDialogGeometry()
  dialogFullscreen.value = enteringFullscreen
  await nextTick()
  const element = document.querySelector('.coding-dialog')
  if (enteringFullscreen && element) {
    element.style.width = ''
    element.style.height = ''
    element.style.transform = ''
  } else if (!enteringFullscreen) {
    restoreDialogGeometry()
  }
  appendOperationLog(enteringFullscreen ? '最大化窗口' : '还原窗口')
}

const minimizeCodingDialog = () => {
  persistDialogGeometry()
  dialogMinimized.value = true
  dialogVisible.value = false
  appendOperationLog('最小化窗口')
}

const restoreCodingDialog = () => {
  dialogMinimized.value = false
  dialogVisible.value = true
  appendOperationLog('恢复窗口')
}

const closeCodingDialog = () => {
  persistDialogGeometry()
  dialogVisible.value = false
  dialogMinimized.value = false
}

const ignoreRecommendations = () => {
  if (isCoding.value) cancelCoding()
  appendOperationLog('忽略推荐', { resultCount: resultTotal.value })
  closeCodingDialog()
  ElMessage.info('已忽略本次智能编码推荐')
}

const copyResultCodes = async () => {
  const collectLines = (result, label) => {
    const nameIndex = result.headers.findIndex((header) => /名称/.test(header))
    const codeIndex = result.headers.findIndex(
      (header) => /^(诊断编码|手术编码)$/.test(String(header).replace(/\*\*/g, '').trim())
    )
    if (codeIndex < 0) return []
    return result.rows.map(
      (row) => `${label}\t${row[nameIndex] || '-'}\t${row[codeIndex] || '-'}`
    )
  }
  const text = [
    ...collectLines(diagnosisResult.value, '疾病诊断'),
    ...collectLines(surgeryResult.value, '手术操作'),
  ].join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('编码结果已复制')
  } catch (_) {
    ElMessage.error('复制失败，请重试')
  }
}

const normalizeOcrKey = (key = '') =>
  String(key).trim().toLowerCase().replace(/[\s_-]/g, '')

const ocrValueToText = (value) => {
  if (value === null || value === undefined) return ''
  if (Array.isArray(value)) return value.map(ocrValueToText).filter(Boolean).join('；')
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value).trim()
}

const parseOcrContent = (content) => {
  if (content && typeof content === 'object' && !Array.isArray(content)) return content
  if (typeof content !== 'string') return null
  const cleaned = content.replace(/```(?:json)?|```/gi, '').trim()
  try {
    const parsed = JSON.parse(cleaned)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null
  } catch (_) {
    const start = cleaned.indexOf('{')
    const end = cleaned.lastIndexOf('}')
    if (start >= 0 && end > start) {
      try {
        const parsed = JSON.parse(cleaned.slice(start, end + 1))
        return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null
      } catch (_) {}
    }
  }
  return null
}

const resetCodingSessionForNewRecord = () => {
  activeController?.abort()
  activeController = null
  isCoding.value = false
  dialogVisible.value = false
  dialogMinimized.value = false
  dialogFullscreen.value = false
  diagnosisResult.value = { headers: [], rows: [] }
  surgeryResult.value = { headers: [], rows: [] }
  selectedRows.value = { diagnosis: [], surgery: [] }
  agentLogs.value = []
  processDetails.value = []
  showProcessDetails.value = false
  activeResultTab.value = 'diagnosis'
  requestError.value = ''
  finishedAt.value = ''
  writebackResults.value = { diagnosis: [], surgery: [] }
  acceptedResultCount.value = 0
}

const applyOcrFields = (ocrData) => {
  const nextRecord = createEmptyRecord()
  const entries = Object.entries(ocrData)
  const normalizedEntries = new Map(
    entries.map(([key, value]) => [normalizeOcrKey(key), { key, value }])
  )
  const consumedKeys = new Set()

  Object.entries(OCR_FIELD_ALIASES).forEach(([targetField, aliases]) => {
    for (const alias of aliases) {
      const matched = normalizedEntries.get(normalizeOcrKey(alias))
      const value = ocrValueToText(matched?.value)
      if (!value) continue
      nextRecord[targetField] = value
      consumedKeys.add(matched.key)
      break
    }
  })

  // Keep OCR fields that are not shown in the simplified form for model coding.
  entries.forEach(([key, value]) => {
    const text = ocrValueToText(value)
    if (!consumedKeys.has(key) && text) nextRecord[key] = text
  })

  fillMissingPatientInfo(nextRecord)

  resetCodingSessionForNewRecord()
  record.value = nextRecord
  ocrFilledCount.value = Object.values(nextRecord).filter(
    (value) => String(value || '').trim()
  ).length
  activeRecordTab.value = 'summary'
}

const stopOcrProgressTimer = () => {
  if (ocrProgressTimer) {
    clearInterval(ocrProgressTimer)
    ocrProgressTimer = null
  }
}

const processPdfWithOcr = async (file) => {
  ocrController?.abort()
  const controller = new AbortController()
  ocrController = controller
  ocrDialogVisible.value = true
  ocrProcessing.value = true
  ocrProgress.value = 8
  ocrStepIndex.value = 0
  ocrFileName.value = file.name
  ocrError.value = ''
  ocrSuccess.value = false
  ocrFilledCount.value = 0

  stopOcrProgressTimer()
  ocrProgressTimer = setInterval(() => {
    if (ocrProgress.value < 82) ocrProgress.value += 2
    if (ocrProgress.value >= 26 && ocrStepIndex.value < 1) ocrStepIndex.value = 1
    if (ocrProgress.value >= 58 && ocrStepIndex.value < 2) ocrStepIndex.value = 2
  }, 700)

  let timedOut = false
  const timeoutId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, 240000)

  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch('/ocr/ocr', {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`OCR 服务返回 ${response.status}${errorText ? `：${errorText}` : ''}`)
    }
    const result = await response.json()
    if (result.error) throw new Error(result.error)
    const ocrData = parseOcrContent(result?.data?.content)
    if (!ocrData) throw new Error('OCR 未返回可用的结构化病历字段')

    ocrProgress.value = 91
    ocrStepIndex.value = 3
    applyOcrFields(ocrData)
    ocrProgress.value = 100
    ocrSuccess.value = true
    ElMessage.success(`病历识别完成，已填写 ${ocrFilledCount.value} 个字段`)
  } catch (error) {
    if (error.name === 'AbortError' && !timedOut) return
    ocrError.value = timedOut ? 'OCR 识别超时，请稍后重试' : error.message || 'PDF 识别失败'
    ElMessage.error(ocrError.value)
  } finally {
    clearTimeout(timeoutId)
    stopOcrProgressTimer()
    if (ocrController === controller) ocrController = null
    ocrProcessing.value = false
  }
}

const handlePdfSelected = (uploadFile) => {
  const file = uploadFile?.raw
  pdfUploadRef.value?.clearFiles()
  if (!file) return
  const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name)
  if (!isPdf) {
    ElMessage.error('请上传 PDF 格式的病历文件')
    return
  }
  if (file.size > 13 * 1024 * 1024) {
    ElMessage.error('PDF 文件不能超过 13MB')
    return
  }
  if (!file.size) {
    ElMessage.error('PDF 文件内容为空')
    return
  }
  processPdfWithOcr(file)
}

const cancelOcr = () => {
  ocrController?.abort()
  ocrController = null
  stopOcrProgressTimer()
  ocrProcessing.value = false
  ocrDialogVisible.value = false
}

const resetDemo = () => {
  resetCodingSessionForNewRecord()
  record.value = createDemoRecord()
  activeRecordTab.value = 'summary'
  ElMessage.success('已恢复示例病历')
}
</script>

<style scoped>
:global(body) {
  margin: 0;
  min-width: 320px;
  color: #24313d;
  background: #eef2f5;
  font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
}

.his-page {
  width: 100%;
  min-height: calc(100vh - 130px);
  background: #eef2f5;
  letter-spacing: 0;
}

.his-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  color: #fff;
  background: #075985;
  box-shadow: 0 2px 8px rgb(15 23 42 / 16%);
}

.brand-block,
.patient-primary,
.patient-meta,
.header-user,
.dialog-heading,
.record-actions,
.progress-summary,
.result-heading {
  display: flex;
  align-items: center;
}

.brand-block {
  width: 248px;
  gap: 10px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  color: #075985;
  background: #fff;
  border-radius: 4px;
  font-weight: 800;
  font-size: 20px;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
}

.brand-system {
  margin-top: 2px;
  color: #cce8f5;
  font-size: 12px;
}

.his-nav {
  align-self: stretch;
  display: flex;
  gap: 2px;
}

.his-nav button {
  min-width: 98px;
  padding: 0 16px;
  color: #d7edf7;
  background: transparent;
  border: 0;
  border-bottom: 3px solid transparent;
  font-size: 14px;
  cursor: pointer;
}

.his-nav button:hover,
.his-nav button.active {
  color: #fff;
  background: rgb(255 255 255 / 8%);
  border-bottom-color: #67e8f9;
}

.header-user {
  margin-left: auto;
  gap: 7px;
  color: #d7edf7;
  font-size: 13px;
}

.patient-list-page {
  min-height: calc(100vh - 64px);
  padding: 22px 24px 32px;
}

.patient-list-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin: 0 auto 18px;
  max-width: 1500px;
}

.page-eyebrow {
  color: #26728f;
  font-size: 12px;
  font-weight: 700;
}

.patient-list-heading h1 {
  margin: 4px 0 5px;
  color: #173c53;
  font-size: 24px;
}

.patient-list-heading p {
  margin: 0;
  color: #75858f;
  font-size: 13px;
}

.patient-list-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.patient-list-search {
  width: 300px;
}

.patient-list-panel {
  max-width: 1500px;
  margin: 0 auto;
  overflow: hidden;
  background: #fff;
  border: 1px solid #d5dfe4;
  border-radius: 4px;
}

.patient-list-summary {
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  color: #73838d;
  background: #f6f9fa;
  border-bottom: 1px solid #dce4e8;
  font-size: 12px;
}

.patient-list-summary > div {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.patient-list-summary strong {
  color: #0c6f96;
  font-size: 22px;
}

.patient-management-table :deep(th.el-table__cell) {
  color: #294d5e;
  background: #edf4f6;
  font-weight: 700;
}

.patient-management-table :deep(td.el-table__cell) {
  color: #40545f;
}

.patient-table-name {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.patient-table-name span {
  color: #203f4f;
  font-size: 14px;
  font-weight: 700;
}

.patient-table-name small {
  color: #81909a;
  font-size: 11px;
}

.patient-record-number {
  color: #315c6f;
  font-family: Consolas, "Courier New", monospace;
  font-weight: 600;
}

.patient-list-panel :deep(.el-empty) {
  min-height: 360px;
}

.patient-strip {
  min-height: 72px;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #dce3e8;
}

.patient-primary {
  gap: 10px;
}

.patient-name {
  font-size: 20px;
  font-weight: 700;
  color: #172b3a;
}

.patient-meta {
  flex: 1;
  flex-wrap: wrap;
  gap: 10px 24px;
  color: #60707c;
  font-size: 13px;
}

.coding-button {
  min-width: 142px;
  height: 40px;
  border-radius: 4px;
  font-weight: 600;
}

.patient-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.patient-actions :deep(.el-upload),
.patient-actions :deep(.el-button) {
  height: 40px;
}

.writeback-notice {
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  color: #246249;
  background: #edf8f3;
  border-bottom: 1px solid #c5e5d7;
  font-size: 12px;
}

.writeback-notice button {
  margin-left: auto;
  padding: 4px 8px;
  color: #28775a;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.coding-mini-window {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2100;
  width: 330px;
  min-height: 66px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #244555;
  background: #fff;
  border: 1px solid #b9d2dc;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgb(26 62 82 / 20%);
  cursor: pointer;
  text-align: left;
}

.mini-window-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: #fff;
  background: #087aa5;
  border-radius: 5px;
  font-size: 20px;
}

.coding-mini-window strong,
.coding-mini-window small {
  display: block;
}

.coding-mini-window strong {
  font-size: 13px;
}

.coding-mini-window small {
  margin-top: 4px;
  color: #7a8994;
  font-size: 11px;
}

.mini-window-action {
  color: #08749b;
  font-size: 12px;
}

.ocr-dialog-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ocr-dialog-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex: 0 0 40px;
  color: #fff;
  background: #087aa5;
  border-radius: 4px;
  font-size: 22px;
}

.ocr-dialog-heading h2 {
  margin: 0;
  color: #193b50;
  font-size: 17px;
}

.ocr-dialog-heading p {
  max-width: 360px;
  margin: 4px 0 0;
  overflow: hidden;
  color: #778691;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ocr-progress-area {
  padding: 4px 2px 8px;
}

.ocr-progress-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 9px;
  color: #445d6a;
  font-size: 13px;
}

.ocr-progress-status strong {
  color: #08779f;
  font-family: Consolas, "Courier New", monospace;
}

.ocr-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-top: 24px;
}

.ocr-step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  color: #9aa5ab;
  font-size: 11px;
}

.ocr-step::before {
  position: absolute;
  top: 11px;
  right: 50%;
  left: -50%;
  height: 2px;
  content: '';
  background: #dfe5e8;
}

.ocr-step:first-child::before {
  display: none;
}

.ocr-step > span {
  position: relative;
  z-index: 1;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  color: #829099;
  background: #edf1f3;
  border: 1px solid #d5dde1;
  border-radius: 50%;
  font-size: 10px;
}

.ocr-step.active {
  color: #0b6e94;
  font-weight: 600;
}

.ocr-step.active > span {
  color: #fff;
  background: #1680a8;
  border-color: #1680a8;
  box-shadow: 0 0 0 4px rgb(22 128 168 / 12%);
}

.ocr-step.completed {
  color: #35745d;
}

.ocr-step.completed::before,
.ocr-step.completed > span {
  background: #2c9a72;
  border-color: #2c9a72;
  color: #fff;
}

.ocr-step.failed > span {
  color: #fff;
  background: #d84d4d;
  border-color: #d84d4d;
}

.ocr-success-message,
.ocr-error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 22px;
  padding: 12px;
  border-radius: 4px;
}

.ocr-success-message {
  color: #246249;
  background: #edf8f3;
  border: 1px solid #c5e5d7;
}

.ocr-error-message {
  color: #9c3f3f;
  background: #fff2f2;
  border: 1px solid #efcccc;
}

.ocr-success-message > .el-icon,
.ocr-error-message > .el-icon {
  flex: 0 0 auto;
  font-size: 21px;
}

.ocr-success-message div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ocr-success-message strong {
  font-size: 13px;
}

.ocr-success-message span {
  color: #5d7b6e;
  font-size: 11px;
}

.his-workspace {
  min-height: calc(100vh - 137px);
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
}

.patient-panel,
.record-panel {
  background: #fff;
  border: 1px solid #dce3e8;
  border-radius: 4px;
}

.patient-panel {
  padding-bottom: 18px;
}

.panel-title {
  padding: 14px 18px;
  border-bottom: 1px solid #e5e9ed;
  color: #173c53;
  font-size: 15px;
  font-weight: 700;
}

.patient-panel :deep(.el-form) {
  padding: 16px 18px 0;
}

.patient-panel :deep(.el-form-item) {
  margin-bottom: 14px;
}

.patient-panel :deep(.el-select),
.patient-panel :deep(.el-date-editor) {
  width: 100%;
}

.two-column-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 10px;
}

.record-panel {
  min-width: 0;
  padding: 0 22px 24px;
}

.record-toolbar {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e9ed;
}

.record-toolbar h1 {
  margin: 0 0 5px;
  color: #173c53;
  font-size: 19px;
}

.record-toolbar span {
  color: #7a8994;
  font-size: 12px;
}

.record-actions {
  gap: 8px;
}

.record-tabs {
  margin-top: 5px;
}

.writeback-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.writeback-tab-label strong {
  min-width: 20px;
  padding: 0 6px;
  color: #fff;
  background: #1680a8;
  border-radius: 10px;
  font-size: 10px;
  line-height: 18px;
  text-align: center;
}

.writeback-workspace {
  padding: 12px 0 6px;
}

.writeback-heading {
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 2px 14px;
  border-bottom: 1px solid #e2e8ec;
}

.writeback-heading h2 {
  margin: 0 0 5px;
  color: #214556;
  font-size: 16px;
}

.writeback-heading p {
  margin: 0;
  color: #7b8992;
  font-size: 12px;
}

.writeback-empty {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: #84939b;
  background: #fafcfd;
  border: 1px dashed #cedbe1;
  margin-top: 18px;
}

.writeback-empty .el-icon {
  color: #6f9daf;
  font-size: 32px;
}

.writeback-empty strong {
  color: #48616d;
  font-size: 14px;
}

.writeback-empty span {
  font-size: 12px;
}

.writeback-section {
  margin-top: 18px;
  border: 1px solid #d6e1e6;
}

.writeback-section-title {
  min-height: 42px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 14px;
  color: #294e5f;
  background: #f1f7f9;
  border-bottom: 1px solid #d6e1e6;
  font-size: 13px;
  font-weight: 700;
}

.writeback-section-title strong {
  color: #68808b;
  font-size: 11px;
  font-weight: 500;
}

.writeback-section :deep(.el-table) {
  --el-table-border-color: #d6e1e6;
  --el-table-header-bg-color: #f7fafb;
}

.writeback-section :deep(.el-table th.el-table__cell) {
  color: #365363;
  font-weight: 700;
}

.writeback-section :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #d4dfe4 inset;
}

.record-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  padding-top: 10px;
}

.record-field {
  min-width: 0;
}

.record-field.full-width {
  grid-column: 1 / -1;
}

.record-field label {
  display: block;
  margin-bottom: 7px;
  color: #344753;
  font-size: 13px;
  font-weight: 600;
}

.record-field :deep(textarea) {
  line-height: 1.75;
}

.dialog-heading {
  gap: 12px;
}

.dialog-brand-logo {
  width: 190px;
  height: 66px;
  display: block;
  flex: 0 0 190px;
  object-fit: contain;
}

.dialog-patient-summary {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px 16px;
  margin-left: 14px;
  padding-left: 18px;
  border-left: 1px solid #dce5e9;
  color: #5e707b;
  font-size: 12px;
}

.dialog-patient-summary strong {
  color: #1f3c4d;
  font-size: 14px;
}

.dialog-window-actions {
  display: flex;
  align-items: center;
  gap: 0;
  margin-left: 4px;
}

.dialog-window-actions button {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  color: #617782;
  background: transparent;
  border: 0;
  border-radius: 2px;
  cursor: pointer;
  line-height: 1;
}

.dialog-window-actions button:hover {
  color: #111a1e;
  background: #e9edef;
}

.dialog-window-actions .close-window:hover {
  color: #111a1e;
  background: #e9edef;
}

.dialog-window-actions .window-control {
  position: relative;
  width: 46px;
  height: 32px;
  padding: 0;
}

.dialog-window-actions .window-icon {
  position: relative;
  display: block;
  width: 14px;
  height: 14px;
  color: #182126;
}

.dialog-window-actions .window-icon-minimize::before {
  position: absolute;
  top: 7px;
  left: 1px;
  width: 12px;
  height: 1px;
  content: '';
  background: currentColor;
}

.dialog-window-actions .window-icon-maximize {
  width: 11px;
  height: 11px;
  border: 1px solid currentColor;
}

.dialog-window-actions .window-icon-close::before,
.dialog-window-actions .window-icon-close::after {
  position: absolute;
  top: 6px;
  left: 0;
  width: 14px;
  height: 1px;
  content: '';
  background: currentColor;
}

.dialog-window-actions .window-icon-close::before {
  transform: rotate(45deg);
}

.dialog-window-actions .window-icon-close::after {
  transform: rotate(-45deg);
}

.dialog-heading h2 {
  margin: 0;
  color: #193b50;
  font-size: 18px;
}

.dialog-heading p {
  margin: 4px 0 0;
  color: #778691;
  font-size: 12px;
}

.dialog-heading .el-tag {
  margin-left: auto;
  margin-right: 2px;
}

.coding-dialog-footer {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.selection-summary {
  color: #667984;
  font-size: 12px;
}

.selection-summary strong {
  color: #086b91;
  font-size: 17px;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.coding-progress {
  padding: 2px 2px 18px;
}

.progress-summary,
.result-heading {
  justify-content: space-between;
}

.progress-summary {
  margin-bottom: 9px;
  color: #455762;
  font-size: 13px;
}

.agent-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 18px;
}

.agent-column {
  border: 1px solid #dfe6ea;
  border-radius: 4px;
  overflow: hidden;
}

.agent-column-title {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 13px;
  color: #27495d;
  background: #f4f7f8;
  border-bottom: 1px solid #e4eaed;
  font-size: 13px;
  font-weight: 700;
}

.agent-list {
  max-height: 198px;
  overflow: auto;
}

.agent-row {
  min-height: 39px;
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 0 13px;
  border-bottom: 1px solid #edf0f2;
  font-size: 12px;
}

.agent-row:last-child {
  border-bottom: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a9b3ba;
}

.status-dot.running {
  background: #e6a23c;
  box-shadow: 0 0 0 4px rgb(230 162 60 / 13%);
}

.status-dot.completed {
  background: #16a06b;
}

.status-dot.failed {
  background: #d94b4b;
}

.agent-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #354853;
}

.agent-state {
  color: #81909a;
}

.agent-empty {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #87949d;
  font-size: 12px;
}

.result-area {
  padding-top: 4px;
}

.result-success-band {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  color: #215743;
  background: #f0f9f5;
  border: 1px solid #cbe9dc;
  border-radius: 4px;
}

.result-success-icon {
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  display: grid;
  place-items: center;
  color: #fff;
  background: #16845c;
  border-radius: 50%;
  font-size: 22px;
}

.result-success-copy {
  min-width: 0;
}

.result-success-copy h3 {
  margin: 0 0 4px;
  color: #174d38;
  font-size: 16px;
}

.result-success-copy span {
  color: #628073;
  font-size: 12px;
}

.result-success-band .result-actions {
  margin-left: auto;
}

.result-overview {
  min-height: 72px;
  display: flex;
  align-items: center;
  margin: 14px 0 4px;
  padding: 0 18px;
  background: #f7f9fa;
  border: 1px solid #e0e6e9;
  border-radius: 4px;
}

.overview-item {
  flex: 1;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 5px;
}

.overview-label {
  margin-right: 10px;
  color: #61717c;
  font-size: 12px;
}

.overview-item strong {
  color: #155f82;
  font-size: 25px;
  line-height: 1;
}

.overview-unit {
  color: #81909a;
  font-size: 12px;
}

.overview-divider {
  width: 1px;
  height: 32px;
  background: #dbe2e6;
}

.result-tabs :deep(.el-tabs__header) {
  margin: 16px 0 12px;
  border-bottom: 1px solid #d9e3e7;
}

.result-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  background: #0d789e;
}

.result-tabs :deep(.el-tabs__item) {
  height: 48px;
  padding: 0 22px;
  color: #62747e;
  font-weight: 600;
}

.result-tabs :deep(.el-tabs__item.is-active) {
  color: #075f82;
  background: #f1f8fa;
}

.result-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.result-tab-label strong {
  min-width: 23px;
  padding: 1px 7px;
  color: #4d6571;
  background: #e5ebee;
  border-radius: 10px;
  font-size: 11px;
  line-height: 19px;
  text-align: center;
}

.result-tabs :deep(.el-tabs__item.is-active) .result-tab-label strong {
  color: #fff;
  background: #1680a8;
}

.process-detail-panel {
  margin: 14px 0 16px;
  padding: 16px;
  background: #f8fafb;
  border: 1px solid #d9e3e8;
  border-radius: 4px;
}

.process-detail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 13px;
}

.process-detail-heading h4 {
  margin: 0 0 4px;
  color: #244555;
  font-size: 14px;
}

.process-detail-heading span {
  color: #7b8a93;
  font-size: 11px;
}

.process-agent-count {
  padding: 4px 8px;
  color: #416171 !important;
  background: #eaf1f4;
  border-radius: 3px;
  white-space: nowrap;
}

.process-source-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.process-source {
  min-width: 0;
  background: #fff;
  border: 1px solid #dce5e9;
  border-radius: 4px;
  overflow: hidden;
}

.process-source-title {
  min-height: 42px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  color: #315363;
  background: #edf4f6;
  border-bottom: 1px solid #dce5e9;
  font-size: 12px;
  font-weight: 700;
}

.process-source-title strong {
  min-width: 22px;
  margin-left: auto;
  padding: 1px 6px;
  text-align: center;
  color: #fff;
  background: #568092;
  border-radius: 10px;
  font-size: 10px;
}

.process-agent-list {
  max-height: 360px;
  overflow: auto;
}

.process-agent-item {
  padding: 12px;
  border-bottom: 1px solid #e8edef;
}

.process-agent-item:last-child {
  border-bottom: 0;
}

.process-agent-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #304a58;
  font-size: 12px;
  font-weight: 700;
}

.process-index {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  flex: 0 0 20px;
  color: #fff;
  background: #1680a8;
  border-radius: 50%;
  font-size: 10px;
}

.constructed-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px 4px;
  margin: 10px 0 0 28px;
  padding: 9px 10px;
  color: #3f5966;
  background: #f6f9fa;
  border: 1px solid #e0e8eb;
  border-radius: 3px;
  font-size: 11px;
  line-height: 1.55;
}

.constructed-item {
  display: inline-block;
  max-width: 100%;
  padding: 2px 6px;
  color: #315866;
  background: #fff;
  border: 1px solid #cfe0e6;
  border-radius: 3px;
  overflow-wrap: anywhere;
}

.list-bracket {
  color: #71909c;
  font-family: Consolas, "Courier New", monospace;
  font-size: 14px;
  font-weight: 700;
}

.list-separator {
  color: #8ca0a9;
  font-family: Consolas, "Courier New", monospace;
}

.constructed-empty,
.process-source-empty {
  color: #95a0a7;
  font-size: 11px;
}

.constructed-empty {
  margin: 9px 0 0 28px;
}

.process-source-empty {
  padding: 30px 12px;
  text-align: center;
}

.result-table-shell {
  border: 1px solid #dce4e8;
  border-radius: 4px;
  overflow: hidden;
}

.table-legend {
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 17px;
  padding: 0 12px;
  color: #71808a;
  background: #f6f9fa;
  border-bottom: 1px solid #e4eaed;
  font-size: 11px;
}

.table-section-name {
  margin-right: 8px;
  color: #294d5e;
  font-size: 12px;
}

.legend-main,
.legend-other {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-main::before,
.legend-other::before {
  width: 7px;
  height: 7px;
  content: '';
  border-radius: 50%;
}

.legend-main::before {
  background: #1676a3;
}

.legend-other::before {
  background: #a8b3ba;
}

.table-count {
  margin-left: auto;
}

.result-table-wrap {
  max-height: 430px;
  overflow: auto;
  background: #fff;
}

.coding-result-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #aebfc7;
  table-layout: fixed;
  color: #344b57;
  font-size: 12px;
}

.coding-result-table.diagnosis-result-table {
  min-width: 1060px;
}

.coding-result-table.surgery-result-table {
  min-width: 1500px;
}

.coding-result-table th,
.coding-result-table td {
  padding: 11px 12px;
  text-align: left;
  vertical-align: top;
  border: 1px solid #bccbd2;
  line-height: 1.6;
  transition: background-color 0.15s ease;
}

.coding-result-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  color: #244c5d;
  background: #dfecef;
  font-weight: 700;
  white-space: nowrap;
  border-color: #9fb6c0;
}

.coding-result-table tbody tr:nth-child(even) td {
  background: #fafbfc;
}

.coding-result-table tbody tr:hover td {
  background: #f0f7fa;
}

.coding-result-table tbody tr.primary-result-row td {
  background: #eef8fc;
  border-bottom-color: #cfe6f0;
}

.coding-result-table tbody tr.primary-result-row:hover td {
  background: #e5f4fa;
}

.coding-result-table tbody tr.primary-result-row td:first-child {
  box-shadow: inset 3px 0 0 #1680ad;
}

.coding-result-table.diagnosis-result-table .column-record {
  width: 130px;
}

.coding-result-table.diagnosis-result-table .column-name {
  width: 165px;
}

.coding-result-table.diagnosis-result-table .column-code {
  width: 155px;
}

.coding-result-table.diagnosis-result-table .column-complication {
  width: 88px;
}

.coding-result-table.diagnosis-result-table .column-evidence {
  width: 390px;
}

.coding-result-table.diagnosis-result-table .column-type {
  width: 132px;
}

.coding-result-table.surgery-result-table .column-record {
  width: 130px;
}

.coding-result-table.surgery-result-table .column-name {
  width: 220px;
}

.coding-result-table.surgery-result-table .column-code {
  width: 165px;
}

.coding-result-table.surgery-result-table .column-level4,
.coding-result-table.surgery-result-table .column-minimally-invasive {
  width: 110px;
  text-align: center;
}

.coding-result-table.surgery-result-table .column-evidence {
  width: 430px;
}

.coding-result-table.surgery-result-table .column-type {
  width: 150px;
}

.coding-result-table .column-record {
  width: 126px;
  color: #687984;
}

.coding-result-table .column-name {
  width: 170px;
}

.coding-result-table .column-code {
  width: 150px;
}

.coding-result-table .column-complication {
  width: 86px;
  text-align: center;
}

.coding-result-table .column-type {
  width: 116px;
}

.coding-result-table .column-evidence {
  min-width: 230px;
}

.result-name {
  color: #2b404c;
  font-weight: 500;
}

.result-name.primary {
  color: #0d6287;
  font-weight: 700;
}

.record-token {
  display: inline-block;
  max-width: 100%;
  color: #607985;
  font-family: Consolas, "Courier New", monospace;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  white-space: nowrap;
}

.code-token {
  display: inline-block;
  max-width: 100%;
  padding: 3px 7px;
  color: #3b5564;
  background: #edf1f3;
  border: 1px solid #dbe2e6;
  border-radius: 3px;
  font-family: Consolas, "Courier New", monospace;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.code-token.primary {
  color: #075f86;
  background: #e1f3fa;
  border-color: #b8ddea;
}

.type-badge,
.complication-badge {
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid transparent;
  border-radius: 3px;
  font-size: 11px;
  line-height: 1.6;
  white-space: nowrap;
}

.type-badge.primary {
  color: #08658c;
  background: #e4f4fa;
  border-color: #b9deec;
}

.type-badge.pathology {
  color: #76531c;
  background: #fff6df;
  border-color: #eed8a4;
}

.type-badge.external {
  color: #8a4747;
  background: #fff0f0;
  border-color: #edcccc;
}

.type-badge.additional {
  color: #52652e;
  background: #f1f7e5;
  border-color: #d5e3b7;
}

.type-badge.other {
  color: #5f6c74;
  background: #f1f3f4;
  border-color: #dce1e4;
}

.complication-badge {
  min-width: 30px;
  color: #87939a;
  background: #f4f5f6;
}

.complication-badge.active {
  color: #a14d26;
  background: #fff1e9;
  border-color: #efcfbc;
  font-weight: 700;
}

.evidence-cell {
  display: -webkit-box;
  overflow: hidden;
  color: #5b6b75;
  font-size: 14px;
  line-height: 1.5;
  padding-left: 10px;
  border-left: 2px solid #bdd4dc;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  white-space: pre-line;
}

.empty-result {
  padding: 48px 16px;
  text-align: center;
  color: #8b979f;
}

.request-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 12px;
  color: #a13b3b;
  background: #fff3f3;
  border: 1px solid #f2cece;
  border-radius: 4px;
  font-size: 13px;
}

@media (max-width: 900px) {
  .header-user {
    display: none;
  }

  .his-nav {
    margin-left: auto;
  }

  .patient-list-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .patient-list-actions {
    width: 100%;
  }

  .patient-list-search {
    flex: 1;
    width: auto;
  }

  .patient-strip {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 9px 18px;
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .patient-meta {
    order: 3;
    flex-basis: 100%;
  }

  .coding-button {
    margin-left: auto;
  }

  .his-workspace {
    grid-template-columns: 1fr;
  }

  .patient-panel {
    display: none;
  }

  .dialog-patient-summary {
    display: none;
  }
}

@media (max-width: 640px) {
  .his-header {
    padding: 0 14px;
  }

  .brand-block {
    width: auto;
  }

  .brand-block > div:last-child {
    display: none;
  }

  .his-nav button {
    min-width: 82px;
    padding: 0 10px;
  }

  .patient-list-page {
    padding: 16px 12px 24px;
  }

  .patient-list-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .patient-list-search,
  .patient-list-actions .el-button {
    width: 100%;
  }

  .patient-strip {
    padding-left: 14px;
    padding-right: 14px;
  }

  .patient-primary {
    flex-wrap: wrap;
  }

  .coding-mini-window {
    right: 12px;
    bottom: 12px;
    width: calc(100% - 24px);
  }

  .coding-dialog-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .footer-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .coding-button {
    flex: 1;
    width: auto;
    margin-left: 0;
  }

  .patient-actions {
    width: 100%;
  }

  .patient-actions :deep(.el-upload),
  .patient-actions :deep(.el-upload .el-button) {
    width: 100%;
  }

  .patient-actions > * {
    flex: 1;
  }

  .his-workspace {
    padding: 8px;
  }

  .record-panel {
    padding: 0 14px 18px;
  }

  .record-toolbar {
    align-items: flex-start;
    gap: 12px;
    padding: 14px 0;
  }

  .record-actions .el-button:first-child {
    display: none;
  }

  .record-form-grid,
  .agent-columns,
  .process-source-columns {
    grid-template-columns: 1fr;
  }

  .record-field.full-width {
    grid-column: auto;
  }

  .result-success-band {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .result-success-band .result-actions {
    width: 100%;
    margin-left: 50px;
    flex-wrap: wrap;
  }

  .result-overview {
    padding: 0 8px;
  }

  .overview-item {
    flex-direction: column;
    align-items: center;
    gap: 3px;
  }

  .overview-label {
    margin-right: 0;
  }

  .coding-result-table {
    min-width: 840px;
  }
}
</style>

<!-- ResultTable is rendered as a child component, so its cell styles must not
     depend on the parent component's scoped attribute. -->
<style>
body.is-sorting-codes {
  cursor: grabbing;
  user-select: none;
}

.coding-dialog:not(.is-fullscreen) {
  min-width: 760px;
  min-height: 420px;
  max-width: 98vw;
  max-height: 94vh;
  overflow: auto;
  resize: both;
}

.coding-dialog .el-dialog__header {
  margin-right: 0;
  padding: 14px 18px 12px;
  border-bottom: 1px solid #dce5e9;
  cursor: move;
}

.coding-dialog .el-dialog__body {
  max-height: calc(94vh - 154px);
  padding: 16px 18px;
  overflow: auto;
}

.coding-dialog .el-dialog__footer {
  padding: 12px 18px;
  border-top: 1px solid #dce5e9;
  background: #fafcfd;
}

.coding-dialog.is-fullscreen {
  width: 100% !important;
  height: 100% !important;
  max-width: none;
  max-height: none;
  display: flex;
  flex-direction: column;
  margin: 0 !important;
  resize: none;
  transform: none !important;
}

.coding-dialog.is-fullscreen .el-dialog__body {
  flex: 1;
  max-height: none;
}

.coding-dialog .result-table-shell {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid #aebfc7;
  border-radius: 4px;
  overflow: hidden;
}

.coding-dialog .table-legend {
  min-height: 40px;
  display: flex;
  align-items: center;
  gap: 17px;
  padding: 0 14px;
  color: #667984;
  background: #f3f7f8;
  border-bottom: 1px solid #aebfc7;
  font-size: 11px;
}

.coding-dialog .table-section-name {
  margin-right: 8px;
  color: #244b5c;
  font-size: 13px;
}

.coding-dialog .legend-main,
.coding-dialog .legend-other {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.coding-dialog .legend-main::before,
.coding-dialog .legend-other::before {
  width: 7px;
  height: 7px;
  content: '';
  border-radius: 50%;
}

.coding-dialog .legend-main::before {
  background: #1676a3;
}

.coding-dialog .legend-other::before {
  background: #a8b3ba;
}

.coding-dialog .table-count {
  margin-left: auto;
}

.coding-dialog .result-table-wrap {
  max-height: 430px;
  overflow: auto;
  background: #fff;
}

.coding-dialog .coding-result-table {
  width: 100%;
  color: #344b57;
  border: 1px solid #aebfc7;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 12px;
}

.coding-dialog .coding-result-table.diagnosis-result-table {
  min-width: 1160px;
}

.coding-dialog .coding-result-table.surgery-result-table {
  min-width: 1500px;
}

.coding-dialog .coding-result-table .column-selection {
  width: 46px;
  padding-right: 8px;
  padding-left: 8px;
  text-align: center;
  vertical-align: middle;
}

.coding-dialog .coding-result-table .column-selection input {
  width: 16px;
  height: 16px;
  accent-color: #087da9;
  cursor: pointer;
}

.coding-dialog .coding-result-table .column-order {
  width: 60px;
  padding-right: 6px;
  padding-left: 6px;
  text-align: center;
  vertical-align: middle;
}

.coding-dialog .drag-handle {
  width: 28px;
  height: 28px;
  display: inline-grid;
  grid-template-columns: repeat(2, 4px);
  grid-template-rows: repeat(3, 4px);
  place-content: center;
  gap: 3px;
  color: #4a788a;
  background: #eff6f8;
  border: 1px solid #c9dce3;
  border-radius: 4px;
  cursor: grab;
}

.coding-dialog .drag-handle:active {
  cursor: grabbing;
}

.coding-dialog .drag-handle i {
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: 50%;
}

.coding-dialog .dragging-result-row {
  opacity: 0.45;
}

.coding-dialog .drag-over-result-row td {
  border-top: 3px solid #1680a8;
}

.coding-dialog .selected-result-row td {
  box-shadow: inset 0 1px 0 rgb(22 128 168 / 5%);
}

.coding-dialog .coding-result-table th,
.coding-dialog .coding-result-table td {
  padding: 11px 12px;
  text-align: left;
  vertical-align: top;
  border: 1px solid #aebfc7;
  line-height: 1.6;
}

.coding-dialog .coding-result-table th {
  position: sticky;
  top: 0;
  z-index: 2;
  color: #173f52;
  background: #dcebef;
  border-color: #93adb8;
  font-weight: 700;
  white-space: nowrap;
}

.coding-dialog .coding-result-table tbody tr:nth-child(even) td {
  background: #f8fafb;
}

.coding-dialog .coding-result-table tbody tr:hover td {
  background: #edf7fa;
}

.coding-dialog .coding-result-table tbody tr.primary-result-row td {
  background: #e7f5fa;
  border-color: #9fc8d7;
}

.coding-dialog .coding-result-table tbody tr.primary-result-row td:first-child {
  box-shadow: inset 4px 0 0 #087da9;
}

.coding-dialog .coding-result-table .column-record {
  width: 130px;
}

.coding-dialog .coding-result-table .column-name {
  width: 175px;
}

.coding-dialog .coding-result-table .column-code {
  width: 155px;
}

.coding-dialog .coding-result-table .column-complication {
  width: 88px;
  text-align: center;
}

.coding-dialog .coding-result-table .column-type {
  width: 132px;
}

.coding-dialog .diagnosis-result-table .column-evidence {
  width: 390px;
}

.coding-dialog .surgery-result-table .column-evidence {
  width: 470px;
}

.coding-dialog .surgery-result-table .column-record {
  width: 140px;
}

.coding-dialog .surgery-result-table .column-name {
  width: 220px;
}

.coding-dialog .surgery-result-table .column-code {
  width: 165px;
}

.coding-dialog .surgery-result-table .column-level4,
.coding-dialog .surgery-result-table .column-minimally-invasive {
  width: 110px;
  min-width: 110px;
  text-align: center;
  white-space: nowrap;
}

.coding-dialog .surgery-result-table .column-type {
  width: 150px;
}

.coding-dialog .result-name {
  color: #2b404c;
  font-weight: 500;
}

.coding-dialog .result-name.primary {
  color: #075f86;
  font-weight: 700;
}

.coding-dialog .record-token {
  display: inline-block;
  max-width: 100%;
  color: #536f7c;
  font-family: Consolas, "Courier New", monospace;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coding-dialog .code-token {
  display: inline-block;
  max-width: 100%;
  padding: 3px 7px;
  color: #3b5564;
  background: #edf1f3;
  border: 1px solid #cbd7dc;
  border-radius: 3px;
  font-family: Consolas, "Courier New", monospace;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.coding-dialog .code-token.primary {
  color: #075f86;
  background: #d9eff7;
  border-color: #9fcfdf;
}

.coding-dialog .type-badge,
.coding-dialog .complication-badge {
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid transparent;
  border-radius: 3px;
  font-size: 11px;
  line-height: 1.6;
  white-space: nowrap;
}

.coding-dialog .type-badge.primary {
  color: #08658c;
  background: #dff2f8;
  border-color: #a8d5e4;
}

.coding-dialog .type-badge.pathology {
  color: #76531c;
  background: #fff6df;
  border-color: #e4cc91;
}

.coding-dialog .type-badge.external {
  color: #8a4747;
  background: #fff0f0;
  border-color: #e6bebe;
}

.coding-dialog .type-badge.additional {
  color: #52652e;
  background: #f1f7e5;
  border-color: #c9dba3;
}

.coding-dialog .type-badge.other {
  color: #5f6c74;
  background: #f1f3f4;
  border-color: #d3dade;
}

.coding-dialog .complication-badge {
  min-width: 30px;
  color: #87939a;
  background: #f4f5f6;
}

.coding-dialog .complication-badge.active {
  color: #a14d26;
  background: #fff1e9;
  border-color: #e9bea5;
  font-weight: 700;
}

.coding-dialog .evidence-cell {
  display: -webkit-box;
  padding-left: 10px;
  overflow: hidden;
  color: #536873;
  font-size: 14px;
  line-height: 1.5;
  border-left: 3px solid #9fc2cf;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  white-space: pre-line;
}

.coding-dialog .evidence-cell.expanded {
  display: block;
  overflow: visible;
  -webkit-line-clamp: unset;
}

.coding-dialog .evidence-toggle {
  margin-top: 6px;
  padding: 2px 0;
  color: #08749b;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: 11px;
}

.coding-dialog .result-pagination {
  position: relative;
  z-index: 2;
  flex: 0 0 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 12px;
  color: #71808a;
  background: #fafcfd;
  border-top: 1px solid #dce4e8;
  box-shadow: 0 -2px 5px rgb(32 70 84 / 5%);
  font-size: 11px;
}

.coding-dialog .result-pagination button {
  min-width: 58px;
  height: 27px;
  color: #356778;
  background: #fff;
  border: 1px solid #cbd9de;
  border-radius: 3px;
  cursor: pointer;
}

.coding-dialog .result-pagination button:disabled {
  color: #aeb8bd;
  background: #f3f5f6;
  cursor: not-allowed;
}

.coding-dialog .empty-result {
  padding: 48px 16px;
  text-align: center;
  color: #8b979f;
}

@media (max-width: 640px) {
  .coding-dialog:not(.is-fullscreen) {
    min-width: 0;
    resize: none;
  }

  .coding-dialog .coding-result-table {
    min-width: 900px;
  }
}

.coding-dialog .table-legend {
  flex-wrap: wrap;
  padding-top: 7px;
  padding-bottom: 7px;
}

.coding-dialog .table-view-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-left: auto;
}

.coding-dialog .table-count {
  margin-left: 0;
  white-space: nowrap;
}

.coding-dialog .table-tool-group {
  display: inline-flex;
  align-items: center;
  overflow: hidden;
  background: #fff;
  border: 1px solid #bdcdd4;
  border-radius: 4px;
}

.coding-dialog .table-tool-button {
  min-width: 34px;
  height: 28px;
  padding: 0 8px;
  color: #315767;
  background: #fff;
  border: 0;
  border-right: 1px solid #d4dfe4;
  cursor: pointer;
  font-size: 12px;
  line-height: 28px;
  white-space: nowrap;
}

.coding-dialog .table-tool-button:last-child {
  border-right: 0;
}

.coding-dialog .table-tool-button:hover:not(:disabled) {
  color: #087da9;
  background: #eaf5f8;
}

.coding-dialog .table-tool-button:disabled {
  color: #aab4b9;
  background: #f4f6f7;
  cursor: not-allowed;
}

.coding-dialog .font-size-value {
  min-width: 42px;
  height: 28px;
  color: #5c707a;
  background: #f7fafb;
  border-right: 1px solid #d4dfe4;
  font-size: 11px;
  line-height: 28px;
  text-align: center;
}

.coding-dialog .reset-font-button {
  min-width: 42px;
}

.coding-dialog .scroll-button {
  min-width: 62px;
}

.coding-dialog .result-table-wrap {
  overflow-x: auto;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.coding-dialog .result-table-wrap::-webkit-scrollbar {
  width: 10px;
  height: 12px;
}

.coding-dialog .result-table-wrap::-webkit-scrollbar-thumb {
  background: #9fb5be;
  border: 2px solid #eef3f5;
  border-radius: 6px;
}

.coding-dialog .result-table-wrap::-webkit-scrollbar-track {
  background: #eef3f5;
}

.coding-dialog .result-table-shell .coding-result-table {
  font-size: var(--result-table-font-size, 12px);
}

.coding-dialog .result-table-shell .type-badge,
.coding-dialog .result-table-shell .complication-badge,
.coding-dialog .result-table-shell .record-token,
.coding-dialog .result-table-shell .evidence-toggle {
  font-size: var(--result-table-small-font-size, 11px);
}

@media (max-width: 860px) {
  .coding-dialog .table-view-tools {
    width: 100%;
    justify-content: flex-start;
    margin-left: 0;
  }
}
</style>
