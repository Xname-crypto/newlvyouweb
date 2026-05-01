<script setup lang="ts">
interface Props {
  text: string
  tag?: string
  containerClass?: string
  textClass?: string
  speed?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'span',
  containerClass: '',
  textClass: '',
  speed: 5,
  disabled: false,
})
</script>

<template>
  <component
    :is="tag"
    :class="['shiny-text', containerClass, { 'is-disabled': disabled }]"
    :style="{ '--shiny-duration': `${speed}s` }"
  >
    <span :class="['shiny-text__content', textClass]">
      {{ text }}
    </span>
  </component>
</template>

<style scoped>
.shiny-text {
  display: inline-block;
}

.shiny-text__content {
  display: inline-block;
  color: rgba(45, 49, 53, 0.34);
  background-image: linear-gradient(
    112deg,
    rgba(45, 49, 53, 0.28) 0%,
    rgba(45, 49, 53, 0.72) 38%,
    rgba(255, 255, 255, 0.98) 50%,
    rgba(45, 49, 53, 0.72) 62%,
    rgba(45, 49, 53, 0.28) 100%
  );
  background-size: 220% 100%;
  background-position: 120% 50%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shiny-text-sweep var(--shiny-duration) linear infinite;
}

.shiny-text.is-disabled .shiny-text__content {
  animation: none;
  background-image: none;
  color: #2d3135;
  -webkit-text-fill-color: currentColor;
}

@keyframes shiny-text-sweep {
  0% {
    background-position: 120% 50%;
  }

  100% {
    background-position: -120% 50%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .shiny-text__content {
    animation: none;
    background-position: 50% 50%;
  }
}
</style>
