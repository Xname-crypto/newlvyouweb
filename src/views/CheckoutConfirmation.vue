<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Heart } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import CheckoutSteps from '@/components/CheckoutSteps.vue'
import { commerceService, getProductImage, type Product } from '@/services/commerceService'
import { readCheckoutDraft, writeCheckoutDraft } from '@/services/checkoutService'

const RECOMMENDATION_CACHE_KEY = 'ct_checkout_recommendations'
const router = useRouter()
const draft = ref(readCheckoutDraft())
const isSubmitting = ref(false)
const errorMessage = ref('')
const recommendedProducts = ref<Product[]>([])

const hasItems = computed(() => draft.value.items.length > 0)
const subtotal = computed(() => draft.value.items.reduce((sum, item) => sum + Number(String(item.price).replace(/[^\d.]/g, '')) * item.quantity, 0))
const total = computed(() => subtotal.value.toFixed(2))
const showcasedRecommendations = computed(() => recommendedProducts.value.slice(0, 8))

const formatProductPrice = (product: Product) => `¥${Number(product.price || ((product.price_cents || 0) / 100).toFixed(2)).toFixed(2)}`
const getOldPrice = (product: Product) => {
  const cents = Number(product.metadata?.old_price_cents || 0)
  return cents > 0 ? `¥${(cents / 100).toFixed(2)}` : ''
}
const hasPromoBadge = (index: number) => index === 0 || index === 4

const readRecommendationCache = () => {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.sessionStorage.getItem(RECOMMENDATION_CACHE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const writeRecommendationCache = (products: Product[]) => {
  if (typeof window === 'undefined') return
  window.sessionStorage.setItem(RECOMMENDATION_CACHE_KEY, JSON.stringify(products))
}

const buildNormalizedShippingAddress = () => {
  const shippingAddress = {
    ...draft.value.shippingAddress,
  }
  const firstName = String(shippingAddress.first_name || '').trim()
  const lastName = String(shippingAddress.last_name || '').trim()

  if (!lastName && firstName) {
    const normalized = firstName.replace(/\s+/g, ' ').trim()
    const parts = normalized.split(' ').filter(Boolean)
    if (parts.length > 1) {
      shippingAddress.last_name = parts[0]
      shippingAddress.first_name = parts.slice(1).join(' ')
    } else {
      shippingAddress.last_name = normalized
      shippingAddress.first_name = normalized
    }
  }

  return shippingAddress
}

const formatShippingAddress = () => {
  const parts = [
    draft.value.shippingAddress.country,
    draft.value.shippingAddress.city,
    draft.value.shippingAddress.post_code,
    draft.value.shippingAddress.address,
  ]
    .map((value) => String(value || '').trim())
    .filter(Boolean)

  return parts.join('')
}

const formatRecipientName = () => {
  const firstName = String(draft.value.shippingAddress.first_name || '').trim()
  const lastName = String(draft.value.shippingAddress.last_name || '').trim()
  if (!firstName && !lastName) return ''
  if (!firstName) return lastName
  if (!lastName) return firstName
  return firstName === lastName ? firstName : `${lastName} ${firstName}`
}

const loadRecommendations = async () => {
  try {
    const products = await commerceService.listProducts()
    const cartProductIds = new Set(draft.value.items.map((item) => item.productId).filter(Boolean))
    recommendedProducts.value = products.filter((product) => !cartProductIds.has(product.id)).slice(0, 8)
    writeRecommendationCache(recommendedProducts.value)
  } catch (error) {
    console.error('Failed to load recommended products:', error)
    if (!recommendedProducts.value.length) {
      recommendedProducts.value = []
    }
  }
}

const placeOrder = async () => {
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    const shippingAddress = buildNormalizedShippingAddress()
    draft.value.shippingAddress = shippingAddress
    const order = await commerceService.createCheckoutOrder({
      items: draft.value.items
        .filter((item) => item.productId)
        .map((item) => ({
          id: item.id,
          cart_item_id: item.id,
          product_id: item.productId as number,
          quantity: item.quantity,
          selected_size: item.size,
          selected_color: item.color,
          metadata: item.productSnapshot || {},
        })),
      shipping_address: shippingAddress,
      shipping_method: draft.value.shippingMethod,
      payment_method: 'alipay',
      contact_email: shippingAddress.email || draft.value.contactEmail,
      contact_phone: shippingAddress.phone || draft.value.contactPhone,
      note: draft.value.note,
      client_request_id: `checkout-${Date.now()}`,
    })
    draft.value.orderId = order.id
    draft.value.orderNo = order.order_no
    draft.value.cachedOrder = order
    draft.value.checkoutPayUrl = order.payment_order?.pay_url || ''
    writeCheckoutDraft(draft.value)
    router.push(`/checkout/payment?order=${order.id}`)
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '确认订单失败，请稍后重试。')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  if (!hasItems.value) {
    router.replace('/cart')
    return
  }

  recommendedProducts.value = readRecommendationCache()
  await loadRecommendations()
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdfa] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <main class="mx-auto max-w-[1280px] px-6 pb-24 pt-[124px] lg:px-10">
      <CheckoutSteps current="confirm" />
      <div class="mt-8 grid gap-12 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section>
          <h1 class="text-[32px] font-semibold tracking-tight">确认订单</h1>
          <p class="mt-6 text-[18px] font-semibold">收货信息</p>

          <div class="mt-5 border border-[#d9d1c8] bg-white">
            <div class="grid grid-cols-[84px_1fr_auto] gap-3 border-b border-[#ece6de] px-4 py-4 text-sm">
              <span class="font-bold text-[#6f665d]">联系方式</span>
              <span>{{ draft.shippingAddress.email || draft.shippingAddress.phone }}</span>
              <router-link to="/checkout/information" class="text-[#e7a688]">修改</router-link>
            </div>
            <div class="grid grid-cols-[84px_1fr_auto] gap-3 border-b border-[#ece6de] px-4 py-4 text-sm">
              <span class="font-bold text-[#6f665d]">收件人</span>
              <span>{{ formatRecipientName() }}</span>
              <router-link to="/checkout/information" class="text-[#e7a688]">修改</router-link>
            </div>
            <div class="grid grid-cols-[84px_1fr_auto] gap-3 px-4 py-4 text-sm">
              <span class="font-bold text-[#6f665d]">收货地址</span>
              <span>{{ formatShippingAddress() }}</span>
              <router-link to="/checkout/information" class="text-[#e7a688]">修改</router-link>
            </div>
          </div>

          <p class="mt-10 text-[18px] font-semibold">配送方式</p>
            <div class="mt-5 border border-[#d9d1c8] px-4 py-4 text-sm">
              <span class="text-[#e7a688]">●</span>
              <span class="ml-2">商品总价以后台售价为准</span>
            </div>

          <p class="mt-10 text-[18px] font-semibold">支付方式</p>
          <div class="mt-5 border border-[#d9d1c8] px-4 py-4 text-sm">
            <span class="text-[#e7a688]">●</span>
            <span class="ml-2">支付宝</span>
          </div>

          <div v-if="errorMessage" class="mt-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
            {{ errorMessage }}
          </div>

          <div class="mt-8 flex flex-wrap items-center justify-between gap-4">
            <router-link to="/checkout/information" class="text-sm font-black text-[#2f2c27]">返回填写信息</router-link>
            <button
              type="button"
              class="bg-[#eca37f] px-8 py-4 text-sm font-black text-white transition-colors hover:bg-[#d78368] disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="isSubmitting"
              @click="placeOrder"
            >
              {{ isSubmitting ? '订单提交中...' : '确认订单' }}
            </button>
          </div>
        </section>

        <aside class="pt-10 lg:pt-12">
          <div v-for="item in draft.items" :key="item.id" class="mb-5 flex items-center gap-4">
            <img :src="item.image" :alt="item.name" class="h-16 w-14 object-cover" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">{{ item.name }}</p>
              <p class="mt-1 text-xs text-[#7c7469]">{{ item.meta }}</p>
            </div>
            <span class="text-sm font-semibold">¥{{ Number(String(item.price).replace(/[^\d.]/g, '')).toFixed(2) }}</span>
          </div>

          <div class="mt-8 border-t border-[#ece6de] pt-5">
            <div class="mb-3 flex items-center justify-between text-sm">
              <span>商品小计</span>
              <span>¥{{ subtotal.toFixed(2) }}</span>
            </div>
            <div class="flex items-center justify-between border-t border-[#ece6de] pt-4 text-[32px] font-semibold text-[#f09e7f]">
              <span class="text-base font-bold text-[#2f2c27]">合计</span>
              <span>¥{{ total }}</span>
            </div>
          </div>
        </aside>
      </div>

      <section v-if="showcasedRecommendations.length" class="mt-24">
        <p class="text-sm font-black uppercase tracking-[0.06em] text-[#827870]">猜你喜欢</p>
        <div class="mt-8 grid grid-cols-2 gap-x-6 gap-y-10 md:grid-cols-3 xl:grid-cols-4">
          <article v-for="(product, index) in showcasedRecommendations" :key="product.id" class="group">
            <router-link :to="{ name: 'product-detail', params: { id: String(product.id) } }" class="block">
              <div class="relative flex h-[260px] items-center justify-center overflow-hidden bg-[#f5f2ee] p-3 sm:h-[320px] lg:h-[360px] lg:p-4">
                <img v-if="getProductImage(product)" class="max-h-full max-w-full object-contain transition duration-500 group-hover:scale-[1.02]" :src="getProductImage(product)" :alt="product.name" />
                <div v-if="hasPromoBadge(index)" class="absolute left-0 top-3 flex items-center text-[10px] font-bold leading-none">
                  <span class="bg-[#ef6d6d] px-2 py-[3px] text-white">-12%</span>
                  <span class="bg-white px-2 py-[3px] text-[#ef6d6d]">新品</span>
                </div>
                <button type="button" class="absolute right-3 top-3 text-white/90">
                  <Heart :size="15" />
                </button>
              </div>
              <p class="mt-4 min-h-[40px] text-[13px] leading-5 text-[#6e655d]">{{ product.name }}</p>
              <div class="mt-2 min-h-[20px] flex items-center gap-2 text-[13px]">
                <span v-if="getOldPrice(product)" class="text-[#b7afa6] line-through">{{ getOldPrice(product) }}</span>
                <span class="font-medium text-[#f0a484]">{{ formatProductPrice(product) }}</span>
              </div>
            </router-link>
          </article>
        </div>
      </section>
    </main>

    <Footer variant="white" />
  </div>
</template>
