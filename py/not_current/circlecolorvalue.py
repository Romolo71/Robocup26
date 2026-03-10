import cv2
import numpy as np
import time

# ================= CONFIG =================
PROCESS_INTERVAL = 0.2  # 5 FPS
WIDTH_PROC = 320        # risoluzione per elaborazione
HEIGHT_PROC = 240
DISPLAY_SCALE = 2       # scala video finale

COLOR_VALUES = {
    "BLACK": -2,
    "RED": -1,
    "YELLOW": 0,
    "GREEN": 1,
    "BLUE": 2
}

# ================= FUNZIONI =================

def get_pixel_color(h, s, v):
    if 0 <= v <= 50:
        return "BLACK"
    if (0 <= h <= 10 or 160 <= h <= 180) and s >= 150:
        return "RED"
    if 20 <= h <= 35 and s >= 100:
        return "YELLOW"
    if 40 <= h <= 75 and s >= 100:
        return "GREEN"
    if 90 <= h <= 130 and s >= 100:
        return "BLUE"
    return None

def analyze_target(frame_small):
    hsv = cv2.cvtColor(frame_small, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT,
        dp=1.2, minDist=50,
        param1=50, param2=25,
        minRadius=15, maxRadius=100
    )
    if circles is None:
        return None

    circles = np.uint16(np.around(circles))
    c = max(circles[0, :], key=lambda x: x[2])
    x, y, r = int(c[0]), int(c[1]), int(c[2])

    ring_results = []
    total_value = 0

    for i in range(5):
        inner_r = 0 if i == 0 else int(r * i / 5)
        outer_r = int(r * (i+1) / 5)

        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, (x, y), outer_r, 255, thickness=-1)
        if inner_r > 0:
            cv2.circle(mask, (x, y), inner_r, 0, thickness=-1)

        pixels_hsv = hsv[mask == 255]
        if len(pixels_hsv) < 10:
            ring_results.append({"ring": i+1, "color": "UNKNOWN", "value": None})
            continue

        votes = {"BLACK":0,"RED":0,"YELLOW":0,"GREEN":0,"BLUE":0}
        for h, s, v in pixels_hsv:
            col = get_pixel_color(h, s, v)
            if col:
                votes[col] += 1

        ring_color = max(votes, key=votes.get)
        ring_value = COLOR_VALUES[ring_color]
        ring_results.append({"ring": i+1, "color": ring_color, "value": ring_value})
        total_value += ring_value

    return ring_results, total_value, (x, y, r)

# ================= MAIN LOOP =================

cap = cv2.VideoCapture(0)
last_time = time.time()

print("Analisi target cognitivi avviata...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (WIDTH_PROC, HEIGHT_PROC))

    now = time.time()
    if now - last_time < PROCESS_INTERVAL:
        continue
    last_time = now

    result = analyze_target(small_frame)
    display_frame = cv2.resize(frame, (WIDTH_PROC*DISPLAY_SCALE, HEIGHT_PROC*DISPLAY_SCALE))

    if result:
        rings, total, circle_info = result
        x, y, r = circle_info
        x_disp = x * DISPLAY_SCALE
        y_disp = y * DISPLAY_SCALE
        r_disp = r * DISPLAY_SCALE

        # Disegna cerchi
        cv2.circle(display_frame, (x_disp, y_disp), r_disp, (0,255,0), 2)
        for i, ring in enumerate(rings):
            inner_r = 0 if i==0 else int(r_disp*i/5)
            outer_r = int(r_disp*(i+1)/5)
            cv2.circle(display_frame, (x_disp, y_disp), outer_r, (255,0,0), 1)
            cv2.putText(display_frame, f"{ring['color']} ({ring['value']})",
                        (x_disp - outer_r, y_disp - outer_r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

        # Stampa somma totale sopra il video
        cv2.putText(display_frame, f"Somma totale: {total}",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        # Console output chiaro
        print("\n--- Risultati Anelli ---")
        for r in rings:
            print(f"Anello {r['ring']}: Colore={r['color']}, Valore={r['value']}")
        print(f"Somma totale valori: {total}")

    cv2.imshow("Target Cognitivi RCJ 2026", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
