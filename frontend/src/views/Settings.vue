<template>
  <div class="space-y-6 max-w-5xl mx-auto pb-16">
    <!-- 顶部操作栏 -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-white tracking-tight">⚙️ 系统配置中心</h2>
        <p class="text-xs text-slate-400 mt-1">管理 Emby 凭据、定时推送计划与多渠道通知设置</p>
      </div>
      <button @click="handleSave" :disabled="saving" class="btn btn-primary px-5 py-2.5 text-xs">
        <span>{{ saving ? '💾 保存中...' : '💾 保存并热重载生效' }}</span>
      </button>
    </div>

    <!-- 1. Emby 服务器设置 -->
    <div class="panel-card p-6 space-y-5">
      <div class="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div>
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>🍿 Emby 服务器设置</span>
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">配置 Emby 的访问地址与 API 密钥</p>
        </div>
        <button @click="handleTestEmby" :disabled="testingEmby" class="btn btn-secondary text-xs">
          <span>{{ testingEmby ? '检测中...' : '🔌 测试 Emby 连接' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Emby 服务器地址</label>
          <input type="text" v-model="form.emby.url" placeholder="http://192.168.1.100:8096" class="input-field">
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Emby API 密钥 (Token)</label>
          <input type="password" v-model="form.emby.api_key" placeholder="在 Emby 后台「API 密钥」中生成" class="input-field">
        </div>
        <div class="md:col-span-2">
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">服务器名称 / Logo</label>
          <input type="text" v-model="form.emby.server_name" placeholder="我的emby" class="input-field">
        </div>
      </div>
    </div>

    <!-- 2. 定时调度设置 -->
    <div class="panel-card p-6 space-y-5">
      <div class="border-b border-slate-800/80 pb-4">
        <h3 class="text-base font-bold text-white flex items-center gap-2">
          <span>⏱️ 定时推送调度 (APScheduler)</span>
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">支持通用 Linux 标准 5 段式 Cron 表达式 (分 时 日 月 周，0/7 为周日，1 为周一，亦支持 sun/mon/mon-fri 等)，可点击预设按钮快速填入</p>
      </div>

      <div class="space-y-4">
        <!-- 播放日榜 -->
        <div class="p-4 bg-dark-900/80 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" v-model="form.schedules.day_rank.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <div>
              <span class="text-sm font-bold text-white">🎬 媒体播放日榜</span>
              <p class="text-xs text-slate-400">每日统计电影与电视剧播放 Top 10 并生成海报</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button @click="form.schedules.day_rank.cron = '30 18 * * *'" type="button" class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">预设: 每天 18:30</button>
            <label class="text-xs text-slate-300 flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" v-model="form.schedules.day_rank.pin_message" class="rounded text-indigo-600 focus:ring-0">
              <span>自动置顶</span>
            </label>
            <input type="text" v-model="form.schedules.day_rank.cron" class="input-field w-32 text-center text-xs font-mono" placeholder="30 18 * * *">
          </div>
        </div>

        <!-- 播放周榜 -->
        <div class="p-4 bg-dark-900/80 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" v-model="form.schedules.week_rank.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <div>
              <span class="text-sm font-bold text-white">🏆 媒体播放周榜</span>
              <p class="text-xs text-slate-400">每周统计全服热播排行并生成专属周榜海报</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button @click="form.schedules.week_rank.cron = '59 23 * * 0'" type="button" class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">预设: 周日 23:59</button>
            <label class="text-xs text-slate-300 flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" v-model="form.schedules.week_rank.pin_message" class="rounded text-indigo-600 focus:ring-0">
              <span>自动置顶</span>
            </label>
            <input type="text" v-model="form.schedules.week_rank.cron" class="input-field w-32 text-center text-xs font-mono" placeholder="59 23 * * 0">
          </div>
        </div>

        <!-- 用户时长日榜 -->
        <div class="p-4 bg-dark-900/80 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" v-model="form.schedules.day_play_rank.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <div>
              <span class="text-sm font-bold text-white">🥇 用户观影时长日榜</span>
              <p class="text-xs text-slate-400">每日统计用户在线看片时长前 10 名</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button @click="form.schedules.day_play_rank.cron = '00 23 * * *'" type="button" class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">预设: 每天 23:00</button>
            <input type="text" v-model="form.schedules.day_play_rank.cron" class="input-field w-32 text-center text-xs font-mono" placeholder="00 23 * * *">
          </div>
        </div>

        <!-- 用户时长周榜 -->
        <div class="p-4 bg-dark-900/80 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <input type="checkbox" v-model="form.schedules.week_play_rank.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <div>
              <span class="text-sm font-bold text-white">🏅 用户观影时长周榜</span>
              <p class="text-xs text-slate-400">每周统计全服用户累计观影时长金银铜排行榜</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button @click="form.schedules.week_play_rank.cron = '00 23 * * 0'" type="button" class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700">预设: 周日 23:00</button>
            <input type="text" v-model="form.schedules.week_play_rank.cron" class="input-field w-32 text-center text-xs font-mono" placeholder="00 23 * * 0">
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 通知渠道设置 -->
    <div class="panel-card p-6 space-y-6">
      <div class="border-b border-slate-800/80 pb-4">
        <h3 class="text-base font-bold text-white flex items-center gap-2">
          <span>📢 通知推送渠道</span>
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">配置接收排行榜海报与消息的机器人或 Webhook</p>
      </div>

      <!-- Telegram -->
      <div class="p-5 bg-dark-900/80 rounded-xl border border-slate-800 space-y-4">
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2.5 cursor-pointer">
            <input type="checkbox" v-model="form.notifiers.telegram.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <span class="text-sm font-bold text-white">✈️ Telegram 机器人</span>
          </label>
          <button @click="handleTestTelegram" class="btn btn-secondary text-xs">📨 发送测试消息</button>
        </div>

        <div v-if="form.notifiers.telegram.enabled" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Bot Token</label>
            <input type="text" v-model="form.notifiers.telegram.bot_token" placeholder="123456789:ABCdefGhI..." class="input-field font-mono">
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Chat ID (频道或群组)</label>
            <input type="text" v-model="form.notifiers.telegram.chat_id" placeholder="-100123456789" class="input-field font-mono">
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">HTTP / SOCKS5 代理 (可选)</label>
            <input type="text" v-model="form.notifiers.telegram.proxy" placeholder="http://127.0.0.1:7890" class="input-field">
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">群聊防刷冷却时间 (秒)</label>
            <input type="number" min="0" max="300" v-model.number="form.notifiers.telegram.cooldown_seconds" placeholder="15" class="input-field">
          </div>
          <div class="md:col-span-2">
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-semibold text-slate-300">私聊授权白名单 User ID (可选)</label>
              <span class="text-[11px] text-slate-400">多个 ID 用逗号分隔，留空表示允许所有人私聊</span>
            </div>
            <input type="text" v-model="form.notifiers.telegram.whitelist_user_ids" placeholder="如: 123456789, 987654321" class="input-field font-mono">
          </div>
          <div class="md:col-span-2 pt-1">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.notifiers.telegram.admin_only" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
              <span class="text-xs font-medium text-slate-300">仅允许群组管理员在群内触发命令 (非管理员无法在群内查榜)</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Discord -->
      <div class="p-5 bg-dark-900/80 rounded-xl border border-slate-800 space-y-4">
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2.5 cursor-pointer">
            <input type="checkbox" v-model="form.notifiers.discord.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <span class="text-sm font-bold text-white">🎮 Discord Webhook</span>
          </label>
          <button @click="handleTestDiscord" class="btn btn-secondary text-xs">📨 发送测试消息</button>
        </div>

        <div v-if="form.notifiers.discord.enabled" class="pt-2">
          <label class="block text-xs font-semibold text-slate-300 mb-1">Webhook URL</label>
          <input type="text" v-model="form.notifiers.discord.webhook_url" placeholder="https://discord.com/api/webhooks/..." class="input-field">
        </div>
      </div>

      <!-- Webhook -->
      <div class="p-5 bg-dark-900/80 rounded-xl border border-slate-800 space-y-4">
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2.5 cursor-pointer">
            <input type="checkbox" v-model="form.notifiers.webhook.enabled" class="w-4 h-4 rounded text-indigo-600 focus:ring-0">
            <span class="text-sm font-bold text-white">🌐 通用 Webhook (企业微信/Bark/PushPlus)</span>
          </label>
          <button @click="handleTestWebhook" class="btn btn-secondary text-xs">📨 发送测试消息</button>
        </div>

        <div v-if="form.notifiers.webhook.enabled" class="pt-2">
          <label class="block text-xs font-semibold text-slate-300 mb-1">URL 地址</label>
          <input type="text" v-model="form.notifiers.webhook.url" placeholder="https://api.example.com/notify" class="input-field">
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchConfig, saveConfig, testEmby, testTelegram, testDiscord, testWebhook } from '../api'
import { showToast } from '../utils/toast'

const form = ref({
  timezone: 'Asia/Shanghai',
  emby: { url: '', api_key: '', server_name: '' },
  poster: { use_backdrop: false, top_limit: 10, assets_dir: './assets' },
  schedules: {
    day_rank: { enabled: false, cron: '30 18 * * *', pin_message: true },
    week_rank: { enabled: false, cron: '59 23 * * 0', pin_message: true },
    day_play_rank: { enabled: false, cron: '00 23 * * *', pin_message: false },
    week_play_rank: { enabled: false, cron: '00 23 * * 0', pin_message: false }
  },
  notifiers: {
    telegram: { enabled: false, bot_token: '', chat_id: '', pin_message: true, proxy: '', admin_only: false, cooldown_seconds: 15, whitelist_user_ids: '' },
    discord: { enabled: false, webhook_url: '' },
    webhook: { enabled: false, url: '', headers: {} }
  }
})

const saving = ref(false)
const testingEmby = ref(false)

async function loadSettings() {
  try {
    const data = await fetchConfig()
    if (data) form.value = data
  } catch (e) {
    console.error(e)
  }
}

async function handleSave() {
  saving.value = true
  try {
    const res = await saveConfig(form.value)
    showToast(res.message || '配置已成功保存并热重载！', 'success')
  } catch (e) {
    showToast('保存失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

async function handleTestEmby() {
  testingEmby.value = true
  try {
    const res = await testEmby({
      url: form.value.emby.url,
      api_key: form.value.emby.api_key
    })
    showToast(res.message, res.success ? 'success' : 'error')
  } catch (e) {
    showToast('测试异常: ' + e.message, 'error')
  } finally {
    testingEmby.value = false
  }
}

async function handleTestTelegram() {
  try {
    const res = await testTelegram(form.value.notifiers.telegram)
    showToast(res.message, res.success ? 'success' : 'error')
  } catch (e) {
    showToast('测试异常: ' + e.message, 'error')
  }
}

async function handleTestDiscord() {
  try {
    const res = await testDiscord(form.value.notifiers.discord)
    showToast(res.message, res.success ? 'success' : 'error')
  } catch (e) {
    showToast('测试异常: ' + e.message, 'error')
  }
}

async function handleTestWebhook() {
  try {
    const res = await testWebhook(form.value.notifiers.webhook)
    showToast(res.message, res.success ? 'success' : 'error')
  } catch (e) {
    showToast('测试异常: ' + e.message, 'error')
  }
}

onMounted(() => {
  loadSettings()
})
</script>
