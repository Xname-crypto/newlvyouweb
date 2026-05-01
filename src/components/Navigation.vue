<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, useAttrs } from 'vue'
import { User } from 'lucide-vue-next'
import { RealtimeChannel } from '@supabase/supabase-js'
import { cn } from '@/utils'
import { safeGetSupabaseSession, supabase } from '@/utils/supabase'
import { profileService } from '@/services/profileService'
import { DEFAULT_AVATAR } from '@/utils/avatar'

const { hideLogo, variant } = withDefaults(
  defineProps<{ hideLogo?: boolean; variant?: 'dark' | 'light' }>(),
  {
    hideLogo: false,
    variant: 'dark',
  },
)

const isScrolled = ref(false)
const user = ref<any>(null)
let profileSubscription: RealtimeChannel | null = null
const initialProfile = (() => {
  try {
    return JSON.parse(localStorage.getItem('nav_profile') || 'null')
  } catch {
    return null
  }
})()
const profile = ref<any>(initialProfile)
const attrs = useAttrs()

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

const navShellClass = computed(() => {
  if (isLightVariant.value) {
    return isScrolled.value
      ? 'bg-[#f4f7f1] py-4 border-b border-[#dfe7da] shadow-[0_8px_24px_rgba(95,116,94,0.08)]'
      : 'bg-transparent py-6 border-b border-transparent shadow-none'
  }
  return isScrolled.value ? 'bg-primary/90 backdrop-blur-sm py-4' : 'bg-transparent'
})

const textClass = computed(() => {
  if (isLightVariant.value) {
    return isScrolled.value ? '!text-[#24342a] hover:!text-[#9b8358]' : '!text-white hover:!text-accent'
  }
  if (isBlackTheme.value) {
    return '!text-black hover:!text-accent'
  }
  return ''
})

const logoClass = computed(() => {
  if (isLightVariant.value) {
    return isScrolled.value ? '!text-[#1f2f25]' : '!text-white'
  }
  if (isBlackTheme.value) {
    return 'text-red-600'
  }
  return ''
})

const avatarBorderClass = computed(() => (isLightVariant.value || isBlackTheme.value ? '!border-gray-200' : ''))

const displayName = computed(() => profile.value?.username || user.value?.email?.split('@')[0] || '')
const displayAvatar = computed(() => profile.value?.avatar_url || DEFAULT_AVATAR)

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

const setupProfileSubscription = (userId: string) => {
  if (profileSubscription) {
    profileSubscription.unsubscribe()
  }

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
          try {
            localStorage.setItem('nav_profile', JSON.stringify(profile.value))
          } catch {}
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
      const data = await profileService.fetchProfile(user.value.id)
      profile.value = data || null
      try {
        if (profile.value) {
          localStorage.setItem('nav_profile', JSON.stringify(profile.value))
        }
      } catch {}
      setupProfileSubscription(user.value.id)
    } else {
      profile.value = null
      try {
        localStorage.removeItem('nav_profile')
      } catch {}
      if (profileSubscription) {
        profileSubscription.unsubscribe()
        profileSubscription = null
      }
    }
  } catch (error) {
    console.error('Navigation auth degraded to guest mode:', error)
    user.value = null
    profile.value = null
    if (profileSubscription) {
      profileSubscription.unsubscribe()
      profileSubscription = null
    }
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  fetchUserData()

  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(() => {
    fetchUserData()
  })

  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
    subscription.unsubscribe()
    if (profileSubscription) profileSubscription.unsubscribe()
  })
})
</script>

<template>
  <nav
    :class="cn(
      'fixed top-0 left-0 z-50 flex w-full items-center justify-between px-8 py-6 transition-all duration-300',
      navShellClass,
      $attrs.class,
    )"
  >
    <template v-if="!hideLogo">
      <slot name="logo">
        <div
          class="text-text-main text-3xl font-bold tracking-wide"
          style="font-family: 'PangMenZhengDao', serif;"
          :class="logoClass"
        >
          椿天社
        </div>
      </slot>
    </template>

    <div
      v-else
      aria-hidden="true"
      class="text-text-main invisible text-3xl font-bold tracking-wide"
      style="font-family: 'PangMenZhengDao', serif;"
      :class="logoClass"
    >
      椿天社
    </div>

    <div class="absolute left-1/2 hidden -translate-x-1/2 items-center space-x-6 pl-32 md:flex">
      <router-link to="/" class="font-sans font-medium text-text-main transition-colors hover:text-accent" :class="textClass">首页</router-link>
      <router-link to="/community" class="font-sans font-medium text-text-main transition-colors hover:text-accent" :class="textClass">社区</router-link>
      <router-link to="/discovery" class="font-sans font-medium text-text-main transition-colors hover:text-accent" :class="textClass">探索发现</router-link>
      <router-link to="/train-tickets" class="font-sans font-medium text-text-main transition-colors hover:text-accent" :class="textClass">旅游出行</router-link>
      <router-link to="/about" class="font-sans font-medium text-text-main transition-colors hover:text-accent" :class="textClass">关于我们</router-link>
      <router-link
        v-if="profile?.role === 'admin' || profile?.role === 'moderator'"
        to="/admin"
        class="font-sans font-medium text-text-main transition-colors hover:text-accent"
        :class="textClass"
      >
        后台管理
      </router-link>
    </div>

    <div v-if="user" class="flex items-center space-x-3">
      <router-link to="/profile" class="flex items-center space-x-3 text-text-main transition-colors hover:text-accent" :class="textClass">
        <div class="h-8 w-8 overflow-hidden rounded-full border border-white/20" :class="avatarBorderClass">
          <img :src="displayAvatar" class="h-full w-full object-cover" />
        </div>
        <span class="hidden font-sans font-medium sm:block">{{ displayName }}</span>
      </router-link>
    </div>

    <router-link v-else to="/login" class="flex cursor-pointer items-center space-x-2 text-text-main transition-colors hover:text-accent" :class="textClass">
      <User :size="24" />
      <span class="hidden font-sans font-medium sm:block">登录</span>
    </router-link>
  </nav>
</template>
