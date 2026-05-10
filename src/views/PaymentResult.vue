<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import PaymentConfirmView from '@/components/checkout/PaymentConfirmView.vue'
import { commerceService, type CommerceOrder } from '@/services/commerceService'
import { clearCheckoutDraft, readCheckoutDraft } from '@/services/checkoutService'
import { removeCartItems } from '@/services/cartService'

const route = useRoute()
const router = useRouter()
type PaymentConfirmState = 'checking' | 'success' | 'pending' | 'expired' | 'error'
const order = ref<CommerceOrder | null>(null)
const errorMessage = ref('')
const statusMessage = ref('正在确认支付结果，请稍候...')
const state = ref<PaymentConfirmState>('checking')
let syncTimer: number | undefined

const checkoutOrderId = computed(() => String(route.query.checkout || route.query.order || ''))
const paymentOrderId = computed(() => String(route.query.payment || ''))

const title = computed(() => {
  if (state.value === 'success') return '支付成功'
  if (state.value === 'expired') return '订单已超时'
  if (state.value === 'error') return '支付结果待确认'
  if (state.value === 'pending') return '等待支付确认'
  return '正在确认支付结果'
})

const clearTimers = () => {
  if (syncTimer) {
    window.clearInterval(syncTimer)
    syncTimer = undefined
  }
}

const finishPaidOrder = (targetOrderId: number | string) => {
  if (typeof window !== 'undefined' && order.value) {
    window.sessionStorage.setItem(`ct_checkout_success_order_${targetOrderId}`, JSON.stringify(order.value))
  }

  const draft = readCheckoutDraft()
  removeCartItems(draft.items.map((item) => item.id))
  clearCheckoutDraft()
  clearTimers()
  router.replace(`/checkout/success?order=${targetOrderId}`)
}

const startSuccessCountdown = (targetOrderId: number | string) => {
  state.value = 'success'
  statusMessage.value = '支付已确认，正在为你跳转到支付成功页面。'
  clearTimers()
  finishPaidOrder(targetOrderId)
}

const syncOrder = async () => {
  if (!checkoutOrderId.value && !paymentOrderId.value) return

  state.value = 'checking'
  errorMessage.value = ''

  try {
    if (checkoutOrderId.value) {
      order.value = await commerceService.syncCheckoutOrder(checkoutOrderId.value)

      if (order.value.status === 'paid') {
        startSuccessCountdown(order.value.id)
        return
      }

      if (order.value.status === 'expired') {
        state.value = 'expired'
        statusMessage.value = '这笔订单已经超过支付保留时间，请返回购物车重新下单。'
        return
      }

      state.value = 'pending'
      statusMessage.value = '还没有收到支付平台的成功通知。如果你已经付款，请稍等几秒或点击重新确认。'
      return
    }

    const payment = await commerceService.syncOrder(paymentOrderId.value)

    if (payment.commerce_order) {
      if (payment.status === 'paid') {
        startSuccessCountdown(payment.commerce_order)
        return
      }

      state.value = 'pending'
      statusMessage.value = '支付平台还在确认这笔付款，请稍等几秒后系统会自动刷新。'
      return
    }

    state.value = 'error'
    statusMessage.value = '暂时没有找到对应的商城订单，请点击重新确认。'
  } catch (error) {
    state.value = 'error'
    errorMessage.value = String((error as any)?.message || error || '支付结果确认失败')
    statusMessage.value = '系统暂时无法确认支付结果，请稍后重试。'
  }
}

const refreshStatus = () => {
  clearTimers()
  syncOrder()
  syncTimer = window.setInterval(syncOrder, 5000)
}

const backToPayment = () => {
  router.push(`/checkout/payment?order=${checkoutOrderId.value || paymentOrderId.value}`)
}

onMounted(() => {
  syncOrder()
  syncTimer = window.setInterval(syncOrder, 5000)
})

onUnmounted(() => {
  clearTimers()
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <PaymentConfirmView
      :state="state"
      :title="title"
      :status-message="statusMessage"
      :order-no="order?.order_no"
      :error-message="errorMessage"
      :disable-back="state === 'success'"
      show-help
      @refresh="refreshStatus"
      @back="backToPayment"
    />

    <Footer variant="white" />
  </div>
</template>
