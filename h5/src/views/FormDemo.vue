<template>
  <div class="page">
    <van-form @submit="onSubmit">
      <van-field v-model="form.name" label="姓名" placeholder="请输入" :rules="[{ required: true, message: '请填写姓名' }]" />
      <van-field v-model="form.phone" label="手机号" placeholder="11 位手机号" :rules="[{ validator: phoneValidator, message: '手机号格式不正确' }]" />
      <van-field name="switch" label="接收通知">
        <template #input><van-switch v-model="form.notify" /></template>
      </van-field>
      <van-field name="rate" label="评分">
        <template #input><van-rate v-model="form.score" /></template>
      </van-field>
      <van-field name="slider" label="进度">
        <template #input><van-slider v-model="form.progress" /></template>
      </van-field>
      <van-field v-model="regionText" label="地区" readonly is-link placeholder="省市区" @click="showRegion = true" />
      <van-field v-model="form.date" label="日期" readonly is-link @click="showDate = true" />
      <div class="card">
        <div>手写签名</div>
        <canvas ref="canvasRef" width="320" height="140" class="sign" @pointerdown="startDraw" @pointermove="draw" @pointerup="endDraw" />
        <van-button size="small" @click.prevent="clearSign">清除</van-button>
      </div>
      <div class="actions">
        <van-button round block type="primary" native-type="submit">提交</van-button>
      </div>
    </van-form>
    <van-popup v-model:show="showRegion" round position="bottom">
      <van-cascader title="地区" :options="regions" @close="showRegion = false" @finish="onRegion" />
    </van-popup>
    <van-calendar v-model:show="showDate" @confirm="onDate" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import http from '@/api/http'
import { localCache } from '@/utils/storage'
import { phone } from '@/utils/validate'
import { track } from '@/utils/track'

const form = reactive({ name: '', phone: '', notify: true, score: 5, progress: 30, date: '', region: '' })
const regionText = ref('')
const regions = ref<any[]>([])
const showRegion = ref(false)
const showDate = ref(false)
const canvasRef = ref<HTMLCanvasElement>()
let drawing = false
let canvasReady = false

function phoneValidator(value: string) {
  return phone(value).ok
}

function mapRegion(nodes: any[]): any[] {
  return (nodes || []).map((node) => ({ text: node.name, value: node.code, children: node.children ? mapRegion(node.children) : undefined }))
}

function onRegion({ selectedOptions }: { selectedOptions: Array<{ text: string }> }) {
  regionText.value = selectedOptions.map((item) => item.text).join(' / ')
  form.region = regionText.value
  showRegion.value = false
}

function onDate(value: Date) {
  form.date = value.toISOString().slice(0, 10)
  showDate.value = false
}

function prepareCanvas() {
  const canvas = canvasRef.value
  if (!canvas || canvasReady) return
  const rect = canvas.getBoundingClientRect()
  const ratio = window.devicePixelRatio || 1
  canvas.width = Math.max(1, Math.floor(rect.width * ratio))
  canvas.height = Math.max(1, Math.floor(rect.height * ratio))
  const ctx = canvas.getContext('2d')
  ctx?.setTransform(ratio, 0, 0, ratio, 0, 0)
  if (ctx) {
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.strokeStyle = '#0f172a'
  }
  canvasReady = true
}

function pointOf(event: PointerEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  return { x: event.clientX - rect.left, y: event.clientY - rect.top }
}

function startDraw(event: PointerEvent) {
  prepareCanvas()
  drawing = true
  const ctx = canvasRef.value?.getContext('2d')
  if (!ctx) return
  const point = pointOf(event)
  ctx.beginPath()
  ctx.moveTo(point.x, point.y)
}

function draw(event: PointerEvent) {
  if (!drawing || !canvasRef.value) return
  const ctx = canvasRef.value.getContext('2d')
  if (!ctx) return
  const point = pointOf(event)
  ctx.lineTo(point.x, point.y)
  ctx.stroke()
}

function endDraw() {
  drawing = false
}

function clearSign() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ratio = window.devicePixelRatio || 1
  canvas.getContext('2d')?.clearRect(0, 0, canvas.width / ratio, canvas.height / ratio)
}

async function persist() {
  const content = JSON.stringify(form)
  localCache.set('draft:form', form)
  await http.post('/api/v1/drafts', { key: 'form', content }).catch(() => undefined)
}

async function onSubmit() {
  track('form_submit')
  await persist()
  showToast('已校验并保存草稿')
}

onMounted(async () => {
  const cached = localCache.get<typeof form>('draft:form')
  if (cached) Object.assign(form, cached)
  try {
    const remote = await http.get<never, { data: { content: string } }>('/api/v1/drafts', { params: { key: 'form' } })
    if (remote.data.content) Object.assign(form, JSON.parse(remote.data.content))
    const tree = await http.get<never, { data: { items: any[] } }>('/api/v1/regions')
    regions.value = mapRegion(tree.data.items)
  } catch {
    /* 草稿恢复失败时继续使用本地内容 */
  }
})

onBeforeUnmount(persist)
</script>

<style scoped>
.sign { width: 100%; height: 140px; background: #fff; border: 1px dashed #dcdee0; border-radius: 8px; touch-action: none; }
.actions { margin: 16px; }
</style>
