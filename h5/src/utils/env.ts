export type ClientEnv = 'wechat' | 'wxwork' | 'douyin' | 'browser'

export function detectEnv(ua = typeof navigator === 'undefined' ? '' : navigator.userAgent): ClientEnv {
  const text = ua.toLowerCase()
  if (text.includes('wxwork')) return 'wxwork'
  if (text.includes('micromessenger')) return 'wechat'
  if (text.includes('aweme') || text.includes('toutiaomicroapp')) return 'douyin'
  return 'browser'
}

export function envLabel(env: ClientEnv) {
  if (env === 'wechat') return '微信'
  if (env === 'wxwork') return '企业微信'
  if (env === 'douyin') return '抖音'
  return '浏览器'
}
