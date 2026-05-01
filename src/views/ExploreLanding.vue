<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, ArrowLeft, ArrowRight, Instagram, MapPin, Twitter } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import ScrollRevealText from '@/components/animations/ScrollRevealText.vue'
import { travelDiscoveryService, type SpotItem } from '@/services/travelDiscoveryService'
import {
  exploreActivities,
  exploreHero,
  exploreHeroSlides,
  explorePartners,
  explorePrinciples,
} from '@/data/exploreLanding'

const router = useRouter()
const scrollY = ref(0)
const heroEntered = ref(false)
const activityStart = ref(0)
const currentHeroSlide = ref(0)
const fallbackCardImage = exploreActivities[0].image
const fallbackWideImage = exploreHero.backgroundImage
const fallbackAvatarImage = '/founder-avatar.jpg'
let heroAutoplayTimer: number | null = null

type ScenicBookingCard = {
  spot_key: string
  name: string
  city: string
  price: string
  rating: string
  image: string
}

const SCENIC_BOOKING_IMAGE_BY_NAME: Record<string, string> = {
  厦门大学: '/discovery-images/xiamen-university.jpg',
  神农顶景区: '/discovery-images/shennongding.jpg',
  皇城相府: '/discovery-images/huangcheng-xiangfu.jpg',
}

const SCENIC_BOOKING_PREFERRED_NAMES = ['厦门大学', '神农顶景区', '皇城相府']

const testimonialCards = [
  {
    name: '林清和',
    role: '独立摄影师',
    quote: '不是那种把景点塞进清单的路线，更像有人已经替你筛掉冗余，只留下真正值得停留的地方。',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=300&auto=format&fit=crop',
  },
  {
    name: '周以衡',
    role: '旅行写作者',
    quote: '页面节奏很克制，第一次读展开的旅途像翻开一本真正的旅行杂志，让人愿意慢下来决定下一站。',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=300&auto=format&fit=crop',
  },
  {
    name: '陈知予',
    role: '山海路线策划',
    quote: '它没有急着告诉你买什么，而是先帮你确定想去哪、想过怎样的一次停留。',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=300&auto=format&fit=crop',
  },
]

const scenicBookingFallbackSpots: SpotItem[] = [
  {
    id: 'kb-1884',
    spot_key: 'kb-1884',
    source_type: 'knowledge_base',
    source_id: '1884',
    name: '厦门大学',
    city: '福建',
    rating: 5,
    price: 0.19,
    description: '',
    cover_image: '',
    tags: [],
    recommendation_reason: '',
    in_itinerary: false,
  },
  {
    id: 'kb-1558',
    spot_key: 'kb-1558',
    source_type: 'knowledge_base',
    source_id: '1558',
    name: '神农顶景区',
    city: '湖北',
    rating: 5,
    price: 0.5,
    description: '',
    cover_image: '',
    tags: [],
    recommendation_reason: '',
    in_itinerary: false,
  },
  {
    id: 'kb-827',
    spot_key: 'kb-827',
    source_type: 'knowledge_base',
    source_id: '827',
    name: '皇城相府',
    city: '山西',
    rating: 5,
    price: 0.7,
    description: '',
    cover_image: '',
    tags: [],
    recommendation_reason: '',
    in_itinerary: false,
  },
]

const formatScenicBookingPrice = (spot: Pick<SpotItem, 'city' | 'price'>) =>
  spot.price > 0 ? `${spot.city} · ¥${spot.price.toFixed(2)}` : `${spot.city} · 在线预订`

const formatScenicBookingRating = (rating: number) => '★'.repeat(Math.max(1, Math.min(5, Math.round(rating || 0))))

const buildScenicBookingCards = (spots: SpotItem[]): ScenicBookingCard[] =>
  spots.slice(0, 3).map((spot) => ({
    spot_key: spot.spot_key,
    name: spot.name,
    city: spot.city,
    price: formatScenicBookingPrice(spot),
    rating: formatScenicBookingRating(spot.rating),
    image: SCENIC_BOOKING_IMAGE_BY_NAME[spot.name] || spot.cover_image || fallbackCardImage,
  }))

const pickScenicBookingSpots = (spots: SpotItem[]) => {
  const picked: SpotItem[] = []
  const usedSpotKeys = new Set<string>()

  for (const name of SCENIC_BOOKING_PREFERRED_NAMES) {
    const matched = spots.find((spot) => spot.name === name && !usedSpotKeys.has(spot.spot_key))
    if (!matched) {
      continue
    }
    picked.push(matched)
    usedSpotKeys.add(matched.spot_key)
  }

  for (const spot of spots) {
    if (picked.length >= 3) {
      break
    }
    if (usedSpotKeys.has(spot.spot_key)) {
      continue
    }
    picked.push(spot)
    usedSpotKeys.add(spot.spot_key)
  }

  return picked.slice(0, 3)
}

const scenicBookingCards = ref<ScenicBookingCard[]>(buildScenicBookingCards(scenicBookingFallbackSpots))
const scenicBookingCatalogSpots = ref<SpotItem[]>([...scenicBookingFallbackSpots])

type BookingPanel = 'date' | 'province' | 'spot'

const ALL_BOOKING_PROVINCES = '全部'
const ALL_BOOKING_SPOTS = '全部'

const bookingDateOptions = ['11月3日 周二', '11月4日 周三', '11月5日 周四', '11月6日 周五', '11月7日 周六']
const bookingProvinceOptions = computed(() => [
  ALL_BOOKING_PROVINCES,
  ...Array.from(new Set(scenicBookingCatalogSpots.value.map((spot) => spot.city?.trim()).filter(Boolean))),
])
const bookingSpotOptionsByProvince = computed<Record<string, string[]>>(() =>
  scenicBookingCatalogSpots.value.reduce<Record<string, string[]>>((result, spot) => {
    const city = spot.city?.trim()
    const name = spot.name?.trim()

    if (!city || !name) {
      return result
    }

    const current = result[city] || []
    if (!current.includes(name)) {
      current.push(name)
    }
    result[city] = current
    return result
  }, {}),
)

const selectedBookingDate = ref(bookingDateOptions[0])
const selectedBookingProvince = ref('')
const selectedBookingSpot = ref('')
const activeBookingPanel = ref<BookingPanel | null>(null)

const allBookingSpotOptions = computed(() =>
  Array.from(new Set(scenicBookingCatalogSpots.value.map((spot) => spot.name?.trim()).filter(Boolean))),
)
const bookingSpotOptions = computed(() =>
  [
    ALL_BOOKING_SPOTS,
    ...(selectedBookingProvince.value === ALL_BOOKING_PROVINCES
      ? allBookingSpotOptions.value
      : (bookingSpotOptionsByProvince.value[selectedBookingProvince.value] ?? [])),
  ],
)
const committedBookingDateValue = ref(new Date(2026, 10, 17))
const draftBookingDateValue = ref(new Date(2026, 10, 17))
const visibleBookingMonth = ref(new Date(2026, 10, 1))
const bookingWeekdayLabels = ['一', '二', '三', '四', '五', '六', '日']

const formatBookingDateLabel = (date: Date) => {
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()]
  return `${date.getMonth() + 1}月 ${date.getDate()}日 ${week}`
}

selectedBookingDate.value = formatBookingDateLabel(committedBookingDateValue.value)

const bookingMonthLabel = computed(() => {
  const year = visibleBookingMonth.value.getFullYear()
  const month = String(visibleBookingMonth.value.getMonth() + 1).padStart(2, '0')
  return `${year} - ${month}`
})

const bookingCalendarCells = computed(() => {
  const monthStart = new Date(visibleBookingMonth.value.getFullYear(), visibleBookingMonth.value.getMonth(), 1)
  const startOffset = (monthStart.getDay() + 6) % 7
  const gridStart = new Date(monthStart)
  gridStart.setDate(monthStart.getDate() - startOffset)

  return Array.from({ length: 35 }, (_, index) => {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + index)

    return {
      key: `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`,
      date,
      label: date.getDate(),
      inCurrentMonth: date.getMonth() === visibleBookingMonth.value.getMonth(),
      isSelected:
        date.getFullYear() === draftBookingDateValue.value.getFullYear() &&
        date.getMonth() === draftBookingDateValue.value.getMonth() &&
        date.getDate() === draftBookingDateValue.value.getDate(),
    }
  })
})

const activeHero = computed(() => exploreHeroSlides[currentHeroSlide.value])
const heroStripDestinations = computed(() =>
  currentHeroSlide.value === 0
    ? [
        { name: 'Trondheim', subtitle: 'Plan a trip' },
        { name: 'Geirangerfjord', subtitle: 'Plan a trip' },
        { name: 'Lofoten', subtitle: 'Plan a trip' },
      ]
    : activeHero.value.destinations,
)

const visibleActivities = computed(() => {
  const result = []
  for (let offset = 0; offset < 4; offset += 1) {
    result.push(exploreActivities[(activityStart.value + offset) % exploreActivities.length])
  }
  return result
})

const handleScroll = () => {
  scrollY.value = window.scrollY
}

const rotateActivities = (direction: 1 | -1) => {
  const next = activityStart.value + direction
  activityStart.value = (next + exploreActivities.length) % exploreActivities.length
}

const nextHeroSlide = () => {
  currentHeroSlide.value = (currentHeroSlide.value + 1) % exploreHeroSlides.length
}

const toggleBookingPanel = (panel: BookingPanel) => {
  activeBookingPanel.value = activeBookingPanel.value === panel ? null : panel

  if (activeBookingPanel.value === 'date') {
    draftBookingDateValue.value = new Date(committedBookingDateValue.value)
    visibleBookingMonth.value = new Date(
      committedBookingDateValue.value.getFullYear(),
      committedBookingDateValue.value.getMonth(),
      1,
    )
  }
}

const selectBookingDate = (option: string) => {
  selectedBookingDate.value = option
  activeBookingPanel.value = null
}

const goToPreviousBookingMonth = () => {
  visibleBookingMonth.value = new Date(
    visibleBookingMonth.value.getFullYear(),
    visibleBookingMonth.value.getMonth() - 1,
    1,
  )
}

const goToNextBookingMonth = () => {
  visibleBookingMonth.value = new Date(
    visibleBookingMonth.value.getFullYear(),
    visibleBookingMonth.value.getMonth() + 1,
    1,
  )
}

const pickBookingCalendarDate = (date: Date) => {
  draftBookingDateValue.value = new Date(date)
}

const confirmBookingCalendarDate = () => {
  committedBookingDateValue.value = new Date(draftBookingDateValue.value)
  selectedBookingDate.value = formatBookingDateLabel(committedBookingDateValue.value)
  activeBookingPanel.value = null
}

const selectBookingProvince = (option: string) => {
  selectedBookingProvince.value = option
  const nextSpots =
    option === ALL_BOOKING_PROVINCES
      ? [ALL_BOOKING_SPOTS, ...allBookingSpotOptions.value]
      : [ALL_BOOKING_SPOTS, ...(bookingSpotOptionsByProvince.value[option] ?? [])]
  if (!nextSpots.includes(selectedBookingSpot.value)) {
    selectedBookingSpot.value = nextSpots[0] ?? ''
  }
  activeBookingPanel.value = null
}

const selectBookingSpot = (option: string) => {
  selectedBookingSpot.value = option
  activeBookingPanel.value = null
}

const goToScenicSearch = () => {
  router.push({
    name: 'scenic-search',
    query: {
      date: selectedBookingDate.value,
      province: selectedBookingProvince.value === ALL_BOOKING_PROVINCES ? undefined : selectedBookingProvince.value,
      spot: selectedBookingSpot.value === ALL_BOOKING_SPOTS ? undefined : selectedBookingSpot.value,
    },
  })
}

const syncScenicBookingSelections = () => {
  const provinces = bookingProvinceOptions.value
  if (!provinces.length) {
    selectedBookingProvince.value = ''
    selectedBookingSpot.value = ''
    return
  }

  if (!provinces.includes(selectedBookingProvince.value)) {
    selectedBookingProvince.value = provinces[0]
  }

  const nextSpots =
    selectedBookingProvince.value === ALL_BOOKING_PROVINCES
      ? [ALL_BOOKING_SPOTS, ...allBookingSpotOptions.value]
      : [ALL_BOOKING_SPOTS, ...(bookingSpotOptionsByProvince.value[selectedBookingProvince.value] ?? [])]
  if (!nextSpots.includes(selectedBookingSpot.value)) {
    selectedBookingSpot.value = nextSpots[0] ?? ''
  }
}

const loadScenicBookingData = async () => {
  try {
    const response = await travelDiscoveryService.listSpots({ limit: 80, sort: 'recommended' })
    scenicBookingCatalogSpots.value = response.items.length ? response.items : [...scenicBookingFallbackSpots]
    const nextSpots = pickScenicBookingSpots(response.items)
    if (!nextSpots.length) {
      syncScenicBookingSelections()
      return
    }
    scenicBookingCards.value = buildScenicBookingCards(nextSpots)
    syncScenicBookingSelections()
  } catch (error) {
    console.error('Failed to load scenic booking data:', error)
    scenicBookingCatalogSpots.value = [...scenicBookingFallbackSpots]
    scenicBookingCards.value = buildScenicBookingCards(scenicBookingFallbackSpots)
    syncScenicBookingSelections()
  }
}

const applyFallbackImage = (event: Event, fallbackSrc: string) => {
  const target = event.target as HTMLImageElement | null
  if (!target || target.dataset.fallbackApplied === 'true') {
    return
  }
  target.dataset.fallbackApplied = 'true'
  target.src = fallbackSrc
}

const handleDocumentPointerDown = (event: PointerEvent) => {
  const target = event.target as HTMLElement | null
  if (!target?.closest('[data-booking-field]')) {
    activeBookingPanel.value = null
  }
}

onMounted(async () => {
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  handleScroll()
  syncScenicBookingSelections()
  await loadScenicBookingData()
  heroAutoplayTimer = window.setInterval(() => {
    nextHeroSlide()
  }, 5200)
  requestAnimationFrame(() => {
    window.setTimeout(() => {
      heroEntered.value = true
    }, 80)
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  if (heroAutoplayTimer !== null) {
    window.clearInterval(heroAutoplayTimer)
  }
})
</script>

<template>
  <div class="min-h-screen overflow-x-hidden bg-white text-[#2d2f33] selection:bg-[#ddb977] selection:text-[#18252c]">
    <Navigation variant="light">
      <template #logo>
        <router-link
          to="/"
          class="font-bold text-4xl tracking-wide transition-colors duration-300"
          :class="scrollY > 48 ? 'text-[#182128]' : 'text-white'"
          style="font-family: 'PangMenZhengDao', serif;"
        >
          椿天社
        </router-link>
      </template>
    </Navigation>

    <main>
      <section id="hero-stage" class="relative min-h-screen overflow-hidden bg-[#10212b]">
        <div class="absolute inset-0">
          <div
            v-for="(slide, index) in exploreHeroSlides"
            :key="`${slide.titleMain}-${index}`"
            class="absolute inset-0 bg-cover bg-center transition-[opacity,transform] duration-[1200ms]"
            :class="index === currentHeroSlide ? 'opacity-100 scale-[1.04]' : 'pointer-events-none opacity-0 scale-[1.08]'"
            :style="{
              backgroundImage: `url('${index === 0 ? 'https://images.unsplash.com/photo-1511497584788-876760111969?q=80&w=2200&auto=format&fit=crop' : slide.backgroundImage}')`,
              transform: index === currentHeroSlide ? `translateY(${scrollY * 0.18}px) scale(1.04)` : undefined,
            }"
          >
            <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(240,218,182,0.26),rgba(95,113,108,0.14),rgba(12,32,32,0.28),rgba(5,14,15,0.56))]" />
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_18%_10%,rgba(255,232,198,0.28),transparent_22%),radial-gradient(circle_at_84%_18%,rgba(255,190,120,0.16),transparent_20%)]" />
          </div>
        </div>

        <div class="pointer-events-none absolute left-8 top-1/2 z-20 hidden -translate-y-1/2 lg:flex">
          <div class="flex flex-col items-center gap-8 text-white">
            <div class="hero-side-label text-lg font-bold tracking-wide text-white">关注我们</div>
            <div class="flex flex-col gap-4">
              <a href="#" class="pointer-events-auto text-white transition-colors hover:text-white/80">
                <Instagram class="h-6 w-6" />
              </a>
              <a href="#" class="pointer-events-auto text-white transition-colors hover:text-white/80">
                <Twitter class="h-6 w-6" />
              </a>
            </div>
          </div>
        </div>

        <div class="pointer-events-none absolute right-0 top-1/2 z-20 hidden -translate-y-1/2 lg:block">
          <div class="pointer-events-auto px-8">
            <button
              type="button"
              class="relative h-[240px] w-[3px] overflow-hidden rounded-full bg-white/20"
              aria-label="切换首屏背景"
              @click="nextHeroSlide"
            >
              <div
                class="absolute left-0 top-0 w-full bg-white transition-transform duration-500 ease-out"
                :style="{ height: `${100 / exploreHeroSlides.length}%`, transform: `translateY(${currentHeroSlide * 100}%)` }"
              ></div>
            </button>
          </div>
        </div>

        <div class="pointer-events-none absolute bottom-10 right-10 z-20 hidden lg:flex">
          <div class="flex items-end gap-2 text-right text-white">
            <div class="text-[56px] font-semibold leading-none">{{ String(currentHeroSlide + 1).padStart(2, '0') }}</div>
            <div class="pb-1 text-xs tracking-[0.34em] text-white/62">/ {{ String(exploreHeroSlides.length).padStart(2, '0') }}</div>
          </div>
        </div>

        <div class="relative z-10 flex min-h-screen flex-col pb-10 pt-32 lg:pt-48">
          <div class="relative -mt-2 flex flex-col">
            <div class="container mx-auto flex max-w-6xl flex-col items-start px-4 text-left text-white lg:px-20">
              <div class="hero-reveal mb-8 flex items-center gap-4" :class="{ 'is-visible': heroEntered }">
                <div class="h-[2px] w-[72px] bg-accent"></div>
                <span class="text-sm font-semibold uppercase tracking-[0.45em] text-white drop-shadow-[0_6px_18px_rgba(0,0,0,0.28)]">Travel Discovery</span>
              </div>

              <h1
                class="hero-reveal hero-reveal-title max-w-5xl font-serif text-5xl leading-tight text-white drop-shadow-[0_10px_30px_rgba(0,0,0,0.22)] md:text-7xl lg:text-[88px]"
                :class="{ 'is-visible': heroEntered }"
              >
                在清透山谷与湖光之间
                <br />
                找到更值得加入行程的一站
              </h1>

              <p
                class="hero-reveal hero-reveal-copy mt-8 max-w-2xl text-base leading-8 text-white drop-shadow-[0_6px_20px_rgba(0,0,0,0.22)] md:text-lg"
                :class="{ 'is-visible': heroEntered }"
              >
                这不是一个把所有景点堆满页面的目录页，而是一条经过筛选后的发现流。游客先看高质量推荐，登录后再叠加你的兴趣与行程偏好。
              </p>

              <div
                class="hero-reveal mt-10 flex items-center gap-4 font-medium text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.22)] animate-bounce"
                :class="{ 'is-visible': heroEntered }"
              >
                <span>向下浏览推荐与筛选</span>
                <ArrowDown :size="20" />
              </div>
            </div>
          </div>

          <div class="flex-1"></div>

          <div class="hidden">
            <div class="hero-reveal" :class="{ 'is-visible': heroEntered }">
              <p class="text-[15px] font-medium tracking-[0.85em] text-white/72">{{ activeHero.eyebrow }}</p>
            </div>
            <h1
              class="hero-reveal mt-5 text-[100px] font-semibold leading-[0.88] sm:text-[132px] lg:text-[178px]"
              :class="{ 'is-visible': heroEntered }"
            >
              {{ activeHero.titleMain }}
            </h1>
            <p
              class="hero-reveal mx-auto mt-7 max-w-[760px] text-[16px] leading-8 text-white/82"
              :class="{ 'is-visible': heroEntered }"
            >
              {{ activeHero.description }}
            </p>
          </div>

          <div id="destinations" class="mx-auto -mt-2 w-full max-w-[980px] px-4 md:px-0">
            <div class="relative overflow-hidden rounded-[2px] bg-[rgba(84,90,92,0.12)] shadow-[0_8px_30px_rgba(0,0,0,0.08)] backdrop-blur-[8px]">
              <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.035),rgba(255,255,255,0.008)_28%,rgba(0,0,0,0.035)_100%)]" />
              <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.025),rgba(255,255,255,0.006)_18%,rgba(255,255,255,0)_42%,rgba(255,255,255,0)_58%,rgba(255,255,255,0.006)_82%,rgba(255,255,255,0.02))]" />

              <div class="relative z-10 grid min-h-[62px] md:grid-cols-3">
                <article
                  v-for="(destination, index) in heroStripDestinations"
                  :key="destination.name"
                  class="flex items-start gap-4 px-10 py-7 text-white"
                  :class="index < heroStripDestinations.length - 1 ? 'border-r border-white/[0.045]' : ''"
                >
                  <MapPin class="mt-0.5 h-5 w-5 shrink-0 text-white/[0.16]" />
                  <div>
                    <h3 class="text-[16px] font-semibold tracking-[-0.02em] text-white">{{ destination.name }}</h3>
                    <p class="mt-1 text-[12px] text-white/[0.28]">{{ destination.subtitle }}</p>
                  </div>
                </article>
              </div>
            </div>
          </div>
          <div class="hidden mt-14 grid gap-5 lg:grid-cols-[repeat(3,minmax(0,1fr))_210px]">
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">出行日期</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('date')"
              >
                <span>{{ selectedBookingDate }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'date' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'date'"
                  class="booking-popover-panel booking-calendar absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[26px] bg-white px-4 pb-4 pt-3 shadow-[0_24px_60px_rgba(24,33,40,0.16)]"
                  @click.stop
                >
                  <div class="mx-auto mb-4 h-[6px] w-[48px] rounded-full bg-[#1e4f46]"></div>
                  <div class="flex items-center justify-between px-2">
                    <button type="button" class="booking-calendar-nav" aria-label="上一个月" @click="goToPreviousBookingMonth">
                      <ArrowLeft class="h-4 w-4" />
                    </button>
                    <div class="text-[14px] font-medium tracking-[0.12em] text-[#2d3135]">{{ bookingMonthLabel }}</div>
                    <button type="button" class="booking-calendar-nav" aria-label="下一个月" @click="goToNextBookingMonth">
                      <ArrowRight class="h-4 w-4" />
                    </button>
                  </div>
                  <div class="mt-4 grid grid-cols-7 gap-y-3 text-center text-[11px] text-[#b6b8bc]">
                    <div v-for="label in bookingWeekdayLabels" :key="label">{{ label }}</div>
                  </div>
                  <div class="mt-3 grid grid-cols-7 gap-y-2 text-center">
                    <button
                      v-for="cell in bookingCalendarCells"
                      :key="cell.key"
                      type="button"
                      class="booking-calendar-day"
                      :class="{ 'is-selected': cell.isSelected, 'is-muted': !cell.inCurrentMonth }"
                      @click="pickBookingCalendarDate(cell.date)"
                    >
                      {{ cell.label }}
                    </button>
                  </div>
                  <button
                    type="button"
                    class="mt-5 flex h-12 w-full items-center justify-center rounded-full bg-[#1e4f46] text-[16px] font-medium text-white transition hover:bg-[#183f39]"
                    @click="confirmBookingCalendarDate"
                  >
                    确定
                  </button>
                </div>
              </transition>
            </div>
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">目的省份</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('province')"
              >
                <span>{{ selectedBookingProvince }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'province' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'province'"
                  class="booking-popover-panel booking-scroll-panel absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[6px] border border-[#ebe5dc] bg-white p-2 shadow-[0_18px_44px_rgba(33,37,41,0.08)]"
                  @click.stop
                >
                  <button
                    v-for="option in bookingProvinceOptions"
                    :key="option"
                    type="button"
                    class="booking-option"
                    :class="{ 'is-active': option === selectedBookingProvince }"
                    @click="selectBookingProvince(option)"
                  >
                    {{ option }}
                  </button>
                </div>
              </transition>
            </div>
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">景点名称</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('spot')"
              >
                <span>{{ selectedBookingSpot }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'spot' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'spot'"
                  class="booking-popover-panel booking-scroll-panel absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[6px] border border-[#ebe5dc] bg-white p-2 shadow-[0_18px_44px_rgba(33,37,41,0.08)]"
                  @click.stop
                >
                  <button
                    v-for="option in bookingSpotOptions"
                    :key="option"
                    type="button"
                    class="booking-option"
                    :class="{ 'is-active': option === selectedBookingSpot }"
                    @click="selectBookingSpot(option)"
                  >
                    {{ option }}
                  </button>
                </div>
              </transition>
            </div>
            <div class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-transparent select-none">立即预订</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-center rounded-[4px] bg-[#434343] text-sm font-semibold tracking-[0.42em] text-white transition hover:bg-[#2d2d2d]"
                @click="goToScenicSearch"
              >
                立即预订
              </button>
            </div>
          </div>
        </div>
      </section>

      <section id="activities" class="bg-white px-8 py-24 lg:px-10 lg:py-32">
        <div class="mx-auto max-w-[1320px]">
          <div class="text-center">
            <p class="text-[11px] font-semibold tracking-[0.62em] text-[#9f9b92]">HUNDREDS OF</p>
            <ScrollRevealText
              tag="h2"
              text="Activities for Everyone"
              :word-stagger="0.08"
              :duration="0.72"
              :translate-y="0.22"
              :base-opacity="0.18"
              :base-rotation="0"
              :blur-strength="1.2"
              :once="false"
              container-class="mt-5 text-[52px] font-semibold tracking-[-0.03em] text-[#2d3135]"
              text-class="justify-center leading-none"
            />
          </div>

          <div class="relative mt-16">
            <button
              type="button"
              class="activity-nav-button group hidden items-center justify-center text-[#6e7277] lg:absolute lg:left-[-152px] lg:top-1/2 lg:flex lg:-translate-y-1/2"
              @click="rotateActivities(-1)"
            >
              <span class="flex flex-col items-center gap-5">
                <span class="activity-nav-mark is-left text-[#9a9ea4]"></span>
                <span class="text-[11px] font-semibold tracking-[0.34em]">BACK</span>
              </span>
            </button>

            <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-4 xl:gap-8">
              <article
                v-for="activity in visibleActivities"
                :key="activity.title"
                class="group relative w-full overflow-hidden rounded-[10px] bg-[#dce2e7] xl:max-w-[306px]"
              >
                <img
                  :src="activity.image"
                  :alt="activity.title"
                  class="h-[560px] w-full object-cover transition duration-700 group-hover:scale-[1.03]"
                  @error="applyFallbackImage($event, fallbackCardImage)"
                />
                <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(7,15,22,0.02),rgba(7,15,22,0.12),rgba(7,15,22,0.62))]" />
                <div class="absolute inset-x-0 bottom-0 p-7 text-white">
                  <h3 class="text-[22px] font-semibold">{{ activity.title }}</h3>
                  <p class="mt-2 text-sm text-white/68">{{ activity.caption }}</p>
                </div>
              </article>
            </div>

            <button
              type="button"
              class="activity-nav-button group hidden items-center justify-center text-[#6e7277] lg:absolute lg:right-[-152px] lg:top-1/2 lg:flex lg:-translate-y-1/2"
              @click="rotateActivities(1)"
            >
              <span class="flex flex-col items-center gap-5">
                <span class="activity-nav-mark is-right text-[#9a9ea4]"></span>
                <span class="text-[11px] font-semibold tracking-[0.34em]">NEXT</span>
              </span>
            </button>

            <div class="mt-8 flex items-center justify-center gap-10 lg:hidden">
              <button type="button" class="group flex items-center justify-center gap-3 text-[#6e7277]" @click="rotateActivities(-1)">
                <ArrowLeft class="h-4 w-4 transition group-hover:-translate-x-1" />
                <span class="text-[11px] font-semibold tracking-[0.34em]">BACK</span>
              </button>

              <button type="button" class="group flex items-center justify-center gap-3 text-[#6e7277]" @click="rotateActivities(1)">
                <span class="text-[11px] font-semibold tracking-[0.34em]">NEXT</span>
                <ArrowRight class="h-4 w-4 transition group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <section id="philosophy" class="bg-white px-8 pb-24 lg:px-10 lg:pb-32">
        <div class="mx-auto max-w-[1320px]">
          <div class="text-center">
            <p class="text-[11px] font-semibold tracking-[0.62em] text-[#9f9b92]">ABOUT US</p>
            <ScrollRevealText
              tag="h2"
              text="Our Philosophy"
              :word-stagger="0.08"
              :duration="0.72"
              :translate-y="0.22"
              :base-opacity="0.18"
              :base-rotation="0"
              :blur-strength="1.2"
              :once="false"
              container-class="mt-5 text-[52px] font-semibold tracking-[-0.03em] text-[#2d3135]"
              text-class="justify-center leading-none"
            />
          </div>

          <div class="mt-16 grid gap-14 lg:grid-cols-[minmax(0,1.08fr)_minmax(340px,0.82fr)] lg:items-start">
            <div class="overflow-hidden rounded-[8px]">
              <img
                src="https://images.unsplash.com/photo-1517821099601-1a4cb3d4ef8d?q=80&w=1600&auto=format&fit=crop"
                alt="山谷与海湾"
                class="h-[520px] w-full object-cover"
                @error="applyFallbackImage($event, fallbackWideImage)"
              />
            </div>

            <div class="space-y-10 pt-2">
              <article
                v-for="principle in explorePrinciples"
                :key="principle.index"
                class="grid gap-5 border-b border-[#ebe7df] pb-8 last:border-b-0 sm:grid-cols-[54px_minmax(0,1fr)]"
              >
                <div class="pt-1 text-[18px] font-medium text-[#b6b0a2]">{{ principle.index }}</div>
                <div>
                  <h3 class="text-[22px] font-semibold text-[#36393d]">{{ principle.title }}</h3>
                  <p class="mt-4 text-[15px] leading-9 text-[#75787b]">{{ principle.description }}</p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section id="stays" class="bg-[#f5f5f5] px-8 py-24 lg:px-10 lg:py-32">
        <div class="mx-auto max-w-[1320px]">
          <div class="text-center">
            <p class="text-[11px] font-semibold tracking-[0.62em] text-[#a7a29a]">DESTINATIONS</p>
            <ScrollRevealText
              tag="h2"
              text="Scenic Spot Booking"
              :word-stagger="0.08"
              :duration="0.72"
              :translate-y="0.22"
              :base-opacity="0.18"
              :base-rotation="0"
              :blur-strength="1.2"
              :once="false"
              container-class="mt-5 text-[52px] font-semibold tracking-[-0.03em] text-[#2d3135]"
              text-class="justify-center leading-none"
            />
          </div>

          <div class="mt-16 grid gap-8 lg:grid-cols-3">
            <article v-for="spot in scenicBookingCards" :key="spot.spot_key" class="space-y-5">
              <div class="overflow-hidden rounded-[6px] bg-white">
                <img
                  :src="spot.image"
                  :alt="spot.name"
                  class="h-[220px] w-full object-cover"
                  @error="applyFallbackImage($event, fallbackCardImage)"
                />
              </div>
              <div class="flex items-center gap-5">
                <h3 class="text-[21px] font-semibold text-[#24282b]">{{ spot.name }}</h3>
                <div class="spot-rating text-[18px] tracking-[0.16em] text-[#ff9f1a]">{{ spot.rating }}</div>
                <div class="text-[18px] tracking-[0.16em] text-[#ff9f1a]">★★★★★</div>
              </div>
              <p class="text-[15px] text-[#94979a]">{{ spot.price }}</p>
            </article>
          </div>

          <div class="mt-14 grid gap-5 lg:grid-cols-[repeat(3,minmax(0,1fr))_210px]">
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">出行日期</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('date')"
              >
                <span>{{ selectedBookingDate }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'date' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'date'"
                  class="booking-popover-panel booking-calendar absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[26px] bg-white px-4 pb-4 pt-3 shadow-[0_24px_60px_rgba(24,33,40,0.16)]"
                  @click.stop
                >
                  <div class="mx-auto mb-4 h-[6px] w-[48px] rounded-full bg-[#1e4f46]"></div>
                  <div class="flex items-center justify-between px-2">
                    <button type="button" class="booking-calendar-nav" aria-label="上一个月" @click="goToPreviousBookingMonth">
                      <ArrowLeft class="h-4 w-4" />
                    </button>
                    <div class="text-[14px] font-medium tracking-[0.12em] text-[#2d3135]">{{ bookingMonthLabel }}</div>
                    <button type="button" class="booking-calendar-nav" aria-label="下一个月" @click="goToNextBookingMonth">
                      <ArrowRight class="h-4 w-4" />
                    </button>
                  </div>
                  <div class="mt-4 grid grid-cols-7 gap-y-3 text-center text-[11px] text-[#b6b8bc]">
                    <div v-for="label in bookingWeekdayLabels" :key="label">{{ label }}</div>
                  </div>
                  <div class="mt-3 grid grid-cols-7 gap-y-2 text-center">
                    <button
                      v-for="cell in bookingCalendarCells"
                      :key="cell.key"
                      type="button"
                      class="booking-calendar-day"
                      :class="{ 'is-selected': cell.isSelected, 'is-muted': !cell.inCurrentMonth }"
                      @click="pickBookingCalendarDate(cell.date)"
                    >
                      {{ cell.label }}
                    </button>
                  </div>
                  <button
                    type="button"
                    class="mt-5 flex h-12 w-full items-center justify-center rounded-full bg-[#1e4f46] text-[16px] font-medium text-white transition hover:bg-[#183f39]"
                    @click="confirmBookingCalendarDate"
                  >
                    确定
                  </button>
                </div>
              </transition>
            </div>
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">目的省份</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('province')"
              >
                <span>{{ selectedBookingProvince }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'province' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'province'"
                  class="booking-popover-panel booking-scroll-panel absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[6px] border border-[#ebe5dc] bg-white p-2 shadow-[0_18px_44px_rgba(33,37,41,0.08)]"
                  @click.stop
                >
                  <button
                    v-for="option in bookingProvinceOptions"
                    :key="option"
                    type="button"
                    class="booking-option"
                    :class="{ 'is-active': option === selectedBookingProvince }"
                    @click="selectBookingProvince(option)"
                  >
                    {{ option }}
                  </button>
                </div>
              </transition>
            </div>
            <div data-booking-field class="relative space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">景点名称</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-left text-[#50555a] transition hover:border-[#d5d0c8]"
                @click.stop="toggleBookingPanel('spot')"
              >
                <span>{{ selectedBookingSpot }}</span>
                <ArrowDown
                  class="h-4 w-4 text-[#9b9fa4] transition-transform duration-300"
                  :class="activeBookingPanel === 'spot' ? 'rotate-0' : 'rotate-[-90deg]'"
                />
              </button>
              <transition name="booking-popover">
                <div
                  v-if="activeBookingPanel === 'spot'"
                  class="booking-popover-panel booking-scroll-panel absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-[6px] border border-[#ebe5dc] bg-white p-2 shadow-[0_18px_44px_rgba(33,37,41,0.08)]"
                  @click.stop
                >
                  <button
                    v-for="option in bookingSpotOptions"
                    :key="option"
                    type="button"
                    class="booking-option"
                    :class="{ 'is-active': option === selectedBookingSpot }"
                    @click="selectBookingSpot(option)"
                  >
                    {{ option }}
                  </button>
                </div>
              </transition>
            </div>
            <div class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-transparent select-none">立即预订</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-center rounded-[4px] bg-[#434343] text-sm font-semibold tracking-[0.42em] text-white transition hover:bg-[#2d2d2d]"
                @click="goToScenicSearch"
              >
                立即预订
              </button>
            </div>
          </div>

          <div class="hidden mt-14 grid gap-5 lg:grid-cols-[repeat(3,minmax(0,1fr))_210px]">
            <label class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">出行日期</span>
              <div class="flex h-16 items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-[#50555a]">
                <span>11月3日 周二</span>
                <ArrowDown class="h-4 w-4 rotate-[-90deg] text-[#9b9fa4]" />
              </div>
            </label>
            <label class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">目的省份</span>
              <div class="flex h-16 items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-[#50555a]">
                <span>四川</span>
                <ArrowDown class="h-4 w-4 rotate-[-90deg] text-[#9b9fa4]" />
              </div>
            </label>
            <label class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-[#a3a09b]">景点名称</span>
              <div class="flex h-16 items-center justify-between rounded-[4px] border border-[#e5e2dc] bg-white px-5 text-[#50555a]">
                <span>九寨沟</span>
                <ArrowDown class="h-4 w-4 rotate-[-90deg] text-[#9b9fa4]" />
              </div>
            </label>
            <div class="space-y-3">
              <span class="block text-[11px] font-semibold tracking-[0.3em] text-transparent select-none">预订</span>
              <button
                type="button"
                class="flex h-16 w-full items-center justify-center rounded-[4px] bg-[#434343] text-sm font-semibold tracking-[0.42em] text-white transition hover:bg-[#2d2d2d]"
                @click="goToScenicSearch"
              >
                立即预订
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-white px-8 py-24 lg:px-10 lg:py-28">
        <div class="mx-auto max-w-[1180px] text-center">
          <p class="text-[11px] font-semibold tracking-[0.62em] text-[#9f9b92]">NETWORK</p>
          <ScrollRevealText
            tag="h2"
            text="Our Partners"
            :word-stagger="0.08"
            :duration="0.72"
            :translate-y="0.22"
            :base-opacity="0.18"
            :base-rotation="0"
            :blur-strength="1.2"
            :once="false"
            container-class="mt-5 text-[52px] font-semibold tracking-[-0.03em] text-[#2d3135]"
            text-class="justify-center leading-none"
          />
          <div class="mt-20 flex flex-wrap items-center justify-center gap-x-8 gap-y-12 text-[#8d8f94] lg:gap-x-10">
            <div v-for="partner in explorePartners" :key="partner.name" class="partner-lockup">
              <svg
                v-if="partner.logo === 'microsoft'"
                viewBox="0 0 180 40"
                aria-hidden="true"
                class="partner-brand partner-brand-microsoft"
              >
                <rect x="1" y="4" width="13" height="13" fill="currentColor" opacity="0.92" />
                <rect x="16.5" y="4" width="13" height="13" fill="currentColor" opacity="0.92" />
                <rect x="1" y="19.5" width="13" height="13" fill="currentColor" opacity="0.92" />
                <rect x="16.5" y="19.5" width="13" height="13" fill="currentColor" opacity="0.92" />
                <text x="38" y="28" fill="currentColor" font-size="18" font-weight="500" letter-spacing="-0.02em">Microsoft</text>
              </svg>

              <svg
                v-else-if="partner.logo === 'magento'"
                viewBox="0 0 190 40"
                aria-hidden="true"
                class="partner-brand partner-brand-magento"
              >
                <path
                  d="M19 2.8 30 9.2v15.6l-6 3.5V13.7L19 10.8l-5 2.9v14.6l-6-3.5V9.2L19 2.8Z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  stroke-linejoin="round"
                />
                <path d="M19 10.8V28" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" />
                <text x="40" y="28" fill="currentColor" font-size="18" font-weight="500" letter-spacing="-0.02em">Magento</text>
              </svg>

              <svg
                v-else-if="partner.logo === 'lakehouse'"
                viewBox="0 0 196 40"
                aria-hidden="true"
                class="partner-brand partner-brand-lakehouse"
              >
                <path
                  d="M19 2.8 30.2 9.6v15.8L19 32.2 7.8 25.4V9.6L19 2.8Z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  stroke-linejoin="round"
                />
                <path d="M13 13.2v9.4h5.4" fill="none" stroke="currentColor" stroke-width="2.05" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M25 13.2v9.4h-5.4" fill="none" stroke="currentColor" stroke-width="2.05" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M19 21.7v-8.5" fill="none" stroke="currentColor" stroke-width="2.05" stroke-linecap="round" />
                <text x="42" y="28" fill="currentColor" font-size="18" font-weight="500" letter-spacing="-0.02em">Lakehouse</text>
              </svg>

              <svg
                v-else
                viewBox="0 0 172 40"
                aria-hidden="true"
                class="partner-brand partner-brand-midea"
              >
                <path
                  d="M20.5 3.8c-8.4 0-15.3 6.7-15.3 15s6.9 15 15.3 15c5.5 0 10.1-2.1 12.9-5.9"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.4"
                  stroke-linecap="round"
                />
                <path
                  d="M15 24.2c2.6-4.7 6-8.5 10.3-11.6 4-2.9 8.3-4.8 13-5.7-2.2 2.8-3.3 6-3.3 9.6 0 4.9 2 8.8 6.1 11.6"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <text x="48" y="27.8" fill="currentColor" font-size="22" font-style="italic" font-weight="500" letter-spacing="-0.03em">Midea</text>
                <circle cx="115" cy="6.8" r="1.7" fill="currentColor" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-white px-8 pb-28 lg:px-10 lg:pb-32">
        <div class="mx-auto max-w-[1540px] overflow-hidden rounded-[14px]">
          <div class="relative min-h-[560px] px-10 py-16 lg:px-16 lg:py-20">
            <img
              src="https://images.unsplash.com/photo-1517821099601-1a4cb3d4ef8d?q=80&w=2400&auto=format&fit=crop"
              alt="高处俯瞰海岸"
              class="absolute inset-0 h-full w-full object-cover"
              @error="applyFallbackImage($event, fallbackWideImage)"
            />
            <div class="absolute inset-0 bg-[linear-gradient(180deg,rgba(13,18,26,0.08),rgba(13,18,26,0.18))]" />

            <div class="relative grid gap-8 pt-10 lg:grid-cols-3 lg:gap-10 lg:pt-16">
              <article v-for="testimonial in testimonialCards" :key="testimonial.name" class="testimonial-item">
                <div class="testimonial-bubble rounded-[16px] bg-white/98 px-9 py-9 shadow-[0_22px_48px_rgba(21,29,34,0.12)]">
                  <div class="text-[30px] leading-none text-[#f0bf7d]">“</div>
                  <p class="mt-5 text-[15px] leading-9 text-[#74787d]">{{ testimonial.quote }}</p>
                </div>
                <div class="mt-10 flex items-center gap-4 pl-8 text-white">
                  <img
                    :src="testimonial.avatar"
                    :alt="testimonial.name"
                    class="h-14 w-14 rounded-full object-cover ring-2 ring-white/35"
                    @error="applyFallbackImage($event, fallbackAvatarImage)"
                  />
                  <div>
                    <div class="text-[17px] font-semibold">{{ testimonial.name }}</div>
                    <div class="mt-1 text-sm text-white/78">{{ testimonial.role }}</div>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>
    </main>

    <Footer variant="light" />
  </div>
</template>

<style scoped>
.hero-side-label {
  display: inline-block;
  writing-mode: vertical-rl;
}

.hero-reveal {
  opacity: 0;
  transform: translateY(22px);
  transition:
    opacity 0.8s ease,
    transform 0.8s ease;
}

.hero-reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.activity-nav-mark {
  position: relative;
  display: inline-block;
  width: 58px;
  height: 12px;
  transition: transform 0.28s ease;
}

.activity-nav-mark::before {
  content: '';
  position: absolute;
  top: 50%;
  width: 46px;
  border-top: 1px solid currentColor;
  transform: translateY(-50%);
  transition: border-color 0.28s ease;
}

.activity-nav-mark::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 8px;
  height: 8px;
  border-top: 1px solid currentColor;
  border-right: 1px solid currentColor;
  transform: translateY(-50%) rotate(45deg);
  transition:
    transform 0.28s ease,
    border-color 0.28s ease;
}

.activity-nav-mark.is-left::before {
  right: 0;
}

.activity-nav-mark.is-left::after {
  left: 1px;
  transform: translateY(-50%) rotate(-135deg);
}

.activity-nav-mark.is-right::before {
  left: 0;
}

.activity-nav-mark.is-right::after {
  right: 1px;
}

.activity-nav-button {
  transition: color 0.28s ease;
}

.activity-nav-button:hover {
  color: #2d3135;
}

.activity-nav-button:hover .activity-nav-mark.is-left {
  transform: translateX(-6px);
}

.activity-nav-button:hover .activity-nav-mark.is-right {
  transform: translateX(6px);
}

.partner-lockup {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 250px;
  min-height: 52px;
  color: #9a9da3;
}

.spot-rating + div {
  display: none;
}

.booking-option {
  display: flex;
  width: 100%;
  align-items: center;
  border-radius: 4px;
  padding: 11px 14px;
  color: #50555a;
  transition:
    background-color 0.24s ease,
    color 0.24s ease;
}

.booking-option:hover {
  background: #f6f3ee;
}

.booking-option.is-active {
  background: #f2ece3;
  color: #2d3135;
}

.booking-scroll-panel {
  max-height: 248px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.booking-scroll-panel::-webkit-scrollbar {
  width: 6px;
}

.booking-scroll-panel::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(164, 160, 153, 0.45);
}

.booking-scroll-panel::-webkit-scrollbar-track {
  background: transparent;
}

.booking-calendar {
  border: 1px solid rgba(227, 232, 228, 0.92);
}

.booking-calendar-nav {
  display: inline-flex;
  height: 34px;
  width: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: #6c7378;
  transition:
    background-color 0.24s ease,
    color 0.24s ease,
    transform 0.24s ease;
}

.booking-calendar-nav:hover {
  background: #f1f5f2;
  color: #1e4f46;
  transform: translateY(-1px);
}

.booking-calendar-day {
  display: inline-flex;
  height: 38px;
  width: 38px;
  align-items: center;
  justify-content: center;
  justify-self: center;
  border-radius: 999px;
  color: #556068;
  transition:
    background-color 0.24s ease,
    color 0.24s ease,
    transform 0.24s ease,
    box-shadow 0.24s ease;
}

.booking-calendar-day:hover {
  background: #edf4f1;
  color: #1e4f46;
}

.booking-calendar-day.is-selected {
  background: #1e4f46;
  color: #fff;
  box-shadow: 0 10px 20px rgba(30, 79, 70, 0.2);
}

.booking-calendar-day.is-muted {
  color: #c7cbcf;
}

.booking-popover-enter-active,
.booking-popover-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.booking-popover-enter-from,
.booking-popover-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.partner-brand {
  height: 50px;
  width: auto;
  overflow: visible;
}

.partner-brand text {
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

.partner-brand-midea text {
  font-family: Georgia, 'Times New Roman', serif;
}

.partner-brand-microsoft {
  width: 214px;
}

.partner-brand-magento {
  width: 212px;
}

.partner-brand-lakehouse {
  width: 232px;
}

.partner-brand-midea {
  width: 214px;
}

.testimonial-item {
  padding-top: 24px;
}

.testimonial-bubble {
  position: relative;
  min-height: 192px;
  background-image: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(252, 252, 252, 0.98));
}

.testimonial-bubble::after {
  content: '';
  position: absolute;
  left: 38px;
  bottom: -14px;
  width: 28px;
  height: 28px;
  background: white;
  clip-path: polygon(0 0, 100% 0, 24% 100%);
  filter: drop-shadow(0 10px 18px rgba(21, 29, 34, 0.08));
}

.testimonial-bubble > div:first-child {
  position: relative;
  font-size: 0;
  line-height: 1;
  color: transparent;
}

.testimonial-bubble > div:first-child::before {
  content: '\201C';
  display: block;
  font-size: 40px;
  font-weight: 600;
  line-height: 1;
  color: #f5c78d;
}
</style>
