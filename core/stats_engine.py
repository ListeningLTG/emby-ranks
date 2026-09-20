import logging
import math
from datetime import datetime
import pytz
from typing import Tuple, List, Optional, Any
from core.emby_client import EmbyClient
from core.drawer import RanksDrawer

try:
    import cn2an
    def to_chinese_num(num: int) -> str:
        return cn2an.an2cn(num)
except ImportError:
    CHINESE_NUMS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    def to_chinese_num(num: int) -> str:
        if 0 <= num < len(CHINESE_NUMS):
            return CHINESE_NUMS[num]
        return str(num)

logger = logging.getLogger("emby-ranks.stats")


def format_seconds(seconds: int) -> str:
    """格式化秒数为中文时分秒"""
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"


class StatsEngine:
    def __init__(self, emby_client: EmbyClient, assets_dir: str = "./assets", 
                 server_name: str = "EMBY SERVER", timezone: str = "Asia/Shanghai",
                 use_backdrop: bool = False, top_limit: int = 10,
                 user_rank_image: str = ""):
        self.emby = emby_client
        self.assets_dir = assets_dir
        self.server_name = server_name
        self.tz = pytz.timezone(timezone)
        self.use_backdrop = use_backdrop
        self.top_limit = top_limit
        self.user_rank_image = user_rank_image

    async def get_user_rank_image_bytes(self) -> Optional[bytes]:
        """获取配置的用户观影时长榜封面图数据 (支持本地文件和 HTTP/HTTPS URL)"""
        if not self.user_rank_image or not self.user_rank_image.strip():
            return None

        img_path_or_url = self.user_rank_image.strip()
        
        # 1. 网络超链接
        if img_path_or_url.startswith(("http://", "https://")):
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(img_path_or_url)
                    if resp.status_code == 200:
                        return resp.content
            except Exception as e:
                logger.error(f"从网络加载用户榜封面图失败 [{img_path_or_url}]: {e}")
                return None

        # 2. 本地文件
        try:
            from pathlib import Path
            path = Path(img_path_or_url)
            if not path.is_absolute() and not path.exists():
                candidate = Path(self.assets_dir) / img_path_or_url
                if candidate.exists():
                    path = candidate
            if path.exists() and path.is_file():
                with open(path, "rb") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"从本地加载用户榜封面图失败 [{img_path_or_url}]: {e}")
            return None

        return None

    async def generate_media_rank(self, days: int = 1, is_weekly: bool = False) -> Tuple[Optional[bytes], str]:
        """
        生成媒体播放日榜 / 周榜
        返回: (海报字节数据, Markdown 榜单文本)
        """
        title_prefix = "播放周榜" if is_weekly else "播放日榜"
        tag = "#WeekRanks" if is_weekly else "#DayRanks"
        today_str = datetime.now(self.tz).strftime("%Y-%m-%d")

        logger.info(f"正在获取媒体{title_prefix}数据 (天数: {days})...")
        movies = await self.emby.get_media_report(media_type="Movie", days=days, limit=self.top_limit)
        tvshows = await self.emby.get_media_report(media_type="Episode", days=days, limit=self.top_limit)

        # 绘制海报
        drawer = RanksDrawer(
            assets_dir=self.assets_dir,
            server_name=self.server_name,
            weekly=is_weekly,
            backdrop=self.use_backdrop
        )
        await drawer.draw(self.emby, movies, tvshows)
        poster_bytes = drawer.save_bytes()

        # 生成文本内容
        body = ""
        if movies:
            body += "**▎🎬 电影:**\n\n"
            for idx, item in enumerate(movies[:self.top_limit], 1):
                user_id, item_id, item_type, name, count, duration = tuple(item)
                duration_str = format_seconds(int(duration) if duration else 0)
                body += f"{idx}. **{name}**\n   播放: `{count}` 次 | 时长: `{duration_str}`\n"

        if tvshows:
            body += "\n**▎📺 电视剧:**\n\n"
            for idx, item in enumerate(tvshows[:self.top_limit], 1):
                user_id, item_id, item_type, name, count, duration = tuple(item)
                duration_str = format_seconds(int(duration) if duration else 0)
                body += f"{idx}. **{name}**\n   播放: `{count}` 次 | 时长: `{duration_str}`\n"

        if not movies and not tvshows:
            body = "暂无播放记录。\n"

        full_text = f"**【{self.server_name} {title_prefix}】**\n\n{body}\n{tag}  `{today_str}`"
        return poster_bytes, full_text

    async def generate_user_play_rank(self, days: int = 7, is_weekly: Optional[bool] = None, page: int = 1, page_size: int = 10) -> Tuple[str, int, int]:
        """
        生成用户观看时长日榜 / 周榜 / 月榜 (支持分页)
        返回: (Markdown 榜单文本, 总页数, 当前页码)
        """
        if days == 30:
            title = "每月观影时长榜"
        elif days == 7 or (is_weekly is True and days not in (1, 30)):
            title = "每周观影时长榜"
        elif days == 1:
            title = "每日观影时长榜"
        else:
            title = f"{days} 天观影时长榜"
        tag = "#UPlaysRank"
        today_str = datetime.now(self.tz).strftime("%Y-%m-%d")

        logger.info(f"正在获取用户{title}数据 (天数: {days}, 页码: {page})...")
        records = await self.emby.get_user_play_report(days=days)
        users_map = await self.emby.get_users_map()

        total_users = len(records)
        total_pages = max(1, math.ceil(total_users / page_size))
        page = max(1, min(page, total_pages))

        medals = ["🥇", "🥈", "🥉", "🏅"]
        
        # 页面标题（简洁展示，不带页码）
        text = f"**▎🏆 {self.server_name} {title}**\n\n"

        if not records:
            text += "过去这段时间大家都很安静，暂无用户观影记录~"
        else:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_records = records[start_idx:end_idx]

            for idx, item in enumerate(page_records, start=start_idx + 1):
                user_id, watch_time = item[0], item[1]
                # 优先匹配 users_map，未匹配则直接使用 Emby 原生返回的用户名，不添加任何 '用户_' 前缀
                user_name = users_map.get(user_id, str(user_id) if user_id else "未知用户")
                medal = medals[idx - 1] if idx <= 3 else medals[3]
                time_str = format_seconds(int(watch_time) if watch_time else 0)

                rank_cn = to_chinese_num(idx)
                text += f"{medal} **第{rank_cn}名** | `{user_name}`\n   观影时长: `{time_str}`\n"

        text += f"\n{tag}  `{today_str}`"
        return text, total_pages, page

    async def generate_watching_status(self) -> str:
        """生成当前实时播放状态报告"""
        sessions = await self.emby.get_sessions()
        online_users = set()
        playing_items = []

        for s in sessions:
            uid = s.get("UserId")
            if uid:
                online_users.add(uid)
            if s.get("NowPlayingItem"):
                playing_items.append(s)

        text = f"📊 **{self.server_name} 实时状态**\n\n"
        text += f"🟢 **在线用户:** `{len(online_users)}` 人\n"
        text += f"🎬 **正在播放:** `{len(playing_items)}` 个会话\n\n"

        if not playing_items:
            text += "当前没有用户在观看媒体。"
            return text

        text += "📝 **当前播放列表:**\n"
        for idx, s in enumerate(playing_items, 1):
            item = s.get("NowPlayingItem", {})
            name = item.get("Name", "未知")
            media_type = item.get("Type", "Unknown")
            is_paused = s.get("PlayState", {}).get("IsPaused", False)
            state_str = "⏸️ 暂停" if is_paused else "▶️ 播放中"

            if media_type == "Episode":
                series = item.get("SeriesName", "")
                name = f"{series} - {name}" if series else name

            text += f"{idx}. `{name}` ({state_str})\n"

        return text
