#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>

const char* ssid = "iPhone di Riccardo";
const char* password = "Verstappen104";

// Pin Motori
const int motor1Pin1 = 27; 
const int motor1Pin2 = 26; 
const int motor2Pin1 = 25; 
const int motor2Pin2 = 33;

AsyncWebServer server(80);

void startServer() {
  server.on("/move", HTTP_GET, [](AsyncWebServerRequest *request){
    if (request->hasParam("dir")) {
      String command = request->getParam("dir")->value();
      Serial.println("Eseguo: " + command);
      
      if (command == "AVANTI") {
          digitalWrite(motor1Pin1, HIGH); digitalWrite(motor1Pin2, LOW);
          digitalWrite(motor2Pin1, HIGH); digitalWrite(motor2Pin2, LOW);
      } else if (command == "STOP") {
          digitalWrite(motor1Pin1, LOW); digitalWrite(motor1Pin2, LOW);
          digitalWrite(motor2Pin1, LOW); digitalWrite(motor2Pin2, LOW);
      }
      // Aggiungi qui Destra e Sinistra...

      request->send(200, "text/plain", "OK");
    }
  });

  server.begin();
  Serial.println(">>> Server Online!");
}

void setup() {
  Serial.begin(115200);

  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);

  // Forza la modalità Station e disabilita il risparmio energetico WiFi
  // che spesso causa disconnessioni sui robot
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false); 
  
  WiFi.begin(ssid, password);
  
  Serial.print("Connessione in corso");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nConnesso!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Aspettiamo che il sistema operativo (FreeRTOS) finisca le sue routine post-connessione
  delay(2000); 
  
  startServer();
}

void loop() {
  // Se perdi la connessione (es. ti allontani col telefono), prova a riconnettere
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi perso. Riconnessione...");
    WiFi.disconnect();
    WiFi.reconnect();
    delay(5000);
  }
}