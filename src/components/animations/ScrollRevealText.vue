<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';

interface Props {
  text: string;
  tag?: string;
  containerClass?: string;
  textClass?: string;
  enableBlur?: boolean;
  baseOpacity?: number;
  baseRotation?: number;
  blurStrength?: number;
  wordStagger?: number;
  duration?: number;
  translateY?: number;
  threshold?: number;
  rootMargin?: string;
  once?: boolean;
}

interface SplitWord {
  text: string;
  type: 'word' | 'space' | 'newline';
  wordIndex: number;
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  containerClass: '',
  textClass: '',
  enableBlur: true,
  baseOpacity: 0.24,
  baseRotation: 2,
  blurStrength: 2.5,
  wordStagger: 0.05,
  duration: 0.7,
  translateY: 0.42,
  threshold: 0.28,
  rootMargin: '0px 0px -12% 0px',
  once: false,
});

const rootRef = ref<HTMLElement | null>(null);
const isVisible = ref(false);

let observer: IntersectionObserver | null = null;

const splitWords = computed<SplitWord[]>(() => {
  let visibleIndex = 0;
  const IntlWithSegmenter = Intl as typeof Intl & {
    Segmenter?: new (
      locales?: string | string[],
      options?: { granularity?: 'grapheme' | 'word' | 'sentence' }
    ) => {
      segment(input: string): Iterable<{ segment: string }>;
    };
  };

  const lineTokens = props.text.split(/(\n)/).flatMap((part) => {
    if (part === '\n') {
      return [part];
    }

    if (typeof Intl !== 'undefined' && typeof IntlWithSegmenter.Segmenter !== 'undefined') {
      return Array.from(
        new IntlWithSegmenter.Segmenter('zh-CN', { granularity: 'word' }).segment(part),
        ({ segment }) => segment
      );
    }

    return part.split(/(\s+)/);
  });

  return lineTokens.map((part) => {
    let type: SplitWord['type'] = 'word';

    if (part === '\n') {
      type = 'newline';
    } else if (/^\s+$/.test(part)) {
      type = 'space';
    }

    const item = {
      text: part,
      type,
      wordIndex: type === 'word' ? visibleIndex : -1,
    };

    if (type === 'word') {
      visibleIndex += 1;
    }

    return item;
  });
});

const rootStyle = computed(() => ({
  '--scroll-reveal-duration': `${props.duration}s`,
  '--scroll-reveal-rotation': `${props.baseRotation}deg`,
  '--scroll-reveal-opacity': `${props.baseOpacity}`,
  '--scroll-reveal-translate': `${props.translateY}em`,
  '--scroll-reveal-blur': props.enableBlur ? `${props.blurStrength}px` : '0px',
}));

const getWordStyle = (word: SplitWord) => {
  if (word.type !== 'word') {
    return {};
  }

  return {
    '--scroll-reveal-delay': `${word.wordIndex * props.wordStagger}s`,
  };
};

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
    :class="['scroll-reveal', containerClass, { 'is-visible': isVisible }]"
    :style="rootStyle"
    :aria-label="text"
  >
    <span aria-hidden="true" :class="['scroll-reveal__content', textClass]">
      <template v-for="(word, index) in splitWords" :key="`${word.text}-${index}`">
        <span
          v-if="word.type === 'word'"
          class="scroll-reveal__word"
          :style="getWordStyle(word)"
        >
          {{ word.text }}
        </span>
        <span v-else-if="word.type === 'space'" class="scroll-reveal__space">{{ word.text }}</span>
        <span v-else class="scroll-reveal__break" aria-hidden="true"></span>
      </template>
    </span>
  </component>
</template>

<style scoped>
.scroll-reveal {
  transform: rotate(var(--scroll-reveal-rotation));
  transform-origin: 0% 50%;
  transition: transform var(--scroll-reveal-duration) cubic-bezier(0.22, 1, 0.36, 1);
}

.scroll-reveal.is-visible {
  transform: rotate(0deg);
}

.scroll-reveal__content {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  width: 100%;
}

.scroll-reveal__word {
  display: inline-block;
  opacity: var(--scroll-reveal-opacity);
  filter: blur(var(--scroll-reveal-blur));
  transform: translate3d(0, var(--scroll-reveal-translate), 0);
  will-change: transform, opacity, filter;
  transition:
    transform var(--scroll-reveal-duration) cubic-bezier(0.22, 1, 0.36, 1) var(--scroll-reveal-delay),
    opacity calc(var(--scroll-reveal-duration) * 0.82) ease-out var(--scroll-reveal-delay),
    filter calc(var(--scroll-reveal-duration) * 0.82) ease-out var(--scroll-reveal-delay);
}

.scroll-reveal.is-visible .scroll-reveal__word {
  opacity: 1;
  filter: blur(0px);
  transform: translate3d(0, 0, 0);
}

.scroll-reveal__space {
  white-space: pre;
}

.scroll-reveal__break {
  flex-basis: 100%;
  height: 0;
}

@media (prefers-reduced-motion: reduce) {
  .scroll-reveal,
  .scroll-reveal.is-visible {
    transform: none !important;
  }

  .scroll-reveal__word {
    opacity: 1 !important;
    filter: none !important;
    transform: none !important;
    transition: none !important;
  }
}
</style>
