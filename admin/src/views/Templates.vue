<template>
  <div class="page">
    <el-table :data="items" border>
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="channel" label="渠道" width="100" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="content" label="内容" />
      <el-table-column label="操作" width="100"><template #default="{ row }"><el-button link @click="open(row)">编辑</el-button></template></el-table-column>
      <template #empty><el-empty description="没有模板" /></template>
    </el-table>
    <el-dialog v-model="visible" title="模板">
      <el-form label-width="80px">
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="渠道"><el-select v-model="form.channel"><el-option label="短信" value="sms" /><el-option label="邮件" value="mail" /><el-option label="站内信" value="inbox" /><el-option label="微信" value="wechat" /></el-select></el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
    <div class="toolbar" style="margin-top: 12px">
      <el-input v-model="phone" placeholder="测试手机号" style="width: 180px" />
      <el-button @click="sms">发测试短信</el-button>
      <el-input v-model="email" placeholder="测试邮箱" style="width: 180px" />
      <el-button @click="mail">发测试邮件</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
const items = ref<any[]>([])
const visible = ref(false)
const form = reactive<any>({ channel: 'sms', enabled: true })
const phone = ref('')
const email = ref('')
async function load() { items.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/templates')).data.items }
function open(row: any) { Object.assign(form, row); visible.value = true }
async function save() { await http.post('/api/v1/admin/templates/save', form); visible.value = false; load() }
async function sms() { const res = await http.post<never, { data: any }>('/api/v1/admin/sms/test', { phone: phone.value, content: '测试短信' }); ElMessage.success(res.data.mock ? '已写入控制台' : '已提交') }
async function mail() { await http.post('/api/v1/admin/mail/test', { email: email.value, title: '测试', content: '你好' }); ElMessage.success('已发送或写入控制台') }
onMounted(load)
</script>
