import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'users', component: () => import('@/views/Users.vue') },
        { path: 'roles', component: () => import('@/views/Roles.vue') },
        { path: 'menus', component: () => import('@/views/Menus.vue') },
        { path: 'banners', component: () => import('@/views/Banners.vue') },
        { path: 'announcements', component: () => import('@/views/Announcements.vue') },
        { path: 'settings', component: () => import('@/views/Settings.vue') },
        { path: 'dicts', component: () => import('@/views/Dicts.vue') },
        { path: 'files', component: () => import('@/views/Files.vue') },
        { path: 'templates', component: () => import('@/views/Templates.vue') },
        { path: 'orders', component: () => import('@/views/Orders.vue') },
        { path: 'logs', component: () => import('@/views/Logs.vue') },
        { path: 'track', component: () => import('@/views/Track.vue') },
        { path: 'tenants', component: () => import('@/views/Tenants.vue') },
        { path: 'forbidden', component: () => import('@/views/Forbidden.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const user = useUserStore()
  if (!user.token) {
    const ok = await user.tryRefresh()
    if (!ok) return '/login'
  }
  return true
})

export default router
