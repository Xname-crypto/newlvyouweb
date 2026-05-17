<script setup lang="ts">
defineProps<{
  activeSection: number;
}>();

const sections = [
  { id: 'hero', label: '\u5f00\u59cb' },
  { id: '01', label: '01' },
  { id: '02', label: '02' },
  { id: '03', label: '03' },
];

const scrollToSection = (sectionId: string) => {
  document.getElementById(sectionId)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  });
};
</script>

<template>
  <div class="fixed right-0 top-1/2 z-40 hidden -translate-y-1/2 flex-col items-end gap-8 px-8 md:flex">
    <div class="flex h-[240px] items-center gap-4">
      <div class="flex h-full flex-col justify-between py-2 text-right">
        <button
          v-for="(section, index) in sections"
          :key="section.id"
          type="button"
          class="cursor-pointer bg-transparent p-0 text-right font-bold transition-colors duration-300 hover:text-text-main focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-main/70 focus-visible:ring-offset-4 focus-visible:ring-offset-transparent"
          :class="index === activeSection ? 'text-text-main' : 'text-text-main/50'"
          @click="scrollToSection(section.id)"
        >
          {{ section.label }}
        </button>
      </div>
      <div class="relative h-full w-[3px] overflow-hidden rounded-full bg-white/20">
        <div
          class="absolute left-0 top-0 w-full bg-text-main transition-all duration-500 ease-out"
          :style="{ height: '25%', transform: `translateY(${activeSection * 100}%)` }"
        ></div>
      </div>
    </div>
  </div>
</template>
