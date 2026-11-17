import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { showDialog } from 'vant'
import 'vant/es/toast/style'
import 'vant/es/dialog/style'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { setupDirectives } from './directives'
import { reportError } from './utils/track'
import { registerSW } from 'virtual:pwa-register'
import './styles/index.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
setupDirectives(app)
app.config.errorHandler = (error) => reportError('vue', (error as Error).message)
window.addEventListener('error', (event) => {
  if (event.message) reportError('js', event.message, event.filename || '')
})
window.addEventListener('unhandledrejection', (event) => reportError('promise', String(event.reason || '')))
app.mount('#app')

const updateSW = registerSW({
  onNeedRefresh() {
    showDialog({ title: '发现新版本', message: '刷新后使用最新内容' })
      .then(() => updateSW(true))
      .catch(() => undefined)
  },
})
