<script setup lang="ts">
const props = defineProps<{ busy: boolean; elapsed: number; stages?: string[] }>()
// Static description of the backend pipeline order — cycled on a timer, NOT live telemetry.
// Pages pass the stage list for their own endpoint; without it only elapsed time is shown.
const list = computed(() => props.stages || [])
const idx = computed(() => Math.min(Math.floor(props.elapsed / 6), list.value.length - 1))
</script>
<template>
  <span class="busy" v-if="busy || elapsed > 0">
    <span v-if="busy" class="spinner" />
    <span v-if="busy && list.length" class="stage">
      <span class="stagetxt">{{ list[idx] }}…</span>
      <span class="stagelbl">pipeline stage {{ idx + 1 }}/{{ list.length }} (typical order, not live telemetry)</span>
    </span>
    <span :class="busy ? 'elapsed' : 'done'">{{ elapsed.toFixed(busy ? 0 : 1) }} s{{ busy ? ' elapsed' : ' · done' }}</span>
  </span>
</template>
