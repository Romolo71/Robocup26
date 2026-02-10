// Definizione PIN Motore A
const int motor1Pin1 = 2; 
const int motor1Pin2 = 4; 

// Definizione PIN Motore B
const int motor2Pin1 = 16; 
const int motor2Pin2 = 17; 

void setup() {
  // Configura i pin come output
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);
  
  Serial.begin(115200);
}

void loop() {
  Serial.println("Avanti...");
  muoviAvanti();
  delay(2000);

  Serial.println("Indietro...");
  muoviIndietro();
  delay(2000);

  Serial.println("Stop.");
  fermaMotori();
  delay(2000);
}

void muoviAvanti() {
  digitalWrite(motor1Pin1, HIGH);
  digitalWrite(motor1Pin2, LOW);
  digitalWrite(motor2Pin1, HIGH);
  digitalWrite(motor2Pin2, LOW);
}

void muoviIndietro() {
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, HIGH);
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, HIGH);
}

void fermaMotori() {
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, LOW);
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, LOW);
}