#include <WiFi.h>
#include <WebServer.h>

// Sostituisci con i dati della tua rete
const char* ssid = "iPhone di Riccardo";
const char* password = "Verstappen104";

// Definizione PIN Motore A
const int pin1 = 2; 
const int pin2 = 4; 

// Definizione PIN Motore B
const int pin3 = 16; 
const int pin4 = 17;

const int ch1=0;
const int ch2=1;
const int ch3=2;
const int ch4=3;

const int freq=5000;
const int resolution=8;

// Web server sulla porta 80
WebServer server(80);

// Pin del LED (GPIO 2 è solitamente il LED integrato)
const int ledPin = 2;

// Gestione della pagina principale


void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  ledcSetup(ch1,freq,resolution);
  ledcSetup(ch2,freq,resolution);
  ledcSetup(ch3,freq,resolution);
  ledcSetup(ch4,freq,resolution);

  ledcAttachPin(pin1,ch1);
  ledcAttachPin(pin2,ch2);
  ledcAttachPin(pin3,ch3);
  ledcAttachPin(pin4,ch4);

  // Connessione Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("Wi-Fi connesso");
  Serial.println("Indirizzo IP: ");
  Serial.println(WiFi.localIP());

  // Definizione dei percorsi del server
  server.on("/on", []() {
    digitalWrite(ledPin, HIGH);
    //server.sendHeader("Location", "/");
    server.send(200, "application/json", "{'text':'Command Confirmed: ON'}");
    Serial.println("HTTP LOG: ON");
  });
  server.on("/off", []() {
    digitalWrite(ledPin, LOW);
    //server.sendHeader("Location", "/");
    server.send(200, "application/json", "{'text':'Command Confirmed: OFF'}");
    Serial.println("HTTP LOG: OFF");
  });

  /* Movement */
  server.on("/move-fwd", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Avanti', 'command':'avanti'}");
    Serial.println("HTTP LOG: avanti");
    // go avanti
    move(0);
  });
  server.on("/move-bkw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Indietro', 'command':'indietro'}");
    Serial.println("HTTP LOG: indietro");
    // go indietro
    move(1);
  });
  server.on("/turn-cw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. orario', 'command':'turn-cw'}");
    Serial.println("HTTP LOG: turn-cw");
    // turn-cw
    move(2);
  });
  server.on("/turn-ccw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. anti-orario', 'command':'turn-ccw'}");
    Serial.println("HTTP LOG: turn-ccw");
    // turn-cw
    move(3);
  });
  server.on("/stop", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Stop', 'command':'stop'}");
    Serial.println("HTTP LOG: stop");
    // stop
    move(4);
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
      ledcWrite(ch2, 255);
      ledcWrite(ch3, 0);
      ledcWrite(ch4, 255);
      break;
    case 1: // indietro
      ledcWrite(ch1, 255);
      ledcWrite(ch2, 0);
      ledcWrite(ch3, 255);
      ledcWrite(ch4, 0);
      break;
    case 2: // destra
      
      break;
    case 3: // sinistra
      
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