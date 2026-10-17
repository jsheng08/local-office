<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Card } from '~/types/office'
const props = defineProps<{ card: Card; color: string; x: number; y: number; missing: Card['staff'] }>()
const emit = defineEmits<{ select: [id: string] }>()
const approval = ref(0)
watch(() => props.card.proposed, (value, before) => { if (before && !value) approval.value++ })
const label = computed(() => {
  const card = props.card
  if (card.change === 'removed') return 'REMOVED'
  if (card.beforePriority && card.priority === 'wont') return 'DEFERRED'
  if (card.change === 'added') return '✦ NEW'
  if (card.beforePriority && card.beforePriority !== card.priority) {
    const order = ['must', 'should', 'could', 'wont']
    return `${order.indexOf(card.priority) < order.indexOf(card.beforePriority) ? '↑' : '↓'} ${{ must: 'MUST', should: 'SHOULD', could: 'NICE', wont: 'LATER' }[card.priority]}`
  }
  return ''
})
const faded = computed(() => props.card.change === 'removed' || label.value === 'DEFERRED')
</script>
<template>
  <g class="bed-position" :style="{ transform: `translate(${x}px, ${y}px)` }">
    <g class="bed interactive" role="button" tabindex="0" :aria-label="`${card.id}: ${card.title}. ${label}. ${card.proposed ? 'Proposed, awaiting approval.' : ''} ${missing.map(person => `${person.name} on leave; doctor needed`).join('. ')}`" @click.stop="emit('select', card.id)" @keydown.enter.stop.prevent="emit('select', card.id)" @keydown.space.stop.prevent="emit('select', card.id)">
      <title>{{ card.id }} · {{ card.title }}{{ card.proposed ? ' · proposed recommendation' : '' }}{{ missing.length ? ` · On leave: ${missing.map(person => person.name).join(', ')}` : '' }}</title>
      <g :opacity="faded ? .48 : 1">
        <ellipse cx="40" cy="28" rx="45" ry="12" fill="#10201f" opacity=".12" />
        <!-- Same 2:1 projection as the office tiles, with raised mattress faces. -->
        <path d="M0 -15 L30 -30 L83 -4 L53 11Z" fill="#fffdf5" stroke="#b3bfb6" />
        <path d="M0 -15 V-3 L53 23 V11Z" fill="#c6d2cb" /><path d="M53 11 L83 -4 V8 L53 23Z" fill="#e1e7de" />
        <path d="M3 -13 V4 M78 -1 V15" stroke="#5c7169" stroke-width="3" /><circle cx="4" cy="8" r="4" fill="#344d47" /><circle cx="78" cy="18" r="4" fill="#344d47" />
        <path d="M3 -18 L28 -30 L43 -23 L18 -10Z" fill="#fff" /><ellipse cx="24" cy="-23" rx="10" ry="7" fill="#e8b98e" /><path d="M15 -25 Q21 -34 31 -26" fill="#493d35" />
        <path d="M24 -8 L49 -21 L82 -5 L55 9 V19 L24 4Z" :fill="color" /><path d="M33 -9 L56 2" stroke="#fff" stroke-opacity=".35" stroke-width="3" />
        <path d="M-4 -17 L29 -35 L88 -6 V13 L53 31 L-4 4Z" fill="none" :stroke="card.proposed ? '#f5a524' : '#80988a'" :stroke-width="card.proposed ? 2.5 : 1" :stroke-dasharray="card.proposed ? '6 4' : undefined" />
        <path d="M84 -6 V-45 H72 M81 -6 H89" stroke="#81978b" stroke-width="2" fill="none" /><rect x="70" y="-43" width="8" height="14" rx="3" fill="#c0e5e2" stroke="#81978b" /><path d="M74 -29 Q68 -8 62 -6" fill="none" stroke="#91b6b2" />
        <g v-if="card.priority === 'must' && card.change !== 'removed'" transform="translate(-5 -40)"><rect width="28" height="20" rx="3" fill="#10201f" /><path class="heartbeat" d="M3 11 H8 L11 5 L14 16 L18 8 L21 11 H25" fill="none" stroke="#76b900" stroke-width="2" /><path d="M14 20 V28" stroke="#81978b" stroke-width="2" /></g>
      </g>
      <g v-if="label" transform="translate(-2 -60)"><rect width="105" height="19" rx="6" :fill="faded ? '#67757c' : card.change === 'added' ? '#287ac6' : '#10201f'" /><text x="52" y="14" text-anchor="middle" fill="white" class="badge">{{ label }}</text></g>
      <rect x="-3" y="26" width="112" height="32" rx="5" fill="#fffdf5" stroke="#b2bbaa" /><rect x="39" y="23" width="22" height="6" rx="2" fill="#81978b" />
      <text x="3" y="39" class="id">{{ card.id.length > 16 ? `${card.id.slice(0, 15)}…` : card.id }}</text><text x="3" y="52" class="title">{{ card.title.length > 14 ? `${card.title.slice(0, 13)}…` : card.title }}</text>
      <g v-if="card.proposed" transform="translate(8 59)"><rect width="88" height="16" rx="4" fill="#f5a524" /><text x="44" y="12" text-anchor="middle" class="badge">PROPOSED</text></g>
      <g v-else-if="approval" :key="approval" class="approved" transform="translate(58 -36)"><circle r="14" fill="#76b900" /><path d="M-7 0 L-2 5 L8 -6" fill="none" stroke="white" stroke-width="3" /></g>
      <g v-for="(person, index) in missing" :key="person.staff_id" :transform="`translate(${91 + index % 2 * 16} ${-12 + Math.floor(index / 2) * 25})`"><title>{{ person.name }} · on leave · doctor needed</title><path d="M-6 0 A6 6 0 1 1 6 0 M-8 20 V10 Q0 2 8 10 V20Z" fill="none" stroke="#e5484d" stroke-dasharray="3 2" /><text x="7" y="2" fill="#e5484d" font-size="19" font-weight="900">!</text></g>
    </g>
  </g>
</template>
<style scoped>
.bed-position { transition: transform .85s cubic-bezier(.22,.8,.25,1); }
.bed { animation: arrive .45s ease-out both; cursor: pointer; outline: none; }
.bed:focus-visible, .bed:hover { filter: drop-shadow(0 0 4px #76b900); }
text { font-family: ui-rounded, 'Trebuchet MS', system-ui, sans-serif; pointer-events: none; }
.id, .title { fill: #10201f; }
.badge { font-size: 11px; font-weight: 900; }
.id { font-size: 11px; font-weight: 900; }
.title { font-size: 12px; font-weight: 600; }
.heartbeat { stroke-dasharray: 45; animation: pulse 1.6s linear infinite; }
.approved { animation: approved .95s ease-out forwards; transform-box: fill-box; transform-origin: center; }
@keyframes arrive { from { opacity: 0; translate: 0 12px; } to { opacity: 1; translate: 0 0; } }
@keyframes pulse { from { stroke-dashoffset: 45; } to { stroke-dashoffset: -45; } }
@keyframes approved { 0% { opacity: 0; scale: .4; } 30%, 65% { opacity: 1; scale: 1.1; } 100% { opacity: 0; scale: 1; } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } .approved { opacity: 1; } }
</style>
