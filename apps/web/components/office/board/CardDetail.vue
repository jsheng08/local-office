<script setup lang="ts">
import type { Card } from '../../../types/office'
import { changeLabel, hours } from './presentation'
defineProps<{ card: Card }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <section class="detail" aria-labelledby="office-card-title" tabindex="-1">
    <header><code>{{ card.id }}</code><button type="button" aria-label="Close card details" @click="$emit('close')">✕</button></header>
    <h2 id="office-card-title">{{ card.title }}</h2>
    <span v-if="changeLabel(card)" class="chip">{{ changeLabel(card) }}</span>
    <section v-if="card.story"><h3>User story</h3><p v-if="card.story.as_a"><b>As a</b> {{ card.story.as_a }}</p><p v-if="card.story.i_want"><b>I want</b> {{ card.story.i_want }}</p><p v-if="card.story.so_that"><b>so that</b> {{ card.story.so_that }}</p></section>
    <section><h3>Acceptance criteria</h3><ul v-if="card.acceptance_criteria?.length"><li v-for="(criterion, index) in card.acceptance_criteria" :key="index">{{ criterion }}</li></ul><p v-else class="muted">No acceptance criteria supplied.</p></section>
    <section v-if="card.est"><h3>Estimated effort</h3><p class="effort">{{ hours(card.est.low) }}–{{ hours(card.est.high) }} h</p><p>Expected: {{ hours(card.est.pert) }} h</p></section>
    <section v-if="card.change && card.reason"><h3>Why this changed</h3><p>{{ card.reason }}</p></section>
    <section><h3>Source evidence</h3><ul v-if="card.citations?.length" class="sources"><li v-for="(citation, index) in card.citations" :key="index"><div class="source-head"><code>{{ citation.paragraph_id }}</code><span class="chip" :class="{ verified: citation.status === 'verified' }">{{ citation.status || 'Unverified' }}</span></div><blockquote>“{{ citation.quote }}”</blockquote></li></ul><p v-else class="muted">No citations supplied.</p></section>
    <section><h3>Recommended staff</h3><p class="approval">Recommendation - requires human approval</p><ul v-if="card.staff.length"><li v-for="person in card.staff" :key="person.staff_id"><strong>{{ person.name }}</strong><p>{{ person.reason || 'No recommendation reason supplied.' }}</p></li></ul><p v-else class="muted">Unassigned</p></section>
  </section>
</template>

<style scoped>
.detail{position:absolute;inset:0 0 0 auto;width:min(600px,100%);box-sizing:border-box;background:#fffdf8;color:#1f2a2e;box-shadow:-18px 0 60px #0005;padding:28px 32px;overflow-y:auto;z-index:3;font-size:18px;line-height:1.6;overflow-wrap:anywhere}.detail header,.source-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.detail button{background:#10201f;color:#fff;border:0;border-radius:10px;width:44px;height:44px;font-size:22px;cursor:pointer}.detail button:focus-visible{outline:4px solid #76b900;outline-offset:3px}h2{font-size:30px;line-height:1.2;margin:22px 0}h3{font-size:20px;margin:0 0 12px}section section{border-top:1px solid #d6cebf;margin-top:26px;padding-top:22px}p{margin:8px 0}ul{padding-left:24px}li{margin-bottom:14px}.sources{list-style:none;padding:0}.sources li{background:#efe7d8;padding:16px;border-radius:12px}blockquote{margin:14px 0 0}.chip{display:inline-block;background:#ffdf9e;color:#684000;font-size:13px;font-weight:750;border-radius:20px;padding:4px 10px}.chip.verified{background:#d7efdc;color:#205a32}.effort{font-size:30px;font-weight:800}.muted{color:#64716b}.approval{color:#684000;font-size:16px}code{font-size:15px}
</style>
