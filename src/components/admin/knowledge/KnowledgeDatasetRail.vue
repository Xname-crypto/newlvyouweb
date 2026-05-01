<template>
  <aside class="atlas-library">
    <div class="atlas-library__head">
      <div class="atlas-library__meta">
        <div class="atlas-library__eyebrow">LIBRARY</div>
        <h3>{{ knowledgeBaseName }}</h3>
        <p>{{ datasets.length }} cards</p>
      </div>
      <div class="atlas-library__pill">{{ currentNumber }}</div>
    </div>

    <div class="atlas-library__nav">
      <button type="button" :disabled="!canGoPrev" @click="$emit('navigateDataset', -1)">↑</button>
      <button type="button" :disabled="!canGoNext" @click="$emit('navigateDataset', 1)">↓</button>
    </div>

    <div class="atlas-library__list">
      <button
        v-for="item in datasets"
        :key="item.id"
        class="atlas-library__item"
        :class="{ 'is-active': activeDataset?.id === item.id }"
        type="button"
        @click="$emit('selectDataset', item)"
      >
        <strong>{{ item.metadata?.title || item.name || item.metadata?.name || `Card ${item.id}` }}</strong>
        <span>{{ item.metadata?.city || item.metadata?.business_type || item.metadata?.category || 'Untitled' }}</span>
      </button>
    </div>

    <div v-if="footerMode === 'dataset'" class="atlas-library__footer">
      <button type="button" @click="$emit('editDataset', activeDataset)" :disabled="!activeDataset">Edit card</button>
      <button type="button" @click="$emit('deleteDataset', activeDataset)" :disabled="!activeDataset">Delete</button>
      <button type="button" @click="$emit('openTesting')" :disabled="!activeDataset">+ Add card</button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { KnowledgeBaseItem } from './types'

const props = defineProps<{
  knowledgeBase: KnowledgeBaseItem | null
  datasets: KnowledgeBaseItem[]
  activeDataset: KnowledgeBaseItem | null
  canGoPrev: boolean
  canGoNext: boolean
  footerMode?: 'dataset' | 'document'
}>()

defineEmits<{
  (e: 'navigateDataset', step: number): void
  (e: 'selectDataset', item: KnowledgeBaseItem): void
  (e: 'editDataset', item: KnowledgeBaseItem | null): void
  (e: 'deleteDataset', item: KnowledgeBaseItem | null): void
  (e: 'openTesting'): void
}>()

const currentNumber = computed(() => {
  const index = props.datasets.findIndex(item => item.id === props.activeDataset?.id)
  return index >= 0 ? String(index + 1).padStart(2, '0') : '00'
})

const knowledgeBaseName = computed(() => props.knowledgeBase?.metadata?.category || props.knowledgeBase?.name || 'Unsorted')
</script>

<style scoped>
.atlas-library {
  width: 214px;
  flex-shrink: 0;
  padding: 14px 12px 16px;
  border-left: 1px solid rgba(28, 31, 44, 0.08);
  background: #fffcf8;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.atlas-library__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.atlas-library__eyebrow {
  color: #a09587;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.28em;
}

.atlas-library__meta h3 {
  margin: 6px 0 4px;
  color: #1d2230;
  font-size: 16px;
  line-height: 1.2;
}

.atlas-library__meta p {
  margin: 0;
  color: #92897f;
  font-size: 12px;
}

.atlas-library__pill {
  min-width: 34px;
  height: 34px;
  padding: 0 8px;
  border-radius: 12px;
  background: #c8f0cc;
  color: #667182;
  display: grid;
  place-items: center;
  font-size: 14px;
  font-weight: 700;
}

.atlas-library__nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.atlas-library__nav button {
  height: 40px;
  border: none;
  border-radius: 12px;
  background: #262843;
  color: #fff8ef;
  font-size: 22px;
  cursor: pointer;
}

.atlas-library__nav button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.atlas-library__list {
  flex: 1;
  margin-top: 12px;
  overflow-y: auto;
}

.atlas-library__item {
  width: 100%;
  padding: 14px 10px;
  border: none;
  border-top: 1px solid rgba(29, 31, 43, 0.08);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.atlas-library__item strong {
  display: block;
  color: #222631;
  font-size: 14px;
  line-height: 1.35;
  font-weight: 600;
}

.atlas-library__item span {
  display: block;
  margin-top: 4px;
  color: #988f83;
  font-size: 11px;
}

.atlas-library__item.is-active {
  margin: 10px 0;
  border-top-color: transparent;
  border-radius: 20px;
  background: #272944;
}

.atlas-library__item.is-active strong,
.atlas-library__item.is-active span {
  color: #fff8ef;
}

.atlas-library__footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.atlas-library__footer button {
  height: 38px;
  border: none;
  border-radius: 12px;
  background: #272944;
  color: #fff8ef;
  font-size: 14px;
  cursor: pointer;
}

.atlas-library__footer button:disabled,
.atlas-library__footer button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .atlas-library {
    width: 100%;
    border-left: none;
    border-top: 1px solid rgba(29, 29, 39, 0.08);
    overflow: visible;
  }

  .atlas-library__list {
    max-height: 260px;
  }
}
</style>
