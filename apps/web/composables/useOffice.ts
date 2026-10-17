// Office view state. Every card, staff row and number comes from a real API response;
// the helper's animation phase only reflects which real call is in flight.
import type { Card, Phase, Priority, Staff } from '~/types/office'

const PID = 'PRJ-SPL'
const ACCEPT = /\.(pdf|png|jpe?g|md|txt)$/i
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

function toCard(r: any, ch?: any, proposed = true): Card {
  const t = r.triage || {}
  const before = ch?.before?.priority as Priority | undefined
  return {
    id: r.id,
    title: r.title,
    priority: (r.priority || 'could') as Priority,
    beforePriority: ch?.change === 'modified' && before && before !== r.priority ? before : null,
    change: ch && ch.change !== 'unchanged' ? ch.change : null,
    proposed,
    est: t.pert != null || t.low != null ? { low: t.low, high: t.high, pert: t.pert } : null,
    staff: (r.recommended_staff || []).map((s: any) => ({ staff_id: s.staff_id, name: s.name, reason: s.reason })),
    citations: r.citations || [],
    story: r.story || null,
    acceptance_criteria: r.acceptance_criteria || [],
    reason: ch && ch.change !== 'unchanged' ? ch.reason : undefined,
  }
}

function removedCard(ch: any): Card {
  const b = ch.before || {}
  return {
    id: ch.req_id, title: ch.title, priority: (b.priority || 'wont') as Priority, beforePriority: null,
    change: 'removed', proposed: true,
    est: b.pert != null ? { low: b.low, high: b.high, pert: b.pert } : null,
    staff: [], reason: ch.reason,
  }
}

export function useOffice() {
  const api = useApi()
  const user = useCurrentUser()
  const { busy, elapsed, run } = useBusy()

  const staff = useState<Staff[]>('office_staff', () => [])
  const cards = useState<Card[]>('office_cards', () => [])
  const analysis = useState<any>('office_analysis', () => null)
  const decision = useState<any>('office_decision', () => null)
  const phase = useState<Phase>('office_phase', () => 'idle')
  const lastDoc = useState<any>('office_doc', () => null)
  const err = ref<any>(null)
  const note = ref<string>('')

  const changeSetId = computed<string | null>(() => analysis.value?.change_set_id || null)
  const decisionStatus = computed<string | null>(() => decision.value?.status || null)
  const hasProposed = computed(() => !!changeSetId.value && !decisionStatus.value)
  const quarantine = computed<any[]>(() => analysis.value?.ignored_instructions || [])

  const boardCounts = computed(() => {
    const c: Record<Priority, number> = { must: 0, should: 0, could: 0, wont: 0 }
    for (const k of cards.value) if (k.change !== 'removed') c[k.priority]++
    return c
  })
  const tasksByStaff = computed(() => {
    const m: Record<string, Card[]> = {}
    for (const k of cards.value) {
      if (k.change === 'removed') continue
      for (const s of k.staff) (m[s.staff_id] ||= []).push(k)
    }
    return m
  })

  const helperSay = computed(() => {
    if (phase.value === 'error') return err.value?.status === 403
      ? 'The server refused that (403). Only a PM can approve.'
      : 'That call failed. No result shown; see the error.'
    const f = lastDoc.value?.filename
    switch (phase.value) {
      case 'receiving': return `Got it! Reading ${f || 'your file'} on this ATOM…`
      case 'reading': return `Nemotron is reading every paragraph… ${Math.round(elapsed.value)}s`
      case 'quarantine': return `Found ${quarantine.value.length} hidden instruction(s). Quarantined, not obeyed.`
      case 'filing': return 'Pinning proposed cards on the board…'
      case 'awaiting': return 'Proposal ready. A PM needs to approve it.'
      case 'applied': return 'Approved! Everyone knows what to work on.'
      default: return cards.value.length ? 'Drop a changed brief and I will re-triage.' : 'Hi! Drop a client brief in the mailroom.'
    }
  })

  async function loadStaff() {
    try { staff.value = await api('/api/staff') } catch (e) { err.value = e }
  }
  async function loadBoard() {
    if (analysis.value) return
    try {
      const d: any = await api(`/api/projects/${PID}/board`)
      cards.value = (d.board || []).map((r: any) => toCard(r, null, false))
    } catch (e) { err.value = e }
  }

  async function upload(files: File[]) {
    const file = files.find(f => ACCEPT.test(f.name))
    err.value = null; note.value = ''
    if (!file) { err.value = { body: 'Unsupported file. Use .pdf, .png, .jpg, .md or .txt.' }; phase.value = 'error'; return }
    if (files.length > 1) note.value = `Processing ${file.name} only; drop one document at a time.`
    lastDoc.value = { filename: file.name }
    try {
      phase.value = 'receiving'
      const fd = new FormData(); fd.append('file', file)
      const doc: any = await run(() => api(`/api/projects/${PID}/documents`, { method: 'POST', body: fd }))
      lastDoc.value = doc
      phase.value = 'reading'
      const kind = cards.value.length || analysis.value ? 'reanalyze' : 'analyze'
      let d: any
      try {
        d = await run(() => api(`/api/projects/${PID}/requirements/${kind}`, { method: 'POST', body: { text: doc.text } }))
      } catch (e: any) {
        if (kind !== 'reanalyze' || e?.status !== 409) throw e
        d = await run(() => api(`/api/projects/${PID}/requirements/analyze`, { method: 'POST', body: { text: doc.text } }))
      }
      analysis.value = d; decision.value = null
      if ((d.ignored_instructions || []).length) { phase.value = 'quarantine'; await sleep(2600) }
      phase.value = 'filing'
      const byId: Record<string, any> = {}
      for (const c of d.changes || []) byId[c.req_id] = c
      const next = (d.requirements || []).map((r: any) => toCard(r, d.changes ? byId[r.id] : null, true))
      for (const c of d.changes || []) if (c.change === 'removed') next.push(removedCard(c))
      cards.value = []
      for (const c of next) { cards.value = [...cards.value, c]; await sleep(180) }
      phase.value = 'awaiting'
    } catch (e) { err.value = e; phase.value = 'error' }
  }

  const baseline = useState<any>('office_baseline', () => null)
  async function resetData() {
    err.value = null; note.value = ''
    try {
      const d: any = await run(() => api('/api/demo/reset', { method: 'POST' }))
      analysis.value = null; decision.value = null; baseline.value = d.baseline
      lastDoc.value = { filename: 'Brief v1 · approved baseline', method: 'recorded run ' + d.baseline?.run_id }
      cards.value = (d.board || []).map((r: any) => toCard(r, null, false))
      phase.value = 'idle'
      await loadStaff()
    } catch (e) { err.value = e; phase.value = 'error' }
  }

  async function decide(dec: 'approve' | 'reject') {
    if (!changeSetId.value) return
    err.value = null
    try {
      const d: any = await run(() => api(`/api/change_sets/${changeSetId.value}/decision`, { method: 'POST', body: { decision: dec } }))
      decision.value = { ...d, by: user.value }
      if (d.status === 'applied') {
        cards.value = (d.board || []).map((r: any) => toCard(r, null, false))
        phase.value = 'applied'
      } else phase.value = 'idle'
    } catch (e) { err.value = e; phase.value = 'error' }
  }

  return {
    staff, cards, analysis, decision, phase, lastDoc, err, note, busy, elapsed,
    changeSetId, decisionStatus, hasProposed, quarantine, boardCounts, tasksByStaff, helperSay,
    loadStaff, loadBoard, upload, decide, resetData, baseline,
  }
}
