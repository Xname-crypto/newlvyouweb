<script setup lang="ts">
import { computed } from 'vue';
import PostCard from '@/components/community/PostCard.vue';
import type { Post } from '@/components/community/PostCard.vue';

type AnimateFrom = 'bottom' | 'top' | 'left' | 'right';

const props = withDefaults(defineProps<{
  posts: Post[];
  duration?: number;
  stagger?: number;
  animateFrom?: AnimateFrom;
  blurToFocus?: boolean;
}>(), {
  duration: 0.78,
  stagger: 0.06,
  animateFrom: 'bottom',
  blurToFocus: true,
});

const emit = defineEmits<{
  (e: 'select', post: Post): void;
}>();

const renderKey = computed(() => props.posts.map((post) => String(post.id)).join('|'));

const getOffset = (direction: AnimateFrom) => {
  switch (direction) {
    case 'top':
      return { x: '0px', y: '-54px' };
    case 'left':
      return { x: '-38px', y: '0px' };
    case 'right':
      return { x: '38px', y: '0px' };
    default:
      return { x: '0px', y: '54px' };
  }
};

const itemStyle = (index: number) => {
  const offset = getOffset(props.animateFrom);

  return {
    '--masonry-index': index,
    '--masonry-duration': `${props.duration}s`,
    '--masonry-stagger': `${props.stagger}s`,
    '--masonry-offset-x': offset.x,
    '--masonry-offset-y': offset.y,
    '--masonry-blur': props.blurToFocus ? '14px' : '0px',
  };
};
</script>

<template>
  <div :key="renderKey" class="community-masonry">
    <article
      v-for="(post, index) in posts"
      :key="`${renderKey}-${post.id}`"
      class="community-masonry__item"
      :style="itemStyle(index)"
      @click="emit('select', post)"
    >
      <PostCard :post="post" />
    </article>
  </div>
</template>

<style scoped>
.community-masonry {
  column-count: 2;
  column-gap: 0.9rem;
}

.community-masonry__item {
  break-inside: avoid;
  margin-bottom: 0.9rem;
  opacity: 0;
  transform: translate3d(var(--masonry-offset-x), var(--masonry-offset-y), 0) scale(0.985);
  filter: blur(var(--masonry-blur));
  animation: community-masonry-reveal var(--masonry-duration) cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--masonry-index) * var(--masonry-stagger));
  will-change: transform, opacity, filter;
}

@keyframes community-masonry-reveal {
  from {
    opacity: 0;
    transform: translate3d(var(--masonry-offset-x), var(--masonry-offset-y), 0) scale(0.985);
    filter: blur(var(--masonry-blur));
  }

  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
    filter: blur(0);
  }
}

@media (min-width: 768px) {
  .community-masonry {
    column-count: 3;
  }
}

@media (min-width: 1100px) {
  .community-masonry {
    column-count: 4;
  }
}

@media (min-width: 1280px) {
  .community-masonry {
    column-count: 5;
  }
}

@media (min-width: 1680px) {
  .community-masonry {
    column-count: 6;
  }
}
</style>
