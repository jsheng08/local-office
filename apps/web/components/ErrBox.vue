<script setup lang="ts">
defineProps<{ err: { status?: number; body: string } | null; hint?: string }>()
</script>
<template>
  <div v-if="err" class="errbox">
    <b>{{ err.status ? `HTTP ${err.status}` : 'Error' }}{{ err.status === 403 ? ' — Access denied' : err.status === 502 ? ' — Local inference failed' : '' }}</b>
    <pre>{{ err.body }}</pre>
    <div v-if="hint && err.status === 403" class="hint">{{ hint }}</div>
  </div>
</template>
