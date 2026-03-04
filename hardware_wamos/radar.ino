// radar.ino - HC-SR04 distance measurement with Arduino Nano
// Wiring:
// HC-SR04 VCC -> 5V
// HC-SR04 GND -> GND
// HC-SR04 TRIG -> D3
// HC-SR04 ECHO -> D2

const int trigPin = 3;
const int echoPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

float readDistanceCm() {
  // Ensure trigger is low
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Trigger pulse: HIGH for 10 us
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read echo pulse width (timeout to avoid hanging if no echo)
  unsigned long duration = pulseIn(echoPin, HIGH, 30000UL); // 30 ms timeout (~5m)

  if (duration == 0) {
    return -1.0; // indicates timeout / no reading
  }

  // Speed of sound: 343 m/s = 0.0343 cm/us
  // Distance = (duration * speed)/2
  float distanceCm = (duration * 0.0343f) / 2.0f;
  return distanceCm;
}

void loop() {
  float cm = readDistanceCm();

  if (cm < 0) {
    Serial.println("No echo (timeout). Check wiring / object range.");
  } else {
    float inches = cm / 2.54f;

    Serial.print("Distance: ");
    Serial.print(cm, 2);
    Serial.print(" cm  |  ");
    Serial.print(inches, 2);
    Serial.println(" in");
  }

  delay(250);
}