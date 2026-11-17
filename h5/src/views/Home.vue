<template>
  <div class="page home">
    <section class="hero">
      <div>
        <p>{{ t('home.hello', { name: user.account?.display_name || t('home.guest') }) }}</p>
        <h1>{{ title }}</h1>
      </div>
      <div class="badge">{{ (user.account?.display_name || t('home.guest')).slice(0, 1) }}</div>
    </section>
    <div class="quick">
      <router-link to="/notices">
        <span class="ico notice"><van-icon name="notes-o" /></span>
        <span>{{ t('home.notice') }}</span>
      </router-link>
      <router-link to="/messages">
        <span class="ico message"><van-icon name="chat-o" /></span>
        <span>{{ t('home.message') }}</span>
      </router-link>
      <router-link to="/plugin/checkin">
        <span class="ico checkin"><van-icon name="calendar-o" /></span>
        <span>{{ t('home.checkin') }}</span>
      </router-link>
      <router-link to="/mine">
        <span class="ico mine"><van-icon name="user-o" /></span>
        <span>{{ t('home.mine') }}</span>
      </router-link>
    </div>
    <div v-if="!app.configReady" class="card loading">{{ t('common.loading') }}</div>
    <div v-else-if="app.configError" class="card fail">
      <p>{{ app.configError }}</p>
      <van-button size="small" type="primary" round @click="reload">{{ t('common.retry') }}</van-button>
    </div>
    <template v-else>
      <van-swipe v-if="banners.length" class="swipe" :autoplay="3000" indicator-color="white">
        <van-swipe-item v-for="item in banners" :key="item.id" @click="openBanner(item)">
          <div class="banner" :style="{ background: item.color || 'linear-gradient(135deg, #1d4ed8, #0891b2)' }">
            <em>{{ t('home.recommend') }}</em>
            <strong>{{ item.title }}</strong>
          </div>
        </van-swipe-item>
      </van-swipe>
      <section class="card feed">
        <div class="row head">
          <strong>{{ t('home.latest') }}</strong>
          <router-link to="/notices">{{ t('common.more') }}</router-link>
        </div>
        <router-link v-for="item in notices" :key="item.id" class="notice-row" :to="`/notices/${item.id}`">
          <span class="mark" />
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
          </div>
          <van-icon name="arrow" />
        </router-link>
        <van-empty v-if="!notices.length" :description="t('notice.empty')" />
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

defineOptions({ name: 'HomePage' })

const { t } = useI18n()
const app = useAppStore()
const user = useUserStore()
const router = useRouter()
const title = computed(() => app.config.settings.h5_title || 'H5')
const banners = computed(() => app.config.banners || [])
const notices = computed(() => app.config.notices || [])

function openBanner(item: { link?: string; jump_type?: string }) {
  if (!item.link || item.jump_type === 'none') return
  if (item.jump_type === 'url' && /^https?:/i.test(item.link)) {
    window.location.href = item.link
    return
  }
  router.push(item.link)
}

function reload() {
  app.loadConfig().catch(() => undefined)
}
</script>

<style scoped>
.hero {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
  margin: -14px -14px 16px;
  padding: 28px 18px 34px;
  color: #fff;
  background:
    radial-gradient(80% 120% at 100% 0%, rgba(125, 211, 252, 0.45), transparent 55%),
    linear-gradient(145deg, #0f172a 0%, #1d4ed8 62%, #0891b2 100%);
  border-radius: 0 0 28px 28px;
}

.hero p {
  margin: 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: 13px;
}

.hero h1 {
  margin: 6px 0 0;
  font-size: 28px;
  letter-spacing: -0.4px;
}

.badge {
  display: grid;
  flex: none;
  width: 46px;
  height: 46px;
  place-items: center;
  font-size: 18px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 16px;
}

.quick {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: -28px;
  margin-bottom: 14px;
}

.quick a {
  display: grid;
  gap: 8px;
  justify-items: center;
  padding: 12px 0 10px;
  color: var(--app-text);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  background: var(--app-card);
  border: 1px solid var(--app-line);
  border-radius: 18px;
  box-shadow: var(--app-shadow);
}

.ico {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  font-size: 18px;
  border-radius: 12px;
}

.notice { color: #1d4ed8; background: #dbeafe; }
.message { color: #0f766e; background: #ccfbf1; }
.checkin { color: #c2410c; background: #ffedd5; }
.mine { color: #6d28d9; background: #ede9fe; }

.swipe {
  margin-bottom: 12px;
  overflow: hidden;
  border-radius: 18px;
}

.banner em {
  position: relative;
  z-index: 1;
  margin-bottom: 6px;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
  letter-spacing: 1px;
  opacity: 0.85;
}

.banner strong {
  position: relative;
  z-index: 1;
}

.loading {
  color: var(--app-muted);
}

.feed {
  padding-bottom: 6px;
}

.head {
  justify-content: space-between;
  margin-bottom: 8px;
}

.head strong {
  font-size: 16px;
}

.head a {
  color: var(--app-primary);
  font-size: 13px;
  text-decoration: none;
}

.notice-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 2px;
  color: inherit;
  text-decoration: none;
  border-top: 1px solid var(--app-line);
}

.mark {
  flex: none;
  width: 8px;
  height: 8px;
  background: linear-gradient(180deg, #2563eb, #06b6d4);
  border-radius: 50%;
}

.notice-row strong {
  display: block;
  font-size: 14px;
}

.notice-row p {
  display: -webkit-box;
  margin: 4px 0 0;
  overflow: hidden;
  color: var(--app-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notice-row :deep(.van-icon) {
  margin-left: auto;
  color: #94a3b8;
}
</style>
