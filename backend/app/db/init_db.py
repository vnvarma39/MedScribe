"""
MedScribe — Standalone Database Initializer
"""
from app.db.database import create_tables, engine
from app.db.models import Base
from app.core.logging import logger

def init() -> None:
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Database tables initialized successfully on engine: {}", engine.url)

if __name__ == "__main__":
    init()
