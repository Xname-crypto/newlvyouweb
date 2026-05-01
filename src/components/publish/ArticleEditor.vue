<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { 
  Undo, Redo, Heading1, List, ListOrdered, Quote, 
  Image as ImageIcon, Smile, Loader2 
} from 'lucide-vue-next';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Placeholder from '@tiptap/extension-placeholder';
import Underline from '@tiptap/extension-underline';

const props = defineProps<{
    title: string;
    content: string;
    loading?: boolean;
}>();

const emit = defineEmits(['update:title', 'update:content', 'publish', 'save']);

const editor = useEditor({
  content: props.content,
  extensions: [
    StarterKit,
    Image,
    Underline,
    Placeholder.configure({
      placeholder: '粘贴到这里或输入文字...',
    }),
  ],
  editorProps: {
    attributes: {
      class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-5 focus:outline-none min-h-[300px] list-disc list-decimal',
    },
  },
  onUpdate: ({ editor }) => {
    emit('update:content', editor.getHTML());
  },
});

watch(() => props.content, (newContent) => {
  if (editor.value && newContent !== editor.value.getHTML()) {
    editor.value.commands.setContent(newContent, { emitUpdate: false });
  }
});

const wordCount = computed(() => {
    // Simple word count from text content
    return editor.value?.storage.characterCount?.words() || 0;
    // Or just fallback to text length if characterCount extension not installed
    // return editor.value?.getText().length || 0;
});

// Using text length for now as per previous implementation logic
const charCount = computed(() => {
    return editor.value?.getText().length || 0;
});

const addImage = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      // In a real app, upload file here and get URL
      // For now, use object URL
      const url = URL.createObjectURL(file);
      if (editor.value) {
        editor.value.chain().focus().setImage({ src: url }).run();
      }
    }
  };
  input.click();
};

const updateTitle = (e: Event) => {
    emit('update:title', (e.target as HTMLInputElement).value);
};

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<template>
  <div class="flex flex-col h-full min-h-[600px] relative">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-medium text-gray-800">新的创作</h2>
    </div>

    <!-- Editor Container -->
    <div class="flex-1 flex flex-col bg-white rounded-lg">
      <!-- Toolbar -->
      <div v-if="editor" class="flex items-center space-x-6 py-4 border-b border-gray-100">
        <div class="flex items-center space-x-4 text-gray-400">
            <button 
                @click="editor.chain().focus().undo().run()"
                :disabled="!editor.can().chain().focus().undo().run()"
                class="hover:text-gray-600 transition-colors disabled:opacity-50"
            >
                <Undo class="w-5 h-5" />
            </button>
            <button 
                @click="editor.chain().focus().redo().run()"
                :disabled="!editor.can().chain().focus().redo().run()"
                class="hover:text-gray-600 transition-colors disabled:opacity-50"
            >
                <Redo class="w-5 h-5" />
            </button>
        </div>
        <div class="w-px h-4 bg-gray-200"></div>
        <div class="flex items-center space-x-4 text-gray-400">
            <button 
                @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
                :class="{ 'text-gray-900': editor.isActive('heading', { level: 1 }) }"
                class="hover:text-gray-600 transition-colors"
            >
                <Heading1 class="w-5 h-5" />
            </button>
            <button 
                @click="editor.chain().focus().toggleBulletList().run()"
                :class="{ 'text-gray-900': editor.isActive('bulletList') }"
                class="hover:text-gray-600 transition-colors"
            >
                <List class="w-5 h-5" />
            </button>
            <button 
                @click="editor.chain().focus().toggleOrderedList().run()"
                :class="{ 'text-gray-900': editor.isActive('orderedList') }"
                class="hover:text-gray-600 transition-colors"
            >
                <ListOrdered class="w-5 h-5" />
            </button>
            <button 
                @click="editor.chain().focus().toggleBlockquote().run()"
                :class="{ 'text-gray-900': editor.isActive('blockquote') }"
                class="hover:text-gray-600 transition-colors"
            >
                <Quote class="w-5 h-5" />
            </button>
        </div>
        <div class="w-px h-4 bg-gray-200"></div>
        <div class="flex items-center space-x-4 text-gray-400">
             <!-- Removed Highlighter as requested -->
             <button @click="addImage" class="hover:text-gray-600 transition-colors"><ImageIcon class="w-5 h-5" /></button>
             <button class="hover:text-gray-600 transition-colors"><Smile class="w-5 h-5" /></button>
        </div>
      </div>

      <!-- Input Area -->
      <div class="flex-1 py-6 flex flex-col overflow-y-auto">
        <input 
          :value="title"
          @input="updateTitle"
          type="text" 
          placeholder="输入标题" 
          class="text-3xl font-bold placeholder-gray-300 border-none outline-none w-full mb-6 bg-transparent px-5"
        />
        <editor-content :editor="editor" class="flex-1 outline-none" />
      </div>
    </div>

    <!-- Bottom Bar -->
    <div class="absolute bottom-0 left-0 w-full bg-white pt-4 pb-0 flex items-center justify-between border-t border-transparent">
        <div class="flex items-center space-x-4">
            <button 
                @click="emit('publish')"
                :disabled="loading"
                class="px-6 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded text-sm transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed flex items-center"
            >
                <Loader2 v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
                {{ loading ? '发布中...' : '发布' }}
            </button>
            <button 
                @click="emit('save')"
                :disabled="loading"
                class="px-6 py-2 border border-gray-200 text-gray-600 font-medium rounded text-sm hover:bg-gray-50 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
            >
                {{ loading ? '保存中...' : '暂存草稿' }}
            </button>
        </div>
        <div class="text-gray-400 text-sm">
            字数: {{ charCount }}
        </div>
    </div>
  </div>
</template>

<style>
/* Custom list styles for Tiptap */
.prose ul {
  list-style-type: disc;
  padding-left: 1.625em;
}

.prose ol {
  list-style-type: decimal;
  padding-left: 1.625em;
}

.prose li {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose h1 {
  font-size: 2.25em;
  font-weight: 800;
  margin-bottom: 0.8888889em;
}

.prose blockquote {
  font-weight: 500;
  font-style: italic;
  color: #111827;
  border-left-width: 0.25rem;
  border-left-color: #e5e7eb;
  margin-top: 1.6em;
  margin-bottom: 1.6em;
  padding-left: 1em;
}

/* Placeholder styling */
.ProseMirror p.is-editor-empty:first-child::before {
  color: #9ca3af;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
