<template>
  <div class="page">
    <div class="card toolbar">
      <van-tabs v-model:active="category" shrink @change="reload">
        <van-tab :title="t('message.all')" name="" />
        <van-tab :title="t('message.system')" name="system" />
        <van-tab :title="t('message.security')" name="security" />
      </van-tabs>
      <van-button size="small" round plain type="primary" @click="readAll">{{ t('message.readAll') }}</van-button>
    </div>
    <van-list v-model:loading="loading" :finished="finished" :finished-text="items.length && !failed ? t('common.noMore') : ''" @load="load">
      <button v-for="item in items" :key="item.id" type="button" class="card msg" @click="open(item)">
        <span v-if="!item.is_read" class="dot" />
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.content }}</p>
        </div>
        <em v-if="!item.is_read">{{ t('message.unread') }}</em>
      </button>
      <van-empty v-if="!loading && finished && !failed && !items.length" :description="t('message.empty')" />
      <div v-if="failed" class="card fail">
        <p>{{ errorText || t('common.failed') }}</p>
        <van-button size="small" type="primary" round @click="retry">{{ t('common.retry') }}</van-button>
      </div>
    </van-list>
    <van-popup v-model:show="showDetail" position="bottom" round class="sheet">
      <strong>{{ active?.title }}</strong>
      <p>{{ active?.content }}</p>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import http, { isCanceled } from '@/api/http'
import { useAppStore } from '@/stores/app'

defineOptions({ name: 'MessageList' })

interface MessageItem {
  id: number
  title: string
  content: string
  is_read: boolean
}

const { t } = useI18n()
const app = useAppStore()
const items = ref<MessageItem[]>([])
const category = ref('')
const loading = ref(false)
const finished = ref(false)
const failed = ref(false)
const errorText = ref('')
const page = ref(1)
const active = ref<MessageItem | null>(null)
const showDetail = computed({
  get: () => Boolean(active.value),
  set: (value: boolean) => {
    if (!value) active.value = null
  },
})
let epoch = 0

async function load() {
  const ticket = epoch
  const currentCategory = category.value
  failed.value = false
  try {
    const res = await http.get<never, { data: { items: MessageItem[]; total: number } }>('/api/v1/messages', {
      params: { category: currentCategory, page: page.value, page_size: 10 },
    })
    if (ticket !== epoch) return
    items.value.push(...res.data.items)
    if (items.value.length >= res.data.total) finished.value = true
    else page.value += 1
  } catch (error) {
    if (isCanceled(error) || ticket !== epoch) return
    failed.value = true
    finished.value = true
    errorText.value = (error as Error).message
  } finally {
    if (ticket === epoch) loading.value = false
  }
}

function reload() {
  epoch += 1
  items.value = []
  page.value = 1
  finished.value = false
  failed.value = false
  loading.value = true
  load()
}

function retry() {
  failed.value = false
  finished.value = false
  loading.value = true
  load()
}

function open(item: MessageItem) {
  active.value = item
  if (!item.is_read) read(item)
}

async function readAll() {
  try {
    await http.post('/api/v1/messages/read', {})
    items.value.forEach((item) => {
      item.is_read = true
    })
    app.loadUnread()
  } catch (error) {
    showToast((error as Error).message)
  }
}

async function read(item: MessageItem) {
  try {
    await http.post('/api/v1/messages/read', { id: item.id })
    item.is_read = true
    app.loadUnread()
  } catch (error) {
    showToast((error as Error).message)
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 4px 0;
}

.toolbar :deep(.van-tabs) {
  flex: 1;
  min-width: 0;
}

.toolbar :deep(.van-tabs__nav) {
  background: transparent;
}

.msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
  color: inherit;
  text-align: left;
  border: 1px solid var(--app-line);
}

.msg strong {
  display: block;
  font-size: 15px;
}

.msg p {
  display: -webkit-box;
  margin: 6px 0 0;
  overflow: hidden;
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.5;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.dot {
  flex: none;
  width: 8px;
  height: 8px;
  margin-top: 7px;
  background: #ef4444;
  border-radius: 50%;
}

.msg em {
  flex: none;
  color: #1d4ed8;
  font-size: 12px;
  font-style: normal;
}

.sheet {
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
}

.sheet p {
  color: var(--app-muted);
  line-height: 1.6;
}
</style>
