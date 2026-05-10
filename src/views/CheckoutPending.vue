<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import PaymentConfirmView from '@/components/checkout/PaymentConfirmView.vue'
import { commerceService, type CommerceOrder } from '@/services/commerceService'
import { readCheckoutDraft, clearCheckoutDraft } from '@/services/checkoutService'
import { removeCartItems } from '@/services/cartService'

type PaymentConfirmState = 'checking' | 'success' | 'pending' | 'expired' | 'error'

const route = useRoute()
const router = useRouter()
const order = ref<CommerceOrder | null>(null)
const errorMessage = ref('')
const statusMessage = ref('正在确认支付结果，请稍候...')
const checking = ref(true)
let timer: number | undefined

const orderId = computed(() => String(route.query.order || ''))
const isPaid = computed(() => order.value?.status === 'paid')
const isPending = computed(() => ['pending_payment', 'payment_created'].includes(String(order.value?.status || '')))
const isExpired = computed(() => order.value?.status === 'expired')

const confirmState = computed<PaymentConfirmState>(() => {
  if (checking.value) return 'checking'
  if (isPaid.value) return 'success'
  if (isExpired.value) return 'expired'
  if (errorMessage.value) return 'error'
  return 'pending'
})

const title = computed(() => {
  if (confirmState.value === 'success') return '支付成功'
  if (confirmState.value === 'expired') return '订单已超时'
  if (confirmState.value === 'error') return '支付结果待确认'
  if (confirmState.value === 'pending') return '等待支付确认'
  return '正在确认支付结果'
})

const clearTimer = () => {
  if (timer) {
    window.clearInterval(timer)
    timer = undefined
  }
}

const finishPaidOrder = () => {
  const draft = readCheckoutDraft()
  removeCartItems(draft.items.map((item) => item.id))
  clearCheckoutDraft()
  clearTimer()
  router.replace(`/checkout/success?order=${order.value?.id}`)
}

const syncOrder = async () => {
  if (!orderId.value) return

  checking.value = true
  try {
    order.value = await commerceService.syncCheckoutOrder(orderId.value)
    errorMessage.value = ''

    if (isPaid.value) {
      statusMessage.value = '支付已确认，正在为你跳转到支付成功页面。'
      finishPaidOrder()
      return
    }

    if (isPending.value) {
      statusMessage.value = '还没有收到支付平台的成功通知。如果你已经付款，请稍等几秒或点击重新确认。'
      return
    }

    if (isExpired.value) {
      statusMessage.value = '这笔订单已经超过支付保留时间，请返回购物车重新下单。'
      return
    }

    statusMessage.value = '当前订单还没有进入支付确认状态，请返回支付页重新发起支付。'
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '支付结果确认失败')
    statusMessage.value = '系统暂时无法确认支付结果，请稍后重试。'
  } finally {
    checking.value = false
  }
}

const backToPayment = () => {
  router.push(`/checkout/payment?order=${orderId.value}`)
}

const refreshStatus = () => {
  syncOrder()
}

onMounted(() => {
  syncOrder()
  timer = window.setInterval(syncOrder, 5000)
})

onUnmounted(() => {
  clearTimer()
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <PaymentConfirmView
      :state="confirmState"
      :title="title"
      :status-message="statusMessage"
      :order-no="order?.order_no"
      :error-message="errorMessage"
      :disable-back="isExpired"
      @refresh="refreshStatus"
      @back="backToPayment"
    />

    <Footer variant="white" />
  </div>
</template>
