<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索用户" style="width: 200px" @change="search" />
      <el-select v-model="status" clearable placeholder="状态" style="width: 120px" @change="search"><el-option label="正常" value="active" /><el-option label="停用" value="disabled" /></el-select>
      <el-button type="primary" @click="open()">新建</el-button>
      <el-button :disabled="!selected.length" @click="batch('active')">批量启用</el-button>
      <el-button :disabled="!selected.length" @click="batch('disabled')">批量停用</el-button>
      <el-button @click="exportUsers">导出</el-button>
    </div>
    <el-table :data="items" border @selection-change="onSelect">
      <el-table-column type="selection" width="42" />
      <el-table-column prop="username" label="账号" />
      <el-table-column prop="display_name" label="昵称" />
      <el-table-column prop="phone" label="手机" />
      <el-table-column label="角色"><template #default="{ row }">{{ (row.role_names || []).join('、') || '—' }}</template></el-table-column>
      <el-table-column prop="tenant_name" label="客户" />
      <el-table-column label="状态" width="90"><template #default="{ row }">{{ row.status === 'active' ? '正常' : '停用' }}</template></el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link @click="detail(row)">详情</el-button>
          <el-button link @click="open(row)">编辑</el-button>
          <el-button link @click="toggle(row)">{{ row.status === 'active' ? '禁用' : '启用' }}</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty><el-empty description="没有用户" /></template>
    </el-table>
    <el-pagination class="pager" background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
    <el-drawer v-model="drawer" title="用户详情" size="480px">
      <p>{{ current?.display_name }} / {{ current?.phone }}</p>
      <p>客户：{{ current?.tenant_name || '平台' }}</p>
      <p>角色：{{ (current?.roles || []).map((item: any) => item.name).join('、') || '—' }}</p>
      <h4>最近登录</h4>
      <el-table :data="current?.login_logs || []" border>
        <el-table-column prop="success" label="结果" width="70"><template #default="{ row }">{{ row.success ? '成功' : '失败' }}</template></el-table-column>
        <el-table-column prop="ip" label="IP" />
        <el-table-column prop="created_at" label="时间" />
        <template #empty><el-empty description="没有登录记录" /></template>
      </el-table>
    </el-drawer>
    <el-dialog v-model="visible" title="用户">
      <el-form label-width="80px">
        <el-form-item label="账号"><el-input v-model="form.username" :disabled="Boolean(form.id)" /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" placeholder="不修改可留空" /></el-form-item>
        <el-form-item label="角色"><el-select v-model="form.role_ids" multiple style="width: 100%"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const items = ref<any[]>([])
const roles = ref<any[]>([])
const keyword = ref('')
const status = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const selected = ref<any[]>([])
const drawer = ref(false)
const current = ref<any>(null)
const visible = ref(false)
const form = reactive<any>({})

async function load() {
  const res = await http.get<never, { data: { items: any[]; total: number } }>('/api/v1/admin/users', {
    params: { keyword: keyword.value, status: status.value, page: page.value, page_size: pageSize },
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

function onSelect(rows: any[]) {
  selected.value = rows
}

function open(row?: any) {
  Object.keys(form).forEach((key) => delete form[key])
  Object.assign(form, row ? { ...row, password: '' } : { username: '', display_name: '', phone: '', password: '', role_ids: [] })
  visible.value = true
}

async function save() {
  await http.post('/api/v1/admin/users/save', form)
  visible.value = false
  ElMessage.success('已保存')
  load()
}

async function toggle(row: any) {
  await http.post('/api/v1/admin/users/status', { id: row.id, status: row.status === 'active' ? 'disabled' : 'active' })
  load()
}

async function batch(next: string) {
  await http.post('/api/v1/admin/users/status', { ids: selected.value.map((row) => row.id), status: next })
  ElMessage.success('已更新')
  load()
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}？`, '危险操作')
  await http.post('/api/v1/admin/users/delete', { id: row.id })
  load()
}

async function detail(row: any) {
  current.value = (await http.get<never, { data: any }>(`/api/v1/admin/users/${row.id}`)).data
  drawer.value = true
}

async function exportUsers() {
  const blob = await http.get<never, Blob>('/api/v1/admin/users/export', { responseType: 'blob' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'users.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  roles.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/roles')).data.items
  load()
})
</script>
