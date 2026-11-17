<template>
  <div class="page offline">
    <van-empty image="network" :description="t('common.offline')">
      <van-button type="primary" round @click="retry">{{ t('common.retry') }}</van-button>
    </van-empty>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

function retry() {
  if (!navigator.onLine) return
  const redirect = String(route.query.redirect || '/home')
  router.replace(redirect.startsWith('/') ? redirect : '/home')
}

onMounted(() => window.addEventListener('online', retry))
onUnmounted(() => window.removeEventListener('online', retry))
</script>
