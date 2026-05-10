<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, useAttrs } from 'vue'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { ShoppingBag, User, X } from 'lucide-vue-next'
import { cn } from '@/utils'
import { safeGetSupabaseSession, supabase } from '@/utils/supabase'
import { profileService } from '@/services/profileService'
import { DEFAULT_AVATAR } from '@/utils/avatar'
import { CART_UPDATED_EVENT, readCartItems, removeCartItem, type CartItem } from '@/services/cartService'
import { createEmptyCheckoutDraft, writeCheckoutDraft } from '@/services/checkoutService'

const { hideLogo, showCart, variant } = withDefaults(
  defineProps<{ hideLogo?: boolean; showCart?: boolean; variant?: 'dark' | 'light' | 'solid-light' }>(),
  {
    hideLogo: false,
    showCart: false,
    variant: 'dark',
  },
)

const attrs = useAttrs()
const isScrolled = ref(false)
const isCartOpen = ref(false)
const cartItems = ref<CartItem[]>([])
const cartError = ref('')
const isCheckingOut = ref(false)
const user = ref<any>(null)
const profile = ref<any>(null)
const cachedAvatarUrl = ref('')
const isProfileLoading = ref(false)
let profileSubscription: RealtimeChannel | null = null
let authSubscription: { unsubscribe: () => void } | null = null

const NAV_PROFILE_CACHE_KEY = 'ct_nav_profile_cache'

const readCachedProfile = (userId: string) => {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(`${NAV_PROFILE_CACHE_KEY}:${userId}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const writeCachedProfile = (userId: string, value: any) => {
  if (typeof window === 'undefined' || !value) return
  try {
    window.localStorage.setItem(`${NAV_PROFILE_CACHE_KEY}:${userId}`, JSON.stringify({
      username: value.username || '',
      avatar_url: value.avatar_url || '',
      role: value.role || '',
    }))
  } catch {
    // Ignore cache failures.
  }
}

const isBlackTheme = computed(() => {
  const cls: any = (attrs as any).class
  if (!cls) return false
  if (Array.isArray(cls)) return cls.join(' ').includes('text-black')
  if (typeof cls === 'string') return cls.includes('text-black')
  if (typeof cls === 'object') {
    return Object.entries(cls).some(([key, value]) => value && key.includes('text-black'))
  }
  return false
})

const isLightVariant = computed(() => variant === 'light')
const isSolidLightVariant = computed(() => variant === 'solid-light')

const navShellClass = computed(() => {
  if (isSolidLightVariant.value) {
    return 'bg-white py-5 border-b border-[#edf0f3] shadow-[0_8px_24px_rgba(95,116,94,0.08)]'
  }
  if (isLightVariant.value) {
    return isScrolled.value
      ? 'bg-[#f4f7f1] py-4 border-b border-[#dfe7da] shadow-[0_8px_24px_rgba(95,116,94,0.08)]'
      : 'bg-transparent py-6 border-b border-transparent shadow-none'
  }
  return isScrolled.value ? 'bg-primary/90 backdrop-blur-sm py-4' : 'bg-transparent'
})

const textClass = computed(() => {
  if (isSolidLightVariant.value) return '!text-[#24342a] hover:!text-[#9b8358]'
  if (isLightVariant.value) return isScrolled.value ? '!text-[#24342a] hover:!text-[#9b8358]' : '!text-white hover:!text-accent'
  if (isBlackTheme.value) return '!text-black hover:!text-accent'
  return ''
})

const logoClass = computed(() => {
  if (isSolidLightVariant.value) return '!text-[#1f2f25]'
  if (isLightVariant.value) return isScrolled.value ? '!text-[#1f2f25]' : '!text-white'
  if (isBlackTheme.value) return '!text-black'
  return ''
})

const avatarBorderClass = computed(() => (isLightVariant.value || isSolidLightVariant.value || isBlackTheme.value ? '!border-gray-200' : ''))
const displayName = computed(() => profile.value?.username || user.value?.email?.split('@')[0] || '')
const displayAvatar = computed(() => profile.value?.avatar_url || cachedAvatarUrl.value || DEFAULT_AVATAR)
const cartTotalQuantity = computed(() => cartItems.value.reduce((total, item) => total + item.quantity, 0))

const normalizePrice = (price: string) => Number(String(price).replace(/[^\d.]/g, ''))
const cartSubtotal = computed(() => {
  const total = cartItems.value.reduce((sum, item) => sum + normalizePrice(item.price) * item.quantity, 0)
  return `¥${Number.isFinite(total) ? total.toFixed(2) : '0.00'}`
})

const loadCartItems = () => {
  cartItems.value = readCartItems()
}

const useFallbackCartImage = (event: Event, item: CartItem) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const removeCartPreviewItem = (id: string) => {
  removeCartItem(id)
  loadCartItems()
}

const viewCart = () => {
  isCartOpen.value = false
  window.location.href = '/cart'
}

const checkoutCart = async () => {
  cartError.value = ''
  const invalidItem = cartItems.value.find((item) => !item.productId)
  if (invalidItem) {
    cartError.value = '购物车里有缺少真实商品数据的条目，请重新从商品目录加入后再结算。'
    return
  }

  isCheckingOut.value = true
  try {
    const draft = createEmptyCheckoutDraft()
    draft.items = cartItems.value
    writeCheckoutDraft(draft)
    isCartOpen.value = false
    window.location.href = '/checkout/information'
  } finally {
    isCheckingOut.value = false
  }
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

const setupProfileSubscription = (userId: string) => {
  profileSubscription?.unsubscribe()
  profileSubscription = supabase
    .channel(`public:profiles:${userId}`)
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'profiles',
        filter: `id=eq.${userId}`,
      },
      (payload: any) => {
        if (payload.new) {
          profile.value = { ...profile.value, ...payload.new }
          cachedAvatarUrl.value = profile.value?.avatar_url || cachedAvatarUrl.value
          writeCachedProfile(userId, profile.value)
        }
      },
    )
    .subscribe()
}

const fetchUserData = async () => {
  try {
    const session = await safeGetSupabaseSession()
    user.value = session?.user || null
    if (user.value) {
      const cachedProfile = readCachedProfile(user.value.id)
      if (cachedProfile) {
        profile.value = { ...cachedProfile }
        cachedAvatarUrl.value = cachedProfile.avatar_url || ''
      }

      isProfileLoading.value = true
      const latestProfile = await profileService.fetchProfile(user.value.id)
      profile.value = latestProfile
      cachedAvatarUrl.value = latestProfile?.avatar_url || cachedAvatarUrl.value
      writeCachedProfile(user.value.id, latestProfile)
      setupProfileSubscription(user.value.id)
    } else {
      profile.value = null
      cachedAvatarUrl.value = ''
      profileSubscription?.unsubscribe()
      profileSubscription = null
    }
  } catch (error) {
    console.error('Navigation auth degraded to guest mode:', error)
    user.value = null
    profile.value = null
    cachedAvatarUrl.value = ''
    profileSubscription?.unsubscribe()
    profileSubscription = null
  } finally {
    isProfileLoading.value = false
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  window.addEventListener(CART_UPDATED_EVENT, loadCartItems)
  loadCartItems()
  fetchUserData()
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(() => {
    fetchUserData()
  })
  authSubscription = subscription
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener(CART_UPDATED_EVENT, loadCartItems)
  authSubscription?.unsubscribe()
  profileSubscription?.unsubscribe()
})
</script>

<template>
  <nav
    :class="cn(
      'fixed left-0 top-0 z-50 flex w-full items-center justify-between px-8 py-6 transition-all duration-300',
      navShellClass,
      $attrs.class,
    )"
  >
    <template v-if="!hideLogo">
      <router-link to="/" class="text-3xl font-bold tracking-wide" style="font-family: 'PangMenZhengDao', serif;" :class="logoClass">
        椿天社
      </router-link>
    </template>
    <div v-else class="invisible text-3xl font-bold tracking-wide" style="font-family: 'PangMenZhengDao', serif;" :class="logoClass">
      椿天社
    </div>

    <div class="absolute left-1/2 hidden -translate-x-1/2 items-center space-x-6 md:flex">
      <router-link to="/" class="font-medium transition-colors" :class="textClass">首页</router-link>
      <router-link to="/community" class="font-medium transition-colors" :class="textClass">社区</router-link>
      <router-link to="/discovery" class="font-medium transition-colors" :class="textClass">探索发现</router-link>
      <router-link to="/train-tickets" class="font-medium transition-colors" :class="textClass">旅游出行</router-link>
      <router-link to="/about" class="font-medium transition-colors" :class="textClass">关于我们</router-link>
      <router-link to="/shop" class="font-medium transition-colors" :class="textClass">商城</router-link>
      <router-link
        v-if="profile?.role === 'admin' || profile?.role === 'moderator'"
        to="/admin"
        class="font-medium transition-colors"
        :class="textClass"
      >
        后台管理
      </router-link>
    </div>

    <div class="flex items-center gap-5">
      <div v-if="showCart" class="relative">
        <button
          type="button"
          class="relative flex h-10 w-10 items-center justify-center transition-colors hover:text-[#9b8358]"
          :class="isSolidLightVariant ? 'text-[#24342a]' : 'text-[#0B1D26]'"
          :aria-expanded="isCartOpen"
          @click="isCartOpen = !isCartOpen"
        >
          <ShoppingBag :size="22" />
          <span class="absolute right-0 top-0 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#0B1D26] px-1 text-[10px] font-black leading-none text-[#FBD784]">
            {{ cartTotalQuantity }}
          </span>
        </button>

        <div
          v-if="isCartOpen"
          class="absolute -right-8 top-[52px] w-[390px] bg-white px-6 pb-6 pt-8 text-[#171b20] shadow-[0_28px_70px_rgba(11,29,38,0.12)]"
        >
          <div class="mb-7 flex items-center justify-between">
            <h3 class="text-sm font-black tracking-[0.04em]">购物车</h3>
            <button type="button" class="text-[#1f252b] transition-colors hover:text-[#9b8358]" @click="isCartOpen = false">
              <X :size="18" />
            </button>
          </div>

          <div v-if="cartItems.length" class="max-h-[420px] divide-y divide-[#eeeeee] overflow-y-auto pr-1">
            <div v-for="item in cartItems" :key="item.id" class="grid grid-cols-[118px_1fr_24px] gap-4 py-4 first:pt-0">
              <img :src="item.image" :alt="item.name" class="h-[120px] w-[118px] object-cover" @error="useFallbackCartImage($event, item)" />
              <div class="min-w-0 pt-2">
                <span class="text-sm font-black text-[#9b8358]">¥{{ normalizePrice(item.price).toFixed(2) }}</span>
                <p class="mt-3 truncate text-sm font-medium text-[#3d3d3d]">{{ item.name }}</p>
                <p class="mt-10 text-sm text-[#9a9a9a]">{{ item.meta }} · 数量 {{ item.quantity }}</p>
              </div>
              <button type="button" class="mt-1 text-[#777] transition-colors hover:text-[#0B1D26]" @click="removeCartPreviewItem(item.id)">
                <X :size="16" />
              </button>
            </div>
          </div>
          <div v-else class="border border-dashed border-[#d7dfd2] bg-[#fbfcf8] px-4 py-8 text-center text-sm font-semibold text-[#758176]">
            购物车还是空的
          </div>

          <p v-if="cartError" class="mt-4 border border-[#f0c7bd] bg-[#fff3ef] px-3 py-2 text-xs font-semibold text-[#b24c37]">
            {{ cartError }}
          </p>

          <div class="mt-6 flex items-center justify-between text-sm font-bold">
            <span>小计</span>
            <span>{{ cartSubtotal }}</span>
          </div>

          <div class="mt-7 grid grid-cols-2 gap-4">
            <button type="button" class="border border-[#0B1D26] px-4 py-3 text-sm font-black tracking-[0.04em] text-[#0B1D26] transition-colors hover:bg-[#FBD784]" @click="viewCart">
              查看购物车
            </button>
            <button
              type="button"
              class="bg-[#0B1D26] px-4 py-3 text-sm font-black tracking-[0.04em] text-white transition-colors hover:bg-[#1A3A4A] disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="!cartItems.length || isCheckingOut"
              @click="checkoutCart"
            >
              {{ isCheckingOut ? '处理中' : '去结算' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="user" class="flex items-center space-x-3">
        <router-link to="/profile" class="flex items-center space-x-3 transition-colors hover:text-accent" :class="textClass">
          <div class="h-8 w-8 overflow-hidden rounded-full border border-white/20 bg-[#f2f3f1]" :class="avatarBorderClass">
            <img :src="displayAvatar" class="h-full w-full object-cover transition-opacity duration-150" :class="isProfileLoading ? 'opacity-90' : 'opacity-100'" />
          </div>
          <span class="hidden font-medium sm:block">{{ displayName }}</span>
        </router-link>
      </div>

      <router-link v-else to="/login" class="flex items-center space-x-2 transition-colors hover:text-accent" :class="textClass">
        <User :size="24" />
        <span class="hidden font-medium sm:block">登录</span>
      </router-link>
    </div>
  </nav>
</template>
