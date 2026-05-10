<template>
  <div class="content-review-shell">
    <div class="content-review-shell__glow content-review-shell__glow--one" aria-hidden="true"></div>
    <div class="content-review-shell__glow content-review-shell__glow--two" aria-hidden="true"></div>
    <div class="content-review-shell__grid" aria-hidden="true"></div>

    <div class="content-review-shell__inner">
      <section class="content-review-topbar content-review-panel">
        <div class="content-review-topbar__copy">
          <p class="content-review-eyebrow">Moderation Workspace</p>
          <div class="content-review-title-row">
            <h2 class="content-review-title">内容审核</h2>
            <span class="content-review-queue-chip">{{ filteredItems.length }} 条当前队列</span>
          </div>
          <p class="content-review-subtitle">
            用更轻的视觉层级处理待审核内容，把注意力集中在判断本身，而不是传统后台表格。
          </p>
        </div>

        <div class="content-review-topbar__actions">
          <div class="content-review-stat-card">
            <span class="content-review-stat-card__label">待处理</span>
            <strong class="content-review-stat-card__value">{{ statusCounts.pending_review }}</strong>
          </div>
          <div class="content-review-stat-card">
            <span class="content-review-stat-card__label">已通过</span>
            <strong class="content-review-stat-card__value">{{ statusCounts.active }}</strong>
          </div>
          <div class="content-review-stat-card">
            <span class="content-review-stat-card__label">已拒绝</span>
            <strong class="content-review-stat-card__value">{{ statusCounts.rejected }}</strong>
          </div>
          <button
            class="content-review-refresh"
            type="button"
            title="刷新数据"
            @click="fetchPendingItems"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
            <span>刷新</span>
          </button>
        </div>
      </section>

      <div class="content-review-layout">
        <aside class="content-review-panel content-review-sidebar">
          <div class="content-review-panel__header">
            <div class="content-review-panel__icon">
              <Layers3 class="h-4 w-4" />
            </div>
            <div>
              <h3 class="content-review-panel__title">审核面板</h3>
              <p class="content-review-panel__desc">按状态与关键词聚焦当前审核批次</p>
            </div>
          </div>

          <div class="content-review-search">
            <Search class="content-review-search__icon h-4 w-4" />
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索标题、来源或正文..."
              class="content-review-search__input"
            />
          </div>

          <div class="content-review-filter-group">
            <button
              v-for="option in filterOptions"
              :key="option.value || 'all'"
              type="button"
              class="content-review-filter-card"
              :class="{ 'content-review-filter-card--active': filterStatus === option.value }"
              @click="filterStatus = option.value"
            >
              <div class="content-review-filter-card__copy">
                <span class="content-review-filter-card__title">{{ option.label }}</span>
                <span class="content-review-filter-card__hint">{{ option.description }}</span>
              </div>
              <span class="content-review-filter-card__count">
                {{ getStatusCount(option.value) }}
              </span>
            </button>
          </div>

          <div class="content-review-insight">
            <div class="content-review-insight__row">
              <span>当前页进度</span>
              <strong>{{ reviewProgress }}%</strong>
            </div>
            <div class="content-review-progress">
              <div class="content-review-progress__bar" :style="{ width: `${reviewProgress}%` }"></div>
            </div>
            <div class="content-review-insight__meta">
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <span>{{ totalItems }} 条内容</span>
            </div>
          </div>

          <div v-if="selectedItems.size > 0" class="content-review-batch">
            <div class="content-review-batch__header">
              <Inbox class="h-4 w-4" />
              <span>已选择 {{ selectedItems.size }} 项</span>
            </div>
            <div class="content-review-batch__actions">
              <button
                class="content-review-button content-review-button--primary"
                type="button"
                :disabled="processing"
                @click="batchApprove"
              >
                批量通过
              </button>
              <button
                class="content-review-button content-review-button--danger"
                type="button"
                :disabled="processing"
                @click="batchReject"
              >
                批量拒绝
              </button>
            </div>
            <button
              class="content-review-inline-link"
              type="button"
              @click="selectedItems.clear()"
            >
              清空选择
            </button>
          </div>
        </aside>

        <section class="content-review-panel content-review-queue">
          <div class="content-review-panel__header content-review-panel__header--space">
            <div>
              <h3 class="content-review-panel__title">审核队列</h3>
              <p class="content-review-panel__desc">
                点击任一内容即可在右侧工作台中完成通过、编辑或拒绝。
              </p>
            </div>
            <button
              class="content-review-inline-link"
              type="button"
              @click="toggleSelectVisible"
            >
              {{ allVisibleSelected ? '取消全选' : '全选本页' }}
            </button>
          </div>

          <div v-if="loading" class="content-review-state">
            <div class="content-review-state__icon">
              <RefreshCw class="h-5 w-5 animate-spin" />
            </div>
            <p>正在加载审核内容...</p>
          </div>

          <div v-else-if="filteredItems.length === 0" class="content-review-state">
            <div class="content-review-state__icon">
              <CheckCircle2 class="h-5 w-5" />
            </div>
            <p>当前筛选下没有可处理内容</p>
          </div>

          <div v-else class="content-review-queue__list">
            <article
              v-for="item in filteredItems"
              :key="item.id"
              class="content-review-queue-card"
              :class="{ 'content-review-queue-card--active': activeItem?.id === item.id }"
              @click="selectItem(item.id)"
            >
              <label class="content-review-check" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedItems.has(item.id)"
                  @change="toggleSelect(item.id)"
                />
                <span></span>
              </label>

              <div class="content-review-queue-card__body">
                <div class="content-review-queue-card__head">
                  <div class="content-review-queue-card__title-wrap">
                    <h4 class="content-review-queue-card__title">
                      {{ getItemTitle(item) }}
                    </h4>
                    <p class="content-review-queue-card__source">
                      {{ getItemSource(item) }}
                    </p>
                  </div>

                  <span class="content-review-status-pill" :class="getStatusPillClass(item.status)">
                    <span class="content-review-status-pill__dot" :class="getStatusDotClass(item.status)"></span>
                    {{ statusLabels[item.status] || item.status }}
                  </span>
                </div>

                <p class="content-review-queue-card__excerpt">
                  {{ getSnippet(item.content, 156) }}
                </p>

                <div class="content-review-queue-card__meta">
                  <span>
                    <Clock3 class="h-3.5 w-3.5" />
                    {{ formatDate(item.metadata?.crawled_at || item.created_at || '') }}
                  </span>
                  <span>
                    <FileText class="h-3.5 w-3.5" />
                    {{ item.metadata?.crawl_method || '人工录入' }}
                  </span>
                  <span>#{{ item.id }}</span>
                </div>
              </div>

              <ChevronRight class="content-review-queue-card__arrow h-4 w-4" />
            </article>
          </div>

          <div v-if="totalItems > pageSize" class="content-review-pagination">
            <button
              class="content-review-button content-review-button--ghost"
              type="button"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
            >
              上一页
            </button>
            <span class="content-review-pagination__label">
              第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
            </span>
            <button
              class="content-review-button content-review-button--ghost"
              type="button"
              :disabled="currentPage >= totalPages"
              @click="goToPage(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </section>

        <aside class="content-review-panel content-review-inspector">
          <template v-if="activeItem">
            <div class="content-review-inspector__hero">
              <span class="content-review-status-pill" :class="getStatusPillClass(activeItem.status)">
                <span class="content-review-status-pill__dot" :class="getStatusDotClass(activeItem.status)"></span>
                {{ statusLabels[activeItem.status] || activeItem.status }}
              </span>
              <h3 class="content-review-inspector__title">{{ getItemTitle(activeItem) }}</h3>
              <p class="content-review-inspector__source">{{ getItemSource(activeItem) }}</p>
            </div>

            <div class="content-review-preview">
              <div class="content-review-preview__head">
                <span>内容摘要</span>
                <span>{{ activeItem.content?.length || 0 }} 字符</span>
              </div>
              <p class="content-review-preview__text">{{ getSnippet(activeItem.content, 260) }}</p>
            </div>

            <div class="content-review-meta-grid">
              <div class="content-review-meta-card">
                <span>来源 URL</span>
                <p>{{ activeItem.metadata?.source || activeItem.metadata?.url || '-' }}</p>
              </div>
              <div class="content-review-meta-card">
                <span>爬取方式</span>
                <p>{{ activeItem.metadata?.crawl_method || '-' }}</p>
              </div>
              <div class="content-review-meta-card">
                <span>入库时间</span>
                <p>{{ formatDate(activeItem.created_at || '') }}</p>
              </div>
              <div class="content-review-meta-card">
                <span>Chunk 索引</span>
                <p>{{ activeItem.metadata?.chunk_index ?? '-' }}</p>
              </div>
            </div>

            <div class="content-review-editor">
              <div class="content-review-editor__head">
                <span>审核编辑</span>
                <PencilLine class="h-4 w-4" />
              </div>
              <textarea
                v-if="activeItem.status === 'pending_review'"
                v-model="editContent[activeItem.id]"
                rows="9"
                class="content-review-editor__textarea"
                placeholder="如需修正内容，可直接在这里编辑..."
              ></textarea>
              <div v-else class="content-review-editor__readonly">
                {{ activeItem.content || '-' }}
              </div>
            </div>

            <div v-if="rejectingId === activeItem.id" class="content-review-reject-box">
              <div class="content-review-reject-box__head">
                <XCircle class="h-4 w-4" />
                <span>拒绝备注</span>
              </div>
              <textarea
                v-model="rejectReason"
                rows="4"
                class="content-review-editor__textarea"
                placeholder="填写拒绝原因，后续追溯会更清晰..."
              ></textarea>
              <div class="content-review-reject-box__actions">
                <button
                  class="content-review-button content-review-button--danger"
                  type="button"
                  :disabled="processing"
                  @click="confirmReject(activeItem)"
                >
                  确认拒绝
                </button>
                <button
                  class="content-review-button content-review-button--ghost"
                  type="button"
                  @click="cancelReject"
                >
                  取消
                </button>
              </div>
            </div>

            <div
              v-else-if="activeItem.status === 'pending_review'"
              class="content-review-decision-bar"
            >
              <button
                class="content-review-button content-review-button--primary"
                type="button"
                :disabled="processing"
                @click="approveItem(activeItem)"
              >
                通过入库
              </button>
              <button
                class="content-review-button content-review-button--danger"
                type="button"
                :disabled="processing"
                @click="rejectItem(activeItem)"
              >
                拒绝并备注
              </button>
            </div>

            <div v-else class="content-review-result-note">
              <component
                :is="activeItem.status === 'active' ? CheckCircle2 : CircleSlash"
                class="h-4 w-4"
              />
              <span>
                当前内容已{{ activeItem.status === 'active' ? '通过审核并入库' : '标记为拒绝' }}
              </span>
            </div>
          </template>

          <div v-else class="content-review-state content-review-state--tall">
            <div class="content-review-state__icon">
              <Inbox class="h-5 w-5" />
            </div>
            <p>从左侧队列选择一条内容开始审核</p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { apiUrl } from '@/utils/apiBase'
import {
  CheckCircle2,
  ChevronRight,
  CircleSlash,
  Clock3,
  FileText,
  Inbox,
  Layers3,
  PencilLine,
  RefreshCw,
  Search,
  XCircle,
} from 'lucide-vue-next'

interface KnowledgeItem {
  id: number
  content: string
  metadata: Record<string, any>
  status: string
  created_at?: string
  updated_at?: string
}

const statusLabels: Record<string, string> = {
  active: '已激活',
  pending_review: '待审核',
  rejected: '已拒绝',
  archived: '已归档',
}

const filterOptions = [
  { value: 'pending_review', label: '待审核', description: '等待最终决定' },
  { value: 'active', label: '已通过', description: '已进入知识库' },
  { value: 'rejected', label: '已拒绝', description: '已被拦截' },
  { value: '', label: '全部', description: '查看当前页全部内容' },
] as const

const loading = ref(false)
const processing = ref(false)
const items = ref<KnowledgeItem[]>([])
const rejectingId = ref<number | null>(null)
const rejectReason = ref('')
const selectedItems = ref<Set<number>>(new Set())
const editContent = ref<Record<number, string>>({})
const activeItemId = ref<number | null>(null)

const filterStatus = ref('pending_review')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const totalItems = ref(0)

const API_URL = apiUrl('/api/knowledge/')

const statusCounts = computed(() =>
  items.value.reduce(
    (acc, item) => {
      if (item.status in acc) {
        acc[item.status as keyof typeof acc] += 1
      }
      return acc
    },
    {
      pending_review: 0,
      active: 0,
      rejected: 0,
      archived: 0,
    }
  )
)

const filteredItems = computed(() => {
  let result = items.value

  if (filterStatus.value) {
    result = result.filter((item) => item.status === filterStatus.value)
  }

  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    result = result.filter((item) => {
      const title = getItemTitle(item).toLowerCase()
      const source = getItemSource(item).toLowerCase()
      return title.includes(keyword) || source.includes(keyword) || item.content?.toLowerCase().includes(keyword)
    })
  }

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))

const activeItem = computed<KnowledgeItem | null>(() => {
  if (!filteredItems.value.length) return null
  return filteredItems.value.find((item) => item.id === activeItemId.value) ?? filteredItems.value[0]
})

const allVisibleSelected = computed(
  () => filteredItems.value.length > 0 && filteredItems.value.every((item) => selectedItems.value.has(item.id))
)

const reviewProgress = computed(() => {
  if (!items.value.length) return 0
  const resolved = statusCounts.value.active + statusCounts.value.rejected
  return Math.round((resolved / items.value.length) * 100)
})

const ensureEditableContent = (item: KnowledgeItem | null) => {
  if (!item) return
  if (editContent.value[item.id] === undefined) {
    editContent.value[item.id] = item.content || ''
  }
}

watch(
  filteredItems,
  (list) => {
    if (!list.length) {
      activeItemId.value = null
      rejectingId.value = null
      return
    }

    if (!list.some((item) => item.id === activeItemId.value)) {
      activeItemId.value = list[0].id
    }

    ensureEditableContent(list.find((item) => item.id === activeItemId.value) ?? list[0])
  },
  { immediate: true }
)

const fetchPendingItems = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      source: 'local',
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
    })

    const response = await fetch(`${API_URL}?${params.toString()}`)
    if (!response.ok) throw new Error('Failed to fetch')

    const data = await response.json()
    items.value = (data.results || []).filter(
      (item: KnowledgeItem) =>
        item.status === 'pending_review' || item.status === 'active' || item.status === 'rejected'
    )
    totalItems.value = data.total || items.value.length
  } catch (error) {
    console.error('Error fetching items:', error)
  } finally {
    loading.value = false
  }
}

const getStatusCount = (status: string) => {
  if (!status) return items.value.length
  return items.value.filter((item) => item.status === status).length
}

const getItemTitle = (item: KnowledgeItem) => item.metadata?.title || item.metadata?.name || '无标题内容'

const getItemSource = (item: KnowledgeItem) => item.metadata?.source || item.metadata?.url || '未知来源'

const getSnippet = (content: string, limit = 180) => {
  if (!content) return '暂无正文内容'
  const plain = content.replace(/\s+/g, ' ').trim()
  return plain.length > limit ? `${plain.slice(0, limit)}...` : plain
}

const getStatusPillClass = (status: string) =>
  ({
    pending_review: 'content-review-status-pill--pending',
    active: 'content-review-status-pill--active',
    rejected: 'content-review-status-pill--rejected',
    archived: 'content-review-status-pill--archived',
  }[status] || 'content-review-status-pill--archived')

const getStatusDotClass = (status: string) =>
  ({
    pending_review: 'content-review-status-pill__dot--pending',
    active: 'content-review-status-pill__dot--active',
    rejected: 'content-review-status-pill__dot--rejected',
    archived: 'content-review-status-pill__dot--archived',
  }[status] || 'content-review-status-pill__dot--archived')

const selectItem = (id: number) => {
  activeItemId.value = id
  ensureEditableContent(filteredItems.value.find((item) => item.id === id) ?? null)
}

const toggleSelect = (id: number) => {
  if (selectedItems.value.has(id)) {
    selectedItems.value.delete(id)
  } else {
    selectedItems.value.add(id)
  }
}

const toggleSelectVisible = () => {
  if (allVisibleSelected.value) {
    filteredItems.value.forEach((item) => selectedItems.value.delete(item.id))
    return
  }

  filteredItems.value.forEach((item) => selectedItems.value.add(item.id))
}

const approveItem = async (item: KnowledgeItem) => {
  processing.value = true
  try {
    const content = editContent.value[item.id]?.trim() || item.content
    const response = await fetch(`${API_URL}${item.id}/?source=local`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        metadata: item.metadata,
        status: 'active',
      }),
    })

    if (!response.ok) throw new Error('Failed to approve')

    item.content = content
    item.status = 'active'
    selectedItems.value.delete(item.id)
    rejectingId.value = null
    rejectReason.value = ''
  } catch (error) {
    console.error('Error approving item:', error)
    alert('操作失败，请重试')
  } finally {
    processing.value = false
  }
}

const rejectItem = (item: KnowledgeItem) => {
  activeItemId.value = item.id
  rejectingId.value = item.id
}

const cancelReject = () => {
  rejectingId.value = null
  rejectReason.value = ''
}

const confirmReject = async (item: KnowledgeItem) => {
  processing.value = true
  try {
    const response = await fetch(`${API_URL}${item.id}/?source=local`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: item.content,
        metadata: {
          ...item.metadata,
          reject_reason: rejectReason.value,
        },
        status: 'rejected',
      }),
    })

    if (!response.ok) throw new Error('Failed to reject')

    item.status = 'rejected'
    selectedItems.value.delete(item.id)
    cancelReject()
  } catch (error) {
    console.error('Error rejecting item:', error)
    alert('操作失败，请重试')
  } finally {
    processing.value = false
  }
}

const batchApprove = async () => {
  processing.value = true
  try {
    const ids = Array.from(selectedItems.value)
    await Promise.all(
      ids.map(async (id) => {
        const item = items.value.find((entry) => entry.id === id)
        if (!item) return

        const content = editContent.value[id]?.trim() || item.content
        await fetch(`${API_URL}${id}/?source=local`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content,
            metadata: item.metadata,
            status: 'active',
          }),
        })

        item.content = content
        item.status = 'active'
      })
    )

    selectedItems.value.clear()
    cancelReject()
  } catch (error) {
    console.error('Error in batch approve:', error)
    alert('批量操作部分失败，请刷新后重试')
  } finally {
    processing.value = false
  }
}

const batchReject = async () => {
  if (!confirm(`确定要拒绝选中的 ${selectedItems.value.size} 项内容吗？`)) return

  processing.value = true
  try {
    const ids = Array.from(selectedItems.value)
    await Promise.all(
      ids.map(async (id) => {
        const item = items.value.find((entry) => entry.id === id)
        if (!item) return

        await fetch(`${API_URL}${id}/?source=local`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: item.content,
            metadata: { ...item.metadata, batch_rejected: true },
            status: 'rejected',
          }),
        })

        item.status = 'rejected'
      })
    )

    selectedItems.value.clear()
    cancelReject()
  } catch (error) {
    console.error('Error in batch reject:', error)
    alert('批量操作部分失败，请刷新后重试')
  } finally {
    processing.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

const goToPage = async (page: number) => {
  currentPage.value = page
  await fetchPendingItems()
}

onMounted(() => {
  fetchPendingItems()
})
</script>

<style scoped>
.content-review-shell {
  --review-surface: rgba(255, 255, 255, 0.84);
  --review-border: rgba(15, 23, 42, 0.07);
  --review-shadow: 0 18px 50px rgba(148, 163, 184, 0.18);
  --review-shadow-soft: 0 10px 30px rgba(148, 163, 184, 0.12);
  --review-text: #182230;
  --review-text-muted: #6b7280;
  --review-text-soft: #94a3b8;
  position: relative;
  min-height: calc(100vh - 3rem);
  overflow: hidden;
  border-radius: 2rem;
  padding: 1.5rem;
  background:
    linear-gradient(180deg, #f5f6f8 0%, #edf1f4 44%, #f7f7f8 100%);
}

.content-review-shell__inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.content-review-shell__glow,
.content-review-shell__grid {
  position: absolute;
  pointer-events: none;
}

.content-review-shell__glow {
  border-radius: 999px;
  filter: blur(48px);
  opacity: 0.42;
}

.content-review-shell__glow--one {
  top: -8%;
  right: 12%;
  width: 18rem;
  height: 18rem;
  background: radial-gradient(circle, rgba(254, 226, 226, 0.45) 0%, rgba(254, 226, 226, 0) 72%);
}

.content-review-shell__glow--two {
  bottom: -5%;
  left: 8%;
  width: 20rem;
  height: 20rem;
  background: radial-gradient(circle, rgba(219, 234, 254, 0.4) 0%, rgba(219, 234, 254, 0) 72%);
}

.content-review-shell__grid {
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.46) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.42) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.12;
}

.content-review-panel {
  border: 1px solid var(--review-border);
  border-radius: 1.8rem;
  background: var(--review-surface);
  box-shadow: var(--review-shadow);
  backdrop-filter: blur(20px);
}

.content-review-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.4rem 1.55rem;
}

.content-review-topbar__copy {
  max-width: 38rem;
}

.content-review-eyebrow {
  margin: 0 0 0.45rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--review-text-soft);
}

.content-review-title-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.content-review-title {
  margin: 0;
  font-size: 1.7rem;
  line-height: 1.1;
  font-weight: 700;
  color: var(--review-text);
}

.content-review-queue-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0 0.85rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(15, 23, 42, 0.06);
  font-size: 0.8rem;
  color: var(--review-text-muted);
}

.content-review-subtitle {
  margin: 0.7rem 0 0;
  max-width: 34rem;
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--review-text-muted);
}

.content-review-topbar__actions {
  display: flex;
  align-items: stretch;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.content-review-stat-card {
  min-width: 7rem;
  padding: 0.9rem 1rem;
  border-radius: 1.3rem;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(15, 23, 42, 0.05);
  box-shadow: var(--review-shadow-soft);
}

.content-review-stat-card__label {
  display: block;
  font-size: 0.74rem;
  color: var(--review-text-soft);
}

.content-review-stat-card__value {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.2rem;
  color: var(--review-text);
}

.content-review-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
  min-height: 3.3rem;
  border: 1px solid rgba(15, 23, 42, 0.07);
  border-radius: 1.2rem;
  background: rgba(255, 255, 255, 0.94);
  color: var(--review-text);
  box-shadow: var(--review-shadow-soft);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.content-review-refresh:hover {
  transform: translateY(-1px);
  border-color: rgba(15, 23, 42, 0.12);
  box-shadow: 0 12px 26px rgba(148, 163, 184, 0.16);
}

.content-review-layout {
  display: grid;
  grid-template-columns: 17rem minmax(0, 1fr) 23rem;
  gap: 1rem;
}

.content-review-sidebar,
.content-review-queue,
.content-review-inspector {
  padding: 1.2rem;
}

.content-review-panel__header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.content-review-panel__header--space {
  justify-content: space-between;
  align-items: flex-start;
}

.content-review-panel__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.95rem;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(15, 23, 42, 0.06);
  color: var(--review-text);
}

.content-review-panel__title {
  margin: 0;
  font-size: 0.98rem;
  color: var(--review-text);
}

.content-review-panel__desc {
  margin: 0.22rem 0 0;
  font-size: 0.8rem;
  line-height: 1.6;
  color: var(--review-text-muted);
}

.content-review-search {
  position: relative;
  margin-bottom: 0.95rem;
}

.content-review-search__icon {
  position: absolute;
  left: 0.95rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--review-text-soft);
}

.content-review-search__input {
  width: 100%;
  min-height: 3rem;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 1rem;
  padding: 0 1rem 0 2.6rem;
  background: rgba(255, 255, 255, 0.86);
  color: var(--review-text);
  outline: none;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.content-review-search__input:focus {
  border-color: rgba(15, 23, 42, 0.14);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.65);
}

.content-review-filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.content-review-filter-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(15, 23, 42, 0.05);
  border-radius: 1.15rem;
  background: rgba(255, 255, 255, 0.68);
  text-align: left;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease;
}

.content-review-filter-card:hover,
.content-review-filter-card--active {
  transform: translateY(-1px);
  border-color: rgba(15, 23, 42, 0.1);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--review-shadow-soft);
}

.content-review-filter-card__copy {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
}

.content-review-filter-card__title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--review-text);
}

.content-review-filter-card__hint {
  font-size: 0.74rem;
  color: var(--review-text-muted);
}

.content-review-filter-card__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.55rem;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--review-text);
}

.content-review-insight {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.content-review-insight__row,
.content-review-insight__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.content-review-insight__row {
  font-size: 0.88rem;
  color: var(--review-text);
}

.content-review-insight__meta {
  margin-top: 0.65rem;
  font-size: 0.76rem;
  color: var(--review-text-muted);
}

.content-review-progress {
  margin-top: 0.75rem;
  height: 0.45rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.16);
  overflow: hidden;
}

.content-review-progress__bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #111827 0%, #475569 100%);
}

.content-review-batch {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 1.3rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.84) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.content-review-batch__header {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--review-text);
}

.content-review-batch__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
  margin-top: 0.85rem;
}

.content-review-inline-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2rem;
  padding: 0;
  border: none;
  background: transparent;
  font-size: 0.8rem;
  color: var(--review-text-muted);
  transition: color 180ms ease;
}

.content-review-inline-link:hover {
  color: var(--review-text);
}

.content-review-queue {
  display: flex;
  flex-direction: column;
  min-height: 40rem;
}

.content-review-queue__list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  flex: 1;
}

.content-review-queue-card {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 1rem;
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(15, 23, 42, 0.05);
  box-shadow: 0 8px 24px rgba(148, 163, 184, 0.08);
  cursor: pointer;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.content-review-queue-card:hover,
.content-review-queue-card--active {
  transform: translateY(-2px);
  border-color: rgba(15, 23, 42, 0.12);
  box-shadow: 0 16px 34px rgba(148, 163, 184, 0.14);
}

.content-review-check {
  position: relative;
  display: inline-flex;
  margin-top: 0.2rem;
}

.content-review-check input {
  position: absolute;
  inset: 0;
  opacity: 0;
}

.content-review-check span {
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: rgba(255, 255, 255, 0.95);
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.content-review-check input:checked + span {
  background: #111827;
  border-color: #111827;
  box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.9);
}

.content-review-queue-card__body {
  min-width: 0;
  flex: 1;
}

.content-review-queue-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.content-review-queue-card__title-wrap {
  min-width: 0;
}

.content-review-queue-card__title {
  margin: 0;
  font-size: 0.95rem;
  color: var(--review-text);
}

.content-review-queue-card__source {
  margin: 0.25rem 0 0;
  font-size: 0.76rem;
  color: var(--review-text-muted);
}

.content-review-queue-card__excerpt {
  margin: 0.75rem 0 0;
  font-size: 0.86rem;
  line-height: 1.75;
  color: #475569;
}

.content-review-queue-card__meta {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex-wrap: wrap;
  margin-top: 0.8rem;
  font-size: 0.74rem;
  color: var(--review-text-soft);
}

.content-review-queue-card__meta span {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
}

.content-review-queue-card__arrow {
  margin-top: 0.1rem;
  color: var(--review-text-soft);
}

.content-review-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 1.8rem;
  padding: 0 0.78rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.74rem;
  font-weight: 600;
  white-space: nowrap;
}

.content-review-status-pill__dot {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
}

.content-review-status-pill--pending {
  background: rgba(254, 243, 199, 0.75);
  color: #9a6700;
  border-color: rgba(251, 191, 36, 0.22);
}

.content-review-status-pill--active {
  background: rgba(220, 252, 231, 0.72);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.18);
}

.content-review-status-pill--rejected {
  background: rgba(254, 226, 226, 0.78);
  color: #b91c1c;
  border-color: rgba(248, 113, 113, 0.18);
}

.content-review-status-pill--archived {
  background: rgba(226, 232, 240, 0.82);
  color: #475569;
  border-color: rgba(148, 163, 184, 0.18);
}

.content-review-status-pill__dot--pending {
  background: #f59e0b;
}

.content-review-status-pill__dot--active {
  background: #22c55e;
}

.content-review-status-pill__dot--rejected {
  background: #ef4444;
}

.content-review-status-pill__dot--archived {
  background: #94a3b8;
}

.content-review-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.content-review-pagination__label {
  font-size: 0.82rem;
  color: var(--review-text-muted);
}

.content-review-inspector {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.content-review-inspector__hero {
  padding: 0.2rem 0 0.1rem;
}

.content-review-inspector__title {
  margin: 0.9rem 0 0;
  font-size: 1.18rem;
  line-height: 1.45;
  color: var(--review-text);
}

.content-review-inspector__source {
  margin: 0.42rem 0 0;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--review-text-muted);
}

.content-review-preview {
  padding: 1rem;
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.content-review-preview__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.74rem;
  color: var(--review-text-soft);
}

.content-review-preview__text {
  margin: 0.7rem 0 0;
  font-size: 0.88rem;
  line-height: 1.8;
  color: #475569;
}

.content-review-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.content-review-meta-card {
  padding: 0.9rem 1rem;
  border-radius: 1.15rem;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.content-review-meta-card span {
  display: block;
  font-size: 0.72rem;
  color: var(--review-text-soft);
}

.content-review-meta-card p {
  margin: 0.45rem 0 0;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--review-text);
  overflow-wrap: anywhere;
}

.content-review-editor {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.content-review-editor__head,
.content-review-reject-box__head,
.content-review-result-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  font-size: 0.82rem;
  color: var(--review-text-muted);
}

.content-review-editor__textarea,
.content-review-editor__readonly {
  width: 100%;
  min-height: 14rem;
  padding: 1rem 1rem 1.05rem;
  border: 1px solid rgba(15, 23, 42, 0.07);
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.92);
  font-size: 0.88rem;
  line-height: 1.8;
  color: var(--review-text);
  resize: vertical;
  outline: none;
}

.content-review-editor__textarea:focus {
  border-color: rgba(15, 23, 42, 0.15);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.72);
}

.content-review-editor__readonly {
  overflow-y: auto;
  white-space: pre-wrap;
}

.content-review-reject-box {
  padding: 1rem;
  border-radius: 1.35rem;
  background: rgba(255, 245, 245, 0.84);
  border: 1px solid rgba(248, 113, 113, 0.18);
}

.content-review-reject-box__actions,
.content-review-decision-bar {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.content-review-result-note {
  padding: 0.95rem 1rem;
  border-radius: 1.2rem;
  justify-content: flex-start;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.content-review-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.9rem;
  padding: 0 1rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.85rem;
  font-weight: 600;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease;
}

.content-review-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.content-review-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.content-review-button--primary {
  background: #111827;
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.16);
}

.content-review-button--primary:hover:not(:disabled) {
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.22);
}

.content-review-button--danger {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(248, 113, 113, 0.2);
  color: #b91c1c;
}

.content-review-button--danger:hover:not(:disabled) {
  background: rgba(254, 242, 242, 0.92);
}

.content-review-button--ghost {
  background: rgba(255, 255, 255, 0.82);
  border-color: rgba(15, 23, 42, 0.08);
  color: var(--review-text);
}

.content-review-state {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  min-height: 18rem;
  border-radius: 1.45rem;
  background: rgba(255, 255, 255, 0.66);
  border: 1px dashed rgba(148, 163, 184, 0.26);
  color: var(--review-text-muted);
  text-align: center;
}

.content-review-state--tall {
  min-height: 32rem;
}

.content-review-state__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.06);
  color: var(--review-text);
}

@media (max-width: 1440px) {
  .content-review-layout {
    grid-template-columns: 15rem minmax(0, 1fr) 21rem;
  }
}

@media (max-width: 1180px) {
  .content-review-layout {
    grid-template-columns: 15rem minmax(0, 1fr);
  }

  .content-review-inspector {
    grid-column: 1 / -1;
  }
}

@media (max-width: 860px) {
  .content-review-shell {
    padding: 1rem;
    border-radius: 1.5rem;
  }

  .content-review-topbar {
    flex-direction: column;
  }

  .content-review-layout {
    grid-template-columns: 1fr;
  }

  .content-review-meta-grid,
  .content-review-batch__actions,
  .content-review-reject-box__actions,
  .content-review-decision-bar {
    grid-template-columns: 1fr;
  }

  .content-review-pagination {
    flex-direction: column;
  }
}
</style>
