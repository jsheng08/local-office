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

// Computed only from /api/health — never hardcoded.
const shortName = (m: any) => String(m?.root || m?.model_id || m?.name || '?').replace(/^.*\//, '')
const okModels = computed(() => (health.value?.models || []).filter((m: any) => m.ok))
const fallbackOn = computed(() => !!health.value?.hosted_fallback)

const tabs = [
  { to: '/', label: 'Client Brief' },
  { to: '/executive', label: 'Executive' },
  { to: '/audit', label: 'Audit' },
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
    <div class="right">
      <div class="chip lastcall" :class="{ muted: !lastCall }" :title="lastCall ? JSON.stringify(lastCall, null, 2) : ''">
        <template v-if="lastCall">
          <span class="tps">{{ fmtNum(lastCall.tok_per_s, 1) }} <small>tok/s</small></span>
          <span class="lcsub">last call · measured · {{ lastCall.model }} · {{ fmtNum(lastCall.latency_ms, 0) }} ms · {{ fmtNum(lastCall.completion_tokens, 0) }} tok</span>
        </template>
        <template v-else><span class="lcsub">Last call: — (no AI call yet)</span></template>
      </div>
      <label class="user">User
        <select v-model="user">
          <option v-for="u in users" :key="u.username" :value="u.username">{{ u.display_name }}</option>
        </select>
      </label>
    </div>
  </header>

  <div class="band" :class="{ bad: healthErr || (health && !okModels.length) || fallbackOn }">
    <template v-if="healthErr">⚠ Health check failed: {{ healthErr }}</template>
    <template v-else-if="!health">Checking on-device models…</template>
    <template v-else>
      <span>🔒 Running on this ATOM</span>
      <span class="sep">·</span>
      <span v-if="okModels.length"><b>{{ okModels.length }}</b> Nemotron model{{ okModels.length === 1 ? '' : 's' }} on-device:
        <span v-for="(m, i) in okModels" :key="m.name" class="mname">{{ shortName(m) }}{{ i < okModels.length - 1 ? ',' : '' }}</span>
      </span>
      <span v-else class="warn">No on-device model reachable right now</span>
      <span class="sep">·</span>
      <span>Cloud fallback: <b :class="fallbackOn ? 'warn' : 'none'">{{ fallbackOn ? 'ENABLED' : 'NONE' }}</b></span>
    </template>
  </div>
  <details v-if="health" class="modeldetails">
    <summary>Model details (live from /api/health) · {{ health.host }}</summary>
    <table class="tbl">
      <thead><tr><th>Endpoint</th><th>Model</th><th>Status</th><th>Health latency</th><th>Max context</th></tr></thead>
      <tbody>
        <tr v-for="m in health.models || []" :key="m.name">
          <td><b>{{ m.name }}</b> <code>{{ m.base_url }}</code></td>
          <td><code>{{ m.root || m.model_id || '—' }}</code></td>
          <td><span class="pill" :class="m.ok ? 'green' : 'red'">{{ m.ok ? 'reachable' : 'offline' }}</span> <span v-if="m.error" class="muted">{{ m.error }}</span></td>
          <td>{{ m.ok ? fmtNum(m.latency_ms, 0) + ' ms' : '—' }}</td>
          <td>{{ m.max_model_len ? fmtNum(m.max_model_len, 0) + ' tokens' : '—' }}</td>
        </tr>
      </tbody>
    </table>
  </details>
  <nav class="tabs">
    <NuxtLink v-for="t in tabs" :key="t.to" :to="t.to" class="tab" active-class="active" exact-active-class="active">{{ t.label }}</NuxtLink>
  </nav>
  <main>
    <NuxtPage />
  </main>
</template>
