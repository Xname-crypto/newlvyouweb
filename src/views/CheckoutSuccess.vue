<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2 } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import CheckoutSteps from '@/components/CheckoutSteps.vue'
import { commerceService, type CommerceOrder } from '@/services/commerceService'

const route = useRoute()
const router = useRouter()
const order = ref<CommerceOrder | null>(null)
const errorMessage = ref('')
const loading = ref(true)

const orderId = computed(() => String(route.query.order || ''))
const orderCacheKey = computed(() => `ct_checkout_success_order_${orderId.value}`)

const normalizeText = (value: unknown) => String(value || '').trim()

const formatRecipientName = (address: Record<string, any>) => {
  const firstName = normalizeText(address.first_name)
  const lastName = normalizeText(address.last_name)
  if (!firstName && !lastName) return ''
  if (!firstName) return lastName
  if (!lastName) return firstName
  return firstName === lastName ? firstName : `${lastName} ${firstName}`
}

const formatShippingAddress = (address: Record<string, any>) =>
  [address.country, address.city, address.post_code, address.address]
    .map(normalizeText)
    .filter(Boolean)
    .join('')

const loadOrder = async () => {
  if (!orderId.value) {
    router.replace('/cart')
    return
  }
  loading.value = true

  if (typeof window !== 'undefined') {
    try {
      const cached = window.sessionStorage.getItem(orderCacheKey.value)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (parsed && typeof parsed === 'object') {
          order.value = parsed
        }
      }
    } catch {
      // ignore cache parse errors
    }
  }

  try {
    const freshOrder = await commerceService.getCheckoutOrder(orderId.value)
    order.value = freshOrder
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(orderCacheKey.value, JSON.stringify(freshOrder))
    }
  } catch (error) {
    if (!order.value) {
      errorMessage.value = String((error as any)?.message || error || '加载订单详情失败。')
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadOrder)
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />
    <main class="mx-auto max-w-[1280px] px-6 pb-24 pt-[124px] lg:px-10">
      <CheckoutSteps current="success" />
      <div class="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section>
          <div class="flex items-center gap-4">
            <CheckCircle2 class="text-[#eca37f]" :size="42" />
            <div>
              <p class="text-sm font-semibold text-[#6f665d]">Order #{{ order?.order_no }}</p>
              <h1 class="text-[34px] font-semibold tracking-tight">支付成功</h1>
            </div>
          </div>

          <div v-if="errorMessage" class="mt-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
            {{ errorMessage }}
          </div>

          <div v-else-if="order" class="mt-8 space-y-4">
            <div class="border border-[#d9d1c8] bg-white px-4 py-4">
              <p class="text-[22px] font-medium">订单已确认</p>
              <p class="mt-2 text-sm text-[#6f665d]">我们会尽快向你发送订单确认信息。</p>
            </div>

            <div class="border border-[#d9d1c8] bg-white px-4 py-5">
              <h2 class="text-lg font-semibold">收货信息</h2>
              <div class="mt-5 grid gap-6 sm:grid-cols-2">
                <div>
                  <p class="text-sm font-bold">联系方式</p>
                  <p class="mt-2 text-sm">{{ order.contact_email || order.contact_phone }}</p>
                </div>
                <div>
                  <p class="text-sm font-bold">支付方式</p>
                  <p class="mt-2 text-sm">支付宝</p>
                </div>
                <div>
                  <p class="text-sm font-bold">收件人</p>
                  <p class="mt-2 text-sm">{{ formatRecipientName(order.shipping_address) }}</p>
                </div>
                <div>
                  <p class="text-sm font-bold">收货地址</p>
                  <p class="mt-2 text-sm leading-7">
                    {{ formatShippingAddress(order.shipping_address) }}
                  </p>
                </div>
              </div>
            </div>

            <router-link to="/product-catalogue" class="inline-flex text-sm font-black text-[#2f2c27]">
              返回继续购物
            </router-link>
          </div>
        </section>

        <aside class="pt-10 lg:pt-12">
          <div v-for="item in order?.items || []" :key="item.id" class="mb-5 flex items-center gap-4">
            <img :src="item.image_url" :alt="item.name" class="h-16 w-14 object-cover" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold">{{ item.name }}</p>
              <p class="mt-1 text-xs text-[#7c7469]">{{ item.selected_size || '-' }} / {{ item.selected_color || '-' }}</p>
            </div>
            <span class="text-sm font-semibold">¥{{ item.line_total }}</span>
          </div>

          <div class="mt-8 border-t border-[#ece6de] pt-5">
            <div v-if="loading" class="mb-3 text-sm text-[#7f756b]">正在加载订单明细...</div>
            <div class="mb-3 flex items-center justify-between text-sm">
              <span>商品小计</span>
              <span>¥{{ order?.subtotal || '0.00' }}</span>
            </div>
            <div class="flex items-center justify-between border-t border-[#ece6de] pt-4 text-[32px] font-semibold text-[#f09e7f]">
              <span class="text-base font-bold text-[#2f2c27]">合计</span>
              <span>¥{{ order?.total_amount || '0.00' }}</span>
            </div>
          </div>
        </aside>
      </div>
    </main>
    <Footer variant="white" />
  </div>
</template>
