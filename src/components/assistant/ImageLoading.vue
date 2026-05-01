<template>
  <div class="flex justify-start mb-4">
    <div class="flex items-center gap-4 p-4 bg-white/80 backdrop-blur-sm rounded-[24px] border border-teal-100 shadow-sm max-w-[320px]">
      <div class="relative flex-shrink-0 w-16 h-16 rounded-full overflow-hidden bg-white flex items-center justify-center">
        <!-- Using the GIF -->
        <img src="@/assets/loading-cat.gif" alt="AI is thinking..." class="w-full h-full object-cover" />
      </div>
      
      <div class="flex flex-col gap-1 min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-gray-800">{{ props.type === 'image' ? '正在绘制中' : '正在思考中' }}</span>
          <div class="flex gap-0.5">
            <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </div>
        </div>
        <span class="text-xs text-gray-500 truncate">{{ props.type === 'image' ? '椿天社在努力绘画中... 🎨' : '椿天社正在为您查询... 🔍' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  type?: 'text' | 'image'
}>();
</script>

<style scoped>
/* Custom animations if needed */
</style>
