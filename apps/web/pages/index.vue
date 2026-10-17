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
const cols = [
  { k: 'must', n: 'Must' }, { k: 'should', n: 'Should' }, { k: 'could', n: 'Could' }, { k: 'wont', n: "Won't (this phase)" },
]
</script>

<template>
  <section>
    <div class="toolbar card">
      <div class="proj"><span class="lbl">Project</span> <b>PRJ-SPL</b></div>
      <button class="btn primary" :disabled="busy" @click="analyze('analyze')">Analyze brief v1</button>
      <button class="btn" :disabled="busy" @click="analyze('reanalyze')">Upload changed brief v2</button>
      <Spinner :busy="busy" :elapsed="elapsed" />
    </div>
    <ErrBox :err="err" />

    <!-- Before / After -->
    <div v-if="changes" class="card">
      <h2>Before → After <span class="sub">proposed re-prioritisation from changed brief</span></h2>
      <div class="chips">
        <span class="lbl">Paragraph diff</span>
        <span v-for="x in changes.paragraph_diff || []" :key="x.id" class="dchip" :class="'d-' + x.change">{{ x.id }} {{ x.change }}</span>
      </div>
      <div class="tablewrap">
        <table class="tbl">
          <thead><tr><th>ID</th><th>Requirement</th><th>Change</th><th>Priority</th><th>Effort</th><th>PERT</th><th>Staff</th><th>Reason</th></tr></thead>
          <tbody>
            <tr v-for="c in changes.changes || []" :key="c.req_id" :class="'ch-' + c.change">
              <td><code>{{ c.req_id }}</code></td>
              <td class="ttl">{{ c.title }}</td>
              <td><span class="cpill" :class="'c-' + c.change">{{ c.change }}</span></td>
              <td><Arrow :a="c.before?.priority" :b="c.after?.priority" /></td>
              <td><Arrow :a="c.before ? `${fmtNum(c.before.low)}–${fmtNum(c.before.high)} h` : null" :b="c.after ? `${fmtNum(c.after.low)}–${fmtNum(c.after.high)} h` : null" /></td>
              <td><Arrow :a="c.before ? fmtNum(c.before.pert) : null" :b="c.after ? fmtNum(c.after.pert) : null" /></td>
              <td><Arrow :a="c.before ? staffNames(c.before) : null" :b="c.after ? staffNames(c.after) : null" /></td>
              <td class="reason">{{ c.reason }}</td>
            </tr>
            <tr v-if="!(changes.changes || []).length"><td colspan="8" class="muted">No changes returned.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Approval bar -->
    <div v-if="analysis?.change_set_id" class="approval">
      <div><span class="muted">Change set</span> <code>{{ analysis.change_set_id }}</code></div>
      <div v-if="!decision" class="pill amber">Pending human approval</div>
      <div v-else-if="decision.status === 'applied'" class="pill green">Applied by {{ decision.by }}</div>
      <div v-else class="pill red">{{ decision.status }} by {{ decision.by }}</div>
      <div class="grow" />
      <button class="btn approve" :disabled="busy || !!decision" @click="decide('approve')">Approve</button>
      <button class="btn reject" :disabled="busy || !!decision" @click="decide('reject')">Reject</button>
    </div>
    <ErrBox :err="decErr" hint="Only a project manager can approve — switch user to Daniel Tan (pm)." />

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
              <span v-if="r.triage?.pert != null">PERT {{ fmtNum(r.triage.pert) }} h</span>
              <span v-if="r.recommended_staff?.length"> · {{ r.recommended_staff.map((s: any) => s.name).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Analysis -->
    <div v-if="analysis" class="grid2">
      <div class="card src">
        <h2>Source document <span class="sub">untrusted · click a citation to locate</span></h2>
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
              <span class="prio" :class="'p-' + r.priority">{{ String(r.priority || '?').toUpperCase() }}</span>
              <h3>{{ r.title }}</h3>
            </div>
            <p v-if="r.story?.as_a" class="story">As a <b>{{ r.story.as_a }}</b>, I want <b>{{ r.story.i_want }}</b>, so that {{ r.story.so_that }}.</p>
            <p v-else-if="r.statement" class="story">{{ r.statement }}</p>
            <div v-if="r.acceptance_criteria?.length" class="ac">
              <div class="lbl">Acceptance criteria</div>
              <ul><li v-for="(a, i) in r.acceptance_criteria" :key="i">{{ a }}</li></ul>
            </div>
            <div class="cites">
              <button v-for="(c, i) in r.citations || []" :key="i" class="cite" :class="c.status" :title="c.quote" @click="cite(c.paragraph_id, c.quote)">
                {{ c.paragraph_id }} · {{ c.status }}
              </button>
            </div>
            <div class="metrics">
              <div><span class="lbl">Effort</span> <b>{{ fmtNum(r.triage?.low) }}–{{ fmtNum(r.triage?.high) }} h</b> (PERT {{ fmtNum(r.triage?.pert) }})</div>
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
        <div class="card warnCard">
          <h2>Ignored instructions <span class="sub">untrusted document — not executed</span></h2>
          <div v-for="(a, i) in analysis.ignored_instructions || []" :key="i" class="ign">
            <span class="warnicon">⚠</span>
            <button class="cite ref" @click="cite(a.paragraph_id, a.quote)">{{ a.paragraph_id }}</button>
            <div class="quote">“{{ a.quote }}”</div>
          </div>
          <div v-if="!(analysis.ignored_instructions || []).length" class="muted">No embedded instructions detected.</div>
        </div>
      </div>
    </div>
  </section>
</template>
