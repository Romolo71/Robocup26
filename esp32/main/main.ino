#include <WiFi.h>
#include <WebServer.h>

// Sostituisci con i dati della tua rete
const char* ssid = "iPhone di Riccardo";
const char* password = "Verstappen104";

// Web server sulla porta 80
WebServer server(80);

// Pin del LED (GPIO 2 è solitamente il LED integrato)
const int ledPin = 2;

// Gestione della pagina principale


void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

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
  });
  server.on("/move-bkw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Indietro', 'command':'indietro'}");
    Serial.println("HTTP LOG: indietro");
    // go indietro
  });
  server.on("/turn-cw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. orario', 'command':'turn-cw'}");
    Serial.println("HTTP LOG: turn-cw");
    // turn-cw
  });
  server.on("/turn-ccw", []() {
    server.send(200, "application/json", "{'text':'Command Confirmed: Giro s. anti-orario', 'command':'turn-ccw'}");
    Serial.println("HTTP LOG: turn-ccw");
    // turn-cw
  });

  server.begin();
  Serial.println("HTTP server attivo");
}

void loop() {
  server.handleClient();
}
