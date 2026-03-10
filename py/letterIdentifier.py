
import cv2
import pytesseract
import os
import platform
import threading
import time
from collections import deque, Counter

# Configurazione Tesseract
script_dir = os.path.dirname(os.path.abspath(__file__))
tessdata_dir = os.path.join(script_dir, 'tessdata')

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

class VideoStream:
    """Classe per gestire l'acquisizione video multithread per aumentare gli FPS."""
    def __init__(self, src=1):
        self.stream = cv2.VideoCapture(src)
        # self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            ret, frame = self.stream.read()
            if not ret:
                self.stopped = True
                continue
            self.frame = frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# Inizializzazione stream
vs = VideoStream(src=1).start()
time.sleep(1.0) # Tempo di riscaldamento camera

size = 100
velocita = 12 
step_y = int(size/4) 
pause_frames = 0 

# Variabili di stato
x = None
y = None
direzione = 1 

# Buffer per stabilizzazione temporale
detection_buffer = deque(maxlen=20)

# Variabili per calcolo FPS e ottimizzazione loop
fps_count = 0
fps_start_time = time.time()
fps_display = 0
frame_count = 0
OCR_SKIP_FRAMES = 3 # Esegue OCR ogni 3 frame per fluidità

print("SISTEMA AVVIATO - Ottimizzazione FPS attiva")

while True:
    frame = vs.read()
    if frame is None:
        continue
        
    h, w, _ = frame.shape
    
    # Definisci la zona centrale (es. 60% centrale dello schermo)
    margin_w = int(w * 0.2)
    margin_h = int(h * 0.2)
    scan_x_min, scan_x_max = margin_w, w - margin_w - size
    scan_y_min, scan_y_max = margin_h, h - margin_h - size
    
    # Inizializzazione posizione
    if x is None or y is None:
        x = scan_x_min
        y = scan_y_min

    # Aggiornamento posizione solo se non siamo in pausa
    if pause_frames > 0:
        pause_frames -= 1
    else:
        # Aggiornamento posizione X
        x += direzione * velocita
        
        # Controllo bordi e aggiornamento Y
        if x >= scan_x_max or x <= scan_x_min:
            direzione *= -1
            y += step_y
            if y > scan_y_max:
                y = scan_y_min
    
    # Clipping x e y
    x = max(scan_x_min, min(x, scan_x_max))
    y = max(scan_y_min, min(y, scan_y_max))
    
    roi = frame[y:y + size, x:x + size]

    # Pre-processing ottimizzato
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Resize ridotto a 2x invece di 3x per velocità
    gray_resized = cv2.resize(gray, (size*2, size*2), interpolation=cv2.INTER_LINEAR)
    
    # Gaussian Blur (molto più veloce di Bilateral)
    gray_filtered = cv2.GaussianBlur(gray_resized, (5, 5), 0)
    
    # Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(gray_filtered, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 25, 10)

    # Pulizia morfologica ridotta
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    detected_char = None
    
    # Esegue OCR solo periodicamente o se siamo lockati su una detection
    frame_count += 1
    if pause_frames > 0 or frame_count % OCR_SKIP_FRAMES == 0:
        config = f'--tessdata-dir "{tessdata_dir}" -l grc --psm 10 -c tessedit_char_whitelist=ΩΦΨ'
        try:
            # image_to_string è più veloce di image_to_data
            text = pytesseract.image_to_string(thresh, config=config).strip()
            if text:
                detected_char = text[0]
                pause_frames = 10 
        except Exception as e:
            pass

    detection_buffer.append(detected_char)
    valid_detections = [c for c in detection_buffer if c is not None]
    
    greek_map = {'Ω': 'Omega', 'Φ': 'Phi', 'Ψ': 'Psi'}

    # HUD ed FPS
    fps_count += 1
    if time.time() - fps_start_time >= 1.0:
        fps_display = fps_count
        fps_count = 0
        fps_start_time = time.time()

    cv2.putText(frame, f"FPS: {fps_display}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Disegna l'AREA DI SCANSIONE
    cv2.rectangle(frame, (scan_x_min, scan_y_min), (scan_x_max + size, scan_y_max + size), (100, 100, 100), 1)

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

    # Disegna il rettangolo di scansione
    color = (0, 255, 0) if pause_frames > 0 else (127, 0, 255)
    cv2.rectangle(frame, (x, y), (x + size, y + size), color, 2)
    
    cv2.imshow("Webcam Scanner", frame)
    cv2.imshow("Debug Thresh", thresh)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vs.stop()
cv2.destroyAllWindows()
