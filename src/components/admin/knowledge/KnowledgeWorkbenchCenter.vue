<template>
  <section class="atlas-stage" @wheel.prevent="handleWheel">
    <div v-if="activeCard" class="atlas-stage__inner">
      <div class="atlas-card-shell" :class="[`dir-${transitionDirection}`, `tick-${transitionTick}`]">
        <article :key="`${activeCard.key}-${transitionTick}`" class="atlas-card">
          <div class="atlas-card__loadbar" aria-hidden="true">
            <div class="atlas-loadbar__track">
              <span class="atlas-loadbar__fill"></span>
              <span class="atlas-loadbar__glow"></span>
            </div>
            <div class="atlas-loadbar__steps">
              <span
                v-for="(step, index) in loadSteps"
                :key="step"
                class="atlas-loadbar__step"
                :style="{ '--step-index': index }"
              >
                {{ step }}
              </span>
            </div>
          </div>

          <div class="atlas-card__content">
            <header class="atlas-card__header">
              <h1>{{ activeCard.title }}</h1>
              <p class="atlas-card__subtitle">{{ activeCard.subtitle }}</p>
              <div class="atlas-card__meta">
                Updated {{ activeCard.updatedLabel }} / {{ activeCard.sourceCount }} sources / {{ activeCard.tags.length }} tags
              </div>
            </header>

            <div class="atlas-card__definition">
              <input
                v-model="cardDefinition"
                type="text"
                class="atlas-card__definition-input"
                placeholder="Write a one-line definition for this concept."
              />
            </div>

            <div v-if="activeCard.tags.length" class="atlas-card__tags">
              <span v-for="tag in activeCard.tags" :key="`${activeCard.key}-${tag}`" class="atlas-card__tag">#{{ tag }}</span>
            </div>

            <section class="atlas-card__section atlas-card__section--meaning">
              <div class="atlas-card__eyebrow">PERSONAL MEANING</div>
              <p class="atlas-card__meaning">{{ activeCard.meaning || DEFAULT_MEANING }}</p>
            </section>

            <section class="atlas-card__section atlas-card__section--sources">
              <div class="atlas-card__eyebrow">SOURCES</div>
              <p v-if="!activeCard.sources.length" class="atlas-card__empty">No sources</p>
              <div v-else class="atlas-card__sources">
                <article v-for="source in activeCard.sources" :key="source.key" class="atlas-card__source">
                  <strong>{{ source.title }}</strong>
                  <span>{{ source.caption }}</span>
                  <p v-if="source.preview">{{ source.preview }}</p>
                </article>
              </div>
            </section>
          </div>
        </article>

        <div class="atlas-card__index">{{ currentIndex + 1 }}/{{ totalCount }}</div>
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
  stackCards: KnowledgeBaseItem[]
  transitionDirection: 'up' | 'down'
  transitionTick: number
}>()

const emit = defineEmits<{
  (e: 'createDataset'): void
  (e: 'wheelNavigate', step: number): void
}>()

const DEFAULT_SUMMARY = 'Write a one-line definition for this concept.'
const DEFAULT_MEANING = 'Capture why this concept matters in your own words.'
const loadSteps = ['Read dataset', 'Parse tags', 'Summarize sources', 'Render card']
const cardDefinition = ref('')

let lastWheelTime = 0
let wheelAccumulator = 0

const normalizeText = (value?: string) =>
  String(value || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

const clampText = (value: string, limit: number) => {
  const plain = normalizeText(value)
  if (!plain) return ''
  return plain.length > limit ? `${plain.slice(0, limit)}...` : plain
}

const formatDate = (value?: string) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

const extractTags = (item?: KnowledgeBaseItem | null) => {
  const metadata = item?.metadata || {}
  const raw = [
    ...(Array.isArray(metadata.tags) ? metadata.tags : []),
    ...(typeof metadata.keywords === 'string' ? metadata.keywords.split(/[,\s/]+/) : []),
    metadata.category,
    metadata.business_type,
    metadata.city,
  ]

  return [...new Set(raw.map(entry => String(entry || '').trim()).filter(Boolean))].slice(0, 6)
}

const sourceTypeLabel = (doc: KnowledgeBaseItem) => {
  const type = doc.metadata?.source_type
  if (type === 'upload') return 'File source'
  if (type === 'crawl') return 'Web source'
  if (type === 'legacy_import') return 'Imported source'
  return 'Text source'
}

const sourceMetaLine = (doc: KnowledgeBaseItem) => {
  const parts = [
    sourceTypeLabel(doc),
    doc.metadata?.city,
    doc.metadata?.business_type || doc.metadata?.category,
  ]
    .map(entry => String(entry || '').trim())
    .filter(Boolean)

  return parts.join(' / ')
}

const previewText = (value?: string) => {
  const plain = normalizeText(value)
  if (!plain) return ''
  return plain.length > 118 ? `${plain.slice(0, 118)}...` : plain
}

const buildDescription = (item?: KnowledgeBaseItem | null, docs: KnowledgeBaseItem[] = []) => {
  const metadata = item?.metadata || {}
  const explicit = [metadata.description, metadata.summary, metadata.alias]
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

const buildMeaning = (item?: KnowledgeBaseItem | null, description = '') => {
  const metadata = item?.metadata || {}
  const explicitMeaning = [metadata.personal_meaning, metadata.meaning, metadata.insight]
    .map(entry => normalizeText(entry))
    .find(Boolean)

  return clampText(explicitMeaning || description || DEFAULT_MEANING, 170) || DEFAULT_MEANING
}

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
    subtitle: [metadata.city, metadata.business_type || metadata.category].filter(Boolean).join(' / ') || metadata.alias || 'New card',
    updatedLabel: formatDate(item.updated_at),
    tags,
    summary: clampText(description || DEFAULT_SUMMARY, 132) || DEFAULT_SUMMARY,
    meaning: buildMeaning(item, description),
    sourceCount: documents.length || 0,
    sources: sourceDocs.map((doc, index) => buildSourcePresentation(doc, index)),
  }
}

const activeCard = computed(() => buildCardPresentation(props.dataset, props.documents, 'active'))

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  const now = Date.now()
  if (now - lastWheelTime > 260) wheelAccumulator = 0

  wheelAccumulator += e.deltaY

  if (Math.abs(wheelAccumulator) > 42 && now - lastWheelTime > 360) {
    emit('wheelNavigate', wheelAccumulator > 0 ? 1 : -1)
    lastWheelTime = now
    wheelAccumulator = 0
  }
}

watch(activeCard, (card) => {
  if (card) {
    cardDefinition.value = card.summary !== DEFAULT_SUMMARY ? card.summary : ''
  }
}, { immediate: true })
</script>

<style scoped>
.atlas-stage {
  min-width: 0;
  min-height: 100%;
  height: 100%;
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f3f6fa 100%);
  box-sizing: border-box;
  overflow: hidden;
}

.atlas-stage__inner {
  height: 100%;
  min-height: 720px;
  display: grid;
  place-items: center;
  padding: 48px 32px 70px;
  box-sizing: border-box;
}

.atlas-card-shell {
  --atlas-card-height: 560px;
  position: relative;
  width: min(880px, 100%);
  max-width: 880px;
  height: calc(var(--atlas-card-height) + 54px);
}

.atlas-card {
  position: relative;
  width: 100%;
  height: var(--atlas-card-height);
  min-height: 0;
  border: 1px solid rgba(219, 229, 240, 0.96);
  border-radius: 12px;
  background: #ffffff;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: 0 24px 56px rgba(15, 23, 42, 0.12);
  animation: atlas-card-enter 880ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.dir-up .atlas-card {
  --enter-y: -18px;
}

.dir-down .atlas-card {
  --enter-y: 18px;
}

.atlas-card__loadbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3;
  padding: 16px 20px 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0) 100%);
}

.atlas-loadbar__track {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: #edf2f7;
  overflow: hidden;
}

.atlas-loadbar__fill,
.atlas-loadbar__glow {
  position: absolute;
  inset: 0 auto 0 0;
  width: 100%;
  border-radius: inherit;
  transform-origin: left center;
}

.atlas-loadbar__fill {
  background: linear-gradient(90deg, #0f1b33 0%, #2563eb 54%, #7dd3fc 100%);
  animation: atlas-load-fill 1320ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.atlas-loadbar__glow {
  width: 26%;
  background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.8) 48%, rgba(255,255,255,0) 100%);
  mix-blend-mode: screen;
  animation: atlas-load-glow 1320ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.atlas-loadbar__steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.atlas-loadbar__step {
  position: relative;
  min-width: 0;
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 800;
  letter-spacing: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  animation: atlas-step-explain 1320ms ease both;
  animation-delay: calc(var(--step-index) * 170ms);
}

.atlas-loadbar__step::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 6px;
  border-radius: 999px;
  background: currentColor;
  vertical-align: 1px;
}

.atlas-card__content {
  height: 100%;
  min-height: 0;
  padding: 70px 48px 44px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  opacity: 0;
  transform: translateY(16px);
  animation: atlas-content-in 720ms cubic-bezier(0.16, 1, 0.3, 1) 520ms both;
}

.atlas-card__header h1 {
  margin: 0;
  color: #0f172a;
  font-size: 42px;
  line-height: 1.08;
  font-family: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  font-weight: 500;
  letter-spacing: 0;
}

.atlas-card__subtitle {
  margin: 10px 0 0;
  color: #2563eb;
  font-size: 16px;
  line-height: 1.4;
  font-weight: 500;
}

.atlas-card__meta {
  margin-top: 12px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.atlas-card__definition {
  margin-top: 22px;
}

.atlas-card__definition-input {
  width: 100%;
  height: 46px;
  padding: 0 18px;
  border: 1px solid #d7e2ee;
  border-radius: 10px;
  background: #f8fafc;
  color: #273449;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.atlas-card__definition-input::placeholder {
  color: #64748b;
}

.atlas-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.atlas-card__tag {
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  background: #eef2ff;
  color: #1d4ed8;
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.atlas-card__section {
  padding-top: 22px;
  border-top: 1px solid #dbe5f0;
  margin-top: 26px;
}

.atlas-card__eyebrow {
  color: #64748b;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.18em;
  margin-bottom: 14px;
  text-transform: uppercase;
}

.atlas-card__meaning,
.atlas-card__empty {
  margin: 0;
  color: #334155;
  font-size: 14px;
  line-height: 1.75;
}

.atlas-card__sources {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.atlas-card__source {
  min-width: 0;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid #dbe5f0;
  background: #f8fafc;
}

.atlas-card__source strong {
  display: block;
  color: #172033;
  font-size: 14px;
  line-height: 1.4;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-card__source span {
  display: block;
  margin-top: 4px;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.atlas-card__source p {
  margin: 8px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.atlas-card__index {
  position: absolute;
  top: calc(var(--atlas-card-height) + 18px);
  left: 0;
  right: 0;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 700;
}

.atlas-stage__empty {
  display: grid;
  place-items: center;
  min-height: 100%;
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

@keyframes atlas-card-enter {
  0% {
    opacity: 0;
    filter: blur(12px);
    transform: translateY(var(--enter-y, 18px)) scale(0.985);
  }
  100% {
    opacity: 1;
    filter: blur(0);
    transform: translateY(0) scale(1);
  }
}

@keyframes atlas-load-fill {
  0% { transform: scaleX(0); }
  24% { transform: scaleX(0.32); }
  48% { transform: scaleX(0.58); }
  72% { transform: scaleX(0.82); }
  100% { transform: scaleX(1); }
}

@keyframes atlas-load-glow {
  0% {
    opacity: 0;
    transform: translateX(-120%);
  }
  12% { opacity: 1; }
  100% {
    opacity: 0;
    transform: translateX(410%);
  }
}

@keyframes atlas-step-explain {
  0%, 18% {
    color: #94a3b8;
    opacity: 0.38;
    transform: translateY(2px);
  }
  36%, 72% {
    color: #0f1b33;
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    color: #2563eb;
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes atlas-content-in {
  0% {
    opacity: 0;
    transform: translateY(18px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .atlas-stage {
    min-height: auto;
    height: auto;
    padding: 0;
    overflow: visible;
  }

  .atlas-stage__inner {
    min-height: 620px;
    padding: 56px 16px 64px;
  }

  .atlas-card-shell {
    --atlas-card-height: 500px;
    width: 100%;
    height: calc(var(--atlas-card-height) + 72px);
  }

  .atlas-card__content {
    height: 100%;
    min-height: 0;
    padding: 70px 24px 32px;
  }

  .atlas-card__header h1 {
    font-size: 34px;
  }

  .atlas-loadbar__steps {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
