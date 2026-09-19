import logging
from fastapi import APIRouter, HTTPException, Request
from core.config import AppConfig, save_config
from core.emby_client import EmbyClient
from core.stats_engine import StatsEngine

logger = logging.getLogger("emby-ranks.api.config")
router = APIRouter(prefix="/api", tags=["系统配置与状态"])


@router.get("/config")
async def get_config(request: Request):
    """获取当前系统配置"""
    config: AppConfig = request.app.state.config
    # 脱敏输出或者直接返回全量配置给前端
    return config.model_dump()


@router.post("/config")
async def update_config(new_config_data: dict, request: Request):
    """更新并保存系统配置，同时热重载调度器"""
    try:
        new_config = AppConfig(**new_config_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"配置格式错误: {str(e)}")

    try:
        # 保存到配置文件
        saved_path = save_config(new_config)
        
        # 更新 app.state
        request.app.state.config = new_config

        # 重新创建 EmbyClient & StatsEngine
        emby = EmbyClient(
            base_url=new_config.emby.url,
            api_key=new_config.emby.api_key,
            timezone=new_config.timezone
        )
        stats = StatsEngine(
            emby_client=emby,
            assets_dir=new_config.poster.assets_dir,
            server_name=new_config.emby.server_name,
            timezone=new_config.timezone,
            use_backdrop=new_config.poster.use_backdrop,
            top_limit=new_config.poster.top_limit,
            user_rank_image=new_config.poster.user_rank_image
        )
        request.app.state.emby = emby
        request.app.state.stats = stats

        # 热重载调度器
        scheduler = request.app.state.scheduler
        if scheduler:
            scheduler.reload_config(new_config, stats)

        logger.info(f"配置已更新并保存至 {saved_path}")
        return {"success": True, "message": "配置更新成功并已热重载生效！"}
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/status")
async def get_status(request: Request):
    """获取系统运行状态"""
    config: AppConfig = request.app.state.config
    scheduler = request.app.state.scheduler
    emby: EmbyClient = request.app.state.emby

    jobs_info = []
    if scheduler and scheduler.scheduler.running:
        for job in scheduler.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
            })

    # 简易检测 Emby 是否连通
    emby_connected = False
    emby_users_count = 0
    try:
        users = await emby.get_users_map()
        if users:
            emby_connected = True
            emby_users_count = len(users)
    except Exception:
        pass

    return {
        "version": "1.0.0",
        "timezone": config.timezone,
        "emby": {
            "server_name": config.emby.server_name,
            "url": config.emby.url,
            "connected": emby_connected,
            "users_count": emby_users_count
        },
        "scheduler_running": scheduler.scheduler.running if scheduler else False,
        "jobs": jobs_info,
        "notifiers": {
            "telegram": config.notifiers.telegram.enabled,
            "discord": config.notifiers.discord.enabled,
            "webhook": config.notifiers.webhook.enabled
        }
    }
