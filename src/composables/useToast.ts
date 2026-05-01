import { ref } from 'vue';

interface ToastState {
  isVisible: boolean;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

const state = ref<ToastState>({
  isVisible: false,
  message: '',
  type: 'info',
});

let timer: any = null;

export const useToast = () => {
  const showToast = (message: string, type: ToastState['type'] = 'info', duration = 3000) => {
    if (timer) clearTimeout(timer);
    
    state.value = {
      isVisible: true,
      message,
      type,
    };

    timer = setTimeout(() => {
      hideToast();
    }, duration);
  };

  const hideToast = () => {
    state.value.isVisible = false;
  };

  return {
    state,
    showToast,
    hideToast,
  };
};
