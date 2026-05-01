<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, ArrowUp, BriefcaseBusiness, CalendarCheck2, MapPinned, Trash2 } from 'lucide-vue-next'
import { supabase } from '@/utils/supabase'
import { useToast } from '@/composables/useToast'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import {
  travelDiscoveryService,
  type BookingIntent,
  type ItineraryItem,
  type ItinerarySummary,
} from '@/services/travelDiscoveryService'

const router = useRouter()
const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const mode = ref<'guest' | 'account'>('guest')
const isLoggedIn = ref(false)
const bookingDialogOpen = ref(false)
const items = ref<ItineraryItem[]>([])
const summary = ref<ItinerarySummary>({
  items_count: 0,
  budget_total: 0,
  city_groups: [],
})
const intents = ref<BookingIntent[]>([])

const bookingForm = reactive({
  trip_name: '',
  contact_name: '',
  contact_phone: '',
  note: '',
})

let authSubscription: { unsubscribe: () => void } | null = null

const hasItems = computed(() => items.value.length > 0)

const loadPage = async () => {
  loading.value = true
  try {
    isLoggedIn.value = await travelDiscoveryService.isLoggedIn()
    const itinerary = await travelDiscoveryService.loadItinerary()
    mode.value = itinerary.mode
    items.value = itinerary.items || []
    summary.value = itinerary.summary

    if (isLoggedIn.value) {
      intents.value = await travelDiscoveryService.listBookingIntents()
    } else {
      intents.value = []
    }
  } catch (error: any) {
    console.error(error)
    showToast(error.message || '加载行程单失败', 'error')
    items.value = []
    summary.value = {
      items_count: 0,
      budget_total: 0,
      city_groups: [],
    }
    intents.value = []
  } finally {
    loading.value = false
  }
}

const persistGuestOrder = () => {
  if (mode.value !== 'guest') {
    return
  }
  const result = travelDiscoveryService.replaceGuestItinerary(items.value)
  summary.value = result.summary
}

const moveItem = (index: number, direction: -1 | 1) => {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= items.value.length) {
    return
  }
  const next = [...items.value]
  const [current] = next.splice(index, 1)
  next.splice(targetIndex, 0, current)
  items.value = next
  persistGuestOrder()
}

const removeItem = async (item: ItineraryItem) => {
  try {
    const result = await travelDiscoveryService.removeItineraryItem(item.item_id)
    items.value = items.value.filter((current) => current.item_id !== item.item_id)
    summary.value = result.summary
    if (!items.value.length) {
      bookingDialogOpen.value = false
    }
    showToast('已从行程单移除', 'success')
  } catch (error: any) {
    showToast(error.message || '删除失败', 'error')
  }
}

const openBookingDialog = () => {
  if (!isLoggedIn.value) {
    showToast('登录后才能提交预订意向', 'warning')
    router.push('/login')
    return
  }

  if (!items.value.length) {
    showToast('行程单还是空的，先加入景点再提交', 'warning')
    return
  }

  bookingDialogOpen.value = true
}

const submitBookingIntent = async () => {
  if (!items.value.length) {
    return
  }

  try {
    submitting.value = true
    await travelDiscoveryService.createBookingIntent({
      trip_name: bookingForm.trip_name,
      contact_name: bookingForm.contact_name,
      contact_phone: bookingForm.contact_phone,
      note: bookingForm.note,
      item_ids: items.value
        .map((item) => item.item_id)
        .filter((itemId): itemId is number => typeof itemId === 'number'),
    })
    bookingDialogOpen.value = false
    bookingForm.trip_name = ''
    bookingForm.contact_name = ''
    bookingForm.contact_phone = ''
    bookingForm.note = ''
    intents.value = await travelDiscoveryService.listBookingIntents()
    showToast('站内待处理订单已生成', 'success')
  } catch (error: any) {
    showToast(error.message || '提交预订意向失败', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadPage()
  const { data } = supabase.auth.onAuthStateChange(async () => {
    await loadPage()
  })
  authSubscription = data.subscription
})

onUnmounted(() => {
  authSubscription?.unsubscribe()
})
</script>

<template>
  <div class="min-h-screen bg-primary text-text-main">
    <Navigation />

    <main class="pt-24">
      <section class="border-b border-white/10">
        <div class="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-16">
          <div class="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end">
            <div>
              <div class="mb-6 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/75">
                <BriefcaseBusiness class="h-4 w-4 text-accent" />
                <span>{{ mode === 'account' ? '账户行程单' : '游客本地行程单' }}</span>
              </div>
              <h1 class="font-serif text-5xl leading-[1.04] md:text-7xl">我的行程单</h1>
              <p class="mt-6 max-w-2xl text-base leading-8 text-white/70">
                主流程不是立即支付，而是先把感兴趣的景点收进同一条决策链路：排序、删减、核算预算，再统一提交站内预订意向。
              </p>
            </div>

            <div class="grid gap-4 md:grid-cols-3">
              <div class="rounded-[28px] border border-white/10 bg-white/6 p-5">
                <p class="text-xs uppercase tracking-[0.24em] text-accent/90">Items</p>
                <p class="mt-3 text-3xl font-semibold">{{ summary.items_count }}</p>
                <p class="mt-2 text-sm text-white/60">已加入景点数量</p>
              </div>
              <div class="rounded-[28px] border border-white/10 bg-white/6 p-5">
                <p class="text-xs uppercase tracking-[0.24em] text-accent/90">Budget</p>
                <p class="mt-3 text-3xl font-semibold">￥{{ summary.budget_total }}</p>
                <p class="mt-2 text-sm text-white/60">预算汇总</p>
              </div>
              <div class="rounded-[28px] border border-white/10 bg-white/6 p-5">
                <p class="text-xs uppercase tracking-[0.24em] text-accent/90">Cities</p>
                <p class="mt-3 text-3xl font-semibold">{{ summary.city_groups.length }}</p>
                <p class="mt-2 text-sm text-white/60">涉及城市数</p>
              </div>
            </div>
          </div>

          <div class="mt-8 flex flex-wrap gap-3">
            <router-link
              to="/discovery"
              class="rounded-full border border-white/12 px-5 py-3 text-sm text-white/80 transition hover:border-white/30 hover:text-white"
            >
              继续添加景点
            </router-link>
            <button
              type="button"
              class="rounded-full bg-accent px-5 py-3 text-sm font-semibold text-[#1b1712] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="!hasItems"
              @click="openBookingDialog"
            >
              提交预订意向
            </button>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div v-if="loading" class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div class="h-[520px] animate-pulse rounded-[32px] border border-white/10 bg-white/5" />
          <div class="h-[520px] animate-pulse rounded-[32px] border border-white/10 bg-white/5" />
        </div>

        <div v-else class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div class="space-y-4">
            <div
              v-if="!items.length"
              class="rounded-[32px] border border-dashed border-white/12 bg-white/4 px-6 py-12 text-center"
            >
              <p class="text-2xl text-white">你的行程单还是空的</p>
              <p class="mt-4 text-sm leading-7 text-white/60">
                {{ mode === 'guest' ? '游客模式会先保存在本地，登录后可同步到账户。' : '先去发现页加入感兴趣的景点，再回来统一提交意向。' }}
              </p>
              <router-link
                to="/discovery"
                class="mt-6 inline-flex rounded-full bg-accent px-5 py-3 text-sm font-semibold text-[#1b1712]"
              >
                去旅游发现
              </router-link>
            </div>

            <article
              v-for="(item, index) in items"
              :key="item.item_id"
              class="rounded-[32px] border border-white/10 bg-white/5 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.16)]"
            >
              <div class="flex flex-col gap-5 lg:flex-row">
                <div
                  class="h-40 w-full shrink-0 rounded-[24px] bg-cover bg-center lg:w-56"
                  :style="{
                    backgroundImage: item.cover_image
                      ? `linear-gradient(180deg, rgba(16,15,15,0.06), rgba(16,15,15,0.45)), url('${item.cover_image}')`
                      : 'linear-gradient(135deg, rgba(211,117,81,0.35), rgba(27,31,38,0.95))',
                  }"
                />

                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div class="inline-flex items-center gap-2 rounded-full bg-white/6 px-3 py-1 text-xs text-white/65">
                        <MapPinned class="h-3.5 w-3.5 text-accent" />
                        {{ item.city || '未标注城市' }}
                      </div>
                      <h2 class="mt-3 text-2xl font-semibold text-white">{{ item.spot_name }}</h2>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-white/55">参考价格</p>
                      <p class="mt-2 text-2xl font-semibold text-accent">
                        {{ item.price > 0 ? `￥${item.price}` : '待定' }}
                      </p>
                    </div>
                  </div>

                  <div class="mt-4 flex flex-wrap gap-2">
                    <span
                      v-for="tag in item.tags"
                      :key="tag"
                      class="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs text-white/70"
                    >
                      {{ tag }}
                    </span>
                  </div>

                  <div class="mt-4 rounded-[20px] border border-accent/20 bg-accent/10 px-4 py-3 text-sm text-accent">
                    {{ item.recommendation_reason || '高评分且价格适中' }}
                  </div>

                  <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
                    <div class="flex gap-2">
                      <button
                        type="button"
                        class="rounded-full border border-white/12 p-2 text-white/70 transition hover:border-white/30 hover:text-white disabled:opacity-30"
                        :disabled="index === 0"
                        @click="moveItem(index, -1)"
                      >
                        <ArrowUp class="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        class="rounded-full border border-white/12 p-2 text-white/70 transition hover:border-white/30 hover:text-white disabled:opacity-30"
                        :disabled="index === items.length - 1"
                        @click="moveItem(index, 1)"
                      >
                        <ArrowDown class="h-4 w-4" />
                      </button>
                    </div>

                    <button
                      type="button"
                      class="inline-flex items-center gap-2 rounded-full border border-red-400/25 px-4 py-2 text-sm text-red-200 transition hover:border-red-300/40 hover:text-white"
                      @click="removeItem(item)"
                    >
                      <Trash2 class="h-4 w-4" />
                      删除
                    </button>
                  </div>
                </div>
              </div>
            </article>
          </div>

          <aside class="space-y-6">
            <div class="rounded-[32px] border border-white/10 bg-white/5 p-6">
              <div class="mb-4 flex items-center gap-3">
                <CalendarCheck2 class="h-5 w-5 text-accent" />
                <h3 class="text-xl font-semibold">预算与城市聚合</h3>
              </div>
              <div class="space-y-3">
                <div
                  v-for="group in summary.city_groups"
                  :key="group.city"
                  class="rounded-[22px] border border-white/10 bg-black/10 px-4 py-4"
                >
                  <div class="flex items-center justify-between gap-4">
                    <div>
                      <p class="text-base text-white">{{ group.city }}</p>
                      <p class="mt-1 text-sm text-white/55">{{ group.count }} 个景点</p>
                    </div>
                    <p class="text-lg font-semibold text-accent">￥{{ group.budget_total }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-[32px] border border-white/10 bg-white/5 p-6">
              <h3 class="text-xl font-semibold">预订意向状态</h3>
              <p class="mt-3 text-sm leading-7 text-white/60">
                V1 只生成站内待处理订单，不接真实支付。客服或后台可据此做后续跟进。
              </p>
              <div class="mt-5">
                <button
                  type="button"
                  class="w-full rounded-full bg-accent px-5 py-3 text-sm font-semibold text-[#1b1712] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="!hasItems"
                  @click="openBookingDialog"
                >
                  从当前行程提交意向
                </button>
              </div>
            </div>

            <div v-if="!isLoggedIn" class="rounded-[32px] border border-dashed border-white/12 bg-white/4 p-6">
              <h3 class="text-xl font-semibold">登录后可同步</h3>
              <p class="mt-3 text-sm leading-7 text-white/60">
                你现在看到的是本地行程单。登录后会自动同步到账户，并能生成待处理订单记录。
              </p>
              <router-link
                to="/login"
                class="mt-5 inline-flex rounded-full border border-white/12 px-5 py-3 text-sm text-white/80 transition hover:border-white/30 hover:text-white"
              >
                去登录
              </router-link>
            </div>
          </aside>
        </div>
      </section>

      <section v-if="isLoggedIn" class="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div class="mb-6 flex items-end justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.28em] text-accent/90">Pending Orders</p>
            <h2 class="mt-2 text-3xl font-semibold">待处理预订意向</h2>
          </div>
        </div>

        <div
          v-if="!intents.length"
          class="rounded-[28px] border border-dashed border-white/12 bg-white/4 px-6 py-10 text-center text-white/60"
        >
          还没有待处理记录。你可以先在上面整理好行程单，再提交第一条意向。
        </div>
        <div v-else class="grid gap-4 lg:grid-cols-2">
          <article
            v-for="intent in intents"
            :key="intent.id"
            class="rounded-[28px] border border-white/10 bg-white/5 p-5"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-accent/90">Intent #{{ intent.id }}</p>
                <h3 class="mt-3 text-2xl font-semibold">{{ intent.trip_name || '未命名行程意向' }}</h3>
              </div>
              <span class="rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs text-accent">
                {{ intent.status }}
              </span>
            </div>
            <div class="mt-4 grid gap-2 text-sm text-white/65">
              <p>联系人：{{ intent.contact_name || '未填写' }}</p>
              <p>电话：{{ intent.contact_phone || '未填写' }}</p>
              <p>景点数量：{{ intent.items_count }}</p>
              <p>预算总计：￥{{ intent.total_estimated_cost }}</p>
            </div>
            <div class="mt-4 rounded-[20px] border border-white/10 bg-black/10 px-4 py-3 text-sm text-white/60">
              {{ intent.note || '暂无备注' }}
            </div>
          </article>
        </div>
      </section>
    </main>

    <div
      v-if="bookingDialogOpen"
      class="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
    >
      <div class="w-full max-w-2xl rounded-[32px] border border-white/10 bg-[#10141b] p-6 text-white shadow-[0_32px_120px_rgba(0,0,0,0.35)]">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.26em] text-accent/90">Booking Intent</p>
            <h3 class="mt-2 text-3xl font-semibold">提交站内预订意向</h3>
          </div>
          <button
            type="button"
            class="rounded-full border border-white/12 px-4 py-2 text-sm text-white/70"
            @click="bookingDialogOpen = false"
          >
            关闭
          </button>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <input
            v-model="bookingForm.trip_name"
            type="text"
            placeholder="行程名称"
            class="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-accent"
          />
          <input
            v-model="bookingForm.contact_name"
            type="text"
            placeholder="联系人"
            class="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-accent"
          />
          <input
            v-model="bookingForm.contact_phone"
            type="text"
            placeholder="联系电话"
            class="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-accent"
          />
          <div class="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white/65">
            将按当前行程单共 {{ summary.items_count }} 个景点生成待处理订单
          </div>
        </div>

        <textarea
          v-model="bookingForm.note"
          rows="4"
          placeholder="补充偏好、出行时间、预算要求或想重点了解的景点"
          class="mt-4 w-full rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white outline-none placeholder:text-white/25 focus:border-accent"
        />

        <div class="mt-4 rounded-[24px] border border-white/10 bg-black/10 p-4">
          <p class="text-sm text-white/70">本次将提交以下景点：</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="item in items"
              :key="item.item_id"
              class="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/75"
            >
              {{ item.spot_name }}
            </span>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button
            type="button"
            class="rounded-full border border-white/12 px-5 py-3 text-sm text-white/80"
            @click="bookingDialogOpen = false"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-full bg-accent px-5 py-3 text-sm font-semibold text-[#1b1712] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="submitting"
            @click="submitBookingIntent"
          >
            {{ submitting ? '提交中...' : '生成待处理订单' }}
          </button>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>
