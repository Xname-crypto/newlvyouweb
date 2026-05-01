<script setup lang="ts">
import { Instagram, Twitter } from 'lucide-vue-next';
</script>

<template>
  <div class="fixed left-0 top-1/2 -translate-y-1/2 flex flex-col items-center gap-8 z-40 px-8 hidden md:flex">
    <div class="writing-vertical-rl text-text-main font-bold text-lg tracking-wide">关注我们</div>
    <div class="flex flex-col gap-4">
      <a href="#" class="text-text-main hover:text-accent transition-colors">
        <Instagram :size="24" />
      </a>
      <a href="#" class="text-text-main hover:text-accent transition-colors">
        <Twitter :size="24" />
      </a>
    </div>
  </div>
</template>

<style scoped>
.writing-vertical-rl {
  writing-mode: vertical-rl;
}
</style>
