import logging
import httpx
from typing import Optional
from notifiers.base import BaseNotifier

logger = logging.getLogger("emby-ranks.discord")


class DiscordNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_report(self, title: str, text: str, 
                          image_bytes: Optional[bytes] = None, 
                          pin: bool = False,
                          task_id: str = "general",
                          reply_markup: Optional[dict] = None) -> bool:
        if not self.webhook_url:
            return False

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if image_bytes:
                    files = {"file": ("rank.jpg", image_bytes, "image/jpeg")}
                    data = {"content": text[:2000]}
                    resp = await client.post(self.webhook_url, data=data, files=files)
                else:
                    resp = await client.post(self.webhook_url, json={"content": text[:2000]})
                
                resp.raise_for_status()
                logger.info(f"Discord 推送成功: {task_id}")
                return True
            except Exception as e:
                logger.error(f"Discord 推送失败: {e}")
                return False
