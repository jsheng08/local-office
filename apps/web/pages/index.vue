<script setup lang="ts">
const PID = 'PRJ-SPL'
const api = useApi()
const user = useCurrentUser()
const { busy, elapsed, run } = useBusy()

// Persist across tab switches.
const paragraphs = useState<any[]>('req_paras', () => [])
const analysis = useState<any>('req_analysis', () => null)
const changes = useState<any>('req_changes', () => null)
const decision = useState<any>('req_decision', () => null)
const err = ref<any>(null)
const decErr = ref<any>(null)
const hl = ref<{ pid: string; quote: string } | null>(null)

async function analyze(kind: 'analyze' | 'reanalyze') {
  err.value = null; decErr.value = null
  lastKind.value = kind
  const demo_file = kind === 'analyze' ? 'requirements_v1.md' : 'requirements_v2.md'
  try {
    const d: any = await run(() => api(`/api/projects/${PID}/requirements/${kind}`, { method: 'POST', body: { demo_file } }))
    if (d.paragraphs?.length) paragraphs.value = d.paragraphs
    analysis.value = d
    changes.value = kind === 'reanalyze' ? d : null
    decision.value = null
  } catch (e) { err.value = e }
}

async function decide(dec: 'approve' | 'reject') {
  decErr.value = null
  try {
    const d: any = await run(() => api(`/api/change_sets/${analysis.value.change_set_id}/decision`, { method: 'POST', body: { decision: dec } }))
    decision.value = { ...d, by: user.value }
  } catch (e) { decErr.value = e }
}

const diffMap = computed(() => {
  const m: Record<string, string> = {}
  for (const x of changes.value?.paragraph_diff || []) m[x.id] = x.change
  return m
})

function cite(pid: string, quote: string) {
  hl.value = { pid, quote: quote || '' }
  nextTick(() => document.getElementById('para-' + pid)?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
}
function parts(p: any) {
  if (!hl.value || hl.value.pid !== p.id || !hl.value.quote) return [p.text, '', '']
  const t: string = p.text
  let i = t.indexOf(hl.value.quote)
  if (i < 0) i = t.toLowerCase().indexOf(hl.value.quote.toLowerCase())
  if (i < 0) return [t, '', '']
  const n = hl.value.quote.length
  return [t.slice(0, i), t.slice(i, i + n), t.slice(i + n)]
}
const conf = (c: any) => c == null ? '—' : typeof c === 'number' && c <= 1 ? Math.round(c * 100) + '%' : c
const staffNames = (s: any) => s?.recommended_staff?.length ? s.recommended_staff.join(', ') : '—'
const PRIO: Record<string, string> = { must: 'Must-have', should: 'Should-have', could: 'Nice-to-have', wont: 'Later' }
const prioLabel = (p: any) => p == null ? '—' : (PRIO[p] || String(p))
const cols = [
  { k: 'must', n: 'Must-have' }, { k: 'should', n: 'Should-have' }, { k: 'could', n: 'Nice-to-have' }, { k: 'wont', n: 'Later' },
]
const lastKind = ref<'analyze' | 'reanalyze'>('analyze')
const STAGES_BASE = [
  'Reading the brief on-device',
  'Extracting requirements with local Nemotron',
  'Verifying every quote against the source',
  'Estimating effort',
  'Ranking staff from the local roster',
]
const stages = computed(() => lastKind.value === 'reanalyze' ? [...STAGES_BASE, 'Comparing v1 and v2'] : STAGES_BASE)

// Cost of change — computed only from the real `changes` array in the v2 response.
const changedRows = computed(() => (changes.value?.changes || []).filter((c: any) => c.change !== 'unchanged'))
const costOfChange = computed(() => {
  const cs: any[] = changes.value?.changes || []
  if (!cs.length) return null
  let hours = 0, added = 0, modified = 0, removed = 0, missing = 0
  const num = (v: any) => (v == null || isNaN(Number(v)) ? null : Number(v))
  for (const c of cs) {
    if (c.change === 'added') { added++; const a = num(c.after?.pert); a == null ? missing++ : (hours += a) }
    else if (c.change === 'modified') { modified++; const a = num(c.after?.pert), b = num(c.before?.pert); a == null || b == null ? missing++ : (hours += a - b) }
    else if (c.change === 'removed') { removed++; const b = num(c.before?.pert); b == null ? missing++ : (hours -= b) }
  }
  return { hours, added, modified, removed, missing }
})
const signed = (n: number) => (n >= 0 ? '+' : '−') + fmtNum(Math.abs(n), 0)
const hrs = (s: any) => s ? `${fmtNum(s.low)}–${fmtNum(s.high)} h` : null
function actAs(u: string) { user.value = u }
</script>

<template>
  <section>
    <div class="toolbar card">
      <div class="proj"><span class="lbl">Project</span> <b>PRJ-SPL</b></div>
      <button class="btn primary big" :disabled="busy" @click="analyze('analyze')">Analyze brief v1</button>
      <button class="btn big" :disabled="busy" @click="analyze('reanalyze')">Upload changed brief v2</button>
      <div class="grow" />
      <div class="actas">
        <button class="btn big" :class="{ on: user === 'aisyah' }" @click="actAs('aisyah')">Act as Analyst (Aisyah)</button>
        <button class="btn big" :class="{ on: user === 'daniel' }" @click="actAs('daniel')">Act as PM (Daniel)</button>
      </div>
    </div>
    <div v-if="busy || elapsed > 0" class="card narr"><Spinner :busy="busy" :elapsed="elapsed" :stages="stages" /></div>
    <ErrBox :err="err" />

    <!-- Attack blocked -->
    <div v-if="analysis && (analysis.ignored_instructions || []).length" class="card attack">
      <h2>⛔ Attack blocked: hidden instruction in the client's file was ignored</h2>
      <div v-for="(a, i) in analysis.ignored_instructions" :key="i" class="ign">
        <button class="cite ref big" @click="cite(a.paragraph_id, a.quote)">{{ a.paragraph_id }}</button>
        <div class="aquote">“{{ a.quote }}”</div>
      </div>
      <div class="sub">The brief is treated as untrusted data — this text was reported, not executed.</div>
    </div>
    <div v-else-if="analysis" class="card"><span class="muted">No embedded instructions detected in this document.</span></div>

    <!-- Before / After -->
    <div v-if="changes" class="card">
      <div v-if="costOfChange" class="coc">
        Client change v2 → <b :class="costOfChange.hours > 0 ? 'up' : 'down'">{{ signed(costOfChange.hours) }} est. hours</b>
        · {{ costOfChange.added }} added · {{ costOfChange.modified }} changed · {{ costOfChange.removed }} removed
      </div>
      <div v-if="costOfChange?.missing" class="sub">{{ costOfChange.missing }} change(s) had no estimate and are excluded from the total.</div>
      <h2>Before → After <span class="sub">proposed re-prioritisation · nothing applied until a PM approves</span></h2>
      <div class="tablewrap">
        <table class="tbl big">
          <thead><tr><th>Req</th><th>Change</th><th>Priority</th><th>Est. hours (low–high)</th><th>Reason</th></tr></thead>
          <tbody>
            <tr v-for="c in changedRows" :key="c.req_id" :class="'ch-' + c.change">
              <td><code>{{ c.req_id }}</code><div class="ttl">{{ c.title }}</div></td>
              <td><span class="cpill" :class="'c-' + c.change">{{ c.change }}</span></td>
              <td><Arrow :a="c.before ? prioLabel(c.before.priority) : null" :b="c.after ? prioLabel(c.after.priority) : null" /></td>
              <td><Arrow :a="hrs(c.before)" :b="hrs(c.after)" /></td>
              <td class="reason">{{ c.reason }}</td>
            </tr>
            <tr v-if="!changedRows.length"><td colspan="5" class="muted">No changed requirements returned.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Approval bar -->
    <div v-if="analysis?.change_set_id" class="approval">
      <div><span class="muted">Change set</span> <code>{{ analysis.change_set_id }}</code></div>
      <div v-if="!decision" class="pill amber big0">Pending human approval</div>
      <div v-else-if="decision.status === 'applied'" class="pill green big0">Applied by {{ decision.by }}</div>
      <div v-else class="pill red big0">{{ decision.status }} by {{ decision.by }}</div>
      <div class="grow" />
      <button class="btn approve big" :disabled="busy || !!decision" @click="decide('approve')">Approve</button>
      <button class="btn reject big" :disabled="busy || !!decision" @click="decide('reject')">Reject</button>
    </div>
    <ErrBox :err="decErr" hint="Only a project manager can approve — click “Act as PM (Daniel)”." />

    <!-- Kanban -->
    <div v-if="decision?.board" class="card">
      <h2>Approved Kanban board <span class="sub">PRJ-SPL · {{ decision.status }} by {{ decision.by }}</span></h2>
      <div class="board">
        <div v-for="c in cols" :key="c.k" class="col" :class="'col-' + c.k">
          <div class="colhead">{{ c.n }} <span class="cnt">{{ decision.board.filter((r: any) => r.priority === c.k).length }}</span></div>
          <div v-for="r in decision.board.filter((r: any) => r.priority === c.k)" :key="r.id" class="kcard">
            <code>{{ r.id }}</code>
            <div class="kt">{{ r.title }}</div>
            <div class="km">
              <span v-if="r.triage?.pert != null">Est. {{ fmtNum(r.triage.pert) }} h</span>
              <span v-if="r.recommended_staff?.length"> · {{ r.recommended_staff.map((s: any) => s.name).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Analysis -->
    <div v-if="analysis" class="grid2">
      <div class="card src">
        <h2>Confidential client brief — processed on this ATOM, never uploaded</h2>
        <div class="sub" style="margin-bottom:.6rem">Untrusted input · click a citation to locate</div>
        <div v-for="p in paragraphs" :id="'para-' + p.id" :key="p.id" class="para"
             :class="[{ hl: hl?.pid === p.id }, diffMap[p.id] && diffMap[p.id] !== 'equal' ? 'diff-' + diffMap[p.id] : '']">
          <span class="pid">{{ p.id }}</span>
          <span v-if="diffMap[p.id] && diffMap[p.id] !== 'equal'" class="dtag">{{ diffMap[p.id] }}</span>
          <div class="ptext">{{ parts(p)[0] }}<mark v-if="parts(p)[1]">{{ parts(p)[1] }}</mark>{{ parts(p)[2] }}</div>
        </div>
      </div>
      <div>
        <div class="card">
          <h2>Proposed requirements <span class="sub">{{ analysis.requirements?.length || 0 }} proposed · not applied until approved</span></h2>
          <article v-for="r in analysis.requirements || []" :key="r.id" class="req">
            <div class="reqhead">
              <code>{{ r.id }}</code>
              <span class="prio" :class="'p-' + r.priority">{{ prioLabel(r.priority) }}</span>
              <h3>{{ r.title }}</h3>
            </div>
            <div class="cites">
              <button v-for="(c, i) in r.citations || []" :key="i" class="cite" :class="c.status" :title="c.quote" @click="cite(c.paragraph_id, c.quote)">
                {{ c.paragraph_id }} · {{ c.status }}
              </button>
            </div>
            <details class="more">
              <summary>Story, acceptance criteria, estimate &amp; staff</summary>
              <p v-if="r.story?.as_a" class="story">As a <b>{{ r.story.as_a }}</b>, I want <b>{{ r.story.i_want }}</b>, so that {{ r.story.so_that }}.</p>
              <p v-else-if="r.statement" class="story">{{ r.statement }}</p>
              <div v-if="r.acceptance_criteria?.length" class="ac">
                <div class="lbl">Acceptance criteria</div>
                <ul><li v-for="(a, i) in r.acceptance_criteria" :key="i">{{ a }}</li></ul>
              </div>
              <div class="metrics">
                <div><span class="lbl">Est. hours</span> <b>{{ fmtNum(r.triage?.low) }}–{{ fmtNum(r.triage?.high) }} h</b> (expected {{ fmtNum(r.triage?.pert) }})</div>
                <div><span class="lbl">Confidence</span> <b>{{ conf(r.triage?.confidence) }}</b></div>
                <div v-if="r.triage?.depends_on?.length"><span class="lbl">Depends on</span> <code v-for="d in r.triage.depends_on" :key="d">{{ d }} </code></div>
              </div>
              <div v-if="r.recommended_staff?.length" class="staff">
                <div class="lbl">Recommended staff · requires human approval</div>
                <ul>
                  <li v-for="s in r.recommended_staff" :key="s.staff_id"><b>{{ s.name }}</b> <span class="muted">{{ s.staff_id }}<template v-if="s.score != null"> · score {{ fmtNum(s.score, 2) }}</template></span>
                    <div class="reason">{{ s.reason }}</div></li>
                </ul>
              </div>
            </details>
          </article>
        </div>
        <div v-if="analysis.ambiguities" class="card">
          <h2>Ambiguities <span class="sub">questions for the client</span></h2>
          <ol v-if="analysis.ambiguities.length" class="qlist">
            <li v-for="a in analysis.ambiguities" :key="a.id">
              <b>{{ a.question }}</b>
              <button v-if="a.paragraph_id" class="cite ref" @click="cite(a.paragraph_id, a.quote)">{{ a.paragraph_id }}</button>
              <div v-if="a.quote" class="quote">“{{ a.quote }}”</div>
            </li>
          </ol>
          <div v-else class="muted">None returned.</div>
        </div>
      </div>
    </div>
  </section>
</template>
