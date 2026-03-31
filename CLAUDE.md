# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RoboCup Junior Rescue Maze 2026** robot system with three integrated components:

1. **ESP32 Firmware** (`esp32/`): Motor control and REST API for autonomous robot navigation
2. **Web UI** (`webUI/`): PHP/JavaScript dashboard for manual robot control and motor calibration
3. **Python Vision System** (`py/`): Computer vision and mapping with Pygame UI, AI inference (TFLite), and modular detectors

These components operate independently but can integrate: the Python wrapper can send detection results to ESP32 via serial, and the Web UI controls ESP32 via HTTP.

## Repository Structure

```
esp32/           # ESP32 Arduino sketches (multiple firmware variants)
├── movimentoWeb/     # Web-enabled firmware with REST API (primary)
├── main/             # Basic motor control sketch
├── remoteMove/       # Remote control variant
├── esp32_receiver/   # Serial receiver
└── CC_RegionaliV_1.0/ # Competition firmware

py/              # Python vision and mapping system
├── Mapping.py        # Main SLAM/mapping application with Pygame UI
├── wrapper.py        # Multi-module wrapper with serial ESP32 communication
├── cognitive_target.py    # Cognitive target detector (concentric circles)
├── enhanced_cognitive_target.py  # Improved detector with color sampling
├── letterIdentifier.py   # OCR-based letter detector (Greek letters)
├── test_enhanced_cognitive_target.py  # Unit tests
└── tessdata/         # Tesseract training data

webUI/           # PHP web dashboard
├── index.php         # Main interface with authentication
├── styles/style.css  # UI styling
└── scripts/          # JavaScript (placeholder files)

ROBOTICA_2/      # Additional project materials (likely documentation/design files)
```

## Development Environment Setup

### Python Environment (Vision System)

```bash
cd py
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install opencv-python numpy pygame pytesseract tensorflow-lite
```

Dependencies (may need manual installation):
- OpenCV (with camera support)
- Pygame (for Mapping.py UI)
- Tesseract OCR (system package + pytesseract Python wrapper)
- TensorFlow Lite runtime

### ESP32 Environment

- Arduino IDE with ESP32 board support
- WiFi credentials in `esp32/movimentoWeb/wifi_secrets.h`:
  ```cpp
  #define WIFI_SSID "your_ssid"
  #define WIFI_PSWD "your_password"
  ```

### Web UI Environment

- PHP built-in server is sufficient:
  ```bash
  cd webUI
  php -S localhost:8000
  ```
- Access: `http://localhost:8000/index.php`
- Default password: `robot2026` (change in `index.php`)

## Common Development Tasks

### Running Python Components

**Run Mapping system (SLAM + AI):**
```bash
cd py
python Mapping.py
```

**Run multi-module wrapper (cognitive target + letter detection + ESP32 serial):**
```bash
cd py
python wrapper.py
# Camera index can be modified in wrapper.py (default: 1)
```

**Run individual detector standalone:**
```bash
python cognitive_target.py
python letterIdentifier.py
```

### Testing

**Run cognitive target detector tests:**
```bash
cd py
python test_enhanced_cognitive_target.py
```
Tests create synthetic target images and validate detection accuracy under various conditions (light levels, noise). Failures save images to `/tmp/failed_test_*.png`.

### ESP32 Firmware

**Build/Flash:**
Open the `.ino` file in Arduino IDE, select ESP32 board, and upload. Primary firmware: `esp32/movimentoWeb/movimentoWeb.ino`.

**ESP32 REST API endpoints** (movimentoWeb firmware):
- `GET /move-fwd` - Move forward
- `GET /move-bkw` - Move backward
- `GET /turn-cw` - Turn clockwise
- `GET /turn-ccw` - Turn counter-clockwise
- `GET /stop` - Stop motors
- `GET /update?fwdA=255&fwdB=255&...` - Update PWM calibration values
- `GET /` - Status page

**Serial protocol** (from wrapper.py):
- Sends single ASCII characters: `0-9` for cognitive target scores, `O/P/S` for letters
- Baud rate: 115200 on `/dev/ttyUSB0`

### Web UI

**Start local server:**
```bash
cd webUI
php -S localhost:8000
```

The UI sends HTTP GET requests to the configured ESP32 IP address.

## Architecture Insights

**Data Flow:**
- Python Mapping.py: Captures camera frames → TFLite inference → Updates 2D grid map → Renders Pygame UI
- Python wrapper.py: Shared camera → cognitive_target + letterIdentifier modules → optional serial to ESP32
- Web UI: User input → HTTP requests → ESP32 → Motor driver outputs
- ESP32: Receives HTTP commands → PWM control via LEDC API → L298N/TB6612 drivers

**Key Configuration Points:**
- `py/Mapping.py` lines 23-72: Global CONFIG dict (window size, grid settings, AI model paths, camera settings, colors)
- `py/wrapper.py` lines 30-36: Serial port configuration
- `esp32/movimentoWeb/movimentoWeb.ino` lines 11-18: Motor pin definitions and PWM calibration variables
- `webUI/index.php` line 3: Default authentication password

**Module Wrapper Pattern:**
The `wrapper.py` demonstrates a production pattern: shared camera resource with multiple detection modules running sequentially. Useful reference for adding new vision modules without camera conflicts.

**Demo Mode:**
`Mapping.py` has `DEMO_MODE: True` in CONFIG - when True, it uses simulated data instead of live camera/AI. Set to False for real operation.

## Notes for Future Development

- Camera indices: wrapper.py uses `1`, Mapping.py default is `0`. Adjust based on hardware.
- Python 3.8+ recommended (tested with type hints and dataclasses)
- ESP32 firmware variants exist - use `movimentoWeb/` for network control, others are legacy/alternative
- Tessdata folder contains trained language data for Greek letter recognition; ensure it's in working directory when running `letterIdentifier.py`
