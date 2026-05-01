<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import { 
  Undo, Redo, Heading1, List, ListOrdered, Quote, 
  Image as ImageIcon, Bold, Italic, Underline as UnderlineIcon
} from 'lucide-vue-next'
import { watch, onBeforeUnmount } from 'vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  minHeight?: string
}>()

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Image,
    Underline,
    Placeholder.configure({
      placeholder: props.placeholder || '请输入内容...',
    }),
  ],
  editorProps: {
    attributes: {
      class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-5 focus:outline-none min-h-[200px] list-disc list-decimal max-w-none',
    },
  },
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

// Watch for external content changes
watch(() => props.modelValue, (newValue) => {
  if (editor.value && newValue !== editor.value.getHTML()) {
    editor.value.commands.setContent(newValue, { emitUpdate: false })
  }
})

const addImage = () => {
  const url = window.prompt('请输入图片URL')
  if (url && editor.value) {
    editor.value.chain().focus().setImage({ src: url }).run()
  }
}

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="flex flex-col border border-slate-300 rounded-lg overflow-hidden bg-white focus-within:ring-2 focus-within:ring-slate-900 focus-within:border-transparent transition-all">
    <!-- Toolbar -->
    <div v-if="editor" class="flex items-center gap-1 p-2 border-b border-slate-100 bg-slate-50 flex-wrap">
      <button 
        @click="editor.chain().focus().undo().run()"
        :disabled="!editor.can().chain().focus().undo().run()"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 disabled:opacity-30 transition-colors"
        title="撤销"
      >
        <Undo class="w-4 h-4" />
      </button>
      <button 
        @click="editor.chain().focus().redo().run()"
        :disabled="!editor.can().chain().focus().redo().run()"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 disabled:opacity-30 transition-colors"
        title="重做"
      >
        <Redo class="w-4 h-4" />
      </button>
      
      <div class="w-px h-4 bg-slate-300 mx-1"></div>
      
      <button 
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('heading', { level: 2 }) }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="标题"
      >
        <Heading1 class="w-4 h-4" />
      </button>
      
      <button 
        @click="editor.chain().focus().toggleBold().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('bold') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="加粗"
      >
        <Bold class="w-4 h-4" />
      </button>
      
      <button 
        @click="editor.chain().focus().toggleItalic().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('italic') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="斜体"
      >
        <Italic class="w-4 h-4" />
      </button>

      <button 
        @click="editor.chain().focus().toggleUnderline().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('underline') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="下划线"
      >
        <UnderlineIcon class="w-4 h-4" />
      </button>
      
      <div class="w-px h-4 bg-slate-300 mx-1"></div>

      <button 
        @click="editor.chain().focus().toggleBulletList().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('bulletList') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="无序列表"
      >
        <List class="w-4 h-4" />
      </button>
      <button 
        @click="editor.chain().focus().toggleOrderedList().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('orderedList') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="有序列表"
      >
        <ListOrdered class="w-4 h-4" />
      </button>
      <button 
        @click="editor.chain().focus().toggleBlockquote().run()"
        :class="{ 'bg-slate-200 text-slate-900': editor.isActive('blockquote') }"
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="引用"
      >
        <Quote class="w-4 h-4" />
      </button>
      
      <div class="w-px h-4 bg-slate-300 mx-1"></div>
      
      <button 
        @click="addImage" 
        class="p-1.5 hover:bg-slate-200 rounded text-slate-600 transition-colors"
        title="插入图片"
      >
        <ImageIcon class="w-4 h-4" />
      </button>
    </div>

    <!-- Editor Content -->
    <editor-content 
      :editor="editor" 
      class="flex-1 p-2 overflow-y-auto outline-none custom-scrollbar"
      :style="{ minHeight: minHeight || '300px' }"
    />
  </div>
</template>

<style>
/* Scoped styles for prose inside this component */
.prose {
  font-size: 0.875rem; /* text-sm */
  line-height: 1.5;
}

.prose p {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose ul {
  list-style-type: disc;
  padding-left: 1.5em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose ol {
  list-style-type: decimal;
  padding-left: 1.5em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose blockquote {
  border-left: 3px solid #cbd5e1;
  padding-left: 1em;
  color: #475569;
  font-style: italic;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose img {
  border-radius: 0.375rem;
  max-width: 100%;
  height: auto;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
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
