#include <WiFi.h>
#include <WebServer.h>

// Sostituisci con i dati della tua rete (dal file .env se disponibile)
#include "wifi_secrets.h"
const char* ssid = WIFI_SSID;
const char* password = WIFI_PSWD;

// Definizione PIN Motore A
const int pin1 = 2; 
const int pin2 = 4; 

// Definizione PIN Motore B
const int pin3 = 16; 
const int pin4 = 17;

// version 2 of the motor driver
// const int ch1=0;
// const int ch2=1;
// const int ch3=2;
// const int ch4=3;

// version 3 of the motor driver
// const int ch1=pin1;
// const int ch2=pin2;
// const int ch3=pin3;
// const int ch4=pin4;

const int freq=5000;
const int resolution=8;

// Web server sulla porta 80
WebServer server(80);

// Pin del LED (GPIO 2 è solitamente il LED integrato)
const int ledPin = 2;

// Detailed PWM Speed values for each direction
int fwdA = 255, fwdB = 255;
int bkwA = 255, bkwB = 255;
int cwA = 200,  cwB = 200;
int ccwA = 200, ccwB = 200;

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  // If you use version 2 of the motor driver, uncomment the following lines:
  // ledcSetup(ch1,freq,resolution);
  // ledcSetup(ch2,freq,resolution);
  // ledcSetup(ch3,freq,resolution);
  // ledcSetup(ch4,freq,resolution);
  // ledcAttachPin(pin1,ch1);
  // ledcAttachPin(pin2,ch2);
  // ledcAttachPin(pin3,ch3);
  // ledcAttachPin(pin4,ch4);

  // If you use version 3 of the motor driver, uncomment the following lines:
  // ledcAttach(pin1,freq,resolution);
  // ledcAttach(pin2,freq,resolution);
  // ledcAttach(pin3,freq,resolution);
  // ledcAttach(pin4,freq,resolution);

  // Connessione Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    //Serial.print(".");
    switch (WiFi.status()) {
      case WL_IDLE_STATUS:
        Serial.println("WL_IDLE_STATUS");
        break;
      case WL_NO_SSID_AVAIL:
        Serial.println("WL_NO_SSID_AVAIL");
        break;
      case WL_SCAN_COMPLETED:
        Serial.println("WL_SCAN_COMPLETED");
        break;
      case WL_CONNECTED:
        Serial.println("WL_CONNECTED");
        break;
      case WL_CONNECT_FAILED:
        Serial.println("WL_CONNECT_FAILED");
        break;
      case WL_CONNECTION_LOST:
        Serial.println("WL_CONNECTION_LOST");
        break;
      case WL_DISCONNECTED:
        Serial.println("WL_DISCONNECTED");
        break;
    }
  }
  Serial.println("");
  Serial.println("Wi-Fi connesso");
  Serial.println("Indirizzo IP: ");
  Serial.println(WiFi.localIP());

  // Gestione globale per le richieste pre-flight CORS
  server.onNotFound([]() {
    if (server.method() == HTTP_OPTIONS) {
      server.sendHeader("Access-Control-Allow-Origin", "*");
      server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
      server.sendHeader("Access-Control-Allow-Headers", "*");
      server.send(204);
    } else {
      server.send(404, "text/plain", "Not Found");
    }
  });

  /* Movement */
  server.on("/move-fwd", []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{'text':'Command Confirmed: Avanti', 'command':'avanti'}");
    Serial.println("HTTP LOG: avanti");
    // go avanti
    move(0);
  });
  server.on("/move-bkw", []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{'text':'Command Confirmed: Indietro', 'command':'indietro'}");
    Serial.println("HTTP LOG: indietro");
    // go indietro
    move(1);
  });
  server.on("/turn-cw", []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. orario', 'command':'turn-cw'}");
    Serial.println("HTTP LOG: turn-cw");
    // turn-cw
    move(2);
  });
  server.on("/turn-ccw", []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. anti-orario', 'command':'turn-ccw'}");
    Serial.println("HTTP LOG: turn-ccw");
    // turn-cw
    move(3);
  });
  server.on("/stop", []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{'text':'Command Confirmed: Stop', 'command':'stop'}");
    Serial.println("HTTP LOG: stop");
    // stop
    move(4);
  });

  server.on("/update", []() {
    if (server.hasArg("fwdA")) fwdA = server.arg("fwdA").toInt();
    if (server.hasArg("fwdB")) fwdB = server.arg("fwdB").toInt();
    if (server.hasArg("bkwA")) bkwA = server.arg("bkwA").toInt();
    if (server.hasArg("bkwB")) bkwB = server.arg("bkwB").toInt();
    if (server.hasArg("cwA"))  cwA  = server.arg("cwA").toInt();
    if (server.hasArg("cwB"))  cwB  = server.arg("cwB").toInt();
    if (server.hasArg("ccwA")) ccwA = server.arg("ccwA").toInt();
    if (server.hasArg("ccwB")) ccwB = server.arg("ccwB").toInt();
    
    String response = "{\"status\":\"ok\", \"fwd\":[" + String(fwdA) + "," + String(fwdB) + "], \"bkw\":[" + String(bkwA) + "," + String(bkwB) + "]}";
    server.send(200, "application/json", response);
    Serial.println("HTTP LOG: Calibration updated");
  });

  server.begin();
  Serial.println("HTTP server attivo");
}

void loop() {
  server.handleClient();
}

void move(int direction) {
  switch (direction) {
    case 0: // avanti
      ledcWrite(ch1, 0);
      ledcWrite(ch2, fwdA);
      ledcWrite(ch3, 0);
      ledcWrite(ch4, fwdB);
      break;
    case 1: // indietro
      ledcWrite(ch1, bkwA);
      ledcWrite(ch2, 0);
      ledcWrite(ch3, bkwB);
      ledcWrite(ch4, 0);
      break;
    case 2: // destra (Giro orario)
      ledcWrite(ch1, cwA);
      ledcWrite(ch2, 0);
      ledcWrite(ch3, 0);
      ledcWrite(ch4, cwB);
      break;
    case 3: // sinistra (Giro anti-orario)
      ledcWrite(ch1, 0);
      ledcWrite(ch2, ccwA);
      ledcWrite(ch3, ccwB);
      ledcWrite(ch4, 0);
      break;
    case 4: // stop
      ledcWrite(ch1, 0);
      ledcWrite(ch2, 0);
      ledcWrite(ch3, 0);
      ledcWrite(ch4, 0);
      break;
    default:
      break;
  }
}