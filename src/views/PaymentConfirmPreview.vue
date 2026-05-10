<script setup lang="ts">
import { computed, ref } from 'vue'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import PaymentConfirmView from '@/components/checkout/PaymentConfirmView.vue'

type PaymentConfirmState = 'checking' | 'success' | 'pending' | 'expired' | 'error'

const currentState = ref<PaymentConfirmState>('checking')

const states: Array<{ value: PaymentConfirmState; label: string }> = [
  { value: 'checking', label: '确认中' },
  { value: 'pending', label: '待确认' },
  { value: 'success', label: '支付成功' },
  { value: 'expired', label: '已超时' },
  { value: 'error', label: '异常' },
]

const title = computed(() => {
  if (currentState.value === 'success') return '支付成功'
  if (currentState.value === 'expired') return '订单已超时'
  if (currentState.value === 'error') return '支付结果待确认'
  if (currentState.value === 'pending') return '等待支付确认'
  return '正在确认支付结果'
})

const statusMessage = computed(() => {
  if (currentState.value === 'success') return '支付已确认，正在为你跳转到支付成功页面。'
  if (currentState.value === 'expired') return '这笔订单已经超过支付保留时间，请返回购物车重新下单。'
  if (currentState.value === 'error') return '系统暂时无法确认支付结果，请稍后重试。'
  if (currentState.value === 'pending') return '还没有收到支付平台的成功通知。如果你已经付款，请稍等几秒或点击重新确认。'
  return '正在向支付平台核对付款结果，请稍候...'
})

const errorMessage = computed(() => {
  if (currentState.value !== 'error') return ''
  return '预览用错误信息：支付平台暂时没有返回明确结果。'
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <div class="preview-switcher fixed right-6 top-[120px] z-30 flex flex-col gap-2 rounded-[18px] border border-[#eee5db] bg-white/95 p-2 shadow-[0_12px_36px_rgba(47,44,39,0.08)] backdrop-blur">
      <button
        v-for="item in states"
        :key="item.value"
        type="button"
        class="rounded-full px-4 py-2 text-xs font-black transition-colors"
        :class="currentState === item.value ? 'bg-[#2f2c27] text-white' : 'text-[#6f665d] hover:bg-[#faf3ed]'"
        @click="currentState = item.value"
      >
        {{ item.label }}
      </button>
    </div>

    <PaymentConfirmView
      :state="currentState"
      :title="title"
      :status-message="statusMessage"
      order-no="CT202605080001"
      :error-message="errorMessage"
      :disable-back="currentState === 'success'"
      show-help
      @refresh="currentState = 'checking'"
      @back="currentState = 'pending'"
    />

    <Footer variant="white" />
  </div>
</template>

<style scoped>
@media (max-width: 768px) {
  .preview-switcher {
    right: 50%;
    top: auto;
    bottom: 1rem;
    transform: translateX(50%);
    width: calc(100vw - 2rem);
    max-width: 360px;
    flex-direction: row;
    justify-content: center;
    overflow-x: auto;
    border-radius: 999px;
  }
}
</style>
