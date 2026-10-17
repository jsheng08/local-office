<script setup lang="ts">
const api = useApi()
const { busy, elapsed, run } = useBusy()
const file = ref<File | null>(null)
const preview = ref('')
const useDemo = ref(false)
const result = ref<any>(null)
const err = ref<any>(null)

function onFile(ev: Event) {
  const f = (ev.target as HTMLInputElement).files?.[0] || null
  file.value = f; useDemo.value = false
  preview.value = f ? URL.createObjectURL(f) : ''
}
function demo() {
  useDemo.value = true; file.value = null; preview.value = ''
  submit()
}
async function submit() {
  err.value = null; result.value = null
  const fd = new FormData()
  if (file.value) fd.append('file', file.value)
  else if (useDemo.value) fd.append('demo_file', 'receipt_grab_001.png')
  else { err.value = { body: 'Choose a receipt image or click “Use demo receipt”.' }; return }
  try { result.value = await run(() => api('/api/finance/claims', { method: 'POST', body: fd })) }
  catch (e) { err.value = e }
}
const FIELDS = ['vendor', 'date', 'currency', 'total_amount', 'category', 'confidence']
</script>
<template>
  <section class="grid2">
    <div class="card">
      <h2>Submit expense claim <span class="sub">receipt read by local Nemotron Omni</span></h2>
      <div class="row">
        <button class="btn primary" :disabled="busy" @click="demo">Use demo receipt</button>
        <span class="muted">or</span>
        <input type="file" accept="image/*" :disabled="busy" @change="onFile">
        <button v-if="file" class="btn" :disabled="busy" @click="submit">Extract &amp; check</button>
        <Spinner :busy="busy" :elapsed="elapsed" />
      </div>
      <div class="preview">
        <img v-if="preview" :src="preview" alt="receipt preview">
        <div v-if="useDemo" class="fname">Demo receipt: <code>receipt_grab_001.png</code> (synthetic, stored locally)</div>
        <div v-else-if="file" class="fname">{{ file.name }}</div>
      </div>
      <ErrBox :err="err" />
    </div>
    <div v-if="result" class="card">
      <h2>Claim <code>{{ result.claim_id }}</code></h2>
      <div class="pill amber big">Pending approval → Finance · AI cannot approve or pay</div>
      <div class="lbl">Extracted fields</div>
      <table class="tbl kv">
        <tr v-for="k in FIELDS" :key="k"><th>{{ k.replace('_', ' ') }}</th>
          <td>{{ k === 'total_amount' && result.extracted?.[k] != null ? fmtNum(result.extracted[k], 2) : (result.extracted?.[k] ?? '—') }}</td></tr>
      </table>
      <div class="lbl">Policy checks (deterministic rules)</div>
      <table class="tbl checks">
        <tr v-for="(c, i) in result.policy_checks || []" :key="i" :class="c.passed ? 'pass' : 'fail'">
          <td class="ck">{{ c.passed ? '✓' : '✗' }}</td><td><b>{{ c.rule }}</b></td><td>{{ c.detail }}</td>
        </tr>
      </table>
    </div>
  </section>
</template>
