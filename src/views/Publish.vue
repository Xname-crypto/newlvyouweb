<script setup lang="ts">
import { ref, onMounted } from 'vue';
import PublishSidebar from '@/components/publish/PublishSidebar.vue';
import UploadZone from '@/components/publish/UploadZone.vue';
import ArticleEditor from '@/components/publish/ArticleEditor.vue';
import CreatorHeader from '@/components/CreatorHeader.vue';
import { Loader2 } from 'lucide-vue-next';
import { publishService } from '@/services/publishService';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const activeTab = ref('video');
const tabs = [
  { id: 'video', label: '上传视频' },
  { id: 'image', label: '上传图文' },
  { id: 'article', label: '写长文' },
];

const title = ref('');
const content = ref('');
const files = ref<File[]>([]);
const existingMedia = ref<string[]>([]);
const loading = ref(false);
const errorMsg = ref('');
const postId = ref<string | undefined>(undefined);

onMounted(async () => {
  if (route.query.id) {
    postId.value = route.query.id as string;
    loading.value = true;
    try {
      const post = await publishService.getPostById(postId.value);
      if (post) {
        title.value = post.title;
        content.value = post.content || '';
        activeTab.value = post.type;
        existingMedia.value = post.media_urls || [];
      }
    } catch (error) {
      console.error('Error loading post:', error);
      errorMsg.value = '加载笔记失败';
    } finally {
      loading.value = false;
    }
  }
});

const handleFilesSelected = (selectedFiles: File[]) => {
  files.value = selectedFiles;
  // Automatically switch tab based on file type if needed
  if (selectedFiles.length > 0) {
    const file = selectedFiles[0];
    if (file.type.startsWith('video/')) {
        activeTab.value = 'video';
    } else if (file.type.startsWith('image/')) {
        activeTab.value = 'image';
    }
  }
};

const getAcceptType = () => {
    if (activeTab.value === 'video') return 'video/*';
    if (activeTab.value === 'image') return 'image/*';
    return '*/*';
};

const handlePublish = async (status: 'published' | 'draft' = 'published') => {
  if (!title.value) {
    errorMsg.value = '请输入标题';
    return;
  }
  
  // Validate files only if published and not article
  if (status === 'published' && files.value.length === 0 && existingMedia.value.length === 0 && activeTab.value !== 'article') {
    errorMsg.value = '请上传文件';
    return;
  }

  try {
    loading.value = true;
    errorMsg.value = '';

    await publishService.createPost({
      id: postId.value,
      title: title.value,
      content: content.value,
      type: activeTab.value as any,
      files: files.value,
      media_urls: existingMedia.value,
      status: status
    });

    // Reset and redirect
    title.value = '';
    content.value = '';
    files.value = [];
    existingMedia.value = [];
    
    if (status === 'published') {
        router.push('/community');
    } else {
        router.push('/publish/notes');
    }
    
  } catch (error: any) {
    console.error(error);
    errorMsg.value = error.message || (status === 'published' ? '发布失败' : '保存失败');
  } finally {
    loading.value = false;
  }
};

const removeExistingMedia = (index: number) => {
    existingMedia.value.splice(index, 1);
};
</script>

<template>
  <div class="min-h-screen bg-[#f9f9f9] flex flex-col">
    <!-- Header -->
    <CreatorHeader />

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <PublishSidebar />

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="bg-white rounded-xl shadow-sm min-h-[600px] p-8 relative">
          <!-- Tabs -->
          <div class="flex space-x-8 border-b border-gray-100 mb-8">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              class="pb-4 text-base font-medium transition-colors relative"
              :class="activeTab === tab.id ? 'text-red-500' : 'text-gray-500 hover:text-gray-900'"
            >
              {{ tab.label }}
              <span v-if="activeTab === tab.id" class="absolute bottom-0 left-0 w-full h-0.5 bg-red-500 rounded-full"></span>
            </button>
            <div 
                @click="router.push('/publish/notes')"
                class="ml-auto flex items-center text-sm text-gray-400 cursor-pointer hover:text-gray-600"
            >
                <span class="mr-1">草稿箱</span>
            </div>
          </div>

          <!-- Article Editor -->
          <ArticleEditor 
            v-if="activeTab === 'article'" 
            v-model:title="title"
            v-model:content="content"
            :loading="loading"
            @publish="() => handlePublish('published')"
            @save="() => handlePublish('draft')"
          />

          <!-- Normal Upload Flow -->
          <template v-else>
            <!-- Content Form -->
            
            <!-- Existing Media List -->
            <div v-if="existingMedia.length > 0" class="mb-4 space-y-2">
                <div v-for="(url, index) in existingMedia" :key="index" class="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                     <div class="w-16 h-16 bg-gray-200 rounded overflow-hidden flex-shrink-0">
                        <img v-if="activeTab === 'image'" :src="url" class="w-full h-full object-cover" />
                        <video v-else-if="activeTab === 'video'" :src="url" class="w-full h-full object-cover"></video>
                        <div v-else class="w-full h-full flex items-center justify-center text-xs text-gray-500">文件</div>
                     </div>
                     <div class="flex-1">
                        <div class="text-sm font-medium text-gray-900 truncate">已上传文件 {{ index + 1 }}</div>
                     </div>
                     <button @click="removeExistingMedia(index)" class="text-sm text-red-500 hover:text-red-600">删除</button>
                </div>
            </div>

            <!-- New Files List -->
            <div v-if="files.length > 0" class="mb-8">
               <div class="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <div class="w-16 h-16 bg-gray-200 rounded overflow-hidden">
                      <!-- Preview (Simplified) -->
                      <div class="w-full h-full flex items-center justify-center text-xs text-gray-500">
                          {{ files[0].type.split('/')[0] }}
                      </div>
                  </div>
                  <div class="flex-1">
                      <div class="text-sm font-medium text-gray-900 truncate">{{ files[0].name }}</div>
                      <div class="text-xs text-gray-500">{{ (files[0].size / 1024 / 1024).toFixed(2) }} MB</div>
                  </div>
                  <button @click="files = []" class="text-sm text-red-500 hover:text-red-600">删除</button>
               </div>
            </div>

            <!-- Upload Area (Show only if no files and no existing media) -->
            <!-- Actually, user might want to add more files? But current UploadZone logic seems single-batch oriented? -->
            <!-- If we have files or existing media, we probably hide UploadZone if we only support 1 file/video. -->
            <!-- But for images, we might support multiple. For now, let's keep it simple: show UploadZone if nothing is there. -->
            <UploadZone 
                v-if="files.length === 0 && existingMedia.length === 0" 
                @files-selected="handleFilesSelected" 
                :accept="getAcceptType()" 
            />
            
            <!-- If we have files/media but want to allow adding more? -->
            <!-- Current logic: UploadZone emits files, we set files=selectedFiles. It replaces. -->
            <!-- So user can only upload one batch. -->

            <!-- Post Metadata Form -->
            <div class="mt-8 space-y-6 max-w-2xl">
              <div class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">标题</label>
                  <input 
                      v-model="title"
                      type="text" 
                      placeholder="填写标题会有更多赞哦~" 
                      class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all"
                  >
              </div>
              
              <div class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">正文</label>
                  <textarea 
                      v-model="content"
                      rows="4"
                      placeholder="填写更全面的描述信息，让更多人看到你吧！" 
                      class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all resize-none"
                  ></textarea>
              </div>

              <div v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</div>

              <div class="flex items-center space-x-4">
                  <button 
                      @click="() => handlePublish('published')"
                      :disabled="loading"
                      class="px-8 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-full transition-all shadow-md hover:shadow-lg disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center min-w-[120px]"
                  >
                      <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
                      {{ loading ? '发布中...' : '发布' }}
                  </button>
                  <button 
                      @click="() => handlePublish('draft')"
                      :disabled="loading"
                      class="px-8 py-3 border border-gray-200 text-gray-600 font-bold rounded-full transition-all hover:bg-gray-50 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center min-w-[120px]"
                  >
                      {{ loading ? '保存中...' : '存草稿' }}
                  </button>
              </div>
            </div>

            <!-- Footer Specs -->
            <div class="mt-12 grid grid-cols-3 gap-8 border-t border-gray-50 pt-8">
              <template v-if="activeTab === 'video'">
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">视频大小</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">支持时长60分钟以内，<br>最大20GB的视频文件</p>
                  </div>
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">视频格式</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">支持常用视频格式，<br>推荐使用mp4、mov</p>
                  </div>
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">视频分辨率</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">推荐上传720P（1280*720）及以上视频，<br>超过1080P的视频同网页端上传画质更清晰</p>
                  </div>
              </template>
              <template v-else-if="activeTab === 'image'">
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">图片大小</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">支持上传的图片大小，<br>最大32MB的图片文件</p>
                  </div>
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">图片格式</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">支持上传的图片格式，<br>推荐使用png、jpg、jpeg、webp，不支持gif、live及其转化后的图片</p>
                  </div>
                  <div class="space-y-2">
                      <h4 class="text-sm font-bold text-gray-700">图片分辨率</h4>
                      <p class="text-xs text-gray-400 leading-relaxed">不限制宽高比例，推荐上传3:4至2:1之间、分辨率不低于720*960的照片，<br>超过1280P的图片用网页端上传画质更清晰</p>
                  </div>
              </template>
            </div>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>
