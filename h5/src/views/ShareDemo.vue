<template>
  <div class="page">
    <div ref="poster" class="card poster">
      <div class="banner" :style="{ background: 'var(--app-primary)' }">{{ title }}</div>
      <p>{{ desc }}</p>
      <div class="muted">{{ link }}</div>
    </div>
    <div class="actions">
      <van-button block type="primary" @click="savePoster">生成海报并保存</van-button>
      <van-button block plain type="primary" @click="share">调用微信分享</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { showToast } from 'vant'
import { useAppStore } from '@/stores/app'
import { track } from '@/utils/track'
import { wechatShare } from '@/utils/wechat'

const app = useAppStore()
const poster = ref<HTMLElement>()
const title = computed(() => app.config.settings.h5_title || 'H5 基座')
const desc = computed(() => app.config.settings.h5_slogan || '分享描述')
const link = computed(() => location.origin + '/home')

async function savePoster() {
  if (!poster.value) return
  const { default: html2canvas } = await import('html2canvas')
  const canvas = await html2canvas(poster.value)
  const anchor = document.createElement('a')
  anchor.href = canvas.toDataURL('image/png')
  anchor.download = 'poster.png'
  anchor.click()
  track('share', { channel: 'poster' })
  showToast('已生成图片，可保存到相册')
}

async function share() {
  const result = await wechatShare({ title: title.value, desc: desc.value, link: link.value, imgUrl: '' })
  track('share', { channel: 'wechat', configured: result.configured })
  showToast(result.configured ? '已设置微信分享' : result.reason)
}
</script>

<style scoped>
.poster { overflow: hidden; }
.poster p { margin: 14px 0 8px; font-size: 15px; line-height: 1.5; }
.poster .muted { overflow-wrap: anywhere; }
.actions { display: grid; gap: 10px; }
</style>
