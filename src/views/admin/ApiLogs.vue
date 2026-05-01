<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">日志监控</h1>
        <p class="text-slate-500 mt-1">查看 API 调用详情与系统操作记录</p>
      </div>
      
      <!-- Tab Switcher -->
      <div class="bg-slate-100 p-1 rounded-lg flex items-center">
        <button 
          @click="activeTab = 'api'"
          class="px-4 py-1.5 text-sm font-medium rounded-md transition-all"
          :class="activeTab === 'api' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        >
          API 调用日志
        </button>
        <button 
          @click="activeTab = 'system'"
          class="px-4 py-1.5 text-sm font-medium rounded-md transition-all"
          :class="activeTab === 'system' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        >
          系统管理日志
        </button>
      </div>
    </div>

    <!-- API Logs Section -->
    <div v-if="activeTab === 'api'" class="space-y-4">
      <!-- Filters -->
      <div class="flex items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div class="flex items-center gap-2">
          <Filter class="w-4 h-4 text-slate-400" />
          <span class="text-sm font-medium text-slate-700">筛选状态:</span>
        </div>
        <select v-model="statusFilter" class="bg-slate-50 border-none text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 outline-none text-slate-700">
          <option value="all">全部</option>
          <option value="success">成功</option>
          <option value="error">失败</option>
        </select>
        
        <div class="ml-auto flex items-center gap-2">
          <button @click="fetchApiLogs" class="p-2 hover:bg-slate-50 rounded-lg transition-colors text-slate-500" title="刷新">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div class="text-xs font-medium text-slate-500 mb-1">总调用量 (今日)</div>
          <div class="text-2xl font-bold text-slate-900">{{ apiStats.total }}</div>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div class="text-xs font-medium text-slate-500 mb-1">成功率</div>
          <div class="text-2xl font-bold text-emerald-600">{{ apiStats.successRate }}%</div>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div class="text-xs font-medium text-slate-500 mb-1">失败次数</div>
          <div class="text-2xl font-bold text-rose-600">{{ apiStats.failed }}</div>
        </div>
      </div>

      <!-- Log List -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div v-if="loading && apiLogs.length === 0" class="p-8 text-center text-slate-500">
          加载中...
        </div>
        <div v-else-if="apiLogs.length === 0" class="p-8 text-center text-slate-500">
          暂无 API 调用记录
        </div>
        <table v-else class="w-full text-left text-sm">
          <thead class="bg-slate-50 border-b border-slate-100 text-slate-500">
            <tr>
              <th class="px-6 py-3 font-medium">状态</th>
              <th class="px-6 py-3 font-medium">调用时间</th>
              <th class="px-6 py-3 font-medium">服务商</th>
              <th class="px-6 py-3 font-medium">能力</th>
              <th class="px-6 py-3 font-medium">耗时</th>
              <th class="px-6 py-3 font-medium">详情</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="log in filteredApiLogs" :key="log.id" class="hover:bg-slate-50/50 transition-colors">
              <td class="px-6 py-3">
                <span 
                  class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="getLogStatus(log) === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'"
                >
                  <CheckCircle2 v-if="getLogStatus(log) === 'success'" class="w-3.5 h-3.5" />
                  <XCircle v-else class="w-3.5 h-3.5" />
                  {{ getLogStatus(log) === 'success' ? '成功' : '失败' }}
                </span>
              </td>
              <td class="px-6 py-3 text-slate-600 font-mono text-xs">{{ formatTime(log.created_at) }}</td>
              <td class="px-6 py-3 text-slate-900 font-medium">{{ log.provider_name }}</td>
              <td class="px-6 py-3 text-slate-500">{{ formatCapability(log.capability) }}</td>
              <td class="px-6 py-3 text-slate-500 font-mono text-xs">{{ log.details?.latency || '-' }}ms</td>
              <td class="px-6 py-3">
                <button @click="showDetails(log)" class="text-blue-600 hover:text-blue-700 font-medium text-xs">查看</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- System Logs Section -->
    <div v-if="activeTab === 'system'" class="space-y-4">
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 class="font-medium text-slate-800">最近操作记录</h3>
          <button @click="fetchAdminLogs" class="text-slate-400 hover:text-slate-600">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </button>
        </div>
        
        <div v-if="loading && adminLogs.length === 0" class="p-8 text-center text-slate-500">
          加载中...
        </div>
        <div v-else-if="adminLogs.length === 0" class="p-8 text-center text-slate-500">
          暂无系统日志
        </div>
        <table v-else class="w-full text-left text-sm">
          <thead class="bg-slate-50 border-b border-slate-100 text-slate-500">
            <tr>
              <th class="px-6 py-3 font-medium">操作时间</th>
              <th class="px-6 py-3 font-medium">操作类型</th>
              <th class="px-6 py-3 font-medium">详情</th>
              <th class="px-6 py-3 font-medium">操作人</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="log in adminLogs" :key="log.id" class="hover:bg-slate-50/50 transition-colors">
              <td class="px-6 py-3 text-slate-600 font-mono text-xs">{{ formatTime(log.created_at) }}</td>
              <td class="px-6 py-3">
                <span class="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
                  {{ log.action_type }}
                </span>
              </td>
              <td class="px-6 py-3 text-slate-700 max-w-md truncate" :title="log.details">{{ log.details }}</td>
              <td class="px-6 py-3 text-slate-500 text-xs">
                {{ log.admin_id ? '管理员' : '系统' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedLog" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="selectedLog = null">
      <div class="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-bold text-lg text-slate-800">日志详情</h3>
          <button @click="selectedLog = null" class="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-slate-500 block text-xs mb-1">ID</span>
              <span class="font-mono bg-slate-50 px-2 py-1 rounded text-slate-700">{{ selectedLog.id }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs mb-1">时间</span>
              <span class="text-slate-700">{{ formatTime(selectedLog.created_at) }}</span>
            </div>
            <div>
              <span class="text-slate-500 block text-xs mb-1">服务商</span>
              <span class="text-slate-700 font-medium">{{ selectedLog.provider_name }}</span>
            </div>
             <div>
              <span class="text-slate-500 block text-xs mb-1">能力</span>
              <span class="text-slate-700">{{ formatCapability(selectedLog.capability) }}</span>
            </div>
          </div>
          
          <div>
            <span class="text-slate-500 block text-xs mb-2">详细数据 (JSON)</span>
            <pre class="bg-slate-900 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-x-auto">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
          </div>
        </div>
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button @click="selectedLog = null" class="px-4 py-2 bg-white border border-slate-200 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors shadow-sm">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { supabase } from '@/utils/supabase'
import { 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  Filter, 
  X
} from 'lucide-vue-next'

const activeTab = ref('api')
const loading = ref(false)
const apiLogs = ref<any[]>([])
const adminLogs = ref<any[]>([])
const selectedLog = ref<any>(null)
const statusFilter = ref('all')

const apiStats = computed(() => {
  const total = apiLogs.value.length
  const failed = apiLogs.value.filter(l => getLogStatus(l) === 'error').length
  const success = total - failed
  const successRate = total > 0 ? Math.round((success / total) * 100) : 0
  
  return {
    total,
    failed,
    successRate
  }
})

const filteredApiLogs = computed(() => {
  if (statusFilter.value === 'all') return apiLogs.value
  return apiLogs.value.filter(log => getLogStatus(log) === statusFilter.value)
})

const getLogStatus = (log: any) => {
  // Check details JSON for status field, default to success if not present (unless error field exists)
  if (log.details?.status) return log.details.status
  if (log.details?.error) return 'error'
  return 'success'
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatCapability = (c: string) => {
  const map: Record<string, string> = {
    chat: '聊天助手',
    image: '图像生成',
    embedding: '向量嵌入',
    search: '网络搜索',
    weather: '天气信息',
    route: '路线规划'
  }
  return map[c] || c
}

const showDetails = (log: any) => {
  selectedLog.value = log
}

const fetchApiLogs = async () => {
  loading.value = true
  const { data, error } = await supabase
    .from('api_usage_logs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(50)
    
  if (data) {
    apiLogs.value = data
  }
  loading.value = false
}

const fetchAdminLogs = async () => {
  loading.value = true
  const { data, error } = await supabase
    .from('admin_logs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(50)
    
  if (data) {
    adminLogs.value = data
  }
  loading.value = false
}

onMounted(() => {
  fetchApiLogs()
  fetchAdminLogs()
})
</script>
