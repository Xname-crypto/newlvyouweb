<script setup lang="ts">
import { ArrowLeft, X } from 'lucide-vue-next';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const shouldLoadVideo = ref(false);

const props = defineProps<{
  videoSrc?: string;
  showBack?: boolean;
  contentOffsetClass?: string;
}>();

defineEmits<{
  (e: 'back'): void
}>();

const goBack = () => {
  router.push('/');
};

onMounted(() => {
  window.requestAnimationFrame(() => {
    shouldLoadVideo.value = true;
  });
});
</script>

<template>
  <div class="min-h-screen w-full bg-[#f0f2f5] flex flex-col items-center justify-center gap-3 p-4">
    <div v-if="$slots.notice" class="pointer-events-none fixed inset-x-0 top-6 z-[9999] flex justify-center px-4">
      <slot name="notice"></slot>
    </div>

    <!-- Card Container -->
    <div class="w-full max-w-4xl bg-white rounded-[2rem] shadow-xl overflow-hidden flex flex-col md:flex-row h-auto md:h-[600px]">
      
      <!-- Left Side: Video/Image -->
      <div class="hidden md:flex md:w-1/2 bg-[#f8f7f5] relative overflow-hidden items-center justify-center">
        <!-- Back Button (Top Left of Video Section) -->
        <button 
          v-if="props.showBack"
          @click="$emit('back')"
          class="absolute top-6 left-6 z-20 p-2 text-white/70 hover:text-white bg-black/20 hover:bg-black/40 backdrop-blur-sm rounded-full transition-all group"
          title="返回上一步"
        >
          <ArrowLeft class="w-6 h-6 transition-transform group-hover:-translate-x-1" />
        </button>

        <video 
          v-if="props.videoSrc && shouldLoadVideo"
          class="auth-layout-video absolute inset-0 h-full w-full bg-[#f8f7f5] object-cover"
          autoplay 
          muted 
          loop 
          preload="metadata"
          playsinline
        >
          <source :src="props.videoSrc" type="video/mp4">
        </video>
      </div>

      <!-- Right Side: Form -->
      <div class="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center bg-white relative">
        <!-- Close Button -->
        <button 
          @click="goBack"
          class="absolute top-6 right-6 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-all"
        >
          <X class="w-6 h-6" />
        </button>

        <div class="max-w-2xl mx-auto w-full" :class="props.contentOffsetClass">
          <div class="mb-8 text-center md:text-left">
            <div class="mb-2 text-2xl font-bold text-gray-800">
              <slot name="title">Welcome</slot>
            </div>
            <p class="text-gray-500 text-sm">
              <slot name="subtitle"></slot>
            </p>
          </div>
          
          <slot></slot>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.auth-layout-video {
  animation: auth-video-in 180ms ease-out both;
}

@keyframes auth-video-in {
  from {
    opacity: 0.01;
  }

  to {
    opacity: 1;
  }
}
</style>
