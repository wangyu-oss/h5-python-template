import http from '@/api/http'
import { detectEnv } from './env'

interface TrackItem {
  name: string
  page?: string
  props?: Record<string, unknown>
}

const MAX_QUEUE = 50
const queue: TrackItem[] = []
let timer = 0

function profile() {
  const ua = navigator.userAgent
  return {
    device: /mobile/i.test(ua) ? 'mobile' : 'desktop',
    os: detectEnv(),
    browser: ua.slice(0, 60),
    network: (navigator as Navigator & { connection?: { effectiveType?: string } }).connection?.effectiveType || '',
  }
}

export function track(name: string, props: Record<string, unknown> = {}) {
  queue.push({ name, page: location.pathname, props })
  if (queue.length > MAX_QUEUE) queue.splice(0, queue.length - MAX_QUEUE)
  window.clearTimeout(timer)
  timer = window.setTimeout(flush, 3000)
}

export async function flush() {
  if (!queue.length) return
  const events = queue.splice(0, queue.length)
  try {
    await http.post('/api/v1/track/events', { events, ...profile() })
  } catch {
    const room = MAX_QUEUE - queue.length
    if (room > 0) queue.unshift(...events.slice(0, Math.min(20, room)))
  }
}

export function reportError(kind: string, message: string, detail = '') {
  http.post('/api/v1/track/errors', { kind, message, page: location.pathname, detail }).catch(() => undefined)
}

export function setupAnalytics(settings: Record<string, string> = {}) {
  if (settings.baidu_site_id) console.info('baidu analytics hook', settings.baidu_site_id)
  if (settings.umeng_site_id) console.info('umeng analytics hook', settings.umeng_site_id)
  if (settings.sensors_server) console.info('sensors hook', settings.sensors_server)
}

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', () => {
    void flush()
  })
}
