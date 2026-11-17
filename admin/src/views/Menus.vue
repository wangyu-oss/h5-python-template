<template>
  <div class="page">
    <div class="toolbar"><el-button type="primary" @click="open()">新建菜单</el-button></div>
    <el-table :data="items" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="path" label="路径" />
      <el-table-column prop="permission" label="权限码" />
      <el-table-column prop="client" label="端" width="90" />
      <el-table-column prop="menu_type" label="类型" width="90" />
      <el-table-column label="操作" width="120"><template #default="{ row }"><el-button link @click="open(row)">编辑</el-button></template></el-table-column>
      <template #empty><el-empty description="没有菜单" /></template>
    </el-table>
    <el-dialog v-model="visible" title="菜单">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="路径"><el-input v-model="form.path" /></el-form-item>
        <el-form-item label="权限"><el-input v-model="form.permission" /></el-form-item>
        <el-form-item label="端"><el-select v-model="form.client"><el-option label="后台" value="admin" /><el-option label="H5" value="h5" /></el-select></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.menu_type"><el-option label="菜单" value="menu" /><el-option label="按钮" value="button" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'

const items = ref<any[]>([])
const visible = ref(false)
const form = reactive<any>({ client: 'admin', menu_type: 'menu' })

async function load() {
  items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/menus')).data.items
}
function open(row?: any) {
  Object.assign(form, row || { id: undefined, name: '', path: '', permission: '', client: 'admin', menu_type: 'menu', visible: true })
  visible.value = true
}
async function save() {
  await http.post('/api/v1/admin/menus/save', form)
  visible.value = false
  load()
}
onMounted(load)
</script>
