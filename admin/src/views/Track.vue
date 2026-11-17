<template>
  <div class="page">
    <el-row :gutter="12">
      <el-col :span="8"><el-card>事件 {{ summary.total }}</el-card></el-col>
      <el-col :span="8"><el-card>异常 {{ summary.errors }}</el-card></el-col>
    </el-row>
    <el-table :data="summary.names" border style="margin-top: 12px">
      <el-table-column prop="name" label="事件" />
      <el-table-column prop="total" label="次数" />
      <template #empty><el-empty description="没有事件" /></template>
    </el-table>
    <h3>事件目录</h3>
    <div class="toolbar">
      <el-input v-model="catalogName" placeholder="事件名" style="width: 160px" />
      <el-input v-model="catalogTitle" placeholder="说明" style="width: 200px" />
      <el-button type="primary" @click="saveCatalog">保存说明</el-button>
    </div>
    <el-table :data="catalogItems" border><el-table-column prop="name" label="事件" /><el-table-column prop="title" label="说明" /><el-table-column prop="enabled" label="启用" /><template #empty><el-empty description="没有目录" /></template></el-table>
    <h3>黑名单</h3>
    <div class="toolbar">
      <el-input v-model="ip" placeholder="IP" style="width: 180px" />
      <el-button type="primary" @click="add">加入</el-button>
    </div>
    <el-table :data="blacklist" border>
      <el-table-column prop="ip" label="IP" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column label="操作"><template #default="{ row }"><el-button link type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      <template #empty><el-empty description="没有黑名单" /></template>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
const summary = reactive<any>({ total: 0, errors: 0, names: [] })
const blacklist = ref<any[]>([])
const ip = ref('')
const catalogItems = ref<any[]>([])
const catalogName = ref('')
const catalogTitle = ref('')
async function load() {
  Object.assign(summary, (await http.get<never, { data: any }>('/api/v1/admin/track/summary')).data)
  blacklist.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/blacklist')).data.items
  catalogItems.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/track/catalog')).data.items
}
async function saveCatalog() {
  await http.post('/api/v1/admin/track/catalog', { name: catalogName.value, title: catalogTitle.value, enabled: true })
  load()
}
async function add() { await http.post('/api/v1/admin/blacklist/save', { ip: ip.value, reason: '手动加入', enabled: true }); load() }
async function remove(row: any) { await http.post('/api/v1/admin/blacklist/delete', { id: row.id }); load() }
onMounted(load)
</script>
