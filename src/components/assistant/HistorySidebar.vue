<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { History, Pin, Clock, Plus, MessageSquare, Trash2 } from 'lucide-vue-next';
import { assistantService, type AssistantSession } from '@/services/assistantService';
import { supabase } from '@/utils/supabase';

const isHovered = ref(false);
const isPinned = ref(false);
const sessions = ref<AssistantSession[]>([]);
const isLoading = ref(false);
const user = ref<any>(null);
const deletingSessionId = ref<string | null>(null);

const emit = defineEmits(['select-session', 'new-chat', 'delete-session']);

const fetchSessions = async () => {
  if (!user.value) return;
  isLoading.value = true;
  sessions.value = await assistantService.getSessions();
  isLoading.value = false;
};

const handleMouseEnter = () => {
  if (!isPinned.value) {
    isHovered.value = true;
  }
};

const handleMouseLeave = () => {
  if (!isPinned.value) {
    isHovered.value = false;
  }
};

const togglePin = () => {
  isPinned.value = !isPinned.value;
  // If we just pinned it, ensure it stays visible (isHovered logic is overridden by isPinned in template)
  // If unpinned, we might want to check if mouse is still over to keep isHovered true, 
  // but simpler to let mouse events handle it or just let it close if mouse is out.
  if (isPinned.value) {
    isHovered.value = true; 
  }
};

const selectSession = (session: AssistantSession) => {
  emit('select-session', session);
};

const newChat = () => {
  emit('new-chat');
};

const deleteSession = async (session: AssistantSession, event: MouseEvent) => {
  event.stopPropagation();
  if (deletingSessionId.value) return;
  if (!window.confirm(`删除会话“${session.title || '未命名会话'}”？`)) return;

  deletingSessionId.value = session.id;
  try {
    await assistantService.deleteSession(session.id);
    sessions.value = sessions.value.filter((item) => item.id !== session.id);
    emit('delete-session', session.id);
  } catch (error) {
    console.error('Error deleting session:', error);
    window.alert(error instanceof Error ? error.message : '删除会话失败，请稍后重试。');
  } finally {
    deletingSessionId.value = null;
  }
};

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession();
  user.value = session?.user || null;
  if (user.value) {
    fetchSessions();
  }
  
  supabase.auth.onAuthStateChange((_event, session) => {
    user.value = session?.user || null;
    if (user.value) {
      fetchSessions();
    } else {
      sessions.value = [];
    }
  });
});

defineExpose({ refresh: fetchSessions });
</script>

<template>
  <div 
    class="fixed right-0 top-24 h-[calc(100vh-96px)] bg-white border-l border-gray-100 shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-40 transition-all duration-300 ease-in-out flex flex-col group"
    :class="[isHovered || isPinned ? 'w-80' : 'w-14']"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Collapsed State -->
    <div 
      class="absolute top-0 left-0 w-14 h-full flex flex-col items-center pt-6 gap-6 transition-opacity duration-200"
      :class="isHovered || isPinned ? 'opacity-0 pointer-events-none' : 'opacity-100'"
    >
      <button class="p-2 rounded-full hover:bg-gray-100 text-gray-400 transition-colors">
        <Clock class="w-6 h-6" />
      </button>
    </div>

    <!-- Expanded State Content -->
    <div 
      class="flex flex-col h-full w-full overflow-hidden transition-opacity duration-300 delay-75"
      :class="isHovered || isPinned ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    >
      <!-- Header -->
      <div class="px-5 py-4 flex items-center justify-between border-b border-gray-50 bg-white flex-shrink-0">
        <div class="flex items-center gap-2 text-gray-900 font-bold text-lg">
          <History class="w-5 h-5 text-teal-600" />
          <span>History</span>
        </div>
        <div class="flex items-center gap-1">
          <button 
            @click="newChat"
            class="p-1.5 rounded-full hover:bg-gray-100 text-gray-400 hover:text-teal-600 transition-colors"
            title="New Chat"
          >
            <Plus class="w-4 h-4" />
          </button>
          <button 
            @click="togglePin"
            class="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
            :class="isPinned ? 'text-teal-600 bg-teal-50' : 'text-gray-400 hover:text-gray-600'"
            title="Pin Sidebar"
          >
            <Pin class="w-4 h-4" :class="{ 'fill-current': isPinned }" />
          </button>
        </div>
      </div>

      <!-- Content List -->
      <div class="flex-1 overflow-y-auto custom-scrollbar px-2 py-2">
        <div v-if="!user" class="p-4 text-center text-gray-400 text-sm">
          Please login to view history
        </div>
        <div v-else-if="sessions.length === 0" class="p-4 text-center text-gray-400 text-sm">
          No history yet
        </div>
        <div v-else>
          <div class="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Recent</div>
          <div class="space-y-0.5">
            <div 
              v-for="session in sessions" 
              :key="session.id"
              role="button"
              tabindex="0"
              @click="selectSession(session)"
              @keydown.enter.prevent="selectSession(session)"
              @keydown.space.prevent="selectSession(session)"
              class="w-full text-left px-3 py-2.5 rounded-lg text-sm text-gray-700 hover:bg-gray-50 hover:text-teal-700 transition-colors block group/item relative"
            >
              <div class="flex items-center gap-2 min-w-0">
                <MessageSquare class="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span class="truncate block flex-1 pr-8">{{ session.title }}</span>
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full flex items-center justify-center text-gray-300 opacity-0 group-hover/item:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all disabled:opacity-60"
                  :disabled="deletingSessionId === session.id"
                  title="删除会话"
                  @click="deleteSession(session, $event)"
                >
                  <Trash2 v-if="deletingSessionId !== session.id" class="w-3.5 h-3.5" />
                  <Clock v-else class="w-3.5 h-3.5 animate-spin" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: transparent;
  border-radius: 20px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
}
</style>
