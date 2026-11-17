<template>
  <div class="page">
    <div class="toolbar"><el-button type="primary" @click="open()">新建轮播</el-button></div>
    <el-table :data="items" border>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="color" label="颜色" />
      <el-table-column prop="link" label="链接" />
      <el-table-column prop="enabled" label="启用" />
      <el-table-column label="操作"><template #default="{ row }"><el-button link @click="open(row)">编辑</el-button><el-button link type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      <template #empty><el-empty description="没有轮播" /></template>
    </el-table>
    <el-dialog v-model="visible" title="轮播">
      <el-form label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="颜色"><el-input v-model="form.color" /></el-form-item>
        <el-form-item label="链接"><el-input v-model="form.link" /></el-form-item>
        <el-form-item label="跳转"><el-select v-model="form.jump_type"><el-option label="页面" value="page" /><el-option label="外链" value="url" /><el-option label="不跳转" value="none" /></el-select></el-form-item>
        <el-form-item label="置顶"><el-switch v-model="form.pinned" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
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
const form = reactive<any>({ enabled: true, color: '#1989fa' })
async function load() { items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/banners')).data.items }
function open(row?: any) { Object.assign(form, row || { id: undefined, title: '', color: '#1989fa', link: '', enabled: true, jump_type: 'page', pinned: false }); visible.value = true }
async function save() { await http.post('/api/v1/admin/banners/save', form); visible.value = false; load() }
async function remove(row: any) { await http.post('/api/v1/admin/banners/delete', { id: row.id }); load() }
onMounted(load)
</script>
