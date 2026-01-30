#include <Stepper.h>

// Numero di passi per una rotazione completa del motore (per il 28BYJ-48 è solitamente 2048)
const int stepsPerRevolution = 2048;

// Inizializzazione della libreria sui pin specificati
// NOTA: L'ordine dei pin per molti motori unipolari deve essere (IN1, IN3, IN2, IN4)
// Quindi: Pin 2, Pin 16, Pin 4, Pin 17
Stepper myStepper(stepsPerRevolution, 2, 16, 4, 17);

void setup() {
  // Imposta la velocità in giri al minuto (RPM)
  myStepper.setSpeed(10); 
  Serial.begin(115200);
}

void loop() {
  // Rotazione in un senso
  Serial.println("Rotazione oraria...");
  myStepper.step(stepsPerRevolution);
  delay(1000);

  // Rotazione nel senso opposto
  Serial.println("Rotazione antioraria...");
  myStepper.step(-stepsPerRevolution);
  delay(1000);
}