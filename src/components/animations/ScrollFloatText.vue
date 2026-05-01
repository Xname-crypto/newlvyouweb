<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';

interface Props {
  text: string;
  tag?: string;
  containerClass?: string;
  textClass?: string;
  stagger?: number;
  duration?: number;
  threshold?: number;
  rootMargin?: string;
  once?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  containerClass: '',
  textClass: '',
  stagger: 0.05,
  duration: 0.9,
  threshold: 0.18,
  rootMargin: '0px 0px -12% 0px',
  once: false,
});

const rootRef = ref<HTMLElement | null>(null);
const isVisible = ref(false);

let observer: IntersectionObserver | null = null;

const characters = computed(() => Array.from(props.text));

const getCharStyle = (index: number) => ({
  '--scroll-float-delay': `${index * props.stagger}s`,
  '--scroll-float-duration': `${props.duration}s`,
});

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    isVisible.value = true;
    return;
  }

  observer = new IntersectionObserver(
    ([entry]) => {
      if (!entry) {
        return;
      }

      if (entry.isIntersecting) {
        isVisible.value = true;

        if (props.once) {
          observer?.disconnect();
        }
      } else if (!props.once) {
        isVisible.value = false;
      }
    },
    {
      threshold: props.threshold,
      rootMargin: props.rootMargin,
    }
  );

  if (rootRef.value) {
    observer.observe(rootRef.value);
  }
});

onUnmounted(() => {
  observer?.disconnect();
});
</script>

<template>
  <component
    :is="tag"
    ref="rootRef"
    :class="['scroll-float', containerClass, { 'is-visible': isVisible }]"
    :aria-label="text"
  >
    <span aria-hidden="true" :class="['scroll-float__content', textClass]">
      <span
        v-for="(char, index) in characters"
        :key="`${char}-${index}`"
        class="scroll-float__char"
        :style="getCharStyle(index)"
      >
        {{ char === ' ' ? '\u00A0' : char }}
      </span>
    </span>
  </component>
</template>

<style scoped>
.scroll-float {
  overflow: hidden;
}

.scroll-float__content {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  width: 100%;
  white-space: pre-wrap;
  padding-bottom: 0.24em;
  margin-bottom: -0.24em;
}

.scroll-float__char {
  display: inline-block;
  opacity: 0;
  filter: blur(6px);
  transform: translate3d(0, 0.82em, 0) scaleX(0.76) scaleY(1.7);
  transform-origin: 50% 0%;
  will-change: transform, opacity, filter;
  transition:
    transform var(--scroll-float-duration) cubic-bezier(0.22, 1, 0.36, 1) var(--scroll-float-delay),
    opacity calc(var(--scroll-float-duration) * 0.72) ease-out var(--scroll-float-delay),
    filter calc(var(--scroll-float-duration) * 0.9) ease-out var(--scroll-float-delay);
}

.scroll-float.is-visible .scroll-float__char {
  opacity: 1;
  filter: blur(0);
  transform: translate3d(0, 0, 0) scaleX(1) scaleY(1);
}

@media (prefers-reduced-motion: reduce) {
  .scroll-float__char {
    opacity: 1;
    filter: none;
    transform: none;
    transition: none;
  }
}
</style>
