<script setup lang="ts">
import type { Staff } from '~/types/office'
defineProps<{ person: Staff; x: number; y: number; color: string; patients: number; proposed: boolean }>()
const emit = defineEmits<{ select: [id: string] }>()
</script>
<template>
  <g class="doctor-position" :style="{ transform: `translate(${x}px, ${y}px)` }">
    <g class="doctor" :class="{ treating: patients > 0 }" role="button" tabindex="0" :aria-label="`${person.name}, ${patients} patients${proposed ? ', proposed recommendation' : ''}`" @click.stop="emit('select', person.id)" @keydown.enter.stop.prevent="emit('select', person.id)" @keydown.space.stop.prevent="emit('select', person.id)">
      <title>{{ person.name }} · {{ person.role }} · {{ patients }} patients{{ proposed ? ' · proposed recommendation' : '' }}</title>
      <ellipse cy="3" rx="13" ry="5" fill="#10201f" opacity=".16" /><path d="M-6 -8 V3 M6 -8 V3" stroke="#344d47" stroke-width="5" stroke-linecap="round" />
      <path d="M-12 -12 V-29 Q0 -36 12 -29 V-12Z" :fill="color" />
      <path v-if="patients" d="M-11 -30 L-3 -33 L0 -23 L3 -33 L11 -30 L14 -10 H-14Z" fill="#fffdf5" stroke="#a7b9ae" /><path v-if="patients" d="M-5 -30 V-22 Q0 -14 5 -22 V-30 M5 -21 L9 -17" fill="none" stroke="#344d47" stroke-width="1.5" /><circle v-if="patients" cx="9" cy="-17" r="2" fill="#344d47" />
      <circle cy="-40" r="9" fill="#e8b98e" /><path d="M-9 -41 Q-11 -53 2 -51 Q11 -51 9 -40 L5 -45Z" fill="#493d35" /><circle cx="-3" cy="-40" r="1" fill="#10201f" /><circle cx="3" cy="-40" r="1" fill="#10201f" />
      <rect x="-22" y="5" width="44" height="14" rx="4" fill="#fffdf5" stroke="#81978b" /><text y="15" text-anchor="middle" font-size="10" font-weight="700">{{ person.name.split(/\s+/)[0]?.slice(0, 8) }}</text>
      <g v-if="patients > 1" transform="translate(0 -61)"><rect x="-43" y="-14" width="86" height="20" rx="9" fill="#10201f" /><text text-anchor="middle" fill="#fff9ec" font-size="11">×{{ patients }} patients</text></g>
    </g>
  </g>
</template>
<style scoped>
.doctor-position { transition: transform .8s cubic-bezier(.4,0,.2,1); }
.doctor { cursor: pointer; outline: none; }
.doctor:focus-visible, .doctor:hover { filter: drop-shadow(0 0 4px #76b900); }
text { font-family: ui-rounded, 'Trebuchet MS', system-ui, sans-serif; pointer-events: none; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
