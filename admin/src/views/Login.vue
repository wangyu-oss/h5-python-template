<template>
  <div class="login">
    <div class="veil" />
    <section class="panel">
      <div class="brand">
        <span class="mark">H5</span>
        <div>
          <h1>管理后台</h1>
        </div>
      </div>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="账号">
          <el-input v-model="username" size="large" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" size="large" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item v-if="showCaptcha" :label="question || '验证码'">
          <div class="captcha">
            <el-input v-model="answer" size="large" placeholder="填写计算结果" @keyup.enter="submit" />
            <button type="button" class="refresh" @click="loadCaptcha">换一题</button>
          </div>
        </el-form-item>
        <div class="row">
          <el-checkbox v-model="agree">我已阅读并同意用户协议</el-checkbox>
          <el-checkbox v-model="remember">记住账号</el-checkbox>
        </div>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">登录</el-button>
        <p v-if="error" class="error">{{ error }}</p>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const username = ref(localStorage.getItem('admin-username') || 'admin')
const password = ref('123456')
const answer = ref('')
const captchaId = ref('')
const question = ref('')
const showCaptcha = ref(false)
const agree = ref(true)
const remember = ref(true)
const loading = ref(false)
const error = ref('')
const router = useRouter()
const user = useUserStore()

async function loadCaptcha() {
  const res = await http.get<never, { data: { captcha_id: string; question: string } }>('/api/v1/auth/captcha')
  captchaId.value = res.data.captcha_id
  question.value = res.data.question
}

async function submit() {
  error.value = ''
  if (!agree.value) {
    error.value = '请先同意用户协议'
    return
  }
  loading.value = true
  try {
    await user.login({
      username: username.value,
      password: password.value,
      captcha_id: showCaptcha.value ? captchaId.value : '',
      captcha_answer: showCaptcha.value ? answer.value : '',
    })
    if (remember.value) localStorage.setItem('admin-username', username.value)
    else localStorage.removeItem('admin-username')
    router.replace('/dashboard')
  } catch (err) {
    error.value = (err as Error).message
    if ((err as Error & { captcha?: boolean }).captcha || error.value.includes('验证码')) {
      showCaptcha.value = true
      loadCaptcha()
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #0b1220 url('/login-bg.jpg') center / cover no-repeat;
  position: relative;
}
.veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(115deg, rgba(8, 15, 32, 0.55), rgba(15, 23, 42, 0.28));
}
.panel {
  position: relative;
  width: min(440px, calc(100vw - 32px));
  padding: 36px 36px 28px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.35);
}
.brand { display: flex; gap: 14px; align-items: center; margin-bottom: 28px; }
.mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
}
h1 { margin: 0; font-size: 22px; letter-spacing: 0.02em; }
p { margin: 6px 0 0; color: #64748b; font-size: 13px; line-height: 1.5; }
.captcha { display: flex; gap: 8px; width: 100%; }
.refresh {
  border: 0;
  border-radius: 8px;
  padding: 0 14px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
  white-space: nowrap;
}
.row { display: flex; justify-content: space-between; margin: 4px 0 18px; }
.submit { width: 100%; }
.error { color: #dc2626; font-size: 13px; margin: 12px 0 0; }
</style>
