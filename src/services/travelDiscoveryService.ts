import { safeGetSupabaseSession } from '@/utils/supabase'

export interface SpotItem {
  id: string
  spot_key: string
  source_type: string
  source_id: string
  name: string
  city: string
  rating: number
  price: number
  description: string
  cover_image: string
  tags: string[]
  opening_hours?: string
  visit_duration?: string
  booking_required?: string
  address?: string
  recommendation_reason: string
  in_itinerary: boolean
}

export interface DiscoveryFilters {
  q?: string
  city?: string
  min_price?: number | null
  max_price?: number | null
  min_rating?: number | null
  duration?: string
  tag?: string
  tags?: string[]
  sort?: string
  limit?: number
  page?: number
  page_size?: number
}

export interface DiscoveryListResponse {
  items: SpotItem[]
  filters: {
    cities: string[]
    tags: string[]
  }
  total: number
  source: string
  page?: number
  page_size?: number
}

export interface SpotDetailResponse extends SpotItem {
  similar_spots?: SpotItem[]
}

export interface ItineraryCityGroup {
  city: string
  count: number
  budget_total: number
}

export interface ItinerarySummary {
  items_count: number
  budget_total: number
  city_groups: ItineraryCityGroup[]
}

export interface ItineraryItem {
  item_id: number | string
  user_id?: string
  spot_key: string
  spot_name: string
  city: string
  price: number
  rating: number
  cover_image: string
  recommendation_reason: string
  tags: string[]
  spot_snapshot: Record<string, any>
  items_count?: number
  created_at?: string
  updated_at?: string
}

export interface ItineraryResponse {
  items: ItineraryItem[]
  summary: ItinerarySummary
  mode: 'guest' | 'account'
}

export interface BookingIntent {
  id: number
  user_id: string
  trip_name: string
  contact_name: string
  contact_phone: string
  note: string
  status: string
  total_estimated_cost: number
  items: Array<Record<string, any>>
  items_count: number
  created_at: string
  updated_at: string
}

interface RequestOptions extends RequestInit {
  body?: any
  requireAuth?: boolean
}

const GUEST_ITINERARY_KEY = 'travel_guest_itinerary_v1'
const GENERIC_DATA_SOURCE_ERROR = '数据源暂时不可用，请稍后再试'
const LOGIN_REQUIRED_ERROR = '请先登录后再继续操作'
const UNKNOWN_CITY = '未标注城市'
const USE_LOCAL_DISCOVERY_DEMO = false

const DEMO_SPOTS: SpotItem[] = [
  {
    id: 'demo-qiandao-lake',
    spot_key: 'demo-qiandao-lake',
    source_type: 'demo',
    source_id: 'demo-1',
    name: '千岛湖云谷晨线',
    city: '杭州',
    rating: 4.9,
    price: 168,
    description: '清透湖面与低云山脊交叠，适合轻徒步、观景台拍照和半日放空。',
    cover_image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1600&auto=format&fit=crop',
    tags: ['自然', '摄影', '轻徒步'],
    opening_hours: '周一至周日 08:30-17:30',
    visit_duration: '3-4小时',
    booking_required: '无需预订',
    address: '杭州淳安县千岛湖镇',
    recommendation_reason: '高评分且价格适中',
    in_itinerary: false,
  },
  {
    id: 'demo-erhai',
    spot_key: 'demo-erhai',
    source_type: 'demo',
    source_id: 'demo-2',
    name: '洱海西岸慢骑',
    city: '大理',
    rating: 4.8,
    price: 128,
    description: '更适合慢节奏游客的一段湖岸路线，光线柔和，适合骑行与日落停留。',
    cover_image: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?q=80&w=1600&auto=format&fit=crop',
    tags: ['湖景', '骑行', '休闲'],
    opening_hours: '全天开放',
    visit_duration: '2-4小时',
    booking_required: '无需预订',
    address: '云南大理洱海西岸',
    recommendation_reason: '适合游客浏览的精选湖景线路',
    in_itinerary: false,
  },
  {
    id: 'demo-yading',
    spot_key: 'demo-yading',
    source_type: 'demo',
    source_id: 'demo-3',
    name: '亚丁雪岭环眺',
    city: '甘孜',
    rating: 4.9,
    price: 260,
    description: '视野开阔、山体层次分明，适合想看高海拔风景但不想走太长线路的游客。',
    cover_image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1600&auto=format&fit=crop',
    tags: ['山岳', '自然', '观景'],
    opening_hours: '周一至周日 07:30-17:30',
    visit_duration: '6-8小时',
    booking_required: '建议提前预订',
    address: '四川甘孜稻城县香格里拉镇',
    recommendation_reason: '与你加入行程的自然风格相近',
    in_itinerary: false,
  },
  {
    id: 'demo-westlake',
    spot_key: 'demo-westlake',
    source_type: 'demo',
    source_id: 'demo-4',
    name: '西湖北山漫游',
    city: '杭州',
    rating: 4.7,
    price: 0,
    description: '经典城市漫游线，树荫多、步行舒适，适合第一次到访时轻松浏览。',
    cover_image: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1600&auto=format&fit=crop',
    tags: ['城市漫游', '自然', '免费'],
    opening_hours: '全天开放',
    visit_duration: '2-3小时',
    booking_required: '无需预订',
    address: '浙江杭州西湖景区',
    recommendation_reason: '因为你偏好城市漫游与湖岸风景',
    in_itinerary: false,
  },
  {
    id: 'demo-lugu',
    spot_key: 'demo-lugu',
    source_type: 'demo',
    source_id: 'demo-5',
    name: '泸沽湖雾岸清晨',
    city: '丽江',
    rating: 4.8,
    price: 138,
    description: '清晨水汽和远山线条很干净，适合喜欢安静、拍照和慢节奏停留的人。',
    cover_image: 'https://images.unsplash.com/photo-1472396961693-142e6e269027?q=80&w=1600&auto=format&fit=crop',
    tags: ['湖景', '摄影', '安静'],
    opening_hours: '全天开放',
    visit_duration: '3-5小时',
    booking_required: '无需预订',
    address: '云南丽江宁蒗县泸沽湖',
    recommendation_reason: '高评分且风格清透克制',
    in_itinerary: false,
  },
  {
    id: 'demo-anji',
    spot_key: 'demo-anji',
    source_type: 'demo',
    source_id: 'demo-6',
    name: '安吉竹海山谷',
    city: '湖州',
    rating: 4.7,
    price: 96,
    description: '明亮、整洁、山谷感强，路线负担小，适合周末短途和家庭游客。',
    cover_image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1600&auto=format&fit=crop',
    tags: ['山谷', '家庭', '轻松'],
    opening_hours: '周一至周日 08:00-17:00',
    visit_duration: '3-4小时',
    booking_required: '无需预订',
    address: '浙江湖州安吉竹海景区',
    recommendation_reason: '价格友好且适合作为轻松出游方案',
    in_itinerary: false,
  },
]

const buildQuery = (filters: DiscoveryFilters = {}) => {
  const query = new URLSearchParams()

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && String(item).trim() !== '') {
          query.append(key, String(item))
        }
      })
      return
    }
    query.set(key, String(value))
  })

  const text = query.toString()
  return text ? `?${text}` : ''
}

const filterDemoSpots = (filters: DiscoveryFilters = {}) => {
  const query = (filters.q || '').trim().toLowerCase()
  const city = (filters.city || '').trim()
  const minPrice = filters.min_price ?? null
  const maxPrice = filters.max_price ?? null
  const minRating = filters.min_rating ?? null
  const tag = (filters.tag || '').trim()
  const tags = (filters.tags || []).map((item) => String(item).trim()).filter(Boolean)
  const sort = filters.sort || 'recommended'

  const items = DEMO_SPOTS.filter((spot) => {
    if (city && spot.city !== city) {
      return false
    }
    if (minPrice !== null && spot.price < minPrice) {
      return false
    }
    if (maxPrice !== null && spot.price > maxPrice) {
      return false
    }
    if (minRating !== null && spot.rating < minRating) {
      return false
    }
    const effectiveTags = tags.length ? tags : tag ? [tag] : []
    if (effectiveTags.length && !effectiveTags.some((item) => spot.tags.includes(item))) {
      return false
    }
    if (query) {
      const haystack = `${spot.name} ${spot.city} ${spot.description} ${spot.tags.join(' ')}`.toLowerCase()
      if (!haystack.includes(query)) {
        return false
      }
    }
    return true
  })

  const sorted = [...items]
  if (sort === 'price_asc') {
    sorted.sort((a, b) => a.price - b.price || b.rating - a.rating)
  } else if (sort === 'rating_desc') {
    sorted.sort((a, b) => b.rating - a.rating || a.price - b.price)
  } else {
    sorted.sort((a, b) => b.rating - a.rating || a.price - b.price)
  }

  return sorted
}

const buildDemoDiscoveryList = (filters: DiscoveryFilters = {}): DiscoveryListResponse => {
  const filtered = filterDemoSpots(filters)
  const limit = filters.limit || 0
  const visible = limit ? filtered.slice(0, limit) : filtered
  return {
    items: mergeGuestFlags(visible.map((item) => ({ ...item }))),
    filters: {
      cities: Array.from(new Set(DEMO_SPOTS.map((item) => item.city))).sort(),
      tags: Array.from(new Set(DEMO_SPOTS.flatMap((item) => item.tags))).sort(),
    },
    total: filtered.length,
    source: 'local_demo',
  }
}

const getToken = async () => {
  const session = await safeGetSupabaseSession()
  return session?.access_token || ''
}

const isNetworkLikeError = (error: unknown) => {
  const message = String((error as any)?.message || error || '')
  return [
    'Failed to fetch',
    'NetworkError',
    'ERR_CONNECTION_REFUSED',
    'ERR_CONNECTION_RESET',
    'Load failed',
  ].some((token) => message.includes(token))
}

const request = async <T>(url: string, options: RequestOptions = {}): Promise<T> => {
  try {
    const token = await getToken()
    const { requireAuth = false } = options

    if (requireAuth && !token) {
      throw new Error(LOGIN_REQUIRED_ERROR)
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    if (!response.ok) {
      let message = response.status >= 500 ? GENERIC_DATA_SOURCE_ERROR : `Request failed: ${response.status}`

      try {
        const rawText = await response.text()
        if (rawText) {
          try {
            const data = JSON.parse(rawText)
            message = data.error || data.detail || message
          } catch {
            if (response.status < 500) {
              message = rawText
            }
          }
        }
      } catch {
        // Keep fallback message.
      }

      throw new Error(message)
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  } catch (error) {
    if (isNetworkLikeError(error)) {
      throw new Error(GENERIC_DATA_SOURCE_ERROR)
    }
    throw error
  }
}

const readGuestItinerary = (): ItineraryItem[] => {
  try {
    const raw = localStorage.getItem(GUEST_ITINERARY_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const writeGuestItinerary = (items: ItineraryItem[]) => {
  localStorage.setItem(GUEST_ITINERARY_KEY, JSON.stringify(items))
}

const toSummary = (items: ItineraryItem[]): ItinerarySummary => {
  const cityMap = new Map<string, ItineraryCityGroup>()
  let budgetTotal = 0

  items.forEach((item) => {
    budgetTotal += Number(item.price || 0)
    const city = item.city || UNKNOWN_CITY
    const group = cityMap.get(city) || {
      city,
      count: 0,
      budget_total: 0,
    }
    group.count += 1
    group.budget_total += Number(item.price || 0)
    cityMap.set(city, group)
  })

  return {
    items_count: items.length,
    budget_total: Number(budgetTotal.toFixed(2)),
    city_groups: Array.from(cityMap.values()).sort((a, b) => {
      if (b.count !== a.count) {
        return b.count - a.count
      }
      return a.city.localeCompare(b.city)
    }),
  }
}

const guestSpotKeys = () => new Set(readGuestItinerary().map((item) => item.spot_key))

const mergeGuestFlags = <T extends { spot_key: string; in_itinerary: boolean }>(items: T[]): T[] => {
  const keys = guestSpotKeys()
  return items.map((item) => ({
    ...item,
    in_itinerary: item.in_itinerary || keys.has(item.spot_key),
  }))
}

const toGuestItem = (spot: SpotItem, recommendationReason?: string): ItineraryItem => ({
  item_id: `guest-${spot.spot_key}`,
  spot_key: spot.spot_key,
  spot_name: spot.name,
  city: spot.city,
  price: Number(spot.price || 0),
  rating: Number(spot.rating || 0),
  cover_image: spot.cover_image,
  recommendation_reason: recommendationReason || spot.recommendation_reason || '',
  tags: spot.tags || [],
  spot_snapshot: {
    spot_key: spot.spot_key,
    name: spot.name,
    city: spot.city,
    price: spot.price,
    rating: spot.rating,
    cover_image: spot.cover_image,
    description: spot.description,
    tags: spot.tags || [],
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
})

const hasSession = async () => {
  const session = await safeGetSupabaseSession()
  return Boolean(session?.user)
}

export const travelDiscoveryService = {
  async listSpots(filters: DiscoveryFilters = {}) {
    if (USE_LOCAL_DISCOVERY_DEMO) {
      return buildDemoDiscoveryList(filters)
    }

    const data = await request<DiscoveryListResponse>(`/api/discovery/spots/${buildQuery(filters)}`)
    return {
      ...data,
      items: mergeGuestFlags(data.items || []),
    }
  },

  async getSpotDetail(spotKey: string) {
    if (USE_LOCAL_DISCOVERY_DEMO) {
      const item = DEMO_SPOTS.find((spot) => spot.spot_key === spotKey) || null
      if (!item) {
        return null
      }
      return {
        ...item,
        similar_spots: DEMO_SPOTS.filter((spot) => spot.spot_key !== spotKey).slice(0, 4),
      } as SpotDetailResponse
    }

    const data = await request<SpotDetailResponse>(`/api/discovery/spots/${encodeURIComponent(spotKey)}/`)
    return {
      ...data,
      in_itinerary: Boolean(data.in_itinerary),
      similar_spots: mergeGuestFlags(data.similar_spots || []),
    }
  },

  getGuestItinerary() {
    const items = readGuestItinerary()
    return {
      items,
      summary: toSummary(items),
      mode: 'guest' as const,
    }
  },

  replaceGuestItinerary(items: ItineraryItem[]) {
    writeGuestItinerary(items)
    return {
      items,
      summary: toSummary(items),
      mode: 'guest' as const,
    }
  },

  async addToItinerary(spot: SpotItem, recommendationReason?: string) {
    if (await hasSession()) {
      return request<{ item: ItineraryItem; summary: ItinerarySummary }>('/api/itinerary/items/', {
        method: 'POST',
        body: {
          spot_key: spot.spot_key,
          recommendation_reason: recommendationReason || spot.recommendation_reason || '',
        },
        requireAuth: true,
      })
    }

    const items = readGuestItinerary()
    const nextItem = toGuestItem(spot, recommendationReason)
    const nextItems = items.some((item) => item.spot_key === spot.spot_key)
      ? items.map((item) =>
          item.spot_key === spot.spot_key
            ? { ...item, ...nextItem, updated_at: new Date().toISOString() }
            : item,
        )
      : [nextItem, ...items]

    writeGuestItinerary(nextItems)

    return {
      item: nextItem,
      summary: toSummary(nextItems),
    }
  },

  async removeItineraryItem(itemId: string | number) {
    if (await hasSession() && typeof itemId === 'number') {
      return request<{ summary: ItinerarySummary }>(`/api/itinerary/items/${itemId}/`, {
        method: 'DELETE',
        requireAuth: true,
      })
    }

    const nextItems = readGuestItinerary().filter((item) => item.item_id !== itemId)
    writeGuestItinerary(nextItems)
    return {
      summary: toSummary(nextItems),
    }
  },

  async syncGuestItineraryToAccount() {
    if (!(await hasSession())) {
      return 0
    }

    const guestItems = readGuestItinerary()
    if (!guestItems.length) {
      return 0
    }

    for (const item of guestItems) {
      await request('/api/itinerary/items/', {
        method: 'POST',
        body: {
          spot_key: item.spot_key,
          recommendation_reason: item.recommendation_reason,
        },
        requireAuth: true,
      })
    }

    localStorage.removeItem(GUEST_ITINERARY_KEY)
    return guestItems.length
  },

  async loadItinerary() {
    if (await hasSession()) {
      await this.syncGuestItineraryToAccount()
      const data = await request<Omit<ItineraryResponse, 'mode'>>('/api/itinerary/', {
        requireAuth: true,
      })
      return {
        ...data,
        mode: 'account' as const,
      }
    }

    return this.getGuestItinerary()
  },

  async listBookingIntents() {
    const data = await request<{ items: BookingIntent[] }>('/api/booking-intents/', {
      requireAuth: true,
    })
    return data.items || []
  },

  async createBookingIntent(payload: {
    trip_name?: string
    contact_name?: string
    contact_phone?: string
    note?: string
    item_ids?: Array<number | string>
  }) {
    return request<BookingIntent>('/api/booking-intents/', {
      method: 'POST',
      body: payload,
      requireAuth: true,
    })
  },

  async isLoggedIn() {
    return hasSession()
  },
}
