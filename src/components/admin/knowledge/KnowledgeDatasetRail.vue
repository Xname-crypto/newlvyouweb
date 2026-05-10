<template>
  <aside class="atlas-library">
    <div class="atlas-library__head">
      <div class="atlas-library__meta">
        <div class="atlas-library__eyebrow">资料库</div>
        <h3>{{ knowledgeBaseName }}</h3>
        <p>{{ datasets.length }} 张卡片</p>
      </div>
    </div>

    <div class="atlas-library__nav">
      <button type="button" :disabled="!canGoPrev" aria-label="上一张卡片" @click="$emit('navigateDataset', -1)">
        <ChevronUp aria-hidden="true" />
      </button>
      <button type="button" :disabled="!canGoNext" aria-label="下一张卡片" @click="$emit('navigateDataset', 1)">
        <ChevronDown aria-hidden="true" />
      </button>
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
        <span>{{ item.metadata?.city || item.metadata?.business_type || item.metadata?.category || '未分类' }}</span>
      </button>
    </div>

    <div class="atlas-library__footer">
      <button class="atlas-library__footer-primary" type="button" @click="$emit('appendDocument')" :disabled="!canManageDocuments">
        <Plus aria-hidden="true" />
        <span>添加卡片</span>
      </button>
      <button type="button" @click="$emit('importLegacy')" :disabled="!canManageDocuments">
        <Upload aria-hidden="true" />
        <span>导入资料</span>
      </button>
      <button type="button" @click="$emit('openTesting')" :disabled="!knowledgeBase">
        <Bot aria-hidden="true" />
        <span>问答测试</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Bot, ChevronDown, ChevronUp, Plus, Upload } from 'lucide-vue-next'
import type { KnowledgeBaseItem } from './types'

const props = defineProps<{
  knowledgeBase: KnowledgeBaseItem | null
  datasets: KnowledgeBaseItem[]
  activeDataset: KnowledgeBaseItem | null
  canGoPrev: boolean
  canGoNext: boolean
  canManageDocuments?: boolean
  footerMode?: 'dataset' | 'document'
}>()

defineEmits<{
  (e: 'navigateDataset', step: number): void
  (e: 'selectDataset', item: KnowledgeBaseItem): void
  (e: 'editDataset', item: KnowledgeBaseItem | null): void
  (e: 'deleteDataset', item: KnowledgeBaseItem | null): void
  (e: 'appendDocument'): void
  (e: 'importLegacy'): void
  (e: 'openTesting'): void
}>()

const knowledgeBaseName = computed(() => props.knowledgeBase?.metadata?.category || props.knowledgeBase?.name || '未分类')
</script>

<style scoped>
.atlas-library {
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 18px 12px 12px;
  border-left: 1px solid #dbe5f0;
  background: linear-gradient(180deg, #f8fafc 0%, #eef4fa 100%);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.atlas-library__head {
  min-height: 64px;
  padding: 0 2px;
}

.atlas-library__eyebrow {
  color: #64748b;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 800;
  letter-spacing: 0;
}

.atlas-library__meta h3 {
  margin: 6px 0 4px;
  color: #0f172a;
  font-size: 17px;
  line-height: 1.25;
  font-weight: 800;
}

.atlas-library__meta p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.35;
}

.atlas-library__nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.atlas-library__nav button {
  height: 38px;
  border: 1px solid #dbe5f0;
  border-radius: 10px;
  background: #ffffff;
  color: #0f1b33;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 160ms ease, background 160ms ease, color 160ms ease, transform 160ms ease;
}

.atlas-library__nav button:hover:not(:disabled) {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  transform: translateY(-1px);
}

.atlas-library__nav svg {
  width: 19px;
  height: 19px;
  stroke-width: 2.4;
}

.atlas-library__nav button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.atlas-library__list {
  flex: 1;
  margin-top: 12px;
  padding-right: 2px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}

.atlas-library__item {
  width: 100%;
  padding: 12px 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.atlas-library__item + .atlas-library__item {
  margin-top: 4px;
}

.atlas-library__item:hover {
  border-color: #dbe5f0;
  background: rgba(255, 255, 255, 0.72);
}

.atlas-library__item strong {
  display: block;
  color: #0f172a;
  font-size: 13.5px;
  line-height: 1.35;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-library__item span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-library__item.is-active {
  border-color: #bfdbfe;
  background: #ffffff;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.1);
  transform: translateX(-1px);
}

.atlas-library__item.is-active strong {
  color: #1d4ed8;
}

.atlas-library__footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #dbe5f0;
}

.atlas-library__footer button {
  height: 42px;
  min-width: 0;
  padding: 0 12px;
  border: 1px solid #dbe5f0;
  border-radius: 10px;
  background: #ffffff;
  color: #0f172a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 160ms ease, background 160ms ease, color 160ms ease, transform 160ms ease;
}

.atlas-library__footer button:hover:not(:disabled) {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  transform: translateY(-1px);
}

.atlas-library__footer-primary {
  border-color: #1d4ed8 !important;
  background: #1d4ed8 !important;
  color: #ffffff !important;
}

.atlas-library__footer-primary:hover:not(:disabled) {
  background: #1e40af !important;
  border-color: #1e40af !important;
  color: #ffffff !important;
}

.atlas-library__footer svg {
  width: 16px;
  height: 16px;
  stroke-width: 2.3;
}

.atlas-library__footer button:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .atlas-library {
    width: 100%;
    border-left: none;
    border-top: 1px solid #dbe5f0;
    overflow: visible;
  }

  .atlas-library__list {
    max-height: 260px;
  }
}
</style>
