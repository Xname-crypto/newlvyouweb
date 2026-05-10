<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDown, ChevronLeft, Heart } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import CheckoutSteps from '@/components/CheckoutSteps.vue'
import { commerceService, getProductImage, type Product } from '@/services/commerceService'
import { profileService } from '@/services/profileService'
import { readCheckoutDraft, writeCheckoutDraft } from '@/services/checkoutService'
import { getCartItemImage, type CartItem } from '@/services/cartService'
import { DEFAULT_AVATAR } from '@/utils/avatar'
import { safeGetSupabaseSession } from '@/utils/supabase'
import chinaRegionsRaw from '@/data/china-regions.json'

interface RegionArea {
  area: string
}

interface RegionCity {
  city: string
  areas?: RegionArea[]
}

interface RegionProvince {
  province: string
  citys?: RegionCity[]
}

const router = useRouter()
const draft = ref(readCheckoutDraft())
const errorMessage = ref('')
const discountMessage = ref('')
const discountCode = ref('')
const keepUpdated = ref(false)
const accountEmail = ref('')
const accountName = ref('')
const accountAvatar = ref(DEFAULT_AVATAR)
const recommendedProducts = ref<Product[]>([])
const RECOMMENDATION_CACHE_KEY = 'ct_checkout_recommendations'
const NAV_PROFILE_CACHE_KEY = 'ct_nav_profile_cache'
const chinaRegions = (chinaRegionsRaw as RegionProvince[]).filter((item) => item?.province)

const normalizeRegionText = (value: string) => {
  try {
    return decodeURIComponent(escape(value))
  } catch {
    return value
  }
}

const hasItems = computed(() => draft.value.items.length > 0)
const subtotalValue = computed(() => draft.value.items.reduce((sum, item) => sum + Number(String(item.price).replace(/[^\d.]/g, '')) * item.quantity, 0))
const subtotal = computed(() => subtotalValue.value.toFixed(2))
const total = computed(() => subtotalValue.value.toFixed(2))

const hideBrokenCartImage = (event: Event) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const readCachedProfile = (userId: string) => {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(`${NAV_PROFILE_CACHE_KEY}:${userId}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const useFallbackAvatar = (event: Event) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.src = DEFAULT_AVATAR
}

const fullName = computed({
  get() {
    return [draft.value.shippingAddress.last_name, draft.value.shippingAddress.first_name].filter(Boolean).join(' ').trim()
  },
  set(value: string) {
    const normalized = value.trim().replace(/\s+/g, ' ')
    if (!normalized) {
      draft.value.shippingAddress.first_name = ''
      draft.value.shippingAddress.last_name = ''
      return
    }

    const parts = normalized.split(' ')
    if (parts.length === 1) {
      draft.value.shippingAddress.last_name = ''
      draft.value.shippingAddress.first_name = parts[0]
      return
    }

    draft.value.shippingAddress.last_name = parts[0]
    draft.value.shippingAddress.first_name = parts.slice(1).join(' ')
  },
})
const displayAccountName = computed(() => {
  if (accountName.value.trim()) return accountName.value.trim()
  const fallbackEmail = accountEmail.value || draft.value.shippingAddress.email || ''
  return fallbackEmail ? fallbackEmail.split('@')[0] : '当前用户'
})
const normalizedChinaRegions = computed(() =>
  chinaRegions.map((province) => ({
    province: normalizeRegionText(province.province),
    citys: (province.citys || []).map((city) => ({
      city: normalizeRegionText(city.city),
      areas: (city.areas || []).map((area) => ({
        area: normalizeRegionText(area.area),
      })),
    })),
  })),
)
const provinceOptions = computed(() => normalizedChinaRegions.value.map((item) => item.province))
const activeProvince = computed(() => normalizedChinaRegions.value.find((item) => item.province === draft.value.shippingAddress.country) || null)
const cityOptions = computed(() => (activeProvince.value?.citys || []).map((item) => item.city))
const activeCity = computed(() => (activeProvince.value?.citys || []).find((item) => item.city === draft.value.shippingAddress.city) || null)
const districtOptions = computed(() => (activeCity.value?.areas || []).map((item) => item.area))

const writeRecommendationCache = (products: Product[]) => {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(RECOMMENDATION_CACHE_KEY, JSON.stringify(products.slice(0, 8).map((product) => ({
      id: product.id,
      sku: product.sku,
      name: product.name,
      category: product.category,
    image_url: getProductImage(product),
      price: product.price,
      price_cents: product.price_cents,
      currency: product.currency,
      metadata: {
        old_price_cents: product.metadata?.old_price_cents,
      },
    }))))
  } catch {
    window.sessionStorage.removeItem(RECOMMENDATION_CACHE_KEY)
  }
}

watch(
  () => draft.value.shippingAddress.country,
  () => {
    if (!activeProvince.value) {
      draft.value.shippingAddress.city = ''
      draft.value.shippingAddress.post_code = ''
      return
    }

    if (!cityOptions.value.includes(draft.value.shippingAddress.city)) {
      draft.value.shippingAddress.city = ''
    }

    if (!districtOptions.value.includes(draft.value.shippingAddress.post_code)) {
      draft.value.shippingAddress.post_code = ''
    }
  },
  { immediate: true },
)

watch(
  () => draft.value.shippingAddress.city,
  () => {
    if (!activeCity.value) {
      draft.value.shippingAddress.post_code = ''
      return
    }

    if (!districtOptions.value.includes(draft.value.shippingAddress.post_code)) {
      draft.value.shippingAddress.post_code = ''
    }
  },
  { immediate: true },
)

const loadRecommendations = async () => {
  try {
    const products = await commerceService.listProducts()
    const cartProductIds = new Set(draft.value.items.map((item) => item.productId).filter(Boolean))
    recommendedProducts.value = products.filter((product) => !cartProductIds.has(product.id)).slice(0, 8)
    writeRecommendationCache(recommendedProducts.value)
  } catch (error) {
    console.error('Failed to load recommended products:', error)
    recommendedProducts.value = []
  }
}

const loadAccount = async () => {
  const session = await safeGetSupabaseSession()
  const user = session?.user || null
  accountEmail.value = user?.email || draft.value.shippingAddress.email || ''
  if (!user?.id) {
    accountName.value = ''
    accountAvatar.value = DEFAULT_AVATAR
    return
  }

  const cachedProfile = readCachedProfile(user.id)
  if (cachedProfile) {
    accountName.value = String(cachedProfile.username || '').trim()
    accountAvatar.value = String(cachedProfile.avatar_url || DEFAULT_AVATAR)
  }

  const profile = await profileService.fetchProfile(user.id)
  if (!profile) return
  accountName.value = String(profile.username || '').trim()
  accountAvatar.value = String(profile.avatar_url || accountAvatar.value || DEFAULT_AVATAR)
}

const refreshDraftItemsFromProducts = async () => {
  const productIds = Array.from(new Set(draft.value.items.map((item) => item.productId).filter(Boolean))) as number[]
  if (!productIds.length) return

  const products = await commerceService.listProducts()
  const productById = new Map(products.map((product) => [product.id, product]))
  draft.value.items = draft.value.items.map((item) => {
    if (!item.productId) return item
    const product = productById.get(item.productId)
    if (!product) return item
    const productImage = getProductImage(product)
    const requiresSize = product.metadata?.requires_size !== false && Array.isArray(product.metadata?.sizes) && product.metadata.sizes.length > 0
    return {
      ...item,
      size: requiresSize ? item.size : '',
      meta: [requiresSize ? item.size : '', item.color].filter(Boolean).join(' / ') || product.category || product.sku,
      price: product.price || ((product.price_cents || 0) / 100).toFixed(2),
      image: getCartItemImage({ ...item, image: productImage }),
      productSnapshot: {
        ...(item.productSnapshot || {}),
        id: product.id,
        sku: product.sku,
        name: product.name,
        image_url: getCartItemImage({ ...item, image: productImage }),
        price_cents: product.price_cents,
        currency: product.currency,
        metadata: {
          shipping_cents: Number(item.shippingCents || item.productSnapshot?.metadata?.shipping_cents || 0) || 0,
          requires_size: requiresSize,
          requires_color: product.metadata?.requires_color === true,
        },
      },
    }
  })
  writeCheckoutDraft(draft.value)
}

const applyDiscount = () => {
  discountMessage.value = discountCode.value.trim() ? '当前暂未开放优惠码，请直接继续下单。' : '请输入优惠码。'
}

const continueNext = () => {
  const address = draft.value.shippingAddress
  const normalizedName = fullName.value.trim()
  const required = [
    normalizedName,
    address.address,
    address.city,
    address.country,
    address.post_code,
    address.phone,
  ]

  if (required.some((value) => !String(value || '').trim())) {
    errorMessage.value = '请先完整填写收货地址信息。'
    return
  }

  if (!address.first_name.trim() && normalizedName) {
    draft.value.shippingAddress.first_name = normalizedName
  }

  errorMessage.value = ''
  draft.value.contactEmail = address.email || draft.value.contactEmail || accountEmail.value
  draft.value.contactPhone = address.phone || draft.value.contactPhone
  writeCheckoutDraft(draft.value)
  router.push('/checkout/confirmation')
}

const formatProductPrice = (product: Product) => `¥${Number(product.price || ((product.price_cents || 0) / 100).toFixed(2)).toFixed(2)}`
const getOldPrice = (product: Product) => {
  const cents = Number(product.metadata?.old_price_cents || 0)
  return cents > 0 ? `¥${(cents / 100).toFixed(2)}` : ''
}

onMounted(async () => {
  if (!hasItems.value) {
    router.replace('/cart')
    return
  }

  await refreshDraftItemsFromProducts()
  await Promise.all([loadAccount(), loadRecommendations()])
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdfa] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <main class="mx-auto max-w-[1320px] px-6 pb-24 pt-[118px] lg:px-10">
      <CheckoutSteps current="contact" />

      <div class="mt-10 grid gap-14 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section>
          <h1 class="text-[34px] font-medium uppercase tracking-[0.08em] text-[#2f2c27]">联系信息</h1>

          <div class="mt-10 flex items-start gap-4">
            <div class="h-14 w-14 overflow-hidden rounded-full bg-[#cfcfcf]">
              <img :src="accountAvatar" alt="用户头像" class="h-full w-full object-cover" @error="useFallbackAvatar" />
            </div>
            <div class="min-w-0">
              <p class="text-lg text-[#373737]">{{ accountEmail || draft.shippingAddress.email || '当前账号' }}</p>
              <p class="mt-1 text-base text-[#444]">{{ displayAccountName }}</p>
            </div>
          </div>

          <label class="mt-6 inline-flex items-center gap-3 text-sm text-[#6b6b6b]">
            <input v-model="keepUpdated" class="h-5 w-5 border border-[#d1d1d1]" type="checkbox" />
            <span>接收新品动态与专属优惠信息</span>
          </label>

          <div class="mt-12">
            <h2 class="text-[20px] font-semibold text-[#2f2c27]">收货地址</h2>

            <div v-if="errorMessage" class="mt-5 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
              {{ errorMessage }}
            </div>

            <div class="mt-6 grid gap-4 sm:grid-cols-2">
              <input v-model="fullName" class="checkout-field sm:col-span-2" placeholder="姓名" />
              <div class="grid gap-4 sm:col-span-2 sm:grid-cols-3">
                <div class="checkout-select-wrap">
                  <select v-model="draft.shippingAddress.country" class="checkout-field checkout-select">
                    <option value="">省份</option>
                    <option v-for="province in provinceOptions" :key="province" :value="province">{{ province }}</option>
                  </select>
                  <ChevronDown :size="16" class="checkout-select-icon" />
                </div>

                <div class="checkout-select-wrap">
                  <select
                    v-model="draft.shippingAddress.city"
                    class="checkout-field checkout-select"
                    :disabled="!draft.shippingAddress.country"
                  >
                    <option value="">城市</option>
                    <option v-for="city in cityOptions" :key="city" :value="city">{{ city }}</option>
                  </select>
                  <ChevronDown :size="16" class="checkout-select-icon" />
                </div>

                <div class="checkout-select-wrap">
                  <select
                    v-model="draft.shippingAddress.post_code"
                    class="checkout-field checkout-select"
                    :disabled="!draft.shippingAddress.city"
                  >
                    <option value="">地区</option>
                    <option v-for="district in districtOptions" :key="district" :value="district">{{ district }}</option>
                  </select>
                  <ChevronDown :size="16" class="checkout-select-icon" />
                </div>
              </div>
              <input v-model="draft.shippingAddress.address" class="checkout-field sm:col-span-2" placeholder="详细地址" />
              <input v-model="draft.shippingAddress.apartment" class="checkout-field sm:col-span-2" placeholder="公寓、楼栋、门牌号等" />
              <input v-model="draft.shippingAddress.phone" class="checkout-field sm:col-span-2" placeholder="电话" />
              <input v-model="draft.shippingAddress.email" class="checkout-field sm:col-span-2" placeholder="邮箱" />
            </div>

            <div class="mt-8 flex flex-wrap items-center justify-between gap-4">
              <router-link to="/cart" class="inline-flex items-center gap-1 text-sm font-black text-[#2f2c27] transition-colors hover:text-[#efb299]">
                <ChevronLeft :size="14" />
                返回购物车
              </router-link>
              <button type="button" class="bg-[#f3b89d] px-10 py-4 text-sm font-black text-white transition-colors hover:bg-[#e8a085]" @click="continueNext">
                立即发货
              </button>
            </div>
          </div>
        </section>

        <aside class="xl:pt-[132px]">
          <div v-for="item in draft.items" :key="item.id" class="grid grid-cols-[74px_minmax(0,1fr)_auto] items-center gap-4 py-4">
            <div class="relative">
              <img v-if="item.image" :src="item.image" :alt="item.name" class="h-[74px] w-[74px] object-cover" @error="hideBrokenCartImage" />
              <span class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-[#f3b89d] text-xs font-bold text-white">
                {{ item.quantity }}
              </span>
            </div>
            <div class="min-w-0">
              <p class="truncate text-base font-medium text-[#393939]">{{ item.name }}</p>
              <p class="mt-1 text-sm text-[#6e6e6e]">{{ item.meta }}</p>
            </div>
            <span class="text-base font-medium text-[#393939]">¥{{ Number(String(item.price).replace(/[^\d.]/g, '')).toFixed(2) }}</span>
          </div>

          <div class="mt-5 border-t border-[#ddd8d0] pt-6">
            <div class="flex gap-3">
              <input v-model="discountCode" class="checkout-field !h-[50px] flex-1" placeholder="优惠码" />
              <button type="button" class="min-w-[92px] border border-[#f3b89d] px-5 text-base font-medium text-[#f3b89d] transition-colors hover:bg-[#fdf2ec]" @click="applyDiscount">
                使用
              </button>
            </div>
            <p v-if="discountMessage" class="mt-3 text-sm text-[#b97b61]">{{ discountMessage }}</p>
          </div>

          <div class="mt-5 border-y border-[#ddd8d0] py-5">
            <div class="mb-3 flex items-center justify-between text-base text-[#444]">
              <span>小计</span>
              <span>¥{{ subtotal }}</span>
            </div>
          </div>

          <div class="mt-5 flex items-end justify-between">
            <span class="text-[18px] font-medium text-[#383838]">合计</span>
            <span class="text-[42px] font-medium text-[#f09e7f]">¥{{ total }}</span>
          </div>
        </aside>
      </div>

      <section v-if="recommendedProducts.length" class="mt-24">
        <p class="text-sm font-black uppercase tracking-[0.08em] text-[#7d736a]">你可能也会喜欢</p>
        <div class="mt-8 grid grid-cols-2 gap-8 lg:grid-cols-4">
          <article v-for="product in recommendedProducts" :key="product.id" class="group">
            <router-link :to="{ name: 'product-detail', params: { id: String(product.id) } }" class="block">
              <div class="relative aspect-[0.82] overflow-hidden bg-[#f5f2ee]">
                <img v-if="getProductImage(product)" class="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" :src="getProductImage(product)" :alt="product.name" />
                <button type="button" class="absolute right-4 top-4 text-white/90">
                  <Heart :size="18" />
                </button>
              </div>
              <p class="mt-4 text-sm text-[#5f5952]">{{ product.name }}</p>
              <div class="mt-2 flex items-center gap-2 text-sm">
                <span v-if="getOldPrice(product)" class="text-[#b7afa6] line-through">{{ getOldPrice(product) }}</span>
                <span class="font-medium text-[#f09e7f]">{{ formatProductPrice(product) }}</span>
              </div>
            </router-link>
          </article>
        </div>
      </section>
    </main>

    <Footer variant="white" />
  </div>
</template>

<style scoped>
.checkout-field {
  height: 46px;
  border: 1px solid #cac5be;
  background: #ffffff;
  padding: 0 20px;
  font-size: 15px;
  color: #383838;
  outline: none;
}

.checkout-field::placeholder {
  color: #8b8b96;
}

.checkout-select-wrap {
  position: relative;
}

.checkout-select {
  width: 100%;
  cursor: pointer;
  appearance: none;
  padding-right: 42px;
}

.checkout-select:disabled {
  cursor: not-allowed;
  color: #a0a0a0;
  background: #faf8f5;
}

.checkout-select-icon {
  position: absolute;
  top: 50%;
  right: 16px;
  pointer-events: none;
  color: #7f7a73;
  transform: translateY(-50%);
}
</style>
