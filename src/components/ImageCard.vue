<script setup lang="ts">
defineProps<{
  src: string;
  alt: string;
}>();
</script>

<template>
  <div class="relative w-full h-[400px] md:h-[500px] lg:h-[720px] overflow-hidden rounded-lg shadow-2xl group">
    <img 
      :src="src" 
      :alt="alt"
      class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
    />
    <div class="absolute inset-0 bg-gradient-to-t from-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
  </div>
</template>
