import cv2
import numpy as np

def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    color_ranges = {
        "ROSSO": [((0, 50, 50), (10, 255, 255)), ((160, 50, 50), (180, 255, 255))],
        "GIALLO": [((20, 100, 100), (40, 255, 255))],
        "VERDE": [((40, 50, 50), (90, 255, 255))],
        "NERO": [((100, 50, 50), (130, 255, 255))],
        "NERO": [((0, 0, 0), (180, 255, 50))],
        # Bianco opaco
        "BIANCO": [((0, 0, 180), (180, 40, 220))],
        #
        "SILVER / RIFLETTENTE": [((0, 0, 100), (180, 30, 200))]
    }

    max_ratio = 0
    detected_color = "BIANCO"

    for color, ranges in color_ranges.items():
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.inRange(hsv, lower, upper)
            mask_total = cv2.bitwise_or(mask_total, mask)

        ratio = np.sum(mask_total > 0) / (frame.shape[0] * frame.shape[1])

        if ratio > 0.05:
            # Controllo extra per silver: varianza del canale V alta → riflettente
            if color == "SILVER / RIFLETTENTE":
                V_pixels = V[mask_total > 0]
                if len(V_pixels) > 0:
                    varianza = np.std(V_pixels)
                    if varianza < 10:  # troppo uniforme → non è silver
                        continue
            if ratio > max_ratio:
                max_ratio = ratio
                detected_color = color

    return detected_color

vid = cv2.VideoCapture(0)

while True:
    ret, frame = vid.read()
    if not ret:
        break

    frame = cv2.resize(frame, (320, 240))
    color_detected = detect_color(frame)

    print(color_detected)
    cv2.imshow("frame", frame)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

vid.release()
cv2.destroyAllWindows()