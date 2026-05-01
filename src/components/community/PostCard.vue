<script setup lang="ts">
import { computed, ref } from 'vue';
import { Heart, Play } from 'lucide-vue-next';

export interface Post {
  id: number;
  title: string;
  image: string;
  type?: 'image' | 'video';
  user: {
    name: string;
    avatar: string;
  };
  likes: number;
  isLiked?: boolean;
}

defineProps<{
  post: Post;
}>();

const mediaRatio = ref(3 / 4);

const updateMediaRatio = (width: number, height: number) => {
  if (!width || !height) return;

  const ratio = width / height;
  mediaRatio.value = Math.min(1.35, Math.max(0.62, ratio));
};

const handleImageLoad = (event: Event) => {
  const target = event.target as HTMLImageElement;
  updateMediaRatio(target.naturalWidth, target.naturalHeight);
};

const handleVideoMetadata = (event: Event) => {
  const target = event.target as HTMLVideoElement;
  updateMediaRatio(target.videoWidth, target.videoHeight);
};

const mediaStyle = computed(() => ({
  aspectRatio: String(mediaRatio.value),
}));

// Helper to check if url is video
const isVideo = (url: string) => {
    return url?.match(/\.(mp4|webm|ogg)$/i);
};
</script>

<template>
  <div class="community-post-card group cursor-pointer overflow-hidden rounded-[1.15rem] border border-gray-100 bg-white shadow-[0_10px_30px_-22px_rgba(15,23,42,0.45)] transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5 hover:border-gray-200 hover:shadow-[0_18px_38px_-24px_rgba(15,23,42,0.32)]">
    <!-- Image/Video -->
    <div class="relative overflow-hidden bg-gray-100" :style="mediaStyle">
      <template v-if="post.type === 'video' || isVideo(post.image)">
          <video
            :src="post.image"
            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            muted
            loop
            playsinline
            preload="metadata"
            onmouseover="this.play()"
            onmouseout="this.pause();this.currentTime=0;"
            @loadedmetadata="handleVideoMetadata"
          ></video>
          <!-- Play Icon Overlay -->
          <div class="absolute right-2 top-2 rounded-full bg-black/20 p-1 backdrop-blur-sm">
              <Play class="w-3 h-3 text-white fill-white" />
          </div>
      </template>
      <img
        v-else
        :src="post.image"
        :alt="post.title"
        class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
        loading="lazy"
        @load="handleImageLoad"
      />
      <!-- Gradient overlay for better text visibility if we put text on image, but here we follow Xiaohongshu style -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300 pointer-events-none"></div>
    </div>

    <!-- Content -->
    <div class="p-3.5">
      <!-- Title -->
      <h3 class="mb-3 text-sm font-medium leading-snug text-gray-900 line-clamp-2 group-hover:text-gray-700">
        {{ post.title }}
      </h3>

      <!-- Footer -->
      <div class="flex items-center justify-between text-xs text-gray-500">
        <!-- User -->
        <div class="flex items-center space-x-1.5 flex-1 min-w-0">
          <img
            :src="post.user.avatar"
            :alt="post.user.name"
            class="w-5 h-5 rounded-full object-cover border border-gray-100 flex-shrink-0"
          />
          <span class="truncate hover:text-gray-900 transition-colors">{{ post.user.name }}</span>
        </div>

        <!-- Likes -->
        <div class="flex items-center space-x-1 flex-shrink-0 group/like">
          <Heart
            class="w-3.5 h-3.5 transition-colors"
            :class="post.isLiked ? 'fill-red-500 text-red-500' : 'text-gray-400 group-hover/like:text-gray-600'"
          />
          <span>{{ post.likes }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
