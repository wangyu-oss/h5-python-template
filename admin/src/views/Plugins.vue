<template>
  <div class="page">
    <el-table :data="items" border>
      <el-table-column prop="name" label="插件" />
      <el-table-column prop="code" label="编码" />
      <el-table-column label="实现"><template #default="{ row }">{{ row.implemented ? '已实现' : '仅占位' }}</template></el-table-column>
      <el-table-column label="开关"><template #default="{ row }"><el-switch :model-value="row.switch === 'yes'" :disabled="!row.implemented" @change="(value: boolean) => toggle(row, value)" /></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const items = ref<any[]>([])
async function load() { items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/plugins')).data.items }
async function toggle(row: any, enabled: boolean) {
  await http.post('/api/v1/admin/plugins/toggle', { code: row.code, enabled })
  load()
}
onMounted(load)
</script>
