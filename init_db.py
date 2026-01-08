"""Initialize database with test user."""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import init_db, AsyncSessionLocal
from app.db.crud import create_user, get_user_by_api_key
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_database():
    """Initialize database and create test user."""
    try:
        # Initialize database tables
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database tables created successfully")

        # Create test user
        async with AsyncSessionLocal() as db:
            # Check if test user already exists
            existing_user = await get_user_by_api_key(db, settings.test_api_key)

            if existing_user:
                logger.info(f"Test user already exists: {existing_user.email}")
            else:
                # Create new test user
                user = await create_user(
                    db=db,
                    email="test@civicsentinel.com",
                    api_key=settings.test_api_key,
                    plan="free",
                    cameras_allowed=settings.max_cameras_free_plan,
                )
                await db.commit()
                logger.info(f"Created test user: {user.email}")
                logger.info(f"API Key: {user.api_key}")

        logger.info("Database initialization complete!")

    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(initialize_database())
