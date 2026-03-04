#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#define SSID     "MonaConnect"
#define PASSWORD ""

#define HOST_IP   "172.16.192.15"
#define HOST_PORT 8080

String jsonBuf;
bool capturingJson = false;
int braceDepth = 0;
unsigned long lastJsonByteMs = 0;

// LED on D1 mini is active-LOW
void ledOn()  { digitalWrite(LED_BUILTIN, LOW); }
void ledOff() { digitalWrite(LED_BUILTIN, HIGH); }

// Heartbeat: toggles every 500ms regardless of POST
unsigned long lastBeat = 0;
void heartbeat() {
  if (millis() - lastBeat >= 500) {
    lastBeat = millis();
    static bool on = false;
    on = !on;
    if (on) ledOn(); else ledOff();
  }
}

bool looksLikeRadarJson(const String& s) {
  return s.startsWith("{") &&
         s.endsWith("}") &&
         s.indexOf("\"id\"") >= 0 &&
         s.indexOf("\"type\"") >= 0 &&
         s.indexOf("\"radar\"") >= 0 &&
         s.indexOf("\"waterheight\"") >= 0 &&
         s.indexOf("\"reserve\"") >= 0 &&
         s.indexOf("\"percentage\"") >= 0;
}

void blink(int n) {
  for (int i = 0; i < n; i++) {
    ledOn();  delay(80);
    ledOff(); delay(120);
  }
}

void wifiEnsure() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);

  Serial.println("D1: WIFI_CONNECTING");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
    blink(1);
    delay(300);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("D1: WIFI_OK IP=");
    Serial.println(WiFi.localIP());
    blink(3);
  } else {
    Serial.println("D1: WIFI_FAIL");
    blink(5);
  }
}

void postJson(const String& payload) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("D1: NO_WIFI");
    return;
  }

  WiFiClient client;
  HTTPClient http;

  // begin(host, port, uri)
  if (!http.begin(client, HOST_IP, HOST_PORT, "/api/update")) {
    Serial.println("D1: HTTP_BEGIN_FAIL");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);
  String resp = http.getString();
  http.end();

  Serial.print("D1: POST_CODE=");
  Serial.println(code);
  Serial.print("D1: RESP=");
  Serial.println(resp);

  if (code == 200) blink(1);
  else blink(2);

}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  ledOff();

  Serial.begin(9600);          // MUST match Nano esp.begin(9600)
  Serial.println("D1: BOOT");  // this will go to Nano (not PC) in Circuit A

  wifiEnsure();
}

void loop() {
  heartbeat();
  wifiEnsure();

  if (capturingJson && (millis() - lastJsonByteMs > 250)) {
    Serial.println("D1: DROP_PARTIAL_FRAME");
    jsonBuf = "";
    capturingJson = false;
    braceDepth = 0;
  }

  // Read serial stream and extract complete JSON objects by braces.
  while (Serial.available()) {
    char c = (char)Serial.read();
    lastJsonByteMs = millis();

    if (!capturingJson) {
      if (c == '{') {
        capturingJson = true;
        braceDepth = 1;
        jsonBuf = "{";
      }
      continue;
    }

    jsonBuf += c;
    if (c == '{') braceDepth++;
    if (c == '}') braceDepth--;

    if (jsonBuf.length() > 500) {
      Serial.println("D1: SKIP_OVERSIZE_FRAME");
      Serial.println("D1:OK");
      jsonBuf = "";
      capturingJson = false;
      braceDepth = 0;
      continue;
    }

    if (braceDepth == 0) {
      jsonBuf.trim();
      Serial.print("D1: RX_LEN=");
      Serial.println(jsonBuf.length());
      if (looksLikeRadarJson(jsonBuf)) {
        postJson(jsonBuf);
      } else {
        Serial.print("D1: SKIP_BAD_FRAME=");
        Serial.println(jsonBuf);
      }
      Serial.println("D1:OK");
      jsonBuf = "";
      capturingJson = false;
    }
  }
}
