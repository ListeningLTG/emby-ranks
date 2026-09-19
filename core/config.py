import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class EmbyConfig(BaseModel):
    url: str = ""
    api_key: str = ""
    server_name: str = ""


class PosterConfig(BaseModel):
    use_backdrop: bool = False
    top_limit: int = 10
    assets_dir: str = "./assets"
    user_rank_image: str = ""


class ScheduleItem(BaseModel):
    enabled: bool = False
    cron: str = "30 18 * * *"
    pin_message: bool = False


class SchedulesConfig(BaseModel):
    day_rank: ScheduleItem = Field(default_factory=lambda: ScheduleItem(enabled=False, cron="30 18 * * *", pin_message=True))
    week_rank: ScheduleItem = Field(default_factory=lambda: ScheduleItem(enabled=False, cron="59 23 * * 0", pin_message=True))
    day_play_rank: ScheduleItem = Field(default_factory=lambda: ScheduleItem(enabled=False, cron="00 23 * * *", pin_message=False))
    week_play_rank: ScheduleItem = Field(default_factory=lambda: ScheduleItem(enabled=False, cron="00 23 * * 0", pin_message=False))


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    pin_message: bool = True
    proxy: str = ""
    admin_only: bool = False
    cooldown_seconds: int = 15
    whitelist_user_ids: str = ""


class DiscordConfig(BaseModel):
    enabled: bool = False
    webhook_url: str = ""


class WebhookConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    headers: Dict[str, str] = Field(default_factory=dict)


class NotifiersConfig(BaseModel):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)


class AppConfig(BaseModel):
    timezone: str = Field(default_factory=lambda: os.getenv("TZ", "Asia/Shanghai"))
    emby: EmbyConfig = Field(default_factory=EmbyConfig)
    poster: PosterConfig = Field(default_factory=PosterConfig)
    schedules: SchedulesConfig = Field(default_factory=SchedulesConfig)
    notifiers: NotifiersConfig = Field(default_factory=NotifiersConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载 YAML 配置文件，支持环境变量覆盖"""
    if not config_path:
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")

    path = Path(config_path)
    if not path.exists():
        example_path = Path("config/config.example.yaml")
        if example_path.exists():
            path = example_path
        else:
            return AppConfig()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # 环境变量覆盖
    if os.getenv("EMBY_URL"):
        data.setdefault("emby", {})["url"] = os.getenv("EMBY_URL")
    if os.getenv("EMBY_API_KEY"):
        data.setdefault("emby", {})["api_key"] = os.getenv("EMBY_API_KEY")
    if os.getenv("EMBY_SERVER_NAME"):
        data.setdefault("emby", {})["server_name"] = os.getenv("EMBY_SERVER_NAME")
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        data.setdefault("notifiers", {}).setdefault("telegram", {})["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
        data["notifiers"]["telegram"]["enabled"] = True
    if os.getenv("TELEGRAM_CHAT_ID"):
        data.setdefault("notifiers", {}).setdefault("telegram", {})["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")
        data["notifiers"]["telegram"]["enabled"] = True

    return AppConfig(**data)


def save_config(config: AppConfig, config_path: Optional[str] = None) -> str:
    """保存配置到 YAML 文件"""
    if not config_path:
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 转换为 dict 并保存
    data = config.model_dump()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
    return str(path)

