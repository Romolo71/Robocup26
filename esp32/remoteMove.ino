#include <WiFi.h>
#include <ESPAsyncWebServer.h>

// Inserisci i tuoi dati WiFi
const char* ssid = "IL_TUO_WIFI";
const char* password = "LA_TUA_PASSWORD";

AsyncWebServer server(80);

void setup() {
  Serial.begin(115200);

  // Configurazione PIN Motori (Esempio)
  pinMode(12, OUTPUT); // Avanti
  pinMode(13, OUTPUT); // Indietro

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connessione WiFi...");
  }
  
  Serial.print("Indirizzo IP dell'ESP32: ");
  Serial.println(WiFi.localIP());

  // Gestione della rotta /move?dir=...
  server.on("/move", HTTP_GET, [](AsyncWebServerRequest *request){
    if (request->hasParam("dir")) {
      String command = request->getParam("dir")->value();
      Serial.println("Comando ricevuto: " + command);

      if (command == "AVANTI") {
          digitalWrite(12, HIGH); digitalWrite(13, LOW);
      } else if (command == "STOP") {
          digitalWrite(12, LOW); digitalWrite(13, LOW);
      }
      // Aggiungi qui gli altri casi (INDIETRO, SINISTRA, DESTRA)
      
      request->send(200, "text/plain", "OK");
    }
  });

  server.begin();
}

void loop() {
  // Il server gira in background
}