<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronDown, ChevronUp, Heart, Home, SlidersHorizontal } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { commerceService, getProductImage as resolveProductImage, type Product } from '@/services/commerceService'

type SortMode = 'recommended' | 'latest' | 'price-asc' | 'price-desc'

const route = useRoute()

const products = ref<Product[]>([])
const loading = ref(false)
const errorMessage = ref('')
const isCategorySectionOpen = ref(false)
const isProductTypeSectionOpen = ref(false)
const isPriceSectionOpen = ref(false)
const isSizeSectionOpen = ref(false)
const isColorSectionOpen = ref(false)
const selectedCategory = ref('全部')
const selectedProductType = ref('全部')
const selectedSize = ref('全部')
const selectedColor = ref('全部')
const selectedSort = ref<SortMode>('recommended')
const pageSize = ref(9)
const currentPage = ref(1)
const onlyInStock = ref(false)
const selectedMinPrice = ref(0)
const selectedMaxPrice = ref(9999)
const favourites = ref(new Set<number>())

const PRICE_FILTER_MIN = 0
const PRICE_FILTER_MAX = 9999
const pageSizeOptions = [9, 12, 18]
const getProductImage = (product: Product) => resolveProductImage(product)

const useFallbackProductImage = (event: Event, product: Product) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const getProductPrice = (product: Product) => Number(product.price || ((product.price_cents || 0) / 100).toFixed(2))
const getOldPrice = (product: Product) => {
  const cents = Number(product.metadata?.old_price_cents || 0)
  return cents > 0 ? (cents / 100).toFixed(2) : ''
}
const getMetaList = (product: Product, field: 'sizes' | 'colors') => {
  const values = product.metadata?.[field]
  return Array.isArray(values) ? values.map((item) => String(item)).filter(Boolean) : []
}
const productRequiresSize = (product: Product) => product.metadata?.requires_size !== false && getMetaList(product, 'sizes').length > 0
const productRequiresColor = (product: Product) => product.metadata?.requires_color === true && getMetaList(product, 'colors').length > 0
const formatPrice = (value: number) => `¥${value.toFixed(2)}`

const categoryOrder = ['男装', '女装', '装备', '创意周边']

const categories = computed(() => {
  const dynamicCategories = Array.from(new Set(products.value.map((item) => item.category).filter(Boolean)))
  const orderedCategories = [
    ...categoryOrder.filter((category) => dynamicCategories.includes(category)),
    ...dynamicCategories.filter((category) => !categoryOrder.includes(category)),
  ]
  return ['全部', ...orderedCategories.slice(0, 4)]
})

const categoryCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const product of products.value) {
    if (!product.category) continue
    counts.set(product.category, (counts.get(product.category) || 0) + 1)
  }
  return counts
})

const categoryFilteredProducts = computed(() => {
  if (selectedCategory.value === '全部') return products.value
  return products.value.filter((product) => product.category === selectedCategory.value)
})

const productTypeOrder = ['T恤', '卫衣', '背心', '正装衬衫', '连衣裙', '针织衫', '半身裙', '衬衫', '背包', '水壶', '帐篷', '登山杖', '徽章', '贴纸', '帆布袋', '明信片']

const getProductType = (product: Product) => String(product.metadata?.type || product.metadata?.product_type || '').trim()

const productTypes = computed(() => {
  const dynamicTypes = Array.from(new Set(categoryFilteredProducts.value.map((item) => getProductType(item)).filter(Boolean)))
  const orderedTypes = [
    ...productTypeOrder.filter((type) => dynamicTypes.includes(type)),
    ...dynamicTypes.filter((type) => !productTypeOrder.includes(type)),
  ]
  return ['全部', ...orderedTypes]
})

const productTypeCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const product of categoryFilteredProducts.value) {
    const type = getProductType(product)
    if (!type) continue
    counts.set(type, (counts.get(type) || 0) + 1)
  }
  return counts
})
const sizeOrder = ['S', 'M', 'L', 'XL', 'XXL']

const sizes = computed(() => {
  const dynamicSizes = Array.from(new Set(products.value.filter(productRequiresSize).flatMap((item) => getMetaList(item, 'sizes'))))
  const orderedSizes = [
    ...sizeOrder.filter((size) => dynamicSizes.includes(size)),
    ...dynamicSizes.filter((size) => !sizeOrder.includes(size)),
  ]
  return orderedSizes.length ? orderedSizes : sizeOrder
})
const colorFallbacks: string[] = []

const colors = computed(() => {
  const dynamicColors = Array.from(new Set(products.value.filter(productRequiresColor).flatMap((item) => getMetaList(item, 'colors'))))
  return dynamicColors.length ? dynamicColors : colorFallbacks
})

const priceBounds = computed(() => {
  return {
    min: PRICE_FILTER_MIN,
    max: PRICE_FILTER_MAX,
  }
})

const normalizedMinPrice = computed(() => Math.min(selectedMinPrice.value, selectedMaxPrice.value))
const normalizedMaxPrice = computed(() => Math.max(selectedMinPrice.value, selectedMaxPrice.value))
const priceRangeSpan = computed(() => Math.max(1, priceBounds.value.max - priceBounds.value.min))
const minThumbPercent = computed(() => ((normalizedMinPrice.value - priceBounds.value.min) / priceRangeSpan.value) * 100)
const maxThumbPercent = computed(() => ((normalizedMaxPrice.value - priceBounds.value.min) / priceRangeSpan.value) * 100)

const filteredProducts = computed(() => {
  const minPrice = Math.min(selectedMinPrice.value, selectedMaxPrice.value)
  const maxPrice = Math.max(selectedMinPrice.value, selectedMaxPrice.value)

  const next = products.value.filter((product) => {
    const price = getProductPrice(product)
    const matchesCategory = selectedCategory.value === '全部' || product.category === selectedCategory.value
    const matchesProductType = selectedProductType.value === '全部' || getProductType(product) === selectedProductType.value
    const matchesSize = selectedSize.value === '全部' || (productRequiresSize(product) && getMetaList(product, 'sizes').includes(selectedSize.value))
    const productColors = getMetaList(product, 'colors')
    const matchesColor = selectedColor.value === '全部' || (productRequiresColor(product) && productColors.includes(selectedColor.value))
    const matchesStock = !onlyInStock.value || product.available_stock > 0
    const matchesPrice = price >= minPrice && price <= maxPrice
    return matchesCategory && matchesProductType && matchesSize && matchesColor && matchesStock && matchesPrice
  })

  if (selectedSort.value === 'price-asc') next.sort((a, b) => getProductPrice(a) - getProductPrice(b))
  if (selectedSort.value === 'price-desc') next.sort((a, b) => getProductPrice(b) - getProductPrice(a))
  if (selectedSort.value === 'latest') next.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  return next
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredProducts.value.length / pageSize.value)))
const pagedProducts = computed(() => filteredProducts.value.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value))
const currentTitle = computed(() => (selectedCategory.value === '全部' ? '全部商品' : selectedCategory.value))

const applyCategoryFromRoute = () => {
  const routeCategory = String(route.query.category || '').trim()
  if (!routeCategory) {
    selectedCategory.value = '全部'
    return
  }
  selectedCategory.value = categories.value.includes(routeCategory) ? routeCategory : '全部'
}

const loadProducts = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    products.value = await commerceService.listProducts()
    applyCategoryFromRoute()
    void import('@/views/ProductDetail.vue')
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '商品目录加载失败，请稍后再试。')
  } finally {
    loading.value = false
  }
}

const toggleFavourite = (id: number) => {
  const next = new Set(favourites.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  favourites.value = next
}

const resetFilters = () => {
  selectedCategory.value = '全部'
  selectedProductType.value = '全部'
  selectedSize.value = '全部'
  selectedColor.value = '全部'
  selectedSort.value = 'recommended'
  onlyInStock.value = false
  selectedMinPrice.value = PRICE_FILTER_MIN
  selectedMaxPrice.value = PRICE_FILTER_MAX
}

const clampPriceValues = () => {
  const minBound = priceBounds.value.min
  const maxBound = priceBounds.value.max
  selectedMinPrice.value = Math.min(maxBound, Math.max(minBound, Number(selectedMinPrice.value || 0)))
  selectedMaxPrice.value = Math.min(maxBound, Math.max(minBound, Number(selectedMaxPrice.value || 0)))
}

watch([selectedCategory, selectedProductType, selectedSize, selectedColor, selectedSort, pageSize, onlyInStock, selectedMinPrice, selectedMaxPrice], () => {
  currentPage.value = 1
})

watch(totalPages, (value) => {
  if (currentPage.value > value) currentPage.value = value
})

watch(priceBounds, clampPriceValues)
watch([selectedMinPrice, selectedMaxPrice], clampPriceValues)

watch(
  () => route.query.category,
  () => {
    applyCategoryFromRoute()
  },
)

watch([selectedCategory, productTypes], () => {
  if (selectedProductType.value !== '全部' && !productTypes.value.includes(selectedProductType.value)) {
    selectedProductType.value = '全部'
  }
})

onMounted(loadProducts)
</script>

<template>
  <div class="min-h-screen bg-white text-[#151515]">
    <Navigation variant="solid-light" show-cart />

    <main class="pt-[92px]">
      <div class="mx-auto max-w-[1500px] px-6 pb-20 pt-9 lg:px-20">
        <div class="mb-10 flex flex-col gap-5 text-sm font-semibold text-[#bdbdbd] md:flex-row md:items-center md:justify-between">
          <div class="flex flex-wrap items-center gap-4">
            <Home :size="17" />
            <span class="h-5 w-px bg-[#d6d6d6]"></span>
            <router-link to="/shop" class="transition-colors hover:text-[#ffad2b]">商城首页</router-link>
            <span>/</span>
            <span class="text-[#151515]">商品目录</span>
          </div>

          <div class="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.16em] text-[#7e7e7e]">
            <SlidersHorizontal :size="15" />
            真实商品数据
          </div>
        </div>

        <div v-if="errorMessage" class="mb-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
          {{ errorMessage }}
        </div>

        <div class="grid gap-9 xl:grid-cols-[310px_minmax(0,1fr)]">
          <aside class="space-y-4">
            <section class="border border-[#ececec] bg-white px-7 pt-7" :class="isCategorySectionOpen ? 'pb-7' : 'pb-5'">
              <button type="button" class="flex w-full items-center justify-between" :class="isCategorySectionOpen ? 'mb-6' : ''" @click="isCategorySectionOpen = !isCategorySectionOpen">
                <h2 class="text-sm font-black uppercase tracking-[0.16em] text-[#161616]">商品分类</h2>
                <ChevronUp :size="18" class="text-[#161616] transition-transform" :class="isCategorySectionOpen ? '' : 'rotate-180'" />
              </button>
              <div v-if="isCategorySectionOpen" class="space-y-4">
                <button
                  v-for="category in categories"
                  :key="category"
                  type="button"
                  class="flex w-full items-center gap-4 text-left text-sm transition-colors"
                  :class="selectedCategory === category ? 'font-black text-[#161616]' : 'font-medium text-[#444] hover:text-[#161616]'"
                  @click="selectedCategory = category"
                >
                  <span
                    class="flex h-7 w-7 shrink-0 items-center justify-center border"
                    :class="selectedCategory === category ? 'border-black bg-black text-white' : 'border-[#d7d7d7] bg-white text-transparent'"
                  >
                    ✓
                  </span>
                  <span class="inline-flex items-center gap-1.5">
                    <span>{{ category }}</span>
                    <span
                      class="text-[13px] font-medium text-[#c8c8c8]"
                    >
                      ({{ category === '全部' ? products.length : categoryCounts.get(category) || 0 }})
                    </span>
                  </span>
                </button>
              </div>
            </section>

            <section class="border border-[#ececec] bg-white px-7 pt-7" :class="isProductTypeSectionOpen ? 'pb-7' : 'pb-5'">
              <button type="button" class="flex w-full items-center justify-between" :class="isProductTypeSectionOpen ? 'mb-6' : ''" @click="isProductTypeSectionOpen = !isProductTypeSectionOpen">
                <h2 class="text-sm font-black uppercase tracking-[0.16em] text-[#161616]">商品类型分类</h2>
                <ChevronUp :size="18" class="text-[#161616] transition-transform" :class="isProductTypeSectionOpen ? '' : 'rotate-180'" />
              </button>
              <div v-if="isProductTypeSectionOpen" class="space-y-4">
                <button
                  v-for="productType in productTypes"
                  :key="productType"
                  type="button"
                  class="flex w-full items-center gap-4 text-left text-sm transition-colors"
                  :class="selectedProductType === productType ? 'font-black text-[#161616]' : 'font-medium text-[#444] hover:text-[#161616]'"
                  @click="selectedProductType = productType"
                >
                  <span
                    class="flex h-7 w-7 shrink-0 items-center justify-center border"
                    :class="selectedProductType === productType ? 'border-black bg-black text-white' : 'border-[#d7d7d7] bg-white text-transparent'"
                  >
                    ✓
                  </span>
                  <span class="inline-flex items-center gap-1.5">
                    <span>{{ productType }}</span>
                    <span
                      class="text-[13px] font-medium text-[#c8c8c8]"
                    >
                      ({{ productType === '全部' ? categoryFilteredProducts.length : productTypeCounts.get(productType) || 0 }})
                    </span>
                  </span>
                </button>
              </div>
            </section>

            <section class="border border-[#ececec] bg-white px-7 pt-7" :class="isPriceSectionOpen ? 'pb-7' : 'pb-5'">
              <button type="button" class="flex w-full items-center justify-between" :class="isPriceSectionOpen ? 'mb-5' : ''" @click="isPriceSectionOpen = !isPriceSectionOpen">
                <h2 class="text-sm font-black uppercase tracking-[0.16em] text-[#161616]">价格</h2>
                <ChevronUp :size="18" class="text-[#161616] transition-transform" :class="isPriceSectionOpen ? '' : 'rotate-180'" />
              </button>
              <div v-if="isPriceSectionOpen">
                <div class="grid grid-cols-2 gap-3 text-xs font-semibold text-[#555]">
                  <label class="border border-[#ededed] bg-[#fafafa] px-3 py-2">
                    <span class="block text-[11px] text-[#a8a8a8]">最低价</span>
                    <input v-model.number="selectedMinPrice" class="mt-1 w-full bg-transparent outline-none" :min="priceBounds.min" :max="priceBounds.max" type="number" />
                  </label>
                  <label class="border border-[#ededed] bg-[#fafafa] px-3 py-2">
                    <span class="block text-[11px] text-[#a8a8a8]">最高价</span>
                    <input v-model.number="selectedMaxPrice" class="mt-1 w-full bg-transparent outline-none" :min="priceBounds.min" :max="priceBounds.max" type="number" />
                  </label>
                </div>
                <div class="price-slider mt-5">
                  <div class="price-slider__track"></div>
                  <div
                    class="price-slider__active"
                    :style="{
                      '--range-start': `${minThumbPercent}`,
                      '--range-width': `${Math.max(0, maxThumbPercent - minThumbPercent)}`,
                    }"
                  ></div>
                  <input v-model.number="selectedMinPrice" class="price-slider__range" :min="priceBounds.min" :max="priceBounds.max" type="range" />
                  <input v-model.number="selectedMaxPrice" class="price-slider__range" :min="priceBounds.min" :max="priceBounds.max" type="range" />
                </div>
              </div>
            </section>

            <section class="border border-[#ececec] bg-white px-7 pt-7" :class="isSizeSectionOpen ? 'pb-7' : 'pb-5'">
              <button type="button" class="flex w-full items-center justify-between" :class="isSizeSectionOpen ? 'mb-5' : ''" @click="isSizeSectionOpen = !isSizeSectionOpen">
                <h2 class="text-sm font-black uppercase tracking-[0.16em] text-[#161616]">尺码</h2>
                <ChevronUp :size="18" class="text-[#161616] transition-transform" :class="isSizeSectionOpen ? '' : 'rotate-180'" />
              </button>
              <div v-if="isSizeSectionOpen">
                <div class="size-grid">
                  <button
                    v-for="size in sizes"
                    :key="size"
                    type="button"
                    class="size-option"
                    :class="selectedSize === size ? 'bg-black text-white' : 'bg-white text-[#555] hover:bg-[#fafafa]'"
                    @click="selectedSize = size"
                  >
                    {{ size }}
                  </button>
                </div>
                <button
                  type="button"
                  class="mt-4 text-xs font-bold text-[#777] transition-colors hover:text-black"
                  @click="selectedSize = '全部'"
                >
                  清除尺码筛选
                </button>
              </div>
            </section>

            <section v-if="colors.length" class="border border-[#ececec] bg-white px-7 pt-7" :class="isColorSectionOpen ? 'pb-7' : 'pb-5'">
              <button type="button" class="flex w-full items-center justify-between" :class="isColorSectionOpen ? 'mb-5' : ''" @click="isColorSectionOpen = !isColorSectionOpen">
                <h2 class="text-sm font-black uppercase tracking-[0.16em] text-[#161616]">颜色</h2>
                <ChevronUp :size="18" class="text-[#161616] transition-transform" :class="isColorSectionOpen ? '' : 'rotate-180'" />
              </button>
              <div v-if="isColorSectionOpen">
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="color in colors"
                    :key="color"
                    type="button"
                    class="min-h-[34px] border px-3 text-xs font-bold transition"
                    :class="selectedColor === color ? 'border-black ring-1 ring-black ring-offset-2 ring-offset-white' : 'border-[#d7d7d7]'"
                    @click="selectedColor = color"
                  >{{ color }}</button>
                </div>
                <button
                  type="button"
                  class="mt-4 text-xs font-bold text-[#777] transition-colors hover:text-black"
                  @click="selectedColor = '全部'"
                >
                  清除颜色筛选
                </button>
              </div>
            </section>

            <button type="button" class="w-full border border-[#151515] px-5 py-3 text-sm font-black text-[#151515] transition-colors hover:bg-black hover:text-white" @click="resetFilters">
              重置筛选
            </button>
          </aside>

          <section>
            <div class="mb-8 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p class="text-xs font-black uppercase tracking-[0.22em] text-[#b6b6b6]">商品目录</p>
                <h1 class="mt-3 text-4xl font-light tracking-tight text-[#151515] md:text-[2.7rem]">
                  {{ currentTitle }}
                  <span class="text-[#d3d3d3]">({{ filteredProducts.length }})</span>
                </h1>
              </div>

              <div class="flex flex-wrap items-center gap-4">
                <label class="flex items-center gap-3 text-sm font-bold text-[#161616]">
                  <span>显示数量</span>
                  <span class="catalogue-select">
                    <select v-model="pageSize">
                    <option v-for="option in pageSizeOptions" :key="option" :value="option">{{ option }}</option>
                    </select>
                    <ChevronDown class="catalogue-select__icon" :size="16" />
                  </span>
                </label>

                <label class="flex items-center gap-3 text-sm font-bold text-[#161616]">
                  <span>排序</span>
                  <span class="catalogue-select catalogue-select--wide">
                    <select v-model="selectedSort">
                    <option value="recommended">推荐</option>
                    <option value="latest">最新上架</option>
                    <option value="price-asc">价格从低到高</option>
                    <option value="price-desc">价格从高到低</option>
                    </select>
                    <ChevronDown class="catalogue-select__icon" :size="16" />
                  </span>
                </label>
              </div>
            </div>

            <div v-if="loading" class="py-20 text-center text-sm text-[#7c7469]">商品目录加载中...</div>

            <div v-else-if="pagedProducts.length" class="grid grid-cols-1 gap-x-10 gap-y-14 sm:grid-cols-2 xl:grid-cols-3">
              <article v-for="product in pagedProducts" :key="product.id" class="group">
                <div class="relative aspect-square overflow-hidden bg-[#f2f2f2]">
                  <router-link class="block h-full w-full" :to="{ name: 'product-detail', params: { id: String(product.id) } }">
                    <img v-if="getProductImage(product)" class="h-full w-full object-cover object-top transition duration-500 group-hover:scale-[1.04]" :src="getProductImage(product)" :alt="product.name" loading="lazy" decoding="async" @error="useFallbackProductImage($event, product)" />
                  </router-link>
                  <button
                    class="absolute right-4 top-4 flex h-12 w-12 items-center justify-center rounded-full transition-colors"
                    :class="favourites.has(product.id) ? 'bg-[#ffad2b] text-white' : 'bg-white/95 text-black hover:bg-[#ffad2b] hover:text-white'"
                    type="button"
                    @click="toggleFavourite(product.id)"
                  >
                    <Heart :size="18" :stroke-width="2.1" />
                  </button>
                </div>

                <div class="mt-5 grid min-h-[72px] grid-cols-[minmax(0,1fr)_auto] grid-rows-2 items-start gap-x-4 gap-y-2">
                  <div class="min-w-0">
                    <router-link class="block text-lg font-medium text-[#222] transition-colors hover:text-[#c9785f]" :to="{ name: 'product-detail', params: { id: String(product.id) } }">
                      {{ product.name }}
                    </router-link>
                  </div>
                  <div class="flex items-end justify-end gap-3 text-right">
                    <span class="text-[1.1rem] font-semibold text-[#d78368]">{{ formatPrice(getProductPrice(product)) }}</span>
                    <span v-if="getOldPrice(product)" class="text-sm font-medium text-[#bababa] line-through">¥{{ getOldPrice(product) }}</span>
                  </div>
                  <p class="text-sm font-medium text-[#8a8a8a]">{{ product.category || product.sku }}</p>
                  <p class="text-right text-xs font-bold" :class="product.available_stock > 0 ? 'text-[#4d7c0f]' : 'text-[#b91c1c]'">
                    {{ product.available_stock > 0 ? `有库存 · 剩余 ${product.available_stock}` : '暂时缺货' }}
                  </p>
                </div>
              </article>
            </div>

            <div v-else class="border border-dashed border-[#d9d9d9] bg-white px-8 py-16 text-center">
              <p class="text-lg font-black text-[#151515]">暂时没有符合条件的商品</p>
              <p class="mt-3 text-sm font-medium text-[#8a8a8a]">可以换个筛选条件，或者先清空左侧条件重新看看。</p>
            </div>

            <div v-if="!loading && filteredProducts.length > pageSize" class="mt-16 flex flex-wrap items-center justify-between gap-3 text-sm font-semibold text-[#555]">
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <div class="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  class="border border-[#d7d7d7] px-4 py-2 transition-colors hover:border-black hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="currentPage === 1"
                  @click="currentPage -= 1"
                >
                  上一页
                </button>
                <button
                  type="button"
                  class="border border-[#d7d7d7] px-4 py-2 transition-colors hover:border-black hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="currentPage === totalPages"
                  @click="currentPage += 1"
                >
                  下一页
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>

    <Footer variant="white" />
  </div>
</template>

<style scoped>
.price-slider {
  position: relative;
  height: 26px;
}

.catalogue-select {
  position: relative;
  display: inline-flex;
  min-width: 106px;
  height: 44px;
  align-items: center;
  border: 1px solid #e3e0db;
  background: #ffffff;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.catalogue-select--wide {
  min-width: 148px;
}

.catalogue-select:focus-within,
.catalogue-select:hover {
  border-color: #151515;
  box-shadow: 0 8px 22px rgba(21, 21, 21, 0.06);
}

.catalogue-select select {
  width: 100%;
  height: 100%;
  appearance: none;
  border: 0;
  background: transparent;
  padding: 0 2.75rem 0 1rem;
  color: #151515;
  font-size: 0.875rem;
  font-weight: 800;
  outline: none;
}

.catalogue-select__icon {
  position: absolute;
  right: 0.95rem;
  color: #151515;
  pointer-events: none;
}

.price-slider__track,
.price-slider__active {
  position: absolute;
  top: 50%;
  height: 4px;
  transform: translateY(-50%);
  border-radius: 999px;
}

.price-slider__track {
  left: 9px;
  right: 9px;
  background: #cfcfcf;
}

.price-slider__active {
  left: calc(9px + (100% - 18px) * var(--range-start, 0) / 100);
  width: calc((100% - 18px) * var(--range-width, 0) / 100);
  background: #111111;
}

.price-slider__range {
  position: absolute;
  inset: 0;
  width: 100%;
  margin: 0;
  appearance: none;
  background: transparent;
  pointer-events: none;
}

.price-slider__range::-webkit-slider-runnable-track {
  height: 4px;
  background: transparent;
}

.price-slider__range::-moz-range-track {
  height: 4px;
  background: transparent;
}

.price-slider__range::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  margin-top: -7px;
  border: 2px solid #111111;
  border-radius: 999px;
  background: #ffffff;
  pointer-events: auto;
  cursor: pointer;
  box-shadow: 0 0 0 2px #ffffff;
}

.price-slider__range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border: 2px solid #111111;
  border-radius: 999px;
  background: #ffffff;
  pointer-events: auto;
  cursor: pointer;
  box-shadow: 0 0 0 2px #ffffff;
}

.size-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  gap: 1px;
  border: 1px solid #d7d7d7;
  background: #d7d7d7;
}

.size-option {
  display: flex;
  min-width: 0;
  height: 52px;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  transition: background-color 0.2s ease, color 0.2s ease;
}

@media (max-width: 1280px) {
  .size-grid {
    grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  }

  .size-option {
    height: 48px;
  }
}
</style>
