import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { safeGetSupabaseSession, safeSupabaseSignOut, supabase } from '@/utils/supabase'
import { useToast } from '@/composables/useToast'

const Home = () => import('@/views/Home.vue')
const About = () => import('@/views/About.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const ForgotPassword = () => import('@/views/ForgotPassword.vue')
const ResetPassword = () => import('@/views/ResetPassword.vue')
const Community = () => import('@/views/Community.vue')
const Publish = () => import('@/views/Publish.vue')
const Profile = () => import('@/views/Profile.vue')
const CreatorHome = () => import('@/views/CreatorHome.vue')
const TrainTickets = () => import('@/views/TrainTickets.vue')
const Notifications = () => import('@/views/Notifications.vue')
const Assistant = () => import('@/views/Assistant.vue')
const Itinerary = () => import('@/views/Itinerary.vue')
const ExploreLanding = () => import('@/views/ExploreLanding.vue')
const ScenicSearch = () => import('@/views/ScenicSearch.vue')
const ScenicDetail = () => import('@/views/ScenicDetail.vue')
const Shop = () => import('@/views/Shop.vue')
const ProductCatalogue = () => import('@/views/ProductCatalogue.vue')
const ProductDetail = () => import('@/views/ProductDetail.vue')
const Orders = () => import('@/views/Orders.vue')
const PaymentResult = () => import('@/views/PaymentResult.vue')
const Cart = () => import('@/views/Cart.vue')
const CheckoutInformation = () => import('@/views/CheckoutInformation.vue')
const CheckoutConfirmation = () => import('@/views/CheckoutConfirmation.vue')
const CheckoutPayment = () => import('@/views/CheckoutPayment.vue')
const CheckoutPending = () => import('@/views/CheckoutPending.vue')
const CheckoutSuccess = () => import('@/views/CheckoutSuccess.vue')
const PaymentConfirmPreview = () => import('@/views/PaymentConfirmPreview.vue')

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
    path: '/shop',
    name: 'shop',
    component: Shop,
  },
  {
    path: '/orders',
    name: 'orders',
    component: Orders,
    meta: { requiresAuth: true },
  },
  {
    path: '/cart',
    name: 'cart',
    component: Cart,
  },
  {
    path: '/checkout/information',
    name: 'checkout-information',
    component: CheckoutInformation,
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout/confirmation',
    name: 'checkout-confirmation',
    component: CheckoutConfirmation,
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout/payment',
    name: 'checkout-payment',
    component: CheckoutPayment,
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout/pending',
    name: 'checkout-pending',
    component: CheckoutPending,
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout/success',
    name: 'checkout-success',
    component: CheckoutSuccess,
    meta: { requiresAuth: true },
  },
  {
    path: '/payment/result',
    name: 'payment-result',
    component: PaymentResult,
  },
  {
    path: '/payment-confirm-preview',
    name: 'payment-confirm-preview',
    component: PaymentConfirmPreview,
  },
  {
    path: '/product-catalogue',
    name: 'product-catalogue',
    component: ProductCatalogue,
  },
  {
    path: '/product/:id',
    name: 'product-detail',
    component: ProductDetail,
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
      { path: 'products', name: 'admin-products', component: () => import('@/views/admin/ProductManager.vue'), meta: { title: '商品管理' } },
      { path: 'orders', name: 'admin-orders', component: () => import('@/views/admin/OrderManager.vue'), meta: { title: '订单管理' } },
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

const ADMIN_ROLE_CACHE_TTL = 60 * 1000
const adminRoles = new Set(['admin', 'moderator'])
let cachedAuthRole: { userId: string; role: string; expiresAt: number } | null = null

const clearCachedAuthRole = () => {
  cachedAuthRole = null
}

const getCachedAuthRole = (userId: string) => {
  if (!cachedAuthRole || cachedAuthRole.userId !== userId || cachedAuthRole.expiresAt <= Date.now()) {
    return null
  }

  return cachedAuthRole.role
}

const setCachedAuthRole = (userId: string, role: string) => {
  cachedAuthRole = {
    userId,
    role,
    expiresAt: Date.now() + ADMIN_ROLE_CACHE_TTL,
  }
}

router.beforeEach(async (to, from, next) => {
  try {
    if (!to.meta.requiresAuth && !to.meta.requiresAdmin) {
      clearCachedAuthRole()
      next()
      return
    }

    const session = await safeGetSupabaseSession()
    const { showToast } = useToast()

    if (session?.user) {
      let role = getCachedAuthRole(session.user.id)
      let profileError: unknown = null

      if (!role) {
        const { data: profile, error } = await supabase
          .from('profiles')
          .select('role')
          .eq('id', session.user.id)
          .single()

        role = profile?.role || ''
        profileError = error

        if (role) {
          setCachedAuthRole(session.user.id, role)
        }
      }

      if (profileError) {
        console.error('Error fetching profile for ban check:', profileError)
      }

      if (role === 'banned') {
        console.log('User is banned, redirecting to login.')
        try {
          await safeSupabaseSignOut()
          clearCachedAuthRole()
        } catch (e) {
          console.error('Error signing out:', e)
        }

        showToast('您的账号已被封禁，无法登录。', 'error')
        if (to.path !== '/login') {
          next({ path: '/login', query: { reason: 'banned' } })
          return
        }
      }

      if (to.meta.requiresAdmin && !adminRoles.has(role || '')) {
        next('/')
        return
      }
    } else if (to.meta.requiresAuth) {
      clearCachedAuthRole()
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
