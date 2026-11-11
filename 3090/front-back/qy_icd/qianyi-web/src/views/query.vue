<!-- 疾病手术知识查询 -->
<template>
  <div class="page-box">
    <div class="welcome-container" v-if="showWelcome">
      <img src="@/assets/logoOne.png" class="welcome-logo" alt="Logo" />
      <div class="welcome-text">您的编码知识管家已上线，快来考考我吧！</div>
    </div>
    <div class="ques-box" ref="answerBox">
      <template v-for="(item, index) in questList" :key="index">
        <div class="ques-ddd">
          <div class="right ques-item">
            <img src="@/assets/user.jpg" class="avatar" alt="" />
            <span class="ques-text">{{ item.question }}</span>
          </div>
          <div
            class="left ques-item"
            v-for="(answer, aIndex) in item.answerList"
            :key="aIndex"
          >
            <img
              src="@/assets/logoOne.png"
              v-if="aIndex % 4 === 0"
              class="avatar"
              alt=""
            />
            <div class="sk-content">
              {{ answer.think }}
            </div>
            <span class="ques-text">
              <span v-if="answer.content" class="name-str">
                {{ answer.name }}:</span
              >
              {{ answer.content }}</span
            >
          </div>
        </div>
      </template>
    </div>
    <div class="chat-input">
      <div class="tip">
        <ul>
          <li>常用问题：</li>
          <li @click="tipClick('药物洗脱冠状动脉支架置入术如何编码')">
            药物洗脱冠状动脉支架置入术如何编码
          </li>
        </ul>
      </div>
      <div class="ci-content">
        <!-- <img
          src="@/assets/images/aiChat/voice-icon.png"
          alt=""
          class="hand voice-icon"
          v-longhandle:[500]="beginSpeak"
          @longHandleEnd="endSpeak"
        /> -->
        <!-- <el-icon style="margin-right: 12px"><Search /></el-icon> -->
        <el-input
          class="input-text"
          v-model.trim="inputVal"
          @keyup.enter="submit"
          :autosize="{ minRows: 1, maxRows: 4 }"
          type="textarea"
          placeholder="请输入疾病名称或手术名称~"
        />
        <div class="bottom-box flex-align" style="justify-content: end">
          <div class="fs-box" @click="submit">
            <el-icon>
              <Position />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup name="bigModel">
import { ref, onMounted, nextTick } from 'vue'
const inputVal = ref(null)
const isyb = ref(false)
const iswj = ref(false)
const questList = ref([])
const answerBox = ref(null)
const showWelcome = ref(true)
const observer = new MutationObserver(function (mutationsList, observer) {
  // 在这里，你可以实现滚动到底部的操作
  answerBox.value.scrollTop = answerBox.value.scrollHeight + 200
})
const config = { childList: true, subtree: true }

onMounted(() => {
  observer.observe(answerBox.value, config)
})
function uuid(nums) {
  nums = nums || 36
  let s = []
  let uuidData = '0123456789abcdefghijklmnopqrstuvwxyz'
  let uuidDataLength = uuidData.length
  for (let i = 0; i < nums; i++) {
    let startLen = Math.floor(Math.random() * uuidDataLength)
    s[i] = uuidData.substring(startLen, ++startLen)
  }
  return s.join('')
}
let answers = [
  {
    name: '',
    think: `以下是药物洗脱冠状动脉支架置入术的 ICD-9-CM-3 编码注意事项，结合分类规则和临床案例综合分析：

一、核心编码规则
主编码选择

药物洗脱冠状动脉支架置入术的主编码为 36.07（冠状动脉支架植入术），需明确是否使用药物洗脱支架。

非药物洗脱支架（裸支架）也使用 36.07，但需通过附加编码区分类型（如 00.55 用于药物洗脱支架的说明）。

附加编码

支架数量：每增加一个支架需附加编码 00.47（例如置入 3 个支架时编码 00.4700）。

血管数量：若涉及多支血管操作，需编码 00.41（单支）或 00.42（双支）等。

血管分叉部位操作：若支架覆盖冠状动脉分叉部位（如左主干分叉），需附加 00.44（血管分叉部位操作）。

二、关键注意事项
区分药物洗脱与裸支架

药物洗脱支架需在 36.07 基础上联合编码 00.55（药物洗脱支架的置入），以明确技术差异。

伴随操作的编码

经皮冠状动脉腔内成形术（PTCA）：若支架置入前进行了球囊扩张，需另编码 00.66（PTCA）。

冠状动脉造影：需附加 88.57（多根导管冠状动脉造影）或 88.55（单根导管）。

解剖部位与术式匹配

必须明确支架置入的具体冠状动脉分支（如左前降支、回旋支），避免笼统归类。

若同时处理颅内或颅外动脉（如颈动脉），需按部位区分编码（如颅外动脉用 00.63，颅内用 00.65）。

分叉部位的特殊处理

若在分叉处使用边支保护技术（如双导丝、球囊保护），需附加 00.44。

例如：左主干分叉病变支架置入需联合编码 00.44 以反映技术复杂性。

三、常见错误案例
漏编附加编码

错误：仅编码 36.07，忽略药物洗脱支架的 00.55 或分叉部位操作的 00.44。

正确：联合编码 36.07+00.55+00.44（若适用）。

混淆血管数量与支架数量

错误：单支血管置入 2 个支架时仅编码 00.40（单支血管操作）。

正确：编码 00.40+00.47（支架数量）。

忽略伴随操作

错误：未编码 PTCA 或冠状动脉造影。

正确：主手术 36.07，附加 00.66（PTCA）和 88.57（造影）。

四、编码步骤建议
阅读手术记录：明确支架类型（药物/裸）、数量、血管分支及是否涉及分叉。

核对类目表注释：例如 36.07 是否包含其他操作（如球囊扩张）。

联合编码：主编码（36.07）+附加编码（00.55/00.44/00.47）+伴随操作（00.66/88.57）。

五、影响与质控
绩效考核：编码错误可能导致四级手术比例统计偏差，影响医院评级。

病案完整性：需确保所有操作（如边支保护、造影）均体现在编码中。

总结：药物洗脱冠状动脉支架置入术的编码需综合支架类型、解剖部位、伴随操作及分叉处理，严格遵循 ICD-9-CM-3 的分类轴心（部位、术式、入路、疾病性质）。建议编码员与临床医师协作，详细核对手术记录以提高准确性。
`,
    content: ``,
  },
]
function submit() {
  let ques = inputVal.value
  inputVal.value = ''
  showWelcome.value = false
  questList.value.push({
    id: uuid(),
    question: ques,
    answerList: [],
  })

  let mainAnswer = [...answers]
  nextAnswer(mainAnswer)
}
function nextAnswer(mainAnswer) {
  let item = mainAnswer.shift()
  if (item) {
    let opObj = questList.value[questList.value.length - 1]
    opObj.answerList.push({
      think: '',
      content: '',
      name: item.name,
    })
    gradualSubstring(item.think, (str) => {
      opObj.answerList[opObj.answerList.length - 1].think += str
    })
      .then(() => {
        gradualSubstring(item.content, (str) => {
          opObj.answerList[opObj.answerList.length - 1].content += str
        }).then(() => {
          nextAnswer(mainAnswer)
        })
      })
      .catch((err) => {
        console.log(err)
      })
  }
}
function gradualSubstring(str, callback) {
  return new Promise((resolve, reject) => {
    let remaining = str
    const intervalId = setInterval(() => {
      if (remaining.length === 0) {
        clearInterval(intervalId)
        resolve()
        return
      }

      // 截取前两个字符（或剩余字符）
      const part = remaining.substring(0, 2)
      callback(part)
      // 更新剩余字符串
      remaining = remaining.substring(2)
    }, 10)
  })
}
function tipClick(value) {
  // 将处理后的文本填入输入框
  inputVal.value = value
  // nextTick(() => {
  //   if(inputVal.value.trim()) {
  //     submit()
  //   }
  // })
}
</script>
<style lang="scss" scoped>
.chat-input {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 0 0 auto;
  .tip ul {
    width: 100%;
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    li {
      list-style: none;
      color: #437ff7;
      font-size: 14px;
      cursor: pointer;
    }
  }
  //   position: absolute;
  //   bottom: 20px;
  //   left: 50%;
  .ci-content {
    border: 1px solid rgba(65, 77, 96, 0.3);
    box-sizing: border-box;
    height: auto;
    width: 800px;
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

.voice-icon {
  width: 30px;
  margin-right: 8px;
}

.submit-icon {
  width: 64px;
}

.yuyin-box {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);

  > img {
    height: 30px;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
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
}

.ques-box {
  flex: 1 1 0;
  width: 860px;
  padding: 20px 30px 0;
  //   position: absolute;
  //   bottom: 20px;
  //   left: 50%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  max-height: calc(100% - 100px);
  overflow-y: auto;
}

.page-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
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
  width: fit-content;
  padding: 14px;
  line-height: 21px;
  font-size: 14px;
  max-width: 700px;

  .avatar {
    position: absolute;
    width: 40px;
    height: 40px;
    right: -25px;
    top: -20px;
    border-radius: 50%;
  }

  &.right {
    text-align: right;
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
      font-size: 14px;
      color: #333;
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
.welcome-container {
  position: absolute;
  top: 50%;
  left: 57%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  z-index: 1;
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
</style>
