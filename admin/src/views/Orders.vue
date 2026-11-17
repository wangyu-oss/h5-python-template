<template>
  <div class="page">
    <div class="toolbar">
      <el-select v-model="status" clearable placeholder="状态" style="width: 140px" @change="search">
        <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="channel" clearable placeholder="渠道" style="width: 120px" @change="search">
        <el-option label="模拟" value="mock" />
        <el-option label="微信" value="wechat" />
        <el-option label="支付宝" value="alipay" />
      </el-select>
      <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" @change="search" />
      <el-input v-model="keyword" placeholder="订单号或标题" style="width: 180px" @change="search" />
    </div>
    <el-table :data="items" border>
      <el-table-column prop="order_no" label="订单号" />
      <el-table-column prop="username" label="用户" />
      <el-table-column prop="subject" label="标题" />
      <el-table-column prop="amount" label="金额(分)" width="100" />
      <el-table-column label="渠道" width="100"><template #default="{ row }">{{ channelLabel(row.channel) }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{ row }">{{ statusLabel(row.status) }}</template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }"><el-button link @click="open(row)">详情</el-button></template>
      </el-table-column>
      <template #empty><el-empty description="没有订单" /></template>
    </el-table>
    <el-pagination class="pager" background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
    <el-drawer v-model="drawer" title="订单详情" size="480px">
      <template v-if="current">
        <p>订单号：{{ current.order_no }}</p>
        <p>用户：{{ current.username }}</p>
        <p>标题：{{ current.subject }}</p>
        <p>金额：{{ current.amount }} 分</p>
        <p>渠道：{{ channelLabel(current.channel) }}</p>
        <p>状态：{{ statusLabel(current.status) }}</p>
        <p>支付时间：{{ current.paid_at || '—' }}</p>
        <p>备注：{{ current.remark || '—' }}</p>
        <div class="toolbar">
          <el-button @click="remark">备注</el-button>
          <el-button v-if="current.status === 'paid'" type="danger" @click="refund">退款</el-button>
        </div>
        <h4>状态记录</h4>
        <el-table :data="current.callbacks || []" border>
          <el-table-column prop="channel" label="渠道" width="90" />
          <el-table-column label="结果" width="80"><template #default="{ row }">{{ row.success ? '成功' : '失败' }}</template></el-table-column>
          <el-table-column prop="created_at" label="时间" />
          <template #empty><el-empty description="没有回调记录" /></template>
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const route = useRoute()
const items = ref<any[]>([])
const status = ref(String(route.query.status || ''))
const channel = ref('')
const keyword = ref('')
const range = ref<string[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const drawer = ref(false)
const current = ref<any>(null)
const statusOptions = [
  { value: 'pending', label: '待支付' },
  { value: 'paid', label: '已支付' },
  { value: 'refunding', label: '退款中' },
  { value: 'refunded', label: '已退款' },
  { value: 'closed', label: '已关闭' },
]

function statusLabel(value: string) {
  return statusOptions.find((item) => item.value === value)?.label || value
}

function channelLabel(value: string) {
  return ({ mock: '模拟', wechat: '微信', alipay: '支付宝' } as Record<string, string>)[value] || value
}

async function load() {
  const params: Record<string, string | number> = { status: status.value, channel: channel.value, keyword: keyword.value, page: page.value, page_size: pageSize }
  if (range.value?.length === 2) {
    params.start = range.value[0]
    params.end = range.value[1]
  }
  const res = await http.get<never, { data: { items: any[]; total: number } }>('/api/v1/admin/orders', { params })
  items.value = res.data.items
  total.value = res.data.total
}

function search() {
  page.value = 1
  load()
}

function onPage(value: number) {
  page.value = value
  load()
}

async function open(row: any) {
  current.value = (await http.get<never, { data: any }>(`/api/v1/admin/orders/${row.order_no}`)).data
  drawer.value = true
}

async function remark() {
  const result = await ElMessageBox.prompt('备注', '订单备注', { inputValue: current.value?.remark || '' })
  await http.post(`/api/v1/admin/orders/${current.value.order_no}/remark`, { remark: result.value })
  await open(current.value)
  load()
}

async function refund() {
  await ElMessageBox.confirm('确认退款？仅模拟渠道会直接改状态', '危险操作')
  await http.post(`/api/v1/admin/orders/${current.value.order_no}/refund`)
  ElMessage.success('已退款')
  await open(current.value)
  load()
}

onMounted(load)
</script>
