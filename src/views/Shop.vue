<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  Heart,
  Mail,
  ShieldCheck,
  ShoppingBag,
  Star,
  Truck,
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { commerceService, getProductImage as resolveProductImage, type Product } from '@/services/commerceService'
import springSelectionImage from '@/assets/images/spring-selection.png'
import lookRecommendationImage from '@/assets/images/look-recommendation.png'
import categoryCityRoamingImage from '@/assets/images/category-city-roaming.png'
import categoryOutdoorGearImage from '@/assets/images/category-outdoor-gear.png'
import categoryTravelWearImage from '@/assets/images/category-travel-wear.png'

const router = useRouter()
const ALL_CATEGORY = '\u5168\u90e8'

type TrendDisplayItem = {
  id: string
  productId?: number
  name: string
  category: string
  price: string
  image: string
}

const shopHeroImage = springSelectionImage
const preloadImageLink = (url: string, highPriority = false) => {
  if (typeof document === 'undefined') return
  if (document.head.querySelector(`link[rel="preload"][href="${url}"]`)) return

  const link = document.createElement('link')
  link.rel = 'preload'
  link.as = 'image'
  link.href = url
  if (highPriority) {
    ;(link as HTMLLinkElement & { fetchPriority?: string }).fetchPriority = 'high'
  }
  document.head.appendChild(link)
}

const preloadImages = (urls: string[]) => {
  if (typeof window === 'undefined') return
  urls.forEach((url) => {
    const image = new Image()
    image.decoding = 'async'
    image.src = url
  })
}

const PRODUCT_CATEGORY_ALL = '\u5168\u90e8'
const HOT_CATEGORIES = [PRODUCT_CATEGORY_ALL, '\u521b\u610f\u5468\u8fb9', '\u88c5\u5907', '\u7537\u88c5', '\u5973\u88c5']


const products = ref<Product[]>([])
const loadingProducts = ref(false)
const selectedCategory = ref(PRODUCT_CATEGORY_ALL)
const currentTrendPage = ref(1)
const TREND_PAGE_SIZE = 4

const getProductImage = (product: Product) => {
  return resolveProductImage(product)
}

const formatProductPrice = (product: Product) => `¥${product.price || ((product.price_cents || 0) / 100).toFixed(2)}`

const categories = computed(() => {
  const dynamicCategories = Array.from(new Set(products.value.map((product) => product.category).filter(Boolean)))
  return [PRODUCT_CATEGORY_ALL, ...dynamicCategories]
})

const trendProducts = computed(() => {
  const adminProducts = products.value
    .filter((product) => product.is_active)
    .map((product): TrendDisplayItem => ({
      id: String(product.id),
      productId: product.id,
      name: product.name,
      category: product.category,
      price: formatProductPrice(product),
      image: getProductImage(product),
    }))

  if (selectedCategory.value === PRODUCT_CATEGORY_ALL) return adminProducts
  return adminProducts.filter((product) => product.category === selectedCategory.value)
})

const trendTotalPages = computed(() => Math.max(1, Math.ceil(trendProducts.value.length / TREND_PAGE_SIZE)))

const pagedTrendProducts = computed(() => {
  const start = (currentTrendPage.value - 1) * TREND_PAGE_SIZE
  return trendProducts.value.slice(start, start + TREND_PAGE_SIZE)
})

const goTrendPage = (direction: -1 | 1) => {
  currentTrendPage.value = Math.min(trendTotalPages.value, Math.max(1, currentTrendPage.value + direction))
}

const goCatalogueCategory = (category: string) => {
  router.push({
    name: 'product-catalogue',
    query: category === PRODUCT_CATEGORY_ALL ? {} : { category },
  })
}

const hideBrokenProductImage = (event: Event) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const loadProducts = async () => {
  loadingProducts.value = true
  try {
    products.value = await commerceService.listProducts()
  } catch {
    products.value = []
  } finally {
    loadingProducts.value = false
  }
}

watch(selectedCategory, () => {
  currentTrendPage.value = 1
})

watch(trendTotalPages, (totalPages) => {
  currentTrendPage.value = Math.min(currentTrendPage.value, totalPages)
})

watch(
  pagedTrendProducts,
  (items) => {
    preloadImages(items.map((item) => item.image).filter(Boolean))
  },
  { immediate: true },
)

const categoryCards = [
  {
    name: '\u57ce\u5e02\u6f2b\u6e38',
    text: '\u9002\u5408\u65e5\u5e38\u901a\u52e4\u4e0e\u77ed\u9014\u65c5\u884c\u7684\u8f7b\u91cf\u5355\u54c1',
    image: categoryCityRoamingImage,
  },
  {
    name: '\u6237\u5916\u88c5\u5907',
    text: '\u56f4\u7ed5\u5c71\u91ce\u8def\u7ebf\u3001\u9732\u8425\u4e0e\u5f92\u6b65\u573a\u666f\u914d\u7f6e',
    image: categoryOutdoorGearImage,
  },
  {
    name: '\u65c5\u884c\u7a7f\u642d',
    text: '\u517c\u987e\u8212\u9002\u3001\u9632\u62a4\u4e0e\u76ee\u7684\u5730\u7167\u7247\u8868\u73b0',
    image: categoryTravelWearImage,
  },
]

const lookItems = [
  { name: '\u9ed1\u5ca9\u675f\u53e3\u5305', price: '\u00a5129' },
  { name: '\u4e09\u7cfb\u65c5\u884c\u676f', price: '\u00a569' },
  { name: '\u8def\u7ebf\u5fbd\u7ae0\u5957\u88c5', price: '\u00a539' },
]

const services = [
  { title: '\u5feb\u901f\u53d1\u8d27', text: '\u6ee1 99 \u5143\u514d\u57fa\u7840\u8fd0\u8d39', icon: Truck },
  { title: '\u5b89\u5168\u652f\u4ed8', text: '\u8ba2\u5355\u4e0e\u652f\u4ed8\u72b6\u6001\u5b9e\u65f6\u540c\u6b65', icon: CreditCard },
  { title: '\u552e\u540e\u4fdd\u969c', text: '\u652f\u6301\u5e93\u5b58\u6821\u9a8c\u4e0e\u8ba2\u5355\u8ffd\u8e2a', icon: ShieldCheck },
]

onMounted(() => {
  preloadImageLink(shopHeroImage, true)
  categoryCards.forEach((card) => preloadImageLink(card.image))
  preloadImages([shopHeroImage, ...categoryCards.map((card) => card.image)])
  void loadProducts()
})
</script>

<template>
  <div class="min-h-screen bg-[#fbfcf8] text-[#26352b] selection:bg-[#fbd784] selection:text-[#0b1d26]">
    <Navigation variant="solid-light" show-cart />

    <main class="pt-[88px]">
      <section class="mx-auto grid max-w-[1500px] grid-cols-1 gap-8 px-6 pb-20 pt-10 lg:grid-cols-[180px_1fr] lg:px-16">
        <aside class="hidden pt-28 lg:block">
          <p class="mb-5 text-xs font-black uppercase tracking-[0.28em] text-[#7d8a80]">SHOP CATEGORIES</p>
          <ul class="space-y-3 text-sm font-semibold text-[#516154]">
            <li v-for="item in categories" :key="item">
              <button type="button" class="transition-colors hover:text-[#b28c4b]" @click="goCatalogueCategory(item)">{{ item }}</button>
            </li>
          </ul>
        </aside>

        <div class="relative min-h-[520px] overflow-hidden bg-[#eef2ea]">
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_80%_70%,rgba(251,215,132,0.28),transparent_34%),linear-gradient(120deg,rgba(255,255,255,0.76),rgba(232,239,229,0.56))]"></div>
          <div class="relative z-10 grid h-full grid-cols-1 items-center gap-8 px-8 py-14 md:grid-cols-[1fr_360px_1fr] md:px-14">
            <div class="space-y-5">
              <p class="text-xs font-black uppercase tracking-[0.32em] text-[#8d7a54]">SPRING OUTDOOR EDIT</p>
              <h1 class="font-serif text-5xl font-semibold leading-none text-[#24342a] md:text-7xl">
                春季<br />
                新品
              </h1>
            </div>

            <div class="relative mx-auto aspect-[4/5] w-full max-w-[340px] overflow-hidden">
              <img
                class="h-full w-full object-cover"
                :src="shopHeroImage"
                alt="Shop hero image"
                decoding="async"
                fetchpriority="high"
              />
              <div class="absolute inset-x-0 bottom-0 bg-[#0b1d26]/80 px-6 py-5 text-white">
                <p class="text-4xl font-light">-30%</p>
                <p class="mt-1 text-sm text-white/72">Seasonal picks</p>
              </div>
            </div>

            <div class="flex flex-col items-start gap-8 md:items-end md:text-right">
              <p class="max-w-[240px] text-sm font-semibold leading-7 text-[#6d796f]">
                春日出行新品上架，精选黑岩束口包、三系旅行杯与路线周边，为轻装旅程补足质感细节。
              </p>
              <button
                class="inline-flex items-center gap-2 border border-[#b28c4b] px-7 py-3 text-sm font-black text-[#7b633a] transition-colors hover:bg-[#b28c4b] hover:text-white"
                type="button"
                @click="router.push('/product-catalogue')"
              >
                <ShoppingBag :size="17" />
                查看全部商品
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-[1280px] px-6 py-16 lg:px-16">
        <div class="mb-10 text-center">
          <p class="text-sm font-black uppercase tracking-[0.28em] text-[#7e8a82]">FEATURED PRODUCTS</p>
          <div class="mt-5 flex flex-wrap justify-center gap-3">
            <button
              v-for="item in categories"
              :key="item"
              class="border px-5 py-2 text-xs font-bold transition-colors hover:border-[#e8a085] hover:text-[#c9785f]"
              :class="selectedCategory === item ? 'border-[#e8a085] bg-[#e8a085] text-white' : 'border-[#d8dfd4] text-[#516154]'"
              type="button"
              @click="selectedCategory = item"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-x-5 gap-y-12 md:grid-cols-4 lg:gap-x-8">
          <article v-for="(product, index) in pagedTrendProducts" :key="product.id" class="group cursor-pointer text-center" @click="goCatalogueCategory(product.category)">
            <div class="relative mx-auto aspect-[3/4] w-full overflow-hidden bg-[#edf1eb]">
              <router-link v-if="product.productId" :to="{ name: 'product-detail', params: { id: String(product.productId) } }">
                <img v-if="product.image" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" :src="product.image" :alt="product.name" decoding="async" loading="lazy" @error="hideBrokenProductImage" />
              </router-link>
              <img v-else-if="product.image" class="h-full w-full object-cover transition duration-500 group-hover:scale-105" :src="product.image" :alt="product.name" decoding="async" loading="lazy" @error="hideBrokenProductImage" />
              <button class="absolute right-4 top-4 flex h-9 w-9 items-center justify-center bg-white/90 text-[#26352b] transition-colors hover:bg-[#fbd784]">
                <Heart :size="16" />
              </button>
            </div>
            <router-link v-if="product.productId" class="mt-5 block text-sm font-black text-[#2f3e34] transition-colors hover:text-[#c9785f]" :to="{ name: 'product-detail', params: { id: String(product.productId) } }">
              {{ product.name }}
            </router-link>
            <h3 v-else class="mt-5 text-sm font-black text-[#2f3e34]">{{ product.name }}</h3>
            <p class="mt-1 text-xs font-semibold text-[#8b958d]">{{ product.category }}</p>
            <p class="mt-2 text-sm font-black text-[#d88a72]">{{ product.price }}</p>
          </article>
        </div>

        <div class="mt-12 flex items-center justify-center gap-5 text-[#a9b2ab]">
          <button
            class="flex h-9 w-9 items-center justify-center transition-colors hover:text-[#26352b] disabled:cursor-not-allowed disabled:opacity-35"
            type="button"
            :disabled="currentTrendPage <= 1"
            aria-label="Previous products"
            @click="goTrendPage(-1)"
          >
            <ChevronLeft :size="18" />
          </button>
          <span class="min-w-[4rem] text-center text-xs font-black tracking-[0.18em] text-[#7e8a82]">
            {{ currentTrendPage }} / {{ trendTotalPages }}
          </span>
          <button
            class="flex h-9 w-9 items-center justify-center transition-colors hover:text-[#26352b] disabled:cursor-not-allowed disabled:opacity-35"
            type="button"
            :disabled="currentTrendPage >= trendTotalPages"
            aria-label="Next products"
            @click="goTrendPage(1)"
          >
            <ChevronRight :size="18" />
          </button>
        </div>
      </section>

      <section class="mx-auto max-w-[1280px] px-6 py-16 lg:px-16">
        <p class="mb-10 text-center text-sm font-black uppercase tracking-[0.28em] text-[#7e8a82]">SHOP CATEGORIES</p>
        <div class="grid grid-cols-1 gap-7 md:grid-cols-3">
          <article v-for="card in categoryCards" :key="card.name" class="group">
            <div class="aspect-[1.05/1] overflow-hidden bg-[#edf1eb]">
              <img class="h-full w-full object-cover transition duration-500 group-hover:scale-105" :src="card.image" :alt="card.name" width="760" height="724" decoding="async" loading="lazy" />
            </div>
            <h3 class="mt-5 text-center text-sm font-black text-[#2f3e34]">{{ card.name }}</h3>
            <p class="mt-2 text-center text-xs font-semibold text-[#8b958d]">{{ card.text }}</p>
          </article>
        </div>
      </section>

      <section class="mx-auto max-w-[1280px] px-6 py-14 lg:px-16">
        <p class="mb-10 text-center text-sm font-black uppercase tracking-[0.28em] text-[#7e8a82]">Only trusted picks</p>
        <div class="grid grid-cols-2 gap-7 text-center text-xs font-black uppercase tracking-[0.2em] text-[#314137] md:grid-cols-6">
          <span>Trail</span>
          <span>Map Lab</span>
          <span>CTNS</span>
          <span>Summit</span>
          <span>Nomad</span>
          <span>Guide Picks</span>
        </div>
      </section>

      <section class="relative mt-12 min-h-[440px] overflow-hidden bg-[#201f1b]">
        <img
          class="absolute inset-0 h-full w-full object-cover opacity-[0.42]"
          src="https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?q=80&w=1800&auto=format&fit=crop"
          alt="Outdoor campaign"
        />
        <div class="absolute inset-0 bg-gradient-to-r from-[#0b1d26] via-[#1b2522]/82 to-[#3a261d]/74"></div>
        <div class="relative z-10 mx-auto flex min-h-[440px] max-w-[1280px] items-center justify-between px-6 lg:px-16">
          <ChevronLeft class="hidden text-white/45 md:block" :size="24" />
          <div class="text-center">
            <p class="text-sm font-bold uppercase tracking-[0.38em] text-[#fbd784]">2026 OUTDOOR EDIT</p>
            <h2 class="mt-5 font-serif text-5xl font-semibold uppercase tracking-[0.14em] text-white md:text-7xl">山野出行精选</h2>
            <button class="mt-10 inline-flex items-center gap-2 bg-white px-8 py-3 text-xs font-black uppercase tracking-[0.18em] text-[#26352b] transition-colors hover:bg-[#fbd784]">
              立即选购
              <ArrowRight :size="15" />
            </button>
          </div>
          <ChevronRight class="hidden text-white/45 md:block" :size="24" />
        </div>
      </section>

      <section class="border-b border-[#edf0f3] bg-white">
        <div class="mx-auto grid max-w-[1180px] grid-cols-1 divide-y divide-[#edf0f3] px-6 py-12 md:grid-cols-3 md:divide-x md:divide-y-0">
          <div v-for="service in services" :key="service.title" class="flex flex-col items-center px-8 py-6 text-center">
            <component :is="service.icon" class="mb-4 text-[#b28c4b]" :size="24" />
            <h3 class="text-sm font-black text-[#2f3e34]">{{ service.title }}</h3>
            <p class="mt-2 text-xs font-semibold leading-6 text-[#8b958d]">{{ service.text }}</p>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-[1120px] px-6 py-24 lg:px-16">
        <p class="mb-12 text-center text-sm font-black uppercase tracking-[0.28em] text-[#7e8a82]">LOOK RECOMMENDATIONS</p>
        <div class="grid grid-cols-1 items-center gap-12 md:grid-cols-[1.1fr_0.9fr]">
          <div class="aspect-[4/3] overflow-hidden bg-[#edf1eb]">
            <img
              class="h-full w-full object-cover"
              :src="lookRecommendationImage"
              alt="Look recommendation"
            />
          </div>
          <div>
            <p class="text-xs font-black uppercase tracking-[0.22em] text-[#7e8a82]">CURATED LOOK</p>
            <div class="mt-6 divide-y divide-[#edf0f3]">
              <div v-for="item in lookItems" :key="item.name" class="flex items-center justify-between py-5">
                <div>
                  <h3 class="text-sm font-black text-[#2f3e34]">{{ item.name }}</h3>
                  <p class="mt-1 text-xs font-semibold text-[#8b958d]">Curated travel goods</p>
                </div>
                <span class="text-sm font-black text-[#2f3e34]">{{ item.price }}</span>
              </div>
            </div>
            <button
              class="mt-8 inline-flex items-center gap-2 border border-[#e8a085] px-8 py-3 text-xs font-black uppercase tracking-[0.16em] text-[#c9785f] transition-colors hover:bg-[#e8a085] hover:text-white"
              type="button"
              @click="router.push('/product-catalogue')"
            >
              <ShoppingBag :size="15" />
              查看搭配商品
            </button>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-[1280px] px-6 pb-24 lg:px-16">
        <div class="grid min-h-[280px] grid-cols-1 overflow-hidden bg-[#efe3d2] md:grid-cols-2">
          <div class="flex flex-col justify-center px-8 py-12 md:px-16">
            <div class="mb-5 flex items-center gap-2 text-[#b28c4b]">
              <Star :size="18" />
              <Star :size="18" />
              <Star :size="18" />
            </div>
            <h2 class="font-serif text-3xl font-semibold text-[#26352b]">Join the travel list</h2>
            <p class="mt-3 max-w-md text-sm font-semibold leading-7 text-[#6d796f]">
              订阅后获取新品上架、库存补货和旅行装备推荐提醒。
            </p>
            <form class="mt-7 flex max-w-md bg-white">
              <label class="sr-only" for="shop-email">Email address</label>
              <input id="shop-email" class="min-w-0 flex-1 px-5 py-3 text-sm outline-none" type="email" placeholder="Email address" />
              <button class="inline-flex items-center gap-2 bg-[#e8a085] px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-[#d47d64]">
                <Mail :size="16" />
                订阅
              </button>
            </form>
          </div>
          <img
            class="h-full min-h-[280px] w-full object-cover"
            src="https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=1200&auto=format&fit=crop"
            alt="Newsletter visual"
          />
        </div>
      </section>
    </main>

    <Footer variant="white" />
  </div>
</template>
