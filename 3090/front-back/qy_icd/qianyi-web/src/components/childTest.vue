<script setup>
import { ref } from 'vue'
const input1 = ref(1)
function clickInput1() {
  input1.value++
}
defineExpose({
  clickInput1,
})
</script>

<template>
  <button @click="clickInput1">{{ input1 }}</button>
</template>
