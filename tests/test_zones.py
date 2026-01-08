"""Tests for zone detection service."""

import pytest
from app.services.zone_service import ZoneDetectionService
from app.models.schemas import Detection, BoundingBox


class TestZoneDetectionService:
    """Test cases for ZoneDetectionService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.zone_service = ZoneDetectionService()

    def test_parse_zone_coordinates(self):
        """Test parsing zone coordinates from JSON."""
        coords_json = '[[100, 200], [300, 200], [300, 400], [100, 400]]'
        coords = self.zone_service.parse_zone_coordinates(coords_json)

        assert len(coords) == 4
        assert coords[0] == (100.0, 200.0)
        assert coords[3] == (100.0, 400.0)

    def test_parse_invalid_coordinates(self):
        """Test parsing invalid coordinates."""
        invalid_json = "invalid json"
        coords = self.zone_service.parse_zone_coordinates(invalid_json)

        assert coords == []

    def test_point_in_polygon_inside(self):
        """Test point inside polygon."""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (50, 50)

        result = self.zone_service.is_point_in_polygon(point, polygon)
        assert result is True

    def test_point_in_polygon_outside(self):
        """Test point outside polygon."""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (150, 150)

        result = self.zone_service.is_point_in_polygon(point, polygon)
        assert result is False

    def test_point_on_edge(self):
        """Test point on polygon edge."""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (0, 50)

        # Point on edge behavior depends on Shapely implementation
        result = self.zone_service.is_point_in_polygon(point, polygon)
        assert isinstance(result, bool)

    def test_get_bbox_center(self):
        """Test getting bounding box center."""
        bbox = BoundingBox(x1=100, y1=200, x2=300, y2=400)
        center = self.zone_service.get_bbox_center(bbox)

        assert center == (200.0, 300.0)

    def test_invalid_polygon(self):
        """Test polygon with less than 3 points."""
        polygon = [(0, 0), (100, 0)]
        point = (50, 50)

        result = self.zone_service.is_point_in_polygon(point, polygon)
        assert result is False
