<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import CheckoutSteps from '@/components/CheckoutSteps.vue'
import { commerceService, type CommerceOrder } from '@/services/commerceService'
import { readCheckoutDraft, writeCheckoutDraft } from '@/services/checkoutService'

const route = useRoute()
const router = useRouter()
const order = ref<CommerceOrder | null>(null)
const payUrl = ref('')
const loading = ref(false)
const errorMessage = ref('')
const now = ref(Date.now())
let countdownTimer: number | undefined

const orderId = computed(() => String(route.query.order || ''))
const orderItems = computed(() => order.value?.items || [])
const expiresAtMs = computed(() => order.value?.expires_at ? new Date(order.value.expires_at).getTime() : 0)
const secondsRemaining = computed(() => expiresAtMs.value ? Math.max(0, Math.ceil((expiresAtMs.value - now.value) / 1000)) : 0)
const isExpired = computed(() => order.value?.status === 'expired' || (!!expiresAtMs.value && secondsRemaining.value <= 0))
const countdownText = computed(() => {
  const minutes = Math.floor(secondsRemaining.value / 60)
  const seconds = secondsRemaining.value % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

const shippingAddress = computed<Record<string, any>>(() => order.value?.shipping_address || {})
const recipientName = computed(() => {
  const firstName = String(shippingAddress.value.first_name || '').trim()
  const lastName = String(shippingAddress.value.last_name || '').trim()
  if (!firstName && !lastName) return '未填写'
  if (!firstName) return lastName
  if (!lastName) return firstName
  return firstName === lastName ? firstName : `${lastName} ${firstName}`
})
const recipientPhone = computed(() => String(shippingAddress.value.phone || order.value?.contact_phone || '').trim())
const maskedPhone = computed(() => {
  const phone = recipientPhone.value
  if (phone.length < 7) return phone || '未填写'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
})
const fullShippingAddress = computed(() => {
  const parts = [
    shippingAddress.value.province,
    shippingAddress.value.country,
    shippingAddress.value.city,
    shippingAddress.value.district,
    shippingAddress.value.post_code,
    shippingAddress.value.address,
    shippingAddress.value.apartment,
  ]
    .map((value) => String(value || '').trim())
    .filter(Boolean)

  return parts.join('') || '未填写'
})

const formatItemOptions = (item: CommerceOrder['items'][number]) => {
  const snapshot = item.product_snapshot || {}
  const metadata = (snapshot.metadata || snapshot) as Record<string, any>
  const requiresSize = metadata.requires_size !== false
  const size = String(item.selected_size || '').trim()
  const color = String(item.selected_color || '').trim()
  const hiddenValues = new Set(['-', '默认', 'default', '#000000', '#000'])
  return [requiresSize ? size : '', color]
    .filter((value) => value && !hiddenValues.has(value.toLowerCase()))
    .join(' / ')
}

const hydrateCachedPayment = () => {
  if (!orderId.value) return
  const draft = readCheckoutDraft()
  if (String(draft.orderId || '') !== orderId.value) return

  if (draft.cachedOrder) {
    order.value = draft.cachedOrder
  }

  const cachedPayUrl = draft.checkoutPayUrl || draft.cachedOrder?.payment_order?.pay_url || ''
  if (cachedPayUrl) {
    payUrl.value = cachedPayUrl
  }
}

const persistPayment = (latestOrder: CommerceOrder, latestPayUrl: string) => {
  const draft = readCheckoutDraft()
  if (draft.orderId && String(draft.orderId) !== String(latestOrder.id)) return

  draft.orderId = latestOrder.id
  draft.orderNo = latestOrder.order_no
  draft.cachedOrder = latestOrder
  draft.checkoutPayUrl = latestPayUrl || latestOrder.payment_order?.pay_url || ''
  writeCheckoutDraft(draft)
}

const loadPayment = async () => {
  if (!orderId.value) {
    router.replace('/cart')
    return
  }

  loading.value = !payUrl.value
  errorMessage.value = ''
  try {
    const payment = await commerceService.createCheckoutPayment(orderId.value)
    order.value = payment.order
    payUrl.value = payment.pay_url || payment.order.payment_order?.pay_url || payUrl.value
    persistPayment(payment.order, payUrl.value)
    if (order.value.status === 'expired') {
      errorMessage.value = '订单已超过支付时限，库存已释放。请重新下单。'
    }
  } catch (error) {
    if (!payUrl.value) {
      errorMessage.value = String((error as any)?.message || error || '加载支付信息失败，请稍后重试。')
    } else {
      console.warn('Failed to refresh payment information:', error)
    }
  } finally {
    loading.value = false
  }
}

const openPayment = () => {
  if (!payUrl.value || isExpired.value) return
  window.open(payUrl.value, '_blank', 'noopener,noreferrer')
  router.push(`/checkout/pending?order=${orderId.value}`)
}

const goPending = () => {
  router.push(`/checkout/pending?order=${orderId.value}`)
}

onMounted(() => {
  hydrateCachedPayment()
  loadPayment()
  countdownTimer = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (countdownTimer) window.clearInterval(countdownTimer)
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <main class="mx-auto max-w-[1180px] px-6 pb-24 pt-[124px] lg:px-8">
      <CheckoutSteps current="payment" />

      <div class="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_400px] lg:items-start">
        <section>
          <h1 class="text-[32px] font-semibold tracking-tight">支付</h1>

          <div class="mt-8 border border-[#e6ddd3] bg-white px-7 py-7">
            <div class="flex flex-wrap items-end justify-between gap-3 border-b border-[#ece6de] pb-5">
              <div>
                <p class="text-[18px] font-semibold">商品信息</p>
                <p class="mt-1 text-xs text-[#8a8178]">{{ order?.order_no || '正在读取订单' }}</p>
              </div>
              <span class="text-sm font-semibold text-[#cf765b]">{{ orderItems.length }} 件商品</span>
            </div>

            <div class="divide-y divide-[#ece6de]">
              <article v-for="item in orderItems" :key="item.id" class="grid gap-6 py-8 sm:grid-cols-[180px_minmax(0,1fr)_auto]">
                <div class="relative h-[210px] bg-[#f5f2ee] sm:h-[180px]">
                  <img :src="item.image_url" :alt="item.name" class="h-full w-full object-cover" />
                  <span class="absolute right-3 top-3 bg-[#2f2c27] px-2 py-1 text-xs font-bold text-white">x{{ item.quantity }}</span>
                </div>

                <div class="min-w-0">
                  <p class="text-[28px] font-semibold leading-none text-[#f09e7f]">¥{{ item.line_total }}</p>
                  <p class="mt-5 text-[17px] font-semibold leading-7 text-[#2f2c27]">{{ item.name }}</p>
                  <p v-if="formatItemOptions(item)" class="mt-7 text-sm text-[#7c7469]">规格：{{ formatItemOptions(item) }}</p>
                  <p class="mt-3 text-sm text-[#7c7469]">数量：{{ item.quantity }}</p>
                  <p class="mt-3 text-sm text-[#9a9187]">单价 ¥{{ item.unit_price }}</p>
                </div>

                <div class="text-right text-sm font-semibold text-[#2f2c27] sm:pt-2">
                  ¥{{ item.line_total }}
                </div>
              </article>
            </div>

            <div class="grid gap-5 border-t border-[#ece6de] pt-6 md:grid-cols-[minmax(0,1fr)_260px]">
              <div>
                <p class="text-sm font-bold text-[#2f2c27]">收件人</p>
                <p class="mt-3 text-sm leading-7 text-[#6f665d]">
                  <span class="font-semibold text-[#2f2c27]">{{ recipientName }}</span>
                  <span class="ml-2">{{ maskedPhone }}</span>
                  <br />
                  {{ fullShippingAddress }}
                </p>
              </div>

              <div class="space-y-3 text-sm">
                <div class="flex items-center justify-between text-[#6f665d]">
                  <span>商品小计</span>
                  <span>¥{{ order?.subtotal || '0.00' }}</span>
                </div>
                <div class="flex items-center justify-between text-[#6f665d]">
                  <span>额外运费</span>
                  <span>无</span>
                </div>
                <div class="flex items-end justify-between border-t border-[#ece6de] pt-4">
                  <span class="font-bold text-[#2f2c27]">合计</span>
                  <span class="text-[24px] font-semibold text-[#f09e7f]">¥{{ order?.total_amount || '0.00' }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <aside class="mt-20 lg:sticky lg:top-28">
          <div class="border border-[#d9d1c8] bg-white px-8 py-7">
            <p class="text-[18px] font-semibold text-[#2f2c27]">订单金额</p>
            <p class="mt-3 text-[32px] font-semibold text-[#f09e7f]">¥ {{ order?.total_amount || '0.00' }}</p>

            <div v-if="errorMessage" class="mt-6 border border-[#f0c7bd] bg-[#fff3ef] px-4 py-4 text-sm font-semibold leading-7 text-[#b24c37]">
              {{ errorMessage }}
            </div>

            <div v-else-if="loading" class="mt-6 border border-[#ece6de] bg-[#faf8f5] px-4 py-4 text-sm leading-7 text-[#6f665d]">
              正在生成支付链接...
            </div>

            <div v-else class="mt-6 rounded border border-[#ece6de] bg-[#faf8f5] px-4 py-4 text-sm leading-7 text-[#6f665d]">
              <p>支付链接已生成。</p>
              <p>点击下方按钮后，将跳转到 ZPay 收银台完成支付。</p>
              <p v-if="order?.expires_at" class="font-bold text-[#b24c37]">
                支付剩余时间：{{ countdownText }}
              </p>
            </div>

            <button
              type="button"
              class="mt-6 w-full bg-[#eca37f] px-5 py-3 text-sm font-black text-white transition-colors hover:bg-[#d78368]"
              :disabled="isExpired || loading || !!errorMessage"
              :class="{ 'cursor-not-allowed opacity-50': isExpired || loading || !!errorMessage }"
              @click="openPayment"
            >
              {{ isExpired ? '订单已超时' : '立即前往支付' }}
            </button>

            <button
              type="button"
              class="mt-3 w-full border border-[#d9d1c8] px-5 py-3 text-sm font-black text-[#2f2c27] transition-colors hover:bg-[#faf8f5]"
              @click="goPending"
            >
              我已完成支付
            </button>

            <button
              v-if="errorMessage"
              type="button"
              class="mt-3 w-full text-sm font-bold text-[#cf765b] transition-colors hover:text-[#a8513a]"
              @click="loadPayment"
            >
              重新生成支付信息
            </button>
          </div>
        </aside>
      </div>
    </main>

    <Footer variant="white" />
  </div>
</template>
