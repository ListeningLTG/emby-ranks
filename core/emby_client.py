import logging
import httpx
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger("emby-ranks.emby")


class EmbyClient:
    def __init__(self, base_url: str, api_key: str, timezone: str = "Asia/Shanghai"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.tz = pytz.timezone(timezone)
        self.headers = {
            "X-Emby-Token": self.api_key,
            "Accept": "application/json"
        }

    async def _request(self, method: str, path: str, **kwargs) -> Optional[Any]:
        if not self.base_url or not self.api_key:
            return None
        url = f"{self.base_url}{path}"
        params = kwargs.pop("params", {})
        if "api_key" not in params and "X-Emby-Token" not in self.headers:
            params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.request(method, url, headers=self.headers, params=params, **kwargs)
                resp.raise_for_status()
                if "image/" in resp.headers.get("Content-Type", ""):
                    return resp.content
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.debug(f"Emby 资源未找到 [404] {url}")
                else:
                    logger.error(f"Emby HTTP 错误 [{e.response.status_code}] 请求 {url}: {e.response.text}")
            except Exception as e:
                logger.error(f"Emby 请求异常 {url}: {str(e)}")
            return None

    async def get_users_map(self) -> Dict[str, str]:
        """获取 UserId -> UserName 映射字典"""
        data = await self._request("GET", "/emby/Users")
        if not data or not isinstance(data, list):
            return {}
        return {user["Id"]: user.get("Name", "未知用户") for user in data}

    async def get_media_report(self, media_type: str = "Movie", days: int = 1, limit: int = 10) -> List[List[Any]]:
        """
        获取媒体播放排行榜（基于 Playback Reporting 插件）
        返回列表元素: [user_id, item_id, item_type, name, play_count, total_duration]
        """
        now = datetime.now(self.tz)
        start_time = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")

        name_clause = "substr(ItemName, 0, instr(ItemName, ' - ')) AS name" if media_type == "Episode" else "ItemName AS name"

        sql = (
            f"SELECT UserId, ItemId, ItemType, {name_clause}, "
            f"COUNT(1) AS play_count, "
            f"SUM(PlayDuration - PauseDuration) AS total_duarion "
            f"FROM PlaybackActivity "
            f"WHERE ItemType = '{media_type}' "
            f"AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}' "
            f"AND UserId NOT IN (SELECT UserId FROM UserList) "
            f"GROUP BY name "
            f"ORDER BY total_duarion DESC "
            f"LIMIT {int(limit)}"
        )

        payload = {
            "CustomQueryString": sql,
            "ReplaceUserId": False
        }

        data = await self._request("POST", "/emby/user_usage_stats/submit_custom_query", json=payload)
        if data and isinstance(data, dict):
            return data.get("results", [])
        return []

    async def get_user_play_report(self, days: int = 7) -> List[List[Any]]:
        """
        获取用户观看时长排行榜（基于 Playback Reporting 插件）
        返回列表元素: [user_id, watch_time_in_seconds]
        """
        now = datetime.now(self.tz)
        start_time = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")

        sql = (
            f"SELECT UserId, SUM(PlayDuration - PauseDuration) AS WatchTime "
            f"FROM PlaybackActivity "
            f"WHERE DateCreated >= '{start_time}' AND DateCreated < '{end_time}' "
            f"GROUP BY UserId "
            f"ORDER BY WatchTime DESC"
        )

        payload = {
            "CustomQueryString": sql,
            "ReplaceUserId": True
        }

        data = await self._request("POST", "/emby/user_usage_stats/submit_custom_query", json=payload)
        if data and isinstance(data, dict):
            return data.get("results", [])
        return []

    async def get_item_image(self, item_id: str, image_type: str = "Primary") -> Optional[bytes]:
        """获取项目的海报或横幅背景图二进制数据"""
        path = f"/emby/Items/{item_id}/Images/{image_type}"
        data = await self._request("GET", path)
        if isinstance(data, bytes):
            return data
        return None

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """获取当前活跃的 Emby 会话"""
        data = await self._request("GET", "/emby/Sessions")
        if data and isinstance(data, list):
            return data
        return []
