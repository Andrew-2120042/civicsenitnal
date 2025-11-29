"""YOLO detection service for object detection."""

import logging
from typing import List, Optional
from pathlib import Path
import numpy as np
from PIL import Image
from ultralytics import YOLO

from app.config import settings
from app.models.schemas import Detection, BoundingBox

logger = logging.getLogger(__name__)


class YOLODetectionService:
    """Service for YOLO-based object detection."""

    def __init__(self):
        """Initialize YOLO detection service."""
        self.model: Optional[YOLO] = None
        self.model_loaded = False
        self.confidence_threshold = settings.model_confidence_threshold
        self.frame_size = settings.model_frame_size

        # COCO class names - person is class 0
        self.person_class_id = 0
        self.class_names = {
            0: "person",
            1: "bicycle",
            2: "car",
            # ... other classes (we only care about person for now)
        }

    def load_model(self) -> bool:
        """Load YOLO model. Downloads if not present."""
        try:
            model_path = Path(settings.model_path)

            # Create models directory if it doesn't exist
            model_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Loading YOLO model from {model_path}")

            # This will auto-download if model doesn't exist
            self.model = YOLO("yolov8s.pt")

            # Move model to specified path
            if not model_path.exists():
                logger.info(f"Saving model to {model_path}")
                # The model is already downloaded in the ultralytics cache
                # We just need to initialize it
                self.model.save(str(model_path))

            self.model_loaded = True
            logger.info("YOLO model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model_loaded = False
            return False

    def detect_objects(self, image: Image.Image) -> List[Detection]:
        """
        Detect objects in an image with improved sensitivity.

        Args:
            image: PIL Image object

        Returns:
            List of Detection objects for persons only
        """
        if not self.model_loaded or self.model is None:
            logger.error("Model not loaded. Call load_model() first.")
            return []

        try:
            # Run inference with VERY LOW threshold to catch all possible detections
            # We'll filter afterwards to avoid missing people
            results = self.model(
                image,
                conf=0.2,  # Low threshold - detect everything, filter later
                imgsz=self.frame_size,
                verbose=False,
            )

            detections = []
            total_person_detections = 0
            rejected_low_conf = 0
            rejected_small_box = 0

            # Process results
            for result in results:
                boxes = result.boxes

                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])

                    # Only process person detections (class 0)
                    if class_id != self.person_class_id:
                        continue

                    total_person_detections += 1

                    # Get confidence
                    confidence = float(box.conf[0])

                    # Get bounding box coordinates (xyxy format)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Calculate box dimensions
                    width = x2 - x1
                    height = y2 - y1

                    # POST-PROCESSING FILTERS:
                    # Filter 1: Confidence must be > 0.3
                    if confidence < 0.3:
                        rejected_low_conf += 1
                        logger.debug(f"Rejected person: low confidence {confidence:.2f}")
                        continue

                    # Filter 2: Box must be reasonable size (not tiny artifacts)
                    if width < 20 or height < 40:
                        rejected_small_box += 1
                        logger.debug(f"Rejected person: too small ({width:.0f}x{height:.0f})")
                        continue

                    # Create detection object
                    detection = Detection(
                        class_name="person",
                        confidence=confidence,
                        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    )
                    detections.append(detection)

            # Log detection summary
            logger.info(f"Detected {len(detections)} persons in image "
                       f"(total: {total_person_detections}, "
                       f"rejected_low_conf: {rejected_low_conf}, "
                       f"rejected_small: {rejected_small_box})")

            return detections

        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return []

    def get_bbox_center(self, bbox: BoundingBox) -> tuple[float, float]:
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


# Global instance
yolo_service = YOLODetectionService()
