<script setup lang="ts">
import { computed } from 'vue'
import type {
  ScenicOption,
  ScenicPriceBounds,
  ScenicRatingOption,
  ScenicSearchFiltersState,
} from './types'

const props = defineProps<{
  filters: ScenicSearchFiltersState
  priceBounds: ScenicPriceBounds
  popularTagOptions: string[]
  durationOptions: ScenicOption[]
  ratingOptions: ScenicRatingOption[]
}>()

const emit = defineEmits<{
  (e: 'update:filters', value: ScenicSearchFiltersState): void
}>()

const priceRange = computed(() => Math.max(1, props.priceBounds.max - props.priceBounds.min))

const minPercent = computed(
  () => ((props.filters.minPrice - props.priceBounds.min) / priceRange.value) * 100,
)

const maxPercent = computed(
  () => ((props.filters.maxPrice - props.priceBounds.min) / priceRange.value) * 100,
)

const patchFilters = (patch: Partial<ScenicSearchFiltersState>) => {
  emit('update:filters', { ...props.filters, ...patch })
}

const clearPopularTags = () => {
  patchFilters({ popularTags: [] })
}

const togglePopularTag = (tag: string) => {
  const next = props.filters.popularTags.includes(tag)
    ? props.filters.popularTags.filter((item) => item !== tag)
    : [...props.filters.popularTags, tag]

  patchFilters({ popularTags: next })
}

const handleMinPriceInput = (event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  patchFilters({ minPrice: Math.min(value, props.filters.maxPrice) })
}

const handleMaxPriceInput = (event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  patchFilters({ maxPrice: Math.max(value, props.filters.minPrice) })
}

const updateMinPriceField = (event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  patchFilters({
    minPrice: Math.max(props.priceBounds.min, Math.min(value || props.priceBounds.min, props.filters.maxPrice)),
  })
}

const updateMaxPriceField = (event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  patchFilters({
    maxPrice: Math.min(props.priceBounds.max, Math.max(value || props.priceBounds.max, props.filters.minPrice)),
  })
}

const setDuration = (duration: string) => {
  patchFilters({ duration })
}

const setMinRating = (minRating: number) => {
  patchFilters({ minRating })
}
</script>

<template>
  <aside class="rounded-[16px] border border-[#edf0f3] bg-white px-5 py-6 shadow-[0_10px_24px_rgba(15,23,42,0.03)]">
    <div class="rounded-[14px] bg-[#f7fbfc] px-4 py-3 text-[12px] leading-5 text-[#7f8798]">
      当前结果页仅保留真实可生效的筛选：标签、价格、时长、评分。
      出发日期会保留到后续预订流程，但不会影响当前景点结果。
    </div>

    <div class="mt-6">
      <h3 class="text-[12px] font-semibold text-[#8891a4]">热门标签</h3>
      <div class="mt-3 space-y-2.5">
        <label class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]">
          <input
            class="h-3.5 w-3.5 rounded-full border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="checkbox"
            :checked="filters.popularTags.length === 0"
            @change="clearPopularTags"
          />
          <span>不限</span>
        </label>
        <label
          v-for="tag in popularTagOptions"
          :key="tag"
          class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]"
        >
          <input
            class="h-3.5 w-3.5 rounded-full border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="checkbox"
            :checked="filters.popularTags.includes(tag)"
            @change="togglePopularTag(tag)"
          />
          <span>{{ tag }}</span>
        </label>
      </div>
    </div>

    <div class="mt-6">
      <h3 class="text-[12px] font-semibold text-[#8891a4]">价格区间</h3>
      <div class="mt-4">
        <div class="relative h-7">
          <div class="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-[#dbe4e8]"></div>
          <div
            class="absolute top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-[#2bc5c4]"
            :style="{ left: `${minPercent}%`, right: `${100 - maxPercent}%` }"
          ></div>
          <input
            class="range-slider absolute left-0 top-0 h-7 w-full"
            type="range"
            :min="priceBounds.min"
            :max="priceBounds.max"
            :value="filters.minPrice"
            @input="handleMinPriceInput"
          />
          <input
            class="range-slider absolute left-0 top-0 h-7 w-full"
            type="range"
            :min="priceBounds.min"
            :max="priceBounds.max"
            :value="filters.maxPrice"
            @input="handleMaxPriceInput"
          />
        </div>

        <div class="mt-3 grid grid-cols-2 gap-3">
          <input
            class="h-9 rounded-[8px] border border-[#eceef2] px-3 text-[12px] text-[#8f96a8] outline-none focus:border-[#2bc5c4]"
            type="number"
            :value="filters.minPrice"
            @change="updateMinPriceField"
          />
          <input
            class="h-9 rounded-[8px] border border-[#eceef2] px-3 text-[12px] text-[#8f96a8] outline-none focus:border-[#2bc5c4]"
            type="number"
            :value="filters.maxPrice"
            @change="updateMaxPriceField"
          />
        </div>
      </div>
    </div>

    <div class="mt-6">
      <h3 class="text-[12px] font-semibold text-[#8891a4]">行程时长</h3>
      <div class="mt-3 space-y-2.5">
        <label class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]">
          <input
            class="h-3.5 w-3.5 border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="radio"
            name="duration"
            :checked="filters.duration === ''"
            @change="setDuration('')"
          />
          <span>不限</span>
        </label>
        <label
          v-for="option in durationOptions"
          :key="option.key"
          class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]"
        >
          <input
            class="h-3.5 w-3.5 border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="radio"
            name="duration"
            :checked="filters.duration === option.key"
            @change="setDuration(option.key)"
          />
          <span>{{ option.label }}</span>
        </label>
      </div>
    </div>

    <div class="mt-6">
      <h3 class="text-[12px] font-semibold text-[#8891a4]">行程评分</h3>
      <div class="mt-3 space-y-2.5">
        <label class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]">
          <input
            class="h-3.5 w-3.5 border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="radio"
            name="rating"
            :checked="filters.minRating === 0"
            @change="setMinRating(0)"
          />
          <span>不限</span>
        </label>
        <label
          v-for="option in ratingOptions"
          :key="option.value"
          class="flex cursor-pointer items-center gap-2.5 text-[12px] text-[#8f96a8]"
        >
          <input
            class="h-3.5 w-3.5 border-[#d9dde4] text-[#2bc5c4] focus:ring-[#2bc5c4]"
            type="radio"
            name="rating"
            :checked="filters.minRating === option.value"
            @change="setMinRating(option.value)"
          />
          <span class="flex items-center gap-0.5 text-[#ffb023]">
            <span v-for="index in 5" :key="index">{{ index <= option.stars ? '★' : '☆' }}</span>
          </span>
        </label>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.range-slider {
  appearance: none;
  background: transparent;
  pointer-events: none;
}

.range-slider::-webkit-slider-runnable-track {
  height: 2px;
  background: transparent;
}

.range-slider::-webkit-slider-thumb {
  appearance: none;
  margin-top: -5px;
  height: 12px;
  width: 12px;
  border-radius: 999px;
  border: 2px solid #2bc5c4;
  background: #ffffff;
  pointer-events: auto;
  cursor: pointer;
}

.range-slider::-moz-range-track {
  height: 2px;
  background: transparent;
}

.range-slider::-moz-range-thumb {
  height: 12px;
  width: 12px;
  border-radius: 999px;
  border: 2px solid #2bc5c4;
  background: #ffffff;
  pointer-events: auto;
  cursor: pointer;
}
</style>
