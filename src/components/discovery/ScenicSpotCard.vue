<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Heart, Star } from 'lucide-vue-next'
import type { ScenicSearchCardData } from './types'

const props = withDefaults(
  defineProps<{
    item: ScenicSearchCardData
    saved?: boolean
  }>(),
  {
    saved: false,
  },
)

const emit = defineEmits<{
  (e: 'action', item: ScenicSearchCardData): void
  (e: 'select', item: ScenicSearchCardData): void
}>()

const fallbackImage =
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1600&auto=format&fit=crop'

const imageSrc = ref(props.item.image || fallbackImage)

watch(
  () => props.item.image,
  (value) => {
    imageSrc.value = value || fallbackImage
  },
)

const starFillPercentages = computed(() => {
  const rating = Math.max(0, Math.min(5, Number(props.item.rating || 0)))
  return Array.from({ length: 5 }, (_, index) => {
    const fill = (rating - index) * 100
    return Math.max(0, Math.min(100, fill))
  })
})

const onImageError = () => {
  imageSrc.value = fallbackImage
}
</script>

<template>
  <article
    class="self-start overflow-hidden rounded-[16px] border border-[#edf0f3] bg-white shadow-[0_10px_26px_rgba(15,23,42,0.04)] transition hover:-translate-y-1 hover:shadow-[0_16px_32px_rgba(15,23,42,0.08)] focus:outline-none focus:ring-2 focus:ring-[#2bc5c4]/30"
    role="link"
    tabindex="0"
    @click="emit('select', item)"
    @keydown.enter.prevent="emit('select', item)"
    @keydown.space.prevent="emit('select', item)"
  >
    <div class="relative overflow-hidden rounded-t-[16px] bg-[#eef3f5]">
      <img
        :src="imageSrc"
        :alt="item.title"
        class="h-[196px] w-full object-cover"
        @error="onImageError"
      />

      <span
        v-if="item.badgeText"
        class="absolute right-3 top-3 rounded-full bg-[#ff9cb4] px-2.5 py-1 text-[10px] font-semibold leading-none text-white"
      >
        {{ item.badgeText }}
      </span>
    </div>

    <div class="px-4 pb-5 pt-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h3 class="truncate text-[15px] font-semibold leading-6 text-[#243251]">{{ item.title }}</h3>
          <p class="mt-1 truncate text-[11px] text-[#b1b7c2]">{{ item.subtitle }}</p>
        </div>

        <button
          type="button"
          class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition"
          :class="saved ? 'text-[#ff648c]' : 'text-[#c5cad4] hover:text-[#9098a8]'"
          @click.stop="emit('action', item)"
        >
          <Heart class="h-4 w-4" :fill="saved ? 'currentColor' : 'none'" />
        </button>
      </div>

      <div class="mt-4 flex items-end justify-between gap-4">
        <div>
          <p class="text-[10px] font-medium text-[#c1c6ce]">起价</p>
          <p class="mt-1 text-[34px] font-bold leading-none tracking-[-0.04em] text-[#243251]">{{ item.displayPrice }}</p>
          <p class="mt-1 text-[10px] text-[#bcc2cc]">*价格会有浮动</p>
        </div>

        <div class="pb-1 text-right">
          <div class="flex justify-end gap-0.5">
            <div
              v-for="(fill, index) in starFillPercentages"
              :key="index"
              class="relative h-3.5 w-3.5"
            >
              <Star class="absolute inset-0 h-3.5 w-3.5 text-[#dfe3ea]" fill="none" />
              <div class="absolute inset-y-0 left-0 overflow-hidden" :style="{ width: `${fill}%` }">
                <Star class="h-3.5 w-3.5 text-[#ffb023]" fill="currentColor" />
              </div>
            </div>
          </div>
          <p class="mt-1 text-[10px] text-[#98a0ae]">{{ item.reviewSummary }}</p>
        </div>
      </div>

      <div class="mt-5 space-y-2 border-t border-[#f0f2f5] pt-4 text-[11px] text-[#9fa6b4]">
        <div class="flex items-center gap-2">
          <span class="h-1.5 w-1.5 rounded-full bg-[#55cdd2]"></span>
          <span>{{ item.visitDuration || item.featureLabels[0] }}</span>
        </div>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div class="flex items-center gap-2">
            <span class="h-1.5 w-1.5 rounded-full bg-[#55cdd2]"></span>
            <span>{{ item.bookingRequired || item.featureLabels[1] }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="h-1.5 w-1.5 rounded-full bg-[#55cdd2]"></span>
            <span>{{ item.openingHours || item.featureLabels[2] }}</span>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>
