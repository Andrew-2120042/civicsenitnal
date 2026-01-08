"""Zone detection service for checking if detections are in restricted zones."""

import json
import logging
from typing import List, Tuple
from shapely.geometry import Point, Polygon

from app.models.database import Zone
from app.models.schemas import Detection, ZoneAlert, BoundingBox

logger = logging.getLogger(__name__)


class ZoneDetectionService:
    """Service for checking if detections fall within restricted zones."""

    @staticmethod
    def parse_zone_coordinates(coordinates_json: str) -> List[Tuple[float, float]]:
        """
        Parse zone coordinates from JSON string.

        Args:
            coordinates_json: JSON string of coordinates [[x1, y1], [x2, y2], ...]

        Returns:
            List of (x, y) tuples
        """
        try:
            coords = json.loads(coordinates_json)
            return [(float(x), float(y)) for x, y in coords]
        except Exception as e:
            logger.error(f"Failed to parse zone coordinates: {e}")
            return []

    @staticmethod
    def is_point_in_polygon(point: Tuple[float, float], polygon_coords: List[Tuple[float, float]]) -> bool:
        """
        Check if a point is inside a polygon using Shapely.

        Args:
            point: (x, y) tuple
            polygon_coords: List of (x, y) tuples defining polygon vertices

        Returns:
            True if point is inside polygon, False otherwise
        """
        try:
            if len(polygon_coords) < 3:
                logger.warning("Polygon must have at least 3 points")
                return False

            point_obj = Point(point[0], point[1])
            polygon = Polygon(polygon_coords)

            return polygon.contains(point_obj)

        except Exception as e:
            logger.error(f"Error checking point in polygon: {e}")
            return False

    @staticmethod
    def get_bbox_center(bbox: BoundingBox) -> Tuple[float, float]:
        """
        Get center point of bounding box.

        Args:
            bbox: BoundingBox object

        Returns:
            Tuple of (center_x, center_y)
        """
        center_x = (bbox.x1 + bbox.x2) / 2
        center_y = (bbox.y1 + bbox.y2) / 2
        return center_x, center_y

    def check_zones(self, detections: List[Detection], zones: List[Zone]) -> List[ZoneAlert]:
        """
        Check if any detections fall within restricted zones.

        Args:
            detections: List of Detection objects
            zones: List of Zone objects to check against

        Returns:
            List of ZoneAlert objects for zone violations
        """
        alerts = []

        if not zones:
            logger.debug("No zones to check")
            return alerts

        for zone in zones:
            # Skip inactive zones
            if not zone.active:
                continue

            # Parse zone coordinates
            polygon_coords = self.parse_zone_coordinates(zone.coordinates_json)
            if not polygon_coords:
                logger.warning(f"Zone {zone.id} has invalid coordinates")
                continue

            # Check each detection
            for detection in detections:
                # Get center of bounding box
                center = self.get_bbox_center(detection.bbox)

                # Check if center is in zone
                if self.is_point_in_polygon(center, polygon_coords):
                    # Create alert
                    alert = ZoneAlert(
                        zone_id=zone.id,
                        zone_name=zone.name,
                        alert_type=zone.alert_type,
                        confidence=detection.confidence,
                    )
                    alerts.append(alert)

                    logger.info(
                        f"Zone violation detected: {zone.name} "
                        f"(confidence: {detection.confidence:.2f})"
                    )

        return alerts


# Global instance
zone_service = ZoneDetectionService()
