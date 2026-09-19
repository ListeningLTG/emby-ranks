<template>
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
    <!-- 左侧海报与封面控制台 -->
    <div class="lg:col-span-5 panel-card p-6 space-y-6">
      <div>
        <h2 class="text-lg font-bold text-white flex items-center gap-2">
          <span>🎨 海报与封面工坊</span>
        </h2>
        <p class="text-xs text-slate-400 mt-1">在线合成榜单海报，并可自定义消息推送的图片版式与封面</p>
      </div>

      <!-- 顶层工坊模块切换 -->
      <div class="grid grid-cols-2 gap-2 p-1 bg-dark-950 rounded-xl border border-slate-800 text-xs">
        <button @click="activeSection = 'media'" 
                :class="activeSection === 'media' ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                class="py-2.5 rounded-lg transition flex items-center justify-center gap-1.5">
          <span>🎬</span>
          <span>媒体播放榜海报</span>
        </button>
        <button @click="activeSection = 'user_cover'" 
                :class="activeSection === 'user_cover' ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                class="py-2.5 rounded-lg transition flex items-center justify-center gap-1.5">
          <span>🏆</span>
          <span>用户时长榜封面</span>
        </button>
      </div>

      <!-- 板块 1: 媒体播放榜海报设置 -->
      <div v-if="activeSection === 'media'" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-2">预览榜单类型</label>
          <div class="grid grid-cols-2 gap-2 p-1 bg-dark-950 rounded-xl border border-slate-800 text-xs">
            <button @click="posterType = 'day_rank'; updatePreview()" 
                    :class="posterType === 'day_rank' ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="py-2 rounded-lg transition">播放日榜海报</button>
            <button @click="posterType = 'week_rank'; updatePreview()" 
                    :class="posterType === 'week_rank' ? 'bg-indigo-600 text-white font-semibold shadow' : 'text-slate-400 hover:text-white'"
                    class="py-2 rounded-lg transition">播放周榜海报</button>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-dark-900/80 border border-slate-800 space-y-3">
          <label class="flex items-center justify-between text-xs text-slate-300 cursor-pointer">
            <span class="font-medium">使用横版剧照 (Backdrop)</span>
            <input type="checkbox" v-model="useBackdrop" @change="handleBackdropChange" :disabled="saving" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
          </label>
          <p class="text-[11px] text-slate-500">开启后优先使用 16:9 横版剧照贴图，关闭则使用标准 2:3 竖版海报。</p>
          <div class="text-[11px] text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-2 flex items-center gap-1.5">
            <span>📢</span>
            <span>此设置会自动保存并直接应用到所有渠道的消息推送中。</span>
          </div>
        </div>

        <div class="pt-2">
          <button @click="updatePreview" :disabled="loading" class="btn btn-primary w-full py-2.5 text-xs">
            <span>{{ loading ? '⏳ 正在合成海报...' : '🔄 重新生成海报' }}</span>
          </button>
        </div>
      </div>

      <!-- 板块 2: 用户观影时长榜封面设置 -->
      <div v-else-if="activeSection === 'user_cover'" class="space-y-4">
        <div class="p-4 rounded-xl bg-dark-900/80 border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-white">封面图配置</span>
            <span v-if="userCoverImage" class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">已启用图文模式</span>
            <span v-else class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">纯文本模式</span>
          </div>
          <p class="text-[11px] text-slate-400 leading-relaxed">
            配置后，推送到 Telegram 等渠道的用户观影时长日榜/周榜将以此图片作为封面图发送，并保留底部的智能数字翻页按键。
          </p>
        </div>

        <!-- 方式 1: 上传本地图片 -->
        <div class="p-4 rounded-xl bg-dark-900/80 border border-slate-800 space-y-3">
          <label class="block text-xs font-semibold text-slate-300">📁 方式一：上传本地图片</label>
          <div class="flex items-center gap-2">
            <input type="file" ref="fileInput" accept="image/*" @change="handleFileUpload" class="hidden" id="user-cover-file" />
            <label for="user-cover-file" :class="uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'" class="btn btn-secondary text-xs flex-1 py-2">
              <span>{{ uploading ? '⏳ 上传中...' : '📤 选择并上传本地图片' }}</span>
            </label>
          </div>
          <p class="text-[10px] text-slate-500">支持 JPG、PNG、WEBP 格式，上传后自动保存为服务器封面。</p>
        </div>

        <!-- 方式 2: 网络图片超链接 -->
        <div class="p-4 rounded-xl bg-dark-900/80 border border-slate-800 space-y-3">
          <label class="block text-xs font-semibold text-slate-300">🌐 方式二：网络图片超链接 (URL)</label>
          <div class="space-y-2">
            <input type="text" v-model="imageUrlInput" placeholder="https://telegra.ph/file/xxx.png 或其他图片直链" class="input-field text-xs font-mono" />
            <button @click="handleSaveImageUrl" :disabled="saving || !imageUrlInput.trim()" class="btn btn-primary w-full py-2 text-xs">
              <span>{{ saving ? '保存中...' : '💾 保存并应用此图片链接' }}</span>
            </button>
          </div>
        </div>

        <!-- 当前路径与清空 -->
        <div v-if="userCoverImage" class="p-4 rounded-xl bg-dark-900/80 border border-slate-800 space-y-2.5">
          <div class="text-[11px] text-slate-400">
            <span>当前封面源：</span>
            <code class="text-indigo-300 font-mono break-all block mt-1 bg-dark-950 p-1.5 rounded border border-slate-800">{{ userCoverImage }}</code>
          </div>
          <button @click="handleClearUserCover" :disabled="saving" class="btn btn-secondary w-full py-1.5 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 border-rose-900/40">
            <span>🗑️ 清空封面（恢复纯文本推送）</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧画布与预览展示区域 -->
    <div class="lg:col-span-7 panel-card p-6 flex flex-col items-center justify-center min-h-[580px] bg-dark-950/60 relative overflow-hidden">
      <!-- 1. 媒体海报预览模式 -->
      <template v-if="activeSection === 'media'">
        <div v-if="loading" class="absolute inset-0 bg-dark-950/80 backdrop-blur-md flex flex-col items-center justify-center z-10 gap-3">
          <div class="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p class="text-xs text-slate-300 font-medium">正在拉取封面资源并合成高清海报...</p>
        </div>

        <img :src="previewUrl" 
             @load="loading = false" 
             @error="handleImgError"
             alt="榜单海报预览" 
             class="max-w-full max-h-[720px] object-contain rounded-xl shadow-2xl border border-slate-800/80 transition-all duration-300 hover:scale-[1.01]" />
      </template>

      <!-- 2. 用户时长榜封面与图文排版预览模式 -->
      <template v-else-if="activeSection === 'user_cover'">
        <div class="w-full max-w-md bg-dark-900/90 rounded-2xl border border-slate-800 shadow-2xl p-4 space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800/60 pb-3">
            <span class="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <span>📱</span> Telegram 消息推送效果模拟
            </span>
            <span class="text-[10px] text-slate-500 font-mono">实时渲染</span>
          </div>

          <!-- 封面图部分 -->
          <div v-if="userCoverImage" class="relative rounded-xl overflow-hidden border border-slate-800 bg-dark-950 aspect-video flex items-center justify-center group">
            <img :src="userCoverPreviewUrl" 
                 @error="handleUserCoverImgError"
                 alt="用户榜封面预览" 
                 class="w-full h-full object-cover transition duration-300 group-hover:scale-105" />
          </div>
          <div v-else class="p-6 rounded-xl border border-dashed border-slate-800 text-center bg-dark-950/40 space-y-2">
            <div class="text-2xl">📝</div>
            <div class="text-xs font-semibold text-slate-300">当前处于纯文本推送模式</div>
            <div class="text-[11px] text-slate-500">未设置封面图，推送时将直接发送榜单文字与翻页按键</div>
          </div>

          <!-- 消息正文模拟 -->
          <div class="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800/80 text-xs space-y-2 font-mono">
            <div class="text-white font-bold text-sm">▎🏆 {{ currentConfig?.emby?.server_name || 'EMBY' }} 1 天观影榜</div>
            <div class="text-slate-300 space-y-1.5 pt-1 text-[11px]">
              <div>🥇 <b>第一名</b> | <span class="text-indigo-400">听风者</span><br><span class="text-slate-500 pl-4">观影时长: 6小时30分</span></div>
              <div>🥈 <b>第二名</b> | <span class="text-indigo-400">极客影迷</span><br><span class="text-slate-500 pl-4">观影时长: 4小时15分</span></div>
              <div>🥉 <b>第三名</b> | <span class="text-indigo-400">星际漫游</span><br><span class="text-slate-500 pl-4">观影时长: 3小时20分</span></div>
            </div>
            <div class="text-[10px] text-slate-500 pt-2 border-t border-slate-800/60 flex items-center justify-between">
              <span>#UPlaysRank 2026-09-19</span>
              <span>21:00</span>
            </div>
          </div>

          <!-- 模拟智能数字翻页按键 -->
          <div class="space-y-1.5 pt-1">
            <div class="grid grid-cols-3 gap-1.5 text-center text-xs">
              <div class="py-1.5 rounded-lg bg-slate-800/90 text-white font-bold border border-slate-700">· 1 ·</div>
              <div class="py-1.5 rounded-lg bg-slate-800/40 text-slate-400 border border-slate-800/60">2</div>
              <div class="py-1.5 rounded-lg bg-slate-800/40 text-slate-400 border border-slate-800/60">3</div>
            </div>
            <div class="py-1.5 text-center text-xs rounded-lg bg-rose-950/20 text-rose-400 border border-rose-900/30">
              ❌ 关闭
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchConfig, saveConfig, uploadUserCover } from '../api'
import { showToast } from '../utils/toast'

const activeSection = ref('media')
const posterType = ref('day_rank')
const useBackdrop = ref(false)
const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const currentConfig = ref(null)
const userCoverImage = ref('')
const imageUrlInput = ref('')
const timestamp = ref(Date.now())
const fileInput = ref(null)

const previewUrl = computed(() => {
  return `/api/poster/preview?type=${posterType.value}&backdrop=${useBackdrop.value}&t=${timestamp.value}`
})

const userCoverPreviewUrl = computed(() => {
  if (!userCoverImage.value) return ''
  if (userCoverImage.value.startsWith('http://') || userCoverImage.value.startsWith('https://')) {
    return userCoverImage.value
  }
  return `/api/poster/user_cover?t=${timestamp.value}`
})

onMounted(async () => {
  await loadCurrentConfig()
})

async function loadCurrentConfig() {
  try {
    const config = await fetchConfig()
    if (config) {
      currentConfig.value = config
      if (config.poster) {
        if (typeof config.poster.use_backdrop === 'boolean') {
          useBackdrop.value = config.poster.use_backdrop
        }
        if (config.poster.user_rank_image) {
          userCoverImage.value = config.poster.user_rank_image
          if (config.poster.user_rank_image.startsWith('http')) {
            imageUrlInput.value = config.poster.user_rank_image
          }
        } else {
          userCoverImage.value = ''
        }
      }
    }
  } catch (e) {
    console.error('获取系统配置失败', e)
  }
}

async function handleBackdropChange() {
  updatePreview()
  if (!currentConfig.value) {
    await loadCurrentConfig()
  }
  
  if (currentConfig.value) {
    saving.value = true
    try {
      if (!currentConfig.value.poster) {
        currentConfig.value.poster = {}
      }
      currentConfig.value.poster.use_backdrop = useBackdrop.value
      await saveConfig(currentConfig.value)
      showToast(useBackdrop.value ? '已切换为 16:9 横版剧照并同步至推送！' : '已切换为 2:3 竖版海报并同步至推送！', 'success')
    } catch (e) {
      showToast('保存海报配置失败: ' + e.message, 'error')
    } finally {
      saving.value = false
    }
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  uploading.value = true
  try {
    const res = await uploadUserCover(file)
    if (res.success) {
      userCoverImage.value = res.image_path
      imageUrlInput.value = ''
      timestamp.value = Date.now()
      await loadCurrentConfig()
      showToast(res.message || '封面图已上传并同步应用至推送！', 'success')
    } else {
      showToast('上传失败: ' + res.message, 'error')
    }
  } catch (e) {
    showToast('上传异常: ' + e.message, 'error')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function handleSaveImageUrl() {
  const url = imageUrlInput.value.trim()
  if (!url) return

  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    showToast('请输入以 http:// 或 https:// 开头的有效图片链接', 'warning')
    return
  }

  if (!currentConfig.value) {
    await loadCurrentConfig()
  }

  saving.value = true
  try {
    if (!currentConfig.value.poster) currentConfig.value.poster = {}
    currentConfig.value.poster.user_rank_image = url
    await saveConfig(currentConfig.value)
    userCoverImage.value = url
    timestamp.value = Date.now()
    showToast('封面图超链接已保存并同步应用至推送！', 'success')
  } catch (e) {
    showToast('保存图片链接失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

async function handleClearUserCover() {
  if (!currentConfig.value) {
    await loadCurrentConfig()
  }

  saving.value = true
  try {
    if (!currentConfig.value.poster) currentConfig.value.poster = {}
    currentConfig.value.poster.user_rank_image = ''
    await saveConfig(currentConfig.value)
    userCoverImage.value = ''
    imageUrlInput.value = ''
    timestamp.value = Date.now()
    showToast('已清空封面图，恢复为纯文本推送模式！', 'success')
  } catch (e) {
    showToast('清空封面图失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

function updatePreview() {
  loading.value = true
  timestamp.value = Date.now()
}

function handleImgError() {
  loading.value = false
  showToast('海报渲染失败，请检查 Emby 连接状态！', 'error')
}

function handleUserCoverImgError() {
  showToast('封面图加载失败，请检查图片链接或上传文件！', 'warning')
}
</script>
