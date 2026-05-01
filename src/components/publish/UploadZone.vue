<script setup lang="ts">
import { ref } from 'vue';
import { Image, Video } from 'lucide-vue-next';

const props = defineProps<{
    accept?: string
}>();

const isDragging = ref(false);
const emit = defineEmits(['files-selected']);

const handleDrop = (e: DragEvent) => {
  isDragging.value = false;
  if (e.dataTransfer?.files) {
    emit('files-selected', Array.from(e.dataTransfer.files));
  }
};

const handleFileInput = (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (input.files) {
    emit('files-selected', Array.from(input.files));
  }
};

const triggerFileInput = () => {
  document.getElementById('file-upload')?.click();
};
</script>

<template>
  <div 
    class="w-full h-[400px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-colors cursor-pointer group bg-gray-50/50 relative"
    :class="isDragging ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-red-300'"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <input 
      id="file-upload" 
      type="file" 
      class="hidden" 
      multiple 
      :accept="accept || 'video/*,image/*'"
      @change="handleFileInput"
    />
    
    <div class="mb-8 relative h-20 w-full flex items-center justify-center">
        <!-- Background Icon (Always Image) -->
        <div class="w-20 h-16 bg-gray-200 rounded-lg flex items-center justify-center transform -rotate-12 absolute shadow-sm">
            <Image class="w-8 h-8 text-white" />
        </div>
        
        <!-- Foreground Icon (Changes based on accept type) -->
        <div class="w-20 h-16 bg-gray-300 rounded-lg flex items-center justify-center transform rotate-6 shadow-md z-10 relative">
             <Video v-if="accept?.includes('video')" class="w-8 h-8 text-white" />
             <Image v-else class="w-8 h-8 text-white" />
        </div>
    </div>
    
    <p class="text-gray-400 text-sm mb-6 mt-12">拖拽{{ accept?.includes('video') ? '视频' : '图片' }}到此处</p>
    
    <button 
        @click.stop="triggerFileInput"
        class="px-8 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-full transition-all shadow-md hover:shadow-lg flex items-center space-x-2"
    >
      <span>{{ accept?.includes('video') ? '上传视频' : '上传图片' }}</span>
    </button>
  </div>
</template>
