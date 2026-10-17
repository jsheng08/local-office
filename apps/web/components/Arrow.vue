<script setup lang="ts">
const props = defineProps<{ a: any; b: any }>()
const A = computed(() => props.a ?? '—')
const B = computed(() => props.b ?? '—')
</script>
<template>
  <span v-if="A === B">{{ A }}</span>
  <span v-else><span class="old">{{ A }}</span> → <span class="new">{{ B }}</span></span>
</template>
