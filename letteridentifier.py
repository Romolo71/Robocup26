

import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break


    roi = frame[100:300, 100:300]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)


    config = '--psm 10 -c tessedit_char_whitelist=HSU'
    text = pytesseract.image_to_string(thresh, config=config).strip().upper()

    if text in ['H', 'S', 'U']:
        print("Lettera rilevata:", text)
        cv2.putText(frame, f"Lettera: {text}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    cv2.rectangle(frame, (100, 100), (300, 300), (255, 0, 0), 2)
    cv2.imshow("Webcam", frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()