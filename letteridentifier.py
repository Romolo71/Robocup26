import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


cap = cv2.VideoCapture(0)
size = 200
x = 0
direzione = 1 #quando è uguale a 1 va verso destra else = -1 va a sinistra
velocita = 3
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


    config = '--psm 10 -c tessedit_char_whitelist=HSU'
    text = pytesseract.image_to_string(thresh, config=config).strip().upper()

    if text in ['H', 'S', 'U']:
        print("Lettera rilevata:", text)
        cv2.putText(frame, f"Lettera: {text}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    cv2.rectangle(frame, (x, 100), (x+size, 100+size), (100, 0, 255), 2)
    cv2.imshow("Webcam", frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
