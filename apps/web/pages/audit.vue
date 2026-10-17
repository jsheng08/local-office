<script setup lang="ts">
const api = useApi()
const user = useCurrentUser()
const d = ref<any>(null)
const err = ref<any>(null)
const loading = ref(false)
async function load() {
  err.value = null; loading.value = true
  try { d.value = await api('/api/audit') } catch (e) { err.value = e; d.value = null } finally { loading.value = false }
}
onMounted(load)
watch(user, load)
function lastCall(e: any) {
  const m = e.meta || {}
  const c = m.calls?.length ? m.calls[m.calls.length - 1] : m
  return { model: c.model || e.model || '', lat: m.total_latency_ms ?? c.latency_ms }
}
const uname = (u: any) => u && typeof u === 'object' ? (u.username || u.display_name) : u
const pillCls = (o: string) => ({ ok: 'green', denied: 'red', error: 'red', pending: 'amber' } as any)[o] || ''
</script>
<template>
  <section class="card">
    <h2>Audit log
      <span v-if="d" class="pill" :class="d.chain_valid ? 'green' : 'red'">{{ d.chain_valid ? 'Hash chain valid ✓' : 'Hash chain INVALID' }}</span>
      <button class="btn small" :disabled="loading" @click="load">Refresh</button>
    </h2>
    <ErrBox :err="err" hint="Audit log requires pm, finance or exec role." />
    <div v-if="d" class="tablewrap">
      <table class="tbl">
        <thead><tr><th>Time</th><th>User</th><th>Role</th><th>Action</th><th>Resource</th><th>Outcome</th><th>Model</th><th class="num">Latency</th></tr></thead>
        <tbody>
          <tr v-for="(e, i) in d.entries || []" :key="i">
            <td class="ts">{{ e.ts }}</td><td>{{ uname(e.user) }}</td><td>{{ e.role || e.user?.role }}</td>
            <td>{{ e.action }}</td><td>{{ e.resource }}</td>
            <td><span class="pill" :class="pillCls(e.outcome)">{{ e.outcome }}</span></td>
            <td>{{ lastCall(e).model }}</td>
            <td class="num">{{ lastCall(e).lat != null ? fmtNum(lastCall(e).lat, 0) + ' ms' : '' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
