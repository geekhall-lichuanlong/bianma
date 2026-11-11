<template>
  <div class="homeIndex">
    <div class="welcome-banner">
      <p style="font-size: 38px; margin-bottom: 20px">
        AI赋能 开启智能医疗管理新纪元
      </p>
      <!-- <h1>欢迎步入高效病案编码新领域</h1> -->
      <p style="font-size: 38px; margin-top: 30px">
        千医·牍智 智能助力 精准高效
      </p>
    </div>
    <div class="module-buttons">
      <router-link to="/drgGrouping" class="module-button">
        <img src="../assets/drgfenzu_icon.jpg" class="title" alt="DRG分组" />
        <img src="../assets//right_yjt.jpg" class="jiantou" alt="箭头" />
      </router-link>
      <router-link to="/bigModel" class="module-button center-button">
        <img
          src="../assets/zhinengbianma_icon.jpg"
          class="title"
          alt="智能编码"
        />
        <img src="../assets//right_yjt.jpg" class="jiantou" alt="箭头" />
      </router-link>
      <router-link to="/query" class="module-button">
        <img
          src="../assets/jibingshoushu_icon.jpg"
          class="title"
          alt="疾病手术"
        />
        <img src="../assets//right_yjt.jpg" class="jiantou" alt="箭头" />
      </router-link>
    </div>
    <!--  -->
  </div>
</template>
<script setup></script>

<style scoped lang="scss">
.homeIndex {
  font-family: 'Arial', sans-serif;
  max-width: 1200px;
  padding: 20px;
  margin-top: 100px;
}

.welcome-banner {
  text-align: center;
  margin-bottom: 40px;
}

.welcome-banner h1 {
  font-size: 28px;
  color: #333;
}

.module-buttons {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 80px;
}

.module-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 350px;
  height: 350px;
  border-radius: 12px;
  font-size: 28px;
  font-weight: bold;
  text-decoration: none;
  color: white;
  transition: all 0.3s ease;
  background-color: #f8fafe;
  border: 2px solid #e0e0e0;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  position: relative;

  .title {
    width: 160px;
  }
  .jiantou {
    width: 100px;
  }
}

.center-button {
  transform: scale(1.1);
  border: 3px solid #42a5f5;
  box-shadow: 0 8px 25px rgba(66, 165, 245, 0.3);
  z-index: 1;
}

.module-button:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.15);
  border-color: #42a5f5;
}

.center-button:hover {
  transform: scale(1.1) translateY(-8px);
  box-shadow: 0 15px 30px rgba(66, 165, 245, 0.4);
}

.blue {
  background-color: #42a5f5;
}

.green {
  background-color: #66bb6a;
}

.yellow {
  background-color: #ffca28;
  color: #333;
}
</style>
