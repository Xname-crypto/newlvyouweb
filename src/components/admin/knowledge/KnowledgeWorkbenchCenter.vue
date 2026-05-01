<template>
  <section class="atlas-stage" @wheel.prevent="handleWheel">
    <div v-if="dataset && visibleStack.length" class="atlas-stage__inner">
      <div class="atlas-stack-wrapper">
        <TransitionGroup name="card-stack" tag="div" class="atlas-stack" :class="[`dir-${transitionDirection}`]">
          <article 
            v-for="card in visibleStack"
            :key="card.key"
            class="atlas-card"
            :class="card.offsetClass"
          >
            <div class="atlas-card__content">
              <header class="atlas-card__header">
                <h1>{{ card.title }}</h1>
                <p class="atlas-card__subtitle">{{ card.subtitle }}</p>
                <div class="atlas-card__meta">
                  Updated {{ card.updatedLabel }} • {{ card.sourceCount }} sources • {{ card.tags.length }} tags
                </div>
              </header>

              <div class="atlas-card__definition">
                <input
                  v-if="card.isPrimary"
                  v-model="cardDefinition"
                  type="text"
                  class="atlas-card__definition-input"
                  placeholder="Write a one-line definition for this concept."
                />
                <input
                  v-else
                  :value="card.summary !== DEFAULT_SUMMARY ? card.summary : ''"
                  readonly
                  type="text"
                  class="atlas-card__definition-input atlas-card__definition-input--ghost"
                  placeholder="Write a one-line definition for this concept."
                />
              </div>

              <div v-if="card.tags.length" class="atlas-card__tags">
                <span v-for="tag in card.tags" :key="`${card.key}-${tag}`" class="atlas-card__tag">#{{ tag }}</span>
              </div>

              <section class="atlas-card__section atlas-card__section--meaning">
                <div class="atlas-card__eyebrow">PERSONAL MEANING</div>
                <p class="atlas-card__meaning">{{ card.meaning || 'Capture why this concept matters in your own words.' }}</p>
              </section>

              <section class="atlas-card__section atlas-card__section--sources">
                <div class="atlas-card__eyebrow">SOURCES</div>
                <p v-if="!card.sources.length" class="atlas-card__empty">No sources</p>
                <div v-else class="atlas-card__sources">
                  <article v-for="source in card.sources" :key="source.key" class="atlas-card__source">
                    <strong>{{ source.title }}</strong>
                    <span>{{ source.caption }}</span>
                    <p v-if="source.preview">{{ source.preview }}</p>
                  </article>
                </div>
              </section>
            </div>
          </article>
        </TransitionGroup>

        <div class="atlas-stack__index">{{ currentIndex + 1 }}/{{ totalCount }}</div>
      </div>
    </div>

    <div v-else class="atlas-stage__empty">
      <h2>No cards yet</h2>
      <p>Create a dataset card and import source material first.</p>
      <button class="atlas-stage__primary" type="button" :disabled="!knowledgeBase" @click="$emit('createDataset')">
        Create card
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { KnowledgeBaseItem } from './types'

interface SourcePresentation {
  key: string
  title: string
  caption: string
  preview: string
}

interface CardPresentation {
  key: string
  id: number
  title: string
  subtitle: string
  updatedLabel: string
  tags: string[]
  summary: string
  meaning: string
  sourceCount: number
  sources: SourcePresentation[]
}

const props = defineProps<{
  knowledgeBase: KnowledgeBaseItem | null
  dataset: KnowledgeBaseItem | null
  documents: KnowledgeBaseItem[]
  currentIndex: number
  totalCount: number
  stackCards: any[]
  transitionDirection: 'up' | 'down'
  transitionTick: number
}>()

const emit = defineEmits<{
  (e: 'createDataset'): void
  (e: 'wheelNavigate', step: number): void
}>()

const DEFAULT_SUMMARY = 'Write a one-line definition for this concept.'
const DEFAULT_MEANING = 'Capture why this concept matters in your own words.'
const cardDefinition = ref('')

let lastWheelTime = 0
let wheelAccumulator = 0

const handleWheel = (e: WheelEvent) => {
  e.preventDefault() // prevent default scrolling behavior entirely for the stage
  
  const now = Date.now()
  if (now - lastWheelTime > 400) {
    wheelAccumulator = 0
  }
  
  wheelAccumulator += e.deltaY
  
  // High threshold for trackpads, low for mouse wheels
  if (Math.abs(wheelAccumulator) > 60) {
    if (now - lastWheelTime > 600) {
      if (wheelAccumulator > 0) {
        emit('wheelNavigate', 1)
      } else {
        emit('wheelNavigate', -1)
      }
      lastWheelTime = now
      wheelAccumulator = 0
    }
  }
}

/**
 * 清理文本中的HTML标签并规范化空白字符

 * @param value 需要处理的文本
 * @returns 清理后的纯文本
 */
const normalizeText = (value?: string) =>
  String(value || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

/**
 * 截断文本到指定长度并在末尾添加省略号
 * @param value 要截断的文本
 * @param limit 最大字符数限制
 * @returns 截断后的文本
 */
const clampText = (value: string, limit: number) => {
  const plain = normalizeText(value)
  if (!plain) return ''
  return plain.length > limit ? `${plain.slice(0, limit)}...` : plain
}

/**
 * 从知识库项目中提取标签列表
 * @param item 知识库项目对象
 * @returns 提取的标签数组
 */
const extractTags = (item?: KnowledgeBaseItem | null) => {
  const metadata = item?.metadata || {}
  const raw = [
    ...(Array.isArray(metadata.tags) ? metadata.tags : []),
    ...(typeof metadata.keywords === 'string' ? metadata.keywords.split(/[,\s，、|/]+/) : []),
    metadata.category,
    metadata.business_type,
    metadata.city,
  ]

  return [...new Set(raw.map(entry => String(entry || '').trim()).filter(Boolean))].slice(0, 6)
}

/**
 * 格式化日期为 YYYY/M/D 格式
 * @param value 日期字符串或时间戳
 * @returns 格式化后的日期字符串
 */
const formatDate = (value?: string) => {
  if (!value) return '-'
  const date = new Date(value)
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

/**
 * 获取文档来源类型标签
 * @param doc 知识库文档对象
 * @returns 来源类型描述文字
 */
const sourceTypeLabel = (doc: KnowledgeBaseItem) => {
  const type = doc.metadata?.source_type
  if (type === 'upload') return 'File source'
  if (type === 'crawl') return 'Web source'
  if (type === 'legacy_import') return 'Imported source'
  return 'Text source'
}

/**
 * 构建文档元数据信息行
 * @param doc 知识库文档对象
 * @returns 格式化的元数据字符串
 */
const sourceMetaLine = (doc: KnowledgeBaseItem) => {
  const parts = [
    sourceTypeLabel(doc),
    doc.metadata?.city,
    doc.metadata?.business_type || doc.metadata?.category,
  ]
  .map(entry => String(entry || '').trim())
  .filter(Boolean)

  return parts.join(' • ')
}

/**
 * 预览文本内容并截断过长部分
 * @param value 要预览的文本
 * @returns 截断后的预览文本
 */
const previewText = (value?: string) => {
  const plain = normalizeText(value)
  if (!plain) return ''
  return plain.length > 118 ? `${plain.slice(0, 118)}...` : plain
}

/**
 * 构建项目描述文本，优先使用显式定义的字段
 * @param item 知识库项目对象
 * @param docs 关联的文档数组
 * @returns 构建的描述文本
 */
const buildDescription = (item?: KnowledgeBaseItem | null, docs: KnowledgeBaseItem[] = []) => {
  const metadata = item?.metadata || {}
  const explicit = [
    metadata.description,
    metadata.summary,
    metadata.alias,
  ]
  .map(entry => normalizeText(entry))
  .filter(Boolean)

  if (explicit.length) return explicit.join(' ')

  return docs
    .slice(0, 3)
    .map(doc => [
      doc.metadata?.description,
      doc.metadata?.summary,
      doc.content,
      doc.metadata?.title,
      doc.metadata?.name,
    ].map(entry => normalizeText(entry)).filter(Boolean).join(' '))
    .filter(Boolean)
    .join(' ')
}

/**
 * 构建个人意义说明文本
 * @param item 知识库项目对象
 * @param description 备用的描述文本
 * @returns 个人意义说明文本
 */
const buildMeaning = (item?: KnowledgeBaseItem | null, description = '') => {
  const metadata = item?.metadata || {}
  const explicitMeaning = [
    metadata.personal_meaning,
    metadata.meaning,
    metadata.insight,
  ]
  .map(entry => normalizeText(entry))
  .find(Boolean)

  return clampText(explicitMeaning || description || DEFAULT_MEANING, 170) || DEFAULT_MEANING
}

/**
 * 构建来源展示数据结构
 * @param doc 知识库文档对象
 * @param index 文档索引
 * @returns 来源展示对象
 */
const buildSourcePresentation = (doc: KnowledgeBaseItem, index: number): SourcePresentation => {
  const title = doc.metadata?.title || doc.metadata?.name || doc.name || `Source ${doc.id}`
  const caption = String(
    doc.metadata?.source_url
    || doc.metadata?.url
    || doc.metadata?.link
    || doc.metadata?.website
    || doc.metadata?.source
    || sourceMetaLine(doc),
  ).trim()

  return {
    key: `source-${doc.id}-${index}`,
    title,
    caption: caption || sourceTypeLabel(doc),
    preview: previewText(doc.metadata?.description || doc.content),
  }
}

/**
 * 构建完整的卡片展示数据结构
 * @param item 知识库项目对象
 * @param documents 关联的文档数组
 * @param keyPrefix 键名前缀
 * @returns 卡片展示对象或null
 */
const buildCardPresentation = (
  item?: KnowledgeBaseItem | null,
  documents: KnowledgeBaseItem[] = [],
  keyPrefix = 'card',
): CardPresentation | null => {
  if (!item) return null

  const metadata = item.metadata || {}
  const description = buildDescription(item, documents)
  const tags = extractTags(item)
  const sourceDocs = (documents.length ? documents : [item]).filter(Boolean).slice(0, 1)

  return {
    key: `${keyPrefix}-${item.id}`,
    id: item.id,
    title: metadata.title || item.name || metadata.name || metadata.city || 'New Card',
    subtitle: [
      metadata.city,
      metadata.business_type || metadata.category,
    ]
      .filter(Boolean)
      .join(' · ') || metadata.alias || '新卡片',
    updatedLabel: formatDate(item.updated_at),
    tags,
    summary: clampText(description || DEFAULT_SUMMARY, 132) || DEFAULT_SUMMARY,
    meaning: buildMeaning(item, description),
    sourceCount: documents.length || 0,
    sources: sourceDocs.map((doc, index) => buildSourcePresentation(doc, index)),
  }
}

/** 当前选中的卡片展示数据 */
const activeIndex = computed(() => Math.max(props.currentIndex, 0))

const visibleStack = computed(() => {
  if (!props.stackCards.length) return []
  const idx = activeIndex.value
  
  const result: (CardPresentation & { offsetClass: string, isPrimary: boolean })[] = []
  
  for (let offset = -2; offset <= 2; offset++) {
    const itemIdx = idx + offset
    if (itemIdx < 0 || itemIdx >= props.stackCards.length) continue
    
    const item = props.stackCards[itemIdx]
    const card = buildCardPresentation(item, [item], `stack-${item.id}`)
    
    if (card) {
      let offsetClass = 'is-primary'
      if (offset < 0) offsetClass = `is-past-${Math.abs(offset)}`
      if (offset > 0) offsetClass = `is-future-${offset}`
      
      result.push({
        ...card,
        isPrimary: offset === 0,
        offsetClass
      })
    }
  }
  
  return result
})

watch(visibleStack, (stack) => {
  const primary = stack.find(card => card.isPrimary)
  if (primary) {
    cardDefinition.value = primary.summary !== DEFAULT_SUMMARY ? primary.summary : ''
  }
}, { immediate: true })
</script>

<style scoped>
.atlas-stage {
  min-width: 0;
  min-height: 100vh;
  height: 100vh;
  padding: 0 12px 0 8px;
  background: #f4efe6;
  box-sizing: border-box;
  overflow-y: auto;
}

.atlas-stage__inner {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.atlas-stack-wrapper {
  position: relative;
  width: min(860px, calc(100% - 16px));
  max-width: 860px;
}

.atlas-stack {
  position: relative;
  width: 100%;
  perspective: 1200px;
  /* The stack gets its height from the .is-primary relative element */
}

/* Transitions */
.card-stack-move,
.card-stack-enter-active,
.card-stack-leave-active {
  transition: all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-stack-leave-active {
  position: absolute !important;
}

.card-stack-enter-from,
.card-stack-leave-to {
  opacity: 0 !important;
}

/* Sliding offsets for entering/leaving to match the visual stack */
.dir-down .card-stack-leave-to {
  transform: translateY(-200px) scale(0.9) !important;
}
.dir-down .card-stack-enter-from {
  transform: translateY(200px) scale(0.9) !important;
}

.dir-up .card-stack-leave-to {
  transform: translateY(200px) scale(0.9) !important;
}
.dir-up .card-stack-enter-from {
  transform: translateY(-200px) scale(0.9) !important;
}

/* Card basic styling */
.atlas-card {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%; /* forces background cards to exactly match the is-primary card height */
  box-sizing: border-box;
  border-radius: 20px;
  background: #ffffff;
  overflow: hidden;
  transform-origin: center center;
  transition: all 0.6s cubic-bezier(0.25, 1, 0.35, 1);
  will-change: transform, opacity, box-shadow;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

/* Primary determines height */
.atlas-card.is-primary {
  position: relative;
  height: auto; /* allows active card to dictate total height */
  z-index: 100;
  transform: translateY(0) scale(1);
  opacity: 1;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.08); /* Strong shadow to separate from background */
}

/* PAST CARDS (going UP relative to primary) */
.atlas-card.is-past-1 {
  z-index: 90;
  transform: translateY(-56px) scale(0.96);
  opacity: 0.7;
  pointer-events: none;
}
.atlas-card.is-past-2 {
  z-index: 80;
  transform: translateY(-108px) scale(0.92);
  opacity: 0.35;
  pointer-events: none;
}

/* FUTURE CARDS (going DOWN relative to primary) */
.atlas-card.is-future-1 {
  z-index: 90;
  transform: translateY(56px) scale(0.96);
  opacity: 0.7;
  pointer-events: none;
}
.atlas-card.is-future-2 {
  z-index: 80;
  transform: translateY(108px) scale(0.92);
  opacity: 0.35;
  pointer-events: none;
}

/* Content */
.atlas-card__content {
  padding: 40px 44px 48px;
  display: flex;
  flex-direction: column;
}

.atlas-card__header h1 {
  margin: 0;
  color: #1a1a1a;
  font-size: 42px;
  line-height: 1.15;
  font-family: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  font-weight: 500;
  letter-spacing: -0.01em;
  transition: all 0.6s cubic-bezier(0.25, 1, 0.35, 1);
}

.atlas-card__subtitle {
  margin: 10px 0 0;
  color: #d4a574;
  font-size: 17px;
  line-height: 1.4;
  font-weight: 400;
}

.atlas-card__meta {
  margin-top: 16px;
  color: #999999;
  font-size: 13px;
  line-height: 1.5;
  font-weight: 400;
}

.atlas-card__definition {
  margin-top: 28px;
}

.atlas-card__definition-input {
  width: 100%;
  height: 46px;
  padding: 0 18px;
  border: 1.5px solid #e5e5e5;
  border-radius: 12px;
  background: #fafafa;
  color: #333333;
  font-size: 14.5px;
  outline: none;
  box-sizing: border-box;
  transition: all 0.25s ease;
}

.atlas-card__definition-input:focus {
  border-color: #b8b8b8;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.04);
}

.atlas-card__definition-input::placeholder {
  color: #bbbbbb;
  font-style: italic;
}

.atlas-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 24px;
}

.atlas-card__tag {
  height: 32px;
  padding: 0 16px;
  border-radius: 16px;
  background: #2c2c3e;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
  cursor: default;
  white-space: nowrap;
}

.atlas-card__section {
  padding-top: 26px;
  border-top: 1px solid #eeeeee;
  margin-top: 30px;
}

.atlas-card__section--meaning {
  margin-top: 32px;
}

.atlas-card__section--sources {
  flex: 1;
  min-height: 0;
  margin-top: 28px;
}

.atlas-card__eyebrow {
  color: #aaaaaa;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  margin-bottom: 14px;
  text-transform: uppercase;
}

.atlas-card__meaning,
.atlas-card__empty {
  margin: 0;
  color: #666666;
  font-size: 15px;
  line-height: 1.75;
  font-weight: 400;
}

.atlas-card__sources {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
}

.atlas-card__source {
  min-width: 0;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #eeeeee;
  background: #fafafa;
}

.atlas-card__source strong {
  display: block;
  color: #222222;
  font-size: 15px;
  line-height: 1.4;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-card__source span {
  display: block;
  margin-top: 6px;
  color: #999999;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-card__source p {
  margin: 8px 0 0;
  color: #666666;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.atlas-stack__index {
  text-align: center;
  color: #aaaaaa;
  font-size: 13px;
  margin-top: 22px;
  font-weight: 500;
}

.atlas-stage__empty {
  display: grid;
  place-items: center;
  min-height: 100vh;
  text-align: center;
}

.atlas-stage__empty h2 {
  margin: 0 0 12px;
  color: #22252e;
  font-size: 36px;
}

.atlas-stage__empty p {
  margin: 0 0 24px;
  color: #8d857b;
  font-size: 16px;
}

.atlas-stage__primary {
  height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: #23253f;
  color: #fff8ef;
  cursor: pointer;
}

@media (max-width: 1100px) {
  .atlas-stage {
    min-height: auto;
    height: auto;
    padding: 20px 16px;
  }

  .atlas-stage__inner {
    padding: 24px 0;
  }

  .atlas-stack {
    width: 100%;
    max-width: 100%;
  }

  .atlas-card__content {
    padding: 28px 24px 32px;
  }
}
</style>
