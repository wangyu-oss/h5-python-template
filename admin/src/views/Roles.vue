<template>
  <div class="page">
    <div class="toolbar"><el-button type="primary" @click="open()">新建角色</el-button></div>
    <el-table :data="items" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="data_scope" label="数据范围" />
      <el-table-column label="操作" width="160"><template #default="{ row }"><el-button link @click="open(row)">编辑</el-button><el-button link type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      <template #empty><el-empty description="没有角色" /></template>
    </el-table>
    <el-dialog v-model="visible" title="角色" width="640px">
      <el-form label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="数据范围"><el-select v-model="form.data_scope"><el-option label="全部" value="all" /><el-option label="本部门" value="dept" /><el-option label="本人" value="self" /></el-select></el-form-item>
        <el-form-item label="权限"><el-tree ref="treeRef" node-key="id" show-checkbox :data="tree" :props="{ label: 'name', children: 'children' }" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import http from '@/api/http'

const items = ref<any[]>([])
const tree = ref<any[]>([])
const visible = ref(false)
const form = reactive<any>({ data_scope: 'all' })
const treeRef = ref<any>()

async function load() {
  items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/roles')).data.items
  tree.value = (await http.get<never, { data: { tree: any[] } }>('/api/v1/admin/menus')).data.tree
}

async function open(row?: any) {
  Object.assign(form, row || { id: undefined, name: '', code: '', data_scope: 'self', menu_ids: [] })
  visible.value = true
  await nextTick()
  treeRef.value?.setCheckedKeys(form.menu_ids || [])
}

async function save() {
  form.menu_ids = treeRef.value?.getCheckedKeys() || []
  await http.post('/api/v1/admin/roles/save', form)
  visible.value = false
  load()
}

async function remove(row: any) {
  await http.post('/api/v1/admin/roles/delete', { id: row.id })
  load()
}

onMounted(load)
</script>
