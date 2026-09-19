import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
from core.emby_client import EmbyClient
from notifiers import TelegramNotifier, DiscordNotifier, GenericWebhookNotifier

logger = logging.getLogger("emby-ranks.api.test")
router = APIRouter(prefix="/api/test", tags=["连通性与推送测试"])


class EmbyTestRequest(BaseModel):
    url: Optional[str] = None
    api_key: Optional[str] = None


class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    proxy: Optional[str] = None


class DiscordTestRequest(BaseModel):
    webhook_url: Optional[str] = None


class WebhookTestRequest(BaseModel):
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@router.post("/emby")
async def test_emby(data: EmbyTestRequest, request: Request):
    """测试 Emby 服务器连接与 API Key 有效性"""
    config = request.app.state.config
    url = data.url or config.emby.url
    api_key = data.api_key or config.emby.api_key

    if not url or not api_key:
        raise HTTPException(status_code=400, detail="缺少 Emby 服务器地址或 API Key")

    client = EmbyClient(base_url=url, api_key=api_key)
    try:
        users = await client.get_users_map()
        if users is not None:
            return {
                "success": True,
                "message": f"连接成功！成功获取到 {len(users)} 位 Emby 用户。"
            }
        else:
            return {
                "success": False,
                "message": "连接失败，请检查 Emby 地址与 API Key 是否正确，以及 Playback Reporting 插件是否就绪。"
            }
    except Exception as e:
        return {"success": False, "message": f"请求异常: {str(e)}"}


@router.post("/telegram")
async def test_telegram(data: TelegramTestRequest, request: Request):
    """测试 Telegram 机器人消息推送"""
    config = request.app.state.config
    token = data.bot_token or config.notifiers.telegram.bot_token
    chat_id = data.chat_id or config.notifiers.telegram.chat_id
    proxy = data.proxy if data.proxy is not None else config.notifiers.telegram.proxy

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="缺少 Telegram Bot Token 或 Chat ID")

    notifier = TelegramNotifier(bot_token=token, chat_id=chat_id, pin_message=False, proxy=proxy)
    success = await notifier.send_report(
        title="测试通知",
        text="🎉 **【Emby-Ranks】测试通知**\n\n恭喜！你的 Telegram 通知渠道已成功配置并可以正常接收推送！",
        pin=False,
        task_id="test"
    )
    if success:
        return {"success": True, "message": "测试消息发送成功，请前往 Telegram 查看！"}
    else:
        return {"success": False, "message": "测试消息发送失败，请检查 Bot Token、Chat ID 以及网络/代理设置。"}


@router.post("/discord")
async def test_discord(data: DiscordTestRequest, request: Request):
    """测试 Discord Webhook 推送"""
    config = request.app.state.config
    url = data.webhook_url or config.notifiers.discord.webhook_url
    if not url:
        raise HTTPException(status_code=400, detail="缺少 Discord Webhook URL")

    notifier = DiscordNotifier(webhook_url=url)
    success = await notifier.send_report(
        title="测试通知",
        text="🎉 **【Emby-Ranks】测试通知**\n\n恭喜！你的 Discord Webhook 已成功配置！",
        task_id="test"
    )
    if success:
        return {"success": True, "message": "Discord 测试消息发送成功！"}
    else:
        return {"success": False, "message": "Discord 测试消息发送失败，请检查 Webhook URL。"}


@router.post("/webhook")
async def test_webhook(data: WebhookTestRequest, request: Request):
    """测试通用 Webhook 推送"""
    config = request.app.state.config
    url = data.url or config.notifiers.webhook.url
    headers = data.headers or config.notifiers.webhook.headers
    if not url:
        raise HTTPException(status_code=400, detail="缺少 Webhook URL")

    notifier = GenericWebhookNotifier(url=url, headers=headers)
    success = await notifier.send_report(
        title="测试通知",
        text="🎉 【Emby-Ranks】测试通知：通用 Webhook 已成功配置！",
        task_id="test"
    )
    if success:
        return {"success": True, "message": "Webhook 测试消息发送成功！"}
    else:
        return {"success": False, "message": "Webhook 测试消息发送失败，请检查 URL 与请求头。"}
