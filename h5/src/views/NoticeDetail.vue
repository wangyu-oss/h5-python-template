<template>
  <div class="page">
    <van-loading v-if="loading" class="wait" />
    <div v-else-if="errorText" class="card fail">
      <p>{{ errorText }}</p>
      <van-button size="small" type="primary" round @click="load">{{ t('common.retry') }}</van-button>
    </div>
    <article v-else class="card article">
      <p class="kicker">{{ t('notice.kicker') }}</p>
      <h1>{{ detail.title }}</h1>
      <time class="muted">{{ detail.created_at }}</time>
      <!-- eslint-disable-next-line vue/no-v-html -- content is sanitized with DOMPurify before render -->
      <div class="content" v-html="safeHtml"></div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DOMPurify from 'dompurify'
import http, { isCanceled } from '@/api/http'

const { t } = useI18n()
const route = useRoute()
const detail = ref<{ title?: string; content?: string; created_at?: string }>({})
const loading = ref(true)
const errorText = ref('')
const safeHtml = computed(() => DOMPurify.sanitize(detail.value.content || ''))

async function load() {
  loading.value = true
  errorText.value = ''
  try {
    const res = await http.get<never, { data: { title?: string; content?: string; created_at?: string } }>(`/api/v1/announcements/${route.params.id}`)
    detail.value = res.data || {}
    if (!res.data) errorText.value = t('notice.missing')
  } catch (error) {
    if (!isCanceled(error)) errorText.value = (error as Error).message || t('notice.missing')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.wait {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.kicker {
  margin: 0;
  color: var(--app-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

h1 {
  margin: 8px 0;
  font-size: 24px;
  line-height: 1.35;
}

.content {
  margin-top: 16px;
  font-size: 15px;
  line-height: 1.75;
}

.content :deep(img) {
  max-width: 100%;
  border-radius: 12px;
}

.content :deep(p) {
  margin: 0 0 12px;
}
</style>
