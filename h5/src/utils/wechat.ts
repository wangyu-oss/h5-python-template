import http from '@/api/http'
import { detectEnv } from './env'

interface WxApi {
  config: (options: Record<string, unknown>) => void
  ready: (callback: () => void) => void
  updateAppMessageShareData?: (options: Record<string, unknown>) => void
  chooseImage?: (options: Record<string, unknown>) => void
  scanQRCode?: (options: Record<string, unknown>) => void
  getLocation?: (options: Record<string, unknown>) => void
  startRecord?: (options: Record<string, unknown>) => void
  chooseWXPay?: (options: Record<string, unknown>) => void
}

declare global {
  interface Window {
    wx?: WxApi
  }
}

function loadScript(src: string) {
  return new Promise<void>((resolve, reject) => {
    if (window.wx) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = src
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('微信 JSSDK 加载失败'))
    document.head.appendChild(script)
  })
}

export async function prepareWechat(jsApiList: string[]) {
  const env = detectEnv()
  if (env !== 'wechat' && env !== 'wxwork') {
    return { configured: false, reason: `${env === 'douyin' ? '抖音' : '当前'}环境不支持微信 JSSDK，已降级` }
  }
  await loadScript('https://res.wx.qq.com/open/js/jweixin-1.6.0.js')
  const res = await http.post<never, { data: Record<string, unknown> }>('/api/v1/wechat/jsconfig', {
    url: location.href.split('#')[0],
  })
  const data = res.data
  if (!data.configured || !window.wx) return { configured: false, reason: '未配置微信公众号' }
  window.wx.config({ debug: false, jsApiList, ...data })
  return { configured: true, reason: '' }
}

export async function wechatShare(options: { title: string; desc: string; link: string; imgUrl: string }) {
  const ready = await prepareWechat(['updateAppMessageShareData'])
  if (!ready.configured || !window.wx?.updateAppMessageShareData) return ready
  window.wx.ready(() => window.wx?.updateAppMessageShareData?.({ ...options, success: () => undefined }))
  return { configured: true, reason: '' }
}
