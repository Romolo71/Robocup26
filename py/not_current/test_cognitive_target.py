import cv2
import numpy as np
from cognitive_target import CognitiveTargetDetector

def create_mock_target(colors):
    """Creates a synthetic target image with given ring colors from center to outside."""
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    img[:] = (200, 200, 200) # Light grey background
    
    center = (200, 200)
    # Radii for 5 circles (diameters 1, 2, 3, 4, 5 cm equivalent)
    # Using 30 pixels per 0.5cm ring width
    radii = [150, 120, 90, 60, 30] # Outer to inner
    colors_bgr = {
        "BLACK": (0, 0, 0),
        "RED": (0, 0, 255),
        "YELLOW": (0, 255, 255),
        "GREEN": (0, 255, 0),
        "BLUE": (255, 0, 0)
    }
    
    # Draw from outer to inner to overlap
    for i, r in enumerate(radii):
        color_name = colors[4 - i] # colors is center to outside
        cv2.circle(img, center, r, colors_bgr[color_name], -1)
        
    return img

def test_detector():
    detector = CognitiveTargetDetector(history_size=1) # No debouncing for static test
    
    test_cases = [
        {
            "colors": ["YELLOW", "YELLOW", "YELLOW", "YELLOW", "YELLOW"],
            "expected_sum": 0,
            "expected_action": "VICTIM_STOP_LED"
        },
        {
            "colors": ["GREEN", "YELLOW", "YELLOW", "YELLOW", "YELLOW"],
            "expected_sum": 1,
            "expected_action": "VICTIM_STOP_LED_1KIT"
        },
        {
            "colors": ["BLUE", "YELLOW", "YELLOW", "YELLOW", "YELLOW"],
            "expected_sum": 2,
            "expected_action": "VICTIM_STOP_LED_2KIT"
        },
        {
             "colors": ["BLACK", "BLACK", "BLACK", "BLACK", "BLACK"],
             "expected_sum": -10,
             "expected_action": "IGNORE"
        },
        {
            "colors": ["BLUE", "BLUE", "BLUE", "BLUE", "BLUE"],
            "expected_sum": 10,
            "expected_action": "IGNORE"
        }
    ]
    
    for i, case in enumerate(test_cases):
        img = create_mock_target(case["colors"])
        score, action = detector.process_frame(img)
        
        print(f"Test Case {i+1}: Input Colors {case['colors']}")
        print(f"  Expected: Sum={case['expected_sum']}, Action={case['expected_action']}")
        print(f"  Got: Score={score}, Action={action}")
        
        assert action == case["expected_action"], f"Action mismatch in case {i+1}"
        if score is not None:
             assert score == case["expected_sum"], f"Score mismatch in case {i+1}"
        print("  Status: PASSED\n")

if __name__ == "__main__":
    test_detector()
