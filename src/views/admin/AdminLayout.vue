<template>
  <div class="flex h-screen bg-white font-sans text-slate-900 relative overflow-hidden">
    <ChatDrawer :isOpen="isChatOpen" :sidebarWidth="chatDrawerSidebarWidth" @close="isChatOpen = false" />
    <!-- 左侧栏：白色背景，极简文字 -->
    <aside
      class="admin-sidebar flex flex-col"
      :class="sidebarClassName"
    >
      <div
        class="admin-sidebar__header flex items-center gap-2"
        :class="isSidebarCompactMode ? 'justify-center px-0 py-5' : 'justify-start pl-5 pr-5 py-8'"
      >
        <div v-if="!isSidebarCompactMode" class="flex min-w-0 items-center gap-3">
          <router-link
            to="/"
            class="admin-sidebar__brand-shell flex min-w-0 items-center hover:opacity-80 transition-opacity"
          >
            <span
              class="admin-sidebar__brand-name text-4xl font-black text-rose-500 tracking-tighter"
              style="font-family: 'PangMenZhengDao', serif;"
            >
              椿天社
            </span>
          </router-link>
          <span class="admin-sidebar__badge text-[10px] font-bold px-2.5 py-1 rounded-full">
            管理后台
          </span>
        </div>
        <button
          class="admin-sidebar__toggle inline-flex shrink-0 items-center justify-center transition-colors"
          type="button"
          :title="isSidebarCompactMode ? '展开菜单' : '收起菜单'"
          @click="toggleSidebarCompact"
        >
          <span
            class="admin-sidebar__toggle-arrow"
            :class="isSidebarCompactMode ? 'admin-sidebar__toggle-arrow--expanded' : ''"
            aria-hidden="true"
          ></span>
        </button>
      </div>
      
      <div class="flex flex-1 flex-col" :key="sidebarAnimationKey">
        <div class="px-4 mb-6">
          <div
            v-if="!isSidebarCompactMode"
            class="admin-sidebar-section-title px-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2"
            style="--stagger-index: 0"
          >
            仪表盘
          </div>
          <nav class="space-y-1">
            <template v-for="item in primarySidebarItems" :key="item.key">
              <button
                v-if="item.chat"
                @click="openAdminChat"
                class="admin-sidebar-link w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-2xl cursor-pointer transition-colors"
                :class="isSidebarItemActive(item) ? 'admin-sidebar-link--active text-slate-950 font-medium' : 'text-slate-600'"
                :style="{ '--stagger-index': item.staggerIndex }"
                :title="isSidebarCompactMode ? item.label : ''"
              >
                <component :is="item.icon" class="admin-sidebar-link__icon w-4 h-4" />
                <span class="admin-sidebar-link__label">{{ item.label }}</span>
              </button>

              <router-link
                v-else
                :to="item.to"
                custom
                v-slot="{ href, navigate, isActive, isExactActive }"
              >
                <a
                  :href="href"
                  @click.prevent="handleNav(navigate)"
                  class="admin-sidebar-link flex items-center gap-3 px-3 py-2.5 text-sm rounded-2xl cursor-pointer transition-colors"
                  :class="isSidebarItemActive(item, { isActive, isExactActive }) ? 'admin-sidebar-link--active text-slate-950 font-medium' : 'text-slate-600'"
                  :style="{ '--stagger-index': item.staggerIndex }"
                  :title="isSidebarCompactMode ? item.label : ''"
                >
                  <component :is="item.icon" class="admin-sidebar-link__icon w-4 h-4" />
                  <span class="admin-sidebar-link__label">{{ item.label }}</span>
                </a>
              </router-link>
            </template>
          </nav>
        </div>

        <div class="px-4">
          <div
            v-if="!isSidebarCompactMode"
            class="admin-sidebar-section-title px-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2"
            style="--stagger-index: 4"
          >
            管理
          </div>
          <nav class="space-y-1">
            <router-link
              v-for="item in managementSidebarItems"
              :key="item.key"
              :to="item.to"
              custom
              v-slot="{ href, navigate, isActive, isExactActive }"
            >
              <a
                :href="href"
                @click.prevent="handleNav(navigate)"
                class="admin-sidebar-link flex items-center gap-3 px-3 py-2.5 text-sm rounded-2xl cursor-pointer transition-colors"
                :class="isSidebarItemActive(item, { isActive, isExactActive }) ? 'admin-sidebar-link--active text-slate-950 font-medium' : 'text-slate-600'"
                :style="{ '--stagger-index': item.staggerIndex }"
                :title="isSidebarCompactMode ? item.label : ''"
              >
                <component :is="item.icon" class="admin-sidebar-link__icon w-4 h-4" />
                <span class="admin-sidebar-link__label">{{ item.label }}</span>
              </a>
            </router-link>
          </nav>
        </div>

      </div>
    </aside>

    <!-- 中间主内容区 -->
    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 border-b border-slate-100 flex items-center justify-between px-8 bg-white">
        <div class="flex items-center gap-4 text-sm">
          <button
            v-if="false"
            class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50"
            type="button"
            @click="adminSidebarOpen = true"
          >
            <Menu class="w-4 h-4" />
          </button>
          <div class="flex items-center gap-2 text-slate-400">
            <LayoutGrid class="w-4 h-4" />
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">管理</span>
            <span class="text-slate-300">/</span>
            <span class="text-slate-900 font-medium">{{ pageTitle }}</span>
            <template v-if="adminSubPageTitle">
              <span class="text-slate-300">/</span>
              <span class="text-slate-900 font-medium">{{ adminSubPageTitle }}</span>
            </template>
          </div>
        </div>
        
        <div class="flex items-center gap-6">
          <div class="relative hidden md:block">
            <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索..."
              class="pl-9 pr-4 py-1.5 bg-slate-50 border-none rounded-lg text-sm w-64 focus:ring-1 focus:ring-slate-200 outline-none transition-all placeholder:text-slate-400"
            />
            <span v-if="!searchQuery" class="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 font-medium border border-slate-200 px-1 rounded">⌘K</span>

            <!-- Search Results Dropdown -->
            <div v-if="searchQuery" class="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl border border-slate-100 py-2 z-50 max-h-64 overflow-y-auto">
              <template v-if="searchResults.length > 0">
                <button
                  v-for="result in searchResults"
                  :key="result.path"
                  @click="navigateTo(result.path)"
                  class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-3 transition-colors group"
                >
                  <div class="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center group-hover:bg-white group-hover:shadow-sm border border-transparent group-hover:border-slate-100 transition-all">
                    <component :is="result.icon" class="w-4 h-4 text-slate-500 group-hover:text-slate-900" />
                  </div>
                  <span>{{ result.title }}</span>
                </button>
              </template>
              <div v-else class="py-8 text-center">
                <p class="text-xs text-slate-400">未找到相关结果</p>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
             <button class="p-2 hover:bg-slate-50 rounded-full transition-colors relative" @click="isChatOpen = true">
               <Bell class="w-4 h-4 text-slate-400" />
               <span v-if="hasUnreadMessages" class="absolute top-2 right-2 w-1.5 h-1.5 bg-rose-500 rounded-full border border-white"></span>
             </button>
             <button class="p-2 hover:bg-slate-50 rounded-full transition-colors">
               <Settings class="w-4 h-4 text-slate-400" />
             </button>
             <button @click="router.push('/')" class="text-xs text-slate-500 hover:text-rose-600 transition-colors font-medium px-2">退出管理平台</button>
          </div>
        </div>
      </header>

      <main
        class="flex-1 overflow-auto bg-white"
        :class="isQATestPage ? 'p-0' : (isKnowledgePage ? 'px-8 pt-4 pb-6' : 'p-8')"
      >
        <router-view />
      </main>
    </div>

    <!-- 右侧栏：通知与活动 -->
    <aside v-if="!isKnowledgePage" class="w-72 border-l border-slate-100 p-6 overflow-hidden hidden xl:flex flex-col bg-white">
      <div class="mb-8 flex-shrink-0">
        <h3 class="text-sm font-semibold mb-4 text-slate-900">通知</h3>
        <div class="space-y-4">
          <div class="flex gap-3 group cursor-pointer">
            <div class="w-8 h-8 rounded-full bg-blue-50 flex-shrink-0 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
              <Bug class="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <p class="text-xs leading-relaxed text-slate-700">系统检测到新的 API 调用异常。</p>
              <span class="text-[10px] text-slate-400">10 分钟前</span>
            </div>
          </div>
          <div class="flex gap-3 group cursor-pointer">
            <div class="w-8 h-8 rounded-full bg-emerald-50 flex-shrink-0 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
              <User class="w-4 h-4 text-emerald-500" />
            </div>
            <div>
              <p class="text-xs leading-relaxed text-slate-700">新用户注册：zhangsan</p>
              <span class="text-[10px] text-slate-400">1 小时前</span>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-8">
        <h3 class="text-sm font-semibold mb-4 text-slate-900">动态</h3>
        <div class="relative pl-4 space-y-6 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-px before:bg-slate-100 overflow-y-auto pr-2 max-h-[250px]">
          <div v-for="log in adminLogs" :key="log.id" class="relative">
            <div class="absolute -left-[13px] top-1 w-2 h-2 rounded-full bg-slate-300 border-2 border-white ring-1 ring-slate-100"></div>
            <div>
              <p class="text-xs text-slate-700">{{ log.details }}</p>
              <span class="text-[10px] text-slate-400">{{ formatLogTime(log.created_at) }}</span>
            </div>
          </div>
          <div v-if="adminLogs.length === 0" class="text-xs text-slate-400 pl-1">
            暂无动态
          </div>
        </div>
      </div>

      <div class="flex-shrink-0">
        <h3 class="text-sm font-semibold mb-4 text-slate-900">工作人员状态</h3>
        <div class="space-y-3">
          <div v-for="user in allStaff" :key="user.id" class="flex items-center gap-3">
            <div class="relative">
              <img 
                v-if="user.avatar_url" 
                :src="user.avatar_url" 
                class="w-8 h-8 rounded-full object-cover border border-slate-200"
                alt="Avatar"
                :class="{'grayscale opacity-70': !onlineUsers.has(user.id)}"
              />
              <div v-else class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500" :class="{'grayscale opacity-70': !onlineUsers.has(user.id)}">
                {{ (user.username || 'A')[0].toUpperCase() }}
              </div>
              <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 border-2 border-white rounded-full" :class="onlineUsers.has(user.id) ? 'bg-emerald-500' : 'bg-slate-300'"></div>
            </div>
            <div class="flex flex-col">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium" :class="onlineUsers.has(user.id) ? 'text-slate-700' : 'text-slate-400'">{{ user.username || '管理员' }}</span>
                <span 
                  class="text-[9px] px-1.5 py-0.5 rounded font-bold"
                  :class="user.role === 'admin' ? (onlineUsers.has(user.id) ? 'bg-rose-50 text-rose-500' : 'bg-slate-100 text-slate-400') : (onlineUsers.has(user.id) ? 'bg-blue-50 text-blue-500' : 'bg-slate-100 text-slate-400')"
                >
                  {{ user.role === 'admin' ? '管理员' : '审核员' }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="allStaff.length === 0" class="text-xs text-slate-400 px-2">加载中...</div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { supabase } from '@/utils/supabase'
import { useRouter, useRoute } from 'vue-router'
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import {
  LayoutGrid,
  Menu,
  UserCircle,
  Settings2,
  Search,
  Bell,
  Settings,
  Bug,
  User,
  ShieldCheck,
  MessageSquare,
  MessageCircle,
  FileText,
  Database,
  CheckCircle,
  Bot,
  Package,
  ReceiptText
} from 'lucide-vue-next'

import { usePresence } from '@/composables/usePresence'
import ChatDrawer from '@/components/admin/ChatDrawer.vue'
import { chatService } from '@/services/chatService'

const router = useRouter()
const route = useRoute()
const isQATestPage = computed(() => route.name === 'admin-qa-test')
const isKnowledgePage = computed(() => route.name === 'admin-knowledge')
const adminSubPageTitle = ref('')
const adminSidebarOpen = ref(true)
const isSidebarCompact = ref(false)
const handleAdminDrawerToggle = () => {
  adminSidebarOpen.value = !adminSidebarOpen.value
}

const hasUnreadMessages = ref(false)
const sidebarAnimationKey = ref(0)
const isSidebarCompactMode = computed(() => isSidebarCompact.value)
const chatDrawerSidebarWidth = computed(() => {
  return isSidebarCompactMode.value ? 88 : 256
})
const sidebarClassName = computed(() => {
  return [
    isSidebarCompactMode.value ? 'admin-sidebar--compact' : '',
    'transition-[width] duration-300 ease-out',
    isSidebarCompactMode.value ? 'w-[5.5rem]' : 'w-64'
  ]
})

type SidebarItem = {
  key: string
  label: string
  icon: any
  to?: string
  exact?: boolean
  chat?: boolean
  staggerIndex: number
}

const primarySidebarItems: SidebarItem[] = [
  { key: 'dashboard', label: '概览', to: '/admin', icon: LayoutGrid, exact: true, staggerIndex: 1 },
  { key: 'qa-test', label: '测试问答', to: '/admin/qa-test', icon: Bot, staggerIndex: 2 },
  { key: 'chat', label: '内部通讯', icon: MessageCircle, chat: true, staggerIndex: 3 }
]

const managementSidebarItems: SidebarItem[] = [
  { key: 'user-role', label: '用户管理', to: '/admin/user-role', icon: UserCircle, staggerIndex: 5 },
  { key: 'staff', label: '人员管理', to: '/admin/staff', icon: ShieldCheck, staggerIndex: 6 },
  { key: 'comments', label: '评论管理', to: '/admin/comments', icon: MessageSquare, staggerIndex: 7 },
  { key: 'knowledge', label: '知识库管理', to: '/admin/knowledge', icon: Database, staggerIndex: 8 },
  { key: 'content-review', label: '内容审核', to: '/admin/content-review', icon: CheckCircle, staggerIndex: 9 },
  { key: 'datasources', label: '数据源管理', to: '/admin/datasources', icon: Database, staggerIndex: 10 },
  { key: 'products', label: '商品管理', to: '/admin/products', icon: Package, staggerIndex: 11 },
  { key: 'orders', label: '订单管理', to: '/admin/orders', icon: ReceiptText, staggerIndex: 12 },
  { key: 'api-provider', label: 'API 管理', to: '/admin/api-provider', icon: Settings2, staggerIndex: 13 },
  { key: 'api-logs', label: 'API 日志', to: '/admin/api-logs', icon: FileText, staggerIndex: 14 }
]

const replaySidebarAnimation = () => {
  sidebarAnimationKey.value += 1
}

const toggleSidebarCompact = () => {
  isSidebarCompact.value = !isSidebarCompact.value
  replaySidebarAnimation()
}

const isSidebarItemActive = (
  item: SidebarItem,
  states: { isActive?: boolean; isExactActive?: boolean } = {}
) => {
  if (item.chat) {
    return isChatOpen.value
  }

  if (item.key === 'dashboard') {
    return route.name === 'admin-dashboard' && !isChatOpen.value
  }

  if (item.exact) {
    return Boolean(states.isExactActive) && !isChatOpen.value
  }

  return Boolean(states.isActive) && !isChatOpen.value
}

const handleNav = (navigate: any) => {
  // If clicking on the same route, ensure chat closes
  if (isChatOpen.value) {
    isChatOpen.value = false
  }
  navigate()
}

const isChatOpen = ref(false)
const openAdminChat = () => {
  isChatOpen.value = true
}

// Close chat when route changes
watch(() => route.path, () => {
  isChatOpen.value = false
  adminSubPageTitle.value = ''
})

const handleAdminSubPageTitle = (event: Event) => {
  adminSubPageTitle.value = String((event as CustomEvent<string>).detail || '')
}

const { onlineUsers, initPresence, cleanupPresence } = usePresence()

// Check for unread messages periodically or when chat is closed
const checkUnreadMessages = async () => {
  try {
    const counts = await chatService.getUnreadCounts()
    const totalUnread = Object.values(counts).reduce((a, b) => a + b, 0)
    hasUnreadMessages.value = totalUnread > 0
  } catch (error) {
    console.error('Failed to check unread messages:', error)
  }
}

// Watch chat state to update unread status
watch(isChatOpen, (isOpen) => {
  if (!isOpen) {
    checkUnreadMessages()
  }
})

watch(adminSidebarOpen, (isOpen, wasOpen) => {
  if (isOpen && !wasOpen) {
    replaySidebarAnimation()
  }
})

let interval: any

onMounted(() => {
  initPresence()
  checkUnreadMessages()
  window.addEventListener('admin-layout:toggle-sidebar', handleAdminDrawerToggle as EventListener)
  window.addEventListener('admin-layout:set-subpage-title', handleAdminSubPageTitle as EventListener)
  // Set up an interval to check for messages periodically (every 30s)
  interval = setInterval(checkUnreadMessages, 30000)
})

onUnmounted(() => {
  cleanupPresence()
  clearInterval(interval)
  window.removeEventListener('admin-layout:toggle-sidebar', handleAdminDrawerToggle as EventListener)
  window.removeEventListener('admin-layout:set-subpage-title', handleAdminSubPageTitle as EventListener)
})

const currentUser = ref<any>(null)

// Search Logic
const searchQuery = ref('')
const searchablePages = [
  ...primarySidebarItems
    .filter(item => item.to)
    .map(item => ({ title: item.label, path: item.to as string, icon: item.icon })),
  ...managementSidebarItems.map(item => ({ title: item.label, path: item.to as string, icon: item.icon }))
]

const searchResults = computed(() => {
  if (!searchQuery.value) return []
  const query = searchQuery.value.toLowerCase()
  return searchablePages.filter(page => 
    page.title.toLowerCase().includes(query)
  )
})

const navigateTo = (path: string) => {
  router.push(path)
  searchQuery.value = ''
}

const allStaff = ref<any[]>([])

const fetchAllStaff = async () => {
  const { data } = await supabase
    .from('profiles')
    .select('id, username, avatar_url, role')
    .in('role', ['admin', 'moderator'])
    .order('username', { ascending: true })
    
  if (data) {
    allStaff.value = data
  }
}

onMounted(() => {
  fetchCurrentUser()
  fetchAdminLogs()
  fetchAllStaff()
  setupRealtime()
  initPresence()
})

onUnmounted(() => {
  if (logSubscription) supabase.removeChannel(logSubscription)
})

const adminLogs = ref<any[]>([])
let logSubscription: any = null

const fetchAdminLogs = async () => {
  const { data } = await supabase
    .from('admin_logs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(20)
  
  if (data) {
    adminLogs.value = data
  }
}

const setupRealtime = () => {
  logSubscription = supabase
    .channel('public:admin_logs')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'admin_logs' }, (payload) => {
      adminLogs.value.unshift(payload.new)
      if (adminLogs.value.length > 20) adminLogs.value.pop()
    })
    .subscribe()
}

const formatLogTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  
  // Format: Today, 11:59 AM
  // If not today: Yesterday, ... or Date
  
  const isToday = date.toDateString() === now.toDateString()
  const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  
  if (isToday) {
    return `今天, ${timeStr}`
  }
  
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return `昨天, ${timeStr}`
  }
  
  return `${date.toLocaleDateString()}, ${timeStr}`
}

const mapping: Record<string, string> = {
  'admin-api-provider': 'API 管理',
  'admin-api-logs': 'API 日志',
  'admin-user-role': '用户管理',
  'admin-staff': '人员管理',
  'admin-comments': '评论管理',
  'admin-knowledge': '知识库管理',
  'admin-content-review': '内容审核',
  'admin-qa-test': '测试问答',
  'admin-datasources': '数据源管理',
  'admin-products': '商品管理',
  'admin-orders': '订单管理',
  'admin-dashboard': '概览',
  'admin': '概览'
}

const pageTitle = computed(() => {
  const name = route.name?.toString() || ''
  return mapping[name] || '概览'
})

const fetchCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  if (user) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('username, avatar_url, role')
      .eq('id', user.id)
      .single()
    
    currentUser.value = profile || { username: 'Admin', role: 'admin' }
  }
}

const logout = async () => {
  cleanupPresence()
  await supabase.auth.signOut()
  router.push('/login')
}
</script>

<style scoped>
.admin-sidebar-section-title,
.admin-sidebar-link {
  animation: admin-sidebar-stagger-in 0.26s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: calc(var(--stagger-index, 0) * 16ms);
}

.admin-sidebar {
  position: relative;
  z-index: 80;
  isolation: isolate;
  overflow: visible;
  border-right: 1px solid #e2e8f0;
  background:
    linear-gradient(180deg, #f3f6f8 0%, #e9eef2 48%, #dde5ec 100%);
  box-shadow:
    24px 0 46px rgba(148, 163, 184, 0.16),
    inset -1px 0 0 rgba(255, 255, 255, 0.48);
  backdrop-filter: blur(18px);
  transition:
    width 320ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 200ms ease-out,
    box-shadow 220ms ease;
}

.admin-sidebar::before,
.admin-sidebar::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.admin-sidebar::before {
  background:
    radial-gradient(circle at 16% 10%, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0) 22%),
    radial-gradient(circle at 82% 18%, rgba(225, 232, 238, 0.72) 0%, rgba(225, 232, 238, 0) 34%),
    radial-gradient(circle at 24% 88%, rgba(211, 221, 230, 0.62) 0%, rgba(211, 221, 230, 0) 28%);
  opacity: 0.82;
}

.admin-sidebar::after {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 22%, rgba(255, 255, 255, 0) 60%);
}

.admin-sidebar > * {
  position: relative;
  z-index: 1;
}

.admin-sidebar-link {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  transform-origin: left center;
  background: rgba(255, 255, 255, 0.01);
  transition:
    color 220ms ease,
    background-color 220ms ease,
    box-shadow 220ms ease,
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.admin-sidebar-link::before,
.admin-sidebar-link::after {
  content: '';
  position: absolute;
  transition:
    opacity 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.admin-sidebar-link::before {
  inset: 0;
  z-index: -2;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.92));
  box-shadow:
    0 14px 28px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  opacity: 0;
  transform: translateX(-12px) scale(0.985);
}

.admin-sidebar-link::after {
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0) 42%);
  opacity: 0;
  transform: scaleX(0.92);
  transform-origin: left center;
}

.admin-sidebar-link__icon,
.admin-sidebar-link__label {
  transition: transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

.admin-sidebar__brand-shell {
  margin-left: -0.125rem;
  padding-left: 0.125rem;
}

.admin-sidebar__toggle {
  position: absolute;
  top: 2.2rem;
  right: 0;
  z-index: 70;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border-radius: 999px;
  background: #ffffff;
  border: none;
  box-shadow:
    0 6px 14px rgba(15, 23, 42, 0.09);
  transform: translateX(50%);
  transition:
    background-color 180ms ease,
    box-shadow 220ms ease,
    transform 220ms ease;
}

.admin-sidebar__toggle:hover {
  background: #ffffff;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.11);
  transform: translateX(50%) scale(1.02);
}

.admin-sidebar--compact .admin-sidebar__toggle {
  top: 1.45rem;
}

.admin-sidebar__toggle-arrow {
  width: 0.34rem;
  height: 0.34rem;
  border-top: 1.6px solid #111827;
  border-right: 1.6px solid #111827;
  transform: rotate(-135deg);
  transition: transform 220ms ease;
}

.admin-sidebar__toggle-arrow--expanded {
  transform: rotate(45deg);
}

.admin-sidebar__brand-name {
  display: block;
  white-space: nowrap;
  transition:
    opacity 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1),
    max-width 320ms ease;
  max-width: 9rem;
  line-height: 1;
}

.admin-sidebar__badge,
.admin-sidebar-link__label {
  overflow: hidden;
  white-space: nowrap;
  transition:
    opacity 220ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1),
    max-width 300ms ease;
}

.admin-sidebar__badge {
  color: rgb(71 85 105);
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid #e2e8f0;
  box-shadow:
    0 10px 18px rgba(15, 23, 42, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
  max-width: 10rem;
}

.admin-sidebar-link__label {
  max-width: 8rem;
}

.admin-sidebar-link__icon {
  color: rgba(71, 85, 105, 0.88);
  transition-duration: 280ms;
}

.admin-sidebar-section-title {
  color: rgba(100, 116, 139, 0.76);
  letter-spacing: 0.18em;
}

.admin-sidebar-link:hover,
.admin-sidebar-link--active {
  transform: translateX(2px);
}

.admin-sidebar-link:hover::before {
  opacity: 0.68;
  transform: translateX(0) scale(1);
}

.admin-sidebar-link--active::before {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.admin-sidebar-link:hover::after {
  opacity: 0.58;
  transform: scaleX(1);
}

.admin-sidebar-link--active::after {
  opacity: 0.9;
  transform: scaleX(1);
}

.admin-sidebar-link:hover .admin-sidebar-link__icon,
.admin-sidebar-link--active .admin-sidebar-link__icon {
  transform: translateX(1px);
}

.admin-sidebar-link:hover .admin-sidebar-link__label,
.admin-sidebar-link--active .admin-sidebar-link__label {
  transform: translateX(4px);
}

.admin-sidebar-link--active {
  box-shadow:
    0 16px 28px rgba(15, 23, 42, 0.06),
    inset 0 0 0 1px rgba(255, 255, 255, 0.96);
}

.admin-sidebar--compact .admin-sidebar-link {
  justify-content: center;
  gap: 0;
  padding-left: 0;
  padding-right: 0;
}

.admin-sidebar--compact .admin-sidebar-link:hover,
.admin-sidebar--compact .admin-sidebar-link--active {
  transform: translateY(-1px);
}

.admin-sidebar--compact .admin-sidebar__brand-name,
.admin-sidebar--compact .admin-sidebar__badge,
.admin-sidebar--compact .admin-sidebar-link__label {
  opacity: 0;
  max-width: 0;
  transform: translateX(-10px);
}

.admin-sidebar--compact .admin-sidebar__brand-shell {
  gap: 0;
}

@keyframes admin-sidebar-stagger-in {
  0% {
    opacity: 0;
    transform: translate3d(-22px, 0, 0) scale(0.985);
  }

  65% {
    opacity: 1;
  }

  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .admin-sidebar-section-title,
  .admin-sidebar-link,
  .admin-sidebar-link::before,
  .admin-sidebar-link::after,
  .admin-sidebar-link__icon,
  .admin-sidebar-link__label {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
}
</style>
