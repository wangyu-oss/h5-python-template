<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="文件名" style="width: 180px" @change="search" />
      <el-upload :http-request="upload" :show-file-list="false"><el-button type="primary">上传</el-button></el-upload>
    </div>
    <el-table :data="items" border>
      <el-table-column prop="name" label="文件" />
      <el-table-column prop="size" label="大小" width="100" />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="storage" label="存储" width="100" />
      <el-table-column label="访问"><template #default="{ row }"><a :href="row.url" target="_blank">打开</a></template></el-table-column>
      <template #empty><el-empty description="没有文件" /></template>
    </el-table>
    <el-pagination class="pager" background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { UploadRequestOptions } from 'element-plus'
import http from '@/api/http'

const items = ref<any[]>([])
const keyword = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)

async function load() {
  const res = await http.get<never, { data: { items: any[]; total: number } }>('/api/v1/admin/files', {
    params: { keyword: keyword.value, page: page.value, page_size: pageSize },
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

async function upload(options: UploadRequestOptions) {
  const body = new FormData()
  body.append('file', options.file)
  await http.post('/api/v1/files/upload', body)
  load()
}

onMounted(load)
</script>
