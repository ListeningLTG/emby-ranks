import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Response, Query, UploadFile, File
from core.stats_engine import StatsEngine, format_seconds
from core.emby_client import EmbyClient
from core.drawer import RanksDrawer
from core.config import save_config

logger = logging.getLogger("emby-ranks.api.ranks")
router = APIRouter(prefix="/api", tags=["榜单数据与海报预览"])


@router.get("/ranks/media")
async def get_media_ranks(days: int = Query(1, description="查询天数: 1为日榜, 7为周榜"), request: Request = None):
    """获取媒体播放次数排行榜数据"""
    emby: EmbyClient = request.app.state.emby
    config = request.app.state.config
    try:
        movies = await emby.get_media_report(media_type="Movie", days=days, limit=config.poster.top_limit)
        tvshows = await emby.get_media_report(media_type="Episode", days=days, limit=config.poster.top_limit)
        
        # 格式化数据结构
        def format_items(items):
            res = []
            for item in items:
                user_id, item_id, item_type, name, count, duration = tuple(item)
                res.append({
                    "item_id": item_id,
                    "type": item_type,
                    "name": name,
                    "play_count": count,
                    "duration_seconds": int(duration) if duration else 0,
                    "duration_str": format_seconds(int(duration) if duration else 0)
                })
            return res

        return {
            "days": days,
            "movies": format_items(movies),
            "tvshows": format_items(tvshows)
        }
    except Exception as e:
        logger.error(f"获取媒体榜单数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取媒体榜单数据失败: {str(e)}")


import math

@router.get("/ranks/users")
async def get_user_ranks(
    days: int = Query(7, description="查询天数: 1为日榜, 7为周榜"),
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页显示条数"),
    request: Request = None
):
    """获取用户观看时长排行榜数据 (支持分页)"""
    emby: EmbyClient = request.app.state.emby
    try:
        records = await emby.get_user_play_report(days=days)
        users_map = await emby.get_users_map()
        
        total_users = len(records)
        total_pages = max(1, math.ceil(total_users / page_size))
        page = min(page, total_pages)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_records = records[start_idx:end_idx]

        res = []
        for idx, item in enumerate(page_records, start=start_idx + 1):
            uid, watch_time = item[0], item[1]
            user_name = users_map.get(uid, str(uid) if uid else "未知用户")
            res.append({
                "rank": idx,
                "user_id": uid,
                "user_name": user_name,
                "watch_time_seconds": int(watch_time) if watch_time else 0,
                "watch_time_str": format_seconds(int(watch_time) if watch_time else 0)
            })

        return {
            "days": days,
            "page": page,
            "page_size": page_size,
            "total_users": total_users,
            "total_pages": total_pages,
            "users": res
        }
    except Exception as e:
        logger.error(f"获取用户时长榜单数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户时长榜单数据失败: {str(e)}")


@router.get("/ranks/sessions")
async def get_sessions(request: Request):
    """获取当前 Emby 正在播放的会话与在线用户"""
    emby: EmbyClient = request.app.state.emby
    try:
        sessions = await emby.get_sessions()
        online_users = set()
        playing_items = []

        for s in sessions:
            uid = s.get("UserId")
            if uid:
                online_users.add(uid)
            
            now_playing = s.get("NowPlayingItem")
            if now_playing:
                play_state = s.get("PlayState", {})
                is_paused = play_state.get("IsPaused", False)
                media_type = now_playing.get("Type", "Unknown")
                name = now_playing.get("Name", "未知")
                if media_type == "Episode":
                    series_name = now_playing.get("SeriesName", "")
                    if series_name:
                        name = f"{series_name} - {name}"

                playing_items.append({
                    "user_name": s.get("UserName", "匿名"),
                    "client": s.get("Client", "未知客户端"),
                    "device_name": s.get("DeviceName", "未知设备"),
                    "item_id": now_playing.get("Id"),
                    "item_name": name,
                    "item_type": media_type,
                    "is_paused": is_paused,
                    "position_ticks": play_state.get("PositionTicks", 0),
                    "total_ticks": now_playing.get("RunTimeTicks", 0)
                })

        return {
            "online_count": len(online_users),
            "playing_count": len(playing_items),
            "playing_items": playing_items
        }
    except Exception as e:
        logger.error(f"获取会话数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话数据失败: {str(e)}")


@router.get("/poster/preview")
async def preview_poster(
    type: str = Query("day_rank", description="海报类型: day_rank 或 week_rank"),
    backdrop: bool = Query(False, description="是否使用横版剧照"),
    request: Request = None
):
    """在线生成海报图片预览并直接返回 JPEG 图片流"""
    emby: EmbyClient = request.app.state.emby
    config = request.app.state.config
    
    is_weekly = (type == "week_rank")
    days = 7 if is_weekly else 1

    try:
        movies = await emby.get_media_report(media_type="Movie", days=days, limit=5)
        tvshows = await emby.get_media_report(media_type="Episode", days=days, limit=5)

        drawer = RanksDrawer(
            assets_dir=config.poster.assets_dir,
            server_name=config.emby.server_name,
            weekly=is_weekly,
            backdrop=backdrop
        )
        await drawer.draw(emby, movies, tvshows)
        img_bytes = drawer.save_bytes()

        return Response(content=img_bytes, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"生成海报预览失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成海报预览失败: {str(e)}")


@router.post("/poster/upload_user_cover")
async def upload_user_cover(file: UploadFile = File(...), request: Request = None):
    """上传本地图片作为用户时长榜的封面图"""
    config = request.app.state.config
    try:
        assets_dir = Path(config.poster.assets_dir)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # 保留文件后缀或默认使用 .jpg
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        if not ext.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
        
        save_name = f"user_rank_cover{ext}"
        target_path = assets_dir / save_name
        
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
            
        relative_path = f"./assets/{save_name}"
        config.poster.user_rank_image = relative_path
        save_config(config)
        
        # 更新 stats 中的引用
        stats: StatsEngine = request.app.state.stats
        if stats:
            stats.user_rank_image = relative_path
            
        logger.info(f"用户时长榜封面已上传并保存至: {target_path}")
        return {
            "success": True, 
            "image_path": relative_path,
            "message": "封面图上传成功并已同步保存至系统配置！"
        }
    except Exception as e:
        logger.error(f"上传封面失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传封面失败: {str(e)}")


@router.get("/poster/user_cover")
async def get_user_cover(request: Request):
    """获取当前配置的用户时长榜封面图"""
    stats: StatsEngine = request.app.state.stats
    if not stats:
        raise HTTPException(status_code=500, detail="服务未初始化")
    img_bytes = await stats.get_user_rank_image_bytes()
    if not img_bytes:
        raise HTTPException(status_code=404, detail="未配置封面图或封面加载失败")
    return Response(content=img_bytes, media_type="image/jpeg")


@router.post("/trigger/{task_name}")
async def trigger_task(task_name: str, request: Request):
    """手动立即触发指定的榜单推送任务"""
    scheduler = request.app.state.scheduler
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    task_map = {
        "day_rank": scheduler.run_day_rank,
        "week_rank": scheduler.run_week_rank,
        "day_play_rank": scheduler.run_day_play_rank,
        "week_play_rank": scheduler.run_week_play_rank,
    }

    if task_name not in task_map:
        raise HTTPException(status_code=400, detail=f"未知任务: {task_name}，可选: {list(task_map.keys())}")

    try:
        logger.info(f"网页端手动触发任务: {task_name}")
        await task_map[task_name]()
        return {"success": True, "message": f"任务 [{task_name}] 已成功执行并分发至通知渠道！"}
    except Exception as e:
        logger.error(f"执行任务 [{task_name}] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")
