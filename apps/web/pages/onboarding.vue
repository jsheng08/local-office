<script setup lang="ts">
const api = useApi()
const { busy, elapsed, run } = useBusy()
const log = useState<any[]>('onb_log', () => [])
const q = ref('')
const err = ref<any>(null)
const SUGG = [
  'How many days of annual leave do I get?',
  'What is the meal claim limit?',
  'Can I paste client documents into ChatGPT?',
  "What is the CEO's salary?",
]
async function ask(text: string) {
  text = (text || '').trim()
  if (!text || busy.value) return
  err.value = null
  log.value.push({ role: 'user', text })
  q.value = ''
  try {
    const d: any = await run(() => api('/api/onboarding/ask', { method: 'POST', body: { question: text } }))
    log.value.push({ role: 'bot', d, call: d.meta?.calls?.[d.meta.calls.length - 1] })
  } catch (e) { err.value = e }
}
</script>
<template>
  <section class="card chat">
    <h2>Onboarding assistant <span class="sub">answers only from authorized policy sources</span></h2>
    <div class="chatlog">
      <div v-for="(m, i) in log" :key="i" class="msg" :class="m.role">
        <template v-if="m.role === 'user'">{{ m.text }}</template>
        <template v-else>
          <div class="who">Onboarding agent
            <span v-if="m.d.status === 'escalate'" class="pill red">Escalated to HR</span>
            <span v-else class="pill green">Answered from policy</span>
          </div>
          <div class="ans">{{ m.d.answer }}</div>
          <div v-if="m.d.citations?.length" class="chips">
            <span v-for="c in m.d.citations" :key="c.section_id" class="pchip" :title="c.doc">{{ c.section_id }} · {{ c.title }}</span>
          </div>
          <div class="mmeta">
            <template v-if="m.d.sections_considered != null">{{ m.d.sections_considered }} authorized sections considered</template>
            <template v-if="m.call"> · {{ m.call.model }} · {{ fmtNum(m.call.latency_ms, 0) }} ms</template>
          </div>
        </template>
      </div>
    </div>
    <div class="chips">
      <button v-for="s in SUGG" :key="s" class="sugg" :disabled="busy" @click="ask(s)">{{ s }}</button>
    </div>
    <form class="askrow" @submit.prevent="ask(q)">
      <input v-model="q" placeholder="Ask about leave, claims, IT security…" autocomplete="off">
      <button class="btn primary" type="submit" :disabled="busy">Ask</button>
      <Spinner :busy="busy" :elapsed="elapsed" />
    </form>
    <ErrBox :err="err" />
  </section>
</template>
