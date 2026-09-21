import logging
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.config import AppConfig
from core.stats_engine import StatsEngine
from notifiers import TelegramNotifier, DiscordNotifier, GenericWebhookNotifier

logger = logging.getLogger("emby-ranks.scheduler")


import re

def normalize_standard_cron(expr: str) -> str:
    """
    将通用的 Linux / Unix 标准 Cron 表达式转换为 APScheduler 兼容格式。
    在 Linux 标准 Cron 中：0 和 7 均代表周日(Sunday)，1-6 分别代表周一至周六。
    APScheduler 默认 0 为周一，直接传入数字易产生歧义。
    本函数将星期字段规范化为英文单词缩写 (sun, mon, tue, wed, thu, fri, sat)。
    """
    if not expr:
        return expr
    
    parts = expr.strip().split()
    if len(parts) != 5:
        return expr
    
    minute, hour, day, month, dow = parts
    
    day_map = {
        '0': 'sun',
        '1': 'mon',
        '2': 'tue',
        '3': 'wed',
        '4': 'thu',
        '5': 'fri',
        '6': 'sat',
        '7': 'sun'
    }
    
    # 替换独立数字 0-7 为对应英文星期简写
    converted_dow = re.sub(r'\b[0-7]\b', lambda m: day_map.get(m.group(0), m.group(0)), dow.lower())
    
    return f"{minute} {hour} {day} {month} {converted_dow}"


class RankScheduler:
    def __init__(self, config: AppConfig, stats_engine: StatsEngine):
        self.config = config
        self.stats = stats_engine
        self.tz = pytz.timezone(config.timezone)
        self.scheduler = AsyncIOScheduler(timezone=self.tz)
        self.notifiers = []
        self._init_notifiers()

    def _init_notifiers(self):
        # 1. Telegram
        tg_cfg = self.config.notifiers.telegram
        if tg_cfg.enabled and tg_cfg.bot_token and tg_cfg.chat_id:
            self.notifiers.append(
                TelegramNotifier(
                    bot_token=tg_cfg.bot_token,
                    chat_id=tg_cfg.chat_id,
                    pin_message=tg_cfg.pin_message,
                    proxy=tg_cfg.proxy,
                    admin_only=tg_cfg.admin_only,
                    cooldown_seconds=tg_cfg.cooldown_seconds,
                    whitelist_user_ids=tg_cfg.whitelist_user_ids
                )
            )
            logger.info("已启用 Telegram 通知渠道")

        # 2. Discord
        dc_cfg = self.config.notifiers.discord
        if dc_cfg.enabled and dc_cfg.webhook_url:
            self.notifiers.append(DiscordNotifier(webhook_url=dc_cfg.webhook_url))
            logger.info("已启用 Discord 通知渠道")

        # 3. Webhook
        wh_cfg = self.config.notifiers.webhook
        if wh_cfg.enabled and wh_cfg.url:
            self.notifiers.append(GenericWebhookNotifier(url=wh_cfg.url, headers=wh_cfg.headers))
            logger.info("已启用 Webhook 通知渠道")

    async def broadcast(self, title: str, text: str, image_bytes=None, pin: bool = False, task_id: str = "general", reply_markup=None):
        """广播通知至所有已启用的通知渠道"""
        if not self.notifiers:
            logger.warning("未配置任何启用的通知渠道，输出至日志:")
            logger.info(f"\n{text}")
            return

        for notifier in self.notifiers:
            try:
                await notifier.send_report(
                    title=title,
                    text=text,
                    image_bytes=image_bytes,
                    pin=pin,
                    task_id=task_id,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"通知渠道推送异常: {e}")

    async def run_day_rank(self):
        """执行媒体播放日榜任务"""
        logger.info("【定时任务】开始执行【媒体播放日榜】")
        pin = self.config.schedules.day_rank.pin_message
        img, text = await self.stats.generate_media_rank(days=1, is_weekly=False)
        await self.broadcast(
            title=f"{self.config.emby.server_name} 播放日榜",
            text=text,
            image_bytes=img,
            pin=pin,
            task_id="day_rank"
        )
        logger.info("【定时任务】媒体播放日榜执行完毕")

    async def run_week_rank(self):
        """执行媒体播放周榜任务"""
        logger.info("【定时任务】开始执行【媒体播放周榜】")
        pin = self.config.schedules.week_rank.pin_message
        img, text = await self.stats.generate_media_rank(days=7, is_weekly=True)
        await self.broadcast(
            title=f"{self.config.emby.server_name} 播放周榜",
            text=text,
            image_bytes=img,
            pin=pin,
            task_id="week_rank"
        )
        logger.info("【定时任务】媒体播放周榜执行完毕")

    async def run_day_play_rank(self):
        """执行用户时长日榜任务"""
        logger.info("【定时任务】开始执行【用户观看时长日榜】")
        pin = self.config.schedules.day_play_rank.pin_message
        from notifiers.telegram import make_pagination_keyboard
        text, total_pages, cur_page = await self.stats.generate_user_play_rank(days=1, is_weekly=False, page=1)
        reply_markup = make_pagination_keyboard(days=1, current_page=cur_page, total_pages=total_pages)
        user_img = await self.stats.get_user_rank_image_bytes()
        await self.broadcast(
            title=f"{self.config.emby.server_name} 用户时长日榜",
            text=text,
            image_bytes=user_img,
            pin=pin,
            task_id="day_play_rank",
            reply_markup=reply_markup
        )
        logger.info("【定时任务】用户观看时长日榜执行完毕")

    async def run_week_play_rank(self):
        """执行用户时长周榜任务"""
        logger.info("【定时任务】开始执行【用户观看时长周榜】")
        pin = self.config.schedules.week_play_rank.pin_message
        from notifiers.telegram import make_pagination_keyboard
        text, total_pages, cur_page = await self.stats.generate_user_play_rank(days=7, is_weekly=True, page=1)
        reply_markup = make_pagination_keyboard(days=7, current_page=cur_page, total_pages=total_pages)
        user_img = await self.stats.get_user_rank_image_bytes()
        await self.broadcast(
            title=f"{self.config.emby.server_name} 用户时长周榜",
            text=text,
            image_bytes=user_img,
            pin=pin,
            task_id="week_play_rank",
            reply_markup=reply_markup
        )
        logger.info("【定时任务】用户观看时长周榜执行完毕")

    def register_jobs(self):
        """注册配置中的定时任务 (自动适配 Linux 标准 Cron 规范)"""
        sched_map = {
            "day_rank": (self.config.schedules.day_rank, self.run_day_rank),
            "week_rank": (self.config.schedules.week_rank, self.run_week_rank),
            "day_play_rank": (self.config.schedules.day_play_rank, self.run_day_play_rank),
            "week_play_rank": (self.config.schedules.week_play_rank, self.run_week_play_rank),
        }

        for task_name, (sched_item, func) in sched_map.items():
            if sched_item.enabled and sched_item.cron:
                try:
                    normalized_cron = normalize_standard_cron(sched_item.cron)
                    trigger = CronTrigger.from_crontab(normalized_cron, timezone=self.tz)
                    job = self.scheduler.add_job(
                        func,
                        trigger=trigger,
                        id=task_name,
                        name=task_name,
                        replace_existing=True
                    )
                    next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if job.next_run_time else "未知"
                    logger.info(f"已注册定时任务 [{task_name}]: cron='{sched_item.cron}' (规范化: '{normalized_cron}'), 下次执行: {next_run}")
                except Exception as e:
                    logger.error(f"注册任务 [{task_name}] 失败，cron 格式错误 '{sched_item.cron}': {e}")

    def _start_telegram_polling(self):
        for notifier in self.notifiers:
            if isinstance(notifier, TelegramNotifier):
                notifier.start_polling(self.stats)

    def _stop_telegram_polling(self):
        for notifier in self.notifiers:
            if isinstance(notifier, TelegramNotifier):
                notifier.stop_polling()

    def start(self):
        self.register_jobs()
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler 调度器已启动")

        # 启动 Telegram 轮询监听
        self._start_telegram_polling()

    def reload_config(self, new_config: AppConfig, new_stats_engine: StatsEngine):
        """动态热重载配置、通知渠道与定时任务"""
        logger.info("正在热重载调度器配置...")
        # 1. 停止旧的 Telegram 监听
        self._stop_telegram_polling()

        self.config = new_config
        self.stats = new_stats_engine
        self.tz = pytz.timezone(new_config.timezone)
        
        # 2. 重新初始化通知渠道
        self.notifiers.clear()
        self._init_notifiers()

        # 3. 启动新的 Telegram 监听
        self._start_telegram_polling()
        
        # 4. 清除旧任务并重新注册
        self.scheduler.remove_all_jobs()
        self.register_jobs()
        logger.info("调度器热重载完成！")


