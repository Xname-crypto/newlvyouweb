<template>
  <div class="h-full flex flex-col bg-slate-50">
    <!-- Header -->
    <div class="px-8 py-6 bg-white border-b border-slate-200 flex justify-between items-center shrink-0">
      <div>
        <h2 class="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Database class="w-6 h-6 text-blue-600" />
          数据源管理
        </h2>
        <p class="text-xs text-slate-500 mt-0.5">管理所有数据库连接，查看表结构和数据</p>
      </div>
      <button 
        @click="openCreateModal"
        class="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        新建连接
      </button>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: Connections List -->
      <div class="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0">
        <div class="p-4 border-b border-slate-100 bg-slate-50/50">
          <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider">已保存的连接</h3>
        </div>
        
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
          <div v-if="loading" class="text-center py-4 text-slate-400 text-sm">加载中...</div>
          <div v-else-if="connections.length === 0" class="text-center py-8 text-slate-400 text-sm px-4">
            暂无连接，请点击右上角新建
          </div>
          
          <button 
            v-for="conn in connections" 
            :key="conn.id"
            @click="selectConnection(conn)"
            class="w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between group transition-colors"
            :class="selectedConnection?.id === conn.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-slate-700 hover:bg-slate-50'"
          >
            <div class="flex items-center gap-2 truncate">
              <div class="w-2 h-2 rounded-full" :class="getTypeColor(conn.type)"></div>
              <span class="truncate">{{ conn.name }}</span>
            </div>
            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
               <button @click.stop="editConnection(conn)" class="p-1 hover:bg-white rounded text-slate-400 hover:text-blue-600">
                 <Settings class="w-3 h-3" />
               </button>
               <button @click.stop="deleteConnection(conn)" class="p-1 hover:bg-white rounded text-slate-400 hover:text-red-600">
                 <Trash2 class="w-3 h-3" />
               </button>
            </div>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="flex-1 flex flex-col overflow-hidden bg-slate-50/30">
        <div v-if="!selectedConnection" class="flex-1 flex flex-col items-center justify-center text-slate-400">
          <Database class="w-12 h-12 mb-4 opacity-20" />
          <p>请从左侧选择一个数据库连接</p>
        </div>
        
        <div v-else class="flex-1 flex overflow-hidden">
           <!-- Table List (Tree) -->
           <div class="w-60 bg-white border-r border-slate-200 flex flex-col shrink-0">
              <div class="p-3 border-b border-slate-100 flex items-center justify-between">
                 <div class="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Database class="w-4 h-4 text-slate-400" />
                    {{ selectedConnection.name }}
                 </div>
                 <button @click="fetchTables(selectedConnection.id)" class="text-slate-400 hover:text-blue-600 p-1 rounded hover:bg-slate-50" title="刷新表列表">
                    <RefreshCw class="w-3 h-3" :class="{'animate-spin': tablesLoading}" />
                 </button>
              </div>
              
              <div class="flex-1 overflow-y-auto p-1">
                 <div v-if="tablesLoading" class="p-4 text-center text-xs text-slate-400">加载表结构...</div>
                 <div v-else-if="tables.length === 0" class="p-4 text-center text-xs text-slate-400">未找到表</div>
                 
                 <button 
                    v-for="table in tables" 
                    :key="table"
                    @click="selectTable(table)"
                    class="w-full text-left px-3 py-1.5 rounded text-xs flex items-center gap-2 transition-colors truncate"
                    :class="selectedTable === table ? 'bg-blue-50 text-blue-700 font-medium' : 'text-slate-600 hover:bg-slate-50'"
                 >
                    <Table2 class="w-3 h-3 shrink-0" />
                    <span class="truncate">{{ table }}</span>
                 </button>
              </div>
           </div>
           
           <!-- Data Preview -->
           <div class="flex-1 flex flex-col overflow-hidden bg-white">
              <div v-if="!selectedTable" class="flex-1 flex items-center justify-center text-slate-400 text-sm">
                 选择一张表以预览数据
              </div>
              <div v-else class="flex-1 flex flex-col overflow-hidden">
                 <div class="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <h3 class="font-medium text-sm text-slate-700 flex items-center gap-2">
                       <Table2 class="w-4 h-4 text-blue-600" />
                       {{ selectedTable }}
                       <span class="text-xs font-normal text-slate-400 ml-2" v-if="previewData.data">(前 {{ previewData.data.length }} 行预览)</span>
                    </h3>
                    <div class="flex gap-2">
                       <button @click="openIngestModal" class="text-xs bg-slate-900 text-white px-3 py-1 rounded hover:bg-slate-800 flex items-center gap-1">
                          <CloudUpload class="w-3 h-3" />
                          导入到知识库
                       </button>
                       <button @click="fetchTablePreview(selectedTable)" class="text-xs bg-white border border-slate-200 px-2 py-1 rounded hover:bg-slate-50 text-slate-600">
                          刷新数据
                       </button>
                    </div>
                 </div>
                 
                 <div class="flex-1 overflow-auto">
                    <div v-if="dataLoading" class="flex items-center justify-center h-full text-slate-400 text-sm">
                       <RefreshCw class="w-5 h-5 animate-spin mr-2" />
                       加载数据中...
                    </div>
                    <table v-else class="w-full text-left border-collapse text-sm">
                       <thead class="bg-slate-50 sticky top-0 z-10 shadow-sm">
                          <tr>
                             <th v-for="col in previewData.columns" :key="col" class="px-4 py-2 font-medium text-slate-600 border-b border-slate-200 whitespace-nowrap text-xs">
                                {{ col }}
                             </th>
                          </tr>
                       </thead>
                       <tbody>
                          <tr v-for="(row, idx) in previewData.data" :key="idx" class="hover:bg-slate-50/50 border-b border-slate-100 last:border-0">
                             <td v-for="col in previewData.columns" :key="col" class="px-4 py-2 text-slate-600 whitespace-nowrap text-xs max-w-xs truncate" :title="String(row[col])">
                                {{ row[col] }}
                             </td>
                          </tr>
                       </tbody>
                    </table>
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>

    <!-- Ingest Modal -->
    <div v-if="showIngestModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/20 backdrop-blur-sm" @click="showIngestModal = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 class="text-lg font-bold text-slate-900">导入表数据: {{ selectedTable }}</h3>
          <button @click="showIngestModal = false" class="text-slate-400 hover:text-slate-600">
            <X class="w-5 h-5" />
          </button>
        </div>
        
        <div class="p-6 space-y-4 overflow-y-auto">
          <p class="text-sm text-slate-500">
            选择要导入的字段。内容字段将被组合成文本块进行向量化，元数据字段将用于筛选。
          </p>
          
          <div class="space-y-3">
            <div class="flex justify-between items-center">
                <h4 class="text-sm font-medium text-slate-800">字段选择</h4>
                <div class="text-xs space-x-2">
                    <button @click="selectAllContent" class="text-blue-600 hover:underline">全选内容</button>
                    <button @click="selectAllMetadata" class="text-purple-600 hover:underline">全选元数据</button>
                    <button @click="clearAll" class="text-slate-500 hover:underline">清空</button>
                </div>
            </div>
            
            <div class="max-h-60 overflow-y-auto border rounded-lg divide-y">
                <div v-for="col in previewData.columns" :key="col" class="flex items-center justify-between p-2 hover:bg-slate-50 text-sm">
                    <span class="font-mono text-slate-700">{{ col }}</span>
                    <div class="flex gap-4">
                        <label class="flex items-center gap-1 cursor-pointer">
                            <input type="checkbox" v-model="ingestConfig.contentCols" :value="col" class="rounded text-blue-600" />
                            <span class="text-xs text-slate-500">内容</span>
                        </label>
                        <label class="flex items-center gap-1 cursor-pointer">
                            <input type="checkbox" v-model="ingestConfig.metaCols" :value="col" class="rounded text-purple-600" />
                            <span class="text-xs text-slate-500">元数据</span>
                        </label>
                    </div>
                </div>
            </div>
          </div>
          
          <div class="space-y-1">
             <label class="text-xs font-medium text-slate-700">导入行数限制</label>
             <input v-model.number="ingestConfig.limit" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          
          <div v-if="ingestMessage" :class="ingestSuccess ? 'text-green-600 bg-green-50' : 'text-slate-600 bg-slate-50'" class="text-xs p-3 rounded border whitespace-pre-line mb-3">
             {{ ingestMessage }}
          </div>
          
          <div v-if="ingesting" class="space-y-1">
             <div class="flex justify-between text-xs text-slate-500">
                <span>进度: {{ ingestStats.processed }} / {{ ingestStats.total }}</span>
                <span>{{ ingestProgress }}%</span>
             </div>
             <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" :style="{ width: `${ingestProgress}%` }"></div>
             </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
          <button @click="showIngestModal = false" class="px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-sm font-medium">取消</button>
          <button 
            @click="ingestTable" 
            :disabled="ingesting || ingestConfig.contentCols.length === 0"
            class="px-4 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw v-if="ingesting" class="w-4 h-4 animate-spin" />
            <CloudUpload v-else class="w-4 h-4" />
            {{ ingesting ? '导入中...' : '开始导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/20 backdrop-blur-sm" @click="showModal = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 class="text-lg font-bold text-slate-900">{{ isEditing ? '编辑连接' : '新建连接' }}</h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600">
            <X class="w-5 h-5" />
          </button>
        </div>
        
        <div class="p-6 space-y-4 overflow-y-auto">
          <div class="grid grid-cols-2 gap-4">
             <div class="space-y-1 col-span-2">
               <label class="text-xs font-medium text-slate-700">连接名称</label>
               <input v-model="form.name" type="text" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" placeholder="例如：生产环境 MySQL" />
             </div>
             
             <div class="space-y-1 col-span-2">
               <label class="text-xs font-medium text-slate-700">数据库类型</label>
               <select v-model="form.type" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white">
                  <option value="mysql">MySQL</option>
                  <option value="postgresql">PostgreSQL / Supabase</option>
                  <option value="sqlite">SQLite</option>
               </select>
             </div>

             <!-- Host/Port for Network DBs -->
             <template v-if="form.type !== 'sqlite'">
                <div class="space-y-1">
                  <label class="text-xs font-medium text-slate-700">主机地址 (Host)</label>
                  <input v-model="form.host" type="text" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" placeholder="127.0.0.1" />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-medium text-slate-700">端口 (Port)</label>
                  <input v-model.number="form.port" type="number" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-medium text-slate-700">用户名</label>
                  <input v-model="form.user" type="text" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div class="space-y-1 relative">
                  <label class="text-xs font-medium text-slate-700">密码</label>
                  <div class="relative">
                    <input 
                      v-model="form.password" 
                      :type="showPassword ? 'text' : 'password'" 
                      class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none pr-10" 
                      :placeholder="isEditing ? '不修改请留空' : ''" 
                    />
                    <button 
                      @click="showPassword = !showPassword" 
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                      type="button"
                    >
                      <Eye v-if="!showPassword" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div class="space-y-1 col-span-2">
                  <label class="text-xs font-medium text-slate-700">数据库名</label>
                  <input v-model="form.database_name" type="text" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
             </template>
             
             <!-- Path for SQLite -->
             <template v-else>
                <div class="space-y-1 col-span-2">
                  <label class="text-xs font-medium text-slate-700">文件路径 (绝对路径)</label>
                  <input v-model="form.file_path" type="text" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" placeholder="/path/to/db.sqlite3" />
                </div>
             </template>
          </div>
          
          <div v-if="testMessage" :class="testSuccess ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'" class="text-xs p-2 rounded border">
             {{ testMessage }}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-between gap-3">
          <button 
             @click="testConnection" 
             class="px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-sm font-medium flex items-center gap-2"
             :disabled="testing"
          >
             <RefreshCw class="w-3 h-3" :class="{'animate-spin': testing}" />
             测试连接
          </button>
          
          <div class="flex gap-3">
             <button @click="showModal = false" class="px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-sm font-medium">取消</button>
             <button @click="saveConnection" class="px-4 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-sm font-medium">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { Database, Plus, Settings, Trash2, X, RefreshCw, Table2, Eye, EyeOff, CloudUpload } from 'lucide-vue-next'

const API_URL = '/api/datasources'

interface Connection {
  id: number
  name: string
  type: string
  host?: string
  port?: number
  user?: string
  database_name?: string
  file_path?: string
  created_at: string
}

const connections = ref<Connection[]>([])
const loading = ref(false)
const selectedConnection = ref<Connection | null>(null)

// Tree & Data
const tables = ref<string[]>([])
const tablesLoading = ref(false)
const selectedTable = ref<string | null>(null)
const dataLoading = ref(false)
const previewData = ref<{columns: string[], data: any[]}>({ columns: [], data: [] })

// Modal
const showModal = ref(false)
const isEditing = ref(false)
const testing = ref(false)
const testMessage = ref('')
const testSuccess = ref(false)
const showPassword = ref(false)

const form = reactive({
   id: null as number | null,
   name: '',
   type: 'mysql',
   host: '127.0.0.1',
   port: 3306,
   user: 'root',
   password: '',
   database_name: '',
   file_path: ''
})

const getTypeColor = (type: string) => {
   switch(type) {
      case 'mysql': return 'bg-orange-400'
      case 'postgresql': return 'bg-blue-400'
      case 'sqlite': return 'bg-emerald-400'
      default: return 'bg-slate-400'
   }
}

const fetchConnections = async () => {
   loading.value = true
   try {
      const res = await fetch(`${API_URL}/`)
      if (res.ok) {
         connections.value = await res.json()
      }
   } catch (e) {
      console.error(e)
   } finally {
      loading.value = false
   }
}

const selectConnection = async (conn: Connection) => {
   selectedConnection.value = conn
   selectedTable.value = null
   previewData.value = { columns: [], data: [] }
   await fetchTables(conn.id)
}

const fetchTables = async (id: number) => {
   tablesLoading.value = true
   tables.value = []
   try {
      const res = await fetch(`${API_URL}/${id}/tables/`)
      if (res.ok) {
         tables.value = await res.json()
      } else {
         const err = await res.json()
         alert(`获取表结构失败: ${err.error}`)
      }
   } catch (e) {
      console.error(e)
   } finally {
      tablesLoading.value = false
   }
}

const selectTable = async (table: string) => {
   selectedTable.value = table
   await fetchTablePreview(table)
}

const fetchTablePreview = async (table: string) => {
   if (!selectedConnection.value) return
   dataLoading.value = true
   try {
      const res = await fetch(`${API_URL}/${selectedConnection.value.id}/preview/${table}/`)
      if (res.ok) {
         previewData.value = await res.json()
      } else {
         const err = await res.json()
         alert(`获取数据预览失败: ${err.error}`)
      }
   } catch (e) {
      console.error(e)
   } finally {
      dataLoading.value = false
   }
}

// Modal Actions
const openCreateModal = () => {
   isEditing.value = false
   testMessage.value = ''
   showPassword.value = false
   form.id = null
   form.name = ''
   form.type = 'mysql'
   form.host = '127.0.0.1'
   form.port = 3306
   form.user = 'root'
   form.password = ''
   form.database_name = ''
   form.file_path = ''
   showModal.value = true
}

const editConnection = (conn: Connection) => {
   isEditing.value = true
   testMessage.value = ''
   showPassword.value = false
   form.id = conn.id
   form.name = conn.name
   form.type = conn.type
   form.host = conn.host || '127.0.0.1'
   form.port = conn.port || 3306
   form.user = conn.user || ''
   form.password = '' // Don't fill password
   form.database_name = conn.database_name || ''
   form.file_path = conn.file_path || ''
   showModal.value = true
}

const deleteConnection = async (conn: Connection) => {
   if(!confirm(`确定要删除连接 "${conn.name}" 吗？`)) return
   try {
      await fetch(`${API_URL}/${conn.id}/`, { method: 'DELETE' })
      if (selectedConnection.value?.id === conn.id) {
         selectedConnection.value = null
      }
      await fetchConnections()
   } catch (e) {
      alert('删除失败')
   }
}

const testConnection = async () => {
   testing.value = true
   testMessage.value = ''
   try {
      const res = await fetch(`${API_URL}/test_connection/`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(form)
      })
      const data = await res.json()
      if (res.ok) {
         testSuccess.value = true
         testMessage.value = '✅ 连接成功！'
      } else {
         testSuccess.value = false
         testMessage.value = `❌ 连接失败: ${data.error}`
      }
   } catch (e: any) {
      testSuccess.value = false
      testMessage.value = `❌ 网络错误: ${e.message}`
   } finally {
      testing.value = false
   }
}

const saveConnection = async () => {
   try {
      const url = isEditing.value ? `${API_URL}/${form.id}/` : `${API_URL}/`
      const method = isEditing.value ? 'PUT' : 'POST'
      
      const res = await fetch(url, {
         method,
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(form)
      })
      
      if (res.ok) {
         showModal.value = false
         await fetchConnections()
      } else {
         const data = await res.json()
         alert(`保存失败: ${JSON.stringify(data)}`)
      }
   } catch (e) {
      alert('保存失败')
   }
}

// Ingest Logic
const showIngestModal = ref(false)
const ingesting = ref(false)
const ingestMessage = ref('')
const ingestSuccess = ref(false)
const ingestConfig = reactive({
    contentCols: [] as string[],
    metaCols: [] as string[],
    limit: 100
})

const selectAllContent = () => {
    ingestConfig.contentCols = [...previewData.value.columns]
}

const selectAllMetadata = () => {
    ingestConfig.metaCols = [...previewData.value.columns]
}

const clearAll = () => {
    ingestConfig.contentCols = []
    ingestConfig.metaCols = []
}

const openIngestModal = () => {
    if (!selectedTable.value || !previewData.value.columns.length) {
        alert('请先选择表并等待数据加载完成')
        return
    }
    ingestConfig.contentCols = [...previewData.value.columns]
    ingestConfig.metaCols = previewData.value.columns.filter(c => c === 'id' || c === 'name' || c.includes('_id'))
    ingestConfig.limit = 100
    ingestMessage.value = ''
    ingestSuccess.value = false
    showIngestModal.value = true
}

const ingestProgress = ref(0)
const ingestStats = reactive({
    processed: 0,
    total: 0,
    errors: 0
})

const ingestTable = async () => {
    if (!selectedConnection.value || !selectedTable.value) return
    
    ingesting.value = true
    ingestMessage.value = '正在初始化导入任务...'
    ingestSuccess.value = false
    ingestProgress.value = 0
    ingestStats.processed = 0
    ingestStats.total = 0
    ingestStats.errors = 0
    
    try {
        const response = await fetch(`${API_URL}/${selectedConnection.value.id}/ingest/${selectedTable.value}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_columns: ingestConfig.contentCols,
                metadata_columns: ingestConfig.metaCols,
                limit: ingestConfig.limit
            })
        })

        if (!response.ok) {
             const data = await response.json()
             throw new Error(data.error || '导入请求失败')
        }

        if (!response.body) throw new Error('ReadableStream not supported')

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || '' // Keep the last incomplete line
            
            for (const line of lines) {
                if (!line.trim()) continue
                try {
                    const data = JSON.parse(line)
                    
                    if (data.error) {
                        throw new Error(data.error)
                    }
                    
                    if (data.progress !== undefined) {
                        ingestProgress.value = data.progress
                        if (data.processed) ingestStats.processed = data.processed
                        if (data.total) ingestStats.total = data.total
                        if (data.errors) ingestStats.errors = data.errors
                        
                        ingestMessage.value = `正在导入: ${ingestStats.processed} / ${ingestStats.total}`
                        if (ingestStats.errors > 0) {
                             ingestMessage.value += ` (失败: ${ingestStats.errors})`
                        }
                    }
                    
                    if (data.done) {
                        ingestSuccess.value = true
                        ingestMessage.value = `✅ ${data.message}`
                        if (data.errors > 0) {
                            ingestMessage.value += `\n⚠️ 有 ${data.errors} 行导入失败。`
                        }
                    }
                } catch (e) {
                    console.error('Error parsing stream chunk:', e)
                }
            }
        }
        
    } catch (e: any) {
        ingestSuccess.value = false
        ingestMessage.value = `❌ 导入失败: ${e.message}`
    } finally {
        ingesting.value = false
    }
}

onMounted(() => {
   fetchConnections()
})
</script>
