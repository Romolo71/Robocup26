# 🤖 RoboCup 2026 - Rescue Robot System

Benvenuto nel repository del progetto per la **RoboCup Junior Rescue Maze 2026**.
Questo progetto implementa il software completo per la gestione di un robot di salvataggio autonomo, diviso in tre componenti principali: controllo hardware su ESP32, un'interfaccia web di comando e un avanzato sistema di visione artificiale in Python.

---

## 🏗️ Architettura del Progetto

Il repository è strutturato in tre moduli principali per garantire la massima modularità e flessibilità:

### 1. `esp32/` - Firmware Hardware (C++)
Contiene gli sketch per il microcontrollore **ESP32**, responsabile della gestione dei motori e della connettività.
* **API RESTful integrata**: L'ESP32 espone un server web in ascolto su WiFi per ricevere comandi di movimento (`/move-fwd`, `/move-bkw`, `/turn-cw`, `/turn-ccw`, `/stop`).
* **Calibrazione Motori (PWM)**: Include endpoint (`/update`) per la taratura fine della velocità dei singoli motori per ogni direzione, permettendo di correggere derive hardware e ottenere movimenti rettilinei.
* **Driver L298N / TB6612**: Supporto implementato tramite le API `ledc` dell'ESP32 per il controllo hardware del PWM.

### 2. `webUI/` - Control Center (PHP/JS)
Una dashboard di comando web usata per il controllo remoto, il debug e la configurazione del robot.
* **Pannello di Controllo Manuale**: Permette di guidare il robot durante i test tramite pulsanti o tastiera.
* **Sistema di Calibrazione Avanzata**: Un menu dedicato per configurare le velocità PWM (0-255) per ciascun motore in base alle diverse direzioni (Avanti, Indietro, Destra, Sinistra). Le impostazioni vengono salvate live sull'ESP32.
* **Sicurezza**: Protetto da password per limitare l'accesso ai soli operatori.

### 3. `py/` - Mapping & Computer Vision (Python)
Il "cervello" della navigazione autonoma e del riconoscimento visivo, pensato per girare su un single-board computer (es. Raspberry Pi 5).
* **Computer Vision AI**: Utilizza **TensorFlow Lite** per l'inferenza real-time delle immagini dalla videocamera, riconoscendo muri, pavimenti, vittime e lettere sui muri (X, Y, H).
* **Mappatura Dinamica (SLAM-like)**: Genera e mantiene una mappa in tempo reale del labirinto, tracciando la posizione del robot, i perimetri esplorati e la presenza di vittime.
* **Interfaccia Grafica Professionale**: Realizzata in **Pygame**, mostra la mappa del labirinto che si svela progressivamente, completa di legenda, calcolo degli FPS, e statistiche live su vittime e target visivi identificati. Presenta anche una comoda "Demo Mode" integrata.

---

## 🚀 Setup e Installazione

### ESP32 Firmware
1. Assicurati di avere l'IDE Arduino configurato per schede ESP32.
2. Copia (o posiziona come `.env`) le credenziali del Wi-Fi nel file `wifi_secrets.h`.
3. Compila e flasha lo sketch contenuto inside `esp32/movimentoWeb/movimentoWeb.ino`.
4. Prendi nota dell'Indirizzo IP che l'ESP32 stampo sul monitor seriale o inseriscilo nella Web UI.

### Web UI
1. Ospita i file all'interno della cartella `webUI/` in un server web con supporto PHP (Apache/Nginx o semplicemente `php -S`).
2. Accedi alla dashboard tramite `http://localhost/index.php`.
3. Inserisci la password predefinita e immetti l'indirizzo IP del tuo ESP32 per collegare i sistemi.

### Python Mapping
1. È raccomandato creare un virtual environment: `python -m venv venv && source venv/bin/activate`
2. Installa le dipendenze richieste (Pygame, Numpy, TensorFlow/TFLite, ecc.).
3. Esegui il software principale di mappatura:
```bash
cd py
python Mapping.py
```

---

## 🛠 Sviluppi Futuri
* Integrazione sensori ToF/Ultrasuoni sull'ESP32 per l'anti-collisione.
* Collegamento diretto tra il map-planner Python e le chiamate HTTP all'IP dell'ESP32 per far muovere il robot autonomamente all'interno del labirinto.

## 📄 Licenza
Fai riferimento al file [LICENSE](LICENSE) per ulteriori dettagli sui permessi e sull'utilizzo del codice sorgente di questo progetto.
