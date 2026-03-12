import cv2
import numpy as np
from enhanced_cognitive_target import EnhancedCognitiveTarget

def create_mock_target(colors, target_size=(640, 480), noise_level=0, light_level=1.0):
    """Creates a synthetic target image with given ring colors from outside to inside."""
    img = np.zeros((*target_size, 3), dtype=np.uint8)
    img[:] = (200, 200, 200) # Light grey background
    
    center = (target_size[0] // 2, target_size[1] // 2)
    radii = [180, 140, 100, 60, 20] # Outer to inner
    colors_bgr = {
        "ROSSO": (0, 0, 255),
        "NERO": (0, 0, 0),
        "VERDE": (0, 255, 0),
        "AZZURRO": (255, 255, 0),
        "GIALLO": (0, 255, 255)
    }
    
    # Draw from OUTER to INNER so smaller circles overlap larger ones
    # colors list should be CENTER TO OUTSIDE to match detector expectation
    for i, r in enumerate(radii):
        color_name = colors[4 - i] # 4 is outer, 0 is inner
        cv2.circle(img, center, r, colors_bgr[color_name], -1)
        
    # Scale light level (simulate low light)
    img = (img * light_level).astype(np.uint8)
    
    # Add salt and pepper noise
    if noise_level > 0:
        noise = np.random.randint(0, 256, (*target_size, 3), dtype=np.uint8)
        mask = np.random.rand(*target_size) < noise_level
        img[mask] = noise[mask]
        
    return img

def test_detector():
    detector = EnhancedCognitiveTarget(history_size=1)
    
    test_cases = [
        {
            "name": "Standard Light",
            "colors": ["GIALLO", "GIALLO", "GIALLO", "GIALLO", "GIALLO"],
            "light": 1.0,
            "noise": 0.0,
            "expected_action": "VICTIM_STOP_LED"
        },
        {
            "name": "Low Light (20%)",
            "colors": ["VERDE", "GIALLO", "GIALLO", "GIALLO", "GIALLO"],
            "light": 0.2, # Very dark
            "noise": 0.0,
            "expected_action": "VICTIM_STOP_LED_1KIT"
        },
        {
            "name": "Noisy (5% noise)",
            "colors": ["AZZURRO", "GIALLO", "GIALLO", "GIALLO", "GIALLO"],
            "light": 1.0,
            "noise": 0.05, # 5% pixels are noisy
            "expected_action": "VICTIM_STOP_LED_2KIT"
        },
        {
            "name": "Black Target",
            "colors": ["NERO", "NERO", "NERO", "NERO", "NERO"],
            "light": 1.0,
            "noise": 0.0,
            "expected_action": "IGNORE"
        },
        {
            "name": "Red Target",
            "colors": ["ROSSO", "ROSSO", "ROSSO", "ROSSO", "ROSSO"],
            "light": 1.0,
            "noise": 0.0,
            "expected_action": "IGNORE"
        }
    ]
    
    passed = 0
    for i, case in enumerate(test_cases):
        img = create_mock_target(case["colors"], light_level=case["light"], noise_level=case["noise"])
        
        start_time = time.time()
        score, action = detector.process_frame(img)
        duration = time.time() - start_time
        
        print(f"Test case '{case['name']}':")
        print(f"  Colors: {case['colors']}")
        print(f"  Got score: {score}, action: {action} (Time: {duration:.4f}s)")
        
        if action == case["expected_action"]:
            print("  Status: PASSED")
            passed += 1
        else:
            print(f"  Status: FAILED (Expected {case['expected_action']})")
            # Save failed case for inspection
            cv2.imwrite(f"/tmp/failed_test_{i}.png", img)
            
    print(f"\nResult: {passed}/{len(test_cases)} PASSED")
    assert passed == len(test_cases), "Some tests failed!"

if __name__ == "__main__":
    import time
    test_detector()
