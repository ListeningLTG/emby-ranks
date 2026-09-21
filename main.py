import os
import sys
import asyncio
import argparse
import logging
from core.logger import init_logger
from core.config import load_config
from core.emby_client import EmbyClient
from core.stats_engine import StatsEngine
from scheduler import RankScheduler

# 初始化全局日志 (控制台 + data/logs/emby-ranks.log 按天滚动保留7天)
init_logger()
logger = logging.getLogger("emby-ranks")


async def main():
    parser = argparse.ArgumentParser(description="Emby-Ranks 媒体统计与榜单推送服务")
    parser.add_argument("-c", "--config", type=str, default=None, help="指定配置文件路径 (默认: config/config.yaml)")
    parser.add_argument("-d", "--daemon", action="store_true", help="以守护进程方式运行定时调度器")
    parser.add_argument("-r", "--run", type=str, choices=["day_rank", "week_rank", "day_play_rank", "week_play_rank", "watching"], help="手动单次执行指定任务")
    parser.add_argument("--save-poster", type=str, default=None, help="手动生成海报时将图片保存至指定文件路径")

    parser.add_argument("--host", type=str, default=os.getenv("HOST", "0.0.0.0"), help="Web 服务监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Web 服务监听端口 (默认: 8000)")

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    logger.info(f"正在初始化 Emby-Ranks (服务器: {config.emby.server_name}, 目标: {config.emby.url})")

    # 模式 1: 手动执行单次任务 (CLI 模式)
    if args.run:
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
        rank_sched = RankScheduler(config, stats)

        logger.info(f"正在手动触发任务: {args.run}")
        if args.run == "day_rank":
            img, text = await stats.generate_media_rank(days=1, is_weekly=False)
            if args.save_poster and img:
                with open(args.save_poster, "wb") as f:
                    f.write(img)
                logger.info(f"海报已保存至: {args.save_poster}")
            await rank_sched.broadcast(f"{config.emby.server_name} 播放日榜", text, image_bytes=img, pin=False, task_id="day_rank")

        elif args.run == "week_rank":
            img, text = await stats.generate_media_rank(days=7, is_weekly=True)
            if args.save_poster and img:
                with open(args.save_poster, "wb") as f:
                    f.write(img)
                logger.info(f"海报已保存至: {args.save_poster}")
            await rank_sched.broadcast(f"{config.emby.server_name} 播放周榜", text, image_bytes=img, pin=False, task_id="week_rank")

        elif args.run == "day_play_rank":
            text = await stats.generate_user_play_rank(days=1, is_weekly=False)
            await rank_sched.broadcast(f"{config.emby.server_name} 用户时长日榜", text, pin=False, task_id="day_play_rank")

        elif args.run == "week_play_rank":
            text = await stats.generate_user_play_rank(days=7, is_weekly=True)
            await rank_sched.broadcast(f"{config.emby.server_name} 用户时长周榜", text, pin=False, task_id="week_play_rank")

        elif args.run == "watching":
            text = await stats.generate_watching_status()
            logger.info(f"\n{text}")
            await rank_sched.broadcast(f"{config.emby.server_name} 实时状态", text, pin=False, task_id="watching")
        return

    # 模式 2: Web 控制台与后台定时调度模式 (默认)
    import uvicorn
    from backend.app import create_app

    logger.info(f"启动 Emby-Ranks Web 控制台与定时调度服务: http://{args.host}:{args.port}")
    app = create_app(config)
    
    server_config = uvicorn.Config(
        app=app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(server_config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Emby-Ranks 服务已安全退出。")
        try:
            sys.exit(0)
        except SystemExit:
            pass

