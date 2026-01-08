"""
YOLO Detection Demo - No GUI Version
Processes video and saves output without displaying window
"""

import cv2
from ultralytics import YOLO
import numpy as np

# Colors for different classes (BGR format)
COLORS = {
    'person': (0, 255, 0),      # Green for persons
    'car': (255, 0, 0),          # Blue for cars
    'truck': (0, 165, 255),      # Orange for trucks
    'default': (0, 255, 255)     # Yellow for others
}

def draw_detections(frame, detections):
    """Draw bounding boxes and labels on the frame"""
    for detection in detections:
        if len(detection.boxes) == 0:
            continue

        for i in range(len(detection.boxes)):
            # Get bounding box coordinates
            x1, y1, x2, y2 = detection.boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Get confidence and class
            confidence = float(detection.boxes.conf[i])
            class_id = int(detection.boxes.cls[i])
            class_name = detection.names[class_id]

            # Get color for this class
            color = COLORS.get(class_name, COLORS['default'])

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Prepare label
            label = f'{class_name}: {confidence:.2f}'

            # Calculate label size
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )

            # Draw label background
            cv2.rectangle(
                frame,
                (x1, y1 - label_height - baseline - 5),
                (x1 + label_width, y1),
                color,
                -1
            )

            # Draw label text
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

    return frame

def process_video_nogui(video_path, output_path, model_path='../yolov8s.pt', confidence_threshold=0.5):
    """Process video without GUI, save output directly"""

    print(f"Loading YOLO model from {model_path}...")
    model = YOLO(model_path)

    print(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video info: {width}x{height} @ {fps}fps, {total_frames} frames")

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    print(f"Output will be saved to: {output_path}")

    frame_count = 0
    detection_stats = {}

    print("\nProcessing video (no GUI)...")
    print("This may take a while depending on video length...\n")

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # Run detection
        results = model(frame, conf=confidence_threshold, verbose=False)

        # Count detections by class
        for result in results:
            for box in result.boxes:
                class_name = result.names[int(box.cls[0])]
                detection_stats[class_name] = detection_stats.get(class_name, 0) + 1

        # Draw detections on frame
        frame_with_detections = draw_detections(frame, results)

        # Add frame counter
        cv2.putText(
            frame_with_detections,
            f'Frame: {frame_count}/{total_frames}',
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Add detection count
        detection_count = sum(len(r.boxes) for r in results)
        cv2.putText(
            frame_with_detections,
            f'Detections: {detection_count}',
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Write frame
        writer.write(frame_with_detections)

        # Progress indicator
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")

    # Cleanup
    cap.release()
    writer.release()

    # Print statistics
    print("\n" + "="*50)
    print("Processing Complete!")
    print("="*50)
    print(f"Output saved to: {output_path}")
    print("\nDetection Statistics:")
    print("="*50)
    for class_name, count in sorted(detection_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{class_name}: {count} detections")
    print("="*50)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='YOLO Detection Demo - No GUI')
    parser.add_argument('video', help='Path to input video file')
    parser.add_argument('output', help='Path to save output video')
    parser.add_argument('--model', '-m', default='../yolov8s.pt', help='Path to YOLO model')
    parser.add_argument('--confidence', '-c', type=float, default=0.5, help='Confidence threshold (0-1)')

    args = parser.parse_args()

    process_video_nogui(
        video_path=args.video,
        output_path=args.output,
        model_path=args.model,
        confidence_threshold=args.confidence
    )

if __name__ == '__main__':
    main()
