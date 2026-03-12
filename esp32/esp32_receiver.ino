/*
 * ESP32 Serial Receiver for RoboCup 2026
 * Receives letters (O, P, S) from Python wrapper via Serial
 */

#define BAUDRATE 115200

void setup() {
  // Inizializza la comunicazione seriale
  Serial.begin(BAUDRATE);
  while (!Serial) {
    ; // Attendi connessione seriale
  }
  
  Serial.println("ESP32 pronto a ricevere notifiche...");
  
  // Opzionale: Inizializza LED integrato per feedback visivo
  pinMode(2, OUTPUT); 
  digitalWrite(2, LOW);
}

void loop() {
  // Controlla se ci sono dati disponibili sulla seriale
  if (Serial.available() > 0) {
    // Leggi il carattere in arrivo
    char receivedChar = Serial.read();
    
    // Feedback visivo (flash LED)
    digitalWrite(2, HIGH);
    delay(100);
    digitalWrite(2, LOW);
    
    // Gestione delle lettere ricevute
    switch(receivedChar) {
      case 'O':
        Serial.println("Rilevato: OMEGA (O)");
        // Aggiungi qui l'azione per Omega
        break;
      case 'P':
        Serial.println("Rilevato: PHI (P)");
        // Aggiungi qui l'azione per Phi
        break;
      case 'S':
        Serial.println("Rilevato: PSI (S)");
        // Aggiungi qui l'azione per Psi
        break;
      case '0':
        Serial.println("Cerchio Rilevato: Valore 0 (STOP/LED)");
        break;
      case '1':
        Serial.println("Cerchio Rilevato: Valore 1 (1 KIT)");
        break;
      case '2':
        Serial.println("Cerchio Rilevato: Valore 2 (2 KIT)");
        break;
      default:
        Serial.print("Ricevuto carattere sconosciuto: ");
        Serial.println(receivedChar);
        break;
    }
  }
}
