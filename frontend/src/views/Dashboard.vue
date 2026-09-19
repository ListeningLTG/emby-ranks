<template>
  <div class="space-y-6">
    <!-- Emby 未连接引导提示 -->
    <div v-if="!status.emby?.connected" class="panel-card p-6 bg-gradient-to-r from-rose-950/40 via-purple-950/20 to-slate-900 border-rose-500/30">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-2xl shrink-0">
            ⚠️
          </div>
          <div>
            <h3 class="text-base font-bold text-white">尚未连接到 Emby 媒体服务器</h3>
            <p class="text-xs text-slate-400 mt-1">请前往「系统配置」填入你的 Emby 服务器地址、API 密钥并确保已安装 Playback Reporting 插件。</p>
          </div>
        </div>
        <button @click="$emit('nav', 'settings')" class="btn btn-primary text-xs shrink-0">
          ⚙️ 立即前往配置
        </button>
      </div>
    </div>

    <!-- 顶部 4 组指标统计大屏卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 1. 服务器卡片 -->
      <div class="stat-widget p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400">Emby 服务器</span>
          <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            🍿
          </div>
        </div>
        <div class="mt-4">
          <h4 class="text-lg font-bold text-white truncate">{{ status.emby?.server_name || '未命名' }}</h4>
          <p class="text-xs text-slate-400 font-mono mt-0.5 truncate">{{ status.emby?.url || '未配置' }}</p>
        </div>
      </div>

      <!-- 2. 正在播放 -->
      <div class="stat-widget p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400">活跃播放会话</span>
          <div class="w-9 h-9 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
            🎬
          </div>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-2xl font-black text-pink-400">{{ sessions.playing_count || 0 }}</span>
          <span class="text-xs text-slate-400">路正在串流</span>
        </div>
      </div>

      <!-- 3. 在线人数 -->
      <div class="stat-widget p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400">在线用户</span>
          <div class="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            👥
          </div>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-2xl font-black text-emerald-400">{{ sessions.online_count || 0 }}</span>
          <span class="text-xs text-slate-400">人当前活跃</span>
        </div>
      </div>

      <!-- 4. 定时调度 -->
      <div class="stat-widget p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400">定时调度器</span>
          <div class="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            ⏱️
          </div>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-2xl font-black text-amber-400">{{ status.jobs?.length || 0 }}</span>
          <span class="text-xs text-slate-400">项活跃任务</span>
        </div>
      </div>
    </div>

    <!-- 快捷手动触发栏 -->
    <div class="panel-card p-4 flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
        <span class="text-xs font-bold text-slate-300 uppercase tracking-wider">⚡ 快捷手动触发推送</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button @click="handleTrigger('day_rank')" :disabled="triggering" class="btn btn-secondary text-xs">
          🎬 推送播放日榜
        </button>
        <button @click="handleTrigger('week_rank')" :disabled="triggering" class="btn btn-secondary text-xs">
          🏆 推送播放周榜
        </button>
        <button @click="handleTrigger('day_play_rank')" :disabled="triggering" class="btn btn-secondary text-xs">
          🥇 推送用户时长日榜
        </button>
        <button @click="handleTrigger('week_play_rank')" :disabled="triggering" class="btn btn-secondary text-xs">
          🏅 推送用户时长周榜
        </button>
      </div>
    </div>

    <!-- 正在播放流 (Now Playing) -->
    <div v-if="sessions.playing_items && sessions.playing_items.length > 0" class="panel-card p-6 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-bold text-white flex items-center gap-2">
          <span>🎬 正在播放流 (Now Playing)</span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-pink-500/20 text-pink-300 font-mono">{{ sessions.playing_items.length }}</span>
        </h3>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(item, idx) in sessions.playing_items" :key="idx" 
             class="p-4 rounded-xl bg-dark-900/90 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between gap-3">
          <div class="flex items-start justify-between gap-2">
            <div class="truncate">
              <span class="text-[11px] font-medium text-slate-400">👤 {{ item.user_name }}</span>
              <h4 class="text-sm font-bold text-white truncate mt-0.5" :title="item.item_name">{{ item.item_name }}</h4>
            </div>
            <span class="text-[11px] px-2 py-0.5 rounded-md font-semibold shrink-0"
                  :class="item.is_paused ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'">
              {{ item.is_paused ? '⏸️ 已暂停' : '▶️ 播放中' }}
            </span>
          </div>

          <div class="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 font-mono">
            <span class="truncate max-w-[120px]">{{ item.client }}</span>
            <span class="truncate max-w-[120px] text-right">{{ item.device_name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 排行榜展示卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 1. 媒体播放榜单 -->
      <div class="panel-card p-6 space-y-6">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>🎬 热门媒体排行榜</span>
          </h3>
          <div class="flex bg-dark-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button @click="mediaTab = 1; loadMediaRanks(1)" 
                    :class="mediaTab === 1 ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="px-3.5 py-1.5 rounded-lg transition">今日日榜</button>
            <button @click="mediaTab = 7; loadMediaRanks(7)" 
                    :class="mediaTab === 7 ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="px-3.5 py-1.5 rounded-lg transition">本周周榜</button>
          </div>
        </div>

        <div v-if="loadingMedia" class="py-12 flex flex-col items-center justify-center text-slate-400 text-xs gap-2">
          <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <span>加载媒体排行数据中...</span>
        </div>

        <div v-else class="space-y-6">
          <!-- 电影榜 -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">🍿 电影 Top 10</span>
            </div>
            <div v-if="!mediaData.movies || mediaData.movies.length === 0" class="text-xs text-slate-500 py-3 text-center">暂无播放数据</div>
            <div v-else class="space-y-3">
              <div v-for="(m, idx) in mediaData.movies" :key="idx" class="space-y-1">
                <div class="flex items-center justify-between text-xs">
                  <div class="flex items-center gap-2 truncate pr-2">
                    <span class="w-5 font-bold font-mono text-center" 
                          :class="idx === 0 ? 'text-amber-400' : idx === 1 ? 'text-slate-300' : idx === 2 ? 'text-amber-600' : 'text-slate-500'">
                      {{ idx + 1 }}
                    </span>
                    <span class="font-medium text-slate-200 truncate">{{ m.name }}</span>
                  </div>
                  <span class="text-slate-400 font-mono shrink-0">
                    <b class="text-indigo-400">{{ m.play_count }}</b> 次 · {{ m.duration_str }}
                  </span>
                </div>
                <div class="rank-progress">
                  <div class="rank-progress-bar" 
                       :style="{ width: getPercentage(m.play_count, mediaData.movies[0]?.play_count) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 剧集榜 -->
          <div class="border-t border-slate-800/80 pt-5">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-bold text-pink-400 uppercase tracking-wider">📺 电视剧 Top 10</span>
            </div>
            <div v-if="!mediaData.tvshows || mediaData.tvshows.length === 0" class="text-xs text-slate-500 py-3 text-center">暂无播放数据</div>
            <div v-else class="space-y-3">
              <div v-for="(t, idx) in mediaData.tvshows" :key="idx" class="space-y-1">
                <div class="flex items-center justify-between text-xs">
                  <div class="flex items-center gap-2 truncate pr-2">
                    <span class="w-5 font-bold font-mono text-center" 
                          :class="idx === 0 ? 'text-amber-400' : idx === 1 ? 'text-slate-300' : idx === 2 ? 'text-amber-600' : 'text-slate-500'">
                      {{ idx + 1 }}
                    </span>
                    <span class="font-medium text-slate-200 truncate">{{ t.name }}</span>
                  </div>
                  <span class="text-slate-400 font-mono shrink-0">
                    <b class="text-pink-400">{{ t.play_count }}</b> 次 · {{ t.duration_str }}
                  </span>
                </div>
                <div class="rank-progress">
                  <div class="rank-progress-bar bg-gradient-to-r from-pink-500 to-purple-500" 
                       :style="{ width: getPercentage(t.play_count, mediaData.tvshows[0]?.play_count) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 用户时长排行榜 -->
      <div class="panel-card p-6 space-y-6">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>🏆 用户观影时长榜</span>
          </h3>
          <div class="flex bg-dark-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button @click="userTab = 1; userPage = 1; loadUserRanks(1, 1)" 
                    :class="userTab === 1 ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="px-3.5 py-1.5 rounded-lg transition">今日</button>
            <button @click="userTab = 7; userPage = 1; loadUserRanks(7, 1)" 
                    :class="userTab === 7 ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="px-3.5 py-1.5 rounded-lg transition">本周</button>
          </div>
        </div>

        <div v-if="loadingUsers" class="py-12 flex flex-col items-center justify-center text-slate-400 text-xs gap-2">
          <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <span>加载用户时长排行中...</span>
        </div>

        <div v-else>
          <div v-if="!userData.users || userData.users.length === 0" class="text-xs text-slate-500 py-12 text-center">暂无用户观看记录</div>
          <div v-else class="space-y-3">
            <div v-for="u in userData.users" :key="u.rank"
                 class="p-3 rounded-xl bg-dark-900/60 border border-slate-800/80 hover:border-slate-700 transition flex flex-col gap-2">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2.5">
                  <span class="text-base">
                    <template v-if="u.rank === 1">🥇</template>
                    <template v-else-if="u.rank === 2">🥈</template>
                    <template v-else-if="u.rank === 3">🥉</template>
                    <template v-else><span class="text-xs font-mono font-bold text-slate-500 ml-1">#{{ u.rank }}</span></template>
                  </span>
                  <span class="font-bold text-slate-200">{{ u.user_name }}</span>
                </div>
                <span class="font-mono text-emerald-400 font-semibold">{{ u.watch_time_str }}</span>
              </div>
              <div class="rank-progress">
                <div class="rank-progress-bar bg-gradient-to-r from-emerald-500 to-teal-400" 
                     :style="{ width: getPercentage(u.watch_time_seconds, userData.users[0]?.watch_time_seconds) + '%' }"></div>
              </div>
            </div>

            <!-- 分页控制栏 -->
            <div v-if="userData.total_pages > 1" class="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
              <button @click="changeUserPage(userPage - 1)" :disabled="userPage <= 1" class="btn btn-secondary py-1 px-3 text-xs">
                ◀️ 上一页
              </button>
              <span class="text-slate-400 font-mono">
                第 <b class="text-white">{{ userData.page }}</b> / {{ userData.total_pages }} 页 (共 {{ userData.total_users }} 人)
              </span>
              <button @click="changeUserPage(userPage + 1)" :disabled="userPage >= userData.total_pages" class="btn btn-secondary py-1 px-3 text-xs">
                下一页 ▶️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchSessions, fetchMediaRanks, fetchUserRanks, triggerTask } from '../api'
import { showToast } from '../utils/toast'

defineProps({
  status: Object
})
defineEmits(['nav'])

const sessions = ref({})
const mediaTab = ref(1)
const userTab = ref(7)
const userPage = ref(1)
const mediaData = ref({})
const userData = ref({})
const loadingMedia = ref(false)
const loadingUsers = ref(false)
const triggering = ref(false)

function getPercentage(val, max) {
  if (!max || max === 0) return 0
  return Math.min(100, Math.max(5, (val / max) * 100))
}

async function loadSessions() {
  try {
    sessions.value = await fetchSessions()
  } catch (e) {
    console.error(e)
  }
}

async function loadMediaRanks(days = 1) {
  loadingMedia.value = true
  try {
    mediaData.value = await fetchMediaRanks(days)
  } catch (e) {
    console.error(e)
  } finally {
    loadingMedia.value = false
  }
}

function changeUserPage(newPage) {
  if (newPage < 1 || newPage > (userData.value.total_pages || 1)) return
  userPage.value = newPage
  loadUserRanks(userTab.value, newPage)
}

async function loadUserRanks(days = 7, page = 1) {
  loadingUsers.value = true
  try {
    userData.value = await fetchUserRanks(days, page, 10)
    userPage.value = userData.value.page || 1
  } catch (e) {
    console.error(e)
  } finally {
    loadingUsers.value = false
  }
}

async function handleTrigger(taskName) {
  triggering.value = true
  try {
    const res = await triggerTask(taskName)
    showToast(res.message || '任务执行成功！', 'success')
  } catch (e) {
    showToast('触发失败: ' + e.message, 'error')
  } finally {
    triggering.value = false
  }
}

onMounted(() => {
  loadSessions()
  loadMediaRanks(1)
  loadUserRanks(7)
})
</script>
