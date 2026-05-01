<script setup lang="ts">
defineProps<{
  activeSection: number;
}>();

const sections = [
  { id: 'start', label: '开始' },
  { id: '01', label: '01' },
  { id: '02', label: '02' },
  { id: '03', label: '03' },
];
</script>

<template>
  <div class="fixed right-0 top-1/2 -translate-y-1/2 flex flex-col items-end gap-8 z-40 px-8 hidden md:flex">
    <div class="flex items-center gap-4 h-[240px]">
      <div class="flex flex-col justify-between h-full text-right py-2">
        <span 
          v-for="(section, index) in sections" 
          :key="section.id"
          class="font-bold transition-colors duration-300"
          :class="index === activeSection ? 'text-text-main' : 'text-text-main/50'"
        >
          {{ section.label }}
        </span>
      </div>
      <div class="w-[3px] h-full bg-white/20 relative rounded-full overflow-hidden">
        <div 
          class="absolute top-0 left-0 w-full bg-text-main transition-all duration-500 ease-out"
          :style="{ height: '25%', transform: `translateY(${activeSection * 100}%)` }"
        ></div>
      </div>
    </div>
  </div>
</template>
