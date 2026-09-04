"""
MedScribe Backend — Structured Logging via Loguru
"""
from __future__ import annotations

import sys
from loguru import logger


def setup_logging(debug: bool = False) -> None:
    """Configure loguru with human-readable console + rotating file output."""
    logger.remove()  # Clear default handler

    log_level = "DEBUG" if debug else "INFO"

    # ── Console handler (colorized) ──────────────────────────────────────────
    logger.add(
        sys.stdout,
        level=log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    # ── File handler (rotating, JSON-friendly) ───────────────────────────────
    logger.add(
        "logs/medscribe.log",
        level="DEBUG",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        enqueue=True,
    )

    logger.info("Logging initialized — level={}", log_level)


__all__ = ["logger", "setup_logging"]
