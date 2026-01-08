"""Authentication service for API key verification."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User
from app.db.crud import get_user_by_api_key, get_user_cameras

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication and authorization."""

    @staticmethod
    async def verify_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
        """
        Verify API key and return user if valid.

        Args:
            db: Database session
            api_key: API key to verify

        Returns:
            User object if valid, None otherwise
        """
        try:
            user = await get_user_by_api_key(db, api_key)

            if not user:
                logger.warning(f"Invalid API key attempted")
                return None

            if user.status != "active":
                logger.warning(f"Inactive user attempted access: {user.email}")
                return None

            return user

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return None

    @staticmethod
    async def check_camera_limit(db: AsyncSession, user: User, camera_id: str) -> tuple[bool, str]:
        """
        Check if user can add/use this camera based on their plan limits.

        Args:
            db: Database session
            user: User object
            camera_id: Camera ID to check

        Returns:
            Tuple of (allowed: bool, message: str)
        """
        try:
            # Get user's cameras
            cameras = await get_user_cameras(db, user.id)
            camera_ids = [cam.id for cam in cameras]

            # If camera already exists for this user, allow it
            if camera_id in camera_ids:
                return True, "Camera already registered"

            # Check if user has reached their limit
            if len(cameras) >= user.cameras_allowed:
                return False, f"Camera limit reached. Your {user.plan} plan allows {user.cameras_allowed} cameras."

            return True, "Camera limit not reached"

        except Exception as e:
            logger.error(f"Error checking camera limit: {e}")
            return False, "Error checking camera limit"


# Global instance
auth_service = AuthService()
