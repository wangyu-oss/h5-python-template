<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="关键词" style="width: 180px" @change="search" />
      <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" @change="search" />
      <el-button @click="download">导出登录日志</el-button>
    </div>
    <el-tabs v-model="tab" class="tabs" @tab-change="search">
      <el-tab-pane label="登录" name="login" />
      <el-tab-pane label="操作" name="op" />
      <el-tab-pane label="接口异常" name="api" />
    </el-tabs>
    <el-table v-if="tab === 'login'" :data="items" border class="grid">
      <el-table-column prop="username" label="账号" />
      <el-table-column label="成功" width="80"><template #default="{ row }">{{ row.success ? '是' : '否' }}</template></el-table-column>
      <el-table-column prop="message" label="说明" />
      <el-table-column prop="ip" label="IP" />
      <el-table-column prop="created_at" label="时间" />
      <template #empty><el-empty description="没有日志" /></template>
    </el-table>
    <el-table v-else-if="tab === 'op'" :data="items" border class="grid">
      <el-table-column prop="username" label="账号" />
      <el-table-column prop="action" label="动作" />
      <el-table-column prop="target" label="对象" />
      <el-table-column prop="created_at" label="时间" />
      <template #empty><el-empty description="没有日志" /></template>
    </el-table>
    <el-table v-else :data="items" border class="grid">
      <el-table-column prop="method" label="方法" width="80" />
      <el-table-column prop="path" label="路径" />
      <el-table-column prop="status_code" label="状态" width="80" />
      <el-table-column prop="duration_ms" label="耗时" width="80" />
      <el-table-column prop="trace_id" label="traceId" />
      <template #empty><el-empty description="没有日志" /></template>
    </el-table>
    <el-pagination class="pager" background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const tab = ref('login')
const keyword = ref('')
const range = ref<string[]>([])
const items = ref<any[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)

function params() {
  const query: Record<string, string | number> = { keyword: keyword.value, page: page.value, page_size: pageSize }
  if (range.value?.length === 2) {
    query.start = range.value[0]
    query.end = range.value[1]
  }
  if (tab.value === 'api') query.status = 'error'
  return query
}

async function load() {
  const url = tab.value === 'login' ? '/api/v1/admin/logs/login' : tab.value === 'op' ? '/api/v1/admin/logs/operation' : '/api/v1/admin/logs/api'
  const res = await http.get<never, { data: { items: any[]; total: number } }>(url, { params: params() })
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

async function download() {
  const query: Record<string, string> = { keyword: keyword.value }
  if (range.value?.length === 2) {
    query.start = range.value[0]
    query.end = range.value[1]
  }
  const blob = await http.get<never, Blob>('/api/v1/admin/logs/login/export', { params: query, responseType: 'blob' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'login-logs.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.tabs { flex: none; }
.grid { flex: 1; min-height: 0; }
</style>
