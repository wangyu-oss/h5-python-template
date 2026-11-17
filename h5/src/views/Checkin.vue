<template>
  <div class="page">
    <div class="card">
      <strong>{{ status.today ? '今天已签到' : '今天还没有签到' }}</strong>
      <div class="muted">累计 {{ status.total || 0 }} 天，积分 {{ status.points || 0 }}</div>
      <van-button type="primary" block :disabled="status.today" @click="submit">签到</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { showToast } from 'vant'
import http from '@/api/http'

const status = reactive({ today: false, total: 0, points: 0 })

async function load() {
  const res = await http.get<never, { data: typeof status }>('/api/v1/plugins/checkin/status')
  Object.assign(status, res.data)
}

async function submit() {
  try {
    await http.post('/api/v1/plugins/checkin')
    showToast('签到成功')
    await load()
  } catch (error) {
    showToast((error as Error).message)
  }
}

onMounted(load)
</script>

<style scoped>
.card { display: grid; gap: 12px; }
.card strong { font-size: 18px; }
.card :deep(.van-button) { margin-top: 4px; }
</style>
