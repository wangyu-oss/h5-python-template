<template>
  <div class="page">
    <div class="toolbar">
      <el-button type="primary" @click="open()">新建客户</el-button>
    </div>
    <el-table :data="items" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="expire_at" label="到期" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link @click="enter(row)">进入</el-button>
          <el-button link @click="open(row)">编辑</el-button>
          <el-button link type="danger" @click="disable(row)">{{ row.status === 'active' ? '停用' : '启用' }}</el-button>
        </template>
      </el-table-column>
      <template #empty><el-empty description="还没有客户" /></template>
    </el-table>
    <el-dialog v-model="visible" title="客户">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const items = ref<any[]>([])
const visible = ref(false)
const form = reactive<any>({})

async function load() {
  items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/tenants')).data.items
}

function open(row?: any) {
  Object.assign(form, row || { name: '', code: '' })
  visible.value = true
}

async function save() {
  await http.post('/api/v1/admin/tenants/save', form)
  visible.value = false
  ElMessage.success('已保存')
  load()
}

function enter(row: any) {
  useUserStore().setTenant(String(row.id))
  ElMessage.success(`已切换到 ${row.name}`)
}

async function disable(row: any) {
  const next = row.status === 'active' ? 'disabled' : 'active'
  if (next === 'disabled') await ElMessageBox.confirm(`确认停用客户 ${row.name}？`, '危险操作')
  await http.post('/api/v1/admin/tenants/status', { id: row.id, status: next })
  load()
}

onMounted(load)
</script>
