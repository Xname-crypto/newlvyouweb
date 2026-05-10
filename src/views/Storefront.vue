<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Package, ShieldCheck, ShoppingBag, Truck } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { commerceService, getProductImage, type Product } from '@/services/commerceService'

const router = useRouter()
const products = ref<Product[]>([])
const loading = ref(false)
const errorMessage = ref('')
const selectedCategory = ref('All')

const categories = computed(() => ['All', ...Array.from(new Set(products.value.map((item) => item.category).filter(Boolean)))])
const visibleProducts = computed(() => {
  if (selectedCategory.value === 'All') return products.value
  return products.value.filter((item) => item.category === selectedCategory.value)
})
const heroProduct = computed(() => visibleProducts.value[0] || products.value[0] || null)

const loadProducts = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    products.value = await commerceService.listProducts()
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || 'Failed to load storefront products.')
  } finally {
    loading.value = false
  }
}

const openProduct = (productId: number) => {
  router.push({ name: 'product-detail', params: { id: String(productId) } })
}

onMounted(loadProducts)
</script>

<template>
  <div class="min-h-screen bg-[#f8faf7] text-[#1f2f25]">
    <Navigation variant="solid-light" show-cart />

    <main class="pt-[92px]">
      <section class="mx-auto grid max-w-[1320px] gap-10 px-6 pb-12 pt-12 lg:grid-cols-[0.9fr_1.1fr] lg:px-12">
        <div class="flex flex-col justify-center">
          <p class="text-xs font-black uppercase tracking-[0.32em] text-[#b28c4b]">Storefront</p>
          <h1 class="mt-5 max-w-2xl text-5xl font-semibold leading-tight tracking-tight md:text-7xl">
            Shop real products with the new checkout flow
          </h1>
          <p class="mt-6 max-w-xl text-base leading-8 text-[#647266]">
            This page now follows the same path as the rest of the shop: open a real backend product, choose its options, add it to cart,
            then finish checkout through one grouped order.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <button
              v-for="category in categories"
              :key="category"
              class="border px-5 py-2 text-sm font-bold transition-colors"
              :class="selectedCategory === category ? 'border-[#1f2f25] bg-[#1f2f25] text-white' : 'border-[#d7dfd2] bg-white text-[#526052] hover:border-[#b28c4b]'"
              type="button"
              @click="selectedCategory = category"
            >
              {{ category }}
            </button>
          </div>
          <div class="mt-8 flex flex-wrap gap-4">
            <router-link
              to="/product-catalogue"
              class="inline-flex items-center gap-2 bg-[#1f2f25] px-6 py-3 text-sm font-black text-white transition-colors hover:bg-[#b28c4b]"
            >
              Browse catalogue
              <ArrowRight :size="16" />
            </router-link>
            <router-link
              to="/cart"
              class="inline-flex items-center gap-2 border border-[#d7dfd2] bg-white px-6 py-3 text-sm font-black text-[#1f2f25] transition-colors hover:border-[#b28c4b]"
            >
              <ShoppingBag :size="16" />
              Open cart
            </router-link>
          </div>
        </div>

        <div class="min-h-[360px] overflow-hidden bg-[#e9eee5]">
          <img
            v-if="heroProduct && getProductImage(heroProduct)"
            class="h-full w-full object-cover"
            :src="getProductImage(heroProduct)"
            :alt="heroProduct?.name || 'Storefront hero'"
          />
        </div>
      </section>

      <section class="border-y border-[#e3e9df] bg-white">
        <div class="mx-auto grid max-w-[1180px] grid-cols-1 divide-y divide-[#edf0f3] px-6 py-8 md:grid-cols-3 md:divide-x md:divide-y-0">
          <div class="flex items-center gap-4 px-6 py-4">
            <ShieldCheck class="text-[#b28c4b]" :size="24" />
            <span class="text-sm font-bold">Live inventory is checked before checkout starts.</span>
          </div>
          <div class="flex items-center gap-4 px-6 py-4">
            <Package class="text-[#b28c4b]" :size="24" />
            <span class="text-sm font-bold">Multiple items are grouped into one checkout order.</span>
          </div>
          <div class="flex items-center gap-4 px-6 py-4">
            <Truck class="text-[#b28c4b]" :size="24" />
            <span class="text-sm font-bold">Checkout totals are calculated from backend product prices.</span>
          </div>
        </div>
      </section>

      <section class="mx-auto max-w-[1320px] px-6 py-14 lg:px-12">
        <div class="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 class="text-3xl font-semibold">Featured products</h2>
            <p class="mt-2 text-sm text-[#647266]">Pick any product below to continue into the real product detail and cart flow.</p>
          </div>
        </div>

        <div v-if="errorMessage" class="mb-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
          {{ errorMessage }}
        </div>

        <div v-if="loading" class="flex min-h-[220px] items-center justify-center text-[#647266]">
          Loading products...
        </div>

        <div v-else-if="visibleProducts.length" class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="product in visibleProducts.slice(0, 6)"
            :key="product.id"
            class="group cursor-pointer border border-[#e3e9df] bg-white"
            @click="openProduct(product.id)"
          >
            <div class="aspect-[4/3] overflow-hidden bg-[#edf1eb]">
              <img
                v-if="getProductImage(product)"
                class="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
                :src="getProductImage(product)"
                :alt="product.name"
              />
            </div>
            <div class="p-6">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-xs font-black uppercase tracking-[0.2em] text-[#8a967f]">{{ product.category || product.sku }}</p>
                  <h3 class="mt-2 text-xl font-semibold">{{ product.name }}</h3>
                </div>
                <span
                  class="shrink-0 border px-3 py-1 text-xs font-black"
                  :class="product.available_stock > 0 ? 'border-[#cdd8c6] text-[#536747]' : 'border-[#ef4444] text-[#ef4444]'"
                >
                  {{ product.available_stock > 0 ? `Stock ${product.available_stock}` : 'Sold out' }}
                </span>
              </div>
              <p class="mt-4 min-h-[48px] text-sm leading-6 text-[#647266]">{{ product.description || 'Open the detail page to configure this product.' }}</p>
              <div class="mt-6 flex items-center justify-between">
                <span class="text-2xl font-black text-[#d78368]">¥{{ product.price }}</span>
                <span class="inline-flex items-center gap-2 px-5 py-3 text-sm font-black text-[#1f2f25]">
                  <ShoppingBag :size="17" />
                  View details
                </span>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="border border-dashed border-[#d7dfd2] bg-white px-8 py-16 text-center">
          <p class="text-lg font-black">No products available yet</p>
          <p class="mt-3 text-sm text-[#647266]">Once active products exist in the backend catalog, they will appear here automatically.</p>
        </div>
      </section>
    </main>

    <Footer variant="white" />
  </div>
</template>
