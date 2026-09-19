import logging
import httpx
from typing import Optional, Dict
from notifiers.base import BaseNotifier

logger = logging.getLogger("emby-ranks.webhook")


class GenericWebhookNotifier(BaseNotifier):
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}

    async def send_report(self, title: str, text: str, 
                          image_bytes: Optional[bytes] = None, 
                          pin: bool = False,
                          task_id: str = "general",
                          reply_markup: Optional[dict] = None) -> bool:
        if not self.url:
            return False

        payload = {
            "title": title,
            "text": text,
            "task_id": task_id,
            "has_image": image_bytes is not None
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(self.url, json=payload, headers=self.headers)
                resp.raise_for_status()
                logger.info(f"Webhook 推送成功: {task_id}")
                return True
            except Exception as e:
                logger.error(f"Webhook 推送失败: {e}")
                return False
