<template>
  <div class="layout">
    <van-nav-bar v-if="!tab" :title="title" left-arrow fixed placeholder @click-left="router.back()" />
    <div class="stage" :class="{ 'with-tab': tab }">
      <router-view v-slot="{ Component }">
        <transition name="fade">
          <keep-alive :include="['HomePage', 'NoticeList', 'MessageList']">
            <component :is="Component" />
          </keep-alive>
        </transition>
      </router-view>
    </div>
    <van-tabbar v-if="tab" route safe-area-inset-bottom class="dock">
      <van-tabbar-item to="/home" icon="home-o">{{ t('tab.home') }}</van-tabbar-item>
      <van-tabbar-item to="/notices" icon="notes-o">{{ t('tab.notice') }}</van-tabbar-item>
      <van-tabbar-item to="/messages" icon="chat-o" :badge="app.unread || ''">{{ t('tab.message') }}</van-tabbar-item>
      <van-tabbar-item to="/mine" icon="user-o">{{ t('tab.mine') }}</van-tabbar-item>
    </van-tabbar>
    <div v-if="showWatermark" class="watermark" :style="watermarkStyle" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const app = useAppStore()
const user = useUserStore()
const tab = computed(() => Boolean(route.meta.tab))
const title = computed(() => {
  const titleKey = typeof route.meta.titleKey === 'string' ? route.meta.titleKey : ''
  if (titleKey) return t(titleKey)
  return String(route.meta.title || '')
})
const showWatermark = computed(() => app.config.settings.h5_watermark === 'yes')
const watermarkStyle = computed(() => {
  const text = escapeXml(user.account?.display_name || 'H5')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="160" height="100"><text x="10" y="60" fill="rgba(150,150,150,0.25)" transform="rotate(-20 80 50)" font-size="14">${text}</text></svg>`
  return { backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(svg)}")` }
})

function escapeXml(value: string) {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char] || char)
}

let timer = 0

function pullUnread() {
  if (document.hidden || !user.token) return
  app.loadUnread()
}

function onVisibility() {
  if (!document.hidden) pullUnread()
}

onMounted(() => {
  app.loadConfig().catch(() => undefined)
  pullUnread()
  timer = window.setInterval(pullUnread, 20000)
  document.addEventListener('visibilitychange', onVisibility)
})

onUnmounted(() => {
  window.clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisibility)
})
</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.dock {
  overflow: hidden;
  border-radius: 18px 18px 0 0;
}
</style>
