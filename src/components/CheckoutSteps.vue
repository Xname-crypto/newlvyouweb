<script setup lang="ts">
type CheckoutStepId = 'cart' | 'contact' | 'confirm' | 'payment' | 'verify' | 'success'

const props = defineProps<{
  current: CheckoutStepId
}>()

const steps: Array<{ id: CheckoutStepId; label: string }> = [
  { id: 'cart', label: '购物车' },
  { id: 'contact', label: '联系信息' },
  { id: 'confirm', label: '确认订单' },
  { id: 'payment', label: '支付' },
  { id: 'verify', label: '支付确认' },
  { id: 'success', label: '支付成功' },
]

const currentIndex = () => steps.findIndex((step) => step.id === props.current)
</script>

<template>
  <nav class="checkout-steps" aria-label="结算流程">
    <ol>
      <li
        v-for="(step, index) in steps"
        :key="step.id"
        :class="{
          'is-current': step.id === current,
          'is-complete': index < currentIndex(),
        }"
      >
        <span class="step-dot">{{ index + 1 }}</span>
        <span class="step-label">{{ step.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.checkout-steps {
  width: 100%;
  overflow-x: auto;
  padding-bottom: 0.25rem;
}

.checkout-steps ol {
  min-width: max-content;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #9a8f84;
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.checkout-steps li {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  white-space: nowrap;
}

.checkout-steps li:not(:last-child)::after {
  content: "/";
  margin-left: 0.55rem;
  color: #d7c9be;
  font-weight: 800;
}

.step-dot {
  width: 1.35rem;
  height: 1.35rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e1d5ca;
  border-radius: 999px;
  background: #fffdfa;
  color: #b29f91;
  font-size: 0.68rem;
  line-height: 1;
}

.is-complete,
.is-current {
  color: #d78368;
}

.is-complete .step-dot {
  border-color: #efc0aa;
  background: #fff2eb;
  color: #d78368;
}

.is-current .step-dot {
  border-color: #eca37f;
  background: #eca37f;
  color: #ffffff;
}

@media (max-width: 640px) {
  .checkout-steps ol {
    gap: 0.45rem;
    font-size: 0.68rem;
  }

  .step-dot {
    width: 1.2rem;
    height: 1.2rem;
    font-size: 0.62rem;
  }
}
</style>
