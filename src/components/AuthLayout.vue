<script setup lang="ts">
import { ArrowLeft, X } from 'lucide-vue-next';
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const videoReady = ref(false);
const videoErrored = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
let bufferTimer: number | undefined;

const props = defineProps<{
  videoSrc?: string;
  posterSrc?: string;
  showBack?: boolean;
  contentOffsetClass?: string;
}>();

const posterFromVideo = computed(() => {
  const src = props.videoSrc || '';
  if (!src) return '';

  const hashIndex = src.indexOf('#');
  const beforeHash = hashIndex >= 0 ? src.slice(0, hashIndex) : src;
  const hash = hashIndex >= 0 ? src.slice(hashIndex) : '';
  const queryIndex = beforeHash.indexOf('?');
  const path = queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash;
  const query = queryIndex >= 0 ? beforeHash.slice(queryIndex) : '';

  if (!path.toLowerCase().endsWith('.mp4')) return '';

  return `${path.slice(0, -4)}.poster.jpg${query}${hash}`;
});

const videoPoster = computed(() => {
  return props.posterSrc || posterFromVideo.value;
});

defineEmits<{
  (e: 'back'): void
}>();

const goBack = () => {
  router.push('/');
};

const clearBufferTimer = () => {
  if (bufferTimer) {
    window.clearTimeout(bufferTimer);
    bufferTimer = undefined;
  }
};

const resetVideoState = () => {
  clearBufferTimer();
  videoReady.value = false;
  videoErrored.value = false;
};

const bufferedAhead = (video: HTMLVideoElement) => {
  try {
    const current = video.currentTime || 0;
    for (let i = 0; i < video.buffered.length; i += 1) {
      if (video.buffered.start(i) <= current && video.buffered.end(i) >= current) {
        return video.buffered.end(i) - current;
      }
    }
  } catch (_e) {
    return 0;
  }

  return 0;
};

const handleVideoReady = () => {
  const video = videoRef.value;
  if (!video || videoErrored.value) return;

  videoErrored.value = false;
  video.play().catch(() => {
    // Muted autoplay can still be interrupted by the browser; the poster remains underneath.
  });

  const duration = Number.isFinite(video.duration) ? video.duration : 0;
  const requiredBuffer = duration > 0 ? Math.min(2.5, Math.max(1.2, duration * 0.12)) : 1.5;

  if (video.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA || bufferedAhead(video) >= requiredBuffer) {
    clearBufferTimer();
    videoReady.value = true;
    return;
  }

  clearBufferTimer();
  bufferTimer = window.setTimeout(handleVideoReady, 180);
};

const handleVideoError = () => {
  videoErrored.value = true;
  videoReady.value = false;
};

watch(() => props.videoSrc, resetVideoState, { immediate: true });
onBeforeUnmount(clearBufferTimer);
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

        <div
          v-if="videoPoster"
          class="auth-video-poster absolute inset-0 h-full w-full transition-opacity duration-300"
          :class="videoReady ? 'opacity-0' : 'opacity-100'"
          aria-hidden="true"
        >
          <img
            :src="videoPoster"
            alt=""
            class="h-full w-full object-cover"
          />
        </div>

        <video
          v-if="props.videoSrc && !videoErrored"
          ref="videoRef"
          class="auth-layout-video absolute inset-0 h-full w-full object-cover transition-opacity duration-300"
          :class="videoReady ? 'opacity-100' : 'opacity-0'"
          autoplay
          muted 
          loop 
          preload="auto"
          playsinline
          :poster="videoPoster || undefined"
          @loadeddata="handleVideoReady"
          @canplay="handleVideoReady"
          @canplaythrough="handleVideoReady"
          @playing="handleVideoReady"
          @progress="handleVideoReady"
          @error="handleVideoError"
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
  z-index: 1;
  will-change: opacity, transform;
  transform: translateZ(0);
}

.auth-video-poster {
  z-index: 0;
}
</style>
