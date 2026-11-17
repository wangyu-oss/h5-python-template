<template>
  <div class="page">
    <van-pull-refresh v-model="refreshing" @refresh="refresh">
      <van-list v-model:loading="loading" :finished="finished" :finished-text="items.length && !failed ? t('common.noMore') : ''" @load="load">
        <router-link v-for="item in items" :key="item.id" class="card item" :to="`/notices/${item.id}`">
          <div class="row head">
            <strong>{{ item.title }}</strong>
            <span v-if="item.pinned" class="pin">{{ t('notice.pinned') }}</span>
          </div>
          <p v-if="item.summary" class="summary">{{ item.summary }}</p>
          <p class="muted">{{ item.created_at }}</p>
        </router-link>
        <van-empty v-if="!loading && finished && !failed && !items.length" :description="t('notice.empty')" />
        <div v-if="failed" class="card fail">
          <p>{{ errorText || t('common.failed') }}</p>
          <van-button size="small" type="primary" round @click="retry">{{ t('common.retry') }}</van-button>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import http, { isCanceled } from '@/api/http'

defineOptions({ name: 'NoticeList' })

interface NoticeItem {
  id: number
  title: string
  summary?: string
  created_at?: string
  pinned?: boolean
}

const { t } = useI18n()
const items = ref<NoticeItem[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const failed = ref(false)
const errorText = ref('')
const page = ref(1)
let epoch = 0

async function load() {
  const ticket = epoch
  failed.value = false
  try {
    const res = await http.get<never, { data: { items: NoticeItem[]; total: number } }>('/api/v1/announcements', {
      params: { page: page.value, page_size: 10 },
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
    if (ticket === epoch) {
      loading.value = false
      refreshing.value = false
    }
  }
}

function refresh() {
  epoch += 1
  items.value = []
  page.value = 1
  finished.value = false
  failed.value = false
  refreshing.value = true
  load()
}

function retry() {
  failed.value = false
  finished.value = false
  loading.value = true
  load()
}
</script>

<style scoped>
.item {
  display: block;
  color: inherit;
  text-decoration: none;
}

.head {
  justify-content: space-between;
}

.summary {
  margin: 8px 0 0;
  color: var(--app-text);
  font-size: 13px;
  line-height: 1.5;
}

.pin {
  padding: 2px 8px;
  color: #1d4ed8;
  font-size: 12px;
  background: #dbeafe;
  border-radius: 99px;
}

:global(html.dark) .pin {
  color: #bfdbfe;
  background: rgba(37, 99, 235, 0.25);
}
</style>
