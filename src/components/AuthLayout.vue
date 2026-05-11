<script setup lang="ts">
import { ArrowLeft, X } from 'lucide-vue-next';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const shouldLoadVideo = ref(false);
const videoReady = ref(false);
const videoErrored = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
let loadTimer: number | undefined;
let bufferTimer: number | undefined;
let stallTimer: number | undefined;

const props = defineProps<{
  videoSrc?: string;
  posterSrc?: string;
  showBack?: boolean;
  contentOffsetClass?: string;
}>();

const videoPoster = computed(() => {
  return props.posterSrc || '';
});

defineEmits<{
  (e: 'back'): void
}>();

const goBack = () => {
  router.push('/');
};

const clearTimers = () => {
  if (loadTimer) window.clearTimeout(loadTimer);
  if (bufferTimer) window.clearTimeout(bufferTimer);
  if (stallTimer) window.clearTimeout(stallTimer);
  loadTimer = undefined;
  bufferTimer = undefined;
  stallTimer = undefined;
};

const scheduleVideoLoad = () => {
  clearTimers();
  shouldLoadVideo.value = false;
  videoReady.value = false;
  videoErrored.value = false;

  if (!props.videoSrc) return;

  loadTimer = window.setTimeout(() => {
    shouldLoadVideo.value = true;
  }, 650);
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

const waitForBufferAndPlay = () => {
  const video = videoRef.value;
  if (!video || videoErrored.value) return;

  const duration = Number.isFinite(video.duration) ? video.duration : 0;
  const requiredBuffer = duration > 0 ? Math.min(4, Math.max(1.5, duration * 0.2)) : 2.5;

  if (video.readyState >= 4 || bufferedAhead(video) >= requiredBuffer) {
    video.play().catch(() => {
      videoReady.value = false;
    });
    return;
  }

  bufferTimer = window.setTimeout(waitForBufferAndPlay, 240);
};

const handleVideoCanPlay = () => {
  waitForBufferAndPlay();
};

const handleVideoPlaying = () => {
  if (stallTimer) window.clearTimeout(stallTimer);
  videoErrored.value = false;
  videoReady.value = true;
};

const handleVideoWaiting = () => {
  if (stallTimer) window.clearTimeout(stallTimer);
  stallTimer = window.setTimeout(() => {
    videoReady.value = false;
  }, 420);
};

const handleVideoError = () => {
  videoErrored.value = true;
  videoReady.value = false;
};

onMounted(scheduleVideoLoad);
watch(() => props.videoSrc, scheduleVideoLoad);
onBeforeUnmount(clearTimers);
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
          class="auth-video-fallback absolute inset-0 h-full w-full transition-opacity duration-500"
          :class="videoReady ? 'opacity-0' : 'opacity-100'"
          aria-hidden="true"
        >
          <img
            v-if="videoPoster"
            :src="videoPoster"
            alt=""
            class="h-full w-full object-cover"
          />
          <div v-else class="flex h-full w-full items-center justify-center bg-[#111827]">
            <img src="/favicon-chuntianshe.png" alt="" class="h-28 w-28 object-contain opacity-90" />
          </div>
        </div>

        <video
          v-if="props.videoSrc && shouldLoadVideo && !videoErrored"
          ref="videoRef"
          class="auth-layout-video absolute inset-0 h-full w-full object-cover transition-opacity duration-500"
          :class="videoReady ? 'opacity-100' : 'opacity-0'"
          muted 
          loop 
          preload="auto"
          playsinline
          :poster="videoPoster || undefined"
          @canplay="handleVideoCanPlay"
          @canplaythrough="handleVideoCanPlay"
          @playing="handleVideoPlaying"
          @waiting="handleVideoWaiting"
          @stalled="handleVideoWaiting"
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
  animation: auth-video-in 180ms ease-out both;
  will-change: opacity;
  transform: translateZ(0);
}

.auth-video-fallback {
  z-index: 0;
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
