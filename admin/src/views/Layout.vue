<template>
  <el-container class="shell">
    <el-aside :width="collapsed ? '72px' : '232px'" class="aside">
      <div class="brand">
        <img class="mark" src="/favicon.svg" alt="" />
        <strong v-show="!collapsed">工作台</strong>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu :key="menuKey" :default-active="route.path" :collapse="collapsed" :default-openeds="opened" router background-color="transparent" text-color="#cbd5e1" active-text-color="#ffffff">
          <template v-for="node in nav" :key="node.id">
            <el-menu-item v-if="solo(node)" :index="solo(node)!.path">
              <el-icon><component :is="iconOf(solo(node)!)" /></el-icon>
              <template #title>{{ solo(node)!.name }}</template>
            </el-menu-item>
            <el-sub-menu v-else :index="String(node.id)">
              <template #title>
                <el-icon><component :is="iconOf(node)" /></el-icon>
                <span>{{ node.name }}</span>
              </template>
              <el-menu-item v-for="item in kids(node)" :key="item.id" :index="item.path">
                <el-icon><component :is="iconOf(item)" /></el-icon>
                <template #title>{{ item.name }}</template>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>
    <el-container class="right">
      <el-header class="header">
        <el-button class="fold" text @click="collapsed = !collapsed">
          <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-icon v-if="current" class="page-icon"><component :is="iconOf(current)" /></el-icon>
        <div class="crumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>后台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="groupTitle">{{ groupTitle }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ current?.name || '页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <el-tag size="small" effect="plain">{{ env }} {{ version }}</el-tag>
        <el-tag size="small">{{ tenantLabel }}</el-tag>
        <el-select v-if="user.can('admin:tenant')" v-model="user.tenantId" placeholder="全部客户" clearable class="tenant" @change="onTenant">
          <el-option v-for="item in tenants" :key="item.id" :label="item.name" :value="String(item.id)" />
        </el-select>
        <el-dropdown>
          <span class="who">{{ user.account?.display_name || '管理员' }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="passwordOpen = true">修改密码</el-dropdown-item>
              <el-dropdown-item @click="openDevices">登录设备</el-dropdown-item>
              <el-dropdown-item @click="exit">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view :key="user.pageEpoch" />
      </el-main>
    </el-container>
  </el-container>
  <el-dialog v-model="passwordOpen" title="修改密码" width="420px">
    <el-form label-width="80px">
      <el-form-item label="原密码"><el-input v-model="password.old_password" type="password" show-password /></el-form-item>
      <el-form-item label="新密码"><el-input v-model="password.password" type="password" show-password placeholder="至少 8 位，含字母和数字" /></el-form-item>
    </el-form>
    <template #footer><el-button type="primary" @click="changePassword">保存</el-button></template>
  </el-dialog>
  <el-drawer v-model="deviceOpen" title="登录设备" size="420px">
    <el-table :data="devices" border>
      <el-table-column prop="ip" label="IP" width="120" />
      <el-table-column prop="user_agent" label="设备" />
      <el-table-column prop="created_at" label="时间" width="150" />
      <el-table-column label="操作" width="80">
        <template #default="{ row }"><el-button link type="danger" @click="kick(row)">退出</el-button></template>
      </el-table-column>
      <template #empty><el-empty description="没有在线设备" /></template>
    </el-table>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell, Collection, DataAnalysis, Document, Expand, Fold, Folder,
  Menu as MenuIcon, Message, OfficeBuilding, Picture, Setting, Stamp, Tickets, TrendCharts, User,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

type MenuNode = { id: number; name: string; path: string; menu_type: string; visible: boolean; children?: MenuNode[] }

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const collapsed = ref(false)
const env = ref('dev')
const version = ref('')
const tenants = ref<any[]>([])
const passwordOpen = ref(false)
const deviceOpen = ref(false)
const devices = ref<any[]>([])
const password = reactive({ old_password: '', password: '' })
const icons: Record<string, unknown> = {
  '/dashboard': DataAnalysis,
  '/tenants': OfficeBuilding,
  '/users': User,
  '/roles': Stamp,
  '/menus': MenuIcon,
  '/banners': Picture,
  '/announcements': Bell,
  '/orders': Tickets,
  '/templates': Message,
  '/settings': Setting,
  '/dicts': Collection,
  '/files': Folder,
  '/logs': Document,
  '/track': TrendCharts,
  组织: User,
  内容: Picture,
  业务: Tickets,
  系统: Setting,
}

function kids(node: MenuNode) {
  return (node.children || []).filter((item) => item.visible !== false && item.menu_type !== 'button' && item.path !== '/plugins')
}

function solo(node: MenuNode) {
  const children = kids(node)
  if (node.menu_type === 'directory' && children.length === 1) return children[0]
  if (node.menu_type !== 'directory' && !children.length) return node
  return null
}

function iconOf(node: MenuNode) {
  return icons[node.path] || icons[node.name] || Setting
}

const nav = computed(() => (user.menus as MenuNode[]).filter((node) => {
  if (node.visible === false || node.menu_type === 'button' || node.path === '/plugins') return false
  if (node.menu_type === 'directory') return kids(node).length > 0
  return Boolean(node.path)
}))
const opened = computed(() => nav.value.filter((node) => !solo(node)).map((node) => String(node.id)))
const menuKey = computed(() => opened.value.join(',') || 'menu')
const currentGroup = computed(() => nav.value.find((node) => node.path === route.path || kids(node).some((item) => item.path === route.path)))
const current = computed(() => {
  const group = currentGroup.value
  if (!group) return null
  return kids(group).find((item) => item.path === route.path) || (group.path === route.path ? group : null)
})
const groupTitle = computed(() => {
  const group = currentGroup.value
  if (!group || solo(group)) return ''
  return group.name
})
const tenantLabel = computed(() => {
  if (user.can('admin:tenant')) {
    if (!user.tenantId) return '全部客户'
    return tenants.value.find((item) => String(item.id) === user.tenantId)?.name || '当前客户'
  }
  return user.homeTenant?.name || '当前客户'
})

function onTenant() {
  user.setTenant(user.tenantId || '')
}

async function changePassword() {
  try {
    await http.post('/api/v1/auth/password', password)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '修改失败')
    return
  }
  passwordOpen.value = false
  password.old_password = ''
  password.password = ''
  ElMessage.success('密码已更新')
}

async function openDevices() {
  devices.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/online', { params: { mine: 1 } })).data.items
  deviceOpen.value = true
}

async function kick(row: any) {
  await http.post('/api/v1/admin/online/kick', { id: row.id })
  ElMessage.success('已退出该设备')
  openDevices()
}

async function exit() {
  await user.logout()
  router.replace('/login')
}

watch(() => user.pageEpoch, () => {
  user.loadMe().catch(() => undefined)
})

onMounted(async () => {
  document.documentElement.classList.remove('dark')
  await user.loadMe()
  const health = await http.get<never, { data: { env: string; version: string } }>('/api/v1/health')
  env.value = health.data.env
  version.value = health.data.version
  if (user.can('admin:tenant')) tenants.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/tenants')).data.items
})
</script>

<style scoped>
.shell { height: 100vh; overflow: hidden; }
.aside { height: 100vh; display: flex; flex-direction: column; overflow: hidden; background: #0f172a; color: #fff; }
.brand { display: flex; gap: 12px; align-items: center; height: 64px; padding: 0 16px; flex: none; }
.mark { width: 36px; height: 36px; border-radius: 10px; }
.menu-scroll { flex: 1; min-height: 0; height: 100%; }
.menu-scroll :deep(.el-scrollbar__wrap) { overflow-x: hidden; }
.right { height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.header {
  display: flex; align-items: center; gap: 12px; height: 64px; flex: none;
  background: #fff; border-bottom: 1px solid #e8edf5;
}
.fold, .page-icon { font-size: 18px; }
.crumb { flex: 1; min-width: 0; }
.tenant { width: 160px; }
.who { cursor: pointer; font-weight: 600; }
.main { flex: 1; min-height: 0; overflow: hidden; background: #f4f7fb; padding: 0; }
:deep(.el-menu) { border-right: 0; }
:deep(.el-menu-item.is-active) { background: rgba(37, 99, 235, 0.28) !important; }
:deep(.el-sub-menu__title) { color: #cbd5e1 !important; }
:deep(.el-sub-menu .el-menu-item) { background: transparent !important; }
</style>
