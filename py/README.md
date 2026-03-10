# Cartella Moduli Python (RoboCup 2026)

Questa cartella contiene i moduli di elaborazione per le varie task del robot RoboCup Junior Rescue Maze 2026.

## Contenuto

- [Mapping.py](file:///home/samuele/containers-vps/docker/webserver/sites/Robocup26/py/Mapping.py): Sistema di mappatura del labirinto con UI Pygame e integrazione AI (TFLite).
- [cognitive_target.py](file:///home/samuele/containers-vps/docker/webserver/sites/Robocup26/py/cognitive_target.py): Rilevatore di "Cognitive Target" (circle color value) con elaborazione in tempo reale dei cerchi concentrici.
- [letterIdentifier.py](file:///home/samuele/containers-vps/docker/webserver/sites/Robocup26/py/letterIdentifier.py): Rilevatore di lettere greche (Ω, Φ, Ψ) basato su Tesseract OCR e scansione ROI mobile.

## Utilizzo

I file possono essere eseguiti come **standalone**:
```bash
python3 py/cognitive_target.py
```

Oppure integrati nel **wrapper** principale (`wrapper.py`) che gestisce la condivisione della videocamera e il caricamento dinamico dei moduli.

## Requisiti

- OpenCV (`cv2`)
- NumPy
- Pygame (per Rendering mappa)
- Pytesseract (per il rilevamento lettere)
- TensorFlow Lite (per il sistema di visione in Mapping.py)
