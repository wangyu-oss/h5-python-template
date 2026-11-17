<template>
  <div class="page settings">
    <el-tabs v-model="tab" class="tabs">
      <el-tab-pane v-for="name in tabs" :key="name" :label="labels[name]" :name="name" />
    </el-tabs>
    <el-table :data="filtered" border class="grid">
      <el-table-column prop="key" label="键" width="220" />
      <el-table-column prop="remark" label="说明" />
      <el-table-column label="值">
        <template #default="{ row }"><el-input v-model="row.value" /></template>
      </el-table-column>
    </el-table>
    <div class="foot"><el-button type="primary" @click="save">保存全部</el-button></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
const items = ref<any[]>([])
const tab = ref('basic')
const tabs = ['basic', 'security', 'h5', 'pay', 'message']
const labels: Record<string, string> = { basic: '基础', security: '安全', h5: 'H5', pay: '支付', message: '消息' }
const filtered = computed(() => items.value.filter((item) => (item.category || 'basic') === tab.value))
async function load() { items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/settings')).data.items }
async function save() {
  const pay = items.value.find((item) => item.key === 'module_pay' || item.key === 'feature_pay')
  if (pay && pay.value === 'no') await ElMessageBox.confirm('确认关闭支付？', '危险操作')
  await http.post('/api/v1/admin/settings/save', { items: items.value })
  ElMessage.success('已保存，修改已留痕')
}
onMounted(load)
</script>

<style scoped>
.tabs { flex: none; }
.grid { flex: 1; min-height: 0; }
.foot { flex: none; margin-top: 12px; }
</style>
