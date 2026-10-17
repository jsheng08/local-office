<script setup lang="ts">
const o = useOffice()
const user = useCurrentUser()
const api = useApi()
const q = ref('')
const asking = ref(false)
const askRes = ref<any>(null)
const askErr = ref<any>(null)
const SUGGEST = ['What is everyone working on?', 'Who is on leave and what is blocked?', 'What changed in brief v2?']
async function ask(text?: string) {
  if (text) q.value = text
  if (!q.value.trim()) return
  asking.value = true; askErr.value = null; askRes.value = null
  try { askRes.value = await api('/api/knowledge/ask', { method: 'POST', body: { question: q.value } }) }
  catch (e) { askErr.value = e } finally { asking.value = false }
}
const boardOpen = ref(false)
const docOpen = ref(false)
const focusStaff = ref<string | null>(null)

onMounted(() => { o.loadStaff(); o.loadBoard() })
watch(user, () => o.loadStaff())

function openBoard(staffId: string | null = null) { focusStaff.value = staffId; boardOpen.value = true }
async function decide(d: 'approve' | 'reject') {
  await o.decide(d)
  if (!o.err.value) { docOpen.value = false; boardOpen.value = false }
}
function approveAsPM() { user.value = 'daniel'; o.err.value = null; docOpen.value = true }

const STEPS = [
  { k: 'receiving', n: 'Mailroom: document read on this ATOM' },
  { k: 'reading', n: 'Local Nemotron extracts requirements, quotes checked' },
  { k: 'quarantine', n: 'Hidden instructions quarantined' },
  { k: 'filing', n: 'Proposed cards pinned to the board' },
  { k: 'awaiting', n: 'PM approval required' },
]
const ORDER = ['idle', 'receiving', 'reading', 'quarantine', 'filing', 'awaiting', 'applied']
const stepCls = (k: string) => {
  const cur = ORDER.indexOf(o.phase.value), me = ORDER.indexOf(k)
  if (o.phase.value === 'applied' || cur > me) return 'done'
  return cur === me ? 'on' : ''
}
const title = computed(() => ({
  idle: o.cards.value.length ? 'Board is up to date' : 'Waiting for a client document',
  receiving: 'Document received', reading: 'Triage in progress', quarantine: 'Attack blocked',
  filing: 'Updating the board', awaiting: 'Waiting on a human', applied: 'Approved and applied', error: 'Something failed',
} as Record<string, string>)[o.phase.value])
const onLeave = computed(() => o.staff.value.filter(s => s.on_leave))
function actAs(u: string) { user.value = u }
</script>

<template>
  <section class="office">
    <div class="floorwrap">
      <OfficeFloor
        :staff="o.staff.value" :tasks-by-staff="o.tasksByStaff.value" :phase="o.phase.value"
        :helper-say="o.helperSay.value" :board-counts="o.boardCounts.value" :has-proposed="o.hasProposed.value"
        :quarantine-count="o.quarantine.value.length" :busy="o.busy.value" :cards="o.cards.value"
        @drop="o.upload" @open-board="openBoard()" @select-staff="(id: string) => openBoard(id)"
        @open-records="navigateTo('/audit')" @select-card="openBoard()" />

      <aside class="hud">
        <div class="k"><span class="dot" :class="o.phase.value" /> Office helper · local Nemotron</div>
        <h2>{{ title }}</h2>
        <p v-if="o.lastDoc.value?.filename" class="doc">
          📄 {{ o.lastDoc.value.filename }}
          <span v-if="o.lastDoc.value.method" class="muted">· {{ o.lastDoc.value.method }}<template v-if="o.lastDoc.value.chars"> · {{ fmtNum(o.lastDoc.value.chars, 0) }} chars</template></span>
        </p>
        <ol class="steps">
          <li v-for="s in STEPS" :key="s.k" :class="stepCls(s.k)">{{ s.n }}</li>
        </ol>
        <div v-if="o.busy.value" class="muted">{{ fmtNum(o.elapsed.value, 0) }} s · real call in progress</div>
        <div v-for="(a, i) in o.quarantine.value" :key="i" class="alert">
          <b>⛔ Quarantined {{ a.paragraph_id }}:</b> “{{ a.quote }}” was reported, not obeyed.
        </div>
        <div v-if="o.note.value" class="muted">{{ o.note.value }}</div>
        <div class="btns">
          <button class="btn" :class="{ on: user === 'aisyah' }" @click="actAs('aisyah')">Act as Analyst</button>
          <button class="btn" :class="{ on: user === 'daniel' }" @click="actAs('daniel')">Act as PM</button>
          <button class="btn primary" :disabled="!o.cards.value.length" @click="openBoard()">Open board</button>
        </div>
        <div v-if="o.hasProposed.value" class="btns">
          <button class="btn approve big" :disabled="o.busy.value" @click="approveAsPM">Approve as PM</button>
          <button class="btn" :disabled="o.busy.value" @click="actAs('aisyah'); decide('approve')">Try approving as Analyst</button>
        </div>
        <div class="btns">
          <button class="btn" :disabled="o.busy.value" @click="o.resetData()">↺ Reset data (v1 approved)</button>
        </div>
        <div v-if="o.baseline.value" class="muted">Baseline: real local run {{ o.baseline.value.run_id }} · {{ o.baseline.value.analyzed_at }}</div>
        <ErrBox :err="o.err.value" hint="Only a project manager can approve. Click “Act as PM”." />
        <div v-if="onLeave.length" class="leave">🌴 On leave today: {{ onLeave.map(s => s.name.split(' ')[0]).join(', ') }}</div>
      </aside>
    </div>

    <div class="askcard card">
      <h2>Ask the office <span class="sub">instead of a daily stand-up · answered by local Nemotron from the office notes</span></h2>
      <form class="askrow" @submit.prevent="ask()">
        <input v-model="q" placeholder="Who is working on what? What is blocked? Who is away?" :disabled="asking">
        <button class="btn primary" :disabled="asking || !q.trim()">{{ asking ? 'Thinking…' : 'Ask' }}</button>
      </form>
      <div class="chips"><button v-for="s in SUGGEST" :key="s" class="chip" :disabled="asking" @click="ask(s)">{{ s }}</button></div>
      <div v-if="askRes" class="answer">
        <p :class="{ muted: askRes.status !== 'answered' }">{{ askRes.answer }}</p>
        <div class="cites"><span v-for="c in askRes.citations" :key="c.id" class="cite">{{ c.folder === 'live' ? '⚡' : '📓' }} {{ c.id }}</span></div>
        <div class="muted small">{{ askRes.notes_visible }} notes you can access · {{ askRes.meta?.calls?.[0]?.model }} · {{ fmtNum(askRes.meta?.total_latency_ms, 0) }} ms</div>
      </div>
      <ErrBox :err="askErr" />
    </div>

    <OfficeBoardModal
      :open="boardOpen" :cards="o.cards.value" :staff="o.staff.value" :change-set-id="o.changeSetId.value"
      :decision-status="o.decisionStatus.value" :busy="o.busy.value" :focus-staff-id="focusStaff"
      :initial-view="focusStaff ? 'person' : 'priority'"
      @close="boardOpen = false" @approve="approveAsPM" @reject="decide('reject')" />

    <OfficeChangeRequestDoc
      :open="docOpen" :analysis="o.analysis.value" :cards="o.cards.value" :staff="o.staff.value"
      :doc-name="o.lastDoc.value?.filename || null" :user="user" :busy="o.busy.value" :error="o.err.value"
      @close="docOpen = false" @approve="decide('approve')" @reject="decide('reject')" />
  </section>
</template>

<style scoped>
.floorwrap { position: relative; border-radius: 18px; overflow: hidden; background: linear-gradient(#f7f2e9, #ebe1cf); }
.hud { position: absolute; left: 18px; bottom: 18px; width: 380px; max-width: calc(100% - 36px);
  background: rgba(16, 32, 31, .96); color: #e8f3ee; border-radius: 16px; padding: 16px 18px;
  box-shadow: 0 14px 34px rgba(0, 0, 0, .35); font-size: .8rem; }
.hud h2 { font-size: 1.15rem; margin: .3rem 0 .5rem; }
.k { font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; opacity: .7; display: flex; gap: .5rem; align-items: center; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #5b6b68; }
.dot.receiving, .dot.reading, .dot.filing, .dot.awaiting { background: #f5a524; box-shadow: 0 0 0 4px rgba(245, 165, 36, .2); }
.dot.applied { background: #76b900; box-shadow: 0 0 0 4px rgba(118, 185, 0, .25); }
.dot.quarantine, .dot.error { background: #e5484d; box-shadow: 0 0 0 4px rgba(229, 72, 77, .25); }
.doc { margin: 0 0 .4rem; }
.steps { list-style: none; padding: 0; margin: 0 0 .6rem; }
.steps li { padding: 2px 0; opacity: .4; }
.steps li::before { content: "○ "; }
.steps li.on { opacity: 1; } .steps li.on::before { content: "◐ "; color: #f5a524; }
.steps li.done { opacity: .8; } .steps li.done::before { content: "● "; color: #76b900; }
.alert { background: #3a1416; border: 1px solid #7a2a2e; border-radius: 10px; padding: 6px 9px; margin: .4rem 0; }
.btns { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .5rem; }
.btns .btn { font-size: .75rem; padding: .35rem .7rem; }
.leave { margin-top: .6rem; opacity: .85; }
.askcard { margin-top: 16px; }
.askrow { display: flex; gap: .5rem; }
.askrow input { flex: 1; font: inherit; padding: .55rem .8rem; border-radius: 10px; border: 1px solid var(--line); background: var(--panel2); color: var(--text); }
.chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .5rem; }
.chip { font: inherit; font-size: .75rem; border-radius: 999px; padding: .25rem .7rem; background: var(--panel2); color: var(--text); border: 1px solid var(--line); cursor: pointer; }
.answer { margin-top: .7rem; }
.answer p { margin: 0 0 .4rem; white-space: pre-line; }
.cites { display: flex; flex-wrap: wrap; gap: .35rem; margin-bottom: .3rem; }
.cite { font-size: .72rem; background: #1f3317; color: #cfe8a8; border-radius: 6px; padding: .1rem .5rem; }
.small { font-size: .72rem; }
@media (max-width: 900px) { .hud { position: static; width: auto; max-width: none; margin: 12px; } }
</style>
