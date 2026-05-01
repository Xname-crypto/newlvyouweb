import { supabase } from '@/utils/supabase'

export interface AdminQATestMessage {
  id: number
  session: number
  role: 'user' | 'assistant'
  content: string
  sources: string[]
  citations: Array<{
    content: string
    source: string
    url: string
  }>
  latency_ms: number
  created_at: string
}

export interface AdminQATestSession {
  id: number
  admin_user_id: string
  title: string
  knowledge_base: number | null
  knowledge_base_name: string
  provider_id: string
  provider_name: string
  model_name: string
  mode: string
  use_web_search: boolean
  status: 'draft' | 'passed' | 'failed'
  release_enabled: boolean
  notes: string
  latest_question: string
  latest_answer: string
  latest_latency_ms: number
  created_at: string
  updated_at: string
  messages: AdminQATestMessage[]
}

interface RequestOptions extends RequestInit {
  body?: any
}

const request = async <T>(url: string, options: RequestOptions = {}): Promise<T> => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  if (!token) {
    throw new Error('未登录，无法访问管理员测试接口')
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {})
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `Request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const adminQATestService = {
  listSessions() {
    return request<AdminQATestSession[]>('/api/admin-qa-sessions/')
  },

  getSession(sessionId: number) {
    return request<AdminQATestSession>(`/api/admin-qa-sessions/${sessionId}/`)
  },

  createSession(payload: Partial<AdminQATestSession>) {
    return request<AdminQATestSession>('/api/admin-qa-sessions/', {
      method: 'POST',
      body: payload
    })
  },

  chat(sessionId: number, payload: Record<string, any>) {
    return request<{
      session: AdminQATestSession
      message: AdminQATestMessage
      result: {
        question: string
        answer: string
        sources: string[]
        citations: Array<{ content: string; source: string; url: string }>
        latency_ms: number
        provider_name: string
        model_name: string
        knowledge_base_name: string
        status: AdminQATestSession['status']
        release_enabled: boolean
      }
    }>(`/api/admin-qa-sessions/${sessionId}/chat/`, {
      method: 'POST',
      body: payload
    })
  },

  approve(sessionId: number, notes = '') {
    return request<AdminQATestSession>(`/api/admin-qa-sessions/${sessionId}/approve/`, {
      method: 'POST',
      body: { notes }
    })
  },

  reject(sessionId: number, notes = '') {
    return request<AdminQATestSession>(`/api/admin-qa-sessions/${sessionId}/reject/`, {
      method: 'POST',
      body: { notes, sync_kb_status: true }
    })
  }
}
