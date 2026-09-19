import os
import json
import asyncio
import logging
import httpx
from pathlib import Path
from typing import Optional, List, Dict, Any
from notifiers.base import BaseNotifier

logger = logging.getLogger("emby-ranks.telegram")

CAPTION_LIMIT = 1000
TEXT_LIMIT = 4000


def split_text(text: str, max_length: int = 4000) -> List[str]:
    """按段落或长度分割长文本"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    lines = text.split("\n")
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                parts.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                parts.append(line[:max_length])
                current_chunk = line[max_length:] + "\n"
        else:
            current_chunk += line + "\n"
            
    if current_chunk.strip():
        parts.append(current_chunk.strip())
    return parts


def make_pagination_keyboard(days: int, current_page: int, total_pages: int) -> Optional[dict]:
    """生成用户观影榜单智能数字直达与跨页内联键盘 (与 Sakura_embyboss 风格一致)"""
    if total_pages <= 1:
        return None
    
    row1 = []
    if total_pages <= 5:
        for p in range(1, total_pages + 1):
            if p == current_page:
                row1.append({"text": f"· {p} ·", "callback_data": "noop"})
            else:
                row1.append({"text": str(p), "callback_data": f"uplays:{days}:{p}"})
    else:
        if current_page <= 3:
            for p in range(1, 4):
                if p == current_page:
                    row1.append({"text": f"· {p} ·", "callback_data": "noop"})
                else:
                    row1.append({"text": str(p), "callback_data": f"uplays:{days}:{p}"})
            row1.append({"text": "4 ›", "callback_data": f"uplays:{days}:4"})
            row1.append({"text": f"{total_pages} »", "callback_data": f"uplays:{days}:{total_pages}"})
        elif current_page >= total_pages - 2:
            row1.append({"text": "« 1", "callback_data": f"uplays:{days}:1"})
            prev_p = total_pages - 3
            row1.append({"text": f"‹ {prev_p}", "callback_data": f"uplays:{days}:{prev_p}"})
            for p in range(total_pages - 2, total_pages + 1):
                if p == current_page:
                    row1.append({"text": f"· {p} ·", "callback_data": "noop"})
                else:
                    row1.append({"text": str(p), "callback_data": f"uplays:{days}:{p}"})
        else:
            row1.append({"text": "« 1", "callback_data": f"uplays:{days}:1"})
            row1.append({"text": f"‹ {current_page - 1}", "callback_data": f"uplays:{days}:{current_page - 1}"})
            row1.append({"text": f"· {current_page} ·", "callback_data": "noop"})
            row1.append({"text": f"{current_page + 1} ›", "callback_data": f"uplays:{days}:{current_page + 1}"})
            row1.append({"text": f"{total_pages} »", "callback_data": f"uplays:{days}:{total_pages}"})
            
    row2 = [{"text": "❌ 关闭", "callback_data": "closeit"}]
    if total_pages > 5:
        if current_page - 5 >= 1:
            row2.append({"text": "⏮️ 前进-5", "callback_data": f"uplays:{days}:{current_page - 5}"})
        if current_page + 5 <= total_pages:
            row2.append({"text": "⏭️ 后退+5", "callback_data": f"uplays:{days}:{current_page + 5}"})
            
    return {"inline_keyboard": [row1, row2]}


class TelegramNotifier(BaseNotifier):
    def __init__(self, bot_token: str, chat_id: str, 
                 pin_message: bool = True, proxy: str = "",
                 admin_only: bool = False, cooldown_seconds: int = 15,
                 whitelist_user_ids: str = "",
                 pin_cache_file: str = "data/tg_pins.json"):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.pin_message = pin_message
        self.proxy = proxy or None
        self.admin_only = admin_only
        self.cooldown_seconds = cooldown_seconds
        
        # 解析私聊白名单
        self.whitelist_user_ids: set = set()
        if whitelist_user_ids:
            for uid in str(whitelist_user_ids).replace("，", ",").split(","):
                uid = uid.strip()
                if uid.isdigit():
                    self.whitelist_user_ids.add(int(uid))

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.pin_cache_file = Path(pin_cache_file)
        self._polling_task = None
        self._user_cooldowns: Dict[int, float] = {}
        self.bot_username: Optional[str] = None

    def _is_user_allowed_in_private(self, user_id: int) -> bool:
        """检查用户是否有权限私聊使用机器人 (若未配置白名单则默认允许所有人)"""
        if not self.whitelist_user_ids:
            return True
        try:
            return int(user_id) in self.whitelist_user_ids
        except Exception:
            return False

    def start_polling(self, stats_engine):
        """启动后台长轮询任务"""
        if not self._polling_task or self._polling_task.done():
            self._polling_task = asyncio.create_task(self.handle_callback_polling(stats_engine))
            logger.info(f"已启动 Telegram 轮询监听任务 (白名单用户数: {len(self.whitelist_user_ids)})")

    def stop_polling(self):
        """停止后台长轮询任务"""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            self._polling_task = None
            logger.info("已停止旧的 Telegram 轮询监听任务")

    def _get_pinned_id(self, task_id: str) -> Optional[int]:
        if not self.pin_cache_file.exists():
            return None
        try:
            with open(self.pin_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(task_id)
        except Exception:
            return None

    def _save_pinned_id(self, task_id: str, message_id: int):
        self.pin_cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if self.pin_cache_file.exists():
            try:
                with open(self.pin_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[task_id] = message_id
        try:
            with open(self.pin_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"保存置顶消息ID失败: {e}")

    async def _unpin(self, client: httpx.AsyncClient, message_id: int):
        try:
            await client.post(
                f"{self.base_url}/unpinChatMessage",
                json={"chat_id": self.chat_id, "message_id": message_id}
            )
        except Exception as e:
            logger.warning(f"取消置顶消息失败 {message_id}: {e}")

    async def _pin(self, client: httpx.AsyncClient, message_id: int):
        try:
            await client.post(
                f"{self.base_url}/pinChatMessage",
                json={"chat_id": self.chat_id, "message_id": message_id, "disable_notification": True}
            )
        except Exception as e:
            logger.warning(f"置顶消息失败 {message_id}: {e}")

    async def send_message_to_chat(self, client: httpx.AsyncClient, chat_id: Any, 
                                   text: str, image_bytes: Optional[bytes] = None, 
                                   reply_markup: Optional[dict] = None) -> bool:
        """向指定聊天会话发送图文或纯文本消息"""
        try:
            if image_bytes:
                text_parts = split_text(text, max_length=CAPTION_LIMIT)
                files = {"photo": ("rank.jpg", image_bytes, "image/jpeg")}
                data = {
                    "chat_id": chat_id,
                    "caption": text_parts[0],
                    "parse_mode": "Markdown"
                }
                if reply_markup and len(text_parts) == 1:
                    data["reply_markup"] = json.dumps(reply_markup)
                    
                resp = await client.post(f"{self.base_url}/sendPhoto", data=data, files=files)
                resp_json = resp.json()
                if not resp_json.get("ok"):
                    logger.error(f"Telegram 发送图片失败: {resp.text}")
                    return False

                for idx, part in enumerate(text_parts[1:], 1):
                    msg_payload = {
                        "chat_id": chat_id, 
                        "text": part, 
                        "parse_mode": "Markdown"
                    }
                    if reply_markup and idx == len(text_parts) - 1:
                        msg_payload["reply_markup"] = reply_markup
                    await client.post(f"{self.base_url}/sendMessage", json=msg_payload)
            else:
                text_parts = split_text(text, max_length=TEXT_LIMIT)
                for idx, part in enumerate(text_parts):
                    msg_payload = {
                        "chat_id": chat_id, 
                        "text": part, 
                        "parse_mode": "Markdown"
                    }
                    if reply_markup and idx == len(text_parts) - 1:
                        msg_payload["reply_markup"] = reply_markup
                    await client.post(f"{self.base_url}/sendMessage", json=msg_payload)
            return True
        except Exception as e:
            logger.error(f"发送消息到 {chat_id} 异常: {e}")
            return False

    async def send_report(self, title: str, text: str, 
                          image_bytes: Optional[bytes] = None, 
                          pin: bool = False,
                          task_id: str = "general",
                          reply_markup: Optional[dict] = None) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram 配置缺失 bot_token 或 chat_id")
            return False

        transport_args = {}
        if self.proxy:
            transport_args["proxy"] = self.proxy

        async with httpx.AsyncClient(timeout=40.0, **transport_args) as client:
            try:
                # 1. 尝试取消上一期的置顶
                if pin and self.pin_message:
                    old_msg_id = self._get_pinned_id(task_id)
                    if old_msg_id:
                        await self._unpin(client, old_msg_id)

                first_msg_id = None

                # 2. 发送消息
                if image_bytes:
                    text_parts = split_text(text, max_length=CAPTION_LIMIT)
                    files = {"photo": ("rank.jpg", image_bytes, "image/jpeg")}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": text_parts[0],
                        "parse_mode": "Markdown"
                    }
                    if reply_markup and len(text_parts) == 1:
                        data["reply_markup"] = json.dumps(reply_markup)
                        
                    resp = await client.post(f"{self.base_url}/sendPhoto", data=data, files=files)
                    resp_json = resp.json()
                    if not resp_json.get("ok"):
                        logger.error(f"Telegram 发送图片失败: {resp.text}")
                        return False
                    
                    first_msg_id = resp_json["result"]["message_id"]

                    for idx, part in enumerate(text_parts[1:], 1):
                        msg_payload = {
                            "chat_id": self.chat_id, 
                            "text": part, 
                            "parse_mode": "Markdown"
                        }
                        if reply_markup and idx == len(text_parts) - 1:
                            msg_payload["reply_markup"] = reply_markup
                        await client.post(f"{self.base_url}/sendMessage", json=msg_payload)
                else:
                    text_parts = split_text(text, max_length=TEXT_LIMIT)
                    for idx, part in enumerate(text_parts):
                        msg_payload = {
                            "chat_id": self.chat_id, 
                            "text": part, 
                            "parse_mode": "Markdown"
                        }
                        if reply_markup and idx == len(text_parts) - 1:
                            msg_payload["reply_markup"] = reply_markup
                            
                        resp = await client.post(f"{self.base_url}/sendMessage", json=msg_payload)
                        resp_json = resp.json()
                        if idx == 0 and resp_json.get("ok"):
                            first_msg_id = resp_json["result"]["message_id"]

                # 3. 置顶最新消息
                if pin and self.pin_message and first_msg_id:
                    await self._pin(client, first_msg_id)
                    self._save_pinned_id(task_id, first_msg_id)

                logger.info(f"Telegram 榜单推送成功: {task_id}")
                return True

            except Exception as e:
                logger.error(f"Telegram 推送异常: {e}")
                return False

    async def _check_is_admin(self, client: httpx.AsyncClient, chat_id: Any, user_id: int) -> bool:
        """检查用户是否为群组管理员 (私聊自动视为管理员)"""
        try:
            if int(chat_id) > 0:
                return True
            resp = await client.get(
                f"{self.base_url}/getChatMember",
                params={"chat_id": chat_id, "user_id": user_id}
            )
            data = resp.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status", "")
                return status in ("creator", "administrator")
        except Exception as e:
            logger.debug(f"检测管理员权限异常: {e}")
        return False

    def _check_cooldown(self, user_id: int, is_admin: bool) -> Tuple[bool, int]:
        """检查命令冷却时间"""
        if is_admin or self.cooldown_seconds <= 0:
            return True, 0
        now = asyncio.get_event_loop().time()
        last = self._user_cooldowns.get(user_id, 0)
        diff = now - last
        if diff < self.cooldown_seconds:
            return False, int(self.cooldown_seconds - diff)
        self._user_cooldowns[user_id] = now
        return True, 0

    async def handle_callback_polling(self, stats_engine):
        """后台长轮询处理 Telegram 翻页回调与交互命令"""
        offset = 0
        transport_args = {}
        if self.proxy:
            transport_args["proxy"] = self.proxy

        logger.info("已启动 Telegram 交互命令与按键回调监听服务")
        while True:
            try:
                async with httpx.AsyncClient(timeout=35.0, **transport_args) as client:
                    # 首次启动时获取机器人 Username 并注册左下角菜单命令
                    if not self.bot_username:
                        try:
                            me_resp = await client.get(f"{self.base_url}/getMe")
                            me_data = me_resp.json()
                            if me_data.get("ok"):
                                self.bot_username = me_data.get("result", {}).get("username", "").lower()
                        except Exception:
                            pass

                        try:
                            commands = [
                                {"command": "now", "description": "查看当前 Emby 正在播放状态"},
                                {"command": "drank", "description": "今日媒体播放排行榜海报"},
                                {"command": "wrank", "description": "本周媒体播放排行榜海报"},
                                {"command": "urank", "description": "用户观看时长排行榜"},
                                {"command": "help", "description": "显示机器人指令帮助菜单"},
                            ]
                            await client.post(f"{self.base_url}/setMyCommands", json={"commands": commands})
                            await client.post(f"{self.base_url}/setChatMenuButton", json={"menu_button": {"type": "commands"}})
                            logger.info("已成功同步 Telegram 机器人快捷菜单命令")
                        except Exception as e:
                            logger.debug(f"同步 Telegram 快捷菜单命令异常: {e}")

                    resp = await client.get(
                        f"{self.base_url}/getUpdates",
                        params={
                            "offset": offset, 
                            "timeout": 20, 
                            "allowed_updates": ["message", "callback_query"]
                        }
                    )
                    data = resp.json()
                    if not data.get("ok"):
                        await asyncio.sleep(5)
                        continue

                    for update in data.get("result", []):
                        offset = max(offset, update["update_id"] + 1)

                        # 1. 处理按键回调 (Callback Query)
                        callback = update.get("callback_query")
                        if callback:
                            cq_id = callback["id"]
                            cb_data = callback.get("data", "")
                            msg = callback.get("message")
                            cb_user_id = callback.get("from", {}).get("id", 0)
                            cb_chat_id = msg.get("chat", {}).get("id") if msg else 0

                            # 私聊白名单校验
                            if cb_chat_id and int(cb_chat_id) > 0 and not self._is_user_allowed_in_private(cb_user_id):
                                await client.post(f"{self.base_url}/answerCallbackQuery", json={
                                    "callback_query_id": cq_id,
                                    "text": f"⛔ 您未在私聊白名单中 (User ID: {cb_user_id})",
                                    "show_alert": True
                                })
                                continue

                            if cb_data == "noop":
                                await client.post(f"{self.base_url}/answerCallbackQuery", json={"callback_query_id": cq_id})
                                continue

                            if cb_data == "closeit" or cb_data == "close":
                                if msg and "chat" in msg and "message_id" in msg:
                                    try:
                                        await client.post(f"{self.base_url}/deleteMessage", json={
                                            "chat_id": msg["chat"]["id"],
                                            "message_id": msg["message_id"]
                                        })
                                    except Exception as e:
                                        logger.debug(f"删除消息失败: {e}")
                                await client.post(f"{self.base_url}/answerCallbackQuery", json={"callback_query_id": cq_id, "text": "已关闭"})
                                continue

                            if cb_data.startswith("uplays:"):
                                parts = cb_data.split(":")
                                if len(parts) == 3:
                                    days = int(parts[1])
                                    page = int(parts[2])
                                    is_weekly = (days >= 7)

                                    new_text, total_pages, cur_page = await stats_engine.generate_user_play_rank(
                                        days=days, is_weekly=is_weekly, page=page
                                    )
                                    new_markup = make_pagination_keyboard(days, cur_page, total_pages)

                                    is_photo_msg = bool(msg.get("photo"))
                                    if is_photo_msg:
                                        edit_payload = {
                                            "chat_id": msg["chat"]["id"],
                                            "message_id": msg["message_id"],
                                            "caption": new_text,
                                            "parse_mode": "Markdown"
                                        }
                                        if new_markup:
                                            edit_payload["reply_markup"] = new_markup
                                        await client.post(f"{self.base_url}/editMessageCaption", json=edit_payload)
                                    else:
                                        edit_payload = {
                                            "chat_id": msg["chat"]["id"],
                                            "message_id": msg["message_id"],
                                            "text": new_text,
                                            "parse_mode": "Markdown"
                                        }
                                        if new_markup:
                                            edit_payload["reply_markup"] = new_markup
                                        await client.post(f"{self.base_url}/editMessageText", json=edit_payload)

                                    await client.post(
                                        f"{self.base_url}/answerCallbackQuery", 
                                        json={"callback_query_id": cq_id, "text": f"已切换至第 {cur_page}/{total_pages} 页"}
                                    )
                            continue

                        # 2. 处理文本指令 (Message)
                        message = update.get("message")
                        if message and "text" in message:
                            raw_text = message.get("text", "").strip()
                            if not raw_text.startswith("/"):
                                continue

                            chat = message.get("chat", {})
                            chat_id = chat.get("id")
                            from_user = message.get("from", {})
                            user_id = from_user.get("id", 0)

                            parts = raw_text.split()
                            raw_cmd = parts[0]
                            cmd = raw_cmd.lower()
                            
                            # 处理带有 @username 的指令 (如 /now@my_bot)
                            if "@" in cmd:
                                target_cmd, target_bot = cmd.split("@", 1)
                                if self.bot_username and target_bot != self.bot_username:
                                    continue
                                cmd = target_cmd

                            # 1) 私聊白名单限制 (私聊 chat_id > 0)
                            if int(chat_id) > 0 and not self._is_user_allowed_in_private(user_id):
                                await self.send_message_to_chat(
                                    client, chat_id, 
                                    f"⛔ **访问受限**\n您未在机器人的私聊授权白名单中。\n\n🆔 您的 Telegram User ID: `{user_id}`"
                                )
                                continue

                            # 2) 群聊权限与冷却检测 (群聊 chat_id < 0)
                            if int(chat_id) < 0:
                                is_admin = await self._check_is_admin(client, chat_id, user_id)
                                if self.admin_only and not is_admin:
                                    continue

                                allowed, remain = self._check_cooldown(user_id, is_admin)
                                if not allowed:
                                    await self.send_message_to_chat(
                                        client, chat_id, 
                                        f"⏱️ **操作过于频繁**\n请等待 `{remain}` 秒后再试。"
                                    )
                                    continue

                            # 指令 1: 帮助菜单
                            if cmd in ("/help", "/start"):
                                help_msg = (
                                    f"🤖 **{stats_engine.server_name} 机器人指令中心**\n\n"
                                    "🎬 /drank - 召唤今日媒体播放日榜海报\n"
                                    "🏆 /wrank - 召唤本周媒体播放周榜海报\n"
                                    "🥇 /urank - 召唤用户时长榜 (支持 `/urank 1` 或 `/urank 30`)\n"
                                    "📊 /now - 查看当前 Emby 在线与播放状态\n"
                                    "❓ /help - 显示此指令帮助菜单\n\n"
                                    "💡 *直接点击上方蓝色命令即可发送执行；也可点击左下角【菜单】选择命令*"
                                )
                                await self.send_message_to_chat(client, chat_id, help_msg)
                                continue

                            # 指令 2: 实时观影状态
                            if cmd in ("/now", "/status", "/playing"):
                                status_text = await stats_engine.generate_watching_status()
                                await self.send_message_to_chat(client, chat_id, status_text)
                                continue

                            # 指令 3: 播放日榜
                            if cmd in ("/drank", "/day_rank", "/day"):
                                img, text = await stats_engine.generate_media_rank(days=1, is_weekly=False)
                                await self.send_message_to_chat(client, chat_id, text, image_bytes=img)
                                continue

                            # 指令 4: 播放周榜
                            if cmd in ("/wrank", "/week_rank", "/week"):
                                img, text = await stats_engine.generate_media_rank(days=7, is_weekly=True)
                                await self.send_message_to_chat(client, chat_id, text, image_bytes=img)
                                continue

                            # 指令 5: 用户时长榜
                            if cmd in ("/urank", "/uplays", "/play_rank"):
                                days = 7
                                if len(parts) > 1 and parts[1].isdigit():
                                    days = max(1, min(365, int(parts[1])))
                                is_weekly = (days >= 7)

                                text, total_pages, cur_page = await stats_engine.generate_user_play_rank(
                                    days=days, is_weekly=is_weekly, page=1
                                )
                                user_img = await stats_engine.get_user_rank_image_bytes()
                                markup = make_pagination_keyboard(days=days, current_page=cur_page, total_pages=total_pages)
                                await self.send_message_to_chat(client, chat_id, text, image_bytes=user_img, reply_markup=markup)
                                continue

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Telegram 轮询异常 (将在5秒后重试): {e}")
                await asyncio.sleep(5)

