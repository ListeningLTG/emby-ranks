<template>
  <header class="h-16 px-8 border-b border-slate-800/80 bg-dark-900/60 backdrop-blur-md flex items-center justify-between sticky top-0 z-30">
    <!-- 面包屑 / 页面标题 -->
    <div class="flex items-center gap-2 text-sm">
      <span class="text-slate-400">控制台</span>
      <span class="text-slate-600">/</span>
      <span class="font-semibold text-white capitalize">{{ getTitle(currentTab) }}</span>
    </div>

    <!-- 顶部右侧快捷状态与操作 -->
    <div class="flex items-center gap-3">
      <!-- Emby 连通状态徽章 -->
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium"
           :class="status.emby?.connected 
             ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' 
             : 'bg-rose-950/40 border-rose-500/30 text-rose-300'">
        <span class="w-1.5 h-1.5 rounded-full" :class="status.emby?.connected ? 'bg-emerald-400' : 'bg-rose-400'"></span>
        <span>{{ status.emby?.connected ? 'Emby 已连接' : 'Emby 离线/未配置' }}</span>
      </div>

      <!-- 刷新按钮 -->
      <button 
        @click="$emit('refresh')"
        :disabled="loading"
        class="btn btn-secondary text-xs py-1.5 px-3 rounded-lg"
      >
        <span :class="{'animate-spin': loading}">🔄</span>
        <span>刷新数据</span>
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  currentTab: String,
  status: Object,
  loading: Boolean
})
defineEmits(['refresh'])

function getTitle(tab) {
  switch (tab) {
    case 'dashboard': return '监控大屏'
    case 'posters': return '海报工坊'
    case 'settings': return '系统配置'
    default: return '仪表盘'
  }
}
</script>
