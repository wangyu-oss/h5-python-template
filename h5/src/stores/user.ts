import { defineStore } from 'pinia'
import { ref } from 'vue'
import http from '@/api/http'
import { getAccess, setAccess } from '@/utils/token'

export const useUserStore = defineStore('user', () => {
  const token = ref(getAccess())
  const account = ref<Record<string, any> | null>(null)
  const permissions = ref<string[]>([])

  function apply(data: { access_token: string; account: Record<string, any>; permissions?: string[] }) {
    setAccess(data.access_token)
    token.value = data.access_token
    account.value = data.account
    permissions.value = data.permissions || []
  }

  function clearLocal() {
    setAccess('')
    token.value = ''
    account.value = null
    permissions.value = []
  }

  function hasPermission(code?: string) {
    if (!code) return true
    return permissions.value.includes(code)
  }

  async function login(payload: Record<string, unknown>) {
    const res = await http.post<never, { data: any }>('/api/v1/auth/login', payload)
    apply(res.data)
  }

  async function smsLogin(payload: Record<string, unknown>) {
    const res = await http.post<never, { data: any }>('/api/v1/auth/sms/login', payload)
    apply(res.data)
  }

  async function register(payload: Record<string, unknown>) {
    const res = await http.post<never, { data: any }>('/api/v1/auth/register', payload)
    apply(res.data)
  }

  async function guest(deviceId: string) {
    const res = await http.post<never, { data: any }>('/api/v1/auth/guest', { device_id: deviceId })
    apply(res.data)
  }

  async function tryRefresh() {
    if (token.value) return true
    try {
      const res = await http.post<never, { data: any }>('/api/v1/auth/refresh')
      apply(res.data)
      return true
    } catch {
      clearLocal()
      return false
    }
  }

  async function logout() {
    try {
      await http.post('/api/v1/auth/logout')
    } catch {
      /* 退出时即使接口失败也清掉内存令牌 */
    }
    clearLocal()
  }

  return { token, account, permissions, apply, clearLocal, hasPermission, login, smsLogin, register, guest, tryRefresh, logout }
})
