<template>
  <div class="qa-test-page">
    <aside class="qa-agent-sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
      <div class="qa-agent-sidebar-inner" :class="{ 'is-hidden': sidebarCollapsed }">
        <div class="qa-agent-sidebar-top">
          <button class="qa-new-chat-btn" @click="handleNewChat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>开启新对话</span>
          </button>
        </div>

        <div class="qa-agent-group">
          <button class="qa-agent-item" type="button" @click="agentSectionExpanded = !agentSectionExpanded">
            <span class="qa-agent-item-icon qa-agent-item-icon--purple"></span>
            <span class="qa-agent-item-text">超级智能体</span>
            <svg class="qa-agent-chevron" :class="{ 'is-open': agentSectionExpanded }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>

          <div v-if="agentSectionExpanded" class="qa-agent-children">
            <button
              class="qa-agent-subitem"
              :class="{ 'is-active': activeSidebarItem === 'knowledge-bases' }"
              type="button"
              @click="selectSidebarItem('knowledge-bases')"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M3 12h18"></path>
                <path d="M12 3a15 15 0 0 1 4 9 15 15 0 0 1-4 9 15 15 0 0 1-4-9 15 15 0 0 1 4-9z"></path>
              </svg>
              <span>知识库</span>
            </button>
          </div>
        </div>

        <div class="qa-agent-group">
          <div class="qa-group-title">项目</div>
          <button
            class="qa-history-item"
            :class="{ 'is-selected': activeSidebarItem === 'project-rag' }"
            type="button"
            @click="selectSidebarItem('project-rag')"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>RAG 知识库测试</span>
          </button>
        </div>

        <div class="qa-agent-group qa-agent-group--fill">
          <div class="qa-group-title">历史记录</div>
          <button
            v-for="session in displaySessions"
            :key="session.id"
            class="qa-history-item"
            :class="{ 'is-selected': activeHistoryId === session.id }"
            type="button"
            @click="handleSelectSession(session.id)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>{{ session.title || '未命名测试' }}</span>
          </button>
          <div v-if="!sessions.length" class="qa-empty-sidebar">暂无测试记录</div>
        </div>
      </div>
    </aside>

    <main class="qa-main">
      <div class="qa-topbar">
        <div v-if="sidebarCollapsed" class="qa-topbar-compact">
          <button class="qa-topbar-btn" type="button" title="开启新对话" @click="handleNewChat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
          <span class="qa-topbar-divider"></span>
          <button class="qa-topbar-btn" type="button" title="打开侧边栏" @click="toggleSidebar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"></rect>
              <line x1="9" y1="3" x2="9" y2="21"></line>
            </svg>
          </button>
        </div>

        <button v-else class="qa-collapse-btn" type="button" title="关闭侧边栏" @click="toggleSidebar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
          </svg>
        </button>
      </div>

      <div class="qa-content">
        <div class="qa-stage" :class="{ 'has-result': !!result }">
          <div class="qa-hero">
            <h1>椿天社</h1>
            <p>期待与你相遇</p>
          </div>

          <div class="qa-input-card">
            <div class="qa-textarea-wrap">
              <textarea
                v-model="query"
                class="qa-textarea"
                placeholder="输入管理员测试问题，验证知识库与模型效果..."
                @keydown.enter.exact.prevent="handleSearch"
              ></textarea>

              <div class="qa-agent-mode">
                <span>管理员测试模式</span>
                <button class="qa-switch" type="button" :class="{ 'is-on': true }">
                  <span></span>
                </button>
              </div>
            </div>

            <div class="qa-control-row">
              <select v-model="selectedProviderId" class="qa-select">
                <option value="">选择模型提供方</option>
                <option v-for="provider in providerOptions" :key="provider.id" :value="provider.id">
                  {{ provider.name }}
                </option>
              </select>

              <select v-model="mode" class="qa-select">
                <option value="normal">标准问答</option>
                <option value="analysis">深度分析</option>
                <option value="summary">快速总结</option>
              </select>

              <div class="qa-kb-select" data-kb-dropdown>
                <button class="qa-kb-trigger" type="button" @click.stop="showKBDropdown = !showKBDropdown">
                  <span>{{ selectedKBName }}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>

                <div v-if="showKBDropdown" class="qa-kb-dropdown-menu">
                  <button class="qa-kb-option" type="button" @click="clearKBSelection">全部知识库</button>
                  <button
                    v-for="kb in knowledgeBases"
                    :key="kb.id"
                    class="qa-kb-option"
                    type="button"
                    @click="selectKB(kb)"
                  >
                    <span>{{ kb.metadata?.name || `知识库 ${kb.id}` }}</span>
                    <span class="qa-kb-status">{{ kbStatusLabel(kb.status) }}</span>
                  </button>
                </div>
              </div>

              <div class="qa-web-search">
                <span>联网搜索</span>
                <span class="qa-status-dot"></span>
                <button class="qa-switch" type="button" :class="{ 'is-on': webSearch }" @click="webSearch = !webSearch">
                  <span></span>
                </button>
              </div>
            </div>

            <div class="qa-footer-row">
              <div class="qa-footer-meta">
                <span class="qa-meta-chip"><span class="qa-meta-label">会话</span><span class="qa-meta-value">{{ currentSession ? `#${currentSession.id}` : '新会话' }}</span></span>
                <span class="qa-meta-chip" :title="selectedProviderName || '未选择模型'"><span class="qa-meta-label">模型</span><span class="qa-meta-value">{{ selectedProviderName || '未选择模型' }}</span></span>
                <span class="qa-meta-chip" :title="selectedKBName"><span class="qa-meta-label">范围</span><span class="qa-meta-value">{{ selectedKBName }}</span></span>
                <span class="qa-meta-chip"><span class="qa-meta-label">发布</span><span class="qa-meta-value">{{ currentKBStatusText }}</span></span>
              </div>

              <button class="qa-submit-btn" type="button" :disabled="isSearching || !query.trim()" @click="handleSearch">
                <span>{{ isSearching ? '测试中...' : '开始测试' }}</span>
                <svg v-if="!isSearching" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
                </svg>
              </button>
            </div>

            <div class="qa-release-tip" :class="`is-${currentKnowledgeBase?.status || 'empty'}`">
              {{ currentKBReleaseHint }}
            </div>
          </div>

          <div v-if="result" class="qa-result-card">
            <section class="qa-result-section qa-result-toolbar">
              <div class="qa-toolbar-left">
                <span class="qa-state-badge" :class="`is-${result.status}`">{{ qaStatusLabel(result.status) }}</span>
                <span class="qa-toolbar-text">耗时 {{ result.latency_ms }} ms</span>
                <span class="qa-toolbar-text">模型 {{ result.model_name || '未选择' }}</span>
                <span class="qa-toolbar-text">知识库 {{ result.knowledge_base_name || '全部知识库' }}</span>
                <span class="qa-toolbar-text">用户侧 {{ result.release_enabled ? '已启用' : '未启用' }}</span>
              </div>
              <div class="qa-toolbar-actions">
                <button class="qa-action-btn qa-action-btn--success" type="button" :disabled="!canApproveCurrentSession || approving" @click="handleApprove">
                  {{ approving ? '启用中...' : '测试通过并启用' }}
                </button>
                <button class="qa-action-btn qa-action-btn--danger" type="button" :disabled="!currentSession || rejecting" @click="handleReject">
                  {{ rejecting ? '处理中...' : '标记未通过' }}
                </button>
              </div>
            </section>

            <section class="qa-result-section qa-result-section--bordered">
              <div class="qa-result-title">
                <span class="qa-result-icon qa-result-icon--blue">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                </span>
                <span>测试问题</span>
              </div>
              <p class="qa-result-text">{{ result.question }}</p>
            </section>

            <section class="qa-result-section qa-result-section--bordered">
              <div class="qa-result-title">
                <span class="qa-result-icon qa-result-icon--green">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </span>
                <span>系统回答</span>
              </div>
              <div class="qa-result-text qa-result-answer">{{ result.answer }}</div>
            </section>

            <section class="qa-result-section qa-result-section--bordered">
              <div class="qa-result-title">
                <span class="qa-result-icon qa-result-icon--amber">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
                </span>
                <span>引用与来源</span>
              </div>

              <div class="qa-source-list">
                <span v-for="(source, idx) in result.sources" :key="idx" class="qa-source-chip">{{ source }}</span>
              </div>

              <div v-if="result.citations.length" class="qa-citation-list">
                <div class="qa-citation-title">检索切片</div>
                <div v-for="(citation, idx) in result.citations" :key="idx" class="qa-citation-card">
                  <div class="qa-citation-content">{{ citation.content }}</div>
                  <a v-if="citation.url" :href="citation.url" target="_blank" class="qa-citation-link">
                    {{ citation.source || citation.url }}
                  </a>
                  <div v-else class="qa-citation-link qa-citation-link--muted">{{ citation.source }}</div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { AdminQATestSession } from '@/services/adminQATestService'
import { adminQATestService } from '@/services/adminQATestService'
import { apiUrl } from '@/utils/apiBase'

interface KnowledgeBase {
  id: number
  content: string
  metadata: Record<string, any>
  status?: string
}

interface ProviderOption {
  id: string
  name: string
  model_name: string
}

interface SearchResult {
  question: string
  answer: string
  sources: string[]
  citations: Array<{
    content: string
    source: string
    url: string
  }>
  latency_ms: number
  provider_name: string
  model_name: string
  knowledge_base_name: string
  status: 'draft' | 'passed' | 'failed'
  release_enabled: boolean
  knowledge_base_status?: string
}

const sidebarCollapsed = ref(true)
const agentSectionExpanded = ref(true)
const activeSidebarItem = ref<string | null>(null)
const activeHistoryId = ref<number | null>(null)

const query = ref('')
const isSearching = ref(false)
const approving = ref(false)
const rejecting = ref(false)
const result = ref<SearchResult | null>(null)

const webSearch = ref(false)
const mode = ref('normal')
const showKBDropdown = ref(false)
const selectedKB = ref<KnowledgeBase | null>(null)
const selectedProviderId = ref('')

const sessions = ref<AdminQATestSession[]>([])
const currentSessionId = ref<number | null>(null)
const knowledgeBases = ref<KnowledgeBase[]>([])
const providerOptions = ref<ProviderOption[]>([])

const currentSession = computed(() => sessions.value.find(item => item.id === currentSessionId.value) || null)
const displaySessions = computed(() => sessions.value.slice(0, 40))
const selectedProvider = computed(() => providerOptions.value.find(item => item.id === selectedProviderId.value) || null)
const selectedProviderName = computed(() => selectedProvider.value?.name || '')
const selectedKBName = computed(() => selectedKB.value?.metadata?.name || '全部知识库')
const currentKnowledgeBase = computed(() => {
  const knowledgeBaseId = currentSession.value?.knowledge_base || selectedKB.value?.id
  if (!knowledgeBaseId) return selectedKB.value
  return knowledgeBases.value.find(item => item.id === knowledgeBaseId) || selectedKB.value
})
const currentKBStatusText = computed(() => currentKnowledgeBase.value ? kbStatusLabel(currentKnowledgeBase.value.status) : '未选择知识库')
const currentKBReleaseHint = computed(() => {
  if (!currentKnowledgeBase.value) return '未选择知识库，本次测试只能验证模型回答，不能直接发布给用户。'
  if (currentKnowledgeBase.value.status === 'active') return '该知识库当前已启用给用户；如资料刚调整，建议重新测试确认。'
  if (currentKnowledgeBase.value.status === 'pending_review') return '该知识库仍处于待测试状态，只有管理员测试通过后才会对用户开放。'
  if (currentKnowledgeBase.value.status === 'rejected') return '该知识库上次测试未通过，修正资料后需要重新测试并再次启用。'
  return '该知识库当前未处于可发布状态，请先完成测试审核。'
})
const canApproveCurrentSession = computed(() => !!currentSession.value && !!currentSession.value.knowledge_base && !!result.value?.answer?.trim())

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const selectSidebarItem = (item: string) => {
  activeSidebarItem.value = activeSidebarItem.value === item ? null : item
  activeHistoryId.value = null
}

const handleNewChat = () => {
  currentSessionId.value = null
  activeHistoryId.value = null
  query.value = ''
  result.value = null
}

const isRealKnowledgeBase = (item: KnowledgeBase) => {
  const metadata = item.metadata || {}
  if (metadata.record_type === 'knowledge_base') return true
  return !metadata.source
}

const kbStatusLabel = (status?: string) => {
  if (status === 'active') return '已启用'
  if (status === 'pending_review') return '待测试'
  if (status === 'rejected') return '未通过'
  if (status === 'archived') return '已归档'
  return '未知'
}

const qaStatusLabel = (status?: string) => {
  if (status === 'passed') return '已通过'
  if (status === 'failed') return '未通过'
  return '待验证'
}

const clearKBSelection = () => {
  selectedKB.value = null
  showKBDropdown.value = false
}

const selectKB = (kb: KnowledgeBase) => {
  selectedKB.value = kb
  showKBDropdown.value = false
}

const syncSelectedKnowledgeBase = () => {
  if (currentSession.value?.knowledge_base) {
    selectedKB.value = knowledgeBases.value.find(item => item.id === currentSession.value?.knowledge_base) || selectedKB.value
    return
  }
  if (selectedKB.value) {
    selectedKB.value = knowledgeBases.value.find(item => item.id === selectedKB.value?.id) || selectedKB.value
  }
}

const fetchKnowledgeBases = async () => {
  const response = await fetch(apiUrl('/api/knowledge/?source=local&page_size=500'))
  if (!response.ok) throw new Error('获取知识库失败')
  const data = await response.json()
  const items = Array.isArray(data) ? data : data.results || []
  knowledgeBases.value = items.filter((item: KnowledgeBase) => item.status !== 'archived' && isRealKnowledgeBase(item))
  syncSelectedKnowledgeBase()
}

const fetchProviders = async () => {
  const response = await fetch(apiUrl('/api/api-providers/public/?capability=chat&all=1'))
  if (!response.ok) throw new Error('获取模型配置失败')
  const data = await response.json()
  providerOptions.value = (data.data || []).map((item: any) => ({
    id: String(item.id),
    name: item.name,
    model_name: item.config?.model_id || item.name
  }))
  if (!selectedProviderId.value && providerOptions.value.length) {
    selectedProviderId.value = providerOptions.value[0].id
  }
}

const fetchSessions = async () => {
  sessions.value = await adminQATestService.listSessions()
}

const findLatestMessageByRole = (session: AdminQATestSession, role: 'user' | 'assistant') => {
  for (let index = session.messages.length - 1; index >= 0; index -= 1) {
    const message = session.messages[index]
    if (message.role === role) return message
  }
  return null
}

const hydrateResultFromSession = (session: AdminQATestSession) => {
  const assistantMessage = findLatestMessageByRole(session, 'assistant')
  const latestUserMessage = findLatestMessageByRole(session, 'user')
  if (!assistantMessage && !session.latest_answer) {
    result.value = null
    return
  }

  result.value = {
    question: session.latest_question || latestUserMessage?.content || '',
    answer: assistantMessage?.content || session.latest_answer,
    sources: assistantMessage?.sources || [],
    citations: assistantMessage?.citations || [],
    latency_ms: assistantMessage?.latency_ms || session.latest_latency_ms || 0,
    provider_name: session.provider_name,
    model_name: session.model_name,
    knowledge_base_name: session.knowledge_base_name,
    status: session.status,
    release_enabled: session.release_enabled
  }
}

const handleSelectSession = async (sessionId: number) => {
  activeHistoryId.value = activeHistoryId.value === sessionId ? null : sessionId
  if (!activeHistoryId.value) {
    currentSessionId.value = null
    result.value = null
    return
  }

  const session = await adminQATestService.getSession(sessionId)
  currentSessionId.value = session.id
  activeSidebarItem.value = null
  query.value = session.latest_question || ''
  selectedProviderId.value = session.provider_id || selectedProviderId.value
  mode.value = session.mode || 'normal'
  webSearch.value = !!session.use_web_search
  selectedKB.value = knowledgeBases.value.find(item => item.id === session.knowledge_base) || null

  const index = sessions.value.findIndex(item => item.id === session.id)
  if (index >= 0) {
    sessions.value[index] = session
  } else {
    sessions.value.unshift(session)
  }

  hydrateResultFromSession(session)
}

const ensureSession = async () => {
  if (currentSessionId.value) return currentSessionId.value

  const session = await adminQATestService.createSession({
    title: query.value.trim().slice(0, 20) || '新建测试',
    knowledge_base: selectedKB.value?.id || null,
    provider_id: selectedProviderId.value,
    provider_name: selectedProvider.value?.name || '',
    model_name: selectedProvider.value?.model_name || '',
    mode: mode.value,
    use_web_search: webSearch.value,
    latest_question: query.value.trim()
  })

  currentSessionId.value = session.id
  activeHistoryId.value = session.id
  sessions.value.unshift(session)
  return session.id
}

const handleSearch = async () => {
  const question = query.value.trim()
  if (!question || isSearching.value) return

  isSearching.value = true
  try {
    const sessionId = await ensureSession()
    const response = await adminQATestService.chat(sessionId, {
      question,
      knowledge_base_id: selectedKB.value?.id || null,
      provider_id: selectedProviderId.value,
      provider_name: selectedProvider.value?.name || '',
      model_name: selectedProvider.value?.model_name || '',
      mode: mode.value,
      use_web_search: webSearch.value
    })

    const session = response.session
    currentSessionId.value = session.id
    activeHistoryId.value = session.id
    const index = sessions.value.findIndex(item => item.id === session.id)
    if (index >= 0) {
      sessions.value[index] = session
    } else {
      sessions.value.unshift(session)
    }

    result.value = response.result
  } catch (error) {
    console.error('QA test failed:', error)
    result.value = {
      question,
      answer: error instanceof Error ? error.message : '测试失败，请稍后重试。',
      sources: [],
      citations: [],
      latency_ms: 0,
      provider_name: selectedProvider.value?.name || '',
      model_name: selectedProvider.value?.model_name || '',
      knowledge_base_name: selectedKBName.value,
      status: 'failed',
      release_enabled: false
    }
  } finally {
    isSearching.value = false
  }
}

const handleApprove = async () => {
  if (!currentSession.value || approving.value) return
  approving.value = true
  try {
    const session = await adminQATestService.approve(currentSession.value.id)
    const index = sessions.value.findIndex(item => item.id === session.id)
    if (index >= 0) sessions.value[index] = session
    currentSessionId.value = session.id
    hydrateResultFromSession(session)
    if (result.value) {
      result.value.status = session.status
      result.value.release_enabled = session.release_enabled
    }
    await fetchKnowledgeBases()
  } catch (error) {
    console.error('Approve QA test failed:', error)
    window.alert(error instanceof Error ? error.message : '启用失败，请稍后重试。')
  } finally {
    approving.value = false
  }
}

const handleReject = async () => {
  if (!currentSession.value || rejecting.value) return
  rejecting.value = true
  try {
    const session = await adminQATestService.reject(currentSession.value.id)
    const index = sessions.value.findIndex(item => item.id === session.id)
    if (index >= 0) sessions.value[index] = session
    currentSessionId.value = session.id
    hydrateResultFromSession(session)
    if (result.value) {
      result.value.status = session.status
      result.value.release_enabled = session.release_enabled
    }
    await fetchKnowledgeBases()
  } catch (error) {
    console.error('Reject QA test failed:', error)
    window.alert(error instanceof Error ? error.message : '标记未通过失败，请稍后重试。')
  } finally {
    rejecting.value = false
  }
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('[data-kb-dropdown]')) {
    showKBDropdown.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await Promise.all([fetchKnowledgeBases(), fetchProviders(), fetchSessions()])
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.qa-test-page { display: flex; height: calc(100vh - 4rem); background: #f6f7fb; }
.qa-agent-sidebar { width: 208px; flex-shrink: 0; overflow: hidden; background: #fff; border-right: 1px solid #edf0f5; transition: width .22s ease, border-color .22s ease; contain: layout paint; }
.qa-agent-sidebar.is-collapsed { width: 0; border-right-color: transparent; }
.qa-agent-sidebar-inner { display: flex; width: 208px; height: 100%; flex-direction: column; padding: 16px 12px 20px; opacity: 1; transition: opacity .16s ease; }
.qa-agent-sidebar-inner.is-hidden { opacity: 0; pointer-events: none; }
.qa-agent-sidebar-top { margin: 10px 0 14px; }
.qa-new-chat-btn { display: flex; width: 100%; align-items: center; justify-content: center; gap: 8px; border: 1px solid #e6eaf2; border-radius: 9999px; background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%); color: #182230; padding: 10px 14px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 14px rgba(15,23,42,.05); cursor: pointer; transition: border-color .18s ease, background .18s ease, transform .18s ease, color .18s ease; }
.qa-new-chat-btn:hover { border-color: #d7deea; background: #fff; transform: translateY(-1px); }
.qa-agent-group { margin-bottom: 12px; }
.qa-agent-group--fill { flex: 1; overflow-y: auto; }
.qa-group-title { margin-bottom: 8px; padding-left: 10px; color: #98a2b3; font-size: 11px; font-weight: 600; letter-spacing: .02em; }
.qa-agent-item,.qa-agent-subitem,.qa-history-item { display: flex; width: 100%; align-items: center; justify-content: flex-start; gap: 10px; border: 1px solid transparent; border-radius: 10px; background: transparent; color: #475467; padding: 8px 10px; font-size: 13px; line-height: 1.4; text-align: left; cursor: pointer; transition: background .18s ease, border-color .18s ease, color .18s ease; }
.qa-agent-item { color: #101828; font-weight: 600; padding-block: 8px; }
.qa-agent-item-text,.qa-agent-subitem span,.qa-history-item span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.qa-agent-item-icon { width: 8px; height: 8px; border-radius: 9999px; }
.qa-agent-item-icon--purple { background: #8b5cf6; }
.qa-agent-chevron { margin-left: auto; color: #98a2b3; transition: transform .2s ease; }
.qa-agent-chevron.is-open { transform: rotate(90deg); }
.qa-agent-children { margin-top: 4px; padding-left: 0; }
.qa-agent-subitem { padding-left: 20px; }
.qa-agent-item:hover,.qa-agent-subitem:hover,.qa-history-item:hover { background: #f8fafc; color: #111827; }
.qa-agent-subitem.is-active,.qa-history-item.is-selected { background: #f5f7fb; border-color: #e7ebf3; color: #182230; }
.qa-empty-sidebar { padding: 8px 10px; color: #98a2b3; font-size: 13px; line-height: 1.5; }
.qa-main { display: flex; min-width: 0; flex: 1; flex-direction: column; overflow: hidden; }
.qa-topbar { position: relative; z-index: 2; height: 0; flex-shrink: 0; }
.qa-topbar-compact { position: absolute; top: 12px; left: 16px; display: inline-flex; align-items: center; overflow: hidden; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; box-shadow: 0 1px 2px rgba(15,23,42,.05); }
.qa-topbar-btn,.qa-collapse-btn { display: inline-flex; align-items: center; justify-content: center; border: none; background: #fff; color: #6b7280; cursor: pointer; }
.qa-topbar-btn { width: 34px; height: 30px; }
.qa-collapse-btn { position: absolute; top: 12px; left: 16px; width: 22px; height: 22px; border-radius: 6px; }
.qa-topbar-divider { width: 1px; height: 16px; background: #e5e7eb; }
.qa-content { flex: 1; overflow-y: auto; padding: 40px 32px 56px; }
.qa-stage { min-height: 100%; display: flex; flex-direction: column; justify-content: center; transform: translateY(-5vh); }
.qa-stage.has-result { justify-content: flex-start; transform: none; }
.qa-hero { margin-bottom: 22px; text-align: center; }
.qa-hero h1 { margin: 0 0 6px; color: #d92d20; font-size: clamp(30px, 4vw, 36px); font-weight: 700; line-height: 1.05; letter-spacing: .02em; font-family: 'PangMenZhengDao', serif; text-shadow: 0 2px 8px rgba(217,45,32,.08); }
.qa-hero p { margin: 0; color: #98a2b3; font-size: 13px; }
.qa-input-card,.qa-result-card { width: 100%; max-width: 920px; margin: 0 auto; background: #fff; border: 1px solid #edf0f5; border-radius: 18px; box-shadow: 0 8px 24px rgba(15,23,42,.05); }
.qa-input-card { padding: 16px; }
.qa-textarea-wrap { position: relative; margin-bottom: 12px; }
.qa-textarea { width: 100%; min-height: 124px; resize: vertical; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; padding: 16px; color: #111827; font-size: 14px; outline: none; }
.qa-agent-mode { position: absolute; top: 14px; right: 14px; display: flex; align-items: center; gap: 8px; color: #98a2b3; font-size: 10px; font-weight: 700; }
.qa-control-row,.qa-footer-row,.qa-result-toolbar { display: flex; align-items: center; gap: 10px; }
.qa-control-row { flex-wrap: wrap; }
.qa-footer-row { margin-top: 12px; justify-content: space-between; gap: 12px; }
.qa-footer-meta,.qa-toolbar-left,.qa-toolbar-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.qa-footer-meta { gap: 10px; }
.qa-meta-chip,.qa-toolbar-text,.qa-state-badge { border-radius: 9999px; background: #f8fafc; padding: 6px 10px; color: #64748b; font-size: 12px; border: 1px solid #eef2f6; }
.qa-meta-chip { display: inline-flex; align-items: center; min-height: 32px; max-width: 240px; }
.qa-meta-label { color: #98a2b3; margin-right: 6px; }
.qa-meta-value { color: #344054; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.qa-release-tip { margin-top: 12px; border-radius: 14px; border: 1px solid #eef2f6; background: #f8fafc; padding: 12px 14px; color: #475467; font-size: 13px; line-height: 1.6; }
.qa-release-tip.is-active { border-color: #bbf7d0; background: #f0fdf4; color: #166534; }
.qa-release-tip.is-pending_review { border-color: #fde68a; background: #fffbeb; color: #92400e; }
.qa-release-tip.is-rejected { border-color: #fecaca; background: #fef2f2; color: #b42318; }
.qa-release-tip.is-empty { border-style: dashed; color: #667085; }
.qa-state-badge.is-passed { background: #ecfdf3; color: #059669; }
.qa-state-badge.is-failed { background: #fef2f2; color: #dc2626; }
.qa-state-badge.is-draft { background: #eff6ff; color: #2563eb; }
.qa-select,.qa-kb-trigger { height: 38px; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; color: #344054; padding: 0 12px; font-size: 13px; outline: none; }
.qa-select { min-width: 160px; }
.qa-kb-select { position: relative; }
.qa-kb-trigger { display: flex; min-width: 180px; align-items: center; justify-content: space-between; gap: 8px; cursor: pointer; }
.qa-kb-dropdown-menu { position: absolute; top: calc(100% + 8px); left: 0; z-index: 10; min-width: 260px; max-height: 300px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; box-shadow: 0 12px 24px rgba(15,23,42,.12); padding: 8px; }
.qa-kb-option { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 8px; border: none; border-radius: 8px; background: transparent; color: #374151; padding: 9px 10px; text-align: left; font-size: 13px; cursor: pointer; }
.qa-kb-option:hover { background: #f8fafc; }
.qa-kb-status { color: #94a3b8; font-size: 11px; }
.qa-web-search { display: inline-flex; margin-left: auto; align-items: center; gap: 8px; color: #667085; font-size: 12px; }
.qa-status-dot { width: 6px; height: 6px; border-radius: 9999px; background: #22c55e; }
.qa-switch { position: relative; width: 36px; height: 20px; border: none; border-radius: 9999px; background: #d1d5db; cursor: pointer; }
.qa-switch span { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 9999px; background: #fff; transition: transform .2s ease; }
.qa-switch.is-on { background: #93c5fd; }
.qa-switch.is-on span { transform: translateX(16px); }
.qa-submit-btn,.qa-action-btn { display: inline-flex; align-items: center; gap: 8px; border: none; border-radius: 10px; padding: 10px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qa-submit-btn { background: #7aa2ff; color: #fff; }
.qa-action-btn--success { background: #ecfdf3; color: #059669; }
.qa-action-btn--danger { background: #fef2f2; color: #dc2626; }
.qa-submit-btn:disabled,.qa-action-btn:disabled { opacity: .55; cursor: not-allowed; }
.qa-result-card { margin-top: 24px; overflow: hidden; }
.qa-result-section { padding: 22px 24px; }
.qa-result-section--bordered { border-top: 1px solid #f1f5f9; }
.qa-result-title { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #111827; font-size: 14px; font-weight: 700; }
.qa-result-icon { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border-radius: 8px; }
.qa-result-icon--blue { background: #3b82f6; }
.qa-result-icon--green { background: #10b981; }
.qa-result-icon--amber { background: #f59e0b; }
.qa-result-text { margin: 0; color: #374151; font-size: 14px; line-height: 1.8; }
.qa-result-answer { white-space: pre-wrap; }
.qa-source-list { display: flex; flex-wrap: wrap; gap: 8px; }
.qa-source-chip { display: inline-flex; align-items: center; border-radius: 9999px; background: #fef3c7; color: #92400e; padding: 6px 12px; font-size: 12px; }
.qa-citation-list { margin-top: 16px; }
.qa-citation-title { margin-bottom: 8px; color: #6b7280; font-size: 12px; font-weight: 700; }
.qa-citation-card { margin-bottom: 8px; border-radius: 10px; background: #f8fafc; padding: 10px 12px; }
.qa-citation-content { margin-bottom: 6px; color: #374151; font-size: 13px; line-height: 1.6; }
.qa-citation-link { color: #2563eb; font-size: 12px; text-decoration: none; }
.qa-citation-link--muted { color: #94a3b8; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.animate-spin { animation: spin 1s linear infinite; }
@media (max-width: 1200px) { .qa-agent-sidebar { position: absolute; z-index: 5; height: 100%; box-shadow: 8px 0 24px rgba(15,23,42,.08); } }
@media (max-width: 960px) {
  .qa-content { padding: 36px 16px 32px; }
  .qa-footer-row { align-items: flex-start; flex-direction: column; }
  .qa-web-search { margin-left: 0; }
}
</style>





