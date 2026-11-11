<script setup>
import { ref, onMounted } from 'vue'
import Child from '@/components/childTest.vue'
const input = ref(null)
onMounted(() => {
  console.log(input.value)
  // child.value 是 <Child /> 组件的实例
})
function clickInput() {
  input.value.clickInput1()
}
</script>

<template>
  <button @click="clickInput">123</button>
  <Child ref="input"></Child>
</template>
