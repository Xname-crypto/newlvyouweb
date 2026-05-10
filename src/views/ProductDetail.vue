<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Heart,
  Minus,
  PackageCheck,
  Plus,
  RotateCcw,
  Ruler,
  Share2,
  ShieldCheck,
  ShoppingBag,
  Star,
  Truck,
  X,
} from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { commerceService, getProductImage as resolveProductImage, getProductImages, isUsableProductImage, type Product } from '@/services/commerceService'
import { addCartItem } from '@/services/cartService'

const route = useRoute()
const router = useRouter()

type ViewedProduct = {
  id: number
  name: string
  price: string
  image: string
  viewedAt: number
}

const fallbackSizes = ['S', 'M', 'L', 'XL']
const fallbackColors: { name: string; value: string }[] = [
  { name: '雾松绿', value: '#5f7564' },
  { name: '岩石灰', value: '#8f8b82' },
  { name: '沙丘米', value: '#d8c49b' },
].filter(() => false)

const sizeGuideRows = [
  { size: 'S', chest: '106', length: '66', shoulder: '45', height: '160-170' },
  { size: 'M', chest: '112', length: '69', shoulder: '47', height: '170-178' },
  { size: 'L', chest: '118', length: '72', shoulder: '49', height: '178-185' },
  { size: 'XL', chest: '124', length: '75', shoulder: '51', height: '185-192' },
]


const product = ref<Product | null>(null)
const recommendedProducts = ref<Product[]>([])
const recentlyViewedProducts = ref<ViewedProduct[]>([])
const loading = ref(false)
const errorMessage = ref('')
const selectedImage = ref(0)
const selectedSize = ref('M')
const selectedColor = ref<{ name: string; value: string }>({ name: '', value: '' })
const quantity = ref(1)
const isFavourite = ref(false)
const isSizeGuideOpen = ref(false)
const openSections = ref(new Set(['details', 'fit']))
const addedMessage = ref('')
let productLoadSequence = 0

const productId = computed(() => String(route.params.id ?? ''))
const productName = computed(() => product.value?.name || '')
const productDescription = computed(() => product.value?.description || '')
const productPrice = computed(() => (product.value ? `¥${product.value.price || '0.00'}` : ''))
const productOldPrice = computed(() => {
  const cents = Number(product.value?.metadata?.old_price_cents || 0)
  return cents > 0 ? `¥${(cents / 100).toFixed(2)}` : ''
})
const productCode = computed(() => product.value?.sku || '')
const isSoldOut = computed(() => !!product.value && product.value.available_stock <= 0)
const maxQuantity = computed(() => Math.max(1, Math.min(9, product.value?.available_stock || 9)))
const isReady = computed(() => !!product.value && !loading.value)
const RECENTLY_VIEWED_KEY = 'lvyou_recently_viewed_products'
const RECENTLY_VIEWED_LIMIT = 12
const RECENTLY_VIEWED_FALLBACK_LIMITS = [RECENTLY_VIEWED_LIMIT, 6, 2]
const RECENTLY_VIEWED_NAME_LIMIT = 80
const RECENTLY_VIEWED_PRICE_LIMIT = 24
const RECENTLY_VIEWED_IMAGE_LIMIT = 1000
const getProductImage = (item: Product) => resolveProductImage(item)

const getProductDisplayPrice = (item: Product) => `¥${item.price || ((item.price_cents || 0) / 100).toFixed(2)}`

const trimStoredText = (value: unknown, maxLength: number) => String(value || '').slice(0, maxLength)

const normalizeStoredImage = (value: unknown) => {
  const image = trimStoredText(value, RECENTLY_VIEWED_IMAGE_LIMIT)
  if (image.startsWith('data:')) return ''
  return image
}

const getViewedProductImage = (item: ViewedProduct) => (isUsableProductImage(item.image) ? item.image : '')

const normalizeViewedProduct = (item: any): ViewedProduct | null => {
  const id = Number(item?.id)
  if (!Number.isFinite(id) || id <= 0) return null

  const viewedAt = Number(item?.viewedAt)
  return {
    id,
    name: trimStoredText(item?.name, RECENTLY_VIEWED_NAME_LIMIT),
    price: trimStoredText(item?.price, RECENTLY_VIEWED_PRICE_LIMIT),
    image: normalizeStoredImage(item?.image),
    viewedAt: Number.isFinite(viewedAt) ? viewedAt : 0,
  }
}

const readRecentlyViewed = () => {
  if (typeof localStorage === 'undefined') return []

  try {
    const parsed = JSON.parse(localStorage.getItem(RECENTLY_VIEWED_KEY) || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed
      .map(normalizeViewedProduct)
      .filter((item): item is ViewedProduct => !!item)
      .slice(0, RECENTLY_VIEWED_LIMIT)
  } catch {
    try {
      localStorage.removeItem(RECENTLY_VIEWED_KEY)
    } catch {
      // Ignore storage access failures.
    }
    return []
  }
}

const persistRecentlyViewed = (items: ViewedProduct[]) => {
  if (typeof localStorage === 'undefined') return

  const normalizedItems = items
    .map(normalizeViewedProduct)
    .filter((item): item is ViewedProduct => !!item)

  for (const limit of RECENTLY_VIEWED_FALLBACK_LIMITS) {
    try {
      localStorage.setItem(RECENTLY_VIEWED_KEY, JSON.stringify(normalizedItems.slice(0, limit)))
      return
    } catch {
      // Try a smaller payload before giving up.
    }
  }

  try {
    localStorage.removeItem(RECENTLY_VIEWED_KEY)
  } catch {
    // Ignore storage quota, private mode, or disabled storage failures.
  }
}

const writeRecentlyViewed = (item: Product) => {
  const nextItem: ViewedProduct = {
    id: item.id,
    name: trimStoredText(item.name, RECENTLY_VIEWED_NAME_LIMIT),
    price: trimStoredText(getProductDisplayPrice(item), RECENTLY_VIEWED_PRICE_LIMIT),
    image: normalizeStoredImage(getProductImage(item)),
    viewedAt: Date.now(),
  }
  const next = [nextItem, ...readRecentlyViewed().filter((recent) => recent.id !== item.id)].slice(0, RECENTLY_VIEWED_LIMIT)
  persistRecentlyViewed(next)
}

const loadRecentlyViewed = () => {
  recentlyViewedProducts.value = readRecentlyViewed()
    .filter((item) => item.id !== Number(productId.value))
    .sort((a, b) => b.viewedAt - a.viewedAt)
    .slice(0, 2)
}

const shuffleProducts = (items: Product[]) => {
  const next = [...items]
  for (let index = next.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    ;[next[index], next[swapIndex]] = [next[swapIndex], next[index]]
  }
  return next
}

const loadRecommendations = async (currentProductId = Number(productId.value), sequence = productLoadSequence) => {
  try {
    const items = await commerceService.listProducts()
    if (sequence !== productLoadSequence) return
    const candidates = shuffleProducts(items.filter((item) => (
      item.id !== currentProductId
      && item.is_active
      && Number(item.available_stock || 0) > 0
    )))
    recommendedProducts.value = candidates.slice(0, 4)
  } catch {
    if (sequence !== productLoadSequence) return
    recommendedProducts.value = []
  }
}

const parseMetadataList = (field: 'sizes' | 'colors') => {
  const value = product.value?.metadata?.[field]
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : []
}

const isApparelProduct = computed(() => {
  if (!product.value) return false

  if (product.value.metadata?.requires_size === false) return false
  const configuredSizes = parseMetadataList('sizes')
  if (configuredSizes.length) return true

  const category = String(product.value.category || '')
  const type = String(product.value.metadata?.type || product.value.metadata?.product_type || '')
  const text = `${category} ${type} ${product.value.name}`.toLowerCase()
  const apparelKeywords = ['男装', '女装', '童装', '服装', '衣', 't恤', '卫衣', '衬衫', '背心', '裙', '裤', '外套', '马甲', '针织']

  return apparelKeywords.some((keyword) => text.includes(keyword.toLowerCase()))
})

const gallery = computed(() => {
  if (!product.value) return []
  return getProductImages(product.value).filter(isUsableProductImage)
})

const currentImage = computed(() => gallery.value[selectedImage.value] || gallery.value[0] || (product.value ? getProductImage(product.value) : ''))

const useFallbackImage = (event: Event, item?: Partial<Product> | ViewedProduct) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const availableSizes = computed(() => {
  if (!isApparelProduct.value) return []

  const productSizes = parseMetadataList('sizes')
  return productSizes.length ? productSizes : fallbackSizes
})

const availableColors = computed(() => {
  if (product.value?.metadata?.requires_color !== true) return []
  const productColors = parseMetadataList('colors')
  return productColors.map((value) => ({ name: value, value }))
})

const sections = computed(() => {
  const baseSections = [
    {
    id: 'details',
    title: '商品详情',
    body: productDescription.value,
    },
  ]

  if (isApparelProduct.value) {
    baseSections.push({
      id: 'fit',
      title: '尺码与版型',
      body: '标准宽松版型，内搭 T 恤或薄卫衣都舒适。建议按照平时外套尺码选择，喜欢宽松可选大一码。',
    })
  }

  baseSections.push({
    id: 'care',
    title: '材质与护理',
    body: String(product.value?.metadata?.care || '建议冷水轻柔洗涤，悬挂晾干，避免高温烘干。'),
  })

  baseSections.push({
    id: 'delivery',
    title: '配送与退换',
    body: '预计 2-4 天发货。支持 7 天无理由退换，保持吊牌和外包装完整即可。',
  })

  return baseSections
})

const selectImage = (index: number) => {
  selectedImage.value = index
}

const showPreviousImage = () => {
  if (!gallery.value.length) return
  selectedImage.value = selectedImage.value === 0 ? gallery.value.length - 1 : selectedImage.value - 1
}

const showNextImage = () => {
  if (!gallery.value.length) return
  selectedImage.value = selectedImage.value === gallery.value.length - 1 ? 0 : selectedImage.value + 1
}

const toggleSection = (id: string) => {
  const next = new Set(openSections.value)

  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }

  openSections.value = next
}

const updateQuantity = (amount: number) => {
  quantity.value = Math.min(maxQuantity.value, Math.max(1, quantity.value + amount))
}

const addToBag = () => {
  if (!product.value) return

  if (isSoldOut.value) {
    addedMessage.value = '该商品暂时缺货，暂不能加入购物车'
    return
  }

  const colorName = availableColors.value.length ? (selectedColor.value.name || selectedColor.value.value) : ''
  const sizeValue = isApparelProduct.value ? selectedSize.value : ''
  addCartItem({
    id: `${product.value.id}:${sizeValue || 'default'}:${colorName || 'default'}`,
    productId: product.value.id,
    name: product.value.name,
    sku: product.value.sku,
    meta: [sizeValue, colorName].filter(Boolean).join(' / ') || product.value.category || product.value.sku,
    size: sizeValue,
    color: colorName,
    price: product.value.price || ((product.value.price_cents || 0) / 100).toFixed(2),
    image: currentImage.value || getProductImage(product.value),
    quantity: quantity.value,
    currency: product.value.currency,
    productSnapshot: {
      id: product.value.id,
      sku: product.value.sku,
      name: product.value.name,
      image_url: getProductImage(product.value),
      price_cents: product.value.price_cents,
      currency: product.value.currency,
      metadata: {
        shipping_cents: 0,
        requires_size: isApparelProduct.value,
        requires_color: availableColors.value.length > 0,
      },
    },
  })

  addedMessage.value = `已加入购物车：${productName.value} / ${sizeValue || '-'} / ${colorName} / ${quantity.value} 件`
}

const goBack = () => {
  router.push('/product-catalogue')
}

const loadProduct = async () => {
  const sequence = productLoadSequence + 1
  productLoadSequence = sequence
  const currentProductId = Number(productId.value)
  loading.value = true
  errorMessage.value = ''
  product.value = null
  recommendedProducts.value = []
  selectedImage.value = 0
  quantity.value = 1
  addedMessage.value = ''

  try {
    product.value = await commerceService.getProduct(productId.value)
    loadRecentlyViewed()
    writeRecentlyViewed(product.value)
    loading.value = false
    void loadRecommendations(currentProductId, sequence)
  } catch (error) {
    if (sequence !== productLoadSequence) return
    errorMessage.value = String((error as any)?.message || error || '商品详情加载失败，请稍后再试。')
  } finally {
    loading.value = false
  }
}

watch(availableSizes, (nextSizes) => {
  selectedSize.value = nextSizes.includes(selectedSize.value) ? selectedSize.value : nextSizes[0] || 'M'
}, { immediate: true })

watch(availableColors, (nextColors) => {
  selectedColor.value = nextColors.find((color) => color.value === selectedColor.value.value) || nextColors[0] || { name: '', value: '' }
}, { immediate: true })

watch(productId, loadProduct)

onMounted(loadProduct)
</script>

<template>
  <div class="min-h-screen bg-[#fbfaf7] text-[#292720]">
    <Navigation variant="solid-light" show-cart />

    <main class="pt-[92px]">
      <section class="mx-auto max-w-[1500px] px-5 pb-20 pt-8 sm:px-8 lg:px-16">
        <div class="mb-8 flex flex-wrap items-center justify-between gap-4 text-sm text-[#958b7c]">
          <div class="flex items-center gap-2">
            <router-link to="/shop" class="font-semibold transition-colors hover:text-[#c9785f]">创意周边</router-link>
            <span>/</span>
            <router-link to="/product-catalogue" class="font-semibold transition-colors hover:text-[#c9785f]">旅行装备</router-link>
            <span>/</span>
            <span class="text-[#292720]">{{ productName || '商品详情' }}</span>
          </div>
          <button class="inline-flex items-center gap-2 font-bold text-[#665d52] transition-colors hover:text-[#c9785f]" type="button" @click="goBack">
            <ArrowLeft :size="17" />
            返回列表
          </button>
        </div>

        <div class="grid gap-10 lg:grid-cols-[minmax(0,1.08fr)_minmax(410px,0.92fr)] xl:gap-16">
          <section class="grid gap-5 md:grid-cols-[92px_minmax(0,1fr)]">
            <div class="order-2 flex gap-3 overflow-x-auto md:order-1 md:flex-col md:overflow-visible">
              <template v-if="gallery.length">
                <button
                  v-for="(image, index) in gallery"
                  :key="image"
                  class="h-[92px] w-[74px] shrink-0 overflow-hidden border bg-white transition md:h-[108px] md:w-[84px]"
                  :class="selectedImage === index ? 'border-[#e59a7d]' : 'border-transparent opacity-70 hover:opacity-100'"
                  type="button"
                  @click="selectImage(index)"
                >
                  <img class="h-full w-full object-cover" :src="image" :alt="`${productName}缩略图 ${index + 1}`" />
                </button>
              </template>
              <template v-else>
                <div v-for="item in 5" :key="item" class="h-[92px] w-[74px] shrink-0 animate-pulse bg-[#eadfd5] md:h-[108px] md:w-[84px]"></div>
              </template>
            </div>

            <div class="relative order-1 aspect-[4/5] min-h-[420px] overflow-hidden bg-[#ece7de] md:order-2">
              <img v-if="currentImage" class="h-full w-full object-cover transition duration-500" :src="currentImage" :alt="productName" @error="useFallbackImage($event, product || undefined)" />
              <div v-else class="h-full w-full animate-pulse bg-[#eadfd5]"></div>
              <template v-if="gallery.length > 1">
                <button
                  class="absolute left-5 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center bg-white/92 text-[#5f574e] shadow-sm transition hover:bg-[#eaa07f] hover:text-white"
                  type="button"
                  aria-label="上一张商品图"
                  @click="showPreviousImage"
                >
                  <ChevronLeft :size="20" />
                </button>
                <button
                  class="absolute right-5 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center bg-white/92 text-[#5f574e] shadow-sm transition hover:bg-[#eaa07f] hover:text-white"
                  type="button"
                  aria-label="下一张商品图"
                  @click="showNextImage"
                >
                  <ChevronRight :size="20" />
                </button>
              </template>
            </div>
          </section>

          <aside class="lg:pr-8 xl:pr-14">
            <div v-if="loading" class="mb-6 border border-[#eadfd5] bg-white px-5 py-4 text-sm font-semibold text-[#8a7d70]">
              商品详情加载中...
            </div>
            <div v-if="errorMessage" class="mb-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
              {{ errorMessage }}
            </div>

            <template v-if="!isReady">
              <div class="space-y-6">
                <div class="h-4 w-44 animate-pulse bg-[#eadfd5]"></div>
                <div class="h-12 w-4/5 animate-pulse bg-[#eadfd5]"></div>
                <div class="space-y-3">
                  <div class="h-3 w-full animate-pulse bg-[#eadfd5]"></div>
                  <div class="h-3 w-2/3 animate-pulse bg-[#eadfd5]"></div>
                </div>
                <div class="h-8 w-28 animate-pulse bg-[#eadfd5]"></div>
                <div class="h-px bg-[#e9e3dc]"></div>
                <div class="grid grid-cols-4 gap-3 sm:max-w-sm">
                  <div v-for="size in fallbackSizes" :key="size" class="h-12 animate-pulse bg-[#eadfd5]"></div>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="flex items-center gap-1 text-[#e59a7d]">
                <Star v-for="star in 5" :key="star" :size="17" :fill="star < 5 ? 'currentColor' : 'none'" />
                <span class="ml-2 text-sm font-semibold text-[#9c9387]">4.8 · 126 条评价</span>
              </div>

              <div class="mt-4 border-b border-[#e9e3dc] pb-7">
                <p class="text-xs font-bold uppercase tracking-[0.2em] text-[#b9aa99]">Product code · {{ productCode }}</p>
                <h1 class="mt-3 text-4xl font-semibold tracking-tight text-[#292720] md:text-5xl">{{ productName }}</h1>
                <p class="mt-4 max-w-xl text-sm leading-7 text-[#776f65]">{{ productDescription }}</p>
                <div class="mt-6 flex flex-wrap items-end gap-4">
                  <span class="text-3xl font-bold text-[#d78368]">{{ productPrice }}</span>
                  <span v-if="productOldPrice" class="pb-1 text-base font-semibold text-[#b8afa4] line-through">{{ productOldPrice }}</span>
                  <span
                    class="mb-1 border px-3 py-1 text-xs font-black tracking-[0.12em]"
                    :class="isSoldOut ? 'border-[#ef4444] text-[#ef4444]' : 'border-[#d8d8d8] text-[#6c6258]'"
                  >
                    {{ isSoldOut ? '缺货' : `库存 ${product?.available_stock}` }}
                  </span>
                </div>
              </div>

              <div class="space-y-7 border-b border-[#e9e3dc] py-7">
                <div v-if="isApparelProduct">
                  <div class="mb-3 flex items-center justify-between text-sm">
                    <span class="font-bold text-[#6c6258]">尺码：{{ selectedSize }}</span>
                    <button class="inline-flex items-center gap-1 font-semibold text-[#9f7968] underline underline-offset-4 transition hover:text-[#d78368]" type="button" @click="isSizeGuideOpen = true">
                      <Ruler :size="15" />
                      尺码指南
                    </button>
                  </div>
                  <div class="grid grid-cols-4 gap-3 sm:max-w-sm">
                    <button
                      v-for="size in availableSizes"
                      :key="size"
                      class="h-12 border text-sm font-bold transition"
                      :class="selectedSize === size ? 'border-[#e59a7d] bg-[#eaa07f] text-white' : 'border-[#eadfd5] bg-white text-[#766d64] hover:border-[#e59a7d]'"
                      type="button"
                      @click="selectedSize = size"
                    >
                      {{ size }}
                    </button>
                  </div>
                </div>

                <div v-if="availableColors.length">
                  <p class="mb-3 text-sm font-bold text-[#6c6258]">颜色：{{ selectedColor.name }}</p>
                  <div class="flex flex-wrap gap-3">
                    <button
                      v-for="color in availableColors"
                      :key="color.value"
                      class="min-h-11 border px-5 text-sm font-bold transition"
                      :class="selectedColor.value === color.value ? 'border-[#e59a7d] bg-[#fff4f1] text-[#b45f49]' : 'border-[#eadfd5] bg-white text-[#766d64] hover:border-[#e59a7d]'"
                      :aria-label="color.name"
                      type="button"
                      @click="selectedColor = color"
                    >
                      {{ color.name }}
                    </button>
                  </div>
                </div>

                <div class="flex flex-col gap-4 sm:flex-row">
                  <div class="flex h-14 w-full border border-[#eadfd5] bg-white sm:w-36">
                    <button class="flex w-12 items-center justify-center text-[#6f665d] hover:bg-[#f5efe8]" type="button" aria-label="减少数量" @click="updateQuantity(-1)">
                      <Minus :size="16" />
                    </button>
                    <span class="flex flex-1 items-center justify-center text-sm font-bold">{{ quantity }}</span>
                    <button class="flex w-12 items-center justify-center text-[#6f665d] hover:bg-[#f5efe8]" type="button" aria-label="增加数量" @click="updateQuantity(1)">
                      <Plus :size="16" />
                    </button>
                  </div>
                  <button
                    class="inline-flex h-14 flex-1 items-center justify-center gap-3 px-8 text-sm font-black uppercase tracking-[0.12em] text-white transition"
                    :class="isSoldOut ? 'cursor-not-allowed bg-[#c9bdb3]' : 'bg-[#eaa07f] hover:bg-[#d78368]'"
                    type="button"
                    :disabled="isSoldOut"
                    @click="addToBag"
                  >
                    <ShoppingBag :size="18" />
                    {{ isSoldOut ? '暂时缺货' : '加入购物车' }}
                  </button>
                  <button
                    class="flex h-14 w-full items-center justify-center border border-[#eadfd5] bg-white transition hover:border-[#e59a7d] hover:text-[#d78368] sm:w-14"
                    :class="isFavourite ? 'border-[#e59a7d] text-[#d78368]' : 'text-[#766d64]'"
                    type="button"
                    aria-label="收藏商品"
                    @click="isFavourite = !isFavourite"
                  >
                    <Heart :size="20" :fill="isFavourite ? 'currentColor' : 'none'" />
                  </button>
                </div>

                <p v-if="addedMessage" class="border border-[#cdd8c6] bg-[#f0f6ed] px-4 py-3 text-sm font-semibold text-[#536747]">
                  {{ addedMessage }}
                </p>
              </div>

              <div class="grid grid-cols-1 gap-3 border-b border-[#e9e3dc] py-6 text-sm text-[#756c62] sm:grid-cols-2">
                <div class="flex items-center gap-3">
                  <Truck class="text-[#a6896e]" :size="20" />
                  满 199 元包邮
                </div>
                <div class="flex items-center gap-3">
                  <RotateCcw class="text-[#a6896e]" :size="20" />
                  7 天无忧退换
                </div>
                <div class="flex items-center gap-3">
                  <ShieldCheck class="text-[#a6896e]" :size="20" />
                  官方正品保障
                </div>
                <div class="flex items-center gap-3">
                  <PackageCheck class="text-[#a6896e]" :size="20" />
                  随行收纳袋包装
                </div>
              </div>

              <div class="divide-y divide-[#e9e3dc]">
                <section v-for="section in sections" :key="section.id">
                  <button class="flex w-full items-center justify-between py-5 text-left" type="button" @click="toggleSection(section.id)">
                    <span class="text-sm font-black uppercase tracking-[0.14em] text-[#6d6258]">{{ section.title }}</span>
                    <ChevronDown class="transition" :class="openSections.has(section.id) ? 'rotate-180' : ''" :size="18" />
                  </button>
                  <p v-if="openSections.has(section.id)" class="pb-5 text-sm leading-7 text-[#81786d]">
                    {{ section.body }}
                  </p>
                </section>
              </div>

              <button class="mt-5 inline-flex items-center gap-2 text-sm font-bold text-[#9f7968]" type="button">
                <Share2 :size="17" />
                分享商品
              </button>
            </template>
          </aside>
        </div>
      </section>

      <section v-if="recommendedProducts.length" class="mx-auto max-w-[1500px] px-5 py-16 sm:px-8 lg:px-16">
        <h2 class="mb-8 text-sm font-black uppercase tracking-[0.24em] text-[#8c8175]">你可能也喜欢</h2>
        <div class="grid grid-cols-2 gap-x-5 gap-y-10 md:grid-cols-4 lg:gap-x-8">
          <article v-for="(recommendation, index) in recommendedProducts" :key="`${recommendation.id}-${index}`" class="group">
            <div class="relative aspect-[3/4] overflow-hidden bg-[#ebe6de]">
              <router-link :to="{ name: 'product-detail', params: { id: String(recommendation.id) } }">
                <img v-if="getProductImage(recommendation)" class="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]" :src="getProductImage(recommendation)" :alt="recommendation.name" @error="useFallbackImage($event, recommendation)" />
              </router-link>
              <button class="absolute right-3 top-3 flex h-9 w-9 items-center justify-center bg-white/90 text-[#756b61] transition hover:bg-[#eaa07f] hover:text-white" type="button" aria-label="收藏推荐商品">
                <Heart :size="17" />
              </button>
            </div>
            <router-link class="mt-4 block text-sm font-semibold text-[#5f574e] transition-colors hover:text-[#c9785f]" :to="{ name: 'product-detail', params: { id: String(recommendation.id) } }">
              {{ recommendation.name }}
            </router-link>
            <p class="mt-2 text-sm font-bold text-[#d78368]">{{ getProductDisplayPrice(recommendation) }}</p>
          </article>
        </div>
      </section>

      <section v-if="recentlyViewedProducts.length" class="mx-auto max-w-[1500px] px-5 pb-24 pt-8 sm:px-8 lg:px-16">
        <h2 class="mb-8 text-sm font-black uppercase tracking-[0.24em] text-[#8c8175]">最近浏览</h2>
        <div class="grid max-w-2xl grid-cols-2 gap-5 lg:gap-8">
          <article v-for="recentProduct in recentlyViewedProducts" :key="recentProduct.id" class="group">
            <div class="aspect-[3/4] overflow-hidden bg-[#ebe6de]">
              <router-link :to="{ name: 'product-detail', params: { id: String(recentProduct.id) } }">
                <img class="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]" :src="getViewedProductImage(recentProduct)" :alt="recentProduct.name" @error="useFallbackImage($event, recentProduct)" />
              </router-link>
            </div>
            <router-link class="mt-4 block text-sm font-semibold text-[#5f574e] transition-colors hover:text-[#c9785f]" :to="{ name: 'product-detail', params: { id: String(recentProduct.id) } }">
              {{ recentProduct.name }}
            </router-link>
            <p class="mt-2 text-sm font-bold text-[#d78368]">{{ recentProduct.price }}</p>
          </article>
        </div>
      </section>
    </main>

    <div
      v-if="isSizeGuideOpen"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-[#1f1b17]/45 px-5 py-8 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="size-guide-title"
      @click.self="isSizeGuideOpen = false"
    >
      <section class="w-full max-w-[620px] bg-[#fffdfa] p-6 shadow-[0_24px_80px_rgba(49,39,31,0.24)] sm:p-8">
        <div class="flex items-start justify-between gap-6 border-b border-[#efe5dc] pb-5">
          <div>
            <p class="text-xs font-black uppercase tracking-[0.22em] text-[#b69a86]">Size guide</p>
            <h2 id="size-guide-title" class="mt-2 text-2xl font-semibold text-[#292720]">尺码指南</h2>
            <p class="mt-2 text-sm leading-6 text-[#80766d]">单位为厘米，建议按平时外套尺码选择；喜欢宽松可选大一码。</p>
          </div>
          <button class="flex h-10 w-10 shrink-0 items-center justify-center bg-[#f7efe8] text-[#6f665d] transition hover:bg-[#eaa07f] hover:text-white" type="button" aria-label="关闭尺码指南" @click="isSizeGuideOpen = false">
            <X :size="19" />
          </button>
        </div>

        <div class="mt-6 overflow-x-auto">
          <table class="w-full min-w-[520px] border-collapse text-left text-sm">
            <thead>
              <tr class="bg-[#f7efe8] text-[#6d6258]">
                <th class="px-4 py-3 font-black">尺码</th>
                <th class="px-4 py-3 font-black">胸围</th>
                <th class="px-4 py-3 font-black">衣长</th>
                <th class="px-4 py-3 font-black">肩宽</th>
                <th class="px-4 py-3 font-black">建议身高</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#efe5dc] text-[#655d55]">
              <tr v-for="row in sizeGuideRows" :key="row.size" :class="selectedSize === row.size ? 'bg-[#fff4f1] text-[#c9785f]' : 'bg-white'">
                <td class="px-4 py-4 font-black">{{ row.size }}</td>
                <td class="px-4 py-4">{{ row.chest }}</td>
                <td class="px-4 py-4">{{ row.length }}</td>
                <td class="px-4 py-4">{{ row.shoulder }}</td>
                <td class="px-4 py-4">{{ row.height }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <button class="mt-6 w-full bg-[#eaa07f] px-6 py-3 text-sm font-black uppercase tracking-[0.12em] text-white transition hover:bg-[#d78368]" type="button" @click="isSizeGuideOpen = false">
          我知道了
        </button>
      </section>
    </div>

    <Footer variant="white" />
  </div>
</template>
