<template>
  <div class="h-full flex flex-col">
    <!-- 顶部标题与工具栏 -->
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">人员管理</h1>
        <div class="text-sm text-slate-500 mt-1">管理系统内部人员（管理员、审核员）</div>
      </div>
      <div class="flex items-center gap-3">
        <button class="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-2">
          <Filter class="w-4 h-4" />
          筛选
        </button>
        <button 
          v-if="currentUserRole === 'admin'"
          @click="showAddModal = true"
          class="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors flex items-center gap-2"
        >
          <Plus class="w-4 h-4" />
          添加人员
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
            placeholder="搜索人员..." 
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
              <td colspan="6" class="px-6 py-12 text-center text-slate-500 text-sm">加载中...</td>
            </tr>
            <tr v-else-if="list.length === 0">
              <td colspan="6" class="px-6 py-12 text-center text-slate-500 text-sm">暂无数据</td>
            </tr>
            <tr v-for="row in list" :key="row.id" class="group hover:bg-slate-50/50 transition-colors">
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
                    class="appearance-none bg-transparent py-1 pr-6 pl-0 text-sm font-medium focus:outline-none cursor-pointer hover:text-slate-900 transition-colors disabled:cursor-not-allowed disabled:opacity-75"
                    :class="getRoleColor(row.role)"
                    :value="row.role"
                    :disabled="row.role === 'admin' || currentUserRole !== 'admin'"
                    @change="changeRole(row, $event)"
                  >
                    <option value="moderator" v-if="row.role !== 'admin'">审核员</option>
                    <option value="admin">管理员</option>
                    <option value="user" v-if="row.role !== 'admin'">降级为普通用户</option>
                  </select>
                  <ChevronDown v-if="row.role !== 'admin' && currentUserRole === 'admin'" class="w-3 h-3 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
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
                <div v-if="currentUserRole === 'admin'" class="relative group/menu">
                  <button class="p-1.5 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
                    <MoreHorizontal class="w-4 h-4" />
                  </button>
                  
                  <!-- Dropdown Menu -->
                  <div class="absolute right-0 top-full pt-2 w-32 hidden group-hover/menu:block z-20">
                    <div class="bg-white rounded-lg shadow-lg border border-slate-100 py-1">
                      <button 
                        v-if="row.role !== 'admin'"
                        @click="changeRole(row, { target: { value: 'user' } } as any)"
                        class="w-full text-left px-4 py-2 text-sm text-amber-600 hover:bg-slate-50 transition-colors"
                      >
                        移除权限
                      </button>
                      <div v-else class="px-4 py-2 text-xs text-slate-400 italic">管理员不可直接移除权限</div>
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
    <!-- Add Staff Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 flex flex-col h-[500px]">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-slate-900">添加工作人员</h3>
          <button @click="showAddModal = false" class="p-1 hover:bg-slate-100 rounded-lg transition-colors">
            <X class="w-5 h-5 text-slate-400" />
          </button>
        </div>
        
        <div class="mb-4">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              v-model="userSearchKw" 
              type="text" 
              placeholder="搜索用户名..." 
              class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10"
              @keyup.enter="searchUsers"
            />
            <button 
              v-if="userSearchKw" 
              @click="searchUsers" 
              class="absolute right-2 top-1/2 -translate-y-1/2 text-xs bg-slate-900 text-white px-2 py-1 rounded hover:bg-slate-800 transition-colors"
            >
              搜索
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-1">
          <div v-if="searchingUsers" class="text-center py-8 text-slate-400 text-sm">搜索中...</div>
          <div v-else-if="userSearchResults.length === 0" class="text-center py-8 text-slate-400 text-sm">
            {{ userSearchKw ? '未找到相关用户' : '暂无普通用户' }}
          </div>
          <div 
            v-for="user in userSearchResults" 
            :key="user.id" 
            class="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-slate-300 hover:bg-slate-50 transition-all cursor-pointer group"
            @click="promoteUser(user)"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center overflow-hidden">
                <img v-if="user.avatar_url" :src="user.avatar_url" class="w-full h-full object-cover" />
                <span v-else class="text-xs font-bold text-slate-500">{{ (user.username?.[0] || 'U').toUpperCase() }}</span>
              </div>
              <div>
                <div class="text-sm font-bold text-slate-700">{{ user.username }}</div>
                <div class="text-[10px] text-slate-400 font-mono">ID: {{ user.id.slice(0, 6) }}</div>
              </div>
            </div>
            <div class="opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-1 rounded-lg">设为审核员</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
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
  ChevronDown,
  X
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
const currentUserRole = ref('')

// Add Modal State
const showAddModal = ref(false)
const userSearchKw = ref('')
const userSearchResults = ref<Row[]>([])
const searchingUsers = ref(false)

const searchUsers = async () => {
  searchingUsers.value = true
  
  try {
    let query = supabase
      .from('profiles')
      .select('id,username,role,avatar_url')
      .eq('role', 'user') // Only find normal users
      
    if (userSearchKw.value) {
      query = query.ilike('username', `%${userSearchKw.value}%`)
    }
    
    const { data, error } = await query.limit(100)
      
    if (error) throw error
    userSearchResults.value = data as Row[] || []
  } catch (e) {
    console.error(e)
  } finally {
    searchingUsers.value = false
  }
}

watch(showAddModal, (val) => {
  if (val) {
    searchUsers()
  } else {
    userSearchKw.value = ''
    userSearchResults.value = []
  }
})

const promoteUser = async (user: Row) => {
  if (!confirm(`确定要将用户 ${user.username} 提升为审核员吗？`)) return
  
  try {
    const { error } = await supabase.rpc('update_user_role', { 
      target_user_id: user.id, 
      new_role: 'moderator' 
    })
    
    if (error) throw error

    // Log action
    const { data: { user: admin } } = await supabase.auth.getUser()
    if (admin) {
       await supabase.from('admin_logs').insert({
         admin_id: admin.id,
         action_type: 'promote_staff',
         target_id: user.id,
         details: `将用户 ${user.username || user.id} 提升为审核员`
       })
    }
    
    showAddModal.value = false
    userSearchKw.value = ''
    userSearchResults.value = []
    load(1)
    
  } catch (error: any) {
    alert('操作失败: ' + error.message)
  }
}

const formatDate = (str?: string) => {
  if (!str) return '-'
  return new Date(str).toLocaleDateString()
}

const getRoleColor = (role: string) => {
  switch (role) {
    case 'admin': return 'text-red-600 font-bold'
    case 'moderator': return 'text-slate-900 font-medium'
    default: return 'text-slate-600'
  }
}

const load = async (p = 1) => {
  loading.value = true
  page.value = p
  
  try {
    // Get Data
    let query = supabase
      .from('profiles')
      .select('id,username,role,avatar_url,job,updated_at')
      .or('role.eq.admin,role.eq.moderator') // Only get staff
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
      .or('role.eq.admin,role.eq.moderator')

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
  const target = e.target as HTMLSelectElement | { value: string }
  const newValue = target.value
  const oldValue = row.role
  
  if (oldValue === 'admin' && (newValue === 'user' || newValue === 'moderator')) {
    alert('管理员角色不可被降级')
    // Reset UI if triggered by select element
    if (e.target instanceof HTMLSelectElement) {
      e.target.value = oldValue
    }
    return
  }
  
  // 乐观更新
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
         action_type: 'change_staff_role',
         target_id: row.id,
         details: `将人员 ${row.username || row.id} 的角色从 ${oldValue} 修改为 ${newValue}`
       })
    }
    
    // 如果将用户降级为 user，应该从列表中移除
    if (newValue === 'user') {
      const index = list.value.findIndex(item => item.id === row.id)
      if (index !== -1) {
        list.value.splice(index, 1)
        total.value--
      }
    }
  } catch (error: any) {
    row.role = oldValue
    alert('修改失败: ' + error.message)
    console.error('Update role error:', error)
  }
}

const setupRealtime = () => {
  subscription = supabase
    .channel('public:profiles:staff')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'profiles' }, (payload) => {
      // 简化处理：只要有变动就重新加载，确保逻辑简单可靠
      // 实际上对于人员管理，变动频率很低
      load(page.value)
    })
    .subscribe()
}

onMounted(() => {
  load(1)
  setupRealtime()
  initPresence()
  
  // Get current user role
  supabase.auth.getUser().then(async ({ data: { user } }) => {
    if (user) {
      const { data } = await supabase.from('profiles').select('role').eq('id', user.id).single()
      if (data) currentUserRole.value = data.role
    }
  })
})

onUnmounted(() => {
  if (subscription) subscription.unsubscribe()
})
</script>