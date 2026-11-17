<template>
  <div class="page mine">
    <section class="profile">
      <div class="avatar">{{ initial }}</div>
      <div class="who">
        <strong>{{ user.account?.display_name || t('mine.guest') }}</strong>
        <p>{{ accountLine }}</p>
      </div>
    </section>

    <p class="group-title">{{ t('mine.preference') }}</p>
    <van-cell-group inset>
      <van-cell :title="t('mine.theme')" :value="themeLabel" is-link @click="openTheme" />
      <van-cell :title="t('mine.language')" :value="localeLabel" is-link @click="showLanguage = true" />
      <van-cell :title="t('mine.portrait')" center>
        <template #right-icon>
          <van-switch :model-value="portraitOn" size="20" @update:model-value="onPortrait" />
        </template>
      </van-cell>
    </van-cell-group>

    <p class="group-title">{{ t('mine.tools') }}</p>
    <div class="tools">
      <button v-for="item in tools" :key="item.to" type="button" @click="router.push(item.to)">
        <van-icon :name="item.icon" />
        <span>{{ item.title }}</span>
      </button>
    </div>

    <p class="group-title">{{ t('mine.account') }}</p>
    <van-cell-group inset>
      <van-cell :title="t('mine.realname')" is-link @click="showRealname = true" />
      <van-cell :title="t('mine.password')" is-link @click="showPassword = true" />
      <van-cell :title="t('mine.agreement')" is-link @click="showAgreement = true" />
      <van-cell :title="t('mine.cache')" is-link @click="clearCache" />
    </van-cell-group>

    <button type="button" class="logout" @click="onLogout">{{ t('mine.logout') }}</button>
    <p class="version">{{ t('mine.version', { version: app.config.settings.app_version || '1.1.0' }) }}</p>

    <van-action-sheet
      v-model:show="showTheme"
      :actions="themeActions"
      :cancel-text="t('mine.cancel')"
      :description="t('mine.chooseTheme')"
      close-on-click-action
      @select="onTheme"
    />
    <van-action-sheet
      v-model:show="showLanguage"
      :actions="localeActions"
      :cancel-text="t('mine.cancel')"
      :description="t('mine.chooseLanguage')"
      close-on-click-action
      @select="onLocale"
    />

    <van-popup v-model:show="showPassword" round position="bottom" class="sheet">
      <h2>{{ t('mine.password') }}</h2>
      <p class="muted">{{ t('mine.passwordHint') }}</p>
      <van-field v-model="passwordForm.old_password" type="password" :label="t('mine.oldPassword')" :placeholder="t('mine.oldPassword')" />
      <van-field v-model="passwordForm.password" type="password" :label="t('mine.newPassword')" :placeholder="t('mine.passwordHint')" />
      <div class="sheet-actions">
        <van-button round block @click="showPassword = false">{{ t('mine.cancel') }}</van-button>
        <van-button round block type="primary" :loading="saving" @click="changePassword">{{ t('mine.save') }}</van-button>
      </div>
    </van-popup>

    <van-popup v-model:show="showRealname" round position="bottom" class="sheet">
      <h2>{{ t('mine.realname') }}</h2>
      <van-field v-model="realnameForm.real_name" :label="t('mine.realNameLabel')" :placeholder="t('mine.realNameLabel')" />
      <van-field v-model="realnameForm.id_card" :label="t('mine.idCard')" :placeholder="t('mine.idCard')" />
      <div class="sheet-actions">
        <van-button round block @click="showRealname = false">{{ t('mine.cancel') }}</van-button>
        <van-button round block type="primary" :loading="saving" @click="realname">{{ t('mine.save') }}</van-button>
      </div>
    </van-popup>

    <van-popup v-model:show="showAgreement" round position="bottom" class="sheet">
      <h2>{{ t('mine.agreement') }}</h2>
      <p class="agreement">{{ t('mine.agreementBody') }}</p>
      <van-button round block type="primary" @click="showAgreement = false">{{ t('mine.confirm') }}</van-button>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import http from '@/api/http'
import { clearBusinessCache } from '@/utils/storage'

const { t } = useI18n()
const app = useAppStore()
const user = useUserStore()
const router = useRouter()
const showTheme = ref(false)
const showLanguage = ref(false)
const showPassword = ref(false)
const showRealname = ref(false)
const showAgreement = ref(false)
const saving = ref(false)
const portraitOn = ref(false)
const passwordForm = reactive({ old_password: '', password: '' })
const realnameForm = reactive({ real_name: '', id_card: '' })

const tools = computed(() => [
  { title: t('mine.form'), to: '/demo/form', icon: 'edit' },
  { title: t('mine.upload'), to: '/demo/upload', icon: 'upgrade' },
  { title: t('mine.media'), to: '/demo/media', icon: 'photo-o' },
  { title: t('mine.share'), to: '/demo/share', icon: 'share-o' },
  { title: t('mine.toolkit'), to: '/demo/tools', icon: 'apps-o' },
  { title: t('mine.checkin'), to: '/plugin/checkin', icon: 'calendar-o' },
  { title: t('mine.survey'), to: '/plugin/survey', icon: 'records' },
])

const themeActions = computed(() => [
  { name: t('mine.light'), value: 'light' },
  { name: t('mine.dark'), value: 'dark' },
])

const localeActions = computed(() => [
  { name: t('mine.localeZh'), value: 'zh-CN' },
  { name: t('mine.localeTw'), value: 'zh-TW' },
  { name: t('mine.localeEn'), value: 'en' },
])

const themeLabel = computed(() => (app.theme === 'dark' ? t('mine.dark') : t('mine.light')))
const localeLabel = computed(() => localeActions.value.find((item) => item.value === app.locale)?.name || app.locale)
const initial = computed(() => (user.account?.display_name || t('mine.guest')).slice(0, 1))
const accountLine = computed(() => maskAccount(user.account?.phone || user.account?.username || ''))

function maskAccount(value: string) {
  if (/^1\d{10}$/.test(value)) return `${value.slice(0, 3)}****${value.slice(7)}`
  return value
}

function openTheme() {
  if (app.config.settings.feature_dark === 'no') {
    showToast(t('mine.darkOff'))
    return
  }
  showTheme.value = true
}

function onTheme(action: { value?: string }) {
  if (action.value !== 'light' && action.value !== 'dark') return
  app.applyTheme(action.value, { user: true })
}

function onLocale(action: { value?: string }) {
  if (!action.value) return
  app.setLocale(action.value)
}

async function onPortrait(next: boolean) {
  const orientation = screen.orientation as ScreenOrientation & { lock?: (mode: string) => Promise<void>; unlock?: () => void }
  if (!next) {
    orientation.unlock?.()
    portraitOn.value = false
    return
  }
  if (!orientation?.lock) {
    portraitOn.value = false
    showToast(t('mine.portraitUnsupported'))
    return
  }
  try {
    await orientation.lock('portrait')
    portraitOn.value = true
    showToast(t('mine.portraitOk'))
  } catch {
    portraitOn.value = false
    showToast(t('mine.portraitFail'))
  }
}

function passwordOk(value: string) {
  return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value)
}

async function realname() {
  if (!realnameForm.real_name.trim()) {
    showToast(t('mine.nameRequired'))
    return
  }
  saving.value = true
  try {
    await http.post('/api/v1/auth/realname', { ...realnameForm })
    showToast(t('mine.realnameOk'))
    showRealname.value = false
  } catch (error) {
    showToast((error as Error).message)
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passwordOk(passwordForm.password)) {
    showToast(t('mine.passwordInvalid'))
    return
  }
  saving.value = true
  try {
    await http.post('/api/v1/auth/password', { ...passwordForm })
    showToast(t('mine.passwordOk'))
    showPassword.value = false
    passwordForm.old_password = ''
    passwordForm.password = ''
  } catch (error) {
    showToast((error as Error).message)
  } finally {
    saving.value = false
  }
}

async function clearCache() {
  try {
    await showConfirmDialog({ title: t('mine.cache'), message: t('mine.cacheConfirm'), confirmButtonText: t('mine.confirm'), cancelButtonText: t('mine.cancel') })
  } catch {
    return
  }
  clearBusinessCache()
  showToast(t('mine.cacheOk'))
  await user.logout()
  router.replace('/login')
}

async function onLogout() {
  try {
    await showConfirmDialog({ title: t('mine.logout'), message: t('mine.logoutConfirm'), confirmButtonText: t('mine.confirm'), cancelButtonText: t('mine.cancel') })
  } catch {
    return
  }
  await user.logout()
  router.replace('/login')
}
</script>

<style scoped>
.profile {
  display: flex;
  gap: 14px;
  align-items: center;
  margin: -14px -14px 8px;
  padding: 28px 18px 22px;
  color: #fff;
  background:
    radial-gradient(80% 120% at 100% 0%, rgba(125, 211, 252, 0.28), transparent 50%),
    linear-gradient(145deg, #0f172a, #1d4ed8);
  border-radius: 0 0 28px 28px;
}

.avatar {
  display: grid;
  flex: none;
  width: 56px;
  height: 56px;
  place-items: center;
  font-size: 22px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 18px;
}

.who {
  min-width: 0;
}

.who strong,
.who p {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile p {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.85;
}

.group-title {
  margin: 16px 8px 8px;
  color: var(--app-muted);
  font-size: 13px;
}

.tools {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 4px;
  padding: 12px 6px;
  background: var(--app-card);
  border: 1px solid var(--app-line);
  border-radius: var(--app-radius);
  box-shadow: var(--app-shadow);
}

.tools button {
  display: grid;
  gap: 6px;
  justify-items: center;
  min-height: 72px;
  padding: 8px 2px;
  color: var(--app-text);
  font-size: 12px;
  line-height: 1.3;
  text-align: center;
  background: transparent;
  border: 0;
}

.tools :deep(.van-icon) {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  color: var(--app-primary);
  font-size: 18px;
  background: color-mix(in srgb, var(--app-primary) 12%, transparent);
  border-radius: 12px;
}

.logout {
  width: 100%;
  height: 46px;
  margin-top: 16px;
  color: #b42318;
  font-size: 15px;
  font-weight: 650;
  background: var(--app-card);
  border: 1px solid var(--app-line);
  border-radius: var(--app-radius);
  box-shadow: var(--app-shadow);
}

.version {
  margin: 12px 0 0;
  color: var(--app-muted);
  font-size: 12px;
  text-align: center;
}

.sheet {
  padding: 18px 16px calc(18px + env(safe-area-inset-bottom));
}

.sheet h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.sheet .muted,
.agreement {
  margin: 0 0 12px;
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.6;
}

.sheet :deep(.van-cell) {
  margin-bottom: 10px;
  background: var(--app-bg);
  border-radius: 12px;
}

.sheet :deep(.van-cell::after) {
  display: none;
}

.sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 10px;
  margin-top: 8px;
}
</style>
