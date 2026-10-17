<script setup lang="ts">
import { computed } from 'vue'
const props = withDefaults(defineProps<{ x: number; y: number; w: number; d: number; h: number; top?: string; left?: string; right?: string }>(), { top: '#c79a62', left: '#a87d49', right: '#b98b55' })
const faces = computed(() => {
  const p = (x: number, y: number, z = 0) => `${590 + (x - y) * 42},${180 + (x + y) * 21 - z}`
  const { x, y, w, d, h } = props
  const a = p(x, y, h), b = p(x + w, y, h), c = p(x + w, y + d, h), e = p(x, y + d, h)
  return { top: `${a} ${b} ${c} ${e}`, left: `${e} ${c} ${p(x + w, y + d)} ${p(x, y + d)}`, right: `${b} ${c} ${p(x + w, y + d)} ${p(x + w, y)}` }
})
</script>
<template>
  <g stroke="#10201f" stroke-opacity=".12" stroke-linejoin="round">
    <polygon :points="faces.left" :fill="left" />
    <polygon :points="faces.right" :fill="right" />
    <polygon :points="faces.top" :fill="top" />
  </g>
</template>
