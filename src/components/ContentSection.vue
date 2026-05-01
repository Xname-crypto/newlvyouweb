<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next';
import ImageCard from './ImageCard.vue';
import ScrollRevealText from '@/components/animations/ScrollRevealText.vue';
import { cn } from '@/utils';

interface Props {
  step: string;
  tag: string;
  title: string;
  description: string;
  imageSrc: string;
  imageAlt: string;
  reverse?: boolean;
  id?: string;
}

const props = defineProps<Props>();
</script>

<template>
  <section :id="id" class="flex w-full justify-center px-4 py-16 md:py-24 xl:px-0">
    <div
      :class="
        cn(
          'flex w-full max-w-[1600px] flex-col items-center justify-between gap-32 lg:flex-row lg:gap-60 2xl:gap-[264px]',
          props.reverse ? 'lg:flex-row-reverse' : ''
        )
      "
    >
      <div class="relative w-full flex-shrink-0 lg:max-w-[720px]">
        <div
          class="pointer-events-none absolute -top-16 -left-4 z-0 select-none font-sans text-[120px] font-bold leading-none text-white opacity-10 md:-top-[106px] md:-left-[150px] md:text-[240px]"
        >
          {{ step }}
        </div>

        <div class="relative z-10 flex flex-col gap-[27px]">
          <div class="flex items-center gap-4">
            <div class="h-[2px] w-[72px] bg-accent"></div>
            <span class="font-sans text-lg font-extrabold uppercase tracking-[6px] text-accent">{{ tag }}</span>
          </div>

          <ScrollRevealText
            tag="h2"
            :text="title"
            container-class="max-w-[640px]"
            text-class="font-serif text-[40px] md:text-[72px] font-semibold leading-tight text-text-main"
            :base-opacity="0.42"
            :base-rotation="1.4"
            :blur-strength="1.2"
            :word-stagger="0.06"
            :duration="0.55"
            :translate-y="0.24"
          />

          <ScrollRevealText
            tag="p"
            :text="description"
            text-class="font-sans text-base md:text-xl font-bold leading-[36px] text-text-main"
            :enable-blur="false"
            :base-opacity="0.72"
            :base-rotation="0.4"
            :word-stagger="0.018"
            :duration="0.42"
            :translate-y="0.12"
          />

          <a href="#" class="inline-flex items-center gap-2 text-lg font-bold text-accent transition-all hover:gap-4">
            <span>阅读更多</span>
            <ArrowRight :size="16" class="h-4 w-4" />
          </a>
        </div>
      </div>

      <div class="flex w-full flex-shrink-0 justify-center lg:max-w-[660px]">
        <ImageCard :src="imageSrc" :alt="imageAlt" />
      </div>
    </div>
  </section>
</template>
