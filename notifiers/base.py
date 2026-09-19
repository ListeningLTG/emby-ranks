from abc import ABC, abstractmethod
from typing import Optional


class BaseNotifier(ABC):
    @abstractmethod
    async def send_report(self, title: str, text: str, 
                          image_bytes: Optional[bytes] = None, 
                          pin: bool = False,
                          task_id: str = "general",
                          reply_markup: Optional[dict] = None) -> bool:
        """发送榜单通知"""
        pass
