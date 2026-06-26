import asyncio
import logging
from aiohttp import web
from app.logging_config import setup_logging
from app.database import init_db
from app.bots.psychologist.bot import run_psychologist
from app.bots.studio_tg.bot import run_studio_tg
from app.bots.detailing.bot import run_detailing_bot

setup_logging()
logger = logging.getLogger(__name__)

async def health_handler(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.router.add_get('/health', health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health check server started on port 8080")
    while True:
        await asyncio.sleep(3600)

async def resilient_runner(name, coro_func):
    while True:
        try:
            logger.info(f"Starting {name}")
            await coro_func()
        except asyncio.CancelledError:
            logger.info(f"{name} cancelled")
            break
        except Exception as e:
            logger.exception(f"{name} crashed: {e}")
            await asyncio.sleep(5)

async def main():
    await init_db()
    logger.info("Database initialized")
    # Запускаем health‑сервер в фоне
    health_task = asyncio.create_task(run_health_server())
    await asyncio.gather(
        resilient_runner("psychologist", run_psychologist),
        resilient_runner("studio_tg", run_studio_tg),
        resilient_runner("detailing", run_detailing_bot),
        health_task  # health-сервер не должен падать, но если упадёт – перезапустим? для простоты просто ждём
    )

if __name__ == "__main__":
    asyncio.run(main())