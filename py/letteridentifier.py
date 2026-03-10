
import cv2
import pytesseract
import os
import platform
from collections import deque, Counter

# Configurazione Tesseract
script_dir = os.path.dirname(os.path.abspath(__file__))
tessdata_dir = os.path.join(script_dir, 'tessdata')

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'



cap = cv2.VideoCapture(1)
size = 200
velocita = 12 
step_y = 100 
pause_frames = 0 

# Variabili di stato inizializzate al primo frame
x = None
y = None
direzione = 1 

# Buffer per stabilizzazione temporale
detection_buffer = deque(maxlen=20)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    h, w, _ = frame.shape
    
    # Definisci la zona centrale (es. 60% centrale dello schermo)
    margin_w = int(w * 0.2)
    margin_h = int(h * 0.2)
    scan_x_min, scan_x_max = margin_w, w - margin_w - size
    scan_y_min, scan_y_max = margin_h, h - margin_h - size
    
    # Inizializzazione posizione al primo frame nella zona corretta
    if x is None or y is None:
        x = scan_x_min
        y = scan_y_min

    # Aggiornamento posizione solo se non siamo in pausa
    if pause_frames > 0:
        pause_frames -= 1
    else:
        # Aggiornamento posizione X
        x += direzione * velocita
        
        # Controllo bordi della ZONA CENTRALE e aggiornamento Y
        if x >= scan_x_max or x <= scan_x_min:
            direzione *= -1
            y += step_y
            
            # Se superiamo l'altezza massima della zona centrale, ricomincia dall'alto della zona
            if y > scan_y_max:
                y = scan_y_min
    
    # Clipping x e y nei confini della zona centrale per sicurezza
    x = max(scan_x_min, min(x, scan_x_max))
    y = max(scan_y_min, min(y, scan_y_max))
    
    roi = frame[y:y + size, x:x + size]

    # Pre-processing robusto
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray_resized = cv2.resize(gray, (size*3, size*3), interpolation=cv2.INTER_CUBIC)
    
    # Bilateral Filter
    gray_filtered = cv2.bilateralFilter(gray_resized, 9, 75, 75)
    
    # Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(gray_filtered, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 25, 10)

    # Pulizia morfologica
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Configurazione Tesseract
    config = f'--tessdata-dir "{tessdata_dir}" -l grc --psm 8 -c tessedit_char_whitelist=ΩΦΨ'
    
    detected_char = None
    try:
        data = pytesseract.image_to_data(thresh, config=config, output_type=pytesseract.Output.DICT)
        for i, text in enumerate(data['text']):
            conf = int(data['conf'][i])
            if text.strip() and conf > 5: 
                detected_char = text.strip()
                pause_frames = 10 
                break
    except Exception as e:
        pass

    detection_buffer.append(detected_char)
    valid_detections = [c for c in detection_buffer if c is not None]
    
    greek_map = {'Ω': 'Omega', 'Φ': 'Phi', 'Ψ': 'Psi'}

    # Disegna l'AREA DI SCANSIONE (cornice grigia)
    cv2.rectangle(frame, (scan_x_min, scan_y_min), (scan_x_max + size, scan_y_max + size), (100, 100, 100), 1)
    cv2.putText(frame, "Area di Scansione", (scan_x_min, scan_y_min - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

    # Stato scansione
    status = "SCANNING" if pause_frames == 0 else "LOCKING..."
    cv2.putText(frame, f"Mode: {status}", (w-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    if valid_detections:
        counts = Counter(valid_detections)
        most_common, count = counts.most_common(1)[0]
        
        if most_common in greek_map and count >= 5:
            pause_frames = 5
            display_text = greek_map[most_common]
            cv2.putText(frame, f"Greca: {display_text}", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(f"Lettera stabile rilevata: {display_text} ({count} validi in buffer)")

    # Disegna il rettangolo di scansione
    color = (0, 255, 0) if pause_frames > 0 else (127, 0, 255)
    cv2.rectangle(frame, (x, y), (x + size, y + size), color, 2)
    
    cv2.imshow("Webcam Scanner", frame)
    cv2.imshow("Debug Thresh (OCR Input)", thresh)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
