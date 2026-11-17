import { defineStore } from 'pinia'
import { ref } from 'vue'
import http, { isCanceled } from '@/api/http'
import i18n, { type AppLocale } from '@/i18n'
import { setupAnalytics } from '@/utils/track'

const THEME_CHOSEN = 'h5-theme-chosen'

export const useAppStore = defineStore('app', () => {
  const theme = ref<'light' | 'dark'>((localStorage.getItem('h5-theme') as 'light' | 'dark') || 'light')
  const locale = ref(localStorage.getItem('h5-locale') || 'zh-CN')
  const config = ref<{ settings: Record<string, string>; banners: any[]; notices: any[] }>({
    settings: {},
    banners: [],
    notices: [],
  })
  const unread = ref(0)
  const configReady = ref(false)
  const configError = ref('')
  let configTask: Promise<void> | null = null

  function applyTheme(value: 'light' | 'dark', options?: { user?: boolean }) {
    theme.value = value
    localStorage.setItem('h5-theme', value)
    if (options?.user) localStorage.setItem(THEME_CHOSEN, '1')
    document.documentElement.classList.toggle('dark', value === 'dark')
  }

  function setLocale(value: string) {
    locale.value = value
    localStorage.setItem('h5-locale', value)
    i18n.global.locale.value = value as AppLocale
  }

  async function loadConfig() {
    if (!configTask) {
      configTask = (async () => {
        try {
          const res = await http.get<never, { data: typeof config.value }>('/api/v1/config/public')
          config.value = res.data
          configError.value = ''
          const primary = res.data.settings?.h5_primary
          if (primary) document.documentElement.style.setProperty('--app-primary', primary)
          const remoteTheme = res.data.settings?.h5_theme
          if (!localStorage.getItem(THEME_CHOSEN) && (remoteTheme === 'dark' || remoteTheme === 'light')) {
            applyTheme(remoteTheme)
          }
          setupAnalytics(res.data.settings || {})
        } catch (error) {
          if (!isCanceled(error)) configError.value = (error as Error).message || '加载失败'
          throw error
        } finally {
          configReady.value = true
        }
      })().finally(() => {
        configTask = null
      })
    }
    return configTask
  }

  async function loadUnread() {
    try {
      const res = await http.get<never, { data: { count: number } }>('/api/v1/messages/unread')
      unread.value = res.data.count
    } catch {
      unread.value = 0
    }
  }

  applyTheme(theme.value)
  setLocale(locale.value)
  return { theme, locale, config, unread, configReady, configError, applyTheme, setLocale, loadConfig, loadUnread }
})
