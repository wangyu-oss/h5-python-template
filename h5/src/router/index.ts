import { createRouter, createWebHistory } from 'vue-router'
import { setAuthLostHandler } from '@/api/http'
import i18n from '@/i18n'
import { useUserStore } from '@/stores/user'
import { track } from '@/utils/track'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true, titleKey: 'login.title' } },
    { path: '/offline', component: () => import('@/views/Offline.vue'), meta: { public: true, titleKey: 'common.offline' } },
    { path: '/error', component: () => import('@/views/ErrorPage.vue'), meta: { public: true, titleKey: 'common.error' } },
    {
      path: '/',
      component: () => import('@/views/MainLayout.vue'),
      children: [
        { path: '', redirect: '/home' },
        { path: 'home', component: () => import('@/views/Home.vue'), meta: { titleKey: 'tab.home', tab: true, keep: true } },
        { path: 'notices', component: () => import('@/views/Notices.vue'), meta: { titleKey: 'tab.notice', tab: true, keep: true } },
        { path: 'notices/:id', component: () => import('@/views/NoticeDetail.vue'), meta: { titleKey: 'notice.detail' } },
        { path: 'messages', component: () => import('@/views/Messages.vue'), meta: { titleKey: 'tab.message', tab: true, keep: true } },
        { path: 'mine', component: () => import('@/views/Mine.vue'), meta: { titleKey: 'tab.mine', tab: true } },
        { path: 'demo/form', component: () => import('@/views/FormDemo.vue'), meta: { title: '表单' } },
        { path: 'demo/upload', component: () => import('@/views/UploadDemo.vue'), meta: { title: '上传' } },
        { path: 'demo/media', component: () => import('@/views/MediaDemo.vue'), meta: { title: '媒体' } },
        { path: 'demo/share', component: () => import('@/views/ShareDemo.vue'), meta: { title: '分享' } },
        { path: 'demo/tools', component: () => import('@/views/Tools.vue'), meta: { title: '工具' } },
        { path: 'plugin/checkin', component: () => import('@/views/Checkin.vue'), meta: { title: '签到' } },
        { path: 'plugin/survey', component: () => import('@/views/Survey.vue'), meta: { title: '问卷' } },
      ],
    },
    { path: '/:pathMatch(.*)*', component: () => import('@/views/NotFound.vue'), meta: { public: true, titleKey: 'common.notFound' } },
  ],
})

setAuthLostHandler((redirect) => {
  const user = useUserStore()
  user.clearLocal()
  if (router.currentRoute.value.path === '/login') return
  router.replace({ path: '/login', query: { redirect } })
})

router.beforeEach(async (to, from) => {
  if (to.fullPath === from.fullPath) return false
  const offlineAllowed = to.path === '/offline' || to.path === '/login'
  if (typeof navigator !== 'undefined' && !navigator.onLine && !offlineAllowed) {
    return { path: '/offline', query: { redirect: to.fullPath } }
  }
  if (to.meta.public) return true
  const user = useUserStore()
  if (!user.token) {
    const ok = await user.tryRefresh()
    if (!ok) return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

router.afterEach((to) => {
  const titleKey = typeof to.meta.titleKey === 'string' ? to.meta.titleKey : ''
  if (titleKey) document.title = i18n.global.t(titleKey)
  else if (to.meta.title) document.title = String(to.meta.title)
  track('page_view', { path: to.fullPath })
})

export default router
