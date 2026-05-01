import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Home from '@/views/Home.vue'
import About from '@/views/About.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import ForgotPassword from '@/views/ForgotPassword.vue'
import ResetPassword from '@/views/ResetPassword.vue'
import Community from '@/views/Community.vue'
import Publish from '@/views/Publish.vue'
import Profile from '@/views/Profile.vue'
import CreatorHome from '@/views/CreatorHome.vue'
import TrainTickets from '@/views/TrainTickets.vue'
import Notifications from '@/views/Notifications.vue'
import Assistant from '@/views/Assistant.vue'
import Itinerary from '@/views/Itinerary.vue'
import ExploreLanding from '@/views/ExploreLanding.vue'
import ScenicSearch from '@/views/ScenicSearch.vue'
import ScenicDetail from '@/views/ScenicDetail.vue'
import { safeGetSupabaseSession, safeSupabaseSignOut, supabase } from '@/utils/supabase'
import { useToast } from '@/composables/useToast'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: Home,
  },
  {
    path: '/about',
    name: 'about',
    component: About,
  },
  {
    path: '/community',
    name: 'community',
    component: Community,
  },
  {
    path: '/notifications',
    name: 'notifications',
    component: Notifications,
    meta: { requiresAuth: true },
  },
  {
    path: '/assistant',
    name: 'assistant',
    component: Assistant,
  },
  {
    path: '/discovery',
    name: 'discovery',
    component: ExploreLanding,
  },
  {
    path: '/scenic-search',
    name: 'scenic-search',
    component: ScenicSearch,
  },
  {
    path: '/scenic-detail/:id',
    name: 'scenic-detail',
    component: ScenicDetail,
  },
  {
    path: '/explore',
    redirect: '/discovery',
  },
  {
    path: '/itinerary',
    name: 'itinerary',
    component: Itinerary,
  },
  {
    path: '/publish',
    name: 'publish',
    component: Publish,
    meta: { requiresAuth: true },
  },
  {
    path: '/publish/notes',
    name: 'note-manager',
    component: () => import('@/views/NoteManager.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: { requiresAuth: true },
  },
  {
    path: '/creator',
    name: 'creator',
    component: CreatorHome,
    meta: { requiresAuth: true },
  },
  {
    path: '/train-tickets',
    name: 'train-tickets',
    component: TrainTickets,
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: ForgotPassword,
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPassword,
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { title: '概览' } },
      { path: 'api-provider', name: 'admin-api-provider', component: () => import('@/views/admin/ApiProvider.vue'), meta: { title: 'API 提供商' } },
      { path: 'user-role', name: 'admin-user-role', component: () => import('@/views/admin/UserRole.vue'), meta: { title: '用户管理' } },
      { path: 'staff', name: 'admin-staff', component: () => import('@/views/admin/StaffManager.vue'), meta: { title: '人员管理' } },
      { path: 'comments', name: 'admin-comments', component: () => import('@/views/admin/CommentManager.vue'), meta: { title: '评论管理' } },
      { path: 'knowledge', name: 'admin-knowledge', component: () => import('@/views/admin/KnowledgeBase.vue'), meta: { title: '知识库管理' } },
      { path: 'content-review', name: 'admin-content-review', component: () => import('@/views/admin/ContentReview.vue'), meta: { title: '内容审核' } },
      { path: 'qa-test', name: 'admin-qa-test', component: () => import('@/views/admin/AdminQATest.vue'), meta: { title: '测试问答' } },
      { path: 'api-logs', name: 'admin-api-logs', component: () => import('@/views/admin/ApiLogs.vue'), meta: { title: 'API 日志' } },
      { path: 'datasources', name: 'admin-datasources', component: () => import('@/views/admin/DataSourceManager.vue'), meta: { title: '数据源管理' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0, behavior: 'smooth' }
  },
})

router.beforeEach(async (to, from, next) => {
  try {
    const session = await safeGetSupabaseSession()
    const { showToast } = useToast()

    if (session?.user) {
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', session.user.id)
        .single()

      if (profileError) {
        console.error('Error fetching profile for ban check:', profileError)
      }

      if (profile?.role === 'banned') {
        console.log('User is banned, redirecting to login.')
        try {
          await safeSupabaseSignOut()
        } catch (e) {
          console.error('Error signing out:', e)
        }

        showToast('您的账号已被封禁，无法登录。', 'error')
        if (to.path !== '/login') {
          next({ path: '/login', query: { reason: 'banned' } })
          return
        }
      }

      if (to.meta.requiresAdmin && profile?.role !== 'admin' && profile?.role !== 'moderator') {
        next('/')
        return
      }
    } else if (to.meta.requiresAuth) {
      next('/login')
      return
    }

    next()
  } catch (error) {
    console.error('Router auth guard degraded to guest mode:', error)
    if (to.meta.requiresAuth) {
      next('/login')
      return
    }
    next()
  }
})

export default router
