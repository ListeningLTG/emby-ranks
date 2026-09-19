import { ref } from 'vue';

export const toasts = ref([]);

export function showToast(message, type = 'info', duration = 3500) {
  const id = Date.now() + Math.random();
  const toast = { id, message, type };
  toasts.value.push(toast);

  setTimeout(() => {
    removeToast(id);
  }, duration);
}

export function removeToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id);
}
