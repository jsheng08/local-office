<script setup lang="ts">
import type { Card } from '../../../types/office'
import { changeLabel, hours } from './presentation'
defineProps<{ card: Card }>()
defineEmits<{ select: [card: Card] }>()
</script>

<template>
  <button type="button" class="task" :class="[card.change, { proposed: card.proposed }]" @click="$emit('select', card)">
    <span class="meta"><code>{{ card.id }}</code><small v-if="card.proposed">proposed</small></span>
    <span v-if="changeLabel(card)" class="badge" :class="card.change">{{ changeLabel(card) }}</span>
    <strong class="title">{{ card.title }}</strong>
    <span v-if="card.est" class="estimate">{{ hours(card.est.low) }}–{{ hours(card.est.high) }} h</span>
    <span class="names">{{ card.staff.map(person => person.name.trim().split(/\s+/)[0]).join(', ') || 'Unassigned' }}</span>
  </button>
</template>

<style scoped>
.task{display:flex;flex-direction:column;align-items:flex-start;gap:12px;width:100%;height:100%;min-height:170px;padding:20px;background:#fffdf8;color:#1f2a2e;border:2px solid #d6cebf;border-radius:14px;box-shadow:0 4px 0 #d9cfbd;text-align:left;font:inherit;cursor:pointer;overflow-wrap:anywhere}.task:hover{border-color:#426b60}.task:focus-visible{outline:4px solid #76b900;outline-offset:3px}.task.proposed{border-style:dashed}.meta{display:flex;justify-content:space-between;gap:8px;width:100%;color:#596761;font-size:14px}.meta small{font-size:12px}.title{font-size:20px;line-height:1.35}.estimate{font-size:18px;font-weight:750}.names{font-size:16px;color:#596761;margin-top:auto}.badge{font-size:12px;font-weight:800;padding:5px 8px;border-radius:6px;line-height:1.4}.badge.added{background:#dbeafe;color:#174d9f}.badge.modified{background:#ffdf9e;color:#684000}.badge.removed{background:#e1e4e5;color:#4e575d}.task.removed{background:#e9e7e1}.task.removed .title{text-decoration:line-through;color:#65706c}
</style>
