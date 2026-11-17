import { defineStore } from 'pinia'
import { ref } from 'vue'
import http from '@/api/http'
import { getAccess, setAccess } from '@/utils/token'

export const useUserStore = defineStore('user', () => {
  const token = ref(getAccess())
  const account = ref<Record<string, any> | null>(null)
  const permissions = ref<string[]>([])
  const scope = ref('tenant')
  const menus = ref<any[]>([])
  const homeTenant = ref<Record<string, any> | null>(null)
  const tenantId = ref(sessionStorage.getItem('admin-tenant-id') || '')
  const pageEpoch = ref(0)

  function apply(data: { access_token: string; account: Record<string, any>; permissions?: string[] }) {
    setAccess(data.access_token)
    token.value = data.access_token
    account.value = data.account
    permissions.value = data.permissions || []
    scope.value = (data as any).scope || 'tenant'
  }

  async function loadMe() {
    const res = await http.get<never, { data: any }>('/api/v1/auth/me', { params: { client: 'admin' } })
    account.value = res.data.account
    permissions.value = res.data.permissions || []
    scope.value = res.data.scope || 'tenant'
    menus.value = res.data.menus || []
    homeTenant.value = res.data.tenant || null
  }

  function setTenant(id: string) {
    tenantId.value = id || ''
    if (tenantId.value) sessionStorage.setItem('admin-tenant-id', tenantId.value)
    else sessionStorage.removeItem('admin-tenant-id')
    pageEpoch.value += 1
  }

  async function login(payload: { username: string; password: string; captcha_id?: string; captcha_answer?: string }) {
    const res = await http.post<never, { data: any }>('/api/v1/auth/login', { ...payload, client: 'admin' })
    apply(res.data)
  }

  async function tryRefresh() {
    if (token.value) return true
    try {
      const res = await http.post<never, { data: any }>('/api/v1/auth/refresh')
      apply(res.data)
      return true
    } catch {
      token.value = ''
      return false
    }
  }

  function can(code: string) {
    return Boolean(account.value?.is_super) || permissions.value.includes(code)
  }

  async function logout() {
    await http.post('/api/v1/auth/logout').catch(() => undefined)
    setAccess('')
    token.value = ''
    account.value = null
    menus.value = []
  }

  return {
    token, account, permissions, scope, menus, homeTenant, tenantId, pageEpoch,
    login, tryRefresh, can, logout, apply, loadMe, setTenant,
  }
})
