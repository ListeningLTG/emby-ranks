<template>
  <div class="min-h-screen flex bg-dark-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
    <!-- 左侧常驻导航栏 -->
    <Sidebar 
      :current-tab="currentTab" 
      :status="status"
      @update:tab="currentTab = $event" 
    />

    <!-- 右侧内容主干 -->
    <div class="flex-1 flex flex-col min-w-0">
      <Header 
        :current-tab="currentTab" 
        :status="status" 
        :loading="refreshing"
        @refresh="refreshAll" 
      />

      <main class="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
        <Dashboard v-if="currentTab === 'dashboard'" :status="status" @nav="currentTab = $event" ref="dashRef" />
        <Posters v-else-if="currentTab === 'posters'" />
        <Settings v-else-if="currentTab === 'settings'" />
      </main>

      <!-- 底部简易版权 -->
      <footer class="h-10 px-8 border-t border-slate-800/40 text-center text-xs text-slate-500 flex items-center justify-center">
        Emby-Ranks · 专注于轻量与自动化的 Emby 媒体榜单系统
      </footer>
    </div>

    <!-- 全局 Toast 浮动提示容器 -->
    <Toast />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Header from './components/Header.vue'
import Toast from './components/Toast.vue'
import Dashboard from './views/Dashboard.vue'
import Posters from './views/Posters.vue'
import Settings from './views/Settings.vue'
import { fetchStatus } from './api'
import { showToast } from './utils/toast'

const currentTab = ref('dashboard')
const status = ref({})
const refreshing = ref(false)
const dashRef = ref(null)

async function loadStatus() {
  try {
    status.value = await fetchStatus()
  } catch (e) {
    console.error(e)
  }
}

async function refreshAll() {
  refreshing.value = true
  try {
    await loadStatus()
    if (dashRef.value && typeof dashRef.value.loadSessions === 'function') {
      await Promise.all([
        dashRef.value.loadSessions(),
        dashRef.value.loadMediaRanks(1),
        dashRef.value.loadUserRanks(7)
      ])
    }
    showToast('数据已刷新！', 'success')
  } catch (e) {
    showToast('刷新异常: ' + e.message, 'error')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>
