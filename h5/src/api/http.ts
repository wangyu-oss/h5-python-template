import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getAccess, setAccess } from '@/utils/token'

export interface ApiBody<T> {
  code: number
  msg: string
  data: T
}

export class ApiError extends Error {
  code: number

  constructor(message: string, code = -1) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

interface TrackedConfig extends InternalAxiosRequestConfig {
  _key?: string
  _controller?: AbortController
  _retried?: boolean
  _retry?: boolean
}

const pending = new Map<string, AbortController>()

function stable(value: unknown): string {
  if (value == null) return ''
  if (typeof value !== 'object') return String(value)
  if (Array.isArray(value)) return `[${value.map((item) => stable(item)).join(',')}]`
  const record = value as Record<string, unknown>
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${key}:${stable(record[key])}`)
    .join(',')}}`
}

export function requestKey(config: { method?: string; url?: string; params?: unknown }) {
  const method = (config.method || 'get').toLowerCase()
  return `${method}:${config.url || ''}:${stable(config.params)}`
}

export function isCanceled(error: unknown) {
  return axios.isCancel(error) || (axios.isAxiosError(error) && error.code === 'ERR_CANCELED')
}

function traceId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`
}

function release(config?: TrackedConfig) {
  if (!config?._key || !config._controller) return
  if (pending.get(config._key) === config._controller) pending.delete(config._key)
}

let onAuthLost = (redirect: string) => {
  if (location.pathname.startsWith('/login')) return
  location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
}

export function setAuthLostHandler(handler: (redirect: string) => void) {
  onAuthLost = handler
}

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 15000,
  withCredentials: true,
})

http.interceptors.request.use((config) => {
  const tracked = config as TrackedConfig
  const token = getAccess()
  if (token) tracked.headers.Authorization = `Bearer ${token}`
  tracked.headers['X-Trace-Id'] = traceId()
  if ((tracked.method || 'get').toLowerCase() === 'get') {
    const key = requestKey(tracked)
    const controller = new AbortController()
    const previous = pending.get(key)
    pending.set(key, controller)
    previous?.abort()
    tracked.signal = controller.signal
    tracked._key = key
    tracked._controller = controller
  }
  return tracked
})

let refreshing: Promise<string> | null = null

async function refreshAccess() {
  if (!refreshing) {
    refreshing = axios
      .post('/api/v1/auth/refresh', {}, { withCredentials: true, baseURL: import.meta.env.VITE_API_BASE || '' })
      .then((response) => {
        const token = response.data?.data?.access_token || ''
        setAccess(token)
        return token
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

http.interceptors.response.use(
  (response) => {
    release(response.config as TrackedConfig)
    const body = response.data as ApiBody<unknown>
    if (body && typeof body.code === 'number' && body.code !== 0) {
      return Promise.reject(new ApiError(body.msg || '请求失败', body.code))
    }
    return body as never
  },
  async (error: AxiosError<ApiBody<unknown>>) => {
    const config = error.config as TrackedConfig | undefined
    if (isCanceled(error)) {
      release(config)
      return Promise.reject(error)
    }
    if (config && !error.response && !config._retry && (config.method || '').toLowerCase() === 'get') {
      config._retry = true
      release(config)
      return http(config)
    }
    if (error.response?.status === 401 && config && !config._retried && !String(config.url || '').includes('/auth/')) {
      config._retried = true
      try {
        const token = await refreshAccess()
        if (!token) throw new ApiError('登录已失效', 401)
        config.headers.Authorization = `Bearer ${token}`
        return http(config)
      } catch {
        release(config)
        setAccess('')
        onAuthLost(`${location.pathname}${location.search}`)
        return Promise.reject(new ApiError('登录已失效', 401))
      }
    }
    release(config)
    const message = error.response?.data?.msg || error.message || '网络异常'
    const code = error.response?.data?.code ?? error.response?.status ?? -1
    return Promise.reject(new ApiError(message, code))
  },
)

export default http
