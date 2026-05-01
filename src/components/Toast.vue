<script setup lang="ts">
import { useToast } from '@/composables/useToast';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-vue-next';

const { state, hideToast } = useToast();

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const colors = {
  success: 'bg-green-50 text-green-700 border-green-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  info: 'bg-blue-50 text-blue-700 border-blue-200',
  warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
};
</script>

<template>
  <Transition
    enter-active-class="transform ease-out duration-300 transition"
    enter-from-class="translate-y-[-100%] opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition ease-in duration-200"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="state.isVisible"
      class="fixed top-6 left-1/2 -translate-x-1/2 z-[9999] flex items-center shadow-lg rounded-full px-6 py-3 border min-w-[300px] max-w-[90vw]"
      :class="colors[state.type]"
    >
      <component :is="icons[state.type]" class="w-5 h-5 mr-3 flex-shrink-0" />
      <span class="text-sm font-medium flex-1 text-center">{{ state.message }}</span>
      <button @click="hideToast" class="ml-3 p-1 hover:bg-black/5 rounded-full transition-colors">
        <X class="w-4 h-4" />
      </button>
    </div>
  </Transition>
</template>
