<template>
  <div class="h-full flex flex-col">
    <!-- 顶部标题与工具栏 -->
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">用户管理</h1>
        <div class="text-sm text-slate-500 mt-1">管理系统普通用户的账号与状态</div>
      </div>
      <div class="flex items-center gap-3">
        <button class="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-2">
          <Filter class="w-4 h-4" />
          筛选
        </button>
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
            placeholder="搜索用户..." 
            class="w-full pl-9 pr-4 py-2 bg-slate-50 border-none rounded-lg text-sm focus:ring-1 focus:ring-slate-200 placeholder:text-slate-400 transition-all"
            @keyup.enter="load(1)"
          />
        </div>
        <div class="flex items-center gap-2">
          <button @click="load(1)" class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </button>
          <button class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
            <MoreHorizontal class="w-4 h-4" />
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
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">用户</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">角色</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">职位</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">更新时间</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">状态</th>
              <th class="px-4 py-3 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading && list.length === 0">
              <td colspan="7" class="px-6 py-12 text-center text-slate-500 text-sm">加载中...</td>
            </tr>
            <tr v-else-if="list.length === 0">
              <td colspan="7" class="px-6 py-12 text-center text-slate-500 text-sm">暂无数据</td>
            </tr>
            <tr v-for="row in list" :key="row.id" class="group hover:bg-slate-50/50 transition-colors">
              <td class="px-4 py-4 w-12">
                <div class="flex items-center justify-center">
                  <input type="checkbox" class="w-4 h-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900/20" />
                </div>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500 overflow-hidden">
                    <img v-if="row.avatar_url" :src="row.avatar_url" class="w-full h-full object-cover" />
                    <span v-else>{{ (row.username?.[0] || 'U').toUpperCase() }}</span>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-slate-900">{{ row.username || '未命名用户' }}</div>
                    <div class="text-xs text-slate-500 font-mono">ID: #{{ row.id.slice(0, 6) }}</div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4">
                 <div class="relative inline-block text-left">
                  <select 
                    class="appearance-none bg-transparent py-1 pr-6 pl-0 text-sm font-medium focus:outline-none cursor-pointer hover:text-blue-600 transition-colors"
                    :class="row.role === 'banned' ? 'text-red-600' : 'text-slate-700'"
                    :value="row.role"
                    @change="changeRole(row, $event)"
                  >
                    <option value="user">普通用户</option>
                    <option value="banned" class="text-red-600 font-bold">已封禁</option>
                  </select>
                  <ChevronDown class="w-3 h-3 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </td>
              <td class="px-4 py-4">
                <div class="text-sm text-slate-600">{{ row.job || '-' }}</div>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center gap-2 text-sm text-slate-500">
                  <Calendar class="w-3.5 h-3.5" />
                  {{ formatDate(row.updated_at) }}
                </div>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full" :class="onlineUsers.has(row.id) ? 'bg-emerald-500' : 'bg-slate-300'"></div>
                  <span class="text-sm font-medium" :class="onlineUsers.has(row.id) ? 'text-emerald-700' : 'text-slate-500'">
                    {{ onlineUsers.has(row.id) ? 'Online' : 'Offline' }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-4 text-right">
                <div class="relative group/menu">
                  <button class="p-1.5 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
                    <MoreHorizontal class="w-4 h-4" />
                  </button>
                  
                  <!-- Dropdown Menu -->
                  <div class="absolute right-0 top-full pt-2 w-32 hidden group-hover/menu:block z-20">
                    <div class="bg-white rounded-lg shadow-lg border border-slate-100 py-1">
                      <button 
                        @click="changeRole(row, { target: { value: row.role === 'banned' ? 'user' : 'banned' } } as any)"
                        class="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 transition-colors"
                        :class="row.role === 'banned' ? 'text-green-600' : 'text-amber-600'"
                      >
                        {{ row.role === 'banned' ? '解封用户' : '封禁用户' }}
                      </button>
                      <button 
                        @click="deleteUser(row)"
                        class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                      >
                        删除用户
                      </button>
                    </div>
                  </div>
                </div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { supabase } from '@/utils/supabase'
import { RealtimeChannel } from '@supabase/supabase-js'
import { usePresence } from '@/composables/usePresence'
import { 
  Search, 
  Filter, 
  Plus,
  RefreshCw, 
  MoreHorizontal,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ChevronDown
} from 'lucide-vue-next'

type Row = { 
  id: string; 
  username?: string; 
  role: string;
  avatar_url?: string;
  job?: string;
  updated_at?: string;
}

const kw = ref('')
const list = ref<Row[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
let subscription: RealtimeChannel | null = null
const { onlineUsers, initPresence } = usePresence()

const formatDate = (str?: string) => {
  if (!str) return '-'
  return new Date(str).toLocaleDateString()
}

const load = async (p = 1) => {
  loading.value = true
  page.value = p
  
  try {
    // Get Data
    let query = supabase
      .from('profiles')
      .select('id,username,role,avatar_url,job,updated_at')
      .neq('role', 'admin') // Exclude admins
      .neq('role', 'moderator') // Exclude moderators
      .order('updated_at', { ascending: false })
      .range((p - 1) * 20, p * 20 - 1)

    if (kw.value) {
      query = query.ilike('username', `%${kw.value}%`)
    }
    
    const { data, error } = await query
    if (error) throw error
    list.value = data as Row[] || []

    // Get Total
    let countQuery = supabase.from('profiles').select('id', { count: 'exact', head: true })
      .neq('role', 'admin')
      .neq('role', 'moderator')
    if (kw.value) {
      countQuery = countQuery.ilike('username', `%${kw.value}%`)
    }
    const { count } = await countQuery
    if (count !== null) total.value = count

  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const changeRole = async (row: Row, e: Event) => {
  const newValue = (e.target as HTMLSelectElement).value
  const oldValue = row.role
  
  // 乐观更新 (Optimistic Update)
  row.role = newValue
  
  try {
    const { error } = await supabase.rpc('update_user_role', { 
      target_user_id: row.id, 
      new_role: newValue 
    })
    
    if (error) throw error

    // Log action
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
       await supabase.from('admin_logs').insert({
         admin_id: user.id,
         action_type: 'change_role',
         target_id: row.id,
         details: `将用户 ${row.username || row.id} 的角色修改为 ${newValue}`
       })
    }

  } catch (error: any) {
    // 失败回滚
    row.role = oldValue
    alert('修改失败: ' + error.message)
    console.error('Update role error:', error)
  }
}

const deleteUser = async (row: Row) => {
  if (!confirm(`确定要永久删除用户 "${row.username || row.id}" 吗？此操作无法撤销。`)) return

  loading.value = true
  try {
    const { error } = await supabase.rpc('delete_user', { target_user_id: row.id })
    if (error) throw error
    
    // Log action
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
       await supabase.from('admin_logs').insert({
         admin_id: user.id,
         action_type: 'delete_user',
         target_id: row.id,
         details: `删除了用户 ${row.username || row.id}`
       })
    }

    // UI will update via Realtime, but we can also manually remove to be snappy
    const index = list.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      list.value.splice(index, 1)
      total.value--
    }
  } catch (err: any) {
    alert('删除失败: ' + err.message)
    console.error(err)
  } finally {
    loading.value = false
  }
}

const setupRealtime = () => {
  subscription = supabase
    .channel('public:profiles')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'profiles' }, (payload) => {
      console.log('Realtime change:', payload)
      
      if (payload.eventType === 'UPDATE') {
        const newRow = payload.new as Row
        const index = list.value.findIndex(item => item.id === newRow.id)
        if (index !== -1) {
          // 只更新当前列表存在的行
          list.value[index] = { ...list.value[index], ...newRow }
        }
      } else if (payload.eventType === 'DELETE') {
        const index = list.value.findIndex(item => item.id === payload.old.id)
        if (index !== -1) {
          list.value.splice(index, 1)
          total.value = Math.max(0, total.value - 1)
        }
      } else if (payload.eventType === 'INSERT') {
        // 如果在第一页且没有搜索，才插入新数据
        if (page.value === 1 && !kw.value) {
          // 需要完整的 Row 数据，这里 payload.new 可能不包含所有关联字段，
          // 但 profiles 表本身包含了所有字段，所以直接用 payload.new 应该是安全的
          // 注意：如果 newRow 缺少 username 等字段（因为 select 只选了部分），可能需要处理
          // 不过 profiles 表就是源表，payload.new 包含所有列
          const newRow = payload.new as Row
          list.value.unshift(newRow)
          if (list.value.length > 20) list.value.pop()
          total.value++
        }
      }
    })
    .subscribe()
}

onMounted(() => {
  load(1)
  setupRealtime()
  // Ensure presence is initialized if not already (e.g. on direct navigation)
  initPresence()
})

onUnmounted(() => {
  if (subscription) subscription.unsubscribe()
  // No need to cleanup presence here as it's global
})
</script>