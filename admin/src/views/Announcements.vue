<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="标题" style="width: 180px" @change="search" />
      <el-select v-model="enabled" clearable placeholder="状态" style="width: 120px" @change="search">
        <el-option label="启用" value="yes" />
        <el-option label="停用" value="no" />
      </el-select>
      <el-button type="primary" @click="open()">新建公告</el-button>
    </div>
    <el-table :data="items" border>
      <el-table-column prop="title" label="标题" />
      <el-table-column label="启用" width="80"><template #default="{ row }">{{ row.enabled ? '是' : '否' }}</template></el-table-column>
      <el-table-column label="操作" width="160"><template #default="{ row }"><el-button link @click="open(row)">编辑</el-button><el-button link type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      <template #empty><el-empty description="没有公告" /></template>
    </el-table>
    <el-pagination class="pager" background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
    <el-dialog v-model="visible" title="公告" width="720px">
      <el-form label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
        <el-form-item label="正文"><el-input v-model="form.content" type="textarea" :rows="8" placeholder="支持 HTML" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'

const items = ref<any[]>([])
const keyword = ref('')
const enabled = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const visible = ref(false)
const form = reactive<any>({ enabled: true, content: '' })

async function load() {
  const res = await http.get<never, { data: { items: any[]; total: number } }>('/api/v1/admin/announcements', {
    params: { keyword: keyword.value, enabled: enabled.value, page: page.value, page_size: pageSize },
  })
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

function open(row?: any) {
  Object.assign(form, row || { id: undefined, title: '', content: '<p></p>', enabled: true })
  visible.value = true
}

async function save() {
  await http.post('/api/v1/admin/announcements/save', form)
  visible.value = false
  load()
}

async function remove(row: any) {
  await http.post('/api/v1/admin/announcements/delete', { id: row.id })
  load()
}

onMounted(load)
</script>
