<script setup lang="ts">
defineProps<{ busy: boolean; elapsed: number }>()
</script>
<template>
  <span class="busy" v-if="busy || elapsed > 0">
    <span v-if="busy" class="spinner" />
    <span :class="busy ? 'elapsed' : 'done'">{{ elapsed.toFixed(1) }} s{{ busy ? ' · local Nemotron' : '' }}</span>
  </span>
</template>
