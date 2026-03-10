import cv2
import numpy as np
import time
from collections import deque

class EnhancedCognitiveTarget:
    def __init__(self, history_size=5):
        # BGR target colors for distance comparison (simplified)
        self.target_colors = {
            "ROSSO": (0, 0, 255),
            "NERO": (0, 0, 0),
            "VERDE": (0, 255, 0),
            "AZZURRO": (255, 255, 0),
            "GIALLO": (0, 255, 255)
        }
        
        # Scoring Map (legacy compatible if needed)
        self.score_map = {
            "ROSSO": -1,
            "NERO": -2,
            "VERDE": 1,
            "AZZURRO": 2,
            "GIALLO": 0,
            "UNKNOWN": 0
        }
        
        self.history = deque(maxlen=history_size)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def preprocess(self, frame):
        """Enhances contrast for low-light conditions."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = self.clahe.apply(gray)
        return enhanced

    def get_robust_color(self, frame, ellipse, scale):
        """Samples 5 points, discards 2 outliers, returns average color name."""
        (xc, yc), (ma, Mi), angle = ellipse
        # Scale the ellipse to sample within a specific ring
        # For simplicity, we sample at 5 points around the scaled ellipse
        points = []
        angles = [0, 72, 144, 216, 288] # 5 points distributed
        
        h, w = frame.shape[:2]
        
        for a in angles:
            rad = np.deg2rad(a + angle)
            # Sample at 80% of the radius to stay inside the ring/circle
            px = int(xc + (ma/2 * scale * 0.8) * np.cos(rad))
            py = int(yc + (Mi/2 * scale * 0.8) * np.sin(rad))
            
            if 0 <= px < w and 0 <= py < h:
                points.append(frame[py, px].astype(np.float32))
        
        if len(points) < 5:
            return "UNKNOWN"

        # Find 2 outliers
        # Calculate mean of all 5
        while len(points) > 3:
            mean_color = np.mean(points, axis=0)
            # Find the point furthest from the mean
            distances = [np.linalg.norm(p - mean_color) for p in points]
            outlier_idx = np.argmax(distances)
            points.pop(outlier_idx)
            
        # Final average of 3
        avg_bgr = np.mean(points, axis=0)
        
        return self.map_to_color_name(avg_bgr)

    def map_to_color_name(self, bgr):
        """Maps BGR value to one of the 5 predefined colors."""
        hsv_frame = np.uint8([[bgr]])
        hsv = cv2.cvtColor(hsv_frame, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = hsv
        
        # Black if value is very low
        if v < 30: # more aggressive black detection
            res = "NERO"
        # If very low saturation, it's either black or gray
        elif s < 30:
            res = "NERO"
        # Refined Hue ranges
        elif h < 10 or h > 165:
            res = "ROSSO"
        elif 15 <= h < 40:
            res = "GIALLO"
        elif 40 <= h < 90:
            res = "VERDE"
        elif 95 <= h < 140:
            res = "AZZURRO"
        else:
            res = "UNKNOWN"
            
        return res

    def process_frame(self, frame):
        if frame is None:
            return None, "NO_FRAME"
            
        enhanced = self.preprocess(frame)
        
        # Combine Adaptive Threshold and Canny for maximum robustness
        # Synthetic images often work better with simple thresholding
        _, thresh = cv2.threshold(enhanced, 50, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        edges = cv2.Canny(enhanced, 30, 100)
        combined = cv2.bitwise_or(thresh, edges)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_ellipse = None
        max_area = 0
        
        for cnt in contours:
            if len(cnt) < 5: continue
            area = cv2.contourArea(cnt)
            if area < 300: continue
            
            ellipse = cv2.fitEllipse(cnt)
            (xc, yc), (ma, Mi), angle = ellipse
            
            ratio = ma / Mi if Mi != 0 else 0
            if 0.5 < ratio < 2.0:
                if area > max_area:
                    max_area = area
                    best_ellipse = ellipse
        
        if best_ellipse:
            cv2.ellipse(frame, best_ellipse, (0, 255, 0), 2)
            
            # Scales to sample inside the rings
            # If radii are roughly [180, 140, 100, 60, 20]
            # Center-to-outside: 20, 60, 100, 140, 180
            # Normalized: 0.11, 0.33, 0.55, 0.77, 1.0 (approx)
            scales = [0.1, 0.3, 0.5, 0.7, 0.9] # From inside to outside
            ring_colors = []
            for s in scales:
                color = self.get_robust_color(frame, best_ellipse, s)
                ring_colors.append(color)
            
            # Action Mapping based on ring colors
            score = sum(self.score_map.get(c, 0) for c in ring_colors if c != "UNKNOWN")
            
            action = "IGNORE"
            # If at least 3 rings are detected (not UNKNOWN)
            if ring_colors.count("UNKNOWN") <= 2:
                if score == 0: action = "VICTIM_STOP_LED"
                elif score == 1: action = "VICTIM_STOP_LED_1KIT"
                elif score == 2: action = "VICTIM_STOP_LED_2KIT"

            # Debouncing
            self.history.append(action)
            debounced_action = max(set(self.history), key=list(self.history).count)
            
            # HUD text
            cv2.putText(frame, f"Colors: {ring_colors}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(frame, f"Action: {debounced_action}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            return score if debounced_action != "IGNORE" else None, debounced_action

        return None, "IGNORE"

if __name__ == "__main__":
    # Test loop with camera
    cap = cv2.VideoCapture(0)
    detector = EnhancedCognitiveTarget()
    while True:
        ret, frame = cap.read()
        if not ret: break
        score, action = detector.process_frame(frame)
        cv2.imshow("Enhanced Cognitive Target", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()
