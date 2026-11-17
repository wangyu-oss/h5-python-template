<template>
  <div class="page">
    <div class="card">
      <van-uploader :after-read="afterRead" />
      <div v-if="url" class="preview"><img :src="url" alt="" /></div>
    </div>
    <div class="card chunk">
      <strong>分片上传</strong>
      <button type="button" class="pick" @click="openFile">选择文件</button>
      <input ref="fileRef" class="sr-file" type="file" @change="onChunk" />
      <div v-if="chunkText" class="muted">{{ chunkText }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import http from '@/api/http'

const url = ref('')
const chunkText = ref('')
const fileRef = ref<HTMLInputElement>()

function openFile() {
  fileRef.value?.click()
}

async function afterRead(item: UploaderFileListItem | UploaderFileListItem[]) {
  const file = Array.isArray(item) ? item[0].file : item.file
  if (!file) return
  const body = new FormData()
  body.append('file', file)
  try {
    const res = await http.post<never, { data: { url: string } }>('/api/v1/files/upload', body)
    url.value = res.data.url
    showToast('上传成功')
  } catch (error) {
    showToast((error as Error).message)
  }
}

async function onChunk(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const size = 512 * 1024
  const total = Math.ceil(file.size / size)
  const uploadId = `up${Date.now()}`
  try {
    for (let index = 0; index < total; index += 1) {
      const body = new FormData()
      body.append('upload_id', uploadId)
      body.append('index', String(index))
      body.append('total', String(total))
      body.append('file', file.slice(index * size, (index + 1) * size), file.name)
      await http.post('/api/v1/files/chunk', body)
      chunkText.value = `已上传 ${index + 1}/${total}`
    }
    const res = await http.post<never, { data: { url: string } }>('/api/v1/files/chunk/complete', {
      upload_id: uploadId,
      name: file.name,
      total,
    })
    url.value = res.data.url
    chunkText.value = '分片合并完成'
  } catch (error) {
    chunkText.value = '分片上传失败'
    showToast((error as Error).message)
  }
}
</script>

<style scoped>
.preview img,
:deep(.van-uploader__preview-image) {
  width: 100%;
  border-radius: 12px;
}

.preview img { display: block; margin-top: 12px; }

.chunk { display: grid; gap: 12px; justify-items: start; }

.chunk strong { font-size: 16px; }
</style>
