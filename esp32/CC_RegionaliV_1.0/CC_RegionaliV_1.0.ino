/*
 * ============================================================
 *  ESP32 – Movimento 4 - Marzo 2026 _/Regionali\_
 *  Codice navigazione autonoma + gestione vittime
 * ============================================================
 *
 * REGOLE 2026 implementate:
 *  - Vittime lettera: Φ (Harmed), Ψ (Stable), Ω (Unharmed)
 *  - Cognitive targets: cerchi colorati, somma anelli 0/1/2
 *  - Fake target (somma diverso da 0,1,2): ignorati
 *  - Identificazione: fermo se a meno di 15cm, LED blink 500ms ON/OFF per 5s
 *  - Rescue kit: Harmed→2 kit (30pt), Stable→1 kit (10pt), Unharmed→0 kit
 *  - Max kit caricabili: 8
 *  - Exit bonus: blink 1s ON/OFF per almeno 10s, poi stop
 *  - Blue tile: rilevata da TCS34725, robot fermo 5s poi riparte
 *  - Black tile: rilevata da TCS34725, robot si ferma (LoP)
 *  - Silver tile: rilevata da TCS34725, checkpoint segnalato a Rasp
 *  - Red tile:   rilevata da TCS34725, ingresso Dangerous Zone
 *
 * PROTOCOLLO SERIALE (Raspberry Pi → ESP32, Serial1 115200 baud):
 *  'P'  – Harmed letter victim (Φ): blink 5s + 2 rescue kit
 *  'S'  – Stable letter victim (Ψ): blink 5s + 1 rescue kit
 *  'O'  – Unharmed letter victim (Ω): blink 5s + 0 kit
 *  '2'  – Cognitive target Harmed (somma=2): blink 5s + 2 rescue kit
 *  '1'  – Cognitive target Stable (somma=1): blink 5s + 1 rescue kit
 *  '0'  – Cognitive target Unharmed (somma=0): blink 5s + 0 kit
 *  'B'  – Blue tile (fallback da Rasp, gestita anche autonomamente)
 *  'E'  – Exit bonus: blink 1s ON/OFF piu di 10s poi halt
 *
 * PROTOCOLLO SERIALE (ESP32 → Raspberry Pi, Serial1):
 *  'b'  – Blue tile rilevata (ESP32 ha gia fatto stop 5s)
 *  'k'  – Black tile rilevata (LoP: robot fermo)
 *  'v'  – Silver tile/checkpoint rilevata
 *  'r'  – Red tile rilevata (ingresso Dangerous Zone)
 *
 * PIN MAP:
 *  Motore A:           pin1=2, pin2=4
 *  Motore B:           pin3=16, pin4=17
 *  Laser FRONT XSHUT: 23   ──┐
 *  Laser BACK  XSHUT: 18   ──┤  tutti su Wire1 (SDA=26, SCL=25)
 *  Laser LEFT  XSHUT: 33   ──┤  con indirizzi I2C separati via XSHUT
 *  Laser RIGHT XSHUT: 19   ──┘
 *  Servo kit:          15  (0°=riposo, 180°=espulsione)
 *  LED vittima:        32  (SOLO per segnalazione vittime/exit)
 *  TCS34725 SDA:       26  (Wire1)
 *  TCS34725 SCL:       25  (Wire1)
 *  TCS34725 LED EN:    32  (stesso pin LED vittima, nessun conflitto)
 *  Serial1 Rasp:       TX=1, RX=3
 *
 * NOTA PIN 2: LED integrato ESP32 condivide pin 2 con Motore A.
 *             Non usare LED_BUILTIN.
 *
 * LIBRERIE NECESSARIE (Arduino IDE Library Manager):
 *  - Adafruit VL53L0X  (by Adafruit)
 *  - Adafruit TCS34725 (by Adafruit)
 *  - ESP32Servo
 *
 * INDIRIZZI I2C assegnati ai laser in setup():
 *  FRONT = 0x30
 *  BACK  = 0x31
 *  LEFT  = 0x32
 *  RIGHT = 0x33
 * ============================================================
 */

#include <Wire.h>
#include <Adafruit_VL53L0X.h>
#include <Adafruit_TCS34725.h>
#include <ESP32Servo.h>

// ── PIN Motori ────────────────────────────────────────────────
const int pin1 = 2;
const int pin2 = 4;
const int pin3 = 16;
const int pin4 = 17;

// ── PIN XSHUT laser (= pin di attivazione) ────────────────────
const int XSHUT_FRONT = 23;
const int XSHUT_BACK  = 18;
const int XSHUT_LEFT  = 33;
const int XSHUT_RIGHT = 19;

// Indirizzi I2C custom (qualsiasi valore libero != 0x29 e != 0x29 TCS)
const uint8_t ADDR_FRONT = 0x30;
const uint8_t ADDR_BACK  = 0x31;
const uint8_t ADDR_LEFT  = 0x32;
const uint8_t ADDR_RIGHT = 0x33;

// ── PIN Servo e LED ───────────────────────────────────────────
const int SERVO_PIN = 15;
const int LED_PIN   = 32;   // LED vittima + LED enable TCS34725

// ── PIN TCS34725 (Wire1) ──────────────────────────────────────
const int TCS_SDA = 26;
const int TCS_SCL = 25;

// ── Costanti ──────────────────────────────────────────────────
const int  DIST_THRESHOLD_CM = 15;
const int  TURN_DELAY_MS     = 500;
const long BLINK_VICTIM_MS   = 5000;
const long BLINK_EXIT_MS     = 12000;
const int  BLINK_VICTIM_INTV = 500;
const int  BLINK_EXIT_INTV   = 1000;
const int  BLUE_STOP_MS      = 5000;
const int  MAX_RESCUE_KITS   = 8;

// ── Soglie colore TCS34725 (calibrare sul campo!) ─────────────
const float LUMA_BLACK_THR  =  300.0;
const float LUMA_SILVER_THR = 3000.0;
const float BLUE_NORM_THR   =   0.40;
const float RED_NORM_THR    =   0.45;

// ── Tipi tile ─────────────────────────────────────────────────
enum TileColor { TILE_NORMAL, TILE_BLACK, TILE_SILVER, TILE_BLUE, TILE_RED };

// ── Oggetti globali ───────────────────────────────────────────
Adafruit_VL53L0X laserFront;
Adafruit_VL53L0X laserBack;
Adafruit_VL53L0X laserLeft;
Adafruit_VL53L0X laserRight;

Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);
bool tcsOk = false;

Servo rescueServo;
int       kitCount = MAX_RESCUE_KITS;
TileColor lastTile = TILE_NORMAL;

// ═══════════════════════════════════════════════════════════════
//  INIZIALIZZAZIONE LASER VL53L0X
//
//  Tutti i sensori condividono Wire1 (SDA=26, SCL=25).
//  Procedura:
//   1. Porta tutti gli XSHUT LOW  → tutti i sensori spenti
//   2. Accendi un sensore alla volta (XSHUT HIGH)
//   3. Riassegnagli un indirizzo I2C unico
//   4. Passa al successivo
// ═══════════════════════════════════════════════════════════════
void initLasers() {
  // Step 1: spegni tutti i sensori tenendo XSHUT LOW
  pinMode(XSHUT_FRONT, OUTPUT); digitalWrite(XSHUT_FRONT, LOW);
  pinMode(XSHUT_BACK,  OUTPUT); digitalWrite(XSHUT_BACK,  LOW);
  pinMode(XSHUT_LEFT,  OUTPUT); digitalWrite(XSHUT_LEFT,  LOW);
  pinMode(XSHUT_RIGHT, OUTPUT); digitalWrite(XSHUT_RIGHT, LOW);
  delay(10);

  // Step 2+3: accendi e riassegna FRONT
  digitalWrite(XSHUT_FRONT, HIGH);
  delay(10);
  if (!laserFront.begin(ADDR_FRONT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X FRONT non trovato!");
  } else {
    Serial.println("VL53L0X FRONT OK (0x30)");
  }

  // Step 2+3: accendi e riassegna BACK
  digitalWrite(XSHUT_BACK, HIGH);
  delay(10);
  if (!laserBack.begin(ADDR_BACK, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X BACK non trovato!");
  } else {
    Serial.println("VL53L0X BACK  OK (0x31)");
  }

  // Step 2+3: accendi e riassegna LEFT
  digitalWrite(XSHUT_LEFT, HIGH);
  delay(10);
  if (!laserLeft.begin(ADDR_LEFT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X LEFT non trovato!");
  } else {
    Serial.println("VL53L0X LEFT  OK (0x32)");
  }

  // Step 2+3: accendi e riassegna RIGHT
  digitalWrite(XSHUT_RIGHT, HIGH);
  delay(10);
  if (!laserRight.begin(ADDR_RIGHT, false, &Wire1)) {
    Serial.println("ERRORE: VL53L0X RIGHT non trovato!");
  } else {
    Serial.println("VL53L0X RIGHT OK (0x33)");
  }
}

// ═══════════════════════════════════════════════════════════════
//  LETTURA DISTANZA VL53L0X
//  Restituisce la distanza in cm.
//  Se la lettura non e' valida restituisce 999 (via libera).
// ═══════════════════════════════════════════════════════════════
int readDistance(Adafruit_VL53L0X &sensor) {
  VL53L0X_RangingMeasurementData_t measure;
  sensor.rangingTest(&measure, false);
  if (measure.RangeStatus != 4) {          // 4 = out of range / errore
    return measure.RangeMilliMeter / 10;   // mm → cm
  }
  return 999;  // nessun ostacolo rilevato
}

// ═══════════════════════════════════════════════════════════════
//  MOTORI
// ═══════════════════════════════════════════════════════════════
void motorForward() {
  digitalWrite(pin1, HIGH); digitalWrite(pin2, LOW);
  digitalWrite(pin3, HIGH); digitalWrite(pin4, LOW);
}

void motorStop() {
  digitalWrite(pin1, LOW); digitalWrite(pin2, LOW);
  digitalWrite(pin3, LOW); digitalWrite(pin4, LOW);
}

void turnRight() {
  motorStop();
  delay(50);
  digitalWrite(pin1, HIGH); digitalWrite(pin2, LOW);
  digitalWrite(pin3, LOW);  digitalWrite(pin4, HIGH);
  delay(TURN_DELAY_MS);
  motorForward();
}

void turnLeft() {
  motorStop();
  delay(50);
  digitalWrite(pin1, LOW);  digitalWrite(pin2, HIGH);
  digitalWrite(pin3, HIGH); digitalWrite(pin4, LOW);
  delay(TURN_DELAY_MS);
  motorForward();
}

// ═══════════════════════════════════════════════════════════════
//  LED BLINK
// ═══════════════════════════════════════════════════════════════
void blinkLED(int interval_ms, long duration_ms) {
  motorStop();
  unsigned long start = millis();
  bool state = true;
  digitalWrite(LED_PIN, HIGH);
  while (millis() - start < (unsigned long)duration_ms) {
    digitalWrite(LED_PIN, state ? HIGH : LOW);
    delay(interval_ms);
    state = !state;
  }
  digitalWrite(LED_PIN, LOW);
}

// ═══════════════════════════════════════════════════════════════
//  DEPLOY RESCUE KIT
// ═══════════════════════════════════════════════════════════════
void deployRescueKit() {
  if (kitCount <= 0) {
    Serial.println("ATTENZIONE: kit esauriti!");
    return;
  }
  motorStop();
  rescueServo.attach(SERVO_PIN);
  rescueServo.write(180);
  delay(1000);
  rescueServo.write(0);
  delay(1000);
  rescueServo.detach();
  kitCount--;
  Serial.print("Kit rilasciato. Rimanenti: ");
  Serial.println(kitCount);
}

// ═══════════════════════════════════════════════════════════════
//  GESTIONE VITTIMA
//  status: 0=Unharmed, 1=Stable, 2=Harmed
// ═══════════════════════════════════════════════════════════════
void handleVictim(int status) {
  blinkLED(BLINK_VICTIM_INTV, BLINK_VICTIM_MS);
  if (status == 2) {
    deployRescueKit();
    delay(300);
    deployRescueKit();
  } else if (status == 1) {
    deployRescueKit();
  }
  motorForward();
}

// ═══════════════════════════════════════════════════════════════
//  LETTURA COLORE TILE – TCS34725
//  Pin 32 usato come LED enable: acceso 60ms per la lettura,
//  poi spento. Non si sovrappone mai a blinkLED().
// ═══════════════════════════════════════════════════════════════
TileColor readTileColor() {
  if (!tcsOk) return TILE_NORMAL;

  digitalWrite(LED_PIN, HIGH);
  delay(60);

  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  digitalWrite(LED_PIN, LOW);

  if (c == 0) return TILE_NORMAL;

  float lux   = tcs.calculateLux(r, g, b);
  float total = (float)(r + g + b);
  if (total == 0) return TILE_NORMAL;

  float r_n = r / total;
  float g_n = g / total;
  float b_n = b / total;

  // Debug – commenta in gara
  Serial.print("[TCS] lux="); Serial.print(lux, 0);
  Serial.print("  r="); Serial.print(r_n, 2);
  Serial.print("  g="); Serial.print(g_n, 2);
  Serial.print("  b="); Serial.println(b_n, 2);

  if (lux < LUMA_BLACK_THR) return TILE_BLACK;
  if (lux > LUMA_SILVER_THR) return TILE_SILVER;
  if (b_n > BLUE_NORM_THR && b_n > r_n && b_n > g_n) return TILE_BLUE;
  if (r_n > RED_NORM_THR  && r_n > g_n && r_n > b_n) return TILE_RED;
  return TILE_NORMAL;
}

// ═══════════════════════════════════════════════════════════════
//  GESTIONE TILE COLORATA
// ═══════════════════════════════════════════════════════════════
void handleTileColor(TileColor tile) {
  if (tile == lastTile) return;
  lastTile = tile;

  switch (tile) {
    case TILE_BLACK:
      motorStop();
      Serial.println("[TILE] NERO – LoP!");
      Serial1.write('k');
      break;
    case TILE_SILVER:
      Serial.println("[TILE] ARGENTO – Checkpoint");
      Serial1.write('v');
      break;
    case TILE_BLUE:
      motorStop();
      Serial.println("[TILE] BLU – attendo 5s");
      Serial1.write('b');
      delay(BLUE_STOP_MS);
      motorForward();
      break;
    case TILE_RED:
      Serial.println("[TILE] ROSSO – Dangerous Zone");
      Serial1.write('r');
      break;
    case TILE_NORMAL:
    default:
      break;
  }
}

// ═══════════════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, 3, 1);  // Rasp: RX=3, TX=1

  // Motori
  pinMode(pin1, OUTPUT); pinMode(pin2, OUTPUT);
  pinMode(pin3, OUTPUT); pinMode(pin4, OUTPUT);

  // LED pin 32
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Bus I2C secondario (tutti i sensori: 4x VL53L0X + TCS34725)
  Wire1.begin(TCS_SDA, TCS_SCL);

  // TCS34725
  tcsOk = tcs.begin(TCS34725_ADDRESS, &Wire1);
  if (!tcsOk) Serial.println("ERRORE: TCS34725 non trovato!");
  else        Serial.println("TCS34725 OK.");

  // VL53L0X x4 (procedura XSHUT per indirizzi separati)
  initLasers();

  // Servo in posizione iniziale
  rescueServo.attach(SERVO_PIN);
  rescueServo.write(0);
  delay(500);
  rescueServo.detach();

  motorForward();
  Serial.println("=== RoboCup 2026 – Robot M4_V1 avviato ===");
  Serial.print("Kit caricati: "); Serial.println(kitCount);
}

// ═══════════════════════════════════════════════════════════════
//  LOOP PRINCIPALE
// ═══════════════════════════════════════════════════════════════
void loop() {

  // ── 1. Lettura colore pavimento ───────────────────────────────
  TileColor currentTile = readTileColor();
  handleTileColor(currentTile);

  // Tile nera: robot fermo, aspetta solo 'E' dal Rasp
  if (currentTile == TILE_BLACK) {
    if (Serial1.available() > 0) {
      char cmd = Serial1.read();
      if (cmd == 'E') {
        motorStop();
        blinkLED(BLINK_EXIT_INTV, BLINK_EXIT_MS);
        while (true) { delay(1000); }
      }
    }
    delay(100);
    return;
  }

  // ── 2. Comandi dal Raspberry Pi ──────────────────────────────
  if (Serial1.available() > 0) {
    char cmd = Serial1.read();
    Serial.print("[CMD] "); Serial.println(cmd);

    switch (cmd) {
      case 'P':  handleVictim(2); break;   // Φ Harmed   → 2 kit
      case 'S':  handleVictim(1); break;   // Ψ Stable   → 1 kit
      case 'O':  handleVictim(0); break;   // Ω Unharmed → 0 kit
      case '2':  handleVictim(2); break;   // Cognitive Harmed
      case '1':  handleVictim(1); break;   // Cognitive Stable
      case '0':  handleVictim(0); break;   // Cognitive Unharmed
      case 'B':
        motorStop();
        Serial.println("Blue tile (da Rasp): attendo 5s");
        delay(BLUE_STOP_MS);
        motorForward();
        break;
      case 'E':
        motorStop();
        Serial.println("EXIT BONUS: lampeggio e halt.");
        blinkLED(BLINK_EXIT_INTV, BLINK_EXIT_MS);
        while (true) { delay(1000); }
        break;
      default:
        Serial.print("[WARN] Comando sconosciuto: ");
        Serial.println(cmd);
        break;
    }
  }

  // ── 3. Navigazione autonoma ───────────────────────────────────
  int distFront = readDistance(laserFront);

  if (distFront <= DIST_THRESHOLD_CM) {
    motorStop();
    delay(100);
    int distLeft  = readDistance(laserLeft);
    int distRight = readDistance(laserRight);

    Serial.print("[NAV] Ostacolo: SX=");
    Serial.print(distLeft);
    Serial.print(" DX=");
    Serial.println(distRight);

    if (distLeft > distRight) turnLeft();
    else                      turnRight();

  } else {
    motorForward();
  }

  delay(50);
}

//   -----------------------------------------------------------------------------------------------------------
//  |Movimento 4 2026 - Balsamo Alessandro, Bono' Valentina, Bortolato Nicola, Brusegan Samuele, Tonini Riccardo|
//   -----------------------------------------------------------------------------------------------------------
