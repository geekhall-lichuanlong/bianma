<script setup>
import { reactive, ref } from 'vue'
const reactiveObj = reactive({ count: 0 })
const refObj = ref({ count: 0 })
console.log(refObj.value.count)
const secRef = { foo: ref(1) }
</script>

<template>
  <div>
    {{ reactiveObj.count }}
    <div>---------</div>
    {{ refObj.count + 2 }}
    <div>---------</div>
    {{ secRef.foo }} 1 {{ secRef.foo + 1 }} 1 {{ secRef.foo.value + 1 }} 2
  </div>
</template>
