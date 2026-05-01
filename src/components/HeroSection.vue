<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ArrowDown } from 'lucide-vue-next';
import ScrollRevealText from '@/components/animations/ScrollRevealText.vue';

const scrollY = ref(0);

const handleScroll = () => {
  scrollY.value = window.scrollY;
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div class="relative flex h-[1200px] w-full flex-col items-center overflow-hidden pt-32 lg:pt-64">
    <div
      class="absolute top-0 left-0 z-0 h-full w-full bg-cover bg-center pointer-events-none"
      :style="{
        backgroundImage: `url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2070&auto=format&fit=crop')`,
        transform: `translateY(${scrollY * 0.5}px)`,
      }"
    >
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary/30 to-primary"></div>
      <div class="absolute inset-0 bg-gradient-to-t from-primary via-transparent to-transparent opacity-80"></div>
    </div>

    <div class="relative z-10 container mx-auto flex max-w-5xl flex-col items-start px-4 lg:px-20">
      <div class="mb-8 flex items-center gap-4">
        <div class="h-[2px] w-[72px] bg-accent"></div>
        <span class="font-sans text-lg font-bold uppercase tracking-[6px] text-accent">徒步向导</span>
      </div>

      <ScrollRevealText
        tag="h1"
        :text="'为山脉和更远的地方做\n好准备！'"
        container-class="mb-8 max-w-5xl"
        text-class="font-serif text-5xl md:text-7xl lg:text-[88px] leading-tight text-text-main"
        :base-opacity="0.32"
        :base-rotation="1.8"
        :blur-strength="1.4"
        :word-stagger="0.08"
        :duration="0.65"
        :translate-y="0.28"
      />

      <div class="mt-8 flex cursor-pointer items-center gap-4 font-bold text-text-main animate-bounce">
        <span>向下滑动</span>
        <ArrowDown :size="20" />
      </div>
    </div>
  </div>
</template>
