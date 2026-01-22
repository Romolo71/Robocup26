import cv2
import numpy as np
import pytesseract

# Configurazione Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- COLOR PICKER ---
def get_detected_color(frame):
    """
    Analizza il frame e restituisce il colore rilevato come stringa.
    """
    frame_resized = cv2.resize(frame, (320, 240))
    hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    color_ranges = {
        "ROSSO": [((0, 50, 50), (10, 255, 255)), ((160, 50, 50), (180, 255, 255))],
        "GIALLO": [((20, 100, 100), (40, 255, 255))],
        "VERDE": [((40, 50, 50), (90, 255, 255))],
        "NERO": [((0, 0, 0), (180, 255, 50))],
        "BIANCO": [((0, 0, 180), (180, 40, 220))],
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

        ratio = np.sum(mask_total > 0) / (frame_resized.shape[0] * frame_resized.shape[1])

        if ratio > 0.05:
            if color == "SILVER / RIFLETTENTE":
                V_pixels = V[mask_total > 0]
                if len(V_pixels) > 0:
                    varianza = np.std(V_pixels)
                    if varianza < 10: continue
            if ratio > max_ratio:
                max_ratio = ratio
                detected_color = color

    return detected_color


# --- LETTER IDENTIFIER ---
def get_detected_letter(roi):
    """
    Riceve un'area di interesse (ROI) e restituisce la lettera H, S o U.
    Se non rileva nulla, restituisce una stringa vuota.
    """
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    config = '--psm 10 -c tessedit_char_whitelist=HSU'
    text = pytesseract.image_to_string(thresh, config=config).strip().upper()

    if text in ['H', 'S', 'U']:
        return text
    return ""


# --- Ciclo principale ---
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)

    # Variabili per il movimento del rettangolo
    size = 200
    x_rect = 0
    direzione = 1
    velocita = 7

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w, _ = frame.shape

        # 1. Calcolo movimento rettangolo per la lettera
        x_rect += direzione * velocita
        if x_rect + size >= w or x_rect <= 0: direzione *= -1
        roi_lettera = frame[100:100 + size, x_rect:x_rect + size]

        # 2. Chiamata alle due funzioni che restituiscono stringhe
        colore = get_detected_color(frame)
        lettera = get_detected_letter(roi_lettera)

        # 3. Visualizzazione risultati
        cv2.rectangle(frame, (x_rect, 100), (x_rect + size, 100 + size), (127, 0, 255), 2)

        info_testo = f"Colore: {colore} | Lettera: {lettera if lettera else '...'}"
        cv2.putText(frame, info_testo, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Unione Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()