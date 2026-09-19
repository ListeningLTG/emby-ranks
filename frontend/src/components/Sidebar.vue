<template>
  <aside class="w-64 bg-dark-900/90 border-r border-slate-800/80 backdrop-blur-2xl flex flex-col justify-between shrink-0 h-screen sticky top-0 z-40 select-none">
    <div>
      <!-- 品牌 Logo 区域 -->
      <div class="h-16 px-6 flex items-center gap-3 border-b border-slate-800/60">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-glow text-lg">
          📊
        </div>
        <div>
          <h1 class="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
            Emby-Ranks
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">v1.0</span>
          </h1>
          <p class="text-[11px] text-slate-400">媒体统计与榜单中心</p>
        </div>
      </div>

      <!-- 导航列表 -->
      <div class="px-3 py-6 space-y-1.5">
        <div class="px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">核心功能</div>

        <button 
          @click="$emit('update:tab', 'dashboard')"
          :class="currentTab === 'dashboard' 
            ? 'bg-indigo-600/15 text-indigo-400 border-indigo-500/30 font-semibold shadow-sm' 
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border-transparent'"
          class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-sm transition-all text-left group"
        >
          <span class="text-base transition-transform group-hover:scale-110">📊</span>
          <span>监控大屏</span>
        </button>

        <button 
          @click="$emit('update:tab', 'posters')"
          :class="currentTab === 'posters' 
            ? 'bg-indigo-600/15 text-indigo-400 border-indigo-500/30 font-semibold shadow-sm' 
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border-transparent'"
          class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-sm transition-all text-left group"
        >
          <span class="text-base transition-transform group-hover:scale-110">🎨</span>
          <span>海报工坊</span>
        </button>

        <div class="px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider mt-6 mb-2">系统管理</div>

        <button 
          @click="$emit('update:tab', 'settings')"
          :class="currentTab === 'settings' 
            ? 'bg-indigo-600/15 text-indigo-400 border-indigo-500/30 font-semibold shadow-sm' 
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border-transparent'"
          class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-sm transition-all text-left group"
        >
          <span class="text-base transition-transform group-hover:scale-110">⚙️</span>
          <span>系统配置</span>
        </button>
      </div>
    </div>

    <!-- 侧边栏底部信息 -->
    <div class="p-4 border-t border-slate-800/60">
      <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full" :class="status.emby?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'"></div>
          <span class="text-xs text-slate-300 truncate max-w-[120px]">{{ status.emby?.server_name || '未配置' }}</span>
        </div>
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">{{ status.jobs?.length || 0 }} 任务</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  currentTab: String,
  status: Object
})
defineEmits(['update:tab'])
</script>
