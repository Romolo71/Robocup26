
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
    def __init__(self, src=1, cap=None):
        if cap is not None:
            self.stream = cap
        else:
            self.stream = cv2.VideoCapture(src)
        
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
        # Solo se abbiamo creato noi la cattura la rilasciamo
        # In questo caso, per semplicità, non la rilasciamo qui se vogliamo condividerla
        # self.stream.release()

class LetterDetector:
    def __init__(self, size=100, velocita=12):
        self.size = size
        self.velocita = velocita
        self.step_y = int(size/4)
        self.pause_frames = 0
        
        # Variabili di stato
        self.x = None
        self.y = None
        self.direzione = 1
        
        # Buffer per stabilizzazione temporale
        self.detection_buffer = deque(maxlen=20)
        
        # Variabili per calcolo OCR
        self.frame_count = 0
        self.OCR_SKIP_FRAMES = 3
        
        # Configurazione Tesseract
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.tessdata_dir = os.path.join(self.script_dir, 'tessdata')
        
    def process_frame(self, frame):
        if frame is None:
            return None, "NO_FRAME"
            
        h, w, _ = frame.shape
        
        # Definisci la zona centrale (es. 60% centrale dello schermo)
        margin_w = int(w * 0.2)
        margin_h = int(h * 0.2)
        scan_x_min, scan_x_max = margin_w, w - margin_w - self.size
        scan_y_min, scan_y_max = margin_h, h - margin_h - self.size
        
        # Inizializzazione posizione
        if self.x is None or self.y is None:
            self.x = scan_x_min
            self.y = scan_y_min

        # Aggiornamento posizione solo se non siamo in pausa
        if self.pause_frames > 0:
            self.pause_frames -= 1
        else:
            # Aggiornamento posizione X
            self.x += self.direzione * self.velocita
            
            # Controllo bordi e aggiornamento Y
            if self.x >= scan_x_max or self.x <= scan_x_min:
                self.direzione *= -1
                self.y += self.step_y
                if self.y > scan_y_max:
                    self.y = scan_y_min
        
        # Clipping x e y
        self.x = max(scan_x_min, min(self.x, scan_x_max))
        self.y = max(scan_y_min, min(self.y, scan_y_max))
        
        roi = frame[self.y:self.y + self.size, self.x:self.x + self.size]

        # Pre-processing ottimizzato
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Resize ridotto a 2x invece di 3x per velocità
        gray_resized = cv2.resize(gray, (self.size*2, self.size*2), interpolation=cv2.INTER_LINEAR)
        
        # Gaussian Blur
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
        self.frame_count += 1
        if self.pause_frames > 0 or self.frame_count % self.OCR_SKIP_FRAMES == 0:
            config = f'--tessdata-dir "{self.tessdata_dir}" -l grc --psm 10 -c tessedit_char_whitelist=ΩΦΨ'
            try:
                text = pytesseract.image_to_string(thresh, config=config).strip()
                if text:
                    detected_char = text[0]
                    self.pause_frames = 10 
            except Exception:
                pass

        self.detection_buffer.append(detected_char)
        valid_detections = [c for c in self.detection_buffer if c is not None]
        
        greek_map = {'Ω': 'Omega', 'Φ': 'Phi', 'Ψ': 'Psi'}
        result_text = None

        if valid_detections:
            counts = Counter(valid_detections)
            most_common, count = counts.most_common(1)[0]
            
            if most_common in greek_map and count >= 5:
                self.pause_frames = 5
                result_text = greek_map[most_common]
        
        # Visualizzazione sul frame
        status = "SCANNING" if self.pause_frames == 0 else "LOCKING..."
        cv2.putText(frame, f"Mode: {status}", (w-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.rectangle(frame, (scan_x_min, scan_y_min), (scan_x_max + self.size, scan_y_max + self.size), (100, 100, 100), 1)
        
        if result_text:
             cv2.putText(frame, f"Greca: {result_text}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        color = (0, 255, 0) if self.pause_frames > 0 else (127, 0, 255)
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.size, self.y + self.size), color, 2)
        
        return result_text, status

def main():
    vs = VideoStream(src=1).start()
    time.sleep(1.0) # Tempo di riscaldamento camera
    
    detector = LetterDetector()
    
    fps_count = 0
    fps_start_time = time.time()
    fps_display = 0

    print("SISTEMA AVVIATO - Standalone Mode")

    try:
        while True:
            frame = vs.read()
            if frame is None:
                continue
                
            res, status = detector.process_frame(frame)
            
            # Calcolo FPS
            fps_count += 1
            if time.time() - fps_start_time >= 1.0:
                fps_display = fps_count
                fps_count = 0
                fps_start_time = time.time()

            cv2.putText(frame, f"FPS: {fps_display}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Webcam Scanner", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        vs.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
