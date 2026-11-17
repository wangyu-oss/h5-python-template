<template>
  <svg viewBox="0 0 360 168" class="chart" role="img">
    <text v-if="!items.length" x="180" y="84" text-anchor="middle" fill="#94a3b8" font-size="13">暂无数据</text>
    <g v-for="(item, index) in items" :key="index">
      <rect :x="x(index)" :y="y(item.value)" :width="bar" :height="h(item.value)" rx="4" fill="#2563eb" />
      <text :x="x(index) + bar / 2" :y="y(item.value) - 6" text-anchor="middle" fill="#0f172a" font-size="11">{{ item.value }}</text>
      <text :x="x(index) + bar / 2" y="160" text-anchor="middle" fill="#64748b" font-size="11">{{ item.label }}</text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ items: Array<{ label: string; value: number }> }>()
const bar = computed(() => {
  const count = Math.max(props.items.length, 1)
  return Math.min(36, Math.floor(320 / count) - 8)
})
const max = computed(() => Math.max(...props.items.map((item) => item.value), 1))

function x(index: number) {
  const count = Math.max(props.items.length, 1)
  const slot = 320 / count
  return 20 + index * slot + (slot - bar.value) / 2
}

function h(value: number) {
  return Math.max(4, Math.round((value / max.value) * 110))
}

function y(value: number) {
  return 140 - h(value)
}
</script>

<style scoped>
.chart { width: 100%; height: 168px; display: block; }
</style>
