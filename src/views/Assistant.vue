<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import Sidebar from '@/components/community/Sidebar.vue';
import Navigation from '@/components/Navigation.vue';
import HistorySidebar from '@/components/assistant/HistorySidebar.vue';
import ImageLoading from '@/components/assistant/ImageLoading.vue';
import { Search, Sparkles, Mic, Paperclip, Image as ImageIcon, ImagePlus, Palette, LayoutGrid, Globe, CornerDownLeft, Copy, RotateCw, ThumbsUp, ThumbsDown, X, Brain, Check, Bot } from 'lucide-vue-next';
import { assistantService, type AssistantMessage, type AssistantSession } from '@/services/assistantService';
import { supabase } from '@/utils/supabase';
import { useRouter } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { apiUrl } from '@/utils/apiBase';

const query = ref('');
const messages = ref<AssistantMessage[]>([]);
const currentSessionId = ref<string | null>(null);
const historySidebarRef = ref<any>(null);
const messagesContainer = ref<HTMLElement | null>(null);
const router = useRouter();
const { showToast } = useToast();
const isGenerating = ref(false);
const isSubmitting = ref(false); // 新增：用于追踪整个提交过程的状态
const loadingType = ref<'text' | 'image'>('text');
const isRecording = ref(false);

// 防抖控制
const lastSubmitTime = ref(0);
const DEBOUNCE_MS = 1500; // 1.5秒内不允许重复提交
const submitStatusText = ref(''); // 显示当前提交状态

// Model Selection
const models = ref<any[]>([]);
const selectedModel = ref<any>(null);
const activeLeftTool = ref<string | null>(null);
const leftHighlight = ref<'search' | 'image' | 'model' | null>('search');
const isKnowledgeBaseEnabled = ref(false);
const searchState = ref<'active' | 'popover' | null>(null);

const imageModels = ref<any[]>([]);
const selectedImageModel = ref<any>(null);

const fetchModels = async () => {
  const response = await fetch(apiUrl('/api/api-providers/public/?capability=chat&capability=image'));
  if (!response.ok) return;
  const payload = await response.json();
  const providers = payload?.data || [];
  const chatProviders = providers.filter((p: any) => p.capability === 'chat');
  const imgProviders = providers.filter((p: any) => p.capability === 'image');

  if (chatProviders) {
    models.value = chatProviders.map((p: any) => {
      let icon = Bot;
      if (p.name.includes('星火')) icon = Sparkles;
      if (p.name.includes('OpenAI')) icon = Brain;
      if (p.name.includes('Flash')) icon = Sparkles;

      let modelId = p.config?.model_id;
      if (!modelId) {
        if (p.name.includes('星火')) modelId = 'spark-lite';
        else if (p.name.includes('智谱')) modelId = 'glm-4-flash';
        else if (p.name.includes('DeepSeek')) modelId = 'deepseek-chat';
        else if (p.name.includes('OpenAI')) modelId = 'gpt-4o-mini';
        else modelId = p.name;
      }
      
      return {
        id: modelId,
        name: p.name,
        description: p.name.includes('定制') ? '旅游专属微调模型' : (p.config?.model_id || '通用大模型'),
        icon: icon,
        provider_id: p.id // Keep track of provider ID
      };
    });
    
    // Set default selected model (first one, which is highest priority)
    if (models.value.length > 0) {
      selectedModel.value = models.value[0];
    }
  }

  if (imgProviders) {
    imageModels.value = imgProviders.map((p: any) => {
      let icon = ImageIcon;
      if (p.name.includes('Doubao')) icon = Palette;
      if (p.name.includes('Silicon')) icon = ImagePlus;
      if (p.name.includes('Midjourney')) icon = ImageIcon;

      return {
        id: p.config?.model_id || p.name,
        name: p.name,
        desc: p.config?.model_id || 'AI 绘图',
        icon: icon,
        provider_id: p.id
      };
    });

    if (imageModels.value.length > 0) {
      selectedImageModel.value = imageModels.value[0];
    }
  }
};

const selectModel = (model: any) => {
  selectedModel.value = model;
  activeLeftTool.value = null; // Close menu state but keep highlight on 'model'
};

onMounted(() => {
  fetchModels();
  activeLeftTool.value = null;
  searchState.value = 'active';
  leftHighlight.value = 'search';
});
let recognition: any = null;
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);

// Initialize Speech Recognition
const initSpeechRecognition = () => {
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';

    recognition.onstart = () => {
      isRecording.value = true;
      showToast('正在聆听...', 'info');
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0])
        .map((result: any) => result.transcript)
        .join('');
      
      // If it's final result, append to query
      if (event.results[0].isFinal) {
        query.value += transcript;
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      isRecording.value = false;
      showToast('语音识别出错: ' + event.error, 'error');
    };

    recognition.onend = () => {
      isRecording.value = false;
    };
  } else {
    showToast('您的浏览器不支持语音输入', 'error');
  }
};

const toggleVoiceInput = () => {
  if (!recognition) {
    initSpeechRecognition();
  }

  if (isRecording.value) {
    recognition.stop();
  } else {
    recognition.start();
  }
};


const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    
    // Check file type
    if (!file.type.startsWith('image/')) {
      showToast('请上传图片文件', 'warning');
      return;
    }
    
    selectedFile.value = file;
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewUrl.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
    
    // Reset file input so same file can be selected again if needed
    input.value = '';
  }
};

const triggerFileUpload = () => {
  fileInput.value?.click();
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const removeSelectedFile = () => {
  selectedFile.value = null;
  previewUrl.value = null;
};

const handleSubmit = async () => {
  // Allow submit if there is text OR an image
  const q = query.value.trim();
  if (!q && !selectedFile.value) return;

  // 防抖检查：1.5秒内不允许重复提交
  const now = Date.now();
  if (now - lastSubmitTime.value < DEBOUNCE_MS) {
    showToast('操作太频繁，请稍后再试', 'warning');
    return;
  }

  // Prevent double submission
  if (isSubmitting.value || isGenerating.value) return;

  lastSubmitTime.value = now;
  isSubmitting.value = true;
  submitStatusText.value = '准备发送...';

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      showToast('请先登录', 'warning');
      router.push('/login');
      isSubmitting.value = false;
      submitStatusText.value = '';
      return;
    }

    // Create session if not exists
    if (!currentSessionId.value) {
      try {
        submitStatusText.value = '创建会话...';
        const title = q ? (q.substring(0, 30) + (q.length > 30 ? '...' : '')) : '图片分享';
        const newSession = await assistantService.createSession(title);
        currentSessionId.value = newSession.id;
        // Refresh sidebar
        if (historySidebarRef.value) {
          historySidebarRef.value.refresh();
        }
      } catch (error) {
        console.error('Error creating session:', error);
        showToast('创建会话失败', 'error');
        isSubmitting.value = false;
        submitStatusText.value = '';
        return;
      }
    }

    // Save user message
    try {
      submitStatusText.value = '发送消息...';
      let imageUrl = undefined;

      // Handle Image Upload First if exists
      if (selectedFile.value) {
        try {
          imageUrl = await assistantService.uploadImage(selectedFile.value);
        } catch (error: any) {
          console.error('Upload failed:', error);
          showToast('图片上传失败: ' + error.message, 'error');
          isSubmitting.value = false;
          return; // Stop processing if upload fails
        }
      }

      // Save user message (with text and/or image)
      // If no text but has image, use default text
      const content = q || (imageUrl ? '我分享了一张图片' : '');
      const userMsg = await assistantService.saveMessage(currentSessionId.value!, 'user', content, imageUrl);
      
      messages.value.push(userMsg);
      
      // Clear inputs
      query.value = '';
      removeSelectedFile();
      scrollToBottom();

      // AI Response Logic
      let aiResponse = "";
      let aiImageUrl = undefined;
      let startTime = Date.now();
      let latency = 0;

      isGenerating.value = true;
      loadingType.value = 'text';

      // 1. Image Analysis Flow
      if (imageUrl) {
         try {
           // Trigger image analysis
           const analysis = await assistantService.analyzeImage(imageUrl, q); // Pass user query as prompt if available
           aiResponse = analysis;
         } catch (err: any) {
           console.error('Image analysis failed:', err);
           aiResponse = `抱歉，图片分析失败了: ${err.message || '未知错误'}`;
         } finally {
           latency = Date.now() - startTime;
         }
      } 
      // 2. Image Generation Flow (Text -> Image)
      else if (activeLeftTool.value === 'image' || q.includes('画') || q.includes('生成') || q.includes('图')) {
         try {
          loadingType.value = 'image';
          const modelId = selectedImageModel.value?.id || 'doubao-seedream-5-0-260128';
          const generatedUrl = await assistantService.generateImage(q, modelId);
          aiImageUrl = generatedUrl;
         } catch (err: any) {
          console.error('Image generation failed:', err);
          aiResponse = `抱歉，图片生成失败了: ${err.message || '未知错误'}`;
         } finally {
          latency = Date.now() - startTime;
          activeLeftTool.value = null;
         }
      } 
      // 3. Text Chat Flow
      else {
        try {
          // Prepare context
          // const context = messages.value.map(m => ({
          //   role: m.role,
          //   content: m.content
          // })).slice(-10);

          // Django RAG 只需要最新的 user_input，历史记录由后端维护
          // 但为了保持前端逻辑一致，我们依然传递 context，assistantService 会处理
          const context = messages.value.map(m => ({
            role: m.role,
            content: m.content
          }));

          submitStatusText.value = isKnowledgeBaseEnabled.value ? '正在检索知识库...' : '正在生成回答...';
          const result = await assistantService.chat(
            context,
            selectedModel.value?.id || 'glm-4-flash',
            isKnowledgeBaseEnabled.value,
            selectedModel.value?.provider_id
          );
          submitStatusText.value = '正在生成回答...';
          if (typeof result === 'string') {
            aiResponse = result;
          } else {
            aiResponse = result.content;
            aiImageUrl = result.imageUrl;
            // TODO: Handle personality update if needed
            if (result.personality) {
               console.log('Updated personality:', result.personality);
            }
          }
        } catch (err: any) {
          console.error('Chat API Error:', err);
          aiResponse = `抱歉，我遇到了一些问题: ${err.message}`;
        } finally {
          latency = Date.now() - startTime;
        }
      }

      isGenerating.value = false;
      submitStatusText.value = '';

      // Save Assistant Message
      const assistantMsg = await assistantService.saveMessage(currentSessionId.value!, 'assistant', aiResponse, aiImageUrl);
      assistantMsg.latency = latency;
      messages.value.push(assistantMsg);
      scrollToBottom();

    } catch (error) {
      console.error('Error saving message:', error);
      showToast('发送消息失败', 'error');
      isGenerating.value = false;
      submitStatusText.value = '';
    }
  } catch (globalError) {
    console.error('Global error in submit:', globalError);
    showToast('发生意外错误', 'error');
    submitStatusText.value = '';
  } finally {
    isSubmitting.value = false;
  }
};

const handleSelectSession = async (session: AssistantSession) => {
  currentSessionId.value = session.id;
  messages.value = await assistantService.getMessages(session.id);
  scrollToBottom();
};

const handleDeleteSession = (sessionId: string) => {
  if (currentSessionId.value === sessionId) {
    currentSessionId.value = null;
    messages.value = [];
    query.value = '';
  }
};

const handleNewChat = () => {
  currentSessionId.value = null;
  messages.value = [];
  query.value = '';
};
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col pt-24">
    <Navigation class="!bg-white/95 !backdrop-blur-sm shadow-sm text-black">
      <template #logo>
        <router-link to="/" class="text-4xl font-black text-red-500 tracking-tighter flex items-center" style="font-family: 'PangMenZhengDao', serif;">
          椿天社
        </router-link>
      </template>
    </Navigation>

    <div class="flex flex-1">
      <div class="hidden lg:block w-[240px] flex-shrink-0 h-[calc(100vh-96px)] sticky top-24">
        <Sidebar />
      </div>

      <main class="flex-1 min-w-0">
        <div class="relative h-[calc(100vh-96px)]">
          <!-- Chat Messages Area -->
          <div 
            v-if="messages.length > 0" 
            ref="messagesContainer"
            class="absolute top-0 left-0 w-full h-full overflow-y-auto px-4 pb-40"
          >
            <div class="max-w-3xl mx-auto py-8 space-y-8">
              <div v-for="msg in messages" :key="msg.id" class="flex flex-col gap-2">
                <!-- User Message -->
                <div v-if="msg.role === 'user'" class="flex justify-end">
                  <div class="flex flex-col items-end gap-2 max-w-[80%]">
                    <!-- Image Display for User -->
                    <div v-if="msg.imageUrl" class="relative rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-white">
                      <img 
                        :src="msg.imageUrl" 
                        alt="Uploaded Image" 
                        class="max-w-full h-auto max-h-[300px] object-contain"
                        @error="(e) => { (e.target as HTMLImageElement).style.display = 'none'; }" 
                      />
                    </div>
                    <!-- Text Display for User -->
                    <div v-if="msg.content" class="bg-gray-100 rounded-[20px] px-5 py-2.5 text-gray-800 text-base break-words">
                      {{ msg.content }}
                    </div>
                  </div>
                </div>
                
                <!-- Assistant Message -->
                <div v-else class="flex gap-4">
                  <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 border border-gray-200 bg-white">
                    <img src="@/assets/my-avatar.png" alt="Assistant" class="w-full h-full object-cover" />
                  </div>
                  <div class="flex-1 space-y-2">
                    <div class="flex items-center gap-2 text-xs text-gray-500 font-medium mb-1" v-if="msg.latency">
                      <div class="flex items-center gap-1">
                        <span>已思考 (用时 {{ (msg.latency / 1000).toFixed(1) }} 秒)</span>
                      </div>
                    </div>
                    <div v-if="msg.content" class="text-gray-800 text-base leading-relaxed whitespace-pre-wrap">{{ msg.content }}</div>
                    
                    <!-- Image Display -->
                    <div v-if="msg.imageUrl" class="mt-2 relative">
                      <img 
                        :src="msg.imageUrl" 
                        alt="Generated Image" 
                        class="rounded-lg max-w-full h-auto shadow-sm"
                        @error="(e) => { (e.target as HTMLImageElement).style.display = 'none'; console.error('Image load failed:', msg.imageUrl); }" 
                      />
                    </div>

                    <!-- Action Buttons -->
                    <div class="flex items-center gap-1 mt-2">
                      <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors" title="Copy">
                        <Copy class="w-4 h-4" />
                      </button>
                      <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors" title="Regenerate">
                        <RotateCw class="w-4 h-4" />
                      </button>
                      <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors" title="Good">
                        <ThumbsUp class="w-4 h-4" />
                      </button>
                      <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors" title="Bad">
                        <ThumbsDown class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Loading Indicator -->
              <ImageLoading v-if="isGenerating && loadingType === 'image'" :type="loadingType" class="animate-fade-in" />
              
              <!-- Text Loading Indicator -->
              <div v-else-if="isGenerating && loadingType === 'text'" class="flex items-center gap-2 text-gray-500 text-sm px-4 animate-fade-in">
                <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 border border-gray-200 bg-white">
                  <img src="@/assets/my-avatar.png" alt="Assistant" class="w-full h-full object-cover" />
                </div>
                <div class="flex items-center gap-2 bg-gray-50 px-4 py-2 rounded-2xl rounded-tl-none">
                  <RotateCw class="w-3 h-3 animate-spin" />
                  <span>{{ submitStatusText || '正在思考中...' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Search/Input Area -->
          <div 
            class="transition-all duration-500 ease-in-out px-4 pointer-events-none"
            :class="messages.length > 0 
              ? 'fixed bottom-0 right-0 z-10 lg:left-[240px] left-0 pb-8 pt-12 bg-gradient-to-t from-white via-white to-transparent' 
              : 'w-full fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 -mt-8 lg:pl-[240px]'"
          >
            <div class="max-w-3xl mx-auto pointer-events-auto">
              <!-- Initial Welcome Header -->
              <div 
                class="mb-8 text-center transition-opacity duration-300"
                :class="messages.length > 0 ? 'opacity-0 h-0 overflow-hidden mb-0' : 'opacity-100'"
              >
                <div class="text-6xl font-black text-slate-800 tracking-tighter flex justify-center items-center gap-2">
                  <span class="text-red-500" style="font-family: 'PangMenZhengDao', serif;">椿天社</span>
                  <span class="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">期待与你相遇</span>
                </div>
              </div>
              
              <!-- Search Container -->
              <div class="bg-white rounded-[32px] border border-gray-200 shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-4 flex flex-col gap-4 pointer-events-auto">
                <!-- Input Area -->
                <div v-if="selectedFile" class="relative w-fit group mb-2">
                  <img :src="previewUrl!" class="h-20 w-auto rounded-lg border border-gray-200 object-cover" />
                  <button 
                    @click="removeSelectedFile"
                    class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow-md hover:bg-red-600 transition-colors"
                  >
                    <X class="w-3 h-3" />
                  </button>
                </div>
                <textarea
                  v-model="query"
                  placeholder="Ask anything..."
                  class="w-full text-lg placeholder-gray-400 text-gray-800 outline-none resize-none bg-transparent h-12 py-2 disabled:opacity-50"
                  @keydown.enter.prevent="handleSubmit"
                  :disabled="isSubmitting || isGenerating"
                ></textarea>
                
                <!-- Tools Row -->
                <div class="flex items-center justify-between">
                  <!-- Left Tools -->
                  <div class="flex items-center gap-2">
                    <div class="relative inline-flex">
                      <button 
                        class="w-8 h-8 flex items-center justify-center transition-all duration-200"
                        :class="leftHighlight === 'search' ? 'rounded-xl text-red-500 border-2 border-red-500 bg-red-50' : 'rounded-full text-gray-500 hover:bg-gray-100'"
                        title="Focus"
                        @click="
                          (() => {
                            const comingFromOther = activeLeftTool && activeLeftTool !== 'search';
                            activeLeftTool = 'search';
                            leftHighlight = 'search';
                            if (searchState === null) {
                              searchState = comingFromOther ? 'popover' : 'active';
                            } else if (searchState === 'active') {
                              searchState = 'popover';
                            } else {
                              searchState = null;
                              activeLeftTool = null;
                            }
                            if (searchState) { 
                              const chuntiansheModel = models.find(m => m.id.includes('travel'));
                              if (chuntiansheModel) {
                                selectedModel = chuntiansheModel;
                              }
                            }
                          })()
                        "
                      >
                        <Search class="w-4 h-4" />
                      </button>
                      <div 
                        v-if="searchState === 'popover'" 
                        class="absolute left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.1)] border border-gray-100 z-50 w-72 animate-fade-in"
                        :class="messages.length > 0 ? 'bottom-full mb-3 origin-bottom' : 'top-full mt-3 origin-top'"
                      >
                        <div 
                          class="absolute w-3 h-3 bg-white transform rotate-45 z-0 border-gray-100"
                          :class="messages.length > 0 ? '-bottom-1.5 left-1/2 -translate-x-1/2 border-r border-b' : '-top-1.5 left-1/2 -translate-x-1/2 border-l border-t'"
                        ></div>
                        <div class="p-3 space-y-2 relative z-10 bg-white rounded-xl">
                          <div class="flex items-center justify-between">
                            <div class="text-sm font-bold text-gray-900">椿天社定制版</div>
                            <span class="text-[10px] bg-red-50 px-1.5 py-0.5 rounded text-red-500 font-bold">椿天社</span>
                          </div>
                          <div class="text-xs text-gray-500 leading-relaxed">
                            旅游专属微调模型，结合热门景点、玩法与动线规划，更贴合出行与攻略创作场景。
                          </div>
                          <div class="flex items-center justify-between pt-1">
                            <div class="text-[11px] text-gray-400">已设为当前模型</div>
                            <button 
                              class="px-3 py-1.5 text-xs rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                              @click="searchState = 'active'; activeLeftTool = 'search'"
                            >知道了</button>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="relative inline-flex">
                      <button 
                        class="w-8 h-8 flex items-center justify-center transition-all duration-200"
                        :class="leftHighlight === 'image' 
                          ? 'rounded-xl text-red-500 border-2 border-red-500 bg-red-50' 
                          : 'rounded-full text-gray-500 hover:bg-gray-100'"
                        title="文生图"
                        @click="leftHighlight = 'image'; activeLeftTool = activeLeftTool === 'image' ? null : 'image'; searchState = null"
                      >
                        <ImageIcon class="w-4 h-4" />
                      </button>
                      <div 
                        v-if="activeLeftTool === 'image'" 
                        class="absolute left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.1)] border border-gray-100 z-50 w-64 animate-fade-in"
                        :class="messages.length > 0 ? 'bottom-full mb-3 origin-bottom' : 'top-full mt-3 origin-top'"
                      >
                        <div 
                          class="absolute w-3 h-3 bg-white transform rotate-45 z-0 border-gray-100"
                          :class="messages.length > 0 ? '-bottom-1.5 left-1/2 -translate-x-1/2 border-r border-b' : '-top-1.5 left-1/2 -translate-x-1/2 border-l border-t'"
                        ></div>
                        <div class="p-2 space-y-1 relative z-10 bg-white rounded-xl">
                          <div class="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center justify-between">
                            <span>选择生图模型</span>
                            <span class="text-[10px] bg-red-50 px-1.5 py-0.5 rounded text-red-500 font-bold">椿天社</span>
                          </div>
                        <button
                            v-for="im in imageModels"
                            :key="im.id"
                            @click="selectedImageModel = im; activeLeftTool = null; searchState = null"
                            class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-3"
                            :class="selectedImageModel?.id === im.id ? 'bg-red-50 text-red-600' : 'text-gray-700'"
                          >
                            <div class="w-7 h-7 rounded-md flex items-center justify-center bg-gray-100 text-gray-500">
                              <component :is="im.icon" class="w-3.5 h-3.5" />
                            </div>
                            <div class="min-w-0 flex-1">
                              <div class="truncate">{{ im.name }}</div>
                              <div class="text-[10px] text-gray-400 truncate" :class="selectedImageModel?.id === im.id ? 'text-red-400' : ''">{{ im.desc }}</div>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                    <!-- Model Selection -->
                    <div class="relative group">
                      <button 
                        class="w-8 h-8 flex items-center justify-center transition-all duration-200 relative"
                        :class="leftHighlight === 'model' 
                          ? 'rounded-xl text-red-500 border-2 border-red-500 bg-red-50' 
                          : 'rounded-full text-gray-500 hover:bg-gray-100'"
                        title="选择模型"
                        @click="leftHighlight = 'model'; activeLeftTool = activeLeftTool === 'model' ? null : 'model'; searchState = null"
                      >
                        <LayoutGrid class="w-4 h-4" />
                      </button>
                      
                      <!-- Model Menu -->
                      <div 
                        v-if="activeLeftTool === 'model'" 
                        class="absolute bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.1)] border border-gray-100 z-50 animate-fade-in w-64"
                        :class="messages.length > 0 ? 'bottom-full mb-3 left-0 origin-bottom-left' : 'top-full mt-3 left-0 origin-top-left'"
                      >
                        <!-- Arrow -->
                        <div 
                          class="absolute w-3 h-3 bg-white transform rotate-45 z-0 border-gray-100"
                          :class="messages.length > 0 ? '-bottom-1.5 left-3 border-r border-b' : '-top-1.5 left-3 border-l border-t'"
                        ></div>
                        
                        <div class="p-2 space-y-1 relative z-10 bg-white rounded-xl">
                          <div class="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center justify-between">
                            <span>选择模型</span>
                            <span class="text-[10px] bg-red-50 px-1.5 py-0.5 rounded text-red-500 font-bold">椿天社</span>
                          </div>
                            <button 
                            v-for="model in models" 
                            :key="model.id"
                            @click="selectModel(model)"
                            class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-3 group/item relative"
                            :class="{'bg-red-50/50': selectedModel?.id === model.id}"
                          >
                            <div 
                              class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors"
                              :class="selectedModel?.id === model.id ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-500 group-hover/item:bg-white group-hover/item:text-red-500 group-hover/item:shadow-sm'"
                            >
                              <component :is="model.icon" class="w-4 h-4" />
                            </div>
                            <div class="flex-1 min-w-0">
                              <div 
                              class="text-sm font-medium transition-colors relative"
                              :class="selectedModel?.id === model.id ? 'text-red-700' : 'text-gray-700 group-hover/item:text-gray-900'"
                            >
                              <span class="relative">
                                {{ model.name }}
                                <span v-if="model.id.includes('travel')" class="text-[9px] bg-red-50 text-red-600 px-1 rounded-sm absolute -right-8 top-0 scale-75 origin-left font-bold">定制</span>
                              </span>
                            </div>
                              <div class="text-xs text-gray-400 truncate group-hover/item:text-gray-500">
                                {{ model.description }}
                              </div>
                            </div>
                            <div v-if="selectedModel?.id === model.id" class="absolute right-2 top-1/2 -translate-y-1/2 text-red-600">
                              <Check class="w-4 h-4" />
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Right Tools -->
                  <div class="flex items-center gap-2">
                    <button 
                      @click="isKnowledgeBaseEnabled = !isKnowledgeBaseEnabled; searchState = 'active'" 
                      class="w-8 h-8 rounded-full flex items-center justify-center transition-colors" 
                      :class="isKnowledgeBaseEnabled ? 'bg-teal-50 text-teal-600 border border-teal-200' : 'text-gray-500 hover:bg-gray-100'"
                      :title="isKnowledgeBaseEnabled ? '知识库已启用' : '启用知识库'"
                      :aria-pressed="isKnowledgeBaseEnabled"
                    >
                      <Globe class="w-4 h-4" />
                    </button>
                    <!-- Pro button removed per request -->
                    <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleFileUpload" />
                    <button @click="triggerFileUpload(); searchState = 'active'" class="w-8 h-8 rounded-full text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors" title="Attach">
                      <Paperclip class="w-4 h-4" />
                    </button>
                    <button @click="toggleVoiceInput(); searchState = 'active'" class="w-8 h-8 rounded-full text-gray-500 hover:bg-gray-100 flex items-center justify-center transition-colors" :class="{'text-red-500 bg-red-50 animate-pulse': isRecording}" title="Voice">
                      <Mic class="w-4 h-4" />
                    </button>
                    <button 
                      @click="handleSubmit(); searchState = 'active'" 
                      class="w-8 h-8 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed" 
                      :disabled="isSubmitting || isGenerating"
                      title="发送"
                    >
                      <RotateCw v-if="isSubmitting || isGenerating" class="w-4 h-4 animate-spin" />
                      <CornerDownLeft v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div 
                class="text-center text-xs text-gray-400 mt-8 flex items-center justify-center gap-1 transition-opacity duration-300"
                :class="messages.length > 0 ? 'opacity-0 h-0 overflow-hidden mt-0' : 'opacity-100'"
              >
                <span>椿天社 用心规划你的旅程 · 由 许博钧</span>
                <span class="text-red-500">♥</span>
                <span>创作</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <HistorySidebar 
        ref="historySidebarRef"
        @select-session="handleSelectSession"
        @new-chat="handleNewChat"
        @delete-session="handleDeleteSession"
      />
    </div>
  </div>
</template>
