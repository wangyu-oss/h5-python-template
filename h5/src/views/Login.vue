<template>
  <div class="login">
    <div class="atmosphere" aria-hidden="true">
      <span class="orb orb-a" />
      <span class="orb orb-b" />
      <span class="orb orb-c" />
    </div>
    <header class="brand" :class="{ compact: mode !== 'login' }">
      <h1 v-if="mode === 'login'">{{ t('login.title') }}</h1>
    </header>
    <section class="sheet">
      <div v-if="mode !== 'login'" class="sheet-head">
        <button type="button" class="back" @click="mode = 'login'">{{ t('login.back') }}</button>
        <h2>{{ heading }}</h2>
      </div>
      <van-tabs v-if="mode === 'login'" v-model:active="tab" class="tabs" animated>
        <van-tab :title="t('login.passwordTab')">
          <van-form class="form" @submit="onPassword">
            <van-field v-model="form.username" name="username" :label="t('login.username')" :placeholder="t('login.username')" :rules="[{ required: true, message: t('login.username') }]" />
            <van-field v-model="form.password" type="password" name="password" :label="t('login.password')" :placeholder="t('login.passwordPh')" :rules="[{ required: true, message: t('login.password') }]" />
            <van-checkbox v-model="agreed" class="agree" shape="square">{{ t('login.agreement') }}</van-checkbox>
            <div class="actions">
              <van-button round block type="primary" native-type="submit" :loading="submitting">{{ t('login.submit') }}</van-button>
            </div>
          </van-form>
        </van-tab>
        <van-tab :title="t('login.sms')">
          <van-form class="form" @submit="onSms">
            <van-field v-model="sms.phone" :label="t('login.phone')" placeholder="13800138000" :rules="[{ validator: phoneOk, message: t('login.phone') }]" />
            <van-field v-model="sms.code" :label="t('login.code')" :placeholder="t('login.codePh')" :rules="[{ required: true, message: t('login.code') }]">
              <template #button>
                <van-button size="small" round type="primary" plain native-type="button" :disabled="cooldown > 0" @click="sendCode('login')">
                  {{ cooldown > 0 ? `${cooldown}s` : t('login.send') }}
                </van-button>
              </template>
            </van-field>
            <div class="actions">
              <van-button round block type="primary" native-type="submit">{{ t('login.sms') }}</van-button>
            </div>
          </van-form>
        </van-tab>
      </van-tabs>

      <van-form v-else-if="mode === 'register'" class="form" @submit="onRegister">
        <van-field v-model="registerForm.username" :label="t('login.username')" :placeholder="t('login.usernamePh')" :rules="[{ validator: nameOk, message: t('login.usernamePh') }]" />
        <van-field v-model="registerForm.phone" :label="t('login.phone')" placeholder="13800138000" />
        <van-field v-model="registerForm.password" type="password" :label="t('login.password')" :placeholder="t('login.passwordPh')" :rules="[{ validator: passwordOk, message: t('login.passwordPh') }]" />
        <van-checkbox v-model="agreed" class="agree" shape="square">{{ t('login.agreement') }}</van-checkbox>
        <div class="actions">
          <van-button round block type="primary" native-type="submit" :loading="submitting">{{ t('login.registerSubmit') }}</van-button>
        </div>
      </van-form>

      <van-form v-else class="form" @submit="onReset">
        <van-field v-model="resetForm.phone" :label="t('login.phone')" placeholder="13800138000" :rules="[{ validator: phoneOk, message: t('login.phone') }]" />
        <van-field v-model="resetForm.code" :label="t('login.code')" :placeholder="t('login.codePh')" :rules="[{ required: true, message: t('login.code') }]">
          <template #button>
            <van-button size="small" round type="primary" plain native-type="button" :disabled="cooldown > 0" @click="sendCode('reset')">
              {{ cooldown > 0 ? `${cooldown}s` : t('login.send') }}
            </van-button>
          </template>
        </van-field>
        <van-field v-model="resetForm.password" type="password" :label="t('login.newPassword')" :placeholder="t('login.passwordPh')" :rules="[{ validator: passwordOk, message: t('login.passwordPh') }]" />
        <div class="actions">
          <van-button round block type="primary" native-type="submit" :loading="submitting">{{ t('login.resetSubmit') }}</van-button>
        </div>
      </van-form>

      <div v-if="mode === 'login'" class="links">
        <button type="button" @click="mode = 'register'">{{ t('login.register') }}</button>
        <button type="button" @click="mode = 'reset'">{{ t('login.forgot') }}</button>
      </div>

      <template v-if="mode === 'login'">
        <div class="split"><span>{{ t('login.other') }}</span></div>
        <div class="alt">
          <button type="button" @click="onGuest">
            <van-icon name="user-circle-o" />
            <span>{{ t('login.guest') }}</span>
          </button>
          <button type="button" @click="onWechat">
            <van-icon name="wechat" />
            <span>{{ t('login.wechat') }}</span>
          </button>
          <button type="button" @click="onOneClick">
            <van-icon name="phone-circle-o" />
            <span>{{ t('login.oneclick') }}</span>
          </button>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'
import { detectEnv } from '@/utils/env'
import { localCache } from '@/utils/storage'
import { phone } from '@/utils/validate'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const user = useUserStore()
const tab = ref(0)
const mode = ref<'login' | 'register' | 'reset'>('login')
const agreed = ref(false)
const submitting = ref(false)
const cooldown = ref(0)
let cooldownTimer = 0
const devDefaults = import.meta.env.DEV
const form = reactive({
  username: localCache.get<string>('login-username') || (devDefaults ? 'admin' : ''),
  password: devDefaults ? '123456' : '',
})
const sms = reactive({ phone: devDefaults ? '13800138000' : '', code: '' })
const registerForm = reactive({ username: '', phone: '', password: '' })
const resetForm = reactive({ phone: '', code: '', password: '' })
const heading = computed(() => {
  if (mode.value === 'register') return t('login.register')
  if (mode.value === 'reset') return t('login.forgot')
  return t('login.title')
})

function phoneOk(value: string) {
  return phone(value).ok
}

function nameOk(value: string) {
  return String(value || '').trim().length >= 3
}

function passwordOk(value: string) {
  const text = String(value || '')
  return text.length >= 8 && /[A-Za-z]/.test(text) && /\d/.test(text)
}

function goHome() {
  const redirect = String(route.query.redirect || '/home')
  router.replace(redirect.startsWith('/') ? redirect : '/home')
}

function toastError(error: unknown) {
  showToast((error as Error).message)
}

function startCooldown() {
  cooldown.value = 60
  window.clearInterval(cooldownTimer)
  cooldownTimer = window.setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) window.clearInterval(cooldownTimer)
  }, 1000)
}

async function onPassword() {
  if (!agreed.value) {
    showToast(t('login.agreeFirst'))
    return
  }
  submitting.value = true
  try {
    localCache.set('login-username', form.username)
    await user.login({ username: form.username, password: form.password })
    goHome()
  } catch (error) {
    toastError(error)
  } finally {
    submitting.value = false
  }
}

async function sendCode(purpose: 'login' | 'reset') {
  const phoneNumber = purpose === 'reset' ? resetForm.phone : sms.phone
  if (!phone(phoneNumber).ok) {
    showToast(t('login.phone'))
    return
  }
  try {
    const res = await http.post<never, { data: { debug_code?: string } }>('/api/v1/auth/sms/send', { phone: phoneNumber, purpose })
    if (purpose === 'reset') resetForm.code = res.data.debug_code || resetForm.code
    else if (res.data.debug_code) sms.code = res.data.debug_code
    startCooldown()
    showToast(res.data.debug_code ? t('login.debugCode', { code: res.data.debug_code }) : t('login.sent'))
  } catch (error) {
    toastError(error)
  }
}

async function onSms() {
  try {
    await user.smsLogin(sms)
    goHome()
  } catch (error) {
    toastError(error)
  }
}

async function onRegister() {
  if (!agreed.value) {
    showToast(t('login.agreeFirst'))
    return
  }
  submitting.value = true
  try {
    await user.register(registerForm)
    goHome()
  } catch (error) {
    toastError(error)
  } finally {
    submitting.value = false
  }
}

async function onReset() {
  submitting.value = true
  try {
    await http.post('/api/v1/auth/password/reset', { ...resetForm })
    showToast(t('login.resetSubmit'))
    mode.value = 'login'
    form.password = ''
  } catch (error) {
    toastError(error)
  } finally {
    submitting.value = false
  }
}

async function onGuest() {
  try {
    const device = localCache.get<string>('device-id') || `d${Date.now()}`
    localCache.set('device-id', device)
    await user.guest(device)
    goHome()
  } catch (error) {
    toastError(error)
  }
}

async function onWechat() {
  if (detectEnv() !== 'wechat') {
    showToast(t('login.wechatOnly'))
    return
  }
  try {
    const res = await http.post<never, { data: any }>('/api/v1/auth/wechat/official', { code: 'mock-openid' })
    user.apply(res.data)
    goHome()
  } catch (error) {
    toastError(error)
  }
}

async function onOneClick() {
  try {
    await http.post('/api/v1/auth/oneclick', {})
    showToast(t('login.oneclick'))
  } catch (error) {
    toastError(error)
  }
}

onUnmounted(() => window.clearInterval(cooldownTimer))
</script>

<style scoped>
.login {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
  min-height: 0;
  overflow: auto;
  scrollbar-width: thin;
  color: #fff;
  background:
    radial-gradient(90% 50% at 100% 0%, rgba(56, 189, 248, 0.35), transparent 55%),
    radial-gradient(70% 40% at 0% 20%, rgba(99, 102, 241, 0.38), transparent 60%),
    linear-gradient(180deg, #10203d 0%, #071024 100%);
}

.atmosphere {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(8px);
}

.orb-a {
  top: -80px;
  right: -40px;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.7), transparent 68%);
}

.orb-b {
  top: 120px;
  left: -90px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.55), transparent 70%);
}

.orb-c {
  top: 42%;
  right: 18%;
  width: 90px;
  height: 90px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.45), transparent 70%);
  filter: blur(2px);
}

.brand {
  position: relative;
  z-index: 1;
  padding: 28px 24px 22px;
}

.brand.compact {
  padding-bottom: 18px;
}

h1 {
  margin: 8px 0 0;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.6px;
}

.sheet {
  position: relative;
  z-index: 1;
  padding: 8px 16px calc(18px + env(safe-area-inset-bottom));
  color: #0f172a;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 28px 28px 0 0;
  box-shadow: 0 -18px 50px rgba(7, 16, 36, 0.28);
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 4px 4px;
}

.sheet-head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.sheet-head .back {
  width: auto;
  margin: 0;
}

.tabs :deep(.van-tabs__nav) {
  background: transparent;
}

.tabs :deep(.van-tab) {
  color: #64748b;
  font-weight: 600;
}

.tabs :deep(.van-tab--active) {
  color: #0f172a;
}

.tabs :deep(.van-tabs__line) {
  width: 22px;
  height: 3px;
  background: linear-gradient(90deg, #2563eb, #06b6d4);
  border-radius: 99px;
}

.form {
  padding-top: 8px;
}

.form :deep(.van-cell) {
  margin-bottom: 10px;
  overflow: hidden;
  background: #f4f7fb;
  border-radius: 14px;
}

.form :deep(.van-cell::after) {
  display: none;
}

.agree {
  margin: 4px 4px 0;
  color: #475569;
  font-size: 13px;
}

.actions {
  margin-top: 16px;
}

.actions :deep(.van-button--primary) {
  height: 46px;
  font-weight: 700;
  background: linear-gradient(135deg, #1d4ed8, #0891b2);
  border: 0;
  box-shadow: 0 10px 20px rgba(29, 78, 216, 0.28);
}

.links,
.back {
  display: flex;
  justify-content: space-between;
  margin-top: 14px;
  padding: 0;
  color: #1d4ed8;
  font-size: 13px;
  background: transparent;
  border: 0;
}

.links button {
  padding: 4px 2px;
  color: inherit;
  font-size: 13px;
  line-height: 1.4;
  background: transparent;
  border: 0;
}

.back {
  width: 100%;
}

.split {
  display: flex;
  align-items: center;
  margin: 18px 4px 12px;
  color: #94a3b8;
  font-size: 12px;
}

.split::before,
.split::after {
  flex: 1;
  height: 1px;
  content: "";
  background: #e2e8f0;
}

.split span {
  padding: 0 10px;
}

.alt {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.alt button {
  display: grid;
  gap: 8px;
  justify-items: center;
  padding: 12px 6px 10px;
  color: #0f172a;
  font-size: 12px;
  background: #f8fafc;
  border: 1px solid #e8eef6;
  border-radius: 16px;
}

.alt :deep(.van-icon) {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #1d4ed8;
  font-size: 18px;
  background: #e8f1ff;
  border-radius: 12px;
}

:global(html.dark) .sheet {
  color: #f8fafc;
  background: rgba(15, 23, 42, 0.94);
}

:global(html.dark) .tabs :deep(.van-tab--active),
:global(html.dark) .alt button,
:global(html.dark) .links,
:global(html.dark) .back {
  color: #e2e8f0;
}

:global(html.dark) .form :deep(.van-cell),
:global(html.dark) .alt button {
  background: #1e293b;
  border-color: rgba(255, 255, 255, 0.06);
}

:global(html.dark) .agree {
  color: #cbd5e1;
}
</style>
