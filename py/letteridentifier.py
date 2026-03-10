
import cv2
import pytesseract
import os
import platform

# Configurazione Tesseract
script_dir = os.path.dirname(os.path.abspath(__file__))
tessdata_dir = os.path.join(script_dir, 'tessdata')

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

cap = cv2.VideoCapture(0)
size = 200
x = 0
direzione = 1 #quando è uguale a 1 va verso destra else = -1 va a sinistra
velocita = 7

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    h, w, _ = frame.shape
    x += direzione * velocita
    if x + size >= w or x <= 0: direzione *= -1
    
    roi = frame[100:100 + size, x:x+size]

    # Pre-processing migliorato per OCR
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Ridimensionamento per migliorare la leggibilità (2x)
    gray_resized = cv2.resize(gray, (size*2, size*2), interpolation=cv2.INTER_CUBIC)
    
    # Thresholding di Otsu per adattarsi alla luce
    _, thresh = cv2.threshold(gray_resized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Configurazione: usa la lingua greca (grc)
    # Rimosso il whitelist per migliorare il riconoscimento di Φ
    config = f'--tessdata-dir "{tessdata_dir}" -l grc --psm 10'
    
    try:
        text = pytesseract.image_to_string(thresh, config=config).strip()
    except Exception as e:
        text = ""

    # Mappatura per visualizzazione
    greek_map = {
        'Ω': 'Omega',
        'Φ': 'Phi',
        'Ψ': 'Psi'
    }

    if text in greek_map:
        display_text = greek_map[text]
        print(f"Lettera greca rilevata: {display_text}")
        cv2.putText(frame, f"Greca: {display_text}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.rectangle(frame, (x, 100), (x+size, 100+size), (127, 0, 255), 2)
    cv2.imshow("Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
