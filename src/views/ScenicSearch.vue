<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CalendarDays, ChevronLeft, ChevronRight, Search } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import ScenicSearchFilters from '@/components/discovery/ScenicSearchFilters.vue'
import ScenicSpotCard from '@/components/discovery/ScenicSpotCard.vue'
import { travelDiscoveryService, type SpotItem } from '@/services/travelDiscoveryService'
import type {
  ScenicOption,
  ScenicSearchCardData,
  ScenicSearchFiltersState,
} from '@/components/discovery/types'

const router = useRouter()
const route = useRoute()

const DEFAULT_TRAVEL_DATE = '选择出发日期'
const DEFAULT_SORT = '最受欢迎'
const SORT_BY_RATING = '评分最高'
const SORT_BY_PRICE = '价格最低'
const ALL_PROVINCES = '全部目的地'
const ALL_SPOTS = '全部景点'
const PAGE_SIZE = 12

const baseTravelDateOptions = ['2026年10月04日', '2026年10月05日', '2026年10月06日']

const popularTagOptions = ['亲子友好', '轻徒步', '自然风光', '适合拍照', '人文地标']

const durationOptions: ScenicOption[] = [
  { key: 'up_to_1_hour', label: '1 小时以内' },
  { key: 'one_to_four_hours', label: '1 到 4 小时' },
  { key: 'four_hours_to_one_day', label: '4 小时到 1 天' },
  { key: 'one_to_three_days', label: '1 到 3 天' },
  { key: 'three_days_or_more', label: '3 天以上' },
]

const ratingOptions = [
  { value: 5, stars: 5 },
  { value: 4, stars: 4 },
  { value: 3, stars: 3 },
  { value: 2, stars: 2 },
  { value: 1, stars: 1 },
]

const filters = reactive<ScenicSearchFiltersState>({
  travelDate: DEFAULT_TRAVEL_DATE,
  sort: DEFAULT_SORT,
  popularTags: [],
  minPrice: 0,
  maxPrice: 20000,
  duration: '',
  minRating: 0,
  ageGroup: null,
  specialKeys: [],
})

const scenicItems = ref<SpotItem[]>([])
const scenicTotal = ref(0)
const availableCities = ref<string[]>([])
const availableTags = ref<string[]>([])
const scenicSpotOptions = ref<string[]>([])
const loading = ref(false)
const currentPage = ref(1)
const keywordInput = ref('')
const selectedProvince = ref(ALL_PROVINCES)
const selectedSpot = ref(ALL_SPOTS)
const favoriteIds = ref<string[]>(['recent-1'])

const recentCards: ScenicSearchCardData[] = [
  {
    id: 'recent-1',
    title: '山海火车之旅',
    subtitle: '查看最近看过的灵感路线，继续比较价格与行程节奏。',
    image: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1600&auto=format&fit=crop',
    badgeText: '30%',
    displayPrice: '$895.50',
    reviewSummary: '',
    featureLabels: ['10 天 | 9 晚', '', ''],
    rating: 5,
    recentlyViewedLabel: '10 天 | 9 晚',
  },
  {
    id: 'recent-2',
    title: '海湾自然景观',
    subtitle: '把看过的海岸线与湖景路线集中到这里，方便继续挑选。',
    image: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=1600&auto=format&fit=crop',
    badgeText: '30%',
    displayPrice: '$895.50',
    reviewSummary: '',
    featureLabels: ['10 天 | 9 晚', '', ''],
    rating: 5,
    recentlyViewedLabel: '10 天 | 9 晚',
  },
  {
    id: 'recent-3',
    title: '城市暮色三部曲',
    subtitle: '适合回看近期浏览过的城市地标，继续对比哪条路线更合适。',
    image: 'https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=1600&auto=format&fit=crop',
    badgeText: '30%',
    displayPrice: '$895.50',
    reviewSummary: '',
    featureLabels: ['10 天 | 9 晚', '', ''],
    rating: 5,
    recentlyViewedLabel: '10 天 | 9 晚',
  },
]

const spotOptionsCache = new Map<string, string[]>()
let keywordSyncTimer: number | null = null
let syncingFromRoute = false

const normalizeQueryValue = (value: unknown) => {
  if (Array.isArray(value)) {
    return value[0] ?? ''
  }
  return typeof value === 'string' ? value : ''
}

const queryProvince = computed(() => normalizeQueryValue(route.query.province))
const querySpot = computed(() => normalizeQueryValue(route.query.spot))
const queryKeyword = computed(() => normalizeQueryValue(route.query.keyword))
const queryDate = computed(() => normalizeQueryValue(route.query.date))
const queryPage = computed(() => {
  const raw = Number(normalizeQueryValue(route.query.page) || 1)
  return Number.isFinite(raw) && raw > 0 ? Math.floor(raw) : 1
})

const normalizedQueryProvince = computed(() =>
  queryProvince.value && queryProvince.value !== ALL_PROVINCES ? queryProvince.value : '',
)
const normalizedQuerySpot = computed(() =>
  querySpot.value && querySpot.value !== ALL_SPOTS ? querySpot.value : '',
)
const normalizedQueryKeyword = computed(() => queryKeyword.value.trim())

const travelDateOptions = computed(() => {
  const values = new Set<string>([DEFAULT_TRAVEL_DATE, ...baseTravelDateOptions])
  if (queryDate.value) {
    values.add(queryDate.value)
  }
  if (filters.travelDate) {
    values.add(filters.travelDate)
  }
  return Array.from(values)
})

const provinceOptions = computed(() => {
  const values = new Set<string>(availableCities.value.filter(Boolean))
  if (selectedProvince.value && selectedProvince.value !== ALL_PROVINCES) {
    values.add(selectedProvince.value)
  }
  return [ALL_PROVINCES, ...Array.from(values)]
})

const spotOptions = computed(() => {
  const values = new Set<string>(scenicSpotOptions.value.filter(Boolean))
  if (selectedSpot.value && selectedSpot.value !== ALL_SPOTS) {
    values.add(selectedSpot.value)
  }
  return [ALL_SPOTS, ...Array.from(values)]
})

const quickTagOptions = computed(() =>
  availableTags.value.length ? availableTags.value.slice(0, 6) : popularTagOptions,
)

const scenicCards = computed<ScenicSearchCardData[]>(() =>
  scenicItems.value.map((item) => ({
    id: item.spot_key,
    spotKey: item.spot_key,
    title: item.name,
    subtitle: `${item.city} | ${item.address || item.description || '精选景点'}`,
    image: item.cover_image,
    badgeText: item.price > 0 ? '' : '免费',
    displayPrice: item.price > 0 ? `¥${Number(item.price).toFixed(2)}` : '免费',
    reviewSummary: item.rating > 0 ? `${item.rating.toFixed(1)} 分` : '',
    featureLabels: [
      item.visit_duration || '游玩时长待补充',
      item.booking_required || '预约信息待补充',
      item.opening_hours || '开放时间待补充',
    ],
    rating: item.rating || 0,
    openingHours: item.opening_hours || '',
    visitDuration: item.visit_duration || '',
    bookingRequired: item.booking_required || '',
    address: item.address || '',
  })),
)

const totalPages = computed(() => Math.max(1, Math.ceil(scenicTotal.value / PAGE_SIZE)))

const paginationItems = computed<Array<number | 'ellipsis'>>(() => {
  const total = totalPages.value
  const page = Math.min(currentPage.value, total)
  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => index + 1)
  }

  const pages = new Set<number>([1, total, page - 1, page, page + 1])
  if (page <= 3) {
    pages.add(2)
    pages.add(3)
    pages.add(4)
  }
  if (page >= total - 2) {
    pages.add(total - 1)
    pages.add(total - 2)
    pages.add(total - 3)
  }

  const sorted = Array.from(pages)
    .filter((value) => value >= 1 && value <= total)
    .sort((left, right) => left - right)

  const output: Array<number | 'ellipsis'> = []
  sorted.forEach((value, index) => {
    if (index > 0 && value - sorted[index - 1] > 1) {
      output.push('ellipsis')
    }
    output.push(value)
  })
  return output
})

const resultSummaryText = computed(() => {
  const count = scenicCards.value.length
  const start = count ? (currentPage.value - 1) * PAGE_SIZE + 1 : 0
  const end = count ? start + count - 1 : 0
  const keyword = querySpot.value || queryKeyword.value || queryProvince.value || '景点'
  return `显示 ${start} - ${end} 项，共 ${scenicTotal.value} 个与“${keyword}”相关的结果`
})

const buildDiscoverySort = (value: string) => {
  if (value === SORT_BY_RATING) {
    return 'rating_desc'
  }
  if (value === SORT_BY_PRICE) {
    return 'price_asc'
  }
  return 'recommended'
}

const buildDiscoveryQuery = () => ({
  q: normalizedQuerySpot.value || normalizedQueryKeyword.value || undefined,
  city: normalizedQueryProvince.value || undefined,
  min_price: filters.minPrice > 0 ? filters.minPrice : undefined,
  max_price: filters.maxPrice < 20000 ? filters.maxPrice : undefined,
  min_rating: filters.minRating > 0 ? filters.minRating : undefined,
  duration: filters.duration || undefined,
  tags: filters.popularTags.length ? filters.popularTags : undefined,
  sort: buildDiscoverySort(filters.sort),
  page: currentPage.value,
  page_size: PAGE_SIZE,
})

const buildSearchRouteQuery = () => {
  const nextQuery: Record<string, string> = {}

  if (filters.travelDate && filters.travelDate !== DEFAULT_TRAVEL_DATE) {
    nextQuery.date = filters.travelDate
  }
  if (selectedProvince.value && selectedProvince.value !== ALL_PROVINCES) {
    nextQuery.province = selectedProvince.value
  }
  if (selectedSpot.value && selectedSpot.value !== ALL_SPOTS) {
    nextQuery.spot = selectedSpot.value
  }
  if (selectedSpot.value === ALL_SPOTS && keywordInput.value.trim()) {
    nextQuery.keyword = keywordInput.value.trim()
  }
  if (currentPage.value > 1) {
    nextQuery.page = String(currentPage.value)
  }

  return nextQuery
}

const syncControlsFromRoute = () => {
  syncingFromRoute = true
  keywordInput.value = queryKeyword.value
  selectedProvince.value = queryProvince.value || ALL_PROVINCES
  selectedSpot.value = querySpot.value || ALL_SPOTS
  filters.travelDate = queryDate.value || DEFAULT_TRAVEL_DATE
  currentPage.value = queryPage.value
  syncingFromRoute = false
}

const applySearchRouteQuery = () => {
  const nextQuery = buildSearchRouteQuery()

  if (
    (nextQuery.date || '') === queryDate.value &&
    (nextQuery.province || '') === queryProvince.value &&
    (nextQuery.spot || '') === querySpot.value &&
    (nextQuery.keyword || '') === queryKeyword.value &&
    Number(nextQuery.page || 1) === queryPage.value
  ) {
    return
  }

  router.replace({
    name: 'scenic-search',
    query: nextQuery,
  })
}

const scheduleKeywordSync = () => {
  if (keywordSyncTimer !== null) {
    window.clearTimeout(keywordSyncTimer)
  }

  keywordSyncTimer = window.setTimeout(() => {
    applySearchRouteQuery()
    keywordSyncTimer = null
  }, 320)
}

const resetToFirstPage = () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
  }
}

const loadSpotOptions = async (province: string) => {
  const cacheKey = province || '__all__'
  const cached = spotOptionsCache.get(cacheKey)
  if (cached) {
    scenicSpotOptions.value = cached
    return
  }

  try {
    const response = await travelDiscoveryService.listSpots({
      city: province || undefined,
      sort: 'recommended',
      limit: 80,
    })
    const nextOptions = Array.from(
      new Set((response.items || []).map((item) => item.name).filter(Boolean)),
    )

    if (selectedSpot.value !== ALL_SPOTS && !nextOptions.includes(selectedSpot.value)) {
      nextOptions.unshift(selectedSpot.value)
    }

    spotOptionsCache.set(cacheKey, nextOptions)
    scenicSpotOptions.value = nextOptions
  } catch (error) {
    console.error('Failed to load scenic spot options:', error)
    scenicSpotOptions.value = selectedSpot.value !== ALL_SPOTS ? [selectedSpot.value] : []
  }
}

const loadScenicResults = async () => {
  loading.value = true
  try {
    const response = await travelDiscoveryService.listSpots(buildDiscoveryQuery())
    scenicItems.value = response.items || []
    scenicTotal.value = response.total || 0
    availableCities.value = response.filters?.cities || []
    availableTags.value = response.filters?.tags || []
    currentPage.value = response.page || queryPage.value || 1
  } catch (error) {
    console.error('Failed to load scenic search results:', error)
    scenicItems.value = []
    scenicTotal.value = 0
    availableCities.value = []
    availableTags.value = []
  } finally {
    loading.value = false
  }
}

const updateFilters = (nextFilters: ScenicSearchFiltersState) => {
  const previousTravelDate = filters.travelDate

  filters.travelDate = nextFilters.travelDate
  filters.sort = nextFilters.sort
  filters.popularTags = nextFilters.popularTags
  filters.minPrice = nextFilters.minPrice
  filters.maxPrice = nextFilters.maxPrice
  filters.duration = nextFilters.duration
  filters.minRating = nextFilters.minRating
  filters.ageGroup = null
  filters.specialKeys = []

  if (filters.travelDate !== previousTravelDate) {
    resetToFirstPage()
    applySearchRouteQuery()
  }
}

const toggleQuickTag = (tag: string) => {
  filters.popularTags = filters.popularTags.includes(tag)
    ? filters.popularTags.filter((item) => item !== tag)
    : [...filters.popularTags, tag]
  resetToFirstPage()
}

const handleDateChange = (value: string) => {
  filters.travelDate = value
  resetToFirstPage()
  applySearchRouteQuery()
}

const handleProvinceChange = (value: string) => {
  selectedProvince.value = value
  selectedSpot.value = ALL_SPOTS
  resetToFirstPage()
  void loadSpotOptions(value === ALL_PROVINCES ? '' : value)
  applySearchRouteQuery()
}

const handleSpotChange = (value: string) => {
  selectedSpot.value = value
  if (value !== ALL_SPOTS) {
    keywordInput.value = ''
  }
  resetToFirstPage()
  applySearchRouteQuery()
}

const handleKeywordInput = (value: string) => {
  keywordInput.value = value
  if (value.trim() && selectedSpot.value !== ALL_SPOTS) {
    selectedSpot.value = ALL_SPOTS
  }
  resetToFirstPage()
  scheduleKeywordSync()
}

const applyKeywordSearch = () => {
  if (keywordSyncTimer !== null) {
    window.clearTimeout(keywordSyncTimer)
    keywordSyncTimer = null
  }
  if (keywordInput.value.trim() && selectedSpot.value !== ALL_SPOTS) {
    selectedSpot.value = ALL_SPOTS
  }
  resetToFirstPage()
  applySearchRouteQuery()
}

const goToPage = (page: number) => {
  const nextPage = Math.max(1, Math.min(page, totalPages.value))
  if (nextPage === currentPage.value) {
    return
  }
  currentPage.value = nextPage
  applySearchRouteQuery()
}

const toggleFavorite = (item: ScenicSearchCardData) => {
  favoriteIds.value = favoriteIds.value.includes(item.id)
    ? favoriteIds.value.filter((id) => id !== item.id)
    : [...favoriteIds.value, item.id]
}

const openScenicDetail = (item: ScenicSearchCardData) => {
  router.push({
    name: 'scenic-detail',
    params: { id: item.spotKey || item.id },
    query: route.query,
  })
}

watch(
  () => route.query,
  async () => {
    syncControlsFromRoute()
    await loadSpotOptions(normalizedQueryProvince.value)
    await loadScenicResults()
  },
  { immediate: true, deep: true },
)

watch(
  () => [
    filters.sort,
    filters.minPrice,
    filters.maxPrice,
    filters.minRating,
    filters.duration,
    filters.popularTags.join('|'),
  ],
  () => {
    if (syncingFromRoute) {
      return
    }
    resetToFirstPage()
    if (queryPage.value !== 1) {
      applySearchRouteQuery()
      return
    }
    void loadScenicResults()
  },
)

onUnmounted(() => {
  if (keywordSyncTimer !== null) {
    window.clearTimeout(keywordSyncTimer)
  }
})
</script>

<template>
  <div class="min-h-screen bg-white text-[#243251]">
    <Navigation class="text-black !border-b !border-[#edf0f3] !bg-white/95 py-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <template #logo>
        <router-link
          to="/"
          class="text-4xl font-bold tracking-wide text-[#1f2937]"
          style="font-family: 'PangMenZhengDao', serif;"
        >
          旅天行
        </router-link>
      </template>
    </Navigation>

    <main class="px-5 pb-24 pt-28 sm:px-6 lg:px-8">
      <div class="mx-auto max-w-[1220px]">
        <section class="rounded-[20px] border border-[#edf0f3] bg-white px-5 py-5 shadow-[0_16px_40px_rgba(15,23,42,0.05)] sm:px-6">
          <div class="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_repeat(3,minmax(0,0.8fr))]">
            <label class="block">
              <span class="text-[12px] font-semibold text-[#8a92a5]">搜索景点</span>
              <div class="mt-2 flex h-12 items-center gap-3 rounded-[14px] border border-[#edf0f3] bg-[#fbfcfe] px-4">
                <Search class="h-4 w-4 text-[#9aa3b2]" />
                <input
                  class="h-full flex-1 bg-transparent text-[14px] text-[#243251] outline-none placeholder:text-[#aab2c0]"
                  type="text"
                  :value="keywordInput"
                  placeholder="输入景点名、城市或关键词"
                  @input="handleKeywordInput(String(($event.target as HTMLInputElement).value))"
                  @keydown.enter.prevent="applyKeywordSearch"
                />
                <button
                  type="button"
                  class="inline-flex h-8 shrink-0 items-center justify-center rounded-full bg-[#22b69c] px-4 text-[12px] font-semibold text-white transition hover:bg-[#1ba28c]"
                  @click="applyKeywordSearch"
                >
                  搜索
                </button>
              </div>
            </label>

            <label class="block">
              <span class="inline-flex items-center gap-2 text-[12px] font-semibold text-[#8a92a5]">
                <CalendarDays class="h-4 w-4 text-[#22b69c]" />
                出发日期
              </span>
              <select
                class="mt-2 h-12 w-full rounded-[14px] border border-[#edf0f3] bg-[#fbfcfe] px-4 text-[14px] text-[#243251] outline-none transition focus:border-[#22b69c]"
                :value="filters.travelDate"
                @change="handleDateChange(String(($event.target as HTMLSelectElement).value))"
              >
                <option v-for="option in travelDateOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>

            <label class="block">
              <span class="text-[12px] font-semibold text-[#8a92a5]">目的地</span>
              <select
                class="mt-2 h-12 w-full rounded-[14px] border border-[#edf0f3] bg-[#fbfcfe] px-4 text-[14px] text-[#243251] outline-none transition focus:border-[#22b69c]"
                :value="selectedProvince"
                @change="handleProvinceChange(String(($event.target as HTMLSelectElement).value))"
              >
                <option v-for="option in provinceOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>

            <label class="block">
              <span class="text-[12px] font-semibold text-[#8a92a5]">景点选择</span>
              <select
                class="mt-2 h-12 w-full rounded-[14px] border border-[#edf0f3] bg-[#fbfcfe] px-4 text-[14px] text-[#243251] outline-none transition focus:border-[#22b69c]"
                :value="selectedSpot"
                @change="handleSpotChange(String(($event.target as HTMLSelectElement).value))"
              >
                <option v-for="option in spotOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>
          </div>

          <div class="mt-4 flex flex-wrap gap-3">
            <button
              v-for="tag in quickTagOptions"
              :key="tag"
              type="button"
              class="inline-flex items-center rounded-full border px-4 py-2 text-[12px] font-medium transition"
              :class="
                filters.popularTags.includes(tag)
                  ? 'border-[#22b69c] bg-[#22b69c]/10 text-[#167a69]'
                  : 'border-[#edf0f3] bg-white text-[#8a92a5] hover:border-[#dfe5ec] hover:text-[#6f7788]'
              "
              @click="toggleQuickTag(tag)"
            >
              {{ tag }}
            </button>
          </div>

          <div class="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <p class="text-[12px] font-medium text-[#8a92a5]">{{ resultSummaryText }}</p>
            <label class="inline-flex items-center gap-3 text-[12px] text-[#8a92a5]">
              <span>排序方式</span>
              <select
                class="rounded-[10px] border border-[#edf0f3] bg-white px-3 py-2 text-[12px] text-[#374151] outline-none transition focus:border-[#22b69c]"
                :value="filters.sort"
                @change="filters.sort = String(($event.target as HTMLSelectElement).value)"
              >
                <option>{{ DEFAULT_SORT }}</option>
                <option>{{ SORT_BY_RATING }}</option>
                <option>{{ SORT_BY_PRICE }}</option>
              </select>
            </label>
          </div>
        </section>

        <div class="mt-6 grid items-start gap-6 lg:grid-cols-[272px_minmax(0,1fr)]">
          <ScenicSearchFilters
            :filters="filters"
            :price-bounds="{ min: 0, max: 20000 }"
            :popular-tag-options="availableTags.length ? availableTags.slice(0, 8) : popularTagOptions"
            :duration-options="durationOptions"
            :rating-options="ratingOptions"
            @update:filters="updateFilters"
          />

          <div>
            <div class="grid content-start items-start gap-6 md:grid-cols-2">
              <div
                v-if="loading"
                class="col-span-full rounded-[16px] border border-[#edf0f3] bg-white px-6 py-16 text-center text-[14px] text-[#8a92a5]"
              >
                正在加载景点数据...
              </div>
              <div
                v-else-if="!scenicCards.length"
                class="col-span-full rounded-[16px] border border-[#edf0f3] bg-white px-6 py-16 text-center text-[14px] text-[#8a92a5]"
              >
                暂未找到符合条件的景点。
              </div>
              <ScenicSpotCard
                v-for="item in scenicCards"
                :key="item.id"
                :item="item"
                :saved="favoriteIds.includes(item.id)"
                @action="toggleFavorite"
                @select="openScenicDetail"
              />
            </div>

            <div
              v-if="!loading && scenicTotal > PAGE_SIZE"
              class="mt-8 flex flex-wrap items-center justify-center gap-2"
            >
              <button
                type="button"
                class="inline-flex h-10 items-center justify-center rounded-[12px] border border-[#e4e8ef] px-4 text-[13px] text-[#6f7788] transition hover:border-[#cfd7e3] hover:text-[#243251] disabled:cursor-not-allowed disabled:opacity-45"
                :disabled="currentPage === 1"
                @click="goToPage(currentPage - 1)"
              >
                上一页
              </button>

              <template v-for="(item, index) in paginationItems" :key="`${item}-${index}`">
                <span
                  v-if="item === 'ellipsis'"
                  class="inline-flex h-10 w-10 items-center justify-center text-[13px] text-[#9aa3b2]"
                >
                  ...
                </span>
                <button
                  v-else
                  type="button"
                  class="inline-flex h-10 w-10 items-center justify-center rounded-[12px] border text-[13px] font-semibold transition"
                  :class="
                    item === currentPage
                      ? 'border-[#22b69c] bg-[#22b69c] text-white'
                      : 'border-[#e4e8ef] text-[#6f7788] hover:border-[#cfd7e3] hover:text-[#243251]'
                  "
                  @click="goToPage(item)"
                >
                  {{ item }}
                </button>
              </template>

              <button
                type="button"
                class="inline-flex h-10 items-center justify-center rounded-[12px] border border-[#e4e8ef] px-4 text-[13px] text-[#6f7788] transition hover:border-[#cfd7e3] hover:text-[#243251] disabled:cursor-not-allowed disabled:opacity-45"
                :disabled="currentPage === totalPages"
                @click="goToPage(currentPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>

        <section class="mt-24">
          <div class="flex items-end justify-between gap-4">
            <div>
              <h2 class="text-[22px] font-bold text-[#243251]">最近浏览</h2>
              <p class="mt-3 text-[13px] text-[#8a92a5]">
                把你刚看过的景点集中放在这里，方便继续比较和挑选。
              </p>
            </div>

            <div class="flex items-center gap-3">
              <button
                type="button"
                class="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#e6ebf1] text-[#6b7280]"
              >
                <ChevronLeft class="h-5 w-5" />
              </button>
              <button
                type="button"
                class="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[#22b69c] text-white"
              >
                <ChevronRight class="h-5 w-5" />
              </button>
            </div>
          </div>

          <div class="mt-8 grid gap-6 lg:grid-cols-3">
            <article v-for="(item, index) in recentCards" :key="item.id">
              <div class="relative overflow-hidden rounded-[18px]">
                <img :src="item.image" :alt="item.title" class="h-[220px] w-full object-cover" />
                <span
                  class="absolute right-3 top-3 rounded-full bg-[#ffb261] px-2.5 py-1 text-[10px] font-semibold leading-none text-white"
                >
                  {{ item.badgeText }}
                </span>
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                <div class="absolute left-4 top-4 text-[11px] font-medium text-white/86">
                  {{ item.recentlyViewedLabel }}
                </div>
                <div
                  v-if="index === 0"
                  class="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3"
                >
                  <p class="text-[28px] font-bold leading-none text-white">{{ item.displayPrice }}</p>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white text-[#243251]"
                    >
                      <ChevronLeft class="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-9 items-center justify-center rounded-full bg-[#22b69c] px-4 text-[12px] font-semibold text-white"
                    >
                      探索
                    </button>
                  </div>
                </div>
              </div>

              <div class="px-1 pt-4 text-center">
                <h3 class="text-[20px] font-semibold text-[#243251]">{{ item.title }}</h3>
                <p class="mt-3 text-[12px] leading-5 text-[#8a92a5]">{{ item.subtitle }}</p>
              </div>
            </article>
          </div>
        </section>
      </div>
    </main>

    <Footer variant="light" />
  </div>
</template>
