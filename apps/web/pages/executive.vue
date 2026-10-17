<script setup lang="ts">
const api = useApi()
const { busy, elapsed, run } = useBusy()
const d = useState<any>('exec_var', () => null)
const err = ref<any>(null)
async function load() {
  err.value = null; d.value = null
  try { d.value = await run(() => api('/api/executive/variance?month=2026-09')) } catch (e) { err.value = e }
}
</script>
<template>
  <section>
    <div class="toolbar card">
      <button class="btn primary" :disabled="busy" @click="load">Explain September variance</button>
      <Spinner :busy="busy" :elapsed="elapsed" :stages="['Computing variances from local finance records', 'Explaining drivers with local Nemotron', 'Checking narrative figures against the records']" />
      <span class="label">Figures computed by deterministic code · narrative by Nemotron</span>
    </div>
    <ErrBox :err="err" hint="Executive view requires the exec or finance role — switch to Siti or Suresh." />
    <div v-if="d" class="grid2">
      <div class="card">
        <h2>Budget vs actual · {{ d.month }} <span class="sub">deterministic computation</span></h2>
        <div class="tablewrap">
          <table class="tbl fin">
            <thead><tr><th>Project</th><th>Cost centre</th><th>Category</th><th class="num">Budget</th><th class="num">Actual</th><th class="num">Variance</th><th class="num">%</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in d.rows || []" :key="i" :class="{ flag: r.flagged }">
                <td>{{ r.project_id }}</td><td>{{ r.cost_centre }}</td><td>{{ r.category }}</td>
                <td class="num">{{ fmtRM(r.budget_myr) }}</td><td class="num">{{ fmtRM(r.actual_myr) }}</td>
                <td class="num" :class="{ over: Number(r.variance_myr) > 0 }">{{ fmtRM(r.variance_myr) }}</td>
                <td class="num">{{ fmtNum(r.variance_pct, 1) }}%</td>
              </tr>
            </tbody>
            <tfoot v-if="d.totals && d.totals.budget_myr != null">
              <tr><td colspan="3"><b>Total</b></td><td class="num">{{ fmtRM(d.totals.budget_myr) }}</td><td class="num">{{ fmtRM(d.totals.actual_myr) }}</td>
                <td class="num">{{ fmtRM(d.totals.variance_myr) }}</td><td class="num">{{ d.totals.variance_pct != null ? fmtNum(d.totals.variance_pct, 1) + '%' : '' }}</td></tr>
            </tfoot>
          </table>
        </div>
      </div>
      <div class="card">
        <h2>Narrative <span class="sub">Nemotron · grounded in table</span></h2>
        <div v-if="d.unverified_numbers?.length" class="warnbox">
          <b>Unverified figures</b> — not found in the computed table:
          <ul><li v-for="u in d.unverified_numbers" :key="u">{{ u }}</li></ul>
        </div>
        <div v-else class="okbadge">All figures traced to computed table ✓</div>
        <p class="summary">{{ d.narrative?.summary }}</p>
        <div v-if="d.narrative?.drivers?.length" class="lbl">Drivers</div>
        <ul class="drivers"><li v-for="(x, i) in d.narrative?.drivers || []" :key="i"><b>{{ x.item }}</b> — {{ x.explanation }}</li></ul>
      </div>
    </div>
  </section>
</template>
