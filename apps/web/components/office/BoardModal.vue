<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import type { Card, Staff } from '../../types/office'
import TaskCard from './board/TaskCard.vue'
import CardDetail from './board/CardDetail.vue'
import { avatarColor, hours, initials, priorities } from './board/presentation'

const props = withDefaults(defineProps<{
  open: boolean; cards: Card[]; staff: Staff[]; changeSetId: string | null
  decisionStatus: string | null; busy: boolean; initialView?: 'priority' | 'person'; focusStaffId?: string | null
}>(), { initialView: 'priority', focusStaffId: null })
const emit = defineEmits<{ close: []; approve: []; reject: [] }>()
const view = ref<'priority' | 'person'>('priority')
const selectedId = ref<string | null>(null)
const selected = computed(() => props.cards.find(card => card.id === selectedId.value))
const panel = ref<HTMLElement | null>(null)
const pending = computed(() => !!props.changeSetId && !props.decisionStatus)
const status = computed(() => pending.value ? 'Proposed - awaiting PM approval' : props.decisionStatus === 'applied' ? 'Applied' : props.decisionStatus)
const positionedCards = computed(() => {
  const rows = new Map<string, number>()
  return props.cards.map(card => {
    const row = (rows.get(card.priority) ?? 1) + 1
    rows.set(card.priority, row)
    return { card, column: priorities.findIndex(p => p.id === card.priority) + 1, row }
  })
})
const lanes = computed(() => props.staff.map(person => {
  const cards = props.cards.filter(card => card.staff.some(assignment => assignment.staff_id === person.id))
  const estimated = cards.reduce((sum, card) => sum + (Number.isFinite(card.est?.pert) ? Math.max(0, card.est!.pert!) : 0), 0)
  const allocated = Math.max(0, person.allocated_h ?? 0)
  const capacity = Math.max(0, person.weekly_capacity_h ?? 0)
  const scale = Math.max(capacity, allocated + estimated, 1)
  return { person, cards, estimated, allocatedWidth: allocated / scale * 100, estimateWidth: estimated / scale * 100, capacityMark: capacity / scale * 100 }
}))
const unassigned = computed(() => props.cards.filter(card => !card.staff.length))
let previousFocus: HTMLElement | null = null
let previousOverflow: string | null = null
let cardTrigger: HTMLElement | null = null
async function focusLane() {
  await nextTick()
  if (!props.open || !props.focusStaffId) return
  const lane = Array.from(panel.value?.querySelectorAll<HTMLElement>('[data-staff-id]') ?? []).find(el => el.dataset.staffId === props.focusStaffId)
  lane?.scrollIntoView({ block: 'center', behavior: 'instant' })
  lane?.focus({ preventScroll: true })
}
async function selectCard(card: Card) {
  cardTrigger = document.activeElement as HTMLElement
  selectedId.value = card.id
  await nextTick()
  panel.value?.querySelector<HTMLElement>('.detail button')?.focus()
}
async function closeDetail() {
  selectedId.value = null
  await nextTick()
  if (cardTrigger?.isConnected) cardTrigger.focus()
  else panel.value?.focus()
}
function keydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault(); event.stopPropagation()
    if (selected.value) void closeDetail()
    else emit('close')
  }
  if (event.key !== 'Tab') return
  const scope = selected.value ? panel.value?.querySelector('.detail') : panel.value
  const elements = Array.from(scope?.querySelectorAll<HTMLElement>('button:not(:disabled), [tabindex="0"]') ?? []).filter(el => el.getClientRects().length)
  const first = elements[0], last = elements.at(-1)
  if (!first) { event.preventDefault(); panel.value?.focus(); return }
  if (event.shiftKey && (document.activeElement === first || !elements.includes(document.activeElement as HTMLElement))) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && (document.activeElement === last || !elements.includes(document.activeElement as HTMLElement))) { event.preventDefault(); first.focus() }
}
function unlock() {
  if (previousOverflow !== null) { document.body.style.overflow = previousOverflow; previousOverflow = null }
  if (previousFocus?.isConnected) previousFocus.focus()
}
watch(() => props.open, async open => {
  if (typeof document === 'undefined') return
  if (!open) { selectedId.value = null; unlock(); return }
  previousFocus = document.activeElement as HTMLElement
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  view.value = props.focusStaffId ? 'person' : props.initialView
  selectedId.value = null
  await nextTick()
  panel.value?.focus()
  await focusLane()
}, { immediate: true })
watch(() => props.focusStaffId, async id => {
  if (props.open && id) { view.value = 'person'; await focusLane() }
})
watch(selected, (card, previous) => { if (!card && previous && props.open) void closeDetail() })
onBeforeUnmount(() => { if (typeof document !== 'undefined') unlock() })
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="office-board-backdrop" @click.self="emit('close')" @keydown="keydown">
        <section ref="panel" class="office-board" role="dialog" aria-modal="true" aria-labelledby="office-board-title" aria-describedby="office-board-caption" tabindex="-1">
          <div class="board-main" :inert="selected ? true : undefined">
            <header class="board-header">
              <div class="heading"><h1 id="office-board-title">PRJ-SPL Kanban</h1><span v-if="status" class="status" :class="{ pending, applied: decisionStatus === 'applied' }" role="status">{{ status }}</span></div>
              <div class="toolbar"><div class="view-toggle" role="group" aria-label="Group board"><button :aria-pressed="view === 'priority'" @click="view = 'priority'">By priority</button><button :aria-pressed="view === 'person'" @click="view = 'person'">By person</button></div><div v-if="pending" class="decisions"><button class="reject" :disabled="busy" @click="emit('reject')">Reject</button><button class="approve" :disabled="busy" @click="emit('approve')">{{ busy ? 'Working…' : 'Approve' }}</button></div><button class="close" aria-label="Close Kanban board" @click="emit('close')">✕</button></div>
              <p id="office-board-caption">Staff assignments are recommendations and need human approval.</p>
            </header>
            <main class="board-content">
              <div v-if="!cards.length" class="empty"><span aria-hidden="true">▤</span><p>No board yet - drop a client brief at the mailroom.</p></div>
              <TransitionGroup v-else-if="view === 'priority'" name="card" tag="div" class="priority-grid">
                <h2 v-for="(priority, index) in priorities" :key="`heading-${priority.id}`" class="column-heading" :style="{ gridColumn: index + 1, gridRow: 1, '--priority': priority.color }">{{ priority.label }}<span>{{ cards.filter(card => card.priority === priority.id).length }}</span></h2>
                <TaskCard v-for="item in positionedCards" :key="item.card.id" :card="item.card" :style="{ gridColumn: item.column, gridRow: item.row }" @select="selectCard" />
              </TransitionGroup>
              <div v-else class="people-board">
                <section v-for="lane in lanes" :key="lane.person.id" class="person-lane" :class="{ away: lane.person.on_leave, focused: focusStaffId === lane.person.id }" :data-staff-id="lane.person.id" tabindex="-1" :aria-label="lane.person.name">
                  <div class="person-summary"><div class="identity"><span class="avatar" :style="{ background: avatarColor(lane.person.id) }">{{ initials(lane.person.name) }}</span><div><h2>{{ lane.person.name }}</h2><p>{{ lane.person.role }}</p></div></div>
                    <p v-if="lane.person.on_leave" class="leave"><span aria-hidden="true">🌴</span> On leave until {{ lane.person.on_leave.to }}</p>
                    <p v-if="lane.person.on_leave && lane.cards.length" class="leave-warning">Assigned while on leave - reassign before approving</p>
                    <div class="capacity"><p>{{ hours(lane.person.allocated_h) }} / {{ hours(lane.person.weekly_capacity_h) }} h allocated</p><div class="capacity-track" role="img" :aria-label="`${hours(lane.person.allocated_h)} hours allocated of ${hours(lane.person.weekly_capacity_h)} hours capacity, estimated additional ${hours(lane.estimated)} hours`"><span class="allocated" :style="{ width: `${lane.allocatedWidth}%` }" /><span class="estimated" :style="{ width: `${lane.estimateWidth}%` }" /><i v-if="lane.person.weekly_capacity_h" :style="{ left: `${lane.capacityMark}%` }" /></div><p class="estimate-label">est. +{{ hours(lane.estimated) }} h this change set</p><small v-if="lane.cards.some(card => card.est?.pert == null)">Some cards have no expected estimate.</small></div>
                  </div>
                  <TransitionGroup name="card" tag="div" class="lane-cards"><TaskCard v-for="card in lane.cards" :key="card.id" :card="card" @select="selectCard" /><p v-if="!lane.cards.length" key="empty" class="lane-empty">No cards assigned.</p></TransitionGroup>
                </section>
                <section class="person-lane"><div class="person-summary"><h2>Unassigned</h2><p>{{ unassigned.length }} cards</p></div><TransitionGroup name="card" tag="div" class="lane-cards"><TaskCard v-for="card in unassigned" :key="card.id" :card="card" @select="selectCard" /><p v-if="!unassigned.length" key="empty" class="lane-empty">No unassigned cards.</p></TransitionGroup></section>
              </div>
            </main>
          </div>
          <div v-if="selected" class="drawer-backdrop" aria-hidden="true" @click="closeDetail" />
          <Transition name="drawer"><CardDetail v-if="selected" :card="selected" @close="closeDetail" /></Transition>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.office-board-backdrop{position:fixed;inset:0;z-index:1000;background:#071311cc;backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box;font-family:ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif}.office-board{position:relative;width:100%;height:100%;max-width:1800px;background:#efe7d8;border-radius:24px;overflow:hidden;box-shadow:0 30px 100px #0007;color:#1f2a2e;outline:none}.board-main{height:100%;display:flex;flex-direction:column;min-height:0}.board-header{background:#10201f;color:#e8f3ee;padding:24px 30px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}.heading{display:flex;gap:20px;align-items:center;flex-wrap:wrap;flex:1}h1{font-size:clamp(24px,2.5vw,38px);margin:0;letter-spacing:-1px}.status{padding:8px 12px;background:#344642;border-radius:30px;font-size:15px;font-weight:700}.status.pending{background:#f5a524;color:#382300}.status.applied{background:#76b900;color:#142300}.toolbar,.decisions,.view-toggle{display:flex;align-items:center;gap:8px}.board-header button{font-family:inherit;font-size:16px;font-weight:700;min-height:46px;padding:10px 16px;border:1px solid #48645d;background:#203a34;color:#e8f3ee;border-radius:10px;cursor:pointer}.board-header button:focus-visible{outline:3px solid #fff;outline-offset:3px}.board-header button:disabled{opacity:.5;cursor:wait}.view-toggle{gap:0;border:1px solid #48645d;border-radius:12px;padding:3px}.view-toggle button{border:0;background:transparent}.view-toggle button[aria-pressed=true]{background:#efe7d8;color:#10201f}.board-header .approve{background:#76b900;color:#142300;border-color:#76b900}.board-header .reject{border-color:#e8898c;color:#ffb9bc}.board-header .close{font-size:23px;min-width:46px;padding:5px}.board-header>p{flex-basis:100%;margin:0;color:#baccc4;font-size:15px}.board-content{padding:26px;overflow:auto;flex:1;min-height:0}.priority-grid{display:grid;grid-template-columns:repeat(4,minmax(240px,1fr));gap:18px;align-items:stretch;padding-bottom:8px}.column-heading{margin:0;padding:16px;background:#fffdf8;border-top:7px solid var(--priority);border-radius:12px;display:flex;align-items:center;justify-content:space-between;font-size:23px;gap:12px}.column-heading span{background:var(--priority);color:#10201f;min-width:34px;height:34px;display:grid;place-items:center;border-radius:50%;font-size:18px}.people-board{display:flex;flex-direction:column;gap:22px}.person-lane{display:grid;grid-template-columns:280px minmax(0,1fr);gap:24px;background:#f8f4eb;border:2px solid #d6cebf;border-radius:18px;padding:22px;scroll-margin:20px}.person-lane.focused{border-color:#76b900;box-shadow:0 0 0 4px #76b90040}.person-lane:focus-visible{outline:3px solid #426b60}.person-lane.away{background:#e1e3df}.away .identity{filter:grayscale(1)}.identity{display:flex;align-items:center;gap:12px}.avatar{display:grid;place-items:center;flex-shrink:0;width:54px;height:54px;border-radius:50%;font-size:21px;font-weight:800;color:white;box-shadow:0 3px 0 #0002}.person-summary h2{font-size:23px;line-height:1.2;margin:0 0 6px}.person-summary p{margin:6px 0;font-size:16px}.leave{margin-top:18px!important}.leave-warning{background:#fbdcdd;color:#8e2227;padding:10px;border:1px solid #e5484d;border-radius:9px;font-weight:700}.capacity{margin-top:22px}.capacity-track{height:18px;display:flex;position:relative;background:#d4d9d0;border-radius:5px;margin:10px 0}.allocated{background:#76b900;border-radius:5px 0 0 5px}.estimated{background:repeating-linear-gradient(135deg,#f5a524 0 4px,#fff0cd 4px 8px)}.capacity-track i{position:absolute;width:2px;height:24px;top:-3px;background:#10201f;transform:translateX(-2px)}.estimate-label{font-weight:700;color:#765000}.capacity small{color:#626b64}.lane-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px;align-content:start;position:relative}.lane-empty{color:#637068;font-size:18px;padding:12px}.empty{min-height:50vh;display:grid;align-content:center;justify-items:center;text-align:center;font-size:26px;color:#5b6960}.empty span{font-size:80px;color:#76b900}.empty p{max-width:540px}.drawer-backdrop{position:absolute;inset:0;background:#10201f88;z-index:2}.card-move,.card-enter-active,.card-leave-active{transition:transform .4s ease,opacity .25s ease}.card-enter-from{opacity:0;transform:scale(.9)}.card-leave-to{opacity:0;transform:scale(.94)}.card-leave-active{position:absolute;pointer-events:none}.drawer-enter-active,.drawer-leave-active{transition:transform .28s ease}.drawer-enter-from,.drawer-leave-to{transform:translateX(100%)}.modal-enter-active,.modal-leave-active{transition:opacity .2s ease}.modal-enter-from,.modal-leave-to{opacity:0}@media(max-width:1000px){.board-header{padding:20px}.toolbar{flex-wrap:wrap}.person-lane{grid-template-columns:220px minmax(0,1fr)}}@media(max-width:650px){.office-board-backdrop{padding:8px}.office-board{border-radius:16px}.board-content{padding:16px}.board-header{gap:12px;padding:16px}.heading{gap:10px}.toolbar{width:100%}.board-header button{padding:8px 12px;font-size:14px}.person-lane{grid-template-columns:1fr;padding:16px}.board-header>p{font-size:13px}.priority-grid{grid-template-columns:repeat(4,260px)}.lane-cards{grid-template-columns:1fr}}@media(prefers-reduced-motion:reduce){.card-move,.card-enter-active,.card-leave-active,.drawer-enter-active,.drawer-leave-active,.modal-enter-active,.modal-leave-active{transition:none!important}}
</style>
