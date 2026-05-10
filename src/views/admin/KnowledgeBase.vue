<template>
  <div class="kb-page-shell">
    <div class="kb-page-main">
      <div v-if="workspaceLoading && !knowledgeBases.length" class="kb-blank-state">
        <h2>知识工作台加载中</h2>
        <p>正在整理知识库、资料集和资料来源。</p>
      </div>

      <div v-else-if="!selectedKnowledgeBase" class="kb-blank-state">
        <h2>先创建知识库</h2>
        <p>知识库是容器，资料集和原始资料都需要先归属到某个知识库下。</p>
        <button class="kb-page-qa-btn" type="button" @click="openCreateKnowledgeBase">创建第一个知识库</button>
      </div>

      <div v-else class="kb-workbench">
        <section class="kb-admin-head">
          <div>
            <p class="kb-admin-head__crumb">仪表盘 / 知识库管理</p>
            <h1>知识库管理</h1>
            <span>管理景点数据知识卡片</span>
          </div>
          <div class="kb-admin-head__tools">
            <label class="kb-admin-head__search">
              <span>搜索资料</span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索景点、城市、标签..."
              />
            </label>
            <button class="kb-admin-head__button" type="button" @click="openImportModal">导入旧资料</button>
          </div>
        </section>

        <header class="kb-workbench__topbar">
          <div class="kb-workbench__title-block">
            <span>Knowledge Base</span>
            <h1>{{ selectedKnowledgeBase?.name || selectedKnowledgeBase?.metadata?.name || '知识库管理' }}</h1>
          </div>

          <div class="kb-workbench__controls">
            <label class="kb-workbench__select-wrap">
              <span>知识库</span>
              <select class="kb-page-select" :value="selectedKnowledgeBase?.id || ''" @change="handleKnowledgeBaseChange">
                <option v-for="base in knowledgeBases" :key="base.id" :value="base.id">
                  {{ base.name || base.metadata?.name || `KB ${base.id}` }}
                </option>
              </select>
            </label>

            <label class="kb-workbench__select-wrap">
              <span>资料集</span>
              <select class="kb-page-select" :value="selectedDataset?.id || ''" :disabled="!filteredDatasets.length" @change="handleDatasetChange">
                <option value="">全部资料</option>
                <option v-for="item in filteredDatasets" :key="item.id" :value="item.id">
                  {{ item.name || item.metadata?.name || `Dataset ${item.id}` }}
                </option>
              </select>
            </label>
          </div>

          <div class="kb-workbench__actions">
            <button class="kb-page-action" type="button" @click="openCreateKnowledgeBase">新建知识库</button>
            <button class="kb-page-action" type="button" @click="openCreateDataset">新建资料集</button>
            <button class="kb-page-action" type="button" :disabled="!selectedDataset" @click="openAppendModal">添加资料</button>
            <button class="kb-page-qa-btn" type="button" :disabled="!selectedDataset" @click="openImportModal">导入旧资料</button>
            <button class="kb-page-action" type="button" @click="goToQATest">问答测试</button>
          </div>
        </header>

        <section class="kb-workbench__stats">
          <article>
            <strong>{{ workspaceStats.dataset_count || datasets.length }}</strong>
            <span>资料集</span>
          </article>
          <article>
            <strong>{{ workspaceStats.document_count || knowledgeBaseDocuments.length }}</strong>
            <span>资料</span>
          </article>
          <article>
            <strong>{{ filteredCards.length }}</strong>
            <span>当前筛选</span>
          </article>
          <article>
            <strong>{{ workspaceStats.pending_count || 0 }}</strong>
            <span>待处理</span>
          </article>
        </section>

        <section class="kb-filter-panel">
          <div class="kb-filter-panel__search">
            <label class="kb-workbench__select-wrap">
              <span>æœç´¢</span>
              <input
                v-model="searchQuery"
                class="kb-modal__input"
                type="text"
                placeholder="æœç´¢èµ„æ–™æ ‡é¢˜ã€åŸŽå¸‚ã€�æ ‡ç­¾"
              />
            </label>
            <button v-if="isCompactWorkbench" class="kb-page-action" type="button" @click="filterSidebarOpen = true">æ›´å¤šç­›é€‰</button>
          </div>

          <div class="kb-filter-row">
            <span class="kb-filter-row__label">åˆ†ç±»</span>
            <div class="kb-filter-row__chips">
              <button class="kb-filter-chip" :class="{ 'is-active': !activeCategory }" type="button" @click="activeCategory = ''">å…¨éƒ¨</button>
              <button
                v-for="item in workspaceFacets.categories.slice(0, 8)"
                :key="item.value"
                class="kb-filter-chip"
                :class="{ 'is-active': activeCategory === item.value }"
                type="button"
                @click="activeCategory = item.value"
              >
                {{ item.value }}
                <span>{{ item.count }}</span>
              </button>
            </div>
          </div>

          <div class="kb-filter-row">
            <span class="kb-filter-row__label">æ ‡ç­¾</span>
            <div class="kb-filter-row__chips">
              <button class="kb-filter-chip kb-filter-chip--tag" :class="{ 'is-active': !activeTag }" type="button" @click="activeTag = ''">å…¨éƒ¨æ ‡ç­¾</button>
              <button
                v-for="item in workspaceFacets.tags.slice(0, 10)"
                :key="item.value"
                class="kb-filter-chip kb-filter-chip--tag"
                :class="{ 'is-active': activeTag === item.value }"
                type="button"
                @click="activeTag = item.value"
              >
                #{{ item.value }}
              </button>
            </div>
          </div>

          <div v-if="recentlyViewedDatasets.length" class="kb-filter-row">
            <span class="kb-filter-row__label">æœ€è¿‘è®¿é—®</span>
            <div class="kb-filter-row__chips">
              <button
                v-for="item in recentlyViewedDatasets.slice(0, 5)"
                :key="`${item.knowledgeBaseId}-${item.datasetId}`"
                class="kb-filter-chip kb-filter-chip--recent"
                type="button"
                @click="openRecentDataset(item)"
              >
                {{ item.name }}
              </button>
            </div>
          </div>
        </section>

        <div class="kb-workbench__body">
          <KnowledgeWorkbenchCenter
            :knowledge-base="selectedKnowledgeBase"
            :dataset="selectedCard"
            :documents="knowledgeBaseDocuments"
            :current-index="Math.max(currentCardIndex, 0)"
            :total-count="Math.max(filteredCards.length, 1)"
            :stack-cards="filteredCards"
            :transition-direction="transitionDirection"
            :transition-tick="transitionTick"
            @create-dataset="openCreateDataset"
            @wheel-navigate="navigateDataset"
          />

          <KnowledgeDatasetRail
            :knowledge-base="selectedKnowledgeBase"
            :datasets="filteredCards"
            :active-dataset="selectedCard"
            :can-go-prev="currentCardIndex > 0"
            :can-go-next="currentCardIndex >= 0 && currentCardIndex < filteredCards.length - 1"
            :can-manage-documents="Boolean(selectedDataset)"
            :footer-mode="'document'"
            @navigate-dataset="navigateDataset"
            @select-dataset="selectDataset"
            @edit-dataset="openEditDataset"
            @delete-dataset="deleteDataset"
            @append-document="openAppendModal"
            @import-legacy="openImportModal"
            @open-testing="goToQATest"
          />
        </div>
      </div>
    </div>

    <div v-if="modalState.createKnowledgeBase" class="kb-modal-mask">
      <div class="kb-modal-backdrop" @click="modalState.createKnowledgeBase = false"></div>
      <div class="kb-modal">
        <div class="kb-modal__header">
          <h3>新建知识库</h3>
          <button class="kb-modal__close" type="button" @click="modalState.createKnowledgeBase = false">×</button>
        </div>
        <div class="kb-modal__body">
          <label class="kb-modal__field">
            <span>名称</span>
            <input v-model="newKnowledgeBase.name" class="kb-modal__input" type="text" placeholder="例如：哈尔滨城市知识库" />
          </label>
          <label class="kb-modal__field">
            <span>分类</span>
            <input v-model="newKnowledgeBase.category" class="kb-modal__input" type="text" placeholder="例如：城市旅游" />
          </label>
          <label v-if="embeddingProfiles.length" class="kb-modal__field">
            <span>Embedding 配置</span>
            <select v-model="newKnowledgeBase.embedding_profile_id" class="kb-modal__input">
              <option value="">使用默认配置</option>
              <option v-for="profile in embeddingProfiles" :key="profile.id" :value="profile.id">
                {{ profile.name }}{{ profile.quantization ? ` (${profile.quantization})` : '' }}
              </option>
            </select>
          </label>
          <label class="kb-modal__field">
            <span>初始说明</span>
            <textarea v-model="newKnowledgeBase.initial_content" class="kb-modal__textarea" placeholder="可选：补充这个知识库的定位和用途"></textarea>
          </label>
        </div>
        <div class="kb-modal__footer">
          <button class="kb-page-action" type="button" @click="modalState.createKnowledgeBase = false">取消</button>
          <button class="kb-page-qa-btn" type="button" :disabled="creatingKnowledgeBase || !newKnowledgeBase.name.trim()" @click="createKnowledgeBase">
            {{ creatingKnowledgeBase ? '创建中...' : '创建知识库' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="modalState.createDataset || modalState.editDataset" class="kb-modal-mask">
      <div class="kb-modal-backdrop" @click="closeDatasetModal"></div>
      <div class="kb-modal">
        <div class="kb-modal__header">
          <h3>{{ modalState.editDataset ? '编辑资料集' : '新建资料集' }}</h3>
          <button class="kb-modal__close" type="button" @click="closeDatasetModal">×</button>
        </div>
        <div class="kb-modal__body">
          <label class="kb-modal__field">
            <span>资料集名称</span>
            <input v-model="datasetForm.name" class="kb-modal__input" type="text" placeholder="例如：酒店资料集" />
          </label>
          <label class="kb-modal__field">
            <span>分类</span>
            <select v-model="datasetForm.category" class="kb-modal__input">
              <option v-for="category in datasetCategoryOptions" :key="category" :value="category">{{ category }}</option>
            </select>
          </label>
          <label class="kb-modal__field">
            <span>说明</span>
            <textarea v-model="datasetForm.description" class="kb-modal__textarea" placeholder="说明这个资料集承载哪些资料"></textarea>
          </label>
        </div>
        <div class="kb-modal__footer">
          <button class="kb-page-action" type="button" @click="closeDatasetModal">取消</button>
          <button
            class="kb-page-qa-btn"
            type="button"
            :disabled="savingDataset || creatingDataset || !datasetForm.name.trim()"
            @click="modalState.editDataset ? updateDataset() : createDataset()"
          >
            {{ modalState.editDataset ? (savingDataset ? '保存中...' : '保存资料集') : (creatingDataset ? '创建中...' : '创建资料集') }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="modalState.importLegacy" class="kb-modal-mask">
      <div class="kb-modal-backdrop" @click="closeImportModal"></div>
      <div class="kb-modal kb-modal--wide">
        <div class="kb-modal__header">
          <h3>导入旧资料</h3>
          <button class="kb-modal__close" type="button" @click="closeImportModal">×</button>
        </div>
        <div class="kb-modal__body">
          <div class="kb-import-tabs">
            <button
              v-for="mode in legacyImportModes"
              :key="mode.id"
              class="kb-import-tab"
              :class="{ 'is-active': legacyImportMode === mode.id }"
              type="button"
              @click="setLegacyImportMode(mode.id)"
            >
              <strong>{{ mode.label }}</strong>
              <span>{{ mode.description }}</span>
            </button>
          </div>

          <div v-if="legacyImportMode === 'smart'" class="kb-import-panel">
            <div class="kb-import-panel__hero">
              <div>
                <h4>一键导入推荐</h4>
                <p>系统按当前资料集名称、分类和已有标签，自动筛选最相关的旧资料。</p>
              </div>
              <div class="kb-import-panel__tags">
                <span v-for="tag in smartRecommendationLabels" :key="tag">#{{ tag }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="legacyImportMode === 'keyword'" class="kb-import-panel">
            <label class="kb-modal__field">
              <span>关键词</span>
              <input v-model="legacyKeyword" class="kb-modal__input" type="text" placeholder="例如：中央大街、民宿、冰雪大世界" />
            </label>
          </div>

          <div v-else class="kb-import-panel">
            <label class="kb-modal__field">
              <span>关键词</span>
              <input v-model="legacyKeyword" class="kb-modal__input" type="text" placeholder="按标题或正文搜索旧资料" />
            </label>
            <div class="kb-filter-grid">
              <div>
                <div class="kb-modal__field-label">城市筛选</div>
                <div class="kb-choice-wrap">
                  <button
                    v-for="option in legacyCityOptions"
                    :key="option.value"
                    class="kb-choice-chip"
                    :class="{ 'is-active': legacyCities.includes(option.value) }"
                    type="button"
                    @click="toggleLegacyCity(option.value)"
                  >
                    {{ option.value }}
                    <span>{{ option.count }}</span>
                  </button>
                </div>
              </div>
              <div>
                <div class="kb-modal__field-label">旧标签筛选</div>
                <div class="kb-choice-wrap">
                  <button
                    v-for="option in legacyCategoryOptions"
                    :key="option.value"
                    class="kb-choice-chip"
                    :class="{ 'is-active': legacyCategories.includes(option.value) }"
                    type="button"
                    @click="toggleLegacyCategory(option.value)"
                  >
                    {{ option.value }}
                    <span>{{ option.count }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="kb-import-actions">
            <label class="kb-modal__field kb-modal__field--inline">
              <span>导入上限</span>
              <input v-model.number="legacyLimit" class="kb-modal__input" type="number" min="1" max="5000" />
            </label>
            <div class="kb-import-actions__buttons">
              <button class="kb-page-action" type="button" :disabled="previewingLegacy" @click="previewLegacyImport(false, legacyImportMode)">
                {{ previewingLegacy ? '预览中...' : '预览结果' }}
              </button>
              <button class="kb-page-qa-btn" type="button" :disabled="!canImportLegacy" @click="importLegacyData(legacyImportMode)">
                {{ importingLegacy ? '导入中...' : '开始导入' }}
              </button>
            </div>
          </div>

          <div v-if="importingLegacy || legacyImportProgress" class="kb-progress">
            <div class="kb-progress__head">
              <span>导入进度</span>
              <span>{{ legacyImportProgress }}%</span>
            </div>
            <div class="kb-progress__track">
              <div class="kb-progress__bar" :style="{ width: `${legacyImportProgress}%` }"></div>
            </div>
          </div>

          <div v-if="legacyMatchedSummary || legacyImportMessage" class="kb-feedback-panel">
            <div v-if="legacyMatchedSummary">{{ legacyMatchedSummary }}</div>
            <div v-if="legacyImportMessage">{{ legacyImportMessage }}</div>
            <div v-if="legacyPreviewCount !== null">命中 {{ legacyPreviewCount }} 条候选，最多导入 {{ legacyLimit }} 条</div>
          </div>

          <div class="kb-preview-list">
            <article v-for="item in legacyPreviewItems" :key="item.id" class="kb-preview-card">
              <strong>{{ item.name }}</strong>
              <span>{{ item.city }} · {{ item.business_type || item.category }} · {{ item.source_type }}</span>
              <p>{{ item.preview }}</p>
            </article>
            <div v-if="!legacyPreviewItems.length" class="kb-empty-tip">暂无候选资料，请先预览。</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="modalState.appendDocument" class="kb-modal-mask">
      <div class="kb-modal-backdrop" @click="closeAppendModal"></div>
      <div class="kb-modal kb-modal--wide">
        <div class="kb-modal__header">
          <h3>追加资料</h3>
          <button class="kb-modal__close" type="button" @click="closeAppendModal">×</button>
        </div>
        <div class="kb-modal__body">
          <div class="kb-import-tabs kb-import-tabs--compact">
            <button
              v-for="tab in appendTabs"
              :key="tab.id"
              class="kb-import-tab"
              :class="{ 'is-active': activeAppendTab === tab.id }"
              type="button"
              @click="activeAppendTab = tab.id"
            >
              <strong>{{ tab.label }}</strong>
            </button>
          </div>

          <div v-if="activeAppendTab === 'text'" class="kb-import-panel">
            <label class="kb-modal__field">
              <span>资料名称</span>
              <input v-model="textDocName" class="kb-modal__input" type="text" placeholder="例如：北极村景点简介" />
            </label>
            <label class="kb-modal__field">
              <span>正文</span>
              <textarea v-model="textInput" class="kb-modal__textarea kb-modal__textarea--large" placeholder="输入要追加到资料集的文本"></textarea>
            </label>
            <div class="kb-modal__footer kb-modal__footer--inner">
              <span class="kb-inline-tip">文本会作为独立资料加入当前资料集</span>
              <button class="kb-page-qa-btn" type="button" :disabled="submittingText || !textInput.trim()" @click="submitTextDocument">
                {{ submittingText ? '添加中...' : '添加文本资料' }}
              </button>
            </div>
          </div>

          <div v-else-if="activeAppendTab === 'file'" class="kb-import-panel">
            <div class="kb-upload-box" @click="openUploadFilePicker" @dragover.prevent @drop.prevent="handleDrop">
              <input ref="uploadInputRef" type="file" class="kb-hidden-input" accept=".pdf,.docx,.txt,.md,.html,.htm,.pptx,.csv,.json" @change="handleFileSelect" />
              <strong>点击或拖拽上传文件</strong>
              <span>支持 PDF、Word、TXT、Markdown、HTML、PPT、CSV、JSON</span>
            </div>
            <div v-if="uploadFile" class="kb-file-card">
              <div>
                <strong>{{ uploadFile.name }}</strong>
                <span>{{ (uploadFile.size / 1024 / 1024).toFixed(2) }} MB</span>
              </div>
              <button class="kb-page-qa-btn" type="button" :disabled="uploading" @click="uploadDocument">
                {{ uploading ? '上传中...' : '加入资料集' }}
              </button>
            </div>
            <div v-if="uploadMessage" class="kb-feedback-panel">{{ uploadMessage }}</div>
          </div>

          <div v-else class="kb-import-panel">
            <label class="kb-modal__field">
              <span>网页链接</span>
              <input v-model="crawlUrl" class="kb-modal__input" type="text" placeholder="例如：https://example.com/hotel-guide" />
            </label>
            <div class="kb-modal__footer kb-modal__footer--inner">
              <span class="kb-inline-tip">抓取成功后会作为网页资料加入当前资料集</span>
              <button class="kb-page-qa-btn" type="button" :disabled="crawling || !crawlUrl.trim()" @click="startCrawl">
                {{ crawling ? '抓取中...' : '抓取并加入资料集' }}
              </button>
            </div>
            <div v-if="crawlMessage" class="kb-feedback-panel">{{ crawlMessage }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'
import { apiUrl } from '@/utils/apiBase'
import KnowledgeWorkbenchCenter from '@/components/admin/knowledge/KnowledgeWorkbenchCenter.vue'
import KnowledgeDatasetRail from '@/components/admin/knowledge/KnowledgeDatasetRail.vue'
import type {
  EmbeddingProfile,
  KnowledgeBaseItem,
  LegacyOption,
  LegacyPreviewItem,
  WorkspaceFacets,
  WorkspaceResponse,
  WorkspaceStats,
} from '@/components/admin/knowledge/types'

type LegacyImportMode = 'smart' | 'keyword' | 'advanced'
type AppendTab = 'text' | 'file' | 'web'

interface RecentDatasetItem {
  knowledgeBaseId: number
  datasetId: number
  name: string
  category: string
}

const API_URL = apiUrl('/api/knowledge/')
const RECENT_STORAGE_KEY = 'admin-knowledge-recent-datasets'
const datasetCategoryOptions = ['景点', '酒店', '餐饮', '交通', '攻略', '综合', '待分类']
const appendTabs: Array<{ id: AppendTab; label: string }> = [
  { id: 'text', label: '文本资料' },
  { id: 'file', label: '文件导入' },
  { id: 'web', label: '网页抓取' },
]
const legacyImportModes: Array<{ id: LegacyImportMode; label: string; description: string }> = [
  { id: 'smart', label: '一键导入', description: '自动按资料集分类和标签推荐旧资料' },
  { id: 'keyword', label: '关键词导入', description: '按标题、正文和历史标签检索旧资料' },
  { id: 'advanced', label: '高级筛选', description: '按城市、旧标签和关键词精细筛选' },
]
const emptyFacets = (): WorkspaceFacets => ({ categories: [], tags: [], statuses: [] })
const emptyStats = (): WorkspaceStats => ({
  knowledge_base_status: 'empty',
  dataset_count: 0,
  document_count: 0,
  pending_count: 0,
  active_count: 0,
  rejected_count: 0,
  category: '未分类',
})

const router = useRouter()

const workspaceLoading = ref(false)
const creatingKnowledgeBase = ref(false)
const creatingDataset = ref(false)
const savingDataset = ref(false)
const submittingText = ref(false)
const uploading = ref(false)
const crawling = ref(false)
const previewingLegacy = ref(false)
const importingLegacy = ref(false)

const knowledgeBases = ref<KnowledgeBaseItem[]>([])
const datasets = ref<KnowledgeBaseItem[]>([])
const documents = ref<KnowledgeBaseItem[]>([])
const knowledgeBaseDocuments = ref<KnowledgeBaseItem[]>([])
const documentCache = ref<Record<number, KnowledgeBaseItem[]>>({})
const documentRequesting = ref<Record<number, boolean>>({})
const selectedKnowledgeBase = ref<KnowledgeBaseItem | null>(null)
const selectedDataset = ref<KnowledgeBaseItem | null>(null)
const selectedCard = ref<KnowledgeBaseItem | null>(null)
const embeddingProfiles = ref<EmbeddingProfile[]>([])
const workspaceFacets = ref<WorkspaceFacets>(emptyFacets())
const workspaceStats = ref<WorkspaceStats>(emptyStats())
const recentlyViewedDatasets = ref<RecentDatasetItem[]>([])

const searchQuery = ref('')
const activeCategory = ref('')
const activeTag = ref('')
const filterSidebarOpen = ref(false)
const isCompactWorkbench = ref(false)
const activeAppendTab = ref<AppendTab>('text')
const transitionDirection = ref<'up' | 'down'>('down')
const transitionTick = ref(0)

const modalState = reactive({
  createKnowledgeBase: false,
  createDataset: false,
  editDataset: false,
  importLegacy: false,
  appendDocument: false,
})

const newKnowledgeBase = ref({
  name: '',
  category: '城市旅游',
  embedding_profile_id: '' as number | '',
  initial_content: '',
})
const datasetForm = ref({
  name: '',
  category: '景点',
  description: '',
})
const editingDataset = ref<KnowledgeBaseItem | null>(null)

const textDocName = ref('')
const textInput = ref('')
const uploadFile = ref<File | null>(null)
const uploadMessage = ref('')
const uploadInputRef = ref<HTMLInputElement | null>(null)
const crawlUrl = ref('')
const crawlMessage = ref('')

const legacyCities = ref<string[]>([])
const legacyCategories = ref<string[]>([])
const legacyKeyword = ref('')
const legacyLimit = ref(100)
const legacyPreviewCount = ref<number | null>(null)
const legacyImportMessage = ref('')
const legacyTotalCandidates = ref(0)
const legacyCityOptions = ref<LegacyOption[]>([])
const legacyCategoryOptions = ref<LegacyOption[]>([])
const legacyPreviewItems = ref<LegacyPreviewItem[]>([])
const legacyMatchedBy = ref<Record<string, any> | null>(null)
const legacyImportMode = ref<LegacyImportMode>('smart')
const legacyImportProgress = ref(0)
let legacyImportProgressTimer: number | null = null

const parseJsonSafely = async (response: Response) => {
  try {
    return await response.json()
  } catch {
    return null
  }
}

const extractErrorMessage = (data: any, fallback: string) => {
  if (typeof data?.error === 'string' && data.error.trim()) return data.error
  if (typeof data?.message === 'string' && data.message.trim()) return data.message
  return fallback
}

const readStoredAccessToken = () => {
  if (typeof window === 'undefined') return ''

  for (const key of Object.keys(window.localStorage)) {
    if (!key.startsWith('sb-') || !key.endsWith('-auth-token')) continue
    const raw = window.localStorage.getItem(key)
    if (!raw) continue

    try {
      const parsed = JSON.parse(raw)
      if (parsed?.access_token) return parsed.access_token as string
      if (parsed?.currentSession?.access_token) return parsed.currentSession.access_token as string
      if (Array.isArray(parsed) && parsed[0]?.access_token) return parsed[0].access_token as string
    } catch (error) {
      console.warn('Failed to parse local auth cache:', error)
    }
  }

  return ''
}

const getAccessToken = async () => {
  try {
    const sessionResult = await Promise.race([
      supabase.auth.getSession(),
      new Promise<null>(resolve => window.setTimeout(() => resolve(null), 2000)),
    ])

    if (sessionResult && typeof sessionResult === 'object' && 'data' in sessionResult) {
      return sessionResult.data.session?.access_token || readStoredAccessToken()
    }
  } catch (error) {
    console.warn('Failed to get session from Supabase:', error)
  }

  return readStoredAccessToken()
}

const authHeaders = async (includeJson = true) => {
  const token = await getAccessToken()
  const headers: Record<string, string> = {}
  if (includeJson) headers['Content-Type'] = 'application/json'
  if (!token) throw new Error('登录状态获取失败，请刷新页面后重试')
  headers.Authorization = `Bearer ${token}`
  return headers
}

const datasetTags = (item: KnowledgeBaseItem) => {
  const metadata = item.metadata || {}
  const rawTags = [
    ...(Array.isArray(metadata.tags) ? metadata.tags : []),
    ...(typeof metadata.keywords === 'string' ? metadata.keywords.split(/[，,、|/]/) : []),
    metadata.category,
    metadata.name,
  ]
  return [...new Set(rawTags.map(tag => String(tag || '').trim()).filter(Boolean))]
}

const cardTags = (item: KnowledgeBaseItem) => {
  const metadata = item.metadata || {}
  const rawTags = [
    ...(Array.isArray(metadata.tags) ? metadata.tags : []),
    ...(typeof metadata.keywords === 'string' ? metadata.keywords.split(/[ï¼Œ,ã€|/]/) : []),
    metadata.category,
    metadata.business_type,
    metadata.city,
    metadata.name,
    metadata.title,
  ]
  return [...new Set(rawTags.map(tag => String(tag || '').trim()).filter(Boolean))]
}

const filteredDatasets = computed(() => datasets.value.filter(item => {
  const keyword = searchQuery.value.trim().toLowerCase()
  const categoryMatch = !activeCategory.value || (item.metadata?.category || '') === activeCategory.value
  const tagMatch = !activeTag.value || datasetTags(item).includes(activeTag.value)
  const haystack = [item.name, item.metadata?.name, item.metadata?.category, item.metadata?.description, ...datasetTags(item)]
    .map(value => String(value || '').toLowerCase())
    .join('\n')
  const searchMatch = !keyword || haystack.includes(keyword)
  return categoryMatch && tagMatch && searchMatch
}))

const filteredCards = computed(() => knowledgeBaseDocuments.value.filter(item => {
  const keyword = searchQuery.value.trim().toLowerCase()
  const metadata = item.metadata || {}
  const categoryMatch = !activeCategory.value || (metadata.category || '') === activeCategory.value || (metadata.business_type || '') === activeCategory.value
  const tagMatch = !activeTag.value || cardTags(item).includes(activeTag.value)
  const haystack = [
    item.name,
    metadata.name,
    metadata.title,
    metadata.city,
    metadata.category,
    metadata.business_type,
    metadata.description,
    item.content,
    ...cardTags(item),
  ]
    .map(value => String(value || '').toLowerCase())
    .join('\n')
  const searchMatch = !keyword || haystack.includes(keyword)
  return categoryMatch && tagMatch && searchMatch
}))

const currentCardIndex = computed(() => filteredCards.value.findIndex(item => item.id === selectedCard.value?.id))

const smartRecommendationLabels = computed(() => {
  const matched = legacyMatchedBy.value
  if (matched?.mode === 'smart' && Array.isArray(matched?.normalized_categories) && matched.normalized_categories.length) {
    return matched.normalized_categories
  }
  return selectedDataset.value ? datasetTags(selectedDataset.value).slice(0, 5) : []
})

const legacyMatchedSummary = computed(() => {
  const matchedBy = legacyMatchedBy.value
  if (!matchedBy) return ''
  if (matchedBy.mode === 'smart') {
    const labels = Array.isArray(matchedBy.normalized_categories) ? matchedBy.normalized_categories.join(' / ') : ''
    return `系统按“${matchedBy.dataset_category || '待分类'}”进行智能推荐，推荐标签：${labels || '待分类'}`
  }
  if (matchedBy.mode === 'keyword') {
    return matchedBy.keyword ? `当前按关键词“${matchedBy.keyword}”检索旧资料` : '请先输入关键词后再检索'
  }
  const cities = Array.isArray(matchedBy.cities) && matchedBy.cities.length ? matchedBy.cities.join(' / ') : '不限城市'
  const categories = Array.isArray(matchedBy.categories) && matchedBy.categories.length ? matchedBy.categories.join(' / ') : '不限标签'
  return `高级筛选条件：${cities}，${categories}`
})

const canImportLegacy = computed(() => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value || importingLegacy.value) return false
  if (legacyImportMode.value === 'keyword' && !legacyKeyword.value.trim()) return false
  return (legacyPreviewCount.value || 0) > 0
})

watch(filteredCards, items => {
  if (!items.length) {
    selectedCard.value = null
    return
  }

  if (!selectedCard.value || !items.some(item => item.id === selectedCard.value?.id)) {
    selectedCard.value = items[0]
  }
}, { immediate: true })

const syncWorkbenchMode = () => {
  if (typeof window === 'undefined') return
  isCompactWorkbench.value = window.innerWidth <= 1100
  if (!isCompactWorkbench.value) {
    filterSidebarOpen.value = false
  }
}

const loadRecentDatasets = () => {
  if (typeof window === 'undefined') return
  try {
    const raw = window.localStorage.getItem(RECENT_STORAGE_KEY)
    recentlyViewedDatasets.value = raw ? JSON.parse(raw) : []
  } catch {
    recentlyViewedDatasets.value = []
  }
}

const saveRecentDatasets = () => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(recentlyViewedDatasets.value.slice(0, 8)))
}

const rememberRecentDataset = (dataset: KnowledgeBaseItem | null, knowledgeBase: KnowledgeBaseItem | null) => {
  if (!dataset || !knowledgeBase) return
  const next: RecentDatasetItem = {
    knowledgeBaseId: knowledgeBase.id,
    datasetId: dataset.id,
    name: dataset.name || dataset.metadata?.name || `资料集 ${dataset.id}`,
    category: dataset.metadata?.category || '待分类',
  }
  recentlyViewedDatasets.value = [
    next,
    ...recentlyViewedDatasets.value.filter(item => !(item.knowledgeBaseId === next.knowledgeBaseId && item.datasetId === next.datasetId)),
  ].slice(0, 8)
  saveRecentDatasets()
}

const openRecentDataset = async (item: RecentDatasetItem) => {
  await loadWorkspace(item.knowledgeBaseId, item.datasetId)
  filterSidebarOpen.value = false
}

const stopLegacyProgress = (value = 0) => {
  if (legacyImportProgressTimer !== null) {
    window.clearInterval(legacyImportProgressTimer)
    legacyImportProgressTimer = null
  }
  legacyImportProgress.value = value
}

const startLegacyProgress = () => {
  stopLegacyProgress(12)
  legacyImportProgressTimer = window.setInterval(() => {
    const current = legacyImportProgress.value
    if (current >= 90) return
    legacyImportProgress.value = Math.min(90, current + (current < 36 ? 9 : current < 70 ? 5 : 2))
  }, 260)
}

const scheduleLegacyProgressReset = () => {
  window.setTimeout(() => {
    if (!importingLegacy.value) legacyImportProgress.value = 0
  }, 900)
}

const applyLegacyPreviewData = (data: any) => {
  legacyTotalCandidates.value = data?.total_candidates || 0
  legacyPreviewCount.value = data?.total_matches || 0
  legacyCityOptions.value = Array.isArray(data?.city_options) ? data.city_options : []
  legacyCategoryOptions.value = Array.isArray(data?.category_options) ? data.category_options : []
  legacyPreviewItems.value = Array.isArray(data?.preview_items) ? data.preview_items : []
  legacyMatchedBy.value = data?.matched_by || null
}

const resetLegacyPreview = () => {
  legacyPreviewCount.value = null
  legacyImportMessage.value = ''
  legacyTotalCandidates.value = 0
  legacyCityOptions.value = []
  legacyCategoryOptions.value = []
  legacyPreviewItems.value = []
  legacyMatchedBy.value = null
  stopLegacyProgress(0)
}

const resetAppendForm = () => {
  activeAppendTab.value = 'text'
  textDocName.value = ''
  textInput.value = ''
  uploadFile.value = null
  uploadMessage.value = ''
  crawlUrl.value = ''
  crawlMessage.value = ''
  if (uploadInputRef.value) uploadInputRef.value.value = ''
}

const loadWorkspace = async (knowledgeBaseId?: number | null, datasetId?: number | null) => {
  workspaceLoading.value = true
  try {
    const query = new URLSearchParams({ source: 'local' })
    if (knowledgeBaseId) query.set('knowledge_base_id', String(knowledgeBaseId))
    if (datasetId) query.set('dataset_id', String(datasetId))
    const response = await fetch(`${API_URL}workspace/?${query.toString()}`)
    const data = await parseJsonSafely(response) as WorkspaceResponse
    if (!response.ok) throw new Error(extractErrorMessage(data, '获取知识库工作台失败'))

    knowledgeBases.value = Array.isArray(data?.knowledge_bases) ? data.knowledge_bases : []
    const previousKnowledgeBaseId = selectedKnowledgeBase.value?.id || null
    selectedKnowledgeBase.value = data?.knowledge_base || null
    datasets.value = Array.isArray(data?.datasets) ? data.datasets : []
    workspaceFacets.value = data?.facets || emptyFacets()
    workspaceStats.value = data?.stats || emptyStats()
    selectedDataset.value = data?.active_dataset || null
    documents.value = Array.isArray(data?.documents) ? data.documents : []
    if (previousKnowledgeBaseId !== selectedKnowledgeBase.value?.id) {
      documentCache.value = {}
      documentRequesting.value = {}
      knowledgeBaseDocuments.value = []
      selectedCard.value = null
    }
    if (selectedDataset.value) {
      documentCache.value = {
        ...documentCache.value,
        [selectedDataset.value.id]: documents.value,
      }
    }
    if (selectedDataset.value && selectedKnowledgeBase.value) {
      rememberRecentDataset(selectedDataset.value, selectedKnowledgeBase.value)
    }
    if (selectedKnowledgeBase.value) {
      await fetchKnowledgeBaseDocuments(selectedKnowledgeBase.value.id)
    }
  } finally {
    workspaceLoading.value = false
  }
}

const fetchKnowledgeBaseDocuments = async (knowledgeBaseId: number) => {
  if (knowledgeBaseDocuments.value.length && selectedKnowledgeBase.value?.id === knowledgeBaseId) return

  const query = new URLSearchParams({ source: 'local' })
  const response = await fetch(`${API_URL}${knowledgeBaseId}/documents/?${query.toString()}`)
  const data = await parseJsonSafely(response)
  if (!response.ok) throw new Error(extractErrorMessage(data, 'èŽ·å–å…¨éƒ¨èµ„æ–™å¤±è´¥'))

  const nextDocuments = Array.isArray(data) ? data : data?.results || []
  knowledgeBaseDocuments.value = nextDocuments

  if (!selectedCard.value && nextDocuments.length) {
    selectedCard.value = nextDocuments[0]
  }
}

const fetchDocuments = async (knowledgeBaseId: number, datasetId: number) => {
  if (documentCache.value[datasetId]) {
    documents.value = documentCache.value[datasetId]
    return
  }
  if (documentRequesting.value[datasetId]) return

  documentRequesting.value = { ...documentRequesting.value, [datasetId]: true }

  try {
    const query = new URLSearchParams({ source: 'local', dataset_id: String(datasetId) })
    const response = await fetch(`${API_URL}${knowledgeBaseId}/documents/?${query.toString()}`)
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '获取资料失败'))

    const nextDocuments = Array.isArray(data) ? data : data?.results || []
    documentCache.value = { ...documentCache.value, [datasetId]: nextDocuments }
    if (selectedDataset.value?.id === datasetId) {
      documents.value = nextDocuments
    }
  } finally {
    documentRequesting.value = { ...documentRequesting.value, [datasetId]: false }
  }
}

const fetchEmbeddingProfiles = async () => {
  try {
    const response = await fetch(apiUrl('/api/embedding-profiles/'))
    const data = await parseJsonSafely(response)
    if (response.ok) {
      embeddingProfiles.value = Array.isArray(data) ? data : data?.results || []
    }
  } catch (error) {
    console.error('Failed to fetch embedding profiles:', error)
  }
}

const handleKnowledgeBaseChange = async (event: Event) => {
  const nextId = Number((event.target as HTMLSelectElement).value)
  activeCategory.value = ''
  activeTag.value = ''
  searchQuery.value = ''
  documents.value = []
  await loadWorkspace(nextId)
}

const handleDatasetChange = async (event: Event) => {
  if (!selectedKnowledgeBase.value) return
  const nextId = Number((event.target as HTMLSelectElement).value)
  selectedCard.value = null
  documents.value = []
  await loadWorkspace(selectedKnowledgeBase.value.id, Number.isFinite(nextId) && nextId > 0 ? nextId : null)
}

const selectDataset = async (item: KnowledgeBaseItem, direction?: 'up' | 'down') => {
  if (selectedCard.value?.id === item.id) return

  const nextIndex = filteredCards.value.findIndex(entry => entry.id === item.id)
  const currentIndexValue = currentCardIndex.value

  if (nextIndex >= 0 && currentIndexValue >= 0) {
    transitionDirection.value = direction || (nextIndex > currentIndexValue ? 'down' : 'up')
    transitionTick.value += 1
  }

  selectedCard.value = item
}

const navigateDataset = async (step: number) => {
  const next = filteredCards.value[currentCardIndex.value + step]
  if (next) {
    await selectDataset(next, step > 0 ? 'down' : 'up')
  }
}

const openCreateKnowledgeBase = () => {
  newKnowledgeBase.value = {
    name: '',
    category: '城市旅游',
    embedding_profile_id: '',
    initial_content: '',
  }
  modalState.createKnowledgeBase = true
}

const openCreateDataset = () => {
  datasetForm.value = {
    name: '',
    category: '景点',
    description: '',
  }
  editingDataset.value = null
  modalState.createDataset = true
}

const openEditDataset = (dataset: KnowledgeBaseItem | null) => {
  if (!dataset) return
  editingDataset.value = dataset
  datasetForm.value = {
    name: dataset.name || dataset.metadata?.name || '',
    category: dataset.metadata?.category || '待分类',
    description: dataset.metadata?.description || '',
  }
  modalState.editDataset = true
}

const closeDatasetModal = () => {
  modalState.createDataset = false
  modalState.editDataset = false
  editingDataset.value = null
}

const openImportModal = async () => {
  modalState.importLegacy = true
  legacyImportMode.value = 'smart'
  legacyKeyword.value = ''
  legacyCities.value = []
  legacyCategories.value = []
  resetLegacyPreview()
  if (selectedDataset.value) {
    await previewLegacyImport(true, 'smart')
  }
}

const closeImportModal = () => {
  modalState.importLegacy = false
  resetLegacyPreview()
}

const openAppendModal = () => {
  resetAppendForm()
  modalState.appendDocument = true
}

const closeAppendModal = () => {
  resetAppendForm()
  modalState.appendDocument = false
}

const buildLegacyPayload = (dryRun = false, mode: LegacyImportMode = legacyImportMode.value) => {
  const payload: Record<string, any> = {
    dataset_id: selectedDataset.value?.id,
    mode,
    limit: legacyLimit.value,
    dry_run: dryRun,
  }

  if (mode === 'keyword') {
    payload.keyword = legacyKeyword.value.trim()
    return payload
  }

  if (mode === 'advanced') {
    payload.cities = legacyCities.value
    payload.categories = legacyCategories.value
    payload.keyword = legacyKeyword.value.trim()
  }

  return payload
}

const setLegacyImportMode = async (mode: LegacyImportMode) => {
  legacyImportMode.value = mode
  legacyImportMessage.value = ''
  if (mode === 'smart' && selectedDataset.value) {
    await previewLegacyImport(true, 'smart')
  }
}

const toggleLegacyCity = (value: string) => {
  legacyCities.value = legacyCities.value.includes(value)
    ? legacyCities.value.filter(item => item !== value)
    : [...legacyCities.value, value]
}

const toggleLegacyCategory = (value: string) => {
  legacyCategories.value = legacyCategories.value.includes(value)
    ? legacyCategories.value.filter(item => item !== value)
    : [...legacyCategories.value, value]
}

const previewLegacyImport = async (silent = false, mode: LegacyImportMode = legacyImportMode.value) => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value) return
  if (!silent) {
    previewingLegacy.value = true
    legacyImportMessage.value = ''
  }
  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/import_legacy/?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify(buildLegacyPayload(true, mode)),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '预览失败'))
    applyLegacyPreviewData(data)
  } catch (error: any) {
    console.error(error)
    if (!silent) legacyImportMessage.value = error?.message || '预览失败'
  } finally {
    if (!silent) previewingLegacy.value = false
  }
}

const importLegacyData = async (mode: LegacyImportMode = legacyImportMode.value) => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value) return
  if (mode === 'keyword' && !legacyKeyword.value.trim()) {
    legacyImportMessage.value = '请先输入关键词'
    return
  }

  const currentDatasetId = selectedDataset.value.id
  importingLegacy.value = true
  legacyImportMessage.value = ''
  startLegacyProgress()
  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/import_legacy/?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify(buildLegacyPayload(false, mode)),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '导入失败'))

    stopLegacyProgress(100)
    applyLegacyPreviewData(data)
    legacyImportMessage.value = `已导入 ${data?.imported_count || 0} 条旧资料到当前资料集`
    await loadWorkspace(selectedKnowledgeBase.value.id, currentDatasetId)
    scheduleLegacyProgressReset()
  } catch (error: any) {
    console.error(error)
    stopLegacyProgress(0)
    legacyImportMessage.value = error?.message || '导入失败'
  } finally {
    importingLegacy.value = false
  }
}

const createKnowledgeBase = async () => {
  if (!newKnowledgeBase.value.name.trim()) return
  creatingKnowledgeBase.value = true
  try {
    const response = await fetch(`${API_URL}?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify({
        metadata: {
          name: newKnowledgeBase.value.name.trim(),
          category: newKnowledgeBase.value.category.trim() || '城市旅游',
        },
        embedding_profile: newKnowledgeBase.value.embedding_profile_id || null,
        content: newKnowledgeBase.value.initial_content.trim(),
      }),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '创建知识库失败'))
    modalState.createKnowledgeBase = false
    await loadWorkspace(data?.id)
  } catch (error) {
    console.error(error)
    alert(error instanceof Error ? error.message : '创建知识库失败')
  } finally {
    creatingKnowledgeBase.value = false
  }
}

const createDataset = async () => {
  if (!selectedKnowledgeBase.value || !datasetForm.value.name.trim()) return
  creatingDataset.value = true
  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/datasets/?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify({
        metadata: {
          name: datasetForm.value.name.trim(),
          category: datasetForm.value.category,
          description: datasetForm.value.description.trim(),
        },
      }),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '创建资料集失败'))
    closeDatasetModal()
    await loadWorkspace(selectedKnowledgeBase.value.id, data?.id)
  } catch (error) {
    console.error(error)
    alert(error instanceof Error ? error.message : '创建资料集失败')
  } finally {
    creatingDataset.value = false
  }
}

const updateDataset = async () => {
  if (!selectedKnowledgeBase.value || !editingDataset.value || !datasetForm.value.name.trim()) return
  savingDataset.value = true
  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/datasets/${editingDataset.value.id}/?source=local`, {
      method: 'PATCH',
      headers: await authHeaders(),
      body: JSON.stringify({
        metadata: {
          name: datasetForm.value.name.trim(),
          category: datasetForm.value.category,
          description: datasetForm.value.description.trim(),
        },
      }),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '保存资料集失败'))
    const currentId = editingDataset.value.id
    closeDatasetModal()
    await loadWorkspace(selectedKnowledgeBase.value.id, currentId)
  } catch (error) {
    console.error(error)
    alert(error instanceof Error ? error.message : '保存资料集失败')
  } finally {
    savingDataset.value = false
  }
}

const deleteDataset = async (dataset: KnowledgeBaseItem | null) => {
  if (!selectedKnowledgeBase.value || !dataset) return
  const datasetName = dataset.name || dataset.metadata?.name || `资料集 ${dataset.id}`
  if (!window.confirm(`确定删除“${datasetName}”吗？删除后其中资料也会一起移除。`)) return

  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/datasets/${dataset.id}/?source=local`, {
      method: 'DELETE',
      headers: await authHeaders(),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '删除资料集失败'))
    await loadWorkspace(selectedKnowledgeBase.value.id)
  } catch (error) {
    console.error(error)
    alert(error instanceof Error ? error.message : '删除资料集失败')
  }
}

const submitTextDocument = async () => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value || !textInput.value.trim()) return
  submittingText.value = true
  try {
    const response = await fetch(`${API_URL}${selectedKnowledgeBase.value.id}/documents/?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify({
        dataset_id: selectedDataset.value.id,
        content: textInput.value.trim(),
        metadata: {
          name: textDocName.value.trim() || `文本资料 ${documents.value.length + 1}`,
          source_type: 'text',
          category: selectedDataset.value.metadata?.category || '待分类',
        },
      }),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '添加资料失败'))
    await loadWorkspace(selectedKnowledgeBase.value.id, selectedDataset.value.id)
    closeAppendModal()
  } catch (error) {
    console.error(error)
    alert(error instanceof Error ? error.message : '添加资料失败')
  } finally {
    submittingText.value = false
  }
}

const openUploadFilePicker = () => uploadInputRef.value?.click()

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) uploadFile.value = input.files[0]
}

const handleDrop = (event: DragEvent) => {
  if (event.dataTransfer?.files?.[0]) uploadFile.value = event.dataTransfer.files[0]
}

const uploadDocument = async () => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value || !uploadFile.value) return
  uploading.value = true
  uploadMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('files', uploadFile.value)
    formData.append('knowledge_base_id', String(selectedKnowledgeBase.value.id))
    formData.append('dataset_id', String(selectedDataset.value.id))

    const response = await fetch(`${API_URL}upload/?source=local`, {
      method: 'POST',
      headers: await authHeaders(false),
      body: formData,
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '上传失败'))
    await loadWorkspace(selectedKnowledgeBase.value.id, selectedDataset.value.id)
    closeAppendModal()
  } catch (error) {
    console.error(error)
    uploadMessage.value = error instanceof Error ? error.message : '上传失败'
  } finally {
    uploading.value = false
  }
}

const startCrawl = async () => {
  if (!selectedKnowledgeBase.value || !selectedDataset.value || !crawlUrl.value.trim()) return
  crawling.value = true
  crawlMessage.value = ''
  try {
    const response = await fetch(`${API_URL}crawl/?source=local`, {
      method: 'POST',
      headers: await authHeaders(),
      body: JSON.stringify({
        knowledge_base_id: selectedKnowledgeBase.value.id,
        dataset_id: selectedDataset.value.id,
        url: crawlUrl.value.trim(),
      }),
    })
    const data = await parseJsonSafely(response)
    if (!response.ok) throw new Error(extractErrorMessage(data, '抓取失败'))
    await loadWorkspace(selectedKnowledgeBase.value.id, selectedDataset.value.id)
    closeAppendModal()
  } catch (error) {
    console.error(error)
    crawlMessage.value = error instanceof Error ? error.message : '抓取失败'
  } finally {
    crawling.value = false
  }
}

const goToQATest = () => {
  if (!selectedKnowledgeBase.value) return
  router.push({ name: 'admin-qa-test', query: { knowledge_base: String(selectedKnowledgeBase.value.id) } })
}

onMounted(async () => {
  syncWorkbenchMode()
  window.addEventListener('resize', syncWorkbenchMode)
  loadRecentDatasets()
  await Promise.all([loadWorkspace(), fetchEmbeddingProfiles()])
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', syncWorkbenchMode)
  }
})
</script>

<style scoped>
.kb-page-shell {
  position: relative;
  z-index: 1;
  display: block;
  width: 100%;
  max-width: 100%;
  min-height: auto;
  height: auto;
  background: #ffffff;
  overflow: visible;
}
.kb-page-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.26);
  z-index: 40;
}
.kb-page-main {
  min-width: 0;
  width: 100%;
  min-height: auto;
  height: auto;
  padding: 0;
  overflow: visible;
}
.kb-page-select,
.kb-modal__input,
.kb-modal__textarea {
  width: 100%;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #2e2b28;
  outline: none;
  box-sizing: border-box;
}
.kb-page-select {
  min-width: 220px;
  height: 40px;
  padding: 0 12px;
}
.kb-page-action,
.kb-page-qa-btn {
  height: 42px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 14px;
  cursor: pointer;
}
.kb-page-action {
  background: rgba(255, 255, 255, 0.84);
  border-color: rgba(15, 23, 42, 0.08);
  color: #2f2c2a;
}
.kb-page-qa-btn {
  background: #24243f;
  color: #f8f1e7;
}
.kb-page-qa-btn:disabled,
.kb-page-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.kb-workbench {
  display: block;
  width: 100%;
  max-width: 100%;
  min-height: auto;
  height: auto;
  overflow: visible;
  background: #ffffff;
}
.kb-admin-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;
}
.kb-admin-head__crumb {
  margin: 0 0 6px;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1;
  font-weight: 700;
}
.kb-admin-head h1 {
  margin: 0;
  color: #06152d;
  font-size: 26px;
  line-height: 1.12;
  font-weight: 800;
  letter-spacing: 0;
}
.kb-admin-head span {
  display: block;
  margin-top: 4px;
  color: #52647d;
  font-size: 14px;
  line-height: 1.35;
}
.kb-admin-head__tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
.kb-admin-head__search {
  position: relative;
  width: min(360px, 34vw);
}
.kb-admin-head__search span {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.kb-admin-head__search input {
  width: 100%;
  height: 40px;
  padding: 0 16px;
  border: 1px solid #edf2f7;
  border-radius: 12px;
  background: #f8fafc;
  color: #0f172a;
  font-size: 14px;
  outline: none;
  transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}
.kb-admin-head__search input:focus {
  border-color: #bfdbfe;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08);
}
.kb-admin-head__button {
  height: 40px;
  padding: 0 18px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #0f1b33;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}
.kb-workbench__topbar {
  display: none;
  grid-template-columns: minmax(180px, 1fr) minmax(360px, 0.9fr) auto;
  gap: 18px;
  align-items: end;
  padding: 22px 28px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #ffffff;
}
.kb-workbench__title-block span,
.kb-workbench__select-wrap span {
  display: block;
  margin-bottom: 7px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.kb-workbench__title-block h1 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  line-height: 1.2;
  font-weight: 800;
}
.kb-workbench__controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.kb-workbench__select-wrap {
  min-width: 0;
}
.kb-workbench__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}
.kb-workbench__stats {
  display: none;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  padding: 0 28px;
  background: #e2e8f0;
}
.kb-workbench__stats article {
  min-width: 0;
  padding: 14px 18px;
  background: #ffffff;
}
.kb-workbench__stats strong {
  display: block;
  color: #0f172a;
  font-size: 22px;
  line-height: 1;
}
.kb-workbench__stats span {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}
.kb-filter-panel {
  display: none;
  flex-direction: column;
  gap: 12px;
  padding: 16px 28px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #ffffff;
}
.kb-filter-panel__search {
  display: flex;
  align-items: end;
  gap: 12px;
}
.kb-filter-panel__search .kb-workbench__select-wrap {
  flex: 1;
}
.kb-filter-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.kb-filter-row__label {
  width: 56px;
  padding-top: 8px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.kb-filter-row__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.kb-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 999px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
}
.kb-filter-chip span {
  color: #94a3b8;
  font-size: 12px;
}
.kb-filter-chip.is-active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}
.kb-filter-chip--tag,
.kb-filter-chip--recent {
  border-radius: 10px;
}
.kb-workbench__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  min-height: 640px;
  height: calc(100dvh - 154px);
  border: 1px solid #dbe5f0;
  border-radius: 12px;
  background: #f8fafc;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}
.kb-blank-state {
  padding: 56px 32px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.06);
  text-align: center;
}
.kb-blank-state h2 {
  margin: 0 0 12px;
  color: #24243f;
}
.kb-blank-state p {
  margin: 0 0 20px;
  color: #8f8a7d;
}
.kb-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 80;
}
.kb-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
}
.kb-modal {
  position: relative;
  z-index: 2;
  width: min(560px, calc(100vw - 24px));
  margin: 8vh auto 0;
  border-radius: 28px;
  background: #faf7f1;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.24);
}
.kb-modal--wide {
  width: min(860px, calc(100vw - 24px));
}
.kb-modal__header,
.kb-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 22px;
}
.kb-modal__header {
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}
.kb-modal__header h3 {
  margin: 0;
  color: #24243f;
  font-size: 22px;
}
.kb-modal__close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  cursor: pointer;
}
.kb-modal__body {
  padding: 22px;
  max-height: 70vh;
  overflow-y: auto;
}
.kb-modal__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.kb-modal__field span,
.kb-modal__field-label {
  color: #6b675d;
  font-size: 13px;
  font-weight: 600;
}
.kb-modal__field--inline {
  min-width: 140px;
  margin-bottom: 0;
}
.kb-modal__input {
  min-height: 44px;
  padding: 0 14px;
}
.kb-modal__textarea {
  min-height: 120px;
  padding: 12px 14px;
  resize: vertical;
}
.kb-modal__textarea--large {
  min-height: 220px;
}
.kb-modal__footer--inner {
  padding: 0;
  margin-top: 12px;
}
.kb-inline-tip {
  color: #8f8a7d;
  font-size: 12px;
}
.kb-import-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.kb-import-tabs--compact {
  grid-template-columns: repeat(3, minmax(0, 180px));
}
.kb-import-tab {
  padding: 14px 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  text-align: left;
  cursor: pointer;
}
.kb-import-tab strong {
  display: block;
  color: #24243f;
  font-size: 14px;
}
.kb-import-tab span {
  display: block;
  margin-top: 6px;
  color: #8f8a7d;
  font-size: 12px;
  line-height: 1.6;
}
.kb-import-tab.is-active {
  background: rgba(36, 36, 63, 0.08);
  border-color: rgba(36, 36, 63, 0.14);
}
.kb-import-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.06);
}
.kb-import-panel__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.kb-import-panel__hero h4 {
  margin: 0;
  color: #24243f;
}
.kb-import-panel__hero p {
  margin: 8px 0 0;
  color: #8f8a7d;
  line-height: 1.7;
}
.kb-import-panel__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.kb-import-panel__tags span {
  padding: 8px 12px;
  border-radius: 999px;
  background: #24243f;
  color: #f8f1e7;
  font-size: 12px;
}
.kb-import-actions {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}
.kb-import-actions__buttons {
  display: flex;
  gap: 10px;
}
.kb-progress {
  margin-top: 16px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(36, 36, 63, 0.05);
}
.kb-progress__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #4d4841;
  font-size: 13px;
}
.kb-progress__track {
  height: 8px;
  border-radius: 999px;
  background: rgba(36, 36, 63, 0.1);
  overflow: hidden;
}
.kb-progress__bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #5858a8 0%, #24243f 100%);
  transition: width 0.25s ease;
}
.kb-feedback-panel {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(15, 23, 42, 0.06);
  color: #5a544c;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kb-preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}
.kb-preview-card,
.kb-file-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(15, 23, 42, 0.06);
}
.kb-preview-card strong,
.kb-file-card strong {
  display: block;
  color: #24243f;
}
.kb-preview-card span,
.kb-file-card span {
  display: block;
  margin-top: 6px;
  color: #8f8a7d;
  font-size: 12px;
}
.kb-preview-card p {
  margin: 10px 0 0;
  color: #4e4a44;
  line-height: 1.7;
}
.kb-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.kb-choice-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}
.kb-choice-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  background: #fff;
  color: #3b3834;
  cursor: pointer;
}
.kb-choice-chip span {
  color: #8f8a7d;
}
.kb-choice-chip.is-active {
  background: #24243f;
  color: #f8f1e7;
  border-color: #24243f;
}
.kb-choice-chip.is-active span {
  color: rgba(248, 241, 231, 0.72);
}
.kb-upload-box {
  min-height: 190px;
  border: 1.5px dashed rgba(36, 36, 63, 0.22);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-align: center;
}
.kb-upload-box strong {
  color: #24243f;
}
.kb-upload-box span {
  margin-top: 8px;
  color: #8f8a7d;
  font-size: 13px;
}
.kb-file-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}
.kb-hidden-input {
  display: none;
}

@media (max-width: 1100px) {
  .kb-page-shell {
    display: block;
    height: auto;
    overflow: visible;
  }
  .kb-page-main {
    padding: 0;
    width: 100%;
    min-height: auto;
    height: auto;
    overflow: visible;
  }
  .kb-workbench {
    grid-template-columns: 1fr;
    min-height: auto;
    height: auto;
  }
  .kb-workbench__topbar,
  .kb-workbench__body {
    grid-template-columns: 1fr;
  }
  .kb-workbench__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .kb-filter-panel__search,
  .kb-filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .kb-filter-row__label {
    width: auto;
    padding-top: 0;
  }
  .kb-filter-grid {
    grid-template-columns: 1fr;
  }
  .kb-import-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .kb-import-actions__buttons {
    width: 100%;
  }
}

@media (max-width: 720px) {
  .kb-modal {
    margin-top: 4vh;
  }
  .kb-workbench__topbar {
    padding: 18px 16px 14px;
  }
  .kb-filter-panel {
    padding: 14px 16px;
  }
  .kb-workbench__controls,
  .kb-workbench__stats {
    grid-template-columns: 1fr;
  }
  .kb-filter-panel__search,
  .kb-filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .kb-filter-row__label {
    width: auto;
    padding-top: 0;
  }
  .kb-workbench__actions {
    justify-content: stretch;
  }
  .kb-workbench__actions button {
    flex: 1 1 140px;
  }
  .kb-modal__header,
  .kb-modal__body,
  .kb-modal__footer {
    padding-left: 16px;
    padding-right: 16px;
  }
  .kb-import-tabs,
  .kb-import-tabs--compact {
    grid-template-columns: 1fr;
  }
  .kb-file-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
