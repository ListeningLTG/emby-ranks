import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from core.logger import init_logger
from core.config import load_config, AppConfig
from core.emby_client import EmbyClient
from core.stats_engine import StatsEngine
from scheduler import RankScheduler

from backend.api.config_api import router as config_router
from backend.api.ranks_api import router as ranks_router
from backend.api.test_api import router as test_router

init_logger()
logger = logging.getLogger("emby-ranks.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载配置并启动调度器
    logger.info("正在启动 Emby-Ranks 后端服务...")
    config = getattr(app.state, "config", None) or load_config()
    app.state.config = config

    emby = EmbyClient(
        base_url=config.emby.url,
        api_key=config.emby.api_key,
        timezone=config.timezone
    )
    stats = StatsEngine(
        emby_client=emby,
        assets_dir=config.poster.assets_dir,
        server_name=config.emby.server_name,
        timezone=config.timezone,
        use_backdrop=config.poster.use_backdrop,
        top_limit=config.poster.top_limit,
        user_rank_image=config.poster.user_rank_image
    )
    scheduler = RankScheduler(config, stats)

    app.state.emby = emby
    app.state.stats = stats
    app.state.scheduler = scheduler

    scheduler.start()
    logger.info("Emby-Ranks 后端与定时任务调度器已就绪！")

    yield

    # 停止时清理
    logger.info("正在关闭调度器...")
    if scheduler.scheduler.running:
        scheduler.scheduler.shutdown()


def create_app(config: AppConfig = None) -> FastAPI:
    app = FastAPI(
        title="Emby-Ranks Web Console",
        description="Emby 媒体服务器播放与观影统计控制台",
        version="1.0.0",
        lifespan=lifespan
    )

    if config:
        app.state.config = config

    # 跨域配置 (支持本地开发)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由
    app.include_router(config_router)
    app.include_router(ranks_router)
    app.include_router(test_router)

    # 静态前端资源挂载 (SPA 支持)
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists() and (static_dir / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(static_dir / "index.html")

    return app
