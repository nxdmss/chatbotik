"""
Main Application Entry Point
============================

Запуск бота и API сервера.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from fastapi import FastAPI

from core.config import settings
from core.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifecycle manager для FastAPI.
    Запускает и останавливает ресурсы.
    """
    logger.info("Starting application...")
    
    # Startup
    # TODO: Initialize database
    # TODO: Initialize Redis
    # TODO: Start bot polling
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Stop bot


# FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check database connection
    # TODO: Check Redis connection
    return {"status": "ready"}


# Telegram Bot
bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def main() -> None:
    """
    Main function to run both bot and API.
    """
    logger.info(
        "Starting %s v%s in %s mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received signal %s, shutting down...", sig)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start bot polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Error in main: %s", e, exc_info=True)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
