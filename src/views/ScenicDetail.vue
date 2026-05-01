<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Activity,
  ArrowLeft,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  Heart,
  Info,
  MapPin,
  Share2,
  Sparkles,
  Star,
  Users,
  X,
} from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { travelDiscoveryService, type SpotDetailResponse } from '@/services/travelDiscoveryService'
import {
  getScenicDetailById,
  type ScenicDetailData,
  type ScenicFactIconKey,
} from '@/data/scenicDetails'

type SectionId = 'overview' | 'inclusions' | 'reviews' | 'faq' | 'essential'

const route = useRoute()
const remoteDetail = ref<SpotDetailResponse | null>(null)

const staticDetail = computed<ScenicDetailData | null>(() => {
  const id = String(route.params.id ?? '')
  return getScenicDetailById(id)
})

const detail = computed<ScenicDetailData | null>(() => {
  if (remoteDetail.value) {
    const item = remoteDetail.value
    const gallery = item.cover_image
      ? [
          {
            src: item.cover_image,
            alt: item.name,
          },
        ]
      : []

    return {
      id: item.spot_key,
      title: item.name,
      subtitle: item.city,
      locationLabel: item.address || item.city,
      breadcrumb: ['目的地', item.city, item.name],
      reviewCount: 0,
      reviewScore: item.rating || 0,
      price: {
        current: item.price > 0 ? `¥${Number(item.price).toFixed(2)}` : '免费',
        note: '价格以实际预订页为准',
      },
      gallery,
      overview: {
        description: item.description || '暂无景点简介',
        facts: [
          { label: '游玩时间', value: item.visit_duration || '待补充', icon: 'duration' },
          { label: '活动类型', value: (item.tags || []).slice(0, 1)[0] || '景点游览', icon: 'activity' },
          { label: '开放时间', value: item.opening_hours || '待补充', icon: 'season' },
          { label: '预订要求', value: item.booking_required || '待补充', icon: 'group' },
          { label: '适合人群', value: '全年龄', icon: 'age' },
          { label: '所在城市', value: item.city || '待补充', icon: 'season' },
        ],
      },
      bookingPanel: {
        dateOptions: ['今日可查', '明日可查', '周末可查'],
        travelerSummary: '支持多人出行',
        selectionHint: '',
        contactHint: item.address || item.city,
        reserveNote: item.opening_hours || '开放时间以景区当天公示为准',
      },
      itineraryDays: [
        {
          id: 'day-1',
          title: '第 1 天',
          summary: item.description || '建议结合开放时间灵活安排行程。',
          media: gallery[0],
          mapLabel: item.address || '查看位置',
        },
      ],
      includes: [
        `开放时间：${item.opening_hours || '待补充'}`,
        `游玩时间：${item.visit_duration || '待补充'}`,
        `预订要求：${item.booking_required || '待补充'}`,
      ],
      excludes: ['往返交通', '个人消费', '未注明的额外项目'],
      reviews: [],
      faqs: [
        {
          id: 'faq-1',
          question: '这个景点需要预订吗？',
          answer: item.booking_required || '暂未提供预订说明',
        },
        {
          id: 'faq-2',
          question: '开放时间是什么？',
          answer: item.opening_hours || '暂未提供开放时间',
        },
      ],
      essentialInfo: [
        `具体地址：${item.address || '待补充'}`,
        `开放时间：${item.opening_hours || '待补充'}`,
        `建议游玩时长：${item.visit_duration || '待补充'}`,
      ],
      similarTours: (item.similar_spots || []).slice(0, 3).map((spot) => ({
        id: spot.spot_key,
        title: spot.name,
        subtitle: spot.city,
        image: spot.cover_image,
        price: spot.price > 0 ? `¥${Number(spot.price).toFixed(2)}` : '免费',
        badgeText: spot.visit_duration || undefined,
      })),
    }
  }

  return staticDetail.value
})

const currentImageIndex = ref(0)
const openDayIds = ref<string[]>([])
const openFaqIds = ref<string[]>([])
const activeTab = ref<SectionId>('overview')
const selectedDate = ref('')
const travelerCount = ref(3)
const selectedPackage = ref('鏍囧噯鍑鸿')
const isSaved = ref(false)

const packageOptions = ['鏍囧噯鍑鸿', '杞诲ア鍗囩骇', '浜插瓙鍚屾父']

const tabs: { key: SectionId; label: string }[] = [
  { key: 'overview', label: '姒傝' },
  { key: 'inclusions', label: '璐圭敤璇存槑' },
  { key: 'reviews', label: '鐢ㄦ埛璇勪环' },
  { key: 'faq', label: '甯歌闂' },
  { key: 'essential', label: '鍑鸿椤荤煡' },
]

const normalizeQueryValue = (value: unknown) => {
  if (Array.isArray(value)) {
    return value[0] ?? ''
  }

  return typeof value === 'string' ? value : ''
}

const searchContextLabel = computed(() => {
  const province = normalizeQueryValue(route.query.province)
  const spot = normalizeQueryValue(route.query.spot)
  const date = normalizeQueryValue(route.query.date)

  return [province, spot, date].filter(Boolean).join(' 路 ')
})

const currentImage = computed(() => detail.value?.gallery[currentImageIndex.value] ?? null)

const reviewStars = computed(() =>
  Array.from({ length: 5 }, (_, index) => index < Math.round(detail.value?.reviewScore ?? 0)),
)

const visibleGallery = computed(() => detail.value?.gallery.slice(0, 4) ?? [])

const scrollToSection = (section: SectionId) => {
  activeTab.value = section
  document.getElementById(`scenic-section-${section}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

const cycleHero = (direction: 'prev' | 'next') => {
  if (!detail.value?.gallery.length) {
    return
  }

  const total = detail.value.gallery.length
  currentImageIndex.value =
    direction === 'prev'
      ? (currentImageIndex.value - 1 + total) % total
      : (currentImageIndex.value + 1) % total
}

const toggleDay = (dayId: string) => {
  openDayIds.value = openDayIds.value.includes(dayId)
    ? openDayIds.value.filter((value) => value !== dayId)
    : [...openDayIds.value, dayId]
}

const toggleFaq = (faqId: string) => {
  openFaqIds.value = openFaqIds.value.includes(faqId)
    ? openFaqIds.value.filter((value) => value !== faqId)
    : [...openFaqIds.value, faqId]
}

const resolveFactIcon = (icon: ScenicFactIconKey) => {
  const iconMap = {
    duration: Clock3,
    activity: Activity,
    intensity: Sparkles,
    group: Users,
    age: Info,
    season: CalendarDays,
  }

  return iconMap[icon]
}

watch(
  () => route.params.id,
  async () => {
    const id = String(route.params.id ?? '')
    remoteDetail.value = await travelDiscoveryService.getSpotDetail(id)
    currentImageIndex.value = 0
    openDayIds.value = []
    openFaqIds.value = []
    activeTab.value = 'overview'
    selectedDate.value = detail.value?.bookingPanel.dateOptions[0] ?? ''
    travelerCount.value = 3
    selectedPackage.value = '鏍囧噯鍑鸿'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  },
  { immediate: true },
)
</script>

<template>
  <div class="min-h-screen bg-[#fafbfc] text-[#243251]">
    <Navigation
      class="text-black !border-b !border-[#edf0f3] !bg-white/95 py-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]"
    >
      <template #logo>
        <router-link
          to="/"
          class="text-4xl font-bold tracking-wide text-[#1f2937]"
          style="font-family: 'PangMenZhengDao', serif;"
        >
          妞垮ぉ绀?        </router-link>
      </template>
    </Navigation>

    <main class="px-5 pb-24 pt-28 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-[1220px]">
        <div class="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div class="space-y-2">
            <router-link
              :to="{ name: 'scenic-search', query: route.query }"
              class="inline-flex items-center gap-2 text-[13px] font-medium text-[#5d6b82] transition hover:text-[#1b9d98]"
            >
              <ArrowLeft class="h-4 w-4" />
              <span>杩斿洖鎼滅储缁撴灉</span>
            </router-link>
            <p v-if="searchContextLabel" class="text-[12px] text-[#8c95a8]">
              褰撳墠涓婁笅鏂囷細{{ searchContextLabel }}
            </p>
          </div>
        </div>

        <template v-if="detail">
          <section class="grid gap-4 lg:grid-cols-[92px_minmax(0,1fr)]">
            <div class="order-2 flex gap-3 overflow-x-auto pb-2 lg:order-1 lg:flex-col lg:overflow-visible">
              <button
                v-for="(image, index) in visibleGallery"
                :key="`${image.src}-${index}`"
                type="button"
                class="group relative h-[92px] min-w-[92px] overflow-hidden rounded-[18px] border transition"
                :class="
                  currentImageIndex === index
                    ? 'border-[#1bb8b5] shadow-[0_14px_28px_rgba(27,184,181,0.16)]'
                    : 'border-[#e7ecf2] hover:border-[#cfd8e3]'
                "
                @click="currentImageIndex = index"
              >
                <img :src="image.src" :alt="image.alt" class="h-full w-full object-cover transition duration-300 group-hover:scale-105" />
                <div
                  v-if="index === 3 && detail.gallery.length > 4"
                  class="absolute inset-0 flex items-center justify-center bg-[#10223c]/62 text-[11px] font-semibold text-white"
                >
                  +{{ detail.gallery.length - 4 }} 寮犵収鐗?                </div>
              </button>
            </div>

            <div class="order-1 overflow-hidden rounded-[28px] bg-white shadow-[0_24px_60px_rgba(20,31,56,0.08)] lg:order-2">
              <div class="relative h-[280px] sm:h-[420px] lg:h-[470px]">
                <img
                  v-if="currentImage"
                  :src="currentImage.src"
                  :alt="currentImage.alt"
                  class="h-full w-full object-cover"
                />

                <button
                  type="button"
                  class="absolute left-4 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/35 bg-white/18 text-white backdrop-blur-sm transition hover:bg-white/30"
                  @click="cycleHero('prev')"
                >
                  <ChevronLeft class="h-5 w-5" />
                </button>

                <button
                  type="button"
                  class="absolute right-4 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/35 bg-white/18 text-white backdrop-blur-sm transition hover:bg-white/30"
                  @click="cycleHero('next')"
                >
                  <ChevronRight class="h-5 w-5" />
                </button>

                <div class="absolute bottom-4 right-4 inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-2 text-[12px] font-medium text-[#475569] shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <Share2 class="h-3.5 w-3.5" />
                  <span>{{ detail.gallery.length }} 寮犲浘</span>
                </div>
              </div>
            </div>
          </section>

          <section class="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_322px]">
            <div class="min-w-0">
              <div class="rounded-[28px] border border-[#edf1f5] bg-white px-6 py-6 shadow-[0_18px_48px_rgba(15,23,42,0.04)] sm:px-8">
                <div class="flex flex-col gap-5 border-b border-[#eef2f6] pb-6 lg:flex-row lg:items-start lg:justify-between">
                  <div class="min-w-0">
                    <p class="text-[12px] font-medium text-[#9aa3b5]">
                      {{ detail.breadcrumb.join(' / ') }}
                    </p>
                    <h1 class="mt-2 text-[30px] font-semibold leading-tight tracking-[-0.03em] text-[#1d2b49] sm:text-[38px]">
                      {{ detail.title }}
                    </h1>
                    <div class="mt-3 flex flex-wrap items-center gap-3 text-[13px] text-[#7a859b]">
                      <span class="inline-flex items-center gap-1.5">
                        <MapPin class="h-4 w-4 text-[#1bb8b5]" />
                        {{ detail.locationLabel }}
                      </span>
                      <span>{{ detail.subtitle }}</span>
                    </div>
                  </div>

                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#e6ebf1] text-[#8f98ab] transition hover:border-[#d7dee8] hover:text-[#ff6a93]"
                      @click="isSaved = !isSaved"
                    >
                      <Heart class="h-5 w-5" :fill="isSaved ? 'currentColor' : 'none'" :class="isSaved ? 'text-[#ff6a93]' : ''" />
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#e6ebf1] text-[#8f98ab] transition hover:border-[#d7dee8] hover:text-[#1bb8b5]"
                    >
                      <Share2 class="h-5 w-5" />
                    </button>
                  </div>
                </div>

                <div class="mt-5 flex flex-wrap items-center gap-4 text-[13px] text-[#6a758a]">
                  <div class="flex items-center gap-1 text-[#f7aa19]">
                    <Star
                      v-for="(active, index) in reviewStars"
                      :key="index"
                      class="h-4 w-4"
                      :fill="active ? 'currentColor' : 'none'"
                      :class="active ? 'text-[#f7aa19]' : 'text-[#d6dde8]'"
                    />
                  </div>
                  <span class="font-medium text-[#32405f]">
                    {{ detail.reviewScore.toFixed(1) }}
                  </span>
                  <span>{{ detail.reviewCount }} 条评价</span>
                </div>

                <div class="mt-6 flex flex-wrap gap-2 border-b border-[#eef2f6] pb-5">
                  <button
                    v-for="tab in tabs"
                    :key="tab.key"
                    type="button"
                    class="rounded-full px-4 py-2 text-[13px] font-medium transition"
                    :class="
                      activeTab === tab.key
                        ? 'bg-[#17b8b1] text-white shadow-[0_10px_24px_rgba(23,184,177,0.22)]'
                        : 'bg-[#f5f7fa] text-[#7e8798] hover:bg-[#edf2f7] hover:text-[#44506a]'
                    "
                    @click="scrollToSection(tab.key)"
                  >
                    {{ tab.label }}
                  </button>
                </div>

                <section id="scenic-section-overview" class="scroll-mt-32 pt-6">
                  <div class="grid gap-6 lg:grid-cols-[56px_minmax(0,1fr)]">
                    <div class="hidden items-start justify-center lg:flex">
                      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f2fbfb] text-[#19b7b1]">
                        <Info class="h-5 w-5" />
                      </div>
                    </div>

                    <div>
                      <h2 class="text-[18px] font-semibold text-[#22304f]">鏅偣姒傝</h2>
                      <p class="mt-4 max-w-[760px] text-[14px] leading-7 text-[#69758c]">
                        {{ detail.overview.description }}
                      </p>

                      <div class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                        <div
                          v-for="fact in detail.overview.facts"
                          :key="fact.label"
                          class="rounded-[20px] border border-[#edf1f5] bg-[#fbfcfd] px-4 py-4"
                        >
                          <div class="flex items-center gap-3">
                            <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#eff9f8] text-[#1ab6ae]">
                              <component :is="resolveFactIcon(fact.icon)" class="h-4.5 w-4.5" />
                            </div>
                            <div>
                              <p class="text-[11px] uppercase tracking-[0.08em] text-[#9ba4b7]">{{ fact.label }}</p>
                              <p class="mt-1 text-[14px] font-medium text-[#293857]">{{ fact.value }}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                <section id="scenic-section-inclusions" class="scroll-mt-32 border-t border-[#eef2f6] pt-10">
                  <div class="grid gap-8 lg:grid-cols-[56px_minmax(0,1fr)]">
                    <div class="hidden items-start justify-center lg:flex">
                      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f2fbfb] text-[#19b7b1]">
                        <Check class="h-5 w-5" />
                      </div>
                    </div>

                    <div>
                      <div class="space-y-8">
                        <div>
                          <h2 class="text-[18px] font-semibold text-[#22304f]">Itinerary</h2>
                          <div class="mt-6 space-y-4">
                            <article
                              v-for="day in detail.itineraryDays"
                              :key="day.id"
                              class="overflow-hidden rounded-[22px] border border-[#edf1f5] bg-[#fbfcfd]"
                            >
                              <button
                                type="button"
                                class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                                @click="toggleDay(day.id)"
                              >
                                <div class="flex items-center gap-3">
                                  <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#19b7b1] text-[12px] font-semibold text-white">
                                    {{ day.title.split(' ')[1] }}
                                  </span>
                                  <div>
                                    <p class="text-[14px] font-semibold text-[#22304f]">{{ day.title }}</p>
                                    <p class="mt-1 text-[12px] text-[#8d98ab]">{{ day.summary.slice(0, 42) }}...</p>
                                  </div>
                                </div>
                                <ChevronDown
                                  class="h-4 w-4 shrink-0 text-[#96a0b4] transition"
                                  :class="openDayIds.includes(day.id) ? 'rotate-180' : ''"
                                />
                              </button>

                              <div v-if="openDayIds.includes(day.id)" class="border-t border-[#eef2f6] px-5 py-5">
                                <p class="text-[14px] leading-7 text-[#68748b]">
                                  {{ day.summary }}
                                </p>

                                <div
                                  v-if="day.media"
                                  class="mt-5 grid gap-4 md:grid-cols-[220px_minmax(0,1fr)]"
                                >
                                  <img
                                    :src="day.media.src"
                                    :alt="day.media.alt"
                                    class="h-[150px] w-full rounded-[18px] object-cover"
                                  />
                                  <div class="flex items-end">
                                    <button
                                      type="button"
                                      class="inline-flex items-center gap-2 rounded-full border border-[#dce6ee] bg-white px-4 py-2 text-[13px] font-medium text-[#516079] transition hover:border-[#19b7b1] hover:text-[#19b7b1]"
                                    >
                                      <MapPin class="h-4 w-4" />
                                      <span>{{ day.mapLabel }}</span>
                                    </button>
                                  </div>
                                </div>

                                <div
                                  v-if="day.accommodation"
                                  class="mt-6 rounded-[22px] border border-[#edf1f5] bg-white px-5 py-5"
                                >
                                  <div class="flex items-center gap-2 text-[#22304f]">
                                    <Sparkles class="h-4.5 w-4.5 text-[#19b7b1]" />
                                    <h3 class="text-[15px] font-semibold">浣忓瀹夋帓</h3>
                                  </div>
                                  <p class="mt-3 text-[14px] leading-7 text-[#68748b]">
                                    {{ day.accommodation.description }}
                                  </p>
                                  <div class="mt-4 grid gap-3 sm:grid-cols-3 text-[13px] text-[#516079]">
                                    <div class="rounded-2xl bg-[#f7f9fb] px-4 py-3">{{ day.accommodation.sharedRoom }}</div>
                                    <div class="rounded-2xl bg-[#f7f9fb] px-4 py-3">{{ day.accommodation.doubleRoom }}</div>
                                    <div class="rounded-2xl bg-[#f7f9fb] px-4 py-3">{{ day.accommodation.singleRoom }}</div>
                                  </div>
                                  <div class="mt-4 grid gap-3 sm:grid-cols-3">
                                    <img
                                      v-for="room in day.accommodation.roomImages"
                                      :key="room.alt"
                                      :src="room.src"
                                      :alt="room.alt"
                                      class="h-[100px] w-full rounded-[16px] object-cover"
                                    />
                                  </div>
                                </div>
                              </div>
                            </article>
                          </div>
                        </div>

                        <div class="grid gap-6 xl:grid-cols-2">
                          <div class="rounded-[24px] border border-[#edf1f5] bg-white px-5 py-5">
                            <h3 class="text-[16px] font-semibold text-[#22304f]">璐圭敤鍖呭惈</h3>
                            <ul class="mt-4 space-y-3">
                              <li
                                v-for="item in detail.includes"
                                :key="item"
                                class="flex items-start gap-3 text-[14px] leading-6 text-[#617089]"
                              >
                                <Check class="mt-1 h-4 w-4 shrink-0 text-[#19b7b1]" />
                                <span>{{ item }}</span>
                              </li>
                            </ul>
                          </div>

                          <div class="rounded-[24px] border border-[#edf1f5] bg-white px-5 py-5">
                            <h3 class="text-[16px] font-semibold text-[#22304f]">璐圭敤涓嶅惈</h3>
                            <ul class="mt-4 space-y-3">
                              <li
                                v-for="item in detail.excludes"
                                :key="item"
                                class="flex items-start gap-3 text-[14px] leading-6 text-[#617089]"
                              >
                                <X class="mt-1 h-4 w-4 shrink-0 text-[#ff6b6b]" />
                                <span>{{ item }}</span>
                              </li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                <section id="scenic-section-reviews" class="scroll-mt-32 border-t border-[#eef2f6] pt-10">
                  <div class="grid gap-8 lg:grid-cols-[56px_minmax(0,1fr)]">
                    <div class="hidden items-start justify-center lg:flex">
                      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f2fbfb] text-[#19b7b1]">
                        <Star class="h-5 w-5" />
                      </div>
                    </div>

                    <div>
                      <h2 class="text-[18px] font-semibold text-[#22304f]">鐢ㄦ埛璇勪环</h2>
                      <div class="mt-6 space-y-4">
                        <article
                          v-for="review in detail.reviews"
                          :key="review.id"
                          class="rounded-[24px] border border-[#edf1f5] bg-[#fbfcfd] px-5 py-5"
                        >
                          <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                            <div class="flex items-center gap-3">
                              <img :src="review.avatar" :alt="review.author" class="h-12 w-12 rounded-full object-cover" />
                              <div>
                                <p class="text-[15px] font-semibold text-[#22304f]">{{ review.author }}</p>
                                <p class="mt-1 text-[12px] text-[#95a0b3]">{{ review.dateLabel }}</p>
                              </div>
                            </div>

                            <div class="flex items-center gap-1 text-[#f7aa19]">
                              <Star
                                v-for="index in 5"
                                :key="index"
                                class="h-4 w-4"
                                :fill="index <= review.rating ? 'currentColor' : 'none'"
                                :class="index <= review.rating ? 'text-[#f7aa19]' : 'text-[#d6dde8]'"
                              />
                            </div>
                          </div>

                          <h3 class="mt-4 text-[16px] font-semibold text-[#22304f]">{{ review.title }}</h3>
                          <p class="mt-3 text-[14px] leading-7 text-[#68748b]">{{ review.content }}</p>
                        </article>
                      </div>
                    </div>
                  </div>
                </section>

                <section id="scenic-section-faq" class="scroll-mt-32 border-t border-[#eef2f6] pt-10">
                  <div class="grid gap-8 lg:grid-cols-[56px_minmax(0,1fr)]">
                    <div class="hidden items-start justify-center lg:flex">
                      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f2fbfb] text-[#19b7b1]">
                        <CircleHelp class="h-5 w-5" />
                      </div>
                    </div>

                    <div>
                      <h2 class="text-[18px] font-semibold text-[#22304f]">甯歌闂</h2>
                      <div class="mt-6 space-y-3">
                        <article
                          v-for="faq in detail.faqs"
                          :key="faq.id"
                          class="overflow-hidden rounded-[20px] border border-[#edf1f5] bg-[#fbfcfd]"
                        >
                          <button
                            type="button"
                            class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                            @click="toggleFaq(faq.id)"
                          >
                            <span class="text-[14px] font-medium text-[#2c3a59]">{{ faq.question }}</span>
                            <ChevronDown
                              class="h-4 w-4 shrink-0 text-[#96a0b4] transition"
                              :class="openFaqIds.includes(faq.id) ? 'rotate-180' : ''"
                            />
                          </button>

                          <div v-if="openFaqIds.includes(faq.id)" class="border-t border-[#eef2f6] px-5 py-4 text-[14px] leading-7 text-[#68748b]">
                            {{ faq.answer }}
                          </div>
                        </article>
                      </div>
                    </div>
                  </div>
                </section>

                <section id="scenic-section-essential" class="scroll-mt-32 border-t border-[#eef2f6] pt-10">
                  <div class="grid gap-8 lg:grid-cols-[56px_minmax(0,1fr)]">
                    <div class="hidden items-start justify-center lg:flex">
                      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f2fbfb] text-[#19b7b1]">
                        <CalendarDays class="h-5 w-5" />
                      </div>
                    </div>

                    <div>
                      <h2 class="text-[18px] font-semibold text-[#22304f]">鍑鸿椤荤煡</h2>
                      <div class="mt-6 grid gap-4 sm:grid-cols-3">
                        <div
                          v-for="item in detail.essentialInfo"
                          :key="item"
                          class="rounded-[22px] border border-[#edf1f5] bg-[#fbfcfd] px-5 py-5 text-[14px] leading-7 text-[#68748b]"
                        >
                          {{ item }}
                        </div>
                      </div>
                    </div>
                  </div>
                </section>
              </div>

              <section class="mt-12">
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <h2 class="text-[28px] font-semibold tracking-[-0.03em] text-[#22304f]">鐩镐技鏅偣</h2>
                    <p class="mt-2 text-[14px] text-[#8690a3]">继续沿着同一类场景浏览，后续可替换为真实推荐数据。</p>
                  </div>
                  <router-link
                    :to="{ name: 'scenic-search', query: route.query }"
                    class="inline-flex items-center rounded-full bg-[#21bbb4] px-5 py-3 text-[13px] font-semibold text-white shadow-[0_14px_26px_rgba(33,187,180,0.24)] transition hover:bg-[#18a59f]"
                  >
                    鏌ョ湅鍏ㄩ儴
                  </router-link>
                </div>

                <div class="mt-8 grid gap-5 lg:grid-cols-3">
                  <router-link
                    v-for="tour in detail.similarTours"
                    :key="tour.id"
                    :to="{ name: 'scenic-detail', params: { id: tour.id }, query: route.query }"
                    class="group overflow-hidden rounded-[24px] border border-[#ebeff4] bg-white shadow-[0_18px_40px_rgba(15,23,42,0.05)] transition hover:-translate-y-1 hover:shadow-[0_24px_46px_rgba(15,23,42,0.1)]"
                  >
                    <div class="relative h-[220px] overflow-hidden">
                      <img :src="tour.image" :alt="tour.title" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
                      <div class="absolute inset-0 bg-gradient-to-t from-[#10213a]/72 via-transparent to-transparent"></div>
                      <span
                        v-if="tour.badgeText"
                        class="absolute right-4 top-4 rounded-full bg-[#ffb361] px-3 py-1 text-[10px] font-semibold text-white"
                      >
                        {{ tour.badgeText }}
                      </span>
                      <div class="absolute bottom-4 left-4 right-4 flex items-end justify-between gap-3">
                        <div>
                          <p class="text-[12px] text-white/72">{{ tour.subtitle }}</p>
                          <p class="mt-2 text-[30px] font-semibold leading-none text-white">{{ tour.price }}</p>
                        </div>
                        <span class="rounded-full bg-[#21bbb4] px-4 py-2 text-[12px] font-semibold text-white">
                          鏌ョ湅璇︽儏
                        </span>
                      </div>
                    </div>
                    <div class="px-5 pb-5 pt-4">
                      <h3 class="text-[19px] font-semibold text-[#22304f]">{{ tour.title }}</h3>
                      <p class="mt-2 text-[13px] leading-6 text-[#8690a3]">
                        鍚屼竴妯℃澘涓嬬殑鍙︿竴鏉＄ず渚嬫櫙鐐硅鎯咃紝鍚庣画鍙洿鎺ユ浛鎹负鐪熷疄鎺ㄨ崘鍐呭銆?                      </p>
                    </div>
                  </router-link>
                </div>
              </section>
            </div>

            <aside class="lg:sticky lg:top-28 lg:self-start">
              <div class="rounded-[28px] border border-[#edf1f5] bg-white px-5 py-5 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#ff7d72]">棰勮淇℃伅</p>
                    <p class="mt-3 text-[34px] font-semibold leading-none tracking-[-0.04em] text-[#22304f]">
                      {{ detail.price.current }}
                    </p>
                    <p class="mt-2 text-[12px] text-[#9aa3b5]">
                      <span v-if="detail.price.previous" class="mr-2 line-through">{{ detail.price.previous }}</span>
                      姣忎汉璧?                    </p>
                  </div>
                  <span
                    v-if="detail.price.discountLabel"
                    class="rounded-full bg-[#ecfbfa] px-3 py-1 text-[11px] font-semibold text-[#19b7b1]"
                  >
                    {{ detail.price.discountLabel }}
                  </span>
                </div>

                <div class="mt-6 space-y-4">
                  <label class="block">
                    <span class="mb-2 block text-[12px] font-medium text-[#7f899d]">鍑哄彂鏃ユ湡</span>
                    <select
                      v-model="selectedDate"
                      class="h-12 w-full rounded-[16px] border border-[#e6edf3] bg-[#fbfcfd] px-4 text-[14px] text-[#33415f] outline-none transition focus:border-[#19b7b1]"
                    >
                      <option v-for="date in detail.bookingPanel.dateOptions" :key="date" :value="date">
                        {{ date }}
                      </option>
                    </select>
                  </label>

                  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                    <label class="block">
                      <span class="mb-2 block text-[12px] font-medium text-[#7f899d]">鍑鸿浜烘暟</span>
                      <div class="flex h-12 items-center justify-between rounded-[16px] border border-[#e6edf3] bg-[#fbfcfd] px-4">
                        <span class="text-[14px] text-[#33415f]">{{ travelerCount }} 人</span>
                        <div class="flex items-center gap-2">
                          <button
                            type="button"
                            class="inline-flex h-7 w-7 items-center justify-center rounded-full border border-[#dce6ee] text-[#53627d]"
                            @click="travelerCount = Math.max(1, travelerCount - 1)"
                          >
                            -
                          </button>
                          <button
                            type="button"
                            class="inline-flex h-7 w-7 items-center justify-center rounded-full border border-[#dce6ee] text-[#53627d]"
                            @click="travelerCount += 1"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </label>

                    <label class="block">
                      <span class="mb-2 block text-[12px] font-medium text-[#7f899d]">濂楅閫夋嫨</span>
                      <select
                        v-model="selectedPackage"
                        class="h-12 w-full rounded-[16px] border border-[#e6edf3] bg-[#fbfcfd] px-4 text-[14px] text-[#33415f] outline-none transition focus:border-[#19b7b1]"
                      >
                        <option v-for="option in packageOptions" :key="option" :value="option">
                          {{ option }}
                        </option>
                      </select>
                    </label>
                  </div>
                </div>

                <button
                  type="button"
                  class="mt-6 inline-flex h-12 w-full items-center justify-center rounded-full bg-gradient-to-r from-[#ff8447] to-[#ff4f8e] text-[14px] font-semibold text-white shadow-[0_16px_28px_rgba(255,102,127,0.24)] transition hover:translate-y-[-1px]"
                >
                  鏌ョ湅鍙璁㈡€?                </button>

                <div class="mt-5 rounded-[18px] bg-[#f8fafc] px-4 py-4">
                  <p class="text-[12px] font-medium text-[#6f7c92]">{{ detail.bookingPanel.contactHint }}</p>
                  <button
                    type="button"
                    class="mt-4 inline-flex h-10 w-full items-center justify-center rounded-full border border-[#d9e4ec] bg-white text-[13px] font-medium text-[#50607a] transition hover:border-[#19b7b1] hover:text-[#19b7b1]"
                  >
                    鍜ㄨ琛岀▼椤鹃棶
                  </button>
                </div>

                <p class="mt-4 text-[11px] leading-5 text-[#95a0b3]">
                  {{ detail.bookingPanel.reserveNote }}
                </p>
              </div>
            </aside>
          </section>
        </template>

        <template v-else>
          <section class="rounded-[30px] border border-dashed border-[#d8e0ea] bg-white px-8 py-16 text-center shadow-[0_18px_48px_rgba(15,23,42,0.04)]">
            <div class="mx-auto max-w-[520px]">
              <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#eef7f8] text-[#19b7b1]">
                <MapPin class="h-7 w-7" />
              </div>
              <h1 class="mt-6 text-[30px] font-semibold tracking-[-0.03em] text-[#22304f]">鏅偣鏆傛湭鎵惧埌</h1>
              <p class="mt-4 text-[15px] leading-7 text-[#71809a]">
                褰撳墠璺敱娌℃湁鍖归厤鍒板搴旂殑绀轰緥鏅偣鏁版嵁銆傚悗缁帴鍏ョ湡瀹炴帴鍙ｅ悗锛岃繖閲屼細澶嶇敤鍚屼竴濂楄鎯呮ā鏉垮睍绀虹湡瀹炴櫙鐐瑰唴瀹广€?              </p>
              <router-link
                :to="{ name: 'scenic-search', query: route.query }"
                class="mt-8 inline-flex items-center rounded-full bg-[#20bcb5] px-5 py-3 text-[14px] font-semibold text-white shadow-[0_16px_28px_rgba(32,188,181,0.24)] transition hover:bg-[#17a49d]"
              >
                杩斿洖鎼滅储椤?              </router-link>
            </div>
          </section>
        </template>
      </div>
    </main>

    <Footer variant="white" />
  </div>
</template>

