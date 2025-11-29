"""
COMPLETE Zone-Based Detection Demo
Fully functional demonstration of zone drawing + detection + intrusion alerts
"""

import cv2
from ultralytics import YOLO
import numpy as np
import json
import os
from datetime import datetime

# Color scheme (BGR format)
COLORS = {
    'person_box': (0, 255, 0),       # Green for person boxes
    'zone_normal': (255, 255, 0),    # Cyan for normal zones
    'zone_alert': (0, 0, 255),       # Red for alert zones
    'drawing_point': (0, 0, 255),    # Red dots for drawing
    'drawing_line': (255, 255, 0),   # Cyan lines for drawing
    'alert_bg': (0, 0, 200),         # Dark red for alert banner
    'panel_bg': (40, 40, 40),        # Dark gray for panels
    'text_white': (255, 255, 255),
    'text_black': (0, 0, 0)
}

class CompleteZoneDemo:
    def __init__(self, video_path, model_path='../yolov8s.pt', confidence=0.3):
        self.video_path = video_path
        self.confidence = confidence

        # Zone management
        self.zones = []
        self.current_zone = []
        self.drawing_mode = False

        # Detection state
        self.intrusions = {}  # {zone_idx: [detections]}
        self.alert_active = False

        # Mouse state
        self.mouse_x = 0
        self.mouse_y = 0

        # Video state
        self.paused = False
        self.frame_count = 0

        # Statistics
        self.total_intrusions = 0
        self.detection_history = []

        # Load model
        print("═" * 70)
        print("  ZONE-BASED DETECTION DEMO - COMPLETE VERSION")
        print("═" * 70)
        print(f"\n[1/3] Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        print("✓ Model loaded successfully")

        # Open video
        print(f"\n[2/3] Opening video: {video_path}")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Error: Could not open video {video_path}")

        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"✓ Video loaded: {self.width}x{self.height} @ {self.fps}fps")
        print(f"  Total frames: {self.total_frames}")

        # Try to load saved zones
        print(f"\n[3/3] Checking for saved zones...")
        self.load_zones()

        print("\n" + "═" * 70)
        print("  READY TO START!")
        print("═" * 70)
        print("\nKEYBOARD CONTROLS:")
        print("  D      - Start/Stop drawing zone")
        print("  C      - Complete current zone (min 3 points)")
        print("  U      - Undo last zone")
        print("  R      - Reset all zones")
        print("  S      - Save zones to file")
        print("  SPACE  - Pause/Resume video")
        print("  Q      - Quit demo")
        print("\n" + "═" * 70 + "\n")

    def save_zones(self):
        """Save zones to JSON file"""
        zones_file = 'zones_config.json'
        with open(zones_file, 'w') as f:
            json.dump(self.zones, f, indent=2)
        print(f"\n✓ Zones saved to {zones_file}")
        return zones_file

    def load_zones(self):
        """Load zones from JSON file if exists"""
        zones_file = 'zones_config.json'
        if os.path.exists(zones_file):
            with open(zones_file, 'r') as f:
                self.zones = json.load(f)
            print(f"✓ Loaded {len(self.zones)} saved zones from {zones_file}")
        else:
            print("✗ No saved zones found (will create new)")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for zone drawing"""
        self.mouse_x = x
        self.mouse_y = y

        if event == cv2.EVENT_LBUTTONDOWN and self.drawing_mode:
            self.current_zone.append([x, y])
            print(f"  Point {len(self.current_zone)}: ({x}, {y})")

    def point_in_polygon(self, point, polygon):
        """Check if point is inside polygon using ray casting"""
        if len(polygon) < 3:
            return False

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
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    def check_intrusions(self, detections):
        """Check for detections inside zones"""
        self.intrusions = {}

        if len(self.zones) == 0:
            return

        for detection in detections:
            if len(detection.boxes) == 0:
                continue

            for i in range(len(detection.boxes)):
                # Get bounding box
                bbox = detection.boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, bbox)
                center = self.get_bbox_center([x1, y1, x2, y2])

                # Get detection info
                conf = float(detection.boxes.conf[i])
                cls_id = int(detection.boxes.cls[i])
                cls_name = detection.names[cls_id]

                # Check each zone
                for zone_idx, zone in enumerate(self.zones):
                    if self.point_in_polygon(center, zone):
                        if zone_idx not in self.intrusions:
                            self.intrusions[zone_idx] = []

                        self.intrusions[zone_idx].append({
                            'bbox': [x1, y1, x2, y2],
                            'center': center,
                            'class': cls_name,
                            'confidence': conf
                        })

        # Update alert state
        self.alert_active = len(self.intrusions) > 0
        if self.alert_active:
            self.total_intrusions += 1

    def draw_detections(self, frame, detections):
        """Draw bounding boxes for all detections"""
        for detection in detections:
            if len(detection.boxes) == 0:
                continue

            for i in range(len(detection.boxes)):
                # Get bbox
                bbox = detection.boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, bbox)

                # Get info
                conf = float(detection.boxes.conf[i])
                cls_id = int(detection.boxes.cls[i])
                cls_name = detection.names[cls_id]

                # Draw box (thinner)
                cv2.rectangle(frame, (x1, y1), (x2, y2),
                            COLORS['person_box'], 2)

                # Draw center point (smaller)
                center = self.get_bbox_center([x1, y1, x2, y2])
                cv2.circle(frame, center, 4, COLORS['person_box'], -1)

                # Draw label (smaller)
                label = f'{cls_name} {conf:.2f}'
                (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

                cv2.rectangle(frame, (x1, y1 - lh - 8),
                            (x1 + lw + 8, y1),
                            COLORS['person_box'], -1)
                cv2.putText(frame, label, (x1 + 4, y1 - 4),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                           COLORS['text_black'], 1)

        return frame

    def draw_zones(self, frame):
        """Draw all zones with alert highlighting"""
        if len(self.zones) == 0:
            return frame

        overlay = frame.copy()

        for zone_idx, zone in enumerate(self.zones):
            if len(zone) < 3:
                continue

            pts = np.array(zone, np.int32).reshape((-1, 1, 2))

            # Determine color based on intrusion
            if zone_idx in self.intrusions and len(self.intrusions[zone_idx]) > 0:
                color = COLORS['zone_alert']
                alpha = 0.5
            else:
                color = COLORS['zone_normal']
                alpha = 0.3

            # Draw filled polygon
            cv2.fillPoly(overlay, [pts], color)

            # Draw outline (thinner)
            cv2.polylines(frame, [pts], True, color, 2)

            # Draw zone label
            label = f'ZONE {zone_idx + 1}'
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            label_pos = (zone[0][0], zone[0][1] - 15)

            cv2.rectangle(frame,
                         (label_pos[0] - 5, label_pos[1] - lh - 5),
                         (label_pos[0] + lw + 5, label_pos[1] + 5),
                         color, -1)
            cv2.putText(frame, label, label_pos,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                       COLORS['text_black'], 2)

        # Blend overlay
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        return frame

    def draw_current_zone(self, frame):
        """Draw zone being created"""
        if len(self.current_zone) == 0:
            return frame

        # Draw all points
        for point in self.current_zone:
            cv2.circle(frame, tuple(point), 6,
                      COLORS['drawing_point'], -1)
            cv2.circle(frame, tuple(point), 8,
                      COLORS['text_white'], 2)

        # Draw lines between points
        if len(self.current_zone) > 1:
            pts = np.array(self.current_zone, np.int32)
            cv2.polylines(frame, [pts], False,
                         COLORS['drawing_line'], 2)

        # Draw line to cursor
        if len(self.current_zone) > 0:
            cv2.line(frame, tuple(self.current_zone[-1]),
                    (self.mouse_x, self.mouse_y),
                    COLORS['drawing_line'], 1)
            cv2.circle(frame, (self.mouse_x, self.mouse_y), 5,
                      COLORS['drawing_line'], 1)

        return frame

    def draw_alert_banner(self, frame):
        """Draw prominent alert banner when intrusion detected"""
        if not self.alert_active:
            return frame

        banner_height = 100

        # Draw alert background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, banner_height),
                     COLORS['alert_bg'], -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Draw border
        cv2.rectangle(frame, (0, 0), (self.width, banner_height),
                     COLORS['zone_alert'], 5)

        # Draw main alert text
        alert_text = "⚠️  INTRUSION DETECTED  ⚠️"
        (tw, th), _ = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
        text_x = (self.width - tw) // 2
        cv2.putText(frame, alert_text, (text_x, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                   COLORS['text_white'], 3)

        # Draw details
        details = []
        for zone_idx, dets in self.intrusions.items():
            classes = [d['class'] for d in dets]
            details.append(f"Zone {zone_idx + 1}: {len(dets)} {classes[0]}(s)")

        details_text = " | ".join(details)
        (tw, th), _ = cv2.getTextSize(details_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        text_x = (self.width - tw) // 2
        cv2.putText(frame, details_text, (text_x, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                   COLORS['text_white'], 2)

        return frame

    def draw_info_panel(self, frame):
        """Draw compact info panel on the left"""
        panel_width = 200
        panel_height = 130
        margin = 10

        # Draw panel background
        overlay = frame.copy()
        cv2.rectangle(overlay, (margin, self.height - panel_height - margin),
                     (panel_width + margin, self.height - margin),
                     COLORS['panel_bg'], -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Draw panel border
        cv2.rectangle(frame, (margin, self.height - panel_height - margin),
                     (panel_width + margin, self.height - margin),
                     COLORS['text_white'], 1)

        # Draw info text
        y_offset = self.height - panel_height - margin + 22
        line_height = 22

        info_lines = [
            f"Frame: {self.frame_count}/{self.total_frames}",
            f"Zones: {len(self.zones)}",
            f"Mode: {'DRAWING' if self.drawing_mode else 'MONITOR'}",
            f"Status: {'ALERT!' if self.alert_active else 'Normal'}",
            f"Intrusions: {self.total_intrusions}",
        ]

        for line in info_lines:
            color = COLORS['zone_alert'] if 'ALERT' in line else COLORS['text_white']
            cv2.putText(frame, line, (margin + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            y_offset += line_height

        return frame

    def draw_controls_panel(self, frame):
        """Draw compact controls panel on the right"""
        panel_width = 160
        panel_height = 180
        margin = 10

        # Draw panel background
        overlay = frame.copy()
        cv2.rectangle(overlay,
                     (self.width - panel_width - margin, margin),
                     (self.width - margin, panel_height + margin),
                     COLORS['panel_bg'], -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Draw panel border
        cv2.rectangle(frame,
                     (self.width - panel_width - margin, margin),
                     (self.width - margin, panel_height + margin),
                     COLORS['text_white'], 1)

        # Draw controls text
        y_offset = margin + 20
        line_height = 22

        controls = [
            "CONTROLS:",
            "D - Draw",
            "C - Complete",
            "U - Undo",
            "R - Reset",
            "S - Save",
            "SPACE - Pause",
            "Q - Quit",
        ]

        for i, line in enumerate(controls):
            if i == 0:
                color = COLORS['text_white']
                weight = 1
                size = 0.5
            else:
                color = COLORS['text_white']
                weight = 1
                size = 0.42

            cv2.putText(frame, line,
                       (self.width - panel_width - margin + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, size, color, weight)
            y_offset += line_height

        return frame

    def draw_drawing_indicator(self, frame):
        """Draw compact drawing mode indicator"""
        if not self.drawing_mode:
            return frame

        # Draw at bottom center
        text = f"DRAWING MODE - Click to add points ({len(self.current_zone)})"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        x = (self.width - tw) // 2
        y = self.height - 20

        # Background
        overlay = frame.copy()
        cv2.rectangle(overlay, (x - 8, y - th - 8),
                     (x + tw + 8, y + 8),
                     COLORS['drawing_line'], -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Text
        cv2.putText(frame, text, (x, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                   COLORS['text_black'], 1)

        return frame

    def run(self):
        """Run the complete demo"""
        window_name = 'Zone-Based Detection Demo - COMPLETE'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        cv2.setMouseCallback(window_name, self.mouse_callback)

        print("Starting demo... Press Q to quit\n")

        while True:
            if not self.paused:
                ret, frame = self.cap.read()

                if not ret:
                    # Loop video
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.frame_count = 0
                    continue

                self.frame_count += 1

                # Run detection
                results = self.model(frame, conf=self.confidence, verbose=False)

                # Check for intrusions
                self.check_intrusions(results)

                # Draw everything in order
                frame = self.draw_zones(frame)
                frame = self.draw_detections(frame, results)
                frame = self.draw_current_zone(frame)
                frame = self.draw_alert_banner(frame)
                frame = self.draw_info_panel(frame)
                frame = self.draw_controls_panel(frame)
                frame = self.draw_drawing_indicator(frame)

            # Display
            cv2.imshow(window_name, frame)

            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\nQuitting demo...")
                break
            elif key == ord(' '):
                self.paused = not self.paused
                print(f"\n{'Paused' if self.paused else 'Resumed'}")
            elif key == ord('d'):
                self.drawing_mode = not self.drawing_mode
                if self.drawing_mode:
                    print(f"\n✓ Drawing mode ON - Click to add points")
                else:
                    print(f"\n✗ Drawing mode OFF")
            elif key == ord('c'):
                if len(self.current_zone) >= 3:
                    self.zones.append(self.current_zone)
                    print(f"\n✓ Zone {len(self.zones)} completed with {len(self.current_zone)} points")
                    self.current_zone = []
                    self.drawing_mode = False
                else:
                    print(f"\n✗ Need at least 3 points (currently {len(self.current_zone)})")
            elif key == ord('u'):
                if len(self.zones) > 0:
                    self.zones.pop()
                    print(f"\n✓ Removed zone (now {len(self.zones)} zones)")
                else:
                    print(f"\n✗ No zones to remove")
            elif key == ord('r'):
                self.zones = []
                self.current_zone = []
                self.drawing_mode = False
                print(f"\n✓ All zones reset")
            elif key == ord('s'):
                filename = self.save_zones()
                print(f"  Total zones saved: {len(self.zones)}")

        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()

        print("\n" + "═" * 70)
        print("  DEMO COMPLETED")
        print("═" * 70)
        print(f"  Total frames processed: {self.frame_count}")
        print(f"  Total zones created: {len(self.zones)}")
        print(f"  Total intrusions detected: {self.total_intrusions}")
        print("═" * 70 + "\n")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Complete Zone-Based Detection Demo'
    )
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--model', '-m', default='../yolov8s.pt',
                       help='YOLO model path')
    parser.add_argument('--confidence', '-c', type=float, default=0.5,
                       help='Detection confidence (0-1)')

    args = parser.parse_args()

    demo = CompleteZoneDemo(
        video_path=args.video,
        model_path=args.model,
        confidence=args.confidence
    )

    demo.run()

if __name__ == '__main__':
    main()
