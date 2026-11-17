import axios from 'axios'
import { getAccess, setAccess } from '@/utils/token'

const http = axios.create({ baseURL: '', timeout: 15000, withCredentials: true })

http.interceptors.request.use((config) => {
  const token = getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  const tenantId = sessionStorage.getItem('admin-tenant-id')
  if (tenantId) config.headers['X-Tenant-Id'] = tenantId
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.code === 'number' && body.code !== 0) {
      const failure = new Error(body.msg || '请求失败') as Error & { captcha?: boolean }
      failure.captcha = Boolean(body.data?.captcha)
      return Promise.reject(failure)
    }
    return body
  },
  async (error) => {
    const config = error.config || {}
    if (error.response?.status === 401 && !config._retried && !String(config.url || '').includes('/auth/')) {
      config._retried = true
      try {
        const refreshed = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true })
        const token = refreshed.data?.data?.access_token || ''
        setAccess(token)
        config.headers.Authorization = `Bearer ${token}`
        return http(config)
      } catch {
        setAccess('')
        if (!location.pathname.startsWith('/login')) location.assign('/login')
      }
    }
    return Promise.reject(new Error(error.response?.data?.msg || error.message || '网络异常'))
  },
)

export default http
