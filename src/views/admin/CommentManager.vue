<template>
  <div class="h-full flex flex-col">
    <!-- 顶部标题与工具栏 -->
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">评论管理</h1>
        <div class="text-sm text-slate-500 mt-1">管理全站用户发布的评论内容</div>
      </div>
      <div class="flex items-center gap-3 relative">
        <button 
          @click="showFilter = !showFilter"
          class="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-2"
          :class="{'bg-slate-50 ring-2 ring-slate-200': showFilter}"
        >
          <Filter class="w-4 h-4" />
          筛选
        </button>

        <!-- Filter Dropdown -->
        <div v-if="showFilter" class="absolute top-full right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-100 p-5 z-20">
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1.5">用户昵称</label>
              <input 
                v-model="filterForm.username" 
                type="text" 
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                placeholder="输入用户昵称..."
              />
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-500 mb-1.5">开始日期</label>
                <input 
                  v-model="filterForm.dateStart" 
                  type="date" 
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-500 mb-1.5">结束日期</label>
                <input 
                  v-model="filterForm.dateEnd" 
                  type="date" 
                  class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1.5">状态</label>
              <select 
                v-model="filterForm.status" 
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10 appearance-none"
              >
                <option value="all">全部</option>
                <option value="normal">正常</option>
                <option value="deleted">已删除</option>
              </select>
            </div>

            <div class="flex items-center gap-2 pt-2">
              <button 
                @click="resetFilter"
                class="flex-1 px-3 py-2 text-sm font-medium text-slate-600 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
              >
                重置
              </button>
              <button 
                @click="applyFilter"
                class="flex-1 px-3 py-2 text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
              >
                应用筛选
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表卡片 -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm flex-1 flex flex-col min-h-0">
      <!-- 搜索栏 -->
      <div class="p-4 border-b border-slate-100 flex items-center justify-between gap-4">
        <div class="relative flex-1 max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            v-model="kw" 
            type="text" 
            placeholder="搜索评论内容..." 
            class="w-full pl-9 pr-4 py-2 bg-slate-50 border-none rounded-lg text-sm focus:ring-1 focus:ring-slate-200 placeholder:text-slate-400 transition-all"
            @keyup.enter="load(1)"
          />
        </div>
        <div class="flex items-center gap-2">
          <button @click="load(1)" class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </button>
        </div>
      </div>

      <!-- 表格区域 -->
      <div class="overflow-auto flex-1">
        <table class="w-full text-left border-collapse">
          <thead class="bg-slate-50 sticky top-0 z-10">
            <tr>
              <th class="w-12 px-4 py-3 border-b border-slate-200">
                <div class="flex items-center justify-center">
                  <input type="checkbox" class="w-4 h-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900/20" />
                </div>
              </th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider w-1/4">用户</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider w-1/2">评论内容</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">发布时间</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading && list.length === 0">
              <td colspan="5" class="px-6 py-12 text-center text-slate-500 text-sm">加载中...</td>
            </tr>
            <tr v-else-if="list.length === 0">
              <td colspan="5" class="px-6 py-12 text-center text-slate-500 text-sm">暂无数据</td>
            </tr>
            <tr v-for="row in list" :key="row.id" class="group hover:bg-slate-50/50 transition-colors">
              <td class="px-4 py-4 w-12">
                <div class="flex items-center justify-center">
                  <input type="checkbox" class="w-4 h-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900/20" />
                </div>
              </td>
              <td class="px-4 py-4 align-top">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 overflow-hidden flex-shrink-0">
                    <img v-if="row.profiles?.avatar_url" :src="row.profiles.avatar_url" class="w-full h-full object-cover" />
                    <span v-else>{{ (row.profiles?.username?.[0] || 'U').toUpperCase() }}</span>
                  </div>
                  <div class="min-w-0">
                    <div class="text-sm font-medium text-slate-900 truncate">{{ row.profiles?.username || '未知用户' }}</div>
                    <div class="text-xs text-slate-500 font-mono truncate">ID: #{{ row.user_id.slice(0, 6) }}</div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4 align-top">
                <div class="text-sm text-slate-700 break-words line-clamp-3 hover:line-clamp-none transition-all duration-200">
                  <span v-if="row.is_deleted" class="text-red-500 font-bold mr-2">[已删除]</span>
                  <span :class="{'text-slate-400': row.is_deleted}">{{ row.content }}</span>
                </div>
                <div class="mt-1 text-xs text-slate-400">
                  关联帖子 ID: {{ row.post_id }} <span v-if="row.parent_id" class="ml-2 bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">回复</span>
                  <span v-if="row.is_deleted" class="ml-2 text-red-400">删除时间: {{ formatTime(row.deleted_at) }}</span>
                </div>
              </td>
              <td class="px-4 py-4 align-top whitespace-nowrap">
                <div class="flex items-center gap-2 text-sm text-slate-500">
                  <Calendar class="w-3.5 h-3.5" />
                  {{ formatDate(row.created_at) }}
                </div>
                <div class="text-xs text-slate-400 mt-1 pl-5.5">
                  {{ formatTime(row.created_at) }}
                </div>
              </td>
              <td class="px-4 py-4 align-top text-right">
                <button 
                  @click="deleteComment(row)"
                  class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="删除评论"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="p-4 border-t border-slate-100 flex items-center justify-between bg-white rounded-b-xl">
        <div class="text-sm text-slate-500">
          显示 {{ (page - 1) * 20 + 1 }}-{{ Math.min(page * 20, total) }} 条，共 {{ total }} 条
        </div>
        <div class="flex items-center gap-1">
          <button 
            @click="load(page - 1)" 
            :disabled="page <= 1"
            class="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <div class="flex items-center gap-1 px-2">
            <button class="w-8 h-8 flex items-center justify-center rounded-lg bg-slate-900 text-white text-sm font-medium">{{ page }}</button>
          </div>
          <button 
            @click="load(page + 1)" 
            :disabled="page * 20 >= total"
            class="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { supabase } from '@/utils/supabase'
import { apiUrl } from '@/utils/apiBase'
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Trash2,
  Calendar,
  ChevronLeft,
  ChevronRight
} from 'lucide-vue-next'

type CommentRow = { 
  id: number; 
  post_id: number;
  user_id: string;
  parent_id: number | null;
  content: string;
  created_at: string;
  is_deleted?: boolean;
  deleted_at?: string;
  profiles: {
    username: string;
    avatar_url: string;
  } | null;
}

const kw = ref('')
const list = ref<CommentRow[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

const showFilter = ref(false)
const filterForm = reactive({
  username: '',
  dateStart: '',
  dateEnd: '',
  status: 'all'
})

const applyFilter = () => {
  showFilter.value = false
  load(1)
}

const resetFilter = () => {
  filterForm.username = ''
  filterForm.dateStart = ''
  filterForm.dateEnd = ''
  filterForm.status = 'all'
  load(1)
}

const formatDate = (str?: string) => {
  if (!str) return '-'
  return new Date(str).toLocaleDateString()
}

const formatTime = (str?: string) => {
  if (!str) return ''
  return new Date(str).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const authHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) throw new Error('鐧诲綍鐘舵€佸凡杩囨湡锛岃閲嶆柊鐧诲綍')
  return {
    Authorization: `Bearer ${session.access_token}`,
  }
}

const load = async (p = 1) => {
  loading.value = true
  page.value = p
  
  try {
    // Get Data
    let query = supabase
      .from('comments')
      .select(`
        id,
        post_id,
        user_id,
        parent_id,
        content,
        created_at,
        is_deleted,
        deleted_at,
        profiles!inner (
          username,
          avatar_url
        )
      `)
      .order('created_at', { ascending: false })
      .range((p - 1) * 20, p * 20 - 1)

    if (kw.value) {
      query = query.ilike('content', `%${kw.value}%`)
    }

    // Apply Filters
    if (filterForm.username) {
      query = query.ilike('profiles.username', `%${filterForm.username}%`)
    }

    if (filterForm.dateStart) {
      query = query.gte('created_at', filterForm.dateStart)
    }

    if (filterForm.dateEnd) {
       query = query.lte('created_at', `${filterForm.dateEnd}T23:59:59`)
    }

    if (filterForm.status === 'deleted') {
      query = query.eq('is_deleted', true)
    } else if (filterForm.status === 'normal') {
      query = query.eq('is_deleted', false)
    }
    
    const { data, error } = await query
    
    if (error) throw error
    
    // Supabase returns array for joined relation even if one-to-one sometimes, 
    // but usually object if foreign key is correct. Let's handle it safely.
    list.value = (data || []).map((item: any) => ({
      ...item,
      profiles: Array.isArray(item.profiles) ? item.profiles[0] : item.profiles
    })) as CommentRow[]

    // Get Total
    // If username filter is active, we must join profiles to filter count correctly
    let countQuery = supabase.from('comments')
      .select(filterForm.username ? 'id, profiles!inner(username)' : 'id', { count: 'exact', head: true })

    if (kw.value) {
      countQuery = countQuery.ilike('content', `%${kw.value}%`)
    }

    if (filterForm.username) {
      countQuery = countQuery.ilike('profiles.username', `%${filterForm.username}%`)
    }

    if (filterForm.dateStart) {
      countQuery = countQuery.gte('created_at', filterForm.dateStart)
    }

    if (filterForm.dateEnd) {
       countQuery = countQuery.lte('created_at', `${filterForm.dateEnd}T23:59:59`)
    }

    if (filterForm.status === 'deleted') {
      countQuery = countQuery.eq('is_deleted', true)
    } else if (filterForm.status === 'normal') {
      countQuery = countQuery.eq('is_deleted', false)
    }

    const { count } = await countQuery
    if (count !== null) total.value = count

  } catch (err) {
    console.error('Load comments error:', err)
  } finally {
    loading.value = false
  }
}

const deleteComment = async (row: CommentRow) => {
  if (!confirm('确定要彻底删除这条评论吗？此操作不可恢复。')) return

  try {
    const response = await fetch(apiUrl(`/api/community/comments/${row.id}/`), {
      method: 'DELETE',
      headers: await authHeaders(),
    })
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || `Delete failed: ${response.status}`)
    }
    
    // Remove from local list
    const index = list.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      list.value.splice(index, 1)
      total.value--
    }
  } catch (err: any) {
    alert('删除失败: ' + err.message)
    console.error(err)
  }
}

onMounted(() => {
  load(1)
})
</script>
