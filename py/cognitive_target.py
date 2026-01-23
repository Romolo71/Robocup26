import cv2
import numpy as np
import threading
import time
from collections import deque

class VideoStream:
    """Class to handle multithreaded video capture on RPi5."""
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

class CognitiveTargetDetector:
    def __init__(self, history_size=5):
        # HSV Color Ranges (Lower, Upper)
        self.color_ranges = {
            "BLACK":  ((0, 0, 0), (180, 255, 60)),
            "RED":    [((0, 100, 100), (10, 255, 255)), ((160, 100, 100), (180, 255, 255))],
            "YELLOW": ((20, 100, 100), (35, 255, 255)),
            "GREEN":  ((40, 50, 50), (90, 255, 255)),
            "BLUE":   ((100, 100, 50), (130, 255, 255))
        }
        
        # Scoring Map
        self.score_map = {
            "BLACK": -2,
            "RED": -1,
            "YELLOW": 0,
            "GREEN": 1,
            "BLUE": 2,
            "UNKNOWN": 0
        }
        
        # Debouncing history
        self.history = deque(maxlen=history_size)

    def identify_color(self, hsv_pixel):
        """Identifies color of a single pixel in HSV space."""
        h, s, v = hsv_pixel
        
        # Check colors
        for color_name, ranges in self.color_ranges.items():
            if isinstance(ranges, list): # Multi-range (like Red)
                for (lower, upper) in ranges:
                    if all(lower[i] <= hsv_pixel[i] <= upper[i] for i in range(3)):
                        return color_name
            else:
                lower, upper = ranges
                if all(lower[i] <= hsv_pixel[i] <= upper[i] for i in range(3)):
                    return color_name
        return "UNKNOWN"

    def get_ring_colors(self, frame, circle):
        """Samples colors from 5 concentric rings."""
        x, y, r = circle
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 5 rings of 0.5cm each, total diameter 5cm (r=2.5cm)
        # We sample at middle of each ring: 0.25cm, 0.75cm, 1.25cm, 1.75cm, 2.25cm
        # Relative to total radius R: 0.1R, 0.3R, 0.5R, 0.7R, 0.9R
        sample_radii = [r * 0.1, r * 0.3, r * 0.5, r * 0.7, r * 0.9]
        
        detected_colors = []
        for radius in sample_radii:
            # Sample 4 points around the ring to be robust
            offsets = [(0, radius), (0, -radius), (radius, 0), (-radius, 0)]
            ring_samples = []
            for ox, oy in offsets:
                sx, sy = int(x + ox), int(y + oy)
                if 0 <= sx < hsv.shape[1] and 0 <= sy < hsv.shape[0]:
                    ring_samples.append(self.identify_color(hsv[sy, sx]))
            
            # Majority vote for the ring
            if ring_samples:
                most_common = max(set(ring_samples), key=ring_samples.count)
                detected_colors.append(most_common)
            else:
                detected_colors.append("UNKNOWN")
        
        return detected_colors

    def calculate_score_and_action(self, ring_colors):
        """Calculates sum and maps to action."""
        if "UNKNOWN" in ring_colors:
            return None, "IGNORE"
            
        total_sum = sum(self.score_map[c] for c in ring_colors)
        
        action = "IGNORE"
        if total_sum == 0:
            action = "VICTIM_STOP_LED"
        elif total_sum == 1:
            action = "VICTIM_STOP_LED_1KIT"
        elif total_sum == 2:
            action = "VICTIM_STOP_LED_2KIT"
            
        return total_sum, action

    def process_frame(self, frame):
        """Main processing function."""
        if frame is None:
            return None, "NO_FRAME"
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Hough Circles Detection
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
            param1=50, param2=30, minRadius=20, maxRadius=150
        )
        
        current_result = (None, "IGNORE")
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Assume the largest detection is our target if multiple found
            target_circle = max(circles, key=lambda c: c[2])
            
            ring_colors = self.get_ring_colors(frame, target_circle)
            score, action = self.calculate_score_and_action(ring_colors)
            current_result = (score, action)
            
            # Draw for debugging/visualization
            cv2.circle(frame, (target_circle[0], target_circle[1]), target_circle[2], (0, 255, 0), 2)
            for i, c in enumerate(ring_colors):
                cv2.putText(frame, f"R{i+1}: {c}", (10, 30 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Score: {score} Action: {action}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Debouncing: return the most frequent action in history
        self.history.append(current_result[1])
        debounced_action = max(set(self.history), key=list(self.history).count)
        
        # If the debounced action matches current, return current score, else None
        final_score = current_result[0] if current_result[1] == debounced_action else None
        
        return final_score, debounced_action

def main():
    """Main loop for testing on RPi5."""
    vs = VideoStream(src=0).start()
    detector = CognitiveTargetDetector()
    
    print("Starting Cognitive Target Detection... Press 'q' to quit.")
    
    try:
        while True:
            frame = vs.read()
            if frame is None:
                continue
                
            score, action = detector.process_frame(frame)
            
            # Here you would call your robot control functions based on action
            # e.g., if action == "VICTIM_STOP_LED_1KIT": robot.deploy_kit(1)
            
            cv2.imshow("Cognitive Target Detector", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        vs.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
