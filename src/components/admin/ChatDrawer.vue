<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed, onUnmounted } from 'vue';
import { X, Send, ChevronLeft, Search, MessageSquare, Phone, Video, MoreHorizontal, Paperclip, Smile } from 'lucide-vue-next';
import { chatService, type Message } from '@/services/chatService';
import { supabase } from '@/utils/supabase';
import { usePresence } from '@/composables/usePresence';

const props = defineProps<{
  isOpen: boolean;
  sidebarWidth: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const { onlineUsers, initPresence, cleanupPresence } = usePresence();

interface Contact {
  id: string;
  username: string;
  avatar_url: string;
  job: string;
  role: string;
  lastMessage?: string;
  lastMessageTime?: string;
  unreadCount?: number;
}

const contacts = ref<Contact[]>([]);
const activeContact = ref<Contact | null>(null);
const messages = ref<Message[]>([]);
const messagesLoading = ref(false);
const newMessage = ref('');
const loading = ref(false);
const messageContainer = ref<HTMLElement | null>(null);
const currentUser = ref<string | null>(null);
const currentUserProfile = ref<any>(null);
const searchQuery = ref('');
const activeTab = ref<'all' | 'unread'>('all');

const filteredContacts = computed(() => {
  let result = contacts.value;

  // Filter by tab
  if (activeTab.value === 'unread') {
    result = result.filter(c => c.unreadCount && c.unreadCount > 0);
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(contact => 
      contact.username?.toLowerCase().includes(query) || 
      contact.job?.toLowerCase().includes(query)
    );
  }
  
  return result;
});

const CONTACT_PANEL_WIDTH = 320;
const isContactPanelCollapsed = ref(false);
const contactPanelWidth = computed(() => (isContactPanelCollapsed.value ? 0 : CONTACT_PANEL_WIDTH));
const sidebarOffsetStyle = computed(() => ({ left: `${props.sidebarWidth}px` }));
const contactPanelStyle = computed(() => ({
  left: `${props.sidebarWidth}px`,
  width: `${contactPanelWidth.value}px`
}));
const chatPanelStyle = computed(() => ({ left: `${props.sidebarWidth + contactPanelWidth.value}px` }));
const toggleContactPanel = () => {
  isContactPanelCollapsed.value = !isContactPanelCollapsed.value;
};
let latestMessageRequestId = 0;

// Fetch current user and contacts on mount
onMounted(async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (user) {
    currentUser.value = user.id;
    // Fetch user profile for display
    const { data: profile } = await supabase.from('profiles').select('*').eq('id', user.id).single();
    currentUserProfile.value = profile;
    
    await fetchContacts();
    initPresence();
    initSubscription(); // Initialize global subscription
  }
});

onUnmounted(() => {
  cleanupPresence();
});

// Fetch contacts list
const fetchContacts = async () => {
  try {
    loading.value = true;
    const profiles = await chatService.getContacts();
    
    if (!profiles || profiles.length === 0) {
      contacts.value = [];
      return;
    }

    // Fetch unread counts and last messages
    const [unreadCounts, lastMessages] = await Promise.all([
      chatService.getUnreadCounts(),
      chatService.getLastMessagesEfficiently(profiles.map((p: any) => p.id))
    ]);

    contacts.value = profiles.map((p: any) => ({
      ...p,
      unreadCount: unreadCounts[p.id] || 0,
      lastMessage: lastMessages[p.id]?.content || '点击开始聊天...',
      lastMessageTime: lastMessages[p.id]?.created_at
    }));

    // Sort by last message time (newest first)
    contacts.value.sort((a, b) => {
      if (!a.lastMessageTime) return 1;
      if (!b.lastMessageTime) return -1;
      return new Date(b.lastMessageTime).getTime() - new Date(a.lastMessageTime).getTime();
    });

  } catch (error) {
    console.error('Failed to fetch contacts:', error);
  } finally {
    loading.value = false;
  }
};

// Select a contact and load messages
const selectContact = async (contact: Contact) => {
  const requestId = ++latestMessageRequestId;
  activeContact.value = contact;
  messagesLoading.value = true;
  messages.value = [];
  
  // Mark as read locally
  if (contact.unreadCount && contact.unreadCount > 0) {
    contact.unreadCount = 0;
    // Mark as read on server
    chatService.markAsRead(contact.id);
  }
  
  await loadMessages(contact.id, requestId);

  if (requestId !== latestMessageRequestId || activeContact.value?.id !== contact.id) {
    return;
  }

  scrollToBottom();
  // We don't need to re-subscribe here, as we have a global subscription
  // Just ensure we mark messages as read in a real app
};

// Load message history
const loadMessages = async (contactId: string, requestId = latestMessageRequestId) => {
  try {
    const data = await chatService.getMessages(contactId);

    if (requestId !== latestMessageRequestId || activeContact.value?.id !== contactId) {
      return;
    }

    messages.value = data || [];
  } catch (error) {
    console.error('Failed to load messages:', error);
  } finally {
    if (requestId === latestMessageRequestId && activeContact.value?.id === contactId) {
      messagesLoading.value = false;
    }
  }
};

  // Subscribe to real-time messages
  let subscription: any = null;
  const initSubscription = () => {
    if (subscription) subscription.unsubscribe();
    
    subscription = supabase
      .channel(`chat:${currentUser.value}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `receiver_id=eq.${currentUser.value}` // Listen for messages sent to me
        },
        (payload) => {
          const msg = payload.new as Message;
          // If the message is from the active contact, add it
          if (activeContact.value && msg.sender_id === activeContact.value.id) {
            messages.value.push(msg);
            scrollToBottom();
            // Mark as read immediately since we are looking at the chat
            chatService.markAsRead(msg.sender_id);
          } else {
            // Optional: Increment unread count or show notification
            const sender = contacts.value.find(c => c.id === msg.sender_id);
            if (sender) {
               sender.unreadCount = (sender.unreadCount || 0) + 1;
               sender.lastMessage = msg.content; // Update preview
               sender.lastMessageTime = new Date().toISOString();
               
               // Move sender to top of list
               const index = contacts.value.indexOf(sender);
               if (index > 0) {
                 contacts.value.splice(index, 1);
                 contacts.value.unshift(sender);
               }
            }
          }
        }
      )
      .subscribe();
  };

// Send a message
const sendMessage = async () => {
  if (!newMessage.value.trim() || !activeContact.value) return;

  const content = newMessage.value;
  newMessage.value = ''; // Clear input immediately for better UX

  try {
    // Optimistic update
    const tempMessage: Message = {
      id: Date.now(), // Temporary ID
      sender_id: currentUser.value!,
      receiver_id: activeContact.value.id,
      content: content,
      type: 'text',
      created_at: new Date().toISOString()
    };
    messages.value.push(tempMessage);
    scrollToBottom();

    // Send to server
    await chatService.sendMessage(activeContact.value.id, content);
    
    // In a real app, we might replace the temp message with the server response
  } catch (error) {
    console.error('Failed to send message:', error);
    // Remove optimistic message on error or show error state
  }
};

// Scroll to bottom of chat
const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  });
};

// Format time short
const formatTimeShort = (isoString?: string) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '';
  
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  
  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else {
    return date.toLocaleDateString();
  }
};

// Format time
const formatTime = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  
  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
};

// Close drawer
const close = () => {
  emit('close');
};
</script>

<template>
  <div v-if="isOpen" class="pointer-events-none fixed inset-0 z-30">
    <!-- Backdrop (Covers only the main content area, starting from left-64) -->
    <div 
      class="pointer-events-auto fixed inset-y-0 right-0 bg-slate-900/10 backdrop-blur-[2px] z-40 transition-opacity"
      :style="sidebarOffsetStyle"
      @click="close"
    ></div>

    <!-- Contact List Panel (Fixed next to sidebar) -->
    <div 
      class="pointer-events-auto fixed top-0 bottom-0 bg-white z-50 flex flex-col border-r border-slate-100 overflow-hidden transition-[width,opacity] duration-300 ease-in-out"
      :class="isContactPanelCollapsed ? 'pointer-events-none opacity-0 border-r-0' : 'opacity-100'"
      :style="contactPanelStyle"
    >
      <!-- User Profile Header -->
      <div class="p-6 pb-2 pr-16">
        <div class="mb-6 flex items-start gap-3">
          <div class="flex min-w-0 items-center gap-3">
            <div class="relative">
              <img 
                :src="currentUserProfile?.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin'" 
                class="w-12 h-12 rounded-full object-cover bg-slate-100"
              >
              <div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
            </div>
            <div class="min-w-0">
              <h3 class="font-bold text-slate-900 truncate">{{ currentUserProfile?.username || '管理员' }}</h3>
              <p class="text-xs text-slate-500 truncate">{{ currentUserProfile?.job || (currentUserProfile?.role === 'admin' ? '管理员' : (currentUserProfile?.role === 'moderator' ? '审核员' : '前端开发人员')) }}</p>
            </div>
          </div>
        </div>

        <!-- Search -->
        <div class="relative mb-6">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="请输入搜索内容..." 
            class="w-full pl-10 pr-4 py-2.5 bg-slate-50 border-none rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 text-slate-700 placeholder:text-slate-400 transition-all focus:outline-none"
          >
        </div>

        <!-- Tabs -->
        <div class="flex items-center gap-6 mb-4">
          <button 
            @click="activeTab = 'all'"
            class="text-sm font-medium pb-1 transition-colors relative"
            :class="activeTab === 'all' ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'"
          >
            全部
            <div v-if="activeTab === 'all'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"></div>
          </button>
          <button 
            @click="activeTab = 'unread'"
            class="text-sm font-medium pb-1 transition-colors relative"
            :class="activeTab === 'unread' ? 'text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-600'"
          >
            未读
            <div v-if="activeTab === 'unread'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"></div>
          </button>
        </div>
      </div>

      <!-- Contact List -->
      <div class="flex-1 overflow-y-auto px-4 pb-4 space-y-1">
        <div v-if="loading" class="flex justify-center py-8">
          <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
        
        <button 
          v-for="contact in filteredContacts" 
          :key="contact.id"
          @click="selectContact(contact)"
          class="w-full flex items-start gap-3 p-3 rounded-2xl transition-all group relative"
          :class="activeContact?.id === contact.id ? 'bg-blue-50/50' : 'hover:bg-slate-50'"
        >
          <div class="relative flex-shrink-0">
            <img 
              :src="contact.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + contact.username" 
              class="w-10 h-10 rounded-full bg-slate-100 object-cover"
              alt="Avatar"
            >
            <!-- Online indicator -->
            <div 
              class="absolute bottom-0 right-0 w-2.5 h-2.5 border-2 border-white rounded-full transition-colors"
              :class="onlineUsers.has(contact.id) ? 'bg-green-500' : 'bg-slate-300'"
            ></div>
          </div>
          <div class="flex-1 min-w-0 text-left">
            <div class="flex items-center justify-between mb-0.5">
              <span class="font-bold text-slate-900 truncate text-sm">{{ contact.username || '未命名用户' }}</span>
              <span v-if="contact.lastMessageTime" class="text-[10px] text-slate-400">{{ formatTimeShort(contact.lastMessageTime) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="text-xs text-slate-500 truncate pr-2 flex-1">{{ contact.lastMessage || contact.job || (contact.role === 'admin' ? '管理员' : '审核员') }}</div>
              <span v-if="contact.unreadCount" class="bg-rose-500 text-white text-[10px] font-bold px-1.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full">{{ contact.unreadCount }}</span>
            </div>
          </div>
          <!-- Active Indicator Arrow -->
          <div v-if="activeContact?.id === contact.id" class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-l-full"></div>
        </button>

        <!-- Meeting Section Mock -->
        <div class="mt-8 mb-4 px-2">
          <h3 class="text-sm font-bold text-slate-900 mb-4">Meetings</h3>
          <div class="bg-slate-50 p-4 rounded-2xl mb-3 border border-slate-100">
            <div class="font-bold text-slate-800 text-sm mb-1">日常设计会议</div>
            <div class="flex items-center gap-2 text-xs text-blue-500 mb-3">
              <span>10:00 - 11:20</span>
              <span class="text-slate-400">2小时后开始</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex -space-x-2">
                <div class="w-6 h-6 rounded-full bg-slate-200 border-2 border-white"></div>
                <div class="w-6 h-6 rounded-full bg-slate-300 border-2 border-white"></div>
                <div class="w-6 h-6 rounded-full bg-slate-400 border-2 border-white flex items-center justify-center text-[8px] text-white font-bold">+3</div>
              </div>
              <button class="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium hover:bg-blue-700 transition-colors">参加</button>
            </div>
          </div>
        </div>
      </div>

      <button
        class="absolute right-6 top-[2.2rem] flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-700"
        type="button"
        title="收起联系人面板"
        @click="toggleContactPanel"
      >
        <ChevronLeft class="h-4 w-4" />
      </button>
    </div>

    <!-- Chat Area Panel (Fixed next to contact list) -->
    <div 
      class="pointer-events-auto fixed top-0 bottom-0 right-0 bg-white z-40 flex flex-col shadow-xl animate-in fade-in duration-200 transition-[left] ease-in-out duration-300"
      :style="chatPanelStyle"
    >
      <button
        v-if="isContactPanelCollapsed"
        class="absolute left-4 top-[2.2rem] z-20 flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-400 shadow-sm transition-colors hover:bg-slate-50 hover:text-slate-700"
        type="button"
        title="展开联系人面板"
        @click="toggleContactPanel"
      >
        <ChevronLeft class="h-4 w-4 rotate-180" />
      </button>
      <template v-if="activeContact">
        <!-- Chat Header -->
        <div
          class="h-20 border-b border-slate-100 bg-white flex items-center justify-between flex-shrink-0 shadow-sm z-10 transition-[padding] duration-300"
          :class="isContactPanelCollapsed ? 'pl-16 pr-8' : 'px-8'"
        >
          <div class="flex items-center gap-4">
            <img 
              :src="activeContact.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + activeContact.username" 
              class="w-10 h-10 rounded-full bg-slate-100 object-cover"
            >
            <div>
              <h2 class="font-bold text-slate-900 text-base">{{ activeContact.username }}</h2>
              <p class="text-xs text-slate-500">{{ activeContact.job || (activeContact.role === 'admin' ? '管理员' : '审核员') }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="p-2.5 bg-slate-50 text-slate-400 rounded-xl hover:bg-blue-50 hover:text-blue-500 transition-colors">
              <Phone class="w-4 h-4" />
            </button>
            <button class="p-2.5 bg-slate-50 text-slate-400 rounded-xl hover:bg-blue-50 hover:text-blue-500 transition-colors">
              <Video class="w-4 h-4" />
            </button>
            <div class="w-px h-6 bg-slate-100 mx-1"></div>
            <button @click="activeContact = null" class="p-2.5 bg-slate-50 text-slate-400 rounded-xl hover:bg-rose-50 hover:text-rose-500 transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Messages List -->
        <div 
          ref="messageContainer"
          class="chat-message-surface relative flex-1 overflow-y-auto p-8 space-y-6"
        >
          <div class="chat-message-surface__backdrop" aria-hidden="true">
            <div class="chat-message-surface__orb chat-message-surface__orb--top"></div>
            <div class="chat-message-surface__orb chat-message-surface__orb--bottom"></div>
            <div class="chat-message-surface__wordmark">椿天社</div>
          </div>
          <!-- Date Separator Mock -->
          <div v-if="!messagesLoading && messages.length > 0" class="relative z-[1] flex justify-center">
            <span class="text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1 rounded-full">今天</span>
          </div>

          <div v-if="messagesLoading" class="relative z-[1] flex h-64 items-center justify-center">
            <div class="flex flex-col items-center gap-3 text-slate-400">
              <div class="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-500"></div>
              <p class="text-sm font-medium text-slate-500">加载聊天记录中...</p>
            </div>
          </div>

          <div 
            v-show="!messagesLoading"
            v-for="msg in messages" 
            :key="msg.id"
            class="relative z-[1] flex gap-4 group"
            :class="msg.sender_id === currentUser ? 'flex-row-reverse' : ''"
          >
            <img 
              :src="msg.sender_id === currentUser 
                ? (currentUserProfile?.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin')
                : (activeContact.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + activeContact.username)" 
              class="w-10 h-10 rounded-xl bg-slate-200 object-cover mt-1 flex-shrink-0"
            >
            
            <div class="max-w-[60%]">
              <div v-if="msg.sender_id !== currentUser" class="text-xs text-slate-500 mb-1 ml-1">{{ activeContact.username }}</div>
              <div 
                class="px-5 py-3.5 rounded-2xl text-sm shadow-sm leading-relaxed"
                :class="msg.sender_id === currentUser 
                  ? 'bg-white text-slate-800 rounded-tr-sm border border-slate-100' 
                  : 'bg-white text-slate-800 rounded-tl-sm border border-slate-100'"
              >
                <p>{{ msg.content }}</p>
              </div>
              <div 
                class="text-[10px] mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400"
                :class="msg.sender_id === currentUser ? 'text-right' : 'text-left'"
              >
                {{ formatTime(msg.created_at) }}
              </div>
            </div>
          </div>
          
          <div v-if="!messagesLoading && messages.length === 0" class="relative z-[1] flex flex-col items-center justify-center h-64 text-slate-400">
            <MessageSquare class="w-12 h-12 mb-3 text-slate-200" />
            <p class="text-sm">暂无消息，开始聊天吧！</p>
          </div>
        </div>

        <!-- Input Area -->
        <div class="p-6 bg-white border-t border-slate-100">
          <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-2 flex items-center gap-2 focus-within:ring-2 focus-within:ring-blue-500/10 focus-within:border-blue-500/50 transition-all outline-none">
            <div class="flex items-center gap-1 pl-2">
              <img 
                :src="currentUserProfile?.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin'" 
                class="w-8 h-8 rounded-full object-cover bg-slate-100"
              >
            </div>
            
            <input 
              v-model="newMessage"
              @keyup.enter="sendMessage"
              type="text" 
              placeholder="请输入您的信息..." 
              class="flex-1 bg-transparent border-none text-sm focus:ring-0 focus:outline-none text-slate-700 placeholder:text-slate-400 px-3 h-10"
            >
            
            <div class="flex items-center gap-1 pr-1">
              <button class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                <Smile class="w-5 h-5" />
              </button>
              <button class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                <Paperclip class="w-5 h-5" />
              </button>
              <button 
                @click="sendMessage"
                :disabled="!newMessage.trim()"
                class="ml-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                发送
              </button>
            </div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <div v-else class="chat-empty-surface relative flex-1 overflow-hidden">
        <button @click="close" class="absolute top-6 right-8 z-[2] p-2 hover:bg-slate-200 rounded-full text-slate-400 hover:text-slate-600 transition-colors">
          <X class="w-5 h-5" />
        </button>
        <div class="chat-empty-surface__backdrop" aria-hidden="true">
          <div class="chat-empty-surface__orb chat-empty-surface__orb--top"></div>
          <div class="chat-empty-surface__orb chat-empty-surface__orb--bottom"></div>
          <div class="chat-empty-surface__wordmark">椿天社</div>
        </div>
        <div class="chat-empty-surface__content relative z-[1] flex h-full flex-col items-center justify-center text-slate-400">
          <MessageSquare class="mb-4 h-12 w-12 text-slate-200" />
          <p class="text-sm font-medium text-slate-500">选择一位联系人开始聊天</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-empty-surface {
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.96) 0%, rgba(255, 255, 255, 1) 24%, rgba(248, 250, 252, 0.92) 100%);
}

.chat-empty-surface__backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.chat-empty-surface__orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(20px);
  opacity: 0.55;
}

.chat-empty-surface__orb--top {
  top: 3rem;
  right: 10%;
  width: 13rem;
  height: 13rem;
  background: radial-gradient(circle, rgba(191, 219, 254, 0.18) 0%, rgba(255, 255, 255, 0) 72%);
}

.chat-empty-surface__orb--bottom {
  left: 9%;
  bottom: 3.5rem;
  width: 15rem;
  height: 15rem;
  background: radial-gradient(circle, rgba(251, 207, 232, 0.14) 0%, rgba(255, 255, 255, 0) 74%);
}

.chat-empty-surface__wordmark {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-family: 'PangMenZhengDao', serif;
  font-size: clamp(4.75rem, 9vw, 7rem);
  line-height: 1;
  letter-spacing: 0.08em;
  color: rgba(148, 163, 184, 0.14);
  white-space: nowrap;
  user-select: none;
}

.chat-empty-surface__content {
  display: none;
}

.chat-message-surface {
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.82) 0%, rgba(255, 255, 255, 0.96) 22%, rgba(248, 250, 252, 0.7) 100%);
}

.chat-message-surface__backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.chat-message-surface__orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(18px);
  opacity: 0.45;
}

.chat-message-surface__orb--top {
  top: 2.5rem;
  right: 8%;
  width: 12rem;
  height: 12rem;
  background: radial-gradient(circle, rgba(191, 219, 254, 0.22) 0%, rgba(255, 255, 255, 0) 72%);
}

.chat-message-surface__orb--bottom {
  left: 10%;
  bottom: 3rem;
  width: 14rem;
  height: 14rem;
  background: radial-gradient(circle, rgba(251, 207, 232, 0.16) 0%, rgba(255, 255, 255, 0) 74%);
}

.chat-message-surface__wordmark {
  position: absolute;
  left: 50%;
  top: 46%;
  transform: translate(-50%, -50%);
  font-family: 'PangMenZhengDao', serif;
  font-size: clamp(5rem, 10vw, 8rem);
  line-height: 1;
  color: rgba(148, 163, 184, 0.13);
  letter-spacing: 0.08em;
  white-space: nowrap;
  user-select: none;
}

/* Custom scrollbar for webkit browsers */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
