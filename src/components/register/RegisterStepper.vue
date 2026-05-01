<script setup lang="ts">
import { computed } from 'vue';

interface RegisterStepItem {
  id: number;
  code: string;
  label: string;
}

const props = defineProps<{
  currentStep: number;
  steps: RegisterStepItem[];
}>();

const activeStep = computed(
  () => props.steps.find((step) => step.id === props.currentStep) ?? props.steps[0]
);
</script>

<template>
  <div class="register-stepper" aria-label="Registration progress">
    <div :key="activeStep.id" class="register-stepper__inner">
      <span class="register-stepper__code">{{ activeStep.code }}</span>
      <span class="register-stepper__line" aria-hidden="true">
        <span class="register-stepper__line-fill"></span>
      </span>
      <span class="register-stepper__label">{{ activeStep.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.register-stepper {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
}

.register-stepper__inner {
  display: inline-flex;
  align-items: center;
  gap: 0.85rem;
}

.register-stepper__code,
.register-stepper__label {
  animation: register-stepper-fade 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.register-stepper__code {
  font-size: 1.2rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 0.08em;
  color: #f97316;
}

.register-stepper__line {
  position: relative;
  width: 2.4rem;
  height: 1px;
  overflow: hidden;
  background: rgba(226, 232, 240, 0.95);
}

.register-stepper__line-fill {
  display: block;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, rgba(251, 146, 60, 0.92), rgba(251, 146, 60, 0.14));
  transform-origin: left center;
  animation: register-stepper-line 420ms cubic-bezier(0.22, 1, 0.36, 1);
}

.register-stepper__label {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.18em;
  color: #94a3b8;
  text-transform: uppercase;
  white-space: nowrap;
}

@keyframes register-stepper-line {
  from {
    transform: scaleX(0);
    opacity: 0.4;
  }

  to {
    transform: scaleX(1);
    opacity: 1;
  }
}

@keyframes register-stepper-fade {
  from {
    opacity: 0;
    transform: translateX(-0.25rem);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 480px) {
  .register-stepper__inner {
    gap: 0.6rem;
  }

  .register-stepper__code {
    font-size: 0.98rem;
  }

  .register-stepper__line {
    width: 1.7rem;
  }

  .register-stepper__label {
    font-size: 0.78rem;
    letter-spacing: 0.12em;
  }
}
</style>
