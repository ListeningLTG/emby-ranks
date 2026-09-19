<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
    <transition-group 
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div 
        v-for="t in toasts" 
        :key="t.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-xl text-sm font-medium"
        :class="getToastClass(t.type)"
      >
        <span class="text-base">{{ getIcon(t.type) }}</span>
        <span class="flex-1 text-slate-100 leading-snug">{{ t.message }}</span>
        <button @click="removeToast(t.id)" class="text-slate-400 hover:text-white transition">✕</button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { toasts, removeToast } from '../utils/toast'

function getToastClass(type) {
  switch (type) {
    case 'success':
      return 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
    case 'error':
      return 'bg-rose-950/90 border-rose-500/40 text-rose-200'
    case 'warning':
      return 'bg-amber-950/90 border-amber-500/40 text-amber-200'
    default:
      return 'bg-slate-900/90 border-indigo-500/40 text-indigo-200'
  }
}

function getIcon(type) {
  switch (type) {
    case 'success': return '✅'
    case 'error': return '❌'
    case 'warning': return '⚠️'
    default: return 'ℹ️'
  }
}
</script>
