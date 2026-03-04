#include <SoftwareSerial.h>
// IMPORT ALL REQUIRED LIBRARIES

#include <math.h>
#include <string.h>

//**********ENTER IP ADDRESS OF SERVER******************//

#define HOST_IP     "172.16.193.144"       // MUST BE YOUR PC LAN IP FOR ESP8266 (localhost points to the ESP itself, not your computer)
#define HOST_PORT   "8080"            // REPLACE WITH SERVER PORT (BACKEND FLASK API PORT)
#define route       "api/update"      // LEAVE UNCHANGED
#define idNumber    "620169874"       // REPLACE WITH YOUR ID NUMBER

// WIFI CREDENTIALS
#define SSID        "ARRIS-ED5E"      // "REPLACE WITH YOUR WIFI's SSID"
#define PASSWORD    "70DFF79FED5E"  // "REPLACE WITH YOUR WiFi's PASSWORD"

#define stay        100

//**********PIN DEFINITIONS******************//

#define espRX         10
#define espTX         11
#define espTimeout_ms 300
#define TRIG_PIN      3
#define ECHO_PIN      2

#define SENSOR_BASE_HEIGHT_IN 94.5f
#define MAX_WATER_HEIGHT_IN   77.763f
#define TANK_RADIUS_IN        30.75f
#define IN3_PER_GALLON        231.0f
#define CM_PER_INCH           2.54f
#define ULTRASONIC_TIMEOUT_US 30000UL

/* Declare your functions below */
float readDistanceCm();

SoftwareSerial esp(espRX, espTX);

void setup(){

  Serial.begin(115200);
  // Configure GPIO pins here
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  if(strcmp(HOST_IP, "localhost") == 0){
    Serial.println("WARNING: HOST_IP is localhost. Set HOST_IP to your PC LAN IPv4 (e.g. 192.168.x.x)");
  }

  espInit();

}

void loop(){

  // send updates with schema '{"id":"student_id","type":"ultrasonic","radar":0,"waterheight":0,"reserve":0,"percentage":0}'
  char json[200] = {0};
  float radarCm = readDistanceCm();
  float radarIn = 0.0f;
  float waterheight = 0.0f;
  float reserve = 0.0f;
  float percentage = 0.0f;

  if(radarCm > 0.0f){
    // Radar: sensor-to-water distance in inches.
    radarIn = radarCm / CM_PER_INCH;

    // Water height from tank base with only lower clamp to allow overflow behavior.
    waterheight = SENSOR_BASE_HEIGHT_IN - radarIn;
    if(waterheight < 0.0f){ waterheight = 0.0f; }

    // Reserve in gallons for cylindrical volume.
    reserve = (PI * TANK_RADIUS_IN * TANK_RADIUS_IN * waterheight) / IN3_PER_GALLON;

    // Fill percentage relative to the max calibrated water height.
    percentage = (waterheight / MAX_WATER_HEIGHT_IN) * 100.0f;
  }

  snprintf(
    json,
    sizeof(json),
    "{\"id\":\"%s\",\"type\":\"ultrasonic\",\"radar\":%.2f,\"waterheight\":%.2f,\"reserve\":%.2f,\"percentage\":%.2f}",
    idNumber,
    radarIn,
    waterheight,
    reserve,
    percentage
  );

  Serial.println(json);
  espUpdate(json);

  delay(1000);
}

void espUpdate(char mssg[]){
  esp.println(mssg);         // newline-terminated JSON
}

void espInit(){
  esp.begin(9600);           // stable for SoftwareSerial
  Serial.println("ESP link ready (serial forward mode)");
}

//***** Design and implement all util functions below ******
float readDistanceCm(){
  unsigned long durationUs = 0;

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  durationUs = pulseIn(ECHO_PIN, HIGH, ULTRASONIC_TIMEOUT_US);
  if(durationUs == 0){
    return -1.0f;
  }

  return (durationUs * 0.0343f) / 2.0f;
}
