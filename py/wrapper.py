import cv2
import time
import sys
import os
import serial

# Aggiungi la cartella py al path per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'py'))

try:
    from cognitive_target import CognitiveTargetDetector
    from letterIdentifier import LetterDetector
except ImportError as e:
    print(f"Errore Import: {e}")
    sys.exit(1)

class ModuleWrapper:
    def __init__(self, camera_index=0):
        print(f"Inizializzazione Wrapper con Camera {camera_index}...")
        self.cap = cv2.VideoCapture(camera_index)
        
        # Configurazione camera comune
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Inizializzazione moduli
        self.cognitive_detector = CognitiveTargetDetector()
        self.letter_detector = LetterDetector(size=200, velocita=6)
        
        # Inizializzazione Serial per ESP32
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            print("Connessione Serial stabilita su /dev/ttyUSB0")
        except Exception as e:
            print(f"Avviso: Impossibile aprire la porta seriale: {e}")
            self.ser = None

        self.last_letter_time = 0
        self.last_circle_time = 0
        self.detection_cooldown = 2.0  # secondi tra notifiche dello stesso tipo
        
        self.running = True

    def run(self):
        print("Wrapper avviato. Premi 'q' per uscire.")
        
        fps_count = 0
        fps_start_time = time.time()
        fps_display = 0

        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                h, w, _ = frame.shape
                
                # 1. Cognitive Target Detection
                score, action = self.cognitive_detector.process_frame(frame)
                
                # Sincronizzazione Cerchio con ESP32 via Serial
                if score is not None and self.ser:
                    current_time = time.time()
                    if current_time - self.last_circle_time > self.detection_cooldown:
                        char_to_send = str(int(score))
                        self.ser.write(char_to_send.encode())
                        print(f"Inviato a ESP32 (Cerchio): {char_to_send} (Azione: {action})")
                        self.last_circle_time = current_time

                # 2. Letter Recognition
                letter, status = self.letter_detector.process_frame(frame)
                
                # Sincronizzazione Lettera con ESP32 via Serial
                if letter and self.ser:
                    current_time = time.time()
                    if current_time - self.last_letter_time > self.detection_cooldown:
                        char_to_send = letter[0] # Prende la prima lettera (O, P, S)
                        self.ser.write(char_to_send.encode())
                        print(f"Inviato a ESP32 (Lettera): {char_to_send}")
                        self.last_letter_time = current_time
                
                # Calcolo FPS
                fps_count += 1
                if time.time() - fps_start_time >= 1.0:
                    fps_display = fps_count
                    fps_count = 0
                    fps_start_time = time.time()
                
                # HUD Wrapper
                cv2.putText(frame, f"WRAPPER FPS: {fps_display}", (10, h - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow("RoboCup 2026 - Multitask Wrapper", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    
        finally:
            if self.ser:
                self.ser.close()
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    # È possibile passare l'indice della camera come argomento
    # cam_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cam_id = 1
    wrapper = ModuleWrapper(camera_index=cam_id)
    wrapper.run()
