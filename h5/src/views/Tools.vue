<template>
  <div class="page">
    <div class="card">
      <van-field v-model="text" label="内容" placeholder="https://" />
      <img v-if="qr" :src="qr" alt="" class="qr" />
      <div class="row">
        <van-button size="small" type="primary" @click="makeQr">二维码</van-button>
        <van-button size="small" @click="printPage">打印</van-button>
        <van-button size="small" @click="makePdf">导出 PDF</van-button>
      </div>
    </div>
    <div class="card editor" contenteditable="true">{{ text }}</div>
    <div class="card sheet">
      <div class="row">
        <van-button size="small" type="primary" @click="exportLocal">前端导出 Excel</van-button>
        <van-button size="small" @click="exportServer">后端导出 Excel</van-button>
        <button type="button" class="pick" @click="fileRef?.click()">选择 Excel</button>
      </div>
      <input ref="fileRef" class="sr-file" type="file" accept=".xlsx,.xls" @change="importExcel" />
      <pre v-if="imported" class="muted">{{ imported }}</pre>
    </div>
    <div class="card">
      <van-button v-longpress="() => showToast('长按触发')" size="small">长按试试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import http from '@/api/http'
import { getAccess } from '@/utils/token'

const text = ref('https://localhost:5173/home')
const qr = ref('')
const imported = ref('')
const fileRef = ref<HTMLInputElement>()

async function makeQr() {
  const QRCode = await import('qrcode')
  qr.value = await QRCode.toDataURL(text.value || 'h5')
}

function printPage() {
  window.print()
}

async function makePdf() {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF()
  doc.text(text.value || 'H5 PDF', 10, 20)
  doc.save('h5.pdf')
}

async function exportLocal() {
  const XLSX = await import('xlsx')
  const sheet = XLSX.utils.json_to_sheet([{ name: 'demo', value: text.value }])
  const book = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(book, sheet, 'demo')
  XLSX.writeFile(book, 'demo.xlsx')
}

async function exportServer() {
  const response = await fetch('/api/v1/tools/excel/export', { headers: { Authorization: `Bearer ${getAccess()}` } })
  if (!response.ok) {
    showToast('导出失败')
    return
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'users.xlsx'
  anchor.click()
}

async function importExcel(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const XLSX = await import('xlsx')
  const buffer = await file.arrayBuffer()
  const book = XLSX.read(buffer)
  const rows = XLSX.utils.sheet_to_json(book.Sheets[book.SheetNames[0]])
  imported.value = JSON.stringify(rows.slice(0, 5), null, 2)
  const body = new FormData()
  body.append('file', file)
  const remote = await http.post<never, { data: { count: number } }>('/api/v1/tools/excel/import', body)
  showToast(`后端解析 ${remote.data.count} 行`)
}
</script>

<style scoped>
.qr { display: block; width: 160px; margin: 12px auto; }
.row { margin-top: 12px; }
.editor { min-height: 88px; outline: none; line-height: 1.6; overflow-wrap: anywhere; }
.sheet { display: grid; gap: 12px; }
pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
</style>
