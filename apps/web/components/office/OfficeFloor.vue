<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Staff, Card, Phase, Priority } from '~/types/office'
import IsoBlock from './floor/IsoBlock.vue'
import HospitalBed from './floor/HospitalBed.vue'
import Doctor from './floor/Doctor.vue'
import { wardLayout, staffPlacements } from './floor/layout'
const props = defineProps<{
  cards: Card[]; staff: Staff[]; tasksByStaff: Record<string, Card[]>; phase: Phase; helperSay: string
  boardCounts: Record<Priority, number>; hasProposed: boolean; quarantineCount: number; busy: boolean
}>()
const emit = defineEmits<{ drop: [files: File[]]; 'open-board': []; 'select-card': [id: string]; 'select-staff': [id: string]; 'open-records': [] }>()
const input = ref<HTMLInputElement | null>(null)
const dragDepth = ref(0)
const dragging = computed(() => dragDepth.value > 0 && !props.busy)
const iso = (x: number, y: number, z = 0) => [590 + (x - y) * 42, 180 + (x + y) * 21 - z] as const
const at = (x: number, y: number, z = 0) => `translate(${iso(x, y, z).join(' ')})`
const polygon = (points: readonly (readonly number[])[]) => points.map(p => p.join(',')).join(' ')
const lanes: { key: Priority; label: string; color: string }[] = [
  { key: 'must', label: 'MUST', color: '#e5484d' }, { key: 'should', label: 'SHOULD', color: '#f5a524' },
  { key: 'could', label: 'NICE', color: '#3fb26f' }, { key: 'wont', label: 'LATER', color: '#8a949b' },
]
const wards = computed(() => wardLayout(props.cards || []))
const beds = computed(() => wards.value.flatMap(ward => ward.beds))
const doctors = computed(() => staffPlacements(props.staff, props.cards || [], beds.value, desks.value, iso))
const tasks = (id: string) => props.tasksByStaff[id] || []
const shirt = (id: string) => ['#5989a2', '#bf7796', '#dd9b42', '#6a9d82', '#8d82b1'][Array.from(id).reduce((n, c) => n + c.charCodeAt(0), 0) % 5]
const desks = computed(() => props.staff.slice(0, 12).map((person, i) => ({ person, x: 3.2 + (i % 4) * 2.3, y: 4.5 + Math.floor(i / 4) * 2.2 })).sort((a, b) => a.x + a.y - b.x - b.y))
const shortDate = (value: string) => {
  const date = new Date(`${value.slice(0, 10)}T12:00:00`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}
const positions: Record<Phase, [number, number]> = {
  idle: [2.5, 3.6], receiving: [1.4, 8.4], reading: [2.6, 3.2], quarantine: [0.8, 5.7],
  filing: [5.5, 1.9], awaiting: [10.2, 1.9], applied: [7.7, 10.2], error: [1.4, 8.4],
}
const helperPosition = computed(() => { const [x, y] = iso(...positions[props.phase]); return { transform: `translate(${x}px, ${y}px)` } })
const speech = computed(() => {
  const words = props.helperSay.trim().split(/\s+/).flatMap(word => word.match(/.{1,38}/gu) || [])
  const lines: string[] = []
  for (const word of words) {
    if (lines.length && `${lines[lines.length - 1]} ${word}`.length <= 38) lines[lines.length - 1] += ` ${word}`
    else lines.push(word)
  }
  return lines.length > 3 ? [...lines.slice(0, 2), `${lines[2]!.slice(0, 37)}…`] : lines
})
function enter(event: DragEvent) { if (event.dataTransfer?.types.includes('Files')) dragDepth.value++ }
function drop(event: DragEvent) {
  dragDepth.value = 0
  if (!props.busy && event.dataTransfer?.files.length) emit('drop', Array.from(event.dataTransfer.files))
}
function choose() { if (!props.busy) input.value?.click() }
function selected(event: Event) {
  const target = event.target as HTMLInputElement
  if (!props.busy && target.files?.length) emit('drop', Array.from(target.files))
  target.value = ''
}
</script>

<template>
  <div class="office-floor" :class="{ dragging }" :aria-busy="busy" @dragenter.prevent="enter" @dragover.prevent="event => { if (event.dataTransfer) event.dataTransfer.dropEffect = busy ? 'none' : 'copy' }" @dragleave.prevent="dragDepth = Math.max(0, dragDepth - 1)" @drop.prevent="drop">
    <input ref="input" class="file-input" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.md,.txt" aria-label="Upload client documents" :disabled="busy" @change="selected">
    <p class="sr-only" role="status" aria-live="polite">{{ helperSay }}</p>
    <svg class="scene" viewBox="65 -405 1140 1195" role="group" aria-label="Interactive isometric office: upload documents, explore the board, select staff or open records">
      <!-- Same 2:1 isometric projection as the visual reference. -->
      <ellipse cx="626" cy="684" rx="400" ry="62" fill="#071513" opacity=".24" />
      <IsoBlock :x="0" :y="0" :w="13" :d="11" :h="12" top="#efe7d8" left="#c1ad8f" right="#d1bfa4" />
      <path v-for="n in 12" :key="`tile-x-${n}`" :d="`M${iso(n, 0).join(' ')} L${iso(n, 11).join(' ')}`" stroke="#d8ccb6" stroke-width="1" />
      <path v-for="n in 10" :key="`tile-y-${n}`" :d="`M${iso(0, n).join(' ')} L${iso(13, n).join(' ')}`" stroke="#d8ccb6" stroke-width="1" />
      <polygon :points="polygon([iso(0, 0), iso(13, 0), iso(13, 0, 115), iso(0, 0, 115)])" fill="#c3d3c8" stroke="#a4b9ae" />
      <polygon :points="polygon([iso(0, 0), iso(0, 11), iso(0, 11, 115), iso(0, 0, 115)])" fill="#dce5d7" stroke="#a4b9ae" />
      <!-- Windows cast warm patches onto the floor. -->
      <g v-for="y in [2.1, 8.9]" :key="y" :transform="at(0, y, 58)">
        <path d="M0 -28 L-67 5 V61 L0 28 Z" fill="#9dcad0" stroke="#f8f6ea" stroke-width="6" />
        <path d="M-33 -11 V44 M0 0 L-67 33" stroke="#f8f6ea" stroke-width="3" />
        <path d="M-64 64 L0 32 L100 87 L36 119 Z" fill="#fff6cf" opacity=".24" />
      </g>
      <!-- A separate keyed bed layer preserves identity across ward changes. -->
      <text x="96" y="-376" fill="#efe7d8" class="heading">TASK HOSPITAL</text>
      <text x="1180" y="-376" text-anchor="end" fill="#c8d9ca" class="small">{{ hasProposed ? 'Proposed care plan · PM approval required' : 'Project care wards' }}</text>
      <g v-for="ward in wards" :key="ward.key" class="interactive" role="button" tabindex="0" :aria-label="`${ward.label}, ${ward.total} tasks. Open board`" @click="emit('open-board')" @keydown.enter.prevent="emit('open-board')" @keydown.space.prevent="emit('open-board')">
        <rect :x="ward.x" y="-350" width="266" height="365" rx="15" fill="#efe7d8" :stroke="ward.color" stroke-width="3" />
        <path :d="`M${ward.x + 2} -299 H${ward.x + 264} V-277 L${ward.x + 242} -288 H${ward.x + 22} L${ward.x + 2} -277Z`" :fill="ward.color" opacity=".2" />
        <rect :x="ward.x" y="-350" width="266" height="44" rx="12" fill="#10201f" :stroke="ward.color" stroke-width="2" />
        <text :x="ward.x + 133" y="-322" text-anchor="middle" :fill="ward.color" class="ward-heading">{{ ward.label }}</text>
        <path :d="`M${ward.x + 133} -280 V-22`" stroke="#b7bcae" stroke-dasharray="5 6" />
        <text v-if="!ward.total" :x="ward.x + 133" y="-140" text-anchor="middle" fill="#66786f" class="small">Ready for patients</text>
        <text :x="ward.x + 133" y="0" text-anchor="middle" fill="#344d47" class="small bold">{{ ward.total > 6 ? `+${ward.total - 6} more · open board ↗` : `${ward.total} patients · open board ↗` }}</text>
      </g>
      <HospitalBed v-for="bed in beds" :key="bed.card.id" :card="bed.card" :color="bed.color" :x="bed.x" :y="bed.y" :missing="bed.card.staff.filter(member => staff.find(person => person.id === member.staff_id)?.on_leave)" @select="emit('select-card', $event)" />
      <g transform="translate(458 110)"><circle r="23" fill="#fff8e9" stroke="#657c70" stroke-width="4" /><path d="M0 -15 V0 L10 7" fill="none" stroke="#10201f" stroke-width="3" stroke-linecap="round" /></g>
      <!-- PM's glass office and records at the far side. -->
      <IsoBlock :x="10" :y=".35" :w="2.65" :d="2.5" :h="5" top="#abc7bb" left="#71978a" right="#8bac9f" />
      <polygon :points="polygon([iso(10, .35), iso(10, 2.85), iso(10, 2.85, 103), iso(10, .35, 103)])" fill="#b6dbe0" fill-opacity=".42" stroke="#779d9b" stroke-width="3" />
      <polygon :points="polygon([iso(10, .35, 103), iso(12.65, .35, 103), iso(12.65, 2.85, 103), iso(10, 2.85, 103)])" fill="#e1f0e7" fill-opacity=".5" stroke="#779d9b" stroke-width="2" />
      <IsoBlock :x="11" :y=".9" :w="1.4" :d=".8" :h="26" />
      <g :transform="at(11.25, 1.4, 98)"><rect x="-68" y="-20" width="136" height="29" rx="7" fill="#10201f" /><text text-anchor="middle" y="0" fill="#fff8e9" class="heading">PM office</text></g>
      <g class="interactive" role="button" tabindex="0" aria-label="Open records" @click="emit('open-records')" @keydown.enter.prevent="emit('open-records')" @keydown.space.prevent="emit('open-records')">
        <title>Open document records</title>
        <IsoBlock :x="11.8" :y="3.1" :w="1" :d="1.7" :h="58" top="#95aba0" left="#617e70" right="#789487" />
        <g :transform="at(12.2, 4.3, 48)"><path d="M-17 0 L19 18 M-17 17 L19 35" stroke="#d4e2d6" stroke-width="2" /><path d="M-3 1 L7 6 M-3 18 L7 23" stroke="#10201f" stroke-width="4" /><rect x="-55" y="51" width="112" height="28" rx="6" fill="#10201f" /><text x="1" y="71" fill="white" text-anchor="middle" class="heading">Records ↗</text></g>
      </g>
      <!-- Helper's workbench. -->
      <IsoBlock :x=".7" :y="2.4" :w="2" :d=".95" :h="30" />
      <g :transform="at(1.5, 2.65, 30)"><rect x="-24" y="-43" width="48" height="33" rx="4" fill="#243d38" /><rect :class="{ 'monitor-glow': phase === 'reading' }" x="-19" y="-38" width="38" height="23" rx="2" fill="#76b900" /><path d="M0 -10 V0 M-12 0 H12" stroke="#243d38" stroke-width="4" /><text x="0" y="34" text-anchor="middle" class="small bold">Helper / triage</text></g>
      <g :transform="at(.7, 5.1)" :class="{ 'quarantine-flash': phase === 'quarantine' }"><path d="M-24 -45 H24 L19 0 H-19Z" fill="#e5484d" /><path d="M-29 -46 H29" stroke="#963f42" stroke-width="8" /><path d="M0 -37 L12 -32 V-22 Q10 -12 0 -8 Q-10 -12 -12 -22 V-32Z" fill="#fff0dc" /><text y="26" text-anchor="middle" class="small bold">QUARANTINE · {{ quarantineCount }}</text></g>
      <!-- Plants, coffee, rug and sleeping cat. -->
      <g v-for="location in [[.65, .7], [12.2, 8.9], [4, 10.3]]" :key="location.join()" :transform="at(location[0]!, location[1]!)">
        <ellipse cy="3" rx="20" ry="9" fill="#10201f" opacity=".12" /><path d="M-15 -17 H15 L11 5 H-11Z" fill="#bd7958" /><ellipse cy="-17" rx="15" ry="7" fill="#87543f" /><g class="plant"><path d="M0 -17 V-69" stroke="#5d7940" stroke-width="4" /><ellipse cx="-10" cy="-47" rx="9" ry="21" transform="rotate(-36 -10 -47)" fill="#638f53" /><ellipse cx="10" cy="-55" rx="9" ry="22" transform="rotate(35 10 -55)" fill="#86a966" /></g>
      </g>
      <g :transform="at(.8, 7)"><rect x="-30" y="-48" width="55" height="43" rx="5" fill="#654c3c" /><rect x="-23" y="-41" width="40" height="24" rx="3" fill="#213b35" /><path d="M-9 -24 V-12 H5 V-24Z" fill="#fff4d8" /><path class="steam" d="M-3 -52 Q-12 -61 -3 -69 Q4 -76 -2 -83" fill="none" stroke="#fff6df" stroke-width="3" /><text y="16" text-anchor="middle" class="small">Coffee corner</text></g>
      <polygon :points="polygon([iso(5.3, 9.4), iso(8, 9.4), iso(8, 10.6), iso(5.3, 10.6)])" fill="#9bb7a6" stroke="#f9f0db" stroke-width="4" />
      <g :transform="at(5.8, 10.2)"><ellipse rx="25" ry="12" fill="#c9884d" /><circle cx="-16" cy="-9" r="10" fill="#e4a763" /><path d="M-24 -14 L-25 -24 L-15 -17 M-13 -17 L-6 -23 L-6 -11" fill="#e4a763" /><path d="M-23 -9 Q-19 -5 -16 -9 M20 -3 Q40 -20 18 -22" fill="none" stroke="#875635" stroke-width="3" /><text x="8" y="-26" class="small" fill="#657c70">z z</text></g>
      <!-- Desks are sorted by depth so front-row furniture overlaps naturally. -->
      <g v-for="desk in desks" :key="desk.person.id" class="interactive staff-desk" role="button" tabindex="0" :aria-label="`${desk.person.name}, ${desk.person.role}, ${tasks(desk.person.id).length} tasks${desk.person.on_leave ? ', on leave' : ''}`" @click="emit('select-staff', desk.person.id)" @keydown.enter.prevent="emit('select-staff', desk.person.id)" @keydown.space.prevent="emit('select-staff', desk.person.id)">
        <title>{{ desk.person.name }} · {{ desk.person.role }}{{ desk.person.on_leave ? ` · ${desk.person.on_leave.type}, back ${shortDate(desk.person.on_leave.to)}` : '' }}</title>
        <g :transform="at(desk.x + .7, desk.y + .85)"><ellipse cy="4" rx="24" ry="11" fill="#10201f" opacity=".12" /><path d="M-16 -27 Q0 -37 16 -27 V-5 H-16Z" fill="#54736a" /><path d="M0 -5 V12 M-15 16 L0 10 L15 16" stroke="#354f47" stroke-width="4" /></g>
        <IsoBlock :x="desk.x" :y="desk.y" :w="1.75" :d=".85" :h="27" />
        <g :transform="at(desk.x + .75, desk.y + .2, 27)"><rect x="-18" y="-28" width="36" height="25" rx="3" fill="#324a43" /><rect x="-14" y="-24" width="28" height="17" :fill="desk.person.on_leave ? '#51615a' : '#c3e1d4'" /><path d="M0 -3 V3 M-8 3 H8" stroke="#324a43" stroke-width="3" /></g>
        <g :transform="at(desk.x + .9, desk.y + 1.4)">
          <rect x="-54" y="0" width="108" height="27" rx="7" fill="#fff9ec" stroke="#cbbda4" /><text y="19" text-anchor="middle" class="name">{{ desk.person.name.trim().split(/\s+/)[0] }}</text>
          <circle cx="56" cy="1" r="14" :fill="desk.person.on_leave && tasks(desk.person.id).length ? '#e5484d' : '#10201f'" /><text x="56" y="6" text-anchor="middle" fill="white" class="small bold">{{ tasks(desk.person.id).length }}</text>
          <g v-if="desk.person.on_leave"><rect x="-70" y="30" width="140" height="51" rx="7" fill="#fff6db" stroke="#cbbda4" /><text y="47" text-anchor="middle" class="small bold">♧ On leave</text><text y="63" text-anchor="middle" class="tiny">{{ desk.person.on_leave.type.slice(0, 16) }} · back {{ shortDate(desk.person.on_leave.to) }}</text><path d="M-52 43 Q-45 30 -49 24 M-49 24 Q-58 20 -62 27 M-49 24 Q-41 19 -36 27" fill="none" stroke="#52865b" stroke-width="2" /></g>
          <g class="hover-label" transform="translate(0 30)"><rect x="-100" y="0" width="200" height="28" rx="6" fill="#10201f" /><text y="19" text-anchor="middle" fill="white" class="small">{{ desk.person.role }}</text></g>
        </g>
      </g>
      <Doctor v-for="doctor in doctors" :key="doctor.person.id" :person="doctor.person" :x="doctor.x" :y="doctor.y" :color="shirt(doctor.person.id)" :patients="doctor.patients" :proposed="doctor.proposed" @select="emit('select-staff', $event)" />
      <g v-if="phase === 'receiving'" :transform="at(.2, 10.3)" aria-label="Document ambulance arriving">
        <g class="ambulance"><path d="M-52 -41 H14 L36 -20 V2 H-52Z" fill="#fff9ec" stroke="#71978a" stroke-width="3" /><path d="M15 -35 L29 -20 H9 V-35Z" fill="#9dcad0" /><path d="M-50 -8 H34" stroke="#e5484d" stroke-width="6" /><path d="M-28 -33 V-15 M-37 -24 H-19" stroke="#e5484d" stroke-width="6" /><circle cx="-32" cy="4" r="9" fill="#10201f" /><circle cx="19" cy="4" r="9" fill="#10201f" /><rect class="antenna" x="-5" y="-49" width="16" height="8" rx="3" fill="#58adff" /></g>
      </g>
      <!-- Mailroom remains a large keyboard-accessible drop target. -->
      <g class="interactive mailroom" :class="{ 'drop-active': dragging, disabled: busy }" role="button" :tabindex="busy ? -1 : 0" :aria-disabled="busy" :aria-label="busy ? 'Helper is busy' : 'Drop client documents here or choose files'" :transform="at(1.1, 9.4)" @click="choose" @keydown.enter.prevent="choose" @keydown.space.prevent="choose">
        <ellipse class="mail-glow" cy="0" rx="83" ry="34" fill="#76b900" opacity=".15" />
        <path d="M-37 -69 L11 -91 L49 -72 V-9 L0 16 L-37 -4Z" fill="#6d943c" stroke="#456c28" stroke-width="2" /><path d="M-37 -69 L0 -49 L49 -72 L11 -91Z" fill="#a9ce65" /><path d="M-28 -64 L0 -49 L0 16 L-37 -4 V-69Z" fill="#76b900" /><path d="M7 -44 L39 -60 V-47 L7 -31Z" fill="#193d2b" /><path d="M12 -48 L12 -67 L31 -76 L31 -57Z" fill="#fff9e9" /><path d="M16 -64 L27 -69 M16 -59 L25 -64" stroke="#a7b4a4" stroke-width="2" />
        <rect x="-124" y="27" width="248" height="59" rx="10" fill="#10201f" :stroke="dragging ? '#76b900' : '#597366'" stroke-width="2" /><text y="48" text-anchor="middle" fill="#b4d491" class="small bold">MAILROOM / DROP CHUTE</text><text y="71" text-anchor="middle" fill="#fff8e9" class="name">{{ busy ? 'Helper is busy' : 'Drop client documents here' }}</text>
      </g>
      <!-- Phase is supplied by real orchestration; no timers advance this character. -->
      <g class="helper-position" :style="helperPosition">
        <ellipse cy="9" rx="31" ry="12" fill="#10201f" opacity=".2" />
        <g class="helper-body" :class="{ happy: phase === 'applied' }">
          <rect x="-24" y="-6" width="13" height="17" rx="6" fill="#30443d" /><rect x="11" y="-6" width="13" height="17" rx="6" fill="#30443d" />
          <path d="M0 -68 V-79" stroke="#a1be7f" stroke-width="4" /><circle class="antenna" cy="-83" r="5" :fill="phase === 'error' || phase === 'quarantine' ? '#e5484d' : '#b8e575'" />
          <rect x="-30" y="-66" width="60" height="64" rx="23" fill="#76b900" stroke="#568a14" stroke-width="2" /><rect x="-24" y="-54" width="48" height="30" rx="12" fill="#10201f" />
          <path v-if="phase === 'error'" d="M-15 -45 L-6 -41 M6 -41 L15 -45 M-7 -31 Q0 -38 7 -31" fill="none" stroke="#e8f8c9" stroke-width="3" stroke-linecap="round" />
          <g v-else><rect x="-15" y="-46" width="7" height="10" rx="3" fill="#e8f8c9" /><rect x="8" y="-46" width="7" height="10" rx="3" fill="#e8f8c9" /><path d="M-5 -31 Q0 -27 5 -31" fill="none" stroke="#e8f8c9" stroke-width="2" /></g>
          <path d="M-31 -35 L-40 -19" stroke="#76b900" stroke-width="9" stroke-linecap="round" /><path class="helper-arm" :class="{ wave: phase === 'applied' }" d="M31 -35 L41 -20" stroke="#76b900" stroke-width="9" stroke-linecap="round" />
          <circle cy="-14" r="4" fill="#d7efb1" />
          <g v-if="phase === 'receiving' || phase === 'awaiting'" transform="translate(25 -30) rotate(12)"><rect x="-6" y="-2" width="28" height="35" rx="3" :fill="phase === 'awaiting' ? '#b88b55' : '#fff9ec'" /><rect x="-2" y="3" width="20" height="25" fill="#fff9ec" /><path d="M2 10 H14 M2 16 H14 M2 22 H10" stroke="#7f9689" stroke-width="2" /></g>
          <g v-if="phase === 'reading'" transform="translate(41 -57)"><text class="gear" text-anchor="middle" font-size="32" fill="#4d7359">⚙</text><text x="-41" y="-40" text-anchor="middle" class="thinking" font-size="29" fill="#76b900">•••</text></g>
          <rect v-if="phase === 'filing'" x="33" y="-30" width="23" height="24" fill="#f5a524" transform="rotate(-12 33 -30)" />
          <g v-if="phase === 'quarantine'" transform="translate(34 -36)"><path d="M0 0 L14 -5 L28 0 V13 Q25 25 14 29 Q3 25 0 13Z" fill="#e5484d" stroke="#fff4e4" stroke-width="2" /><path d="M8 12 L12 17 L21 7" stroke="white" stroke-width="3" fill="none" /></g>
          <text v-if="phase === 'error'" x="39" y="-54" fill="#e5484d" font-size="38" font-weight="900">!</text>
        </g>
        <g v-if="phase === 'applied'" class="confetti"><path v-for="(lane, i) in lanes" :key="lane.key" :d="`M${-55 + i * 35} -95 l8 -13 m-3 45 l8 5`" :stroke="lane.color" stroke-width="5" fill="none" /></g>
        <g v-if="helperSay.trim()" class="speech" :transform="`translate(0 ${-112 - speech.length * 10})`"><title>{{ helperSay }}</title><rect x="-174" y="-25" width="348" :height="speech.length * 22 + 17" rx="14" fill="#fffdf3" stroke="#779c60" stroke-width="2" /><path :d="`M-9 ${speech.length * 22 - 9} L0 ${speech.length * 22 + 4} L9 ${speech.length * 22 - 9}`" fill="#fffdf3" stroke="#779c60" stroke-width="2" /><text v-for="(line, i) in speech" :key="i" :y="-4 + i * 22" text-anchor="middle" class="speech-text">{{ line }}</text></g>
        <rect x="-48" y="20" width="96" height="24" rx="7" fill="#10201f" /><text y="37" text-anchor="middle" fill="#b7e578" class="small bold">Office helper</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.office-floor { width: 100%; position: relative; border-radius: 18px; background: #10201f; overflow: hidden; }
.scene { display: block; width: 100%; height: auto; font-family: ui-rounded, 'Trebuchet MS', system-ui, sans-serif; color: #10201f; }
.scene text { pointer-events: none; }
.ward-heading { font-size: 17px; font-weight: 900; }
.ambulance { animation: arrive .7s ease-out both; }
@keyframes arrive { from { transform: translateX(-55px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
.heading { font-size: 19px; font-weight: 800; }
.name { font-size: 16px; font-weight: 700; }
.small { font-size: 14px; }
.tiny { font-size: 12px; }
.lane { font-size: 13px; font-weight: 800; }
.bold { font-weight: 800; }
.speech-text { font-size: 16px; font-weight: 600; }
.interactive { cursor: pointer; outline: none; }
.interactive:focus-visible { filter: drop-shadow(0 0 5px #d8ff9c) drop-shadow(0 0 2px #fff); }
.hover-label { opacity: 0; pointer-events: none; transition: opacity .18s; }
.interactive:hover .hover-label, .interactive:focus-visible .hover-label { opacity: 1; }
.staff-desk:hover .name, .staff-desk:focus-visible .name { fill: #427407; }
.board:hover .board-frame { stroke: #76b900; }
.proposed { stroke: #f5a524; stroke-dasharray: 9 6; animation: proposal 2.2s ease-in-out infinite; }
.helper-position { transition: transform 1s cubic-bezier(.4, 0, .2, 1); }
.helper-body { animation: bob 2.6s ease-in-out infinite; }
.person { animation: bob 4.5s ease-in-out infinite; }
.plant { transform-box: fill-box; transform-origin: center bottom; animation: sway 5s ease-in-out infinite; }
.antenna { animation: blink 2s ease-in-out infinite; }
.steam { animation: steam 3s ease-in-out infinite; }
.gear { transform-box: fill-box; transform-origin: center; animation: spin 5s linear infinite; }
.thinking { animation: blink 1.3s ease-in-out infinite; }
.monitor-glow { animation: monitor 1.5s ease-in-out infinite; }
.quarantine-flash { animation: alert 1s ease-in-out infinite; }
.wave { transform-origin: 30px -35px; animation: wave .7s ease-in-out infinite alternate; }
.confetti { animation: celebrate 1.5s ease-out both; pointer-events: none; }
.mail-glow { transition: opacity .2s; }
.mailroom:hover .mail-glow, .drop-active .mail-glow { opacity: .55; }
.drop-active .mail-glow { animation: proposal 1s ease-in-out infinite; }
.dragging { box-shadow: inset 0 0 0 3px #76b900; }
.disabled { cursor: wait; }
.file-input, .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }
@keyframes bob { 50% { transform: translateY(-3px); } }
@keyframes sway { 50% { transform: rotate(4deg); } }
@keyframes blink { 50% { opacity: .4; } }
@keyframes proposal { 50% { stroke-opacity: .5; } }
@keyframes steam { 0%, 100% { opacity: .15; transform: translateY(0); } 50% { opacity: .7; transform: translateY(-7px); } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes monitor { 50% { fill: #b7ec70; } }
@keyframes alert { 50% { opacity: .6; } }
@keyframes wave { to { transform: rotate(-75deg); } }
@keyframes celebrate { from { opacity: 1; transform: translateY(10px) scale(.6); } to { opacity: 0; transform: translateY(-65px) scale(1.5); } }
@media (prefers-reduced-motion: reduce) { .office-floor *, .office-floor *::before, .office-floor *::after { animation: none !important; transition: none !important; } .confetti { opacity: .8; } }
</style>
