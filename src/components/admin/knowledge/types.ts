export interface EmbeddingProfile {
  id: number
  name: string
  quantization?: string
}

export interface KnowledgeBaseItem {
  id: number
  kind: 'knowledge_base' | 'dataset' | 'document'
  parent_knowledge_base?: number | null
  content: string
  metadata: Record<string, any>
  name?: string
  status: string
  documents_count?: number
  datasets_count?: number
  embedding_profile?: number | { id: number; name: string } | null
  created_at: string
  updated_at: string
}

export interface LegacyOption {
  value: string
  count: number
}

export interface LegacyPreviewItem {
  id: number
  name: string
  city: string
  category: string
  business_type?: string
  source_type: string
  preview: string
  created_at: string
}

export interface WorkspaceStats {
  knowledge_base_status: string
  dataset_count: number
  document_count: number
  pending_count: number
  active_count: number
  rejected_count: number
  category: string
}

export interface WorkspaceFacets {
  categories: LegacyOption[]
  tags: LegacyOption[]
  statuses: LegacyOption[]
}

export interface WorkspaceResponse {
  knowledge_bases: KnowledgeBaseItem[]
  knowledge_base: KnowledgeBaseItem | null
  datasets: KnowledgeBaseItem[]
  facets: WorkspaceFacets
  stats: WorkspaceStats
  active_dataset: KnowledgeBaseItem | null
  documents: KnowledgeBaseItem[]
}
