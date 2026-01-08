"""
YOLO Detection Demo with Zone Drawing and Intrusion Detection
Interactive demo showing zone-based detection with visual alerts
"""

import cv2
from ultralytics import YOLO
import numpy as np
import json
import os

# Colors (BGR format)
COLORS = {
    'person': (0, 255, 0),      # Green for persons
    'car': (255, 0, 0),          # Blue for cars
    'truck': (0, 165, 255),      # Orange for trucks
    'default': (0, 255, 255)     # Yellow for others
}

ZONE_COLOR = (255, 0, 255)      # Magenta for zones
ALERT_COLOR = (0, 0, 255)       # Red for alerts
LINE_COLOR = (255, 255, 0)      # Cyan for lines

class ZoneDetectionDemo:
    def __init__(self, video_path, model_path='../yolov8s.pt', confidence_threshold=0.5):
        self.video_path = video_path
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold

        # Zone drawing state
        self.zones = []  # List of polygons (list of points)
        self.current_zone = []  # Points for zone being drawn
        self.drawing_mode = False

        # Detection state
        self.detections_in_zones = {}  # Track detections per zone
        self.alert_frames = 0  # Counter for alert animation

        # Mouse callback state
        self.mouse_x = 0
        self.mouse_y = 0

        # Load model
        print(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)

        # Open video
        print(f"Opening video: {video_path}")
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Error: Could not open video {video_path}")

        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"Video info: {self.width}x{self.height} @ {self.fps}fps, {self.total_frames} frames")

        # Try to load saved zones
        self.load_zones()

    def save_zones(self):
        """Save zones to JSON file"""
        zones_file = 'zones_config.json'
        with open(zones_file, 'w') as f:
            json.dump(self.zones, f, indent=2)
        print(f"\nZones saved to {zones_file}")

    def load_zones(self):
        """Load zones from JSON file if exists"""
        zones_file = 'zones_config.json'
        if os.path.exists(zones_file):
            with open(zones_file, 'r') as f:
                self.zones = json.load(f)
            print(f"Loaded {len(self.zones)} zones from {zones_file}")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for zone drawing"""
        self.mouse_x = x
        self.mouse_y = y

        if event == cv2.EVENT_LBUTTONDOWN and self.drawing_mode:
            # Add point to current zone
            self.current_zone.append([x, y])
            print(f"Point added: ({x}, {y})")

    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting"""
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_bbox_center(self, bbox):
        """Get center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def check_detection_in_zones(self, detections):
        """Check if any detection is in any zone"""
        detections_per_zone = {i: [] for i in range(len(self.zones))}

        for detection in detections:
            if len(detection.boxes) == 0:
                continue

            for i in range(len(detection.boxes)):
                # Get bounding box
                x1, y1, x2, y2 = detection.boxes.xyxy[i].cpu().numpy()
                center = self.get_bbox_center([x1, y1, x2, y2])

                # Get class info
                class_id = int(detection.boxes.cls[i])
                class_name = detection.names[class_id]
                confidence = float(detection.boxes.conf[i])

                # Check each zone
                for zone_idx, zone in enumerate(self.zones):
                    if len(zone) >= 3 and self.point_in_polygon(center, zone):
                        detections_per_zone[zone_idx].append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'class': class_name,
                            'confidence': confidence,
                            'center': center
                        })

        return detections_per_zone

    def draw_zones(self, frame, highlight_zones=None):
        """Draw all zones on frame"""
        if len(self.zones) == 0:
            return frame

        overlay = frame.copy()
        alpha = 0.2  # Default alpha

        for zone_idx, zone in enumerate(self.zones):
            if len(zone) < 2:
                continue

            # Convert to numpy array
            pts = np.array(zone, np.int32)
            pts = pts.reshape((-1, 1, 2))

            # Determine color based on whether zone has detections
            if highlight_zones and zone_idx in highlight_zones and len(highlight_zones[zone_idx]) > 0:
                zone_color = ALERT_COLOR
                alpha = 0.4
            else:
                zone_color = ZONE_COLOR
                alpha = 0.2

            # Draw filled polygon
            cv2.fillPoly(overlay, [pts], zone_color)

            # Draw zone outline
            cv2.polylines(frame, [pts], True, zone_color, 2)

            # Add zone label
            if len(zone) > 0:
                label_pos = (zone[0][0], zone[0][1] - 10)
                cv2.putText(frame, f'Zone {zone_idx + 1}', label_pos,
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, zone_color, 2)

        # Blend overlay with original frame
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        return frame

    def draw_current_zone(self, frame):
        """Draw zone currently being created"""
        if len(self.current_zone) == 0:
            return frame

        # Draw points
        for point in self.current_zone:
            cv2.circle(frame, tuple(point), 5, LINE_COLOR, -1)

        # Draw lines between points
        if len(self.current_zone) > 1:
            pts = np.array(self.current_zone, np.int32)
            cv2.polylines(frame, [pts], False, LINE_COLOR, 2)

        # Draw line to mouse cursor
        if len(self.current_zone) > 0:
            cv2.line(frame, tuple(self.current_zone[-1]),
                    (self.mouse_x, self.mouse_y), LINE_COLOR, 1)

        return frame

    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels"""
        for detection in detections:
            if len(detection.boxes) == 0:
                continue

            for i in range(len(detection.boxes)):
                # Get bounding box
                x1, y1, x2, y2 = detection.boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Get class info
                confidence = float(detection.boxes.conf[i])
                class_id = int(detection.boxes.cls[i])
                class_name = detection.names[class_id]

                # Get color
                color = COLORS.get(class_name, COLORS['default'])

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Draw label
                label = f'{class_name}: {confidence:.2f}'
                (label_width, label_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )

                # Label background
                cv2.rectangle(
                    frame,
                    (x1, y1 - label_height - baseline - 5),
                    (x1 + label_width, y1),
                    color,
                    -1
                )

                # Label text
                cv2.putText(
                    frame, label,
                    (x1, y1 - baseline - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2
                )

        return frame

    def draw_alerts(self, frame, detections_in_zones):
        """Draw alert panel when detections occur in zones"""
        total_detections = sum(len(dets) for dets in detections_in_zones.values())

        if total_detections > 0:
            # Alert banner at top
            alert_height = 80
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (self.width, alert_height), ALERT_COLOR, -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            # Alert text
            cv2.putText(frame, 'INTRUSION DETECTED!',
                       (self.width // 2 - 150, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

            # Details
            y_offset = 60
            for zone_idx, detections in detections_in_zones.items():
                if len(detections) > 0:
                    classes = [d['class'] for d in detections]
                    text = f"Zone {zone_idx + 1}: {len(detections)} {', '.join(set(classes))}"
                    cv2.putText(frame, text,
                               (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y_offset += 20

        return frame

    def draw_instructions(self, frame):
        """Draw instructions overlay"""
        instructions = [
            "Controls:",
            "D - Start/Stop Drawing Zone",
            "C - Complete Current Zone",
            "U - Undo Last Zone",
            "S - Save Zones",
            "R - Reset All Zones",
            "Q - Quit",
            "SPACE - Pause/Resume"
        ]

        # Draw semi-transparent panel
        panel_width = 300
        panel_height = len(instructions) * 25 + 20
        overlay = frame.copy()
        cv2.rectangle(overlay, (self.width - panel_width - 10, 10),
                     (self.width - 10, panel_height + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw text
        y_offset = 35
        for instruction in instructions:
            cv2.putText(frame, instruction,
                       (self.width - panel_width, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 25

        return frame

    def run(self):
        """Run the detection demo"""
        window_name = 'Zone-Based Detection Demo'
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback)

        print("\n" + "="*60)
        print("ZONE-BASED DETECTION DEMO")
        print("="*60)
        print("\nControls:")
        print("  D - Start/Stop drawing zone")
        print("  C - Complete current zone")
        print("  U - Undo last zone")
        print("  S - Save zones")
        print("  R - Reset all zones")
        print("  Q - Quit")
        print("  SPACE - Pause/Resume")
        print("="*60 + "\n")

        paused = False
        frame_count = 0

        while True:
            if not paused:
                ret, frame = self.cap.read()

                if not ret:
                    print("\nEnd of video - restarting...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue

                frame_count += 1

                # Run detection
                results = self.model(frame, conf=self.confidence_threshold, verbose=False)

                # Check detections in zones
                detections_in_zones = self.check_detection_in_zones(results)

                # Draw everything
                frame = self.draw_zones(frame, detections_in_zones)
                frame = self.draw_detections(frame, results)
                frame = self.draw_alerts(frame, detections_in_zones)
                frame = self.draw_current_zone(frame)
                frame = self.draw_instructions(frame)

                # Add frame info
                cv2.putText(frame, f'Frame: {frame_count}/{self.total_frames}',
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # Drawing mode indicator
                if self.drawing_mode:
                    cv2.putText(frame, 'DRAWING MODE - Click to add points',
                               (10, self.height - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, LINE_COLOR, 2)

            # Display frame
            cv2.imshow(window_name, frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord(' '):
                paused = not paused
                print("\nPaused" if paused else "\nResumed")
            elif key == ord('d'):
                self.drawing_mode = not self.drawing_mode
                if self.drawing_mode:
                    print("\nDrawing mode ON - Click to add zone points")
                else:
                    print("\nDrawing mode OFF")
            elif key == ord('c'):
                if len(self.current_zone) >= 3:
                    self.zones.append(self.current_zone)
                    print(f"\nZone {len(self.zones)} completed with {len(self.current_zone)} points")
                    self.current_zone = []
                    self.drawing_mode = False
                else:
                    print("\nNeed at least 3 points to create a zone")
            elif key == ord('u'):
                if len(self.zones) > 0:
                    removed = self.zones.pop()
                    print(f"\nRemoved zone {len(self.zones) + 1}")
                else:
                    print("\nNo zones to remove")
            elif key == ord('s'):
                self.save_zones()
            elif key == ord('r'):
                self.zones = []
                self.current_zone = []
                self.drawing_mode = False
                print("\nAll zones reset")

        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='YOLO Detection with Zone Drawing')
    parser.add_argument('video', help='Path to input video file')
    parser.add_argument('--model', '-m', default='../yolov8s.pt',
                       help='Path to YOLO model')
    parser.add_argument('--confidence', '-c', type=float, default=0.5,
                       help='Confidence threshold (0-1)')

    args = parser.parse_args()

    demo = ZoneDetectionDemo(
        video_path=args.video,
        model_path=args.model,
        confidence_threshold=args.confidence
    )

    demo.run()

if __name__ == '__main__':
    main()
