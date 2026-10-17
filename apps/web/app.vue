<script setup lang="ts">
const api = useApi()
const user = useCurrentUser()
const lastCall = useLastCall()
const health = ref<any>(null)
const healthErr = ref<string>('')
const users = ref<any[]>([])

async function pollHealth() {
  try { health.value = await api('/api/health', { timeout: 15000 }); healthErr.value = '' }
  catch (e: any) { healthErr.value = e.body }
}
let iv: any
onMounted(async () => {
  pollHealth(); iv = setInterval(pollHealth, 15000)
  try { users.value = await api('/api/users') } catch (e: any) { healthErr.value = e.body }
})
onBeforeUnmount(() => clearInterval(iv))
watch(user, (v) => { try { localStorage.setItem('lo_user', v) } catch {} })

const tabs = [
  { to: '/', label: 'Requirements → Kanban' },
  { to: '/onboarding', label: 'Onboarding' },
  { to: '/claims', label: 'Expense claim' },
  { to: '/executive', label: 'Executive' },
  { to: '/audit', label: 'Audit log' },
]
</script>

<template>
  <header class="top">
    <div class="brand">
      <div class="logo">LO</div>
      <div>
        <h1>Local Office</h1>
        <div class="tagline">One ATOM. One Private AI. Your Entire Office.</div>
      </div>
    </div>
    <div class="status">
      <div class="models">
        <div v-for="m in health?.models || []" :key="m.name" class="model" :class="m.ok ? 'ok' : 'bad'" :title="m.base_url + (m.error ? '\n' + m.error : '')">
          <span class="dot" />
          <b>{{ m.name }}</b>
          <span class="mid">{{ m.root || m.model_id }}</span>
          <span class="lat">{{ m.ok ? fmtNum(m.latency_ms, 0) + ' ms' : 'offline' }}</span>
        </div>
        <span v-if="!health && !healthErr" class="muted">Checking local models…</span>
        <span v-if="healthErr" class="model bad"><span class="dot" />Health check failed: {{ healthErr }}</span>
      </div>
      <div class="hostline">
        <span>{{ health?.host }}</span> ·
        <span class="nofallback">Hosted fallback: <b>{{ health?.hosted_fallback ? 'ENABLED' : 'none' }}</b></span>
      </div>
    </div>
    <div class="right">
      <div class="chip lastcall" :class="{ muted: !lastCall }" :title="lastCall ? JSON.stringify(lastCall, null, 2) : ''">
        <template v-if="lastCall">
          <span class="lbl">Last call · measured</span>
          <b>{{ lastCall.model }}</b> · {{ fmtNum(lastCall.latency_ms, 0) }} ms ·
          {{ fmtNum(lastCall.completion_tokens, 0) }} tok · {{ fmtNum(lastCall.tok_per_s, 1) }} tok/s
        </template>
        <template v-else>Last call: —</template>
      </div>
      <label class="user">User
        <select v-model="user">
          <option v-for="u in users" :key="u.username" :value="u.username">{{ u.display_name }} · {{ u.role }}</option>
        </select>
      </label>
    </div>
  </header>
  <nav class="tabs">
    <NuxtLink v-for="t in tabs" :key="t.to" :to="t.to" class="tab" active-class="active" exact-active-class="active">{{ t.label }}</NuxtLink>
  </nav>
  <main>
    <NuxtPage />
  </main>
</template>
