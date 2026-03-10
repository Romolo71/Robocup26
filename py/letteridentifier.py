
import cv2
import pytesseract

import os
import platform

# Configurazione Tesseract: prova il comando di sistema se su Linux, altrimenti usa il percorso Windows
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
elif os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# Se non presente, confida che sia nel PATH


cap = cv2.VideoCapture(0)
size = 200
x = 0
direzione = 1 #quando è uguale a 1 va verso destra else = -1 va a sinistra
velocita = 7
while True:
    ret, frame = cap.read()
    h, w, _ = frame.shape
    x+= direzione*velocita
    if x+size >= w or x<=0: direzione*=-1
    roi = frame[100:100 + size, x:x+size]
    if not ret:
        break



    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)


    # Aggiunte Omega (Ω), Phi (Φ), Psi (Ψ) alla whitelist
    config = '--psm 10 -c tessedit_char_whitelist=HSUΩΦΨ'
    # Per gestire i simboli greci potrebbe essere necessario aggiungere il linguaggio greco se installato:
    # config = '-l eng+grc --psm 10 -c tessedit_char_whitelist=HSUΩΦΨ'
    
    text = pytesseract.image_to_string(thresh, config=config).strip().upper()

    # Mappatura per visualizzazione amichevole
    greek_map = {
        'Ω': 'Omega',
        'Φ': 'Phi',
        'Ψ': 'Psi'
    }

    if text in ['H', 'S', 'U'] or text in greek_map:
        display_text = greek_map.get(text, text)
        print("Lettera rilevata:", display_text)
        cv2.putText(frame, f"Lettera: {display_text}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    cv2.rectangle(frame, (x, 100), (x+size, 100+size), (127, 0, 255), 2)
    cv2.imshow("Webcam", frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
