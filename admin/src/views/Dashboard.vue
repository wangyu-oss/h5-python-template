<template>
  <div class="page dash">
    <div class="toolbar">
      <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" @change="load" />
      <el-button @click="download">导出</el-button>
    </div>
    <el-row :gutter="12">
      <el-col v-for="item in cards" :key="item.label" :span="6">
        <el-card class="stat"><div class="muted">{{ item.label }}</div><strong>{{ item.value }}</strong></el-card>
      </el-col>
    </el-row>
    <el-row :gutter="12" class="charts">
      <el-col :span="8"><el-card header="用户趋势"><TrendChart :items="userBars" /></el-card></el-col>
      <el-col :span="8"><el-card header="订单趋势"><TrendChart :items="orderBars" /></el-card></el-col>
      <el-col :span="8"><el-card header="支付漏斗"><TrendChart :items="funnelBars" /></el-card></el-col>
    </el-row>
    <el-row :gutter="12" class="todos">
      <el-col :span="8">
        <el-card header="待支付">
          <button class="link" type="button" @click="router.push({ path: '/orders', query: { status: 'pending' } })">{{ pending }} 笔待支付订单</button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="发送失败">
          <button v-for="item in failedMessages" :key="item.id" class="link" type="button" @click="router.push('/templates')">{{ item.channel }} {{ item.target }} {{ item.error || '失败' }}</button>
          <el-empty v-if="!failedMessages.length" description="没有失败消息" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="登录失败">
          <button v-for="item in failedLogins" :key="item.id" class="link" type="button" @click="router.push('/logs')">{{ item.username }} {{ item.ip }} {{ item.created_at }}</button>
          <el-empty v-if="!failedLogins.length" description="没有登录失败" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import TrendChart from '@/components/TrendChart.vue'

const router = useRouter()
const cards = ref<Array<{ label: string; value: number }>>([])
const range = ref<string[]>([])
const users = ref<any[]>([])
const orders = ref<any[]>([])
const funnel = ref<any[]>([])
const pending = ref(0)
const failedMessages = ref<any[]>([])
const failedLogins = ref<any[]>([])

const userBars = computed(() => users.value.map((item) => ({ label: String(item.day).slice(5), value: item.total })))
const orderBars = computed(() => orders.value.map((item) => ({ label: String(item.day).slice(5), value: item.total })))
const funnelBars = computed(() => funnel.value.map((item) => ({ label: item.name, value: item.total })))

async function load() {
  const params: Record<string, string> = {}
  if (range.value?.length === 2) {
    params.start = range.value[0]
    params.end = range.value[1]
  }
  const res = await http.get<never, { data: any }>('/api/v1/admin/dashboard', { params })
  const data = res.data
  cards.value = [
    { label: '用户', value: data.users },
    { label: '订单', value: data.orders },
    { label: '已支付', value: data.paid_orders },
    { label: '埋点', value: data.events },
  ]
  users.value = data.users_by_day || []
  orders.value = data.orders_by_day || []
  funnel.value = data.pay_funnel || []
  pending.value = data.pending_orders || 0
  failedMessages.value = data.failed_messages || []
  failedLogins.value = data.failed_logins || []
}

async function download() {
  const params = range.value?.length === 2 ? { start: range.value[0], end: range.value[1] } : {}
  const blob = await http.get<never, Blob>('/api/v1/admin/dashboard/export', { params, responseType: 'blob' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'dashboard.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.dash { overflow: auto; }
.stat strong { display: block; margin-top: 8px; font-size: 28px; }
.muted { color: #64748b; }
.charts, .todos { margin-top: 12px; }
.link {
  display: block; width: 100%; margin: 0 0 8px; padding: 0;
  border: 0; background: transparent; color: #2563eb; text-align: left; cursor: pointer;
}
</style>
