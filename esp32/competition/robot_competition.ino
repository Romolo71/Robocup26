/*
 * ============================================================
 *  ESP32 – Robot Competition Firmware for RoboCup 2026
 *  Definitive Gara Code – No WiFi, Serial Comm with Raspberry
 * ============================================================
 *
 *  Features:
 *   - Motor control with PWM (LEDC) and EEPROM calibration
 *   - TCS34725 color sensor for floor tiles
 *   - 4x VL53L0X distance sensors for obstacle avoidance
 *   - Servo for rescue kit deployment
 *   - Serial protocol with Raspberry Pi (Serial1 @ 115200 baud)
 *   - Dual modes: AUTO (obstacle avoidance) and MANUAL (direct commands)
 *   - Victim handling per 2026 rules (letters Φ,Ψ,Ω and cognitive targets)
 *   - Tile detection: Black (LoP), Silver (checkpoint), Blue (stop 5s), Red (danger)
 *
 *  PIN MAP (matches PCB ROBOTICA_2):
 *    Motor A:       pin1=2, pin2=4
 *    Motor B:       pin3=16, pin4=17
 *    Servo kit:     15
 *    LED Vittima:   32 (also TCS34725 LED enable, shared)
 *    TCS34725 SDA:  26 (Wire1)
 *    TCS34725 SCL:  25 (Wire1)
 *    VL53L0X XSHUT: FRONT=23, BACK=18, LEFT=33, RIGHT=19 (Wire1)
 *    Serial Rasp:   Serial1 (GPIO1=TX, GPIO3=RX)
 *
 *  Libraries (Arduino Library Manager):
 *   - Adafruit VL53L0X
 *   - Adafruit TCS34725
 *   - ESP32Servo
 *   - EEPROM (built-in)
 *
 *  PROTOCOL (Raspberry Pi -> ESP32, one ASCII byte commands):
 *   Movement:   'F'=Forward, 'B'=Backward, 'L'=Left, 'R'=Right, 'S'=Stop
 *   Actions:    'D'=Drop rescue kit
 *   Mode:       'M'=Manual mode, 'A'=Auto mode
 *   Victims:    'P'=Φ (Harmed, 2 kits), 'S'=Ψ (Stable, 1 kit), 'O'=Ω (Unharmed, 0 kits)
 *   Cognitive:  '2'=Harmed, '1'=Stable, '0'=Unharmed
 *   Tiles:      'B'=Blue tile stop (5s), 'E'=Exit bonus (blink 10s & halt)
 *
 *  PROTOCOL (ESP32 -> Raspberry, one ASCII byte events):
 *   'b' = Blue tile detected (and stopped)
 *   'k' = Black tile (LoP)
 *   'v' = Silver tile (checkpoint)
 *   'r' = Red tile (dangerous zone)
 *   'K' = Rescue kit deployed
 *
 *  CALIBRATION PWM:
 *   - Values saved in EEPROM and loaded at boot.
 *   - Default: fwdA=fwdB=bkwA=bkwB=200, cwA=cwB=ccwA=ccwB=180.
 *
 *  ============================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <EEPROM.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_TCS34725.h>
#include <ESP32Servo.h>

// ── PIN DEFINITIONS ───────────────────────────────────────────────
const int PIN_MOTOR_A1 = 2;
const int PIN_MOTOR_A2 = 4;
const int PIN_MOTOR_B1 = 16;
const int PIN_MOTOR_B2 = 17;

const int PIN_SERVO = 15;
const int PIN_LED = 32;   // LED vittima + TCS34725 LED enable (shared)

// VL53L0X XSHUT pins
const int XSHUT_FRONT = 23;
const int XSHUT_BACK  = 18;
const int XSHUT_LEFT  = 33;
const int XSHUT_RIGHT = 19;
const uint8_t ADDR_FRONT = 0x30;
const uint8_t ADDR_BACK  = 0x31;
const uint8_t ADDR_LEFT  = 0x32;
const uint8_t ADDR_RIGHT = 0x33;

// TCS34725 on Wire1
const int TCS_SDA = 26;
const int TCS_SCL = 25;

// ── PWM CONFIG ─────────────────────────────────────────────────────
const int MOTOR_PWM_FREQ = 5000;
const int MOTOR_PWM_RES  = 8;   // 0-255
// LEDC channels: 0->A1, 1->A2, 2->B1, 3->B2

// ── EEPROM CALIBRATION STRUCT ─────────────────────────────────────
#define CALIB_MAGIC 0xA5A5A5A5UL
struct Calibration {
  uint32_t magic;
  uint8_t fwdA, fwdB;
  uint8_t bkwA, bkwB;
  uint8_t cwA,  cwB;
  uint8_t ccwA, ccwB;
};
Calibration calib;

// ── GLOBAL OBJECTS ────────────────────────────────────────────────
Adafruit_VL53L0X laserFront, laserBack, laserLeft, laserRight;
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);
bool tcsOk = false;
Servo rescueServo;

// ── CONSTANTS ──────────────────────────────────────────────────────
const int DIST_THRESHOLD_CM = 15;
const int TURN_DELAY_MS     = 500;
const long BLINK_VICTIM_MS  = 5000;
const long BLINK_EXIT_MS    = 12000;
const int  BLINK_INTV       = 500;  // victim blink interval
const int  BLINK_EXIT_INTV  = 1000; // exit blink interval
const int  BLUE_STOP_MS     = 5000;
const int  MAX_RESCUE_KITS  = 8;

// Color thresholds (calibrate in the field)
const float LUMA_BLACK_THR  = 300.0;
const float LUMA_SILVER_THR = 3000.0;
const float BLUE_NORM_THR   = 0.40;
const float RED_NORM_THR    = 0.45;

// ── ENUMS ──────────────────────────────────────────────────────────
enum TileColor { TILE_NORMAL, TILE_BLACK, TILE_SILVER, TILE_BLUE, TILE_RED };
enum Mode { MODE_AUTO, MODE_MANUAL };
enum MoveCmd { MOVE_NONE, MOVE_FORWARD, MOVE_BACKWARD, MOVE_LEFT, MOVE_RIGHT, MOVE_STOP };

// ── GLOBAL STATE ───────────────────────────────────────────────────
Mode currentMode = MODE_AUTO;
MoveCmd currentMove = MOVE_FORWARD; // for manual mode: last movement command
int kitCount = MAX_RESCUE_KITS;
TileColor lastTile = TILE_NORMAL;

// ── FUNCTION DECLARATIONS ─────────────────────────────────────────
void setMotorPWM(uint8_t a1, uint8_t a2, uint8_t b1, uint8_t b2);
void moveForward();
void moveBackward();
void turnRightInPlace();
void turnLeftInPlace();
void autoTurnRight();
void autoTurnLeft();
void stopMotors();
void initMotorPWM();
bool loadCalibration();
void saveCalibration();
void blinkLED(int interval_ms, long duration_ms);
void deployRescueKit();
void handleVictim(int status);
TileColor readTileColor();
void handleTileColor(TileColor tile);
void initLasers();
int readDistance(Adafruit_VL53L0X &sensor);
void processSerial();
void executeManualMovement();
void doExitBonus();

// ═══════════════════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════════════════
void setup() {
  // Debug serial (USB)
  Serial.begin(115200);
  while (!Serial) { ; } // wait for serial monitor

  // Protocol serial with Raspberry (pins 1 TX, 3 RX)
  Serial1.begin(115200, SERIAL_8N1, 3, 1); // RX=3, TX=1

  // Motor PWM setup
  initMotorPWM();
  stopMotors();

  // LED output
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // Load calibration from EEPROM
  if (!loadCalibration()) {
    // Set defaults and save
    calib = { CALIB_MAGIC, 200,200, 200,200, 180,180, 180,180 };
    saveCalibration();
  }
  Serial.println("Calibrazione PWM caricata.");

  // Wire1 for sensors
  Wire1.begin(TCS_SDA, TCS_SCL);

  // TCS34725 init
  tcsOk = tcs.begin(TCS34725_ADDRESS, &Wire1);
  if (!tcsOk) {
    Serial.println("ERRORE: TCS34725 non trovato!");
  } else {
    Serial.println("TCS34725 OK.");
  }

  // VL53L0X init (4 sensors)
  initLasers();

  // Servo init (rest position)
  rescueServo.setPeriodHZ(50);
  rescueServo.attach(PIN_SERVO, 500, 2400); // typical servo pulse width
  rescueServo.write(0);
  delay(500);
  rescueServo.detach();

  // Start in AUTO forward
  currentMode = MODE_AUTO;
  currentMove = MOVE_FORWARD;
  Serial.println("=== RoboCup 2026 – Robot Competition Firmware ===");
  Serial.print("Kit caricati: "); Serial.println(kitCount);
}

// ═══════════════════════════════════════════════════════════════════
//  MAIN LOOP
// ═══════════════════════════════════════════════════════════════════
void loop() {
  // 1. Read floor tile color
  TileColor currentTile = readTileColor();
  handleTileColor(currentTile);

  // 2. Special handling for Black tile (LoP) – always stop and wait for 'E'
  if (currentTile == TILE_BLACK) {
    stopMotors();
    if (Serial1.available() > 0) {
      char cmd = Serial1.read();
      if (cmd == 'E') {
        doExitBonus();
      }
    }
    delay(100);
    return; // Skip command processing and movement
  }

  // 3. Process incoming serial commands from Raspberry
  processSerial();

  // 4. Movement based on mode
  if (currentMode == MODE_MANUAL) {
    executeManualMovement();
  } else { // AUTO
    // Obstacle avoidance using front laser
    int distFront = readDistance(laserFront);
    if (distFront <= DIST_THRESHOLD_CM && distFront > 0) {
      // Obstacle ahead: decide which way to turn
      int distLeft  = readDistance(laserLeft);
      int distRight = readDistance(laserRight);
      Serial.print("[NAV] Ostacolo a "); Serial.print(distFront);
      Serial.print(" cm. SX="); Serial.print(distLeft);
      Serial.print(" DX="); Serial.println(distRight);
      if (distLeft > distRight) {
        autoTurnLeft();
      } else {
        autoTurnRight();
      }
      // After autoTurn, we continue forward next loop iteration
    } else {
      moveForward();
    }
  }

  delay(50); // small loop period
}

// ═══════════════════════════════════════════════════════════════════
//  MOTOR PWM LOW-LEVEL
// ═══════════════════════════════════════════════════════════════════
void setMotorPWM(uint8_t a1, uint8_t a2, uint8_t b1, uint8_t b2) {
  ledcWrite(0, a1);
  ledcWrite(1, a2);
  ledcWrite(2, b1);
  ledcWrite(3, b2);
}

void initMotorPWM() {
  // Configure 4 LEDC channels
  ledcSetup(0, MOTOR_PWM_FREQ, MOTOR_PWM_RES);
  ledcSetup(1, MOTOR_PWM_FREQ, MOTOR_PWM_RES);
  ledcSetup(2, MOTOR_PWM_FREQ, MOTOR_PWM_RES);
  ledcSetup(3, MOTOR_PWM_FREQ, MOTOR_PWM_RES);
  // Attach pins to channels
  ledcAttachPin(PIN_MOTOR_A1, 0);
  ledcAttachPin(PIN_MOTOR_A2, 1);
  ledcAttachPin(PIN_MOTOR_B1, 2);
  ledcAttachPin(PIN_MOTOR_B2, 3);
}

void moveForward() {
  setMotorPWM(calib.fwdA, 0, calib.fwdB, 0);
}
void moveBackward() {
  setMotorPWM(0, calib.bkwA, 0, calib.bkwB);
}
void turnRightInPlace() {
  setMotorPWM(calib.cwA, 0, 0, calib.cwB);
}
void turnLeftInPlace() {
  setMotorPWM(0, calib.ccwA, calib.ccwB, 0);
}
void stopMotors() {
  setMotorPWM(0,0,0,0);
}

// Auto turning: stop, turn in place for fixed time, then forward
void autoTurnRight() {
  stopMotors();
  delay(50);
  turnRightInPlace();
  delay(TURN_DELAY_MS);
  moveForward();
}
void autoTurnLeft() {
  stopMotors();
  delay(50);
  turnLeftInPlace();
  delay(TURN_DELAY_MS);
  moveForward();
}

// ═══════════════════════════════════════════════════════════════════
//  EEPROM CALIBRATION
// ═══════════════════════════════════════════════════════════════════
bool loadCalibration() {
  EEPROM.begin(512);
  Calibration loaded;
  EEPROM.readBytes(0, &loaded, sizeof(loaded));
  if (loaded.magic != CALIB_MAGIC) return false;
  calib = loaded;
  return true;
}
void saveCalibration() {
  calib.magic = CALIB_MAGIC;
  EEPROM.writeBytes(0, &calib, sizeof(calib));
  EEPROM.commit();
}

// ═══════════════════════════════════════════════════════════════════
//  LED BLINK
// ═══════════════════════════════════════════════════════════════════
void blinkLED(int interval_ms, long duration_ms) {
  stopMotors();
  unsigned long start = millis();
  bool state = true;
  while (millis() - start < (unsigned long)duration_ms) {
    digitalWrite(PIN_LED, state ? HIGH : LOW);
    delay(interval_ms);
    state = !state;
  }
  digitalWrite(PIN_LED, LOW);
}

// ═══════════════════════════════════════════════════════════════════
//  RESCUE KIT DEPLOYMENT
// ═══════════════════════════════════════════════════════════════════
void deployRescueKit() {
  if (kitCount <= 0) {
    Serial.println("ERRORE: Kit esauriti!");
    Serial1.write('X'); // error to Raspberry
    return;
  }
  stopMotors();
  rescueServo.attach(PIN_SERVO);
  rescueServo.write(180); // eject position
  delay(1000);
  rescueServo.write(0);   // rest position
  delay(1000);
  rescueServo.detach();
  kitCount--;
  Serial.print("Kit rilasciato. Rimanenti: ");
  Serial.println(kitCount);
  Serial1.write('K'); // acknowledge to Raspberry
}

// ═══════════════════════════════════════════════════════════════════
//  VICTIM HANDLING
//  status: 0=Unharmed, 1=Stable, 2=Harmed
// ═══════════════════════════════════════════════════════════════════
void handleVictim(int status) {
  stopMotors();
  blinkLED(BLINK_INTV, BLINK_VICTIM_MS);
  if (status == 2) {
    deployRescueKit();
    delay(300);
    deployRescueKit();
  } else if (status == 1) {
    deployRescueKit();
  }
  // Resume movement only if AUTO; in MANUAL we leave stopped (operator will command)
  if (currentMode == MODE_AUTO) {
    moveForward();
  }
}

// ═══════════════════════════════════════════════════════════════════
//  COLOR SENSOR (TCS34725)
// ═══════════════════════════════════════════════════════════════════
TileColor readTileColor() {
  if (!tcsOk) return TILE_NORMAL;
  // Enable TCS LED (shared with PIN_LED)
  digitalWrite(PIN_LED, HIGH);
  delay(60);
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  digitalWrite(PIN_LED, LOW);
  if (c == 0) return TILE_NORMAL;
  float lux = tcs.calculateLux(r, g, b);
  float total = (float)(r + g + b);
  if (total == 0) return TILE_NORMAL;
  float r_n = r / total;
  float g_n = g / total;
  float b_n = b / total;
  // Debug (uncomment if needed)
  // Serial.printf("[TCS] lux=%.0f  r=%.2f g=%.2f b=%.2f\n", lux, r_n, g_n, b_n);
  if (lux < LUMA_BLACK_THR) return TILE_BLACK;
  if (lux > LUMA_SILVER_THR) return TILE_SILVER;
  if (b_n > BLUE_NORM_THR && b_n > r_n && b_n > g_n) return TILE_BLUE;
  if (r_n > RED_NORM_THR && r_n > g_n && r_n > b_n) return TILE_RED;
  return TILE_NORMAL;
}

void handleTileColor(TileColor tile) {
  if (tile == lastTile) return;
  lastTile = tile;
  switch (tile) {
    case TILE_BLACK:
      Serial.println("[TILE] NERO – LoP!");
      Serial1.write('k');
      // Handling of stop and wait is in main loop
      break;
    case TILE_SILVER:
      Serial.println("[TILE] ARGENTO – Checkpoint");
      Serial1.write('v');
      break;
    case TILE_BLUE:
      Serial.println("[TILE] BLU – attendo 5s");
      Serial1.write('b');
      stopMotors();
      delay(BLUE_STOP_MS);
      if (currentMode == MODE_AUTO) {
        moveForward();
      } else {
        executeManualMovement(); // resume manual command after blue stop
      }
      break;
    case TILE_RED:
      Serial.println("[TILE] ROSSO – Dangerous Zone");
      Serial1.write('r');
      // No special action other than notification
      break;
    default:
      break;
  }
}

// ═══════════════════════════════════════════════════════════════════
//  VL53L0X DISTANCE SENSORS INITIALIZATION
// ═══════════════════════════════════════════════════════════════════
void initLasers() {
  // Disable all sensors first
  pinMode(XSHUT_FRONT, OUTPUT); digitalWrite(XSHUT_FRONT, LOW);
  pinMode(XSHUT_BACK,  OUTPUT); digitalWrite(XSHUT_BACK,  LOW);
  pinMode(XSHUT_LEFT,  OUTPUT); digitalWrite(XSHUT_LEFT,  LOW);
  pinMode(XSHUT_RIGHT, OUTPUT); digitalWrite(XSHUT_RIGHT, LOW);
  delay(10);

  // FRONT
  digitalWrite(XSHUT_FRONT, HIGH);
  delay(10);
  if (!laserFront.begin(ADDR_FRONT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X FRONT non trovato!");
  } else {
    Serial.println("VL53L0X FRONT OK (0x30)");
  }

  // BACK
  digitalWrite(XSHUT_BACK, HIGH);
  delay(10);
  if (!laserBack.begin(ADDR_BACK, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X BACK non trovato!");
  } else {
    Serial.println("VL53L0X BACK  OK (0x31)");
  }

  // LEFT
  digitalWrite(XSHUT_LEFT, HIGH);
  delay(10);
  if (!laserLeft.begin(ADDR_LEFT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X LEFT non trovato!");
  } else {
    Serial.println("VL53L0X LEFT  OK (0x32)");
  }

  // RIGHT
  digitalWrite(XSHUT_RIGHT, HIGH);
  delay(10);
  if (!laserRight.begin(ADDR_RIGHT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X RIGHT non trovato!");
  } else {
    Serial.println("VL53L0X RIGHT OK (0x33)");
  }
}

int readDistance(Adafruit_VL53L0X &sensor) {
  VL53L0X_RangingMeasurementData_t measure;
  sensor.rangingTest(&measure, false);
  if (measure.RangeStatus != 4) {
    return measure.RangeMilliMeter / 10; // mm to cm
  }
  return 999; // no obstacle
}

// ═══════════════════════════════════════════════════════════════════
//  SERIAL COMMAND PROCESSING (from Raspberry Pi)
// ═══════════════════════════════════════════════════════════════════
void processSerial() {
  while (Serial1.available() > 0) {
    char cmd = Serial1.read();
    Serial.print("[CMD] "); Serial.println(cmd);
    switch (cmd) {
      // Movement commands
      case 'F':
        currentMode = MODE_MANUAL;
        currentMove = MOVE_FORWARD;
        break;
      case 'B':
        currentMode = MODE_MANUAL;
        currentMove = MOVE_BACKWARD;
        break;
      case 'L':
        currentMode = MODE_MANUAL;
        currentMove = MOVE_LEFT;
        break;
      case 'R':
        currentMode = MODE_MANUAL;
        currentMove = MOVE_RIGHT;
        break;
      case 'S':
        currentMode = MODE_MANUAL;
        currentMove = MOVE_STOP;
        break;
      // Mode switch
      case 'M':
        currentMode = MODE_MANUAL;
        Serial.println("Modalita: MANUAL");
        break;
      case 'A':
        currentMode = MODE_AUTO;
        currentMove = MOVE_FORWARD;
        Serial.println("Modalita: AUTO");
        break;
      // Victim / cognitive
      case 'P': handleVictim(2); break; // Φ
      case 'S': handleVictim(1); break; // Ψ
      case 'O': handleVictim(0); break; // Ω
      case '2': handleVictim(2); break;
      case '1': handleVictim(1); break;
      case '0': handleVictim(0); break;
      // Tile commands (from Raspberry if needed)
      case 'B':
        stopMotors();
        Serial.println("Blue tile (da Rasp): attendo 5s");
        delay(BLUE_STOP_MS);
        if (currentMode == MODE_AUTO) {
          moveForward();
        } else {
          executeManualMovement();
        }
        break;
      case 'E':
        doExitBonus();
        break;
      // Drop kit manual
      case 'D':
        deployRescueKit();
        break;
      default:
        Serial.print("[WARN] Comando sconosciuto: ");
        Serial.println(cmd);
        break;
    }
  }
}

void executeManualMovement() {
  switch (currentMove) {
    case MOVE_FORWARD:  moveForward(); break;
    case MOVE_BACKWARD: moveBackward(); break;
    case MOVE_LEFT:     turnLeftInPlace(); break;
    case MOVE_RIGHT:    turnRightInPlace(); break;
    case MOVE_STOP:     stopMotors();  break;
    default:            stopMotors();  break;
  }
}

void doExitBonus() {
  stopMotors();
  Serial.println("EXIT BONUS: lampeggio e halt.");
  blinkLED(BLINK_EXIT_INTV, BLINK_EXIT_MS);
  while (true) { delay(1000); } // halt forever
}

// End of firmware
