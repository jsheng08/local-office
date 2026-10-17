<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import type { Card, Staff } from '~/types/office'
import { changeCost, staffing, sumEstimates } from './doc/presentation'

const props = defineProps<{
  open: boolean; analysis: any; cards: Card[]; staff: Staff[]
  docName: string | null; user: string; busy: boolean; error: any
}>()
const emit = defineEmits<{ close: []; approve: []; reject: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const paper = ref<HTMLElement | null>(null)
const date = ref('')
const hasChanges = computed(() => Array.isArray(props.analysis?.changes))
const requirements = computed<any[]>(() => props.analysis?.requirements || [])
const cost = computed(() => changeCost(props.analysis?.changes || []))
const totals = computed(() => {
  const estimates = requirements.value.map(r => r.triage)
  return { pert: sumEstimates(estimates, 'pert'), low: sumEstimates(estimates, 'low'), high: sumEstimates(estimates, 'high') }
})
const rows = computed(() => hasChanges.value
  ? props.analysis.changes.filter((c: any) => c.change !== 'unchanged').map((c: any) => {
    const requirement = requirements.value.find(r => r.id === c.req_id)
    const card = props.cards.find(r => r.id === c.req_id)
    return { ...c, id: c.req_id, citations: c.citations ?? c.after?.citations ?? requirement?.citations ?? c.before?.citations ?? card?.citations ?? [] }
  })
  : requirements.value.map(r => ({ ...r, after: { ...r.triage, priority: r.priority }, reason: r.reason ?? r.triage?.reason })))
const recommendations = computed(() => staffing(props.cards, props.staff))
const ignored = computed<any[]>(() => props.analysis?.ignored_instructions || [])
const labels: Record<string, string> = { must: 'Must', should: 'Should', could: 'Nice', wont: 'Later' }
const priority = (p: any) => labels[p] || p || '—'
const signed = (value: number) => `${value >= 0 ? '+' : '−'}${fmtNum(Math.abs(value))}`
const range = (estimate: any) => estimate ? `${fmtNum(estimate.low)}–${fmtNum(estimate.high)} est. hours` : '—'

async function syncDialog() {
  await nextTick()
  if (props.open && dialog.value && !dialog.value.open) {
    date.value = new Date().toLocaleDateString('en-MY', { day: 'numeric', month: 'long', year: 'numeric' })
    dialog.value.showModal()
    if (paper.value) paper.value.scrollTop = 0
  } else if (!props.open && dialog.value?.open) dialog.value.close()
}
watch(() => props.open, syncDialog)
onMounted(syncDialog)
function backdrop(event: MouseEvent) {
  if (event.target !== dialog.value) return
  const bounds = dialog.value.getBoundingClientRect()
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <dialog ref="dialog" class="change-document" aria-label="Change request sign-off" :aria-busy="busy" @cancel.prevent="emit('close')" @click="backdrop">
      <article ref="paper" class="paper">
        <div class="document-tools">
          <span class="pending">Pending human approval</span>
          <button type="button" class="close" autofocus aria-label="Close change request" @click="emit('close')">Close <span aria-hidden="true">×</span></button>
        </div>
        <header class="letterhead">
          <div><p class="company">Teratai Digital · Change Request</p><h1>For your sign-off.</h1><p>Sinar Pantai Logistics · PRJ-SPL</p></div>
          <div class="stamp">LOCAL · ON-DEVICE</div>
        </header>
        <dl class="metadata">
          <div><dt>Source document</dt><dd>{{ docName || 'Not provided' }}</dd></div>
          <div><dt>Date</dt><dd>{{ date }}</dd></div>
          <div class="change-set"><dt>Change set</dt><dd>{{ analysis?.change_set_id || 'Not provided' }}</dd></div>
        </dl>

        <section>
          <h2>Summary</h2>
          <div v-if="hasChanges" class="summary">
            <p class="impact">{{ signed(cost.hours) }} <span>est. hours</span></p>
            <p>{{ cost.added }} added · {{ cost.modified }} modified · {{ cost.removed }} removed</p>
            <p class="note">Net cost of change, based on returned estimates.</p>
            <p v-if="cost.missing" class="warning">{{ cost.missing }} change(s) have missing estimates and are excluded from the total.</p>
          </div>
          <div v-else class="summary">
            <p class="impact">{{ fmtNum(totals.pert.total) }} <span>est. hours</span></p>
            <p>{{ requirements.length }} requirements · {{ fmtNum(totals.low.total) }}–{{ fmtNum(totals.high.total) }} est. hours (low–high)</p>
            <p v-if="totals.pert.missing || totals.low.missing || totals.high.missing" class="warning">Excluded missing estimates: {{ totals.pert.missing }} expected, {{ totals.low.missing }} low, {{ totals.high.missing }} high. Totals may be partial.</p>
          </div>
        </section>

        <section>
          <h2>{{ hasChanges ? 'Proposed changes' : 'Proposed requirements' }}</h2>
          <div class="table-scroll" tabindex="0" role="region" aria-label="Requirement estimates and source citations">
            <table>
              <thead><tr><th>Requirement</th><th>Priority</th><th>Est. hours (low–high)</th><th>Reason &amp; evidence</th></tr></thead>
              <tbody>
                <tr v-for="row in rows" :key="row.id">
                  <td><code>{{ row.id }}</code><span v-if="row.change" class="change-kind">{{ row.change }}</span><strong class="title">{{ row.title }}</strong></td>
                  <td><div class="priority-flow"><template v-if="hasChanges"><span class="priority" :class="row.before?.priority">{{ priority(row.before?.priority) }}</span><span aria-label="to">→</span></template><span class="priority" :class="row.after?.priority">{{ priority(row.after?.priority) }}</span></div></td>
                  <td class="estimates"><template v-if="hasChanges"><div>{{ range(row.before) }}</div><div class="estimate-arrow">↓</div></template><div>{{ range(row.after) }}</div></td>
                  <td>{{ row.reason || 'No reason returned.' }}<div class="citations"><span v-for="(citation, index) in row.citations || []" :key="index" class="citation" :title="citation.quote">{{ citation.paragraph_id }} · {{ citation.status || 'Status not provided' }}</span><span v-if="!row.citations?.length" class="note">No citations returned.</span></div></td>
                </tr>
                <tr v-if="!rows.length"><td colspan="4">{{ hasChanges ? 'No changed requirements returned.' : 'No requirements returned.' }}</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="security">
          <h2>Security</h2>
          <div v-for="(item, index) in ignored" :key="index" class="ignored">
            <div><span class="citation">{{ item.paragraph_id }}</span> <strong>reported, not executed</strong></div>
            <blockquote>“{{ item.quote }}”</blockquote>
          </div>
          <p v-if="!ignored.length">No ignored instructions reported in this analysis.</p>
        </section>

        <section>
          <h2>Staffing recommendations</h2>
          <div v-for="entry in recommendations" :key="entry.person.id" class="staff-row">
            <div><strong>{{ entry.person.name }}</strong><p class="note">{{ entry.person.role }}</p><p v-if="entry.person.on_leave" class="leave">On leave until {{ entry.person.on_leave.to }} — reassign</p></div>
            <div class="staff-cards"><span v-for="card in entry.cards" :key="card.id" class="citation">{{ card.id }}</span></div>
            <div><strong>{{ fmtNum(entry.estimate.total) }} est. hours</strong><p v-if="entry.estimate.missing" class="note">{{ entry.estimate.missing }} missing estimates excluded.</p></div>
          </div>
          <p v-if="!recommendations.length" class="note">No staff recommendations matched the supplied roster.</p>
          <p class="staff-caption">Recommendations only. Approving applies the board; staff assignments still need a human to confirm.</p>
          <p class="note">Est. hours show the full effort of each recommended card, not an allocation between staff.</p>
        </section>

        <footer class="sign-off">
          <h2>PM sign-off</h2>
          <p>Approved by: <strong>{{ user }}</strong></p>
          <div class="signature" aria-hidden="true"></div>
          <p class="note">Your approval is recorded when the server accepts this request.</p>
          <div v-if="error" role="alert" class="error"><p v-if="error.status === 403">The server refused: only a project manager can approve.</p><pre>{{ error.body }}</pre></div>
          <div class="actions">
            <button type="button" class="approve" :disabled="busy" @click="emit('approve')"><span v-if="busy" class="spinner" aria-hidden="true"></span>{{ busy ? 'Applying…' : 'Sign & apply to board' }}</button>
            <button type="button" class="reject" :disabled="busy" @click="emit('reject')">Reject</button>
          </div>
          <p v-if="busy" role="status" class="note">Applying… waiting for the server.</p>
        </footer>
      </article>
    </dialog>
  </Teleport>
</template>

<style scoped>
.change-document { padding: 0; border: 0; border-radius: 5px; width: min(1120px, calc(100vw - 48px)); max-width: none; max-height: calc(100dvh - 48px); color: #10201f; background: #fff; box-shadow: 0 24px 90px #0007, 8px 8px 0 #efe7d8; font: 18px/1.55 ui-sans-serif, system-ui, sans-serif; }
.change-document::backdrop { background: #10201fcf; backdrop-filter: blur(5px); }
.paper { max-height: calc(100dvh - 48px); overflow: auto; overscroll-behavior: contain; padding: 24px 48px 40px; box-sizing: border-box; background: linear-gradient(#76b900, #76b900) top / 100% 6px no-repeat #fff; }
p, h1, h2, blockquote { margin: 0; }
.document-tools, .letterhead, .actions { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.document-tools { margin-bottom: 28px; }
.pending, .note, dt { color: #57645e; font-size: 15px; }
button { font: inherit; cursor: pointer; border-radius: 7px; padding: 12px 20px; }
button:focus-visible, .table-scroll:focus-visible { outline: 3px solid #427400; outline-offset: 4px; }
.close { background: #f5f3ee; color: #10201f; border: 1px solid #d6dcd5; padding: 6px 14px; }
.close span { font-size: 24px; margin-left: 8px; }
.letterhead { border-bottom: 3px solid #10201f; padding-bottom: 26px; }
.company { font-weight: 750; font-size: 17px; }
h1 { font: 600 clamp(32px, 4vw, 48px)/1.2 Georgia, 'Times New Roman', serif; margin: 12px 0; }
h2 { font: 600 28px/1.2 Georgia, 'Times New Roman', serif; margin-bottom: 16px; }
.stamp { flex-shrink: 0; color: #426c00; border: 3px double #76b900; padding: 12px; transform: rotate(-6deg); font-size: 14px; font-weight: 800; letter-spacing: .04em; }
.metadata { display: grid; grid-template-columns: 2fr 1fr; gap: 18px 28px; padding-bottom: 24px; border-bottom: 1px solid #cbd2cc; }
dd { margin: 3px 0 0; font-weight: 600; overflow-wrap: anywhere; }
.change-set { grid-column: 1 / -1; }
section { margin-top: 32px; }
.summary { background: #f4f7ef; border-left: 5px solid #76b900; padding: 18px 22px; }
.impact { font-size: 36px; font-weight: 750; line-height: 1.3; font-variant-numeric: tabular-nums; }
.impact span { font-size: 20px; font-weight: 500; }
.warning { color: #805000; margin-top: 10px; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; font-size: 16px; min-width: 770px; }
th { background: #10201f; color: #fff; font-size: 15px; font-weight: 600; }
th, td { padding: 15px 12px; vertical-align: top; }
td { border-bottom: 1px solid #d8ded8; overflow-wrap: anywhere; }
th:first-child { width: 25%; } th:last-child { width: 32%; }
.title { display: block; margin-top: 7px; }
code { font-size: 15px; }
.change-kind { font-size: 13px; margin-left: 8px; color: #57645e; }
.priority-flow, .citations, .staff-cards { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.priority { display: inline-block; border-radius: 5px; border-left: 4px solid #8a949b; padding: 3px 8px; background: #eef0f1; font-size: 14px; font-weight: 750; }
.priority.must { border-color: #e5484d; background: #ffe9ea; color: #8a2026; }
.priority.should { border-color: #f5a524; background: #fff0d4; color: #714700; }
.priority.could { border-color: #3fb26f; background: #e4f6eb; color: #1b6037; }
.priority.wont { border-color: #8a949b; }
.estimates { font-variant-numeric: tabular-nums; font-size: 15px; }
.estimate-arrow { color: #57645e; }
.citations { margin-top: 12px; }
.citation { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 13px; background: #edf1e9; color: #364731; overflow-wrap: anywhere; }
.security { border: 1px solid #d8ccb6; background: #faf7f0; padding: 22px; }
.ignored + .ignored { margin-top: 20px; }
.ignored strong { color: #805000; font-size: 15px; }
blockquote { margin-top: 10px; padding-left: 15px; border-left: 3px solid #f5a524; overflow-wrap: anywhere; white-space: pre-wrap; }
.staff-row { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 18px; padding: 18px 0; border-bottom: 1px solid #d8ded8; }
.leave { color: #ad252c; background: #fff0f0; border-left: 4px solid #e5484d; padding: 6px 9px; margin-top: 8px; font-size: 16px; font-weight: 650; }
.staff-caption { margin-top: 18px; }
.sign-off { margin-top: 36px; border-top: 3px solid #10201f; padding-top: 26px; }
.signature { border-bottom: 1px solid #10201f; width: min(380px, 100%); height: 38px; margin-bottom: 10px; }
.actions { justify-content: flex-start; flex-wrap: wrap; margin-top: 24px; }
.approve { display: inline-flex; align-items: center; gap: 12px; background: #76b900; color: #102000; border: 2px solid #76b900; font-size: 21px; font-weight: 800; padding: 16px 26px; }
.reject { border: 1px solid #b5bdb7; color: #94282d; background: #fff; font-weight: 650; }
button:disabled { opacity: .6; cursor: wait; }
.error { background: #fff0f0; border-left: 4px solid #e5484d; padding: 16px; margin-top: 22px; color: #8a2026; }
.error pre { white-space: pre-wrap; overflow-wrap: anywhere; font: inherit; margin: 8px 0 0; }
.spinner { width: 18px; height: 18px; border: 2px solid #10200055; border-top-color: #102000; border-radius: 50%; animation: turn .8s linear infinite; }
@keyframes turn { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spinner { animation: none; } }
@media (max-width: 650px) { .change-document { width: calc(100vw - 20px); max-height: calc(100dvh - 24px); } .paper { max-height: calc(100dvh - 24px); padding: 20px; } .letterhead { align-items: flex-start; flex-direction: column; } .stamp { transform: none; } .metadata, .staff-row { grid-template-columns: 1fr; } .change-set { grid-column: auto; } .approve { width: 100%; justify-content: center; } }
</style>
