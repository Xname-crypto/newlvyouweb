<script setup lang="ts">
import { AlertCircle, Check, RefreshCw } from 'lucide-vue-next'
import CheckoutSteps from '@/components/CheckoutSteps.vue'

type PaymentConfirmState = 'checking' | 'success' | 'pending' | 'expired' | 'error'

withDefaults(defineProps<{
  state: PaymentConfirmState
  title: string
  statusMessage: string
  orderNo?: string
  errorMessage?: string
  disableBack?: boolean
  showHelp?: boolean
  showSteps?: boolean
}>(), {
  disableBack: false,
  showHelp: false,
  showSteps: true,
})

defineEmits<{
  refresh: []
  back: []
}>()
</script>

<template>
  <main class="payment-confirm mx-auto max-w-[1280px] px-6 pb-24 pt-[124px] text-center lg:px-10">
    <CheckoutSteps v-if="showSteps" current="verify" />

    <section class="payment-confirm__body">
      <div class="payment-confirm__mark" :data-state="state">
        <div v-if="state === 'checking'" class="payment-confirm__waiting-spinner" aria-hidden="true"></div>
        <div v-else-if="state === 'success'" class="payment-confirm__success-badge" aria-hidden="true">
          <Check :size="104" :stroke-width="3.5" />
        </div>
        <AlertCircle v-else class="text-[#d47e67]" :size="64" />
      </div>

      <h1 class="mt-8 text-[40px] font-semibold tracking-tight">
        {{ title }}
      </h1>

      <p class="mt-4 max-w-[620px] text-base leading-8 text-[#6f665d]">
        {{ statusMessage }}
      </p>

      <p v-if="orderNo" class="mt-2 text-sm text-[#8a8178]">
        订单编号：{{ orderNo }}
      </p>

      <p v-if="errorMessage" class="mt-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
        {{ errorMessage }}
      </p>

      <div class="mt-8 flex flex-wrap items-center justify-center gap-4">
        <button
          type="button"
          class="inline-flex items-center gap-2 bg-[#eca37f] px-8 py-3 text-sm font-black text-white transition-colors hover:bg-[#d78368]"
          @click="$emit('refresh')"
        >
          <RefreshCw :size="16" />
          重新确认
        </button>
        <button
          type="button"
          class="border border-[#d9d1c8] px-8 py-3 text-sm font-black text-[#2f2c27] transition-colors hover:bg-[#faf8f5]"
          :disabled="disableBack"
          :class="{ 'cursor-not-allowed opacity-50': disableBack }"
          @click="$emit('back')"
        >
          返回支付页
        </button>
      </div>

      <div v-if="showHelp" class="payment-confirm__help">
        <p class="text-sm font-black uppercase tracking-[0.12em] text-[#d19a84]">支付说明</p>
        <p class="mt-3 text-sm leading-7 text-[#6f665d]">
          如果你已经完成扫码支付，系统会自动向 ZPay 核对支付结果。网络较慢时可能需要几秒钟，也可以点击“重新确认”手动刷新状态。
        </p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.payment-confirm__body {
  min-height: calc(100vh - 260px);
  max-width: 920px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 2rem auto 0;
}

.payment-confirm__mark {
  width: 132px;
  height: 132px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 10px solid #f2ede6;
  border-radius: 999px;
  background: #ffffff;
  box-shadow: 0 20px 60px rgba(233, 167, 138, 0.12);
}

.payment-confirm__mark[data-state='checking'] {
  width: 190px;
  height: 190px;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.payment-confirm__waiting-spinner {
  position: relative;
  width: 190px;
  height: 190px;
  border-radius: 999px;
  background: conic-gradient(from 20deg, transparent 0deg 58deg, #ffa17e 58deg 238deg, transparent 238deg 360deg);
  animation: payment-confirm-spin 1.35s linear infinite;
}

.payment-confirm__waiting-spinner::after {
  position: absolute;
  inset: 10px;
  content: "";
  border-radius: inherit;
  background: #eeeeee;
}

.payment-confirm__mark[data-state='success'] {
  width: 190px;
  height: 190px;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.payment-confirm__success-badge {
  width: 190px;
  height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f8a17f;
  color: #ffffff;
  animation: payment-confirm-success-pop 420ms cubic-bezier(0.2, 1.2, 0.4, 1) both;
}

.payment-confirm__mark[data-state='expired'],
.payment-confirm__mark[data-state='error'] {
  border-color: #f5dfd8;
  box-shadow: 0 20px 60px rgba(212, 126, 103, 0.12);
}

.payment-confirm__help {
  max-width: 520px;
  margin-top: 2.5rem;
  border: 1px solid #eee5db;
  border-radius: 1rem;
  background: #ffffff;
  padding: 1.25rem 1.5rem;
  text-align: left;
  box-shadow: 0 12px 40px rgba(47, 44, 39, 0.05);
}

@keyframes payment-confirm-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes payment-confirm-success-pop {
  0% {
    opacity: 0;
    transform: scale(0.82);
  }

  70% {
    opacity: 1;
    transform: scale(1.04);
  }

  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 640px) {
  .payment-confirm {
    padding-top: 96px;
  }

  .payment-confirm__body {
    min-height: calc(100vh - 220px);
  }

  .payment-confirm__mark,
  .payment-confirm__mark[data-state='checking'],
  .payment-confirm__mark[data-state='success'],
  .payment-confirm__success-badge {
    width: 112px;
    height: 112px;
  }

  .payment-confirm__waiting-spinner {
    width: 112px;
    height: 112px;
  }

  .payment-confirm__waiting-spinner::after {
    inset: 7px;
  }
}
</style>
