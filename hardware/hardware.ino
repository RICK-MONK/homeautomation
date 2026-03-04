//##################################################################################################################
//##                                      ELET2415 AUTHENTICATION TFT CODE                                       ##
//##################################################################################################################

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include "Adafruit_GFX.h"
#include "Adafruit_ILI9341.h"

// IMPORT IMAGES
#include "lockclose.h"
#include "lockopen.h"

// IMPORT FONTS
#include <Fonts/FreeSansBold18pt7b.h>
#include <Fonts/FreeSansBold9pt7b.h>

// TFT PINS
#define TFT_DC    17
#define TFT_CS    5
#define TFT_RST   16
#define TFT_CLK   18
#define TFT_MOSI  23
#define TFT_MISO  19

// BUTTONS + POT
#define button1   32   // select next digit
#define button2   33   // submit/check
#define button3   25   // force lock closed / reset lock state
#define AD0       36   // potentiometer middle pin

// WIFI
const char* ssid     = "MonaConnect";
const char* password = "";

// Backend aligned with the rest of this project
const char* BACKEND_URL = "http://172.16.192.15:8080/api/check/combination";

// TFT OBJECT
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_MOSI, TFT_CLK, TFT_RST, TFT_MISO);

// APP STATE
uint8_t currentDigit = 1;
bool lockState = false;

uint8_t first  = 0;
uint8_t second = 0;
uint8_t third  = 0;
uint8_t fourth = 0;

// DIGIT BOX LAYOUT
const int DIG_W = 34;
const int DIG_H = 40;
const int DIG_R = 6;
const int DIG_Y = 255;
const int DIG_X[4] = {34, 80, 126, 172};

// redraw guards
int lastDrawnDigits[4] = {-1, -1, -1, -1};
bool lastLockState = false;
bool firstLockDraw = true;

// button debounce
int prevB1 = HIGH, prevB2 = HIGH, prevB3 = HIGH;
unsigned long lastB1Time = 0;
unsigned long lastB2Time = 0;
unsigned long lastB3Time = 0;
const unsigned long debounceMs = 220;

// prototypes
void connectWiFi();
void configurePins();
void drawStaticUI();
void drawAllDigits();
void drawDigitBox(uint8_t index, uint8_t value);
void digit1(uint8_t number);
void digit2(uint8_t number);
void digit3(uint8_t number);
void digit4(uint8_t number);
void showLockState();
void checkPasscode();
uint8_t readPotDigit();
void handleButtons();
void clearStatusArea();

void setup() {
  Serial.begin(115200);

  configurePins();

  tft.begin();
  tft.setRotation(0);               // portrait
  tft.fillScreen(ILI9341_WHITE);

  drawStaticUI();
  drawAllDigits();
  showLockState();

  connectWiFi();
}

void loop() {
  handleButtons();

  uint8_t d = readPotDigit();

  switch (currentDigit) {
    case 1:
      if (d != first) {
        first = d;
        digit1(first);
      }
      break;

    case 2:
      if (d != second) {
        second = d;
        digit2(second);
      }
      break;

    case 3:
      if (d != third) {
        third = d;
        digit3(third);
      }
      break;

    case 4:
      if (d != fourth) {
        fourth = d;
        digit4(fourth);
      }
      break;
  }

  delay(40);
}

void configurePins() {
  pinMode(button1, INPUT_PULLUP);
  pinMode(button2, INPUT_PULLUP);
  pinMode(button3, INPUT_PULLUP);
  pinMode(AD0, INPUT);
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi connected. IP = ");
  Serial.println(WiFi.localIP());
}

uint8_t readPotDigit() {
  long total = 0;
  for (int i = 0; i < 8; i++) {
    total += analogRead(AD0);
    delay(2);
  }

  int raw = total / 8;
  uint8_t d = (uint8_t)map(raw, 0, 4095, 0, 9);

  if (d > 9) d = 9;
  return d;
}

void handleButtons() {
  int b1 = digitalRead(button1);
  int b2 = digitalRead(button2);
  int b3 = digitalRead(button3);

  unsigned long now = millis();

  // button1: next digit
  if (prevB1 == HIGH && b1 == LOW && (now - lastB1Time) > debounceMs) {
    lastB1Time = now;
    currentDigit++;
    if (currentDigit > 4) currentDigit = 1;
    Serial.print("Current digit = ");
    Serial.println(currentDigit);
  }

  // button2: submit/check
  if (prevB2 == HIGH && b2 == LOW && (now - lastB2Time) > debounceMs) {
    lastB2Time = now;
    checkPasscode();
  }

  // button3: force denied/locked
  if (prevB3 == HIGH && b3 == LOW && (now - lastB3Time) > debounceMs) {
    lastB3Time = now;
    lockState = false;
    showLockState();
  }

  prevB1 = b1;
  prevB2 = b2;
  prevB3 = b3;
}

void drawStaticUI() {
  // white background already drawn in setup

  // digit boxes are drawn by drawAllDigits()
  // lock/status drawn by showLockState()
}

void drawAllDigits() {
  digit1(first);
  digit2(second);
  digit3(third);
  digit4(fourth);
}

void drawDigitBox(uint8_t index, uint8_t value) {
  if (index > 3) return;
  if (lastDrawnDigits[index] == value) return;

  lastDrawnDigits[index] = value;

  int x = DIG_X[index];
  int y = DIG_Y;

  // redraw box
  tft.fillRoundRect(x, y, DIG_W, DIG_H, DIG_R, ILI9341_BLACK);

  // convert value to text
  char s[2];
  snprintf(s, sizeof(s), "%u", value);

  // font setup
  tft.setFont(&FreeSansBold18pt7b);
  tft.setTextSize(1);
  tft.setTextColor(ILI9341_BLUE);

  // center using text bounds
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(s, 0, 0, &x1, &y1, &w, &h);

  int16_t tx = x + (DIG_W - (int)w) / 2;
  int16_t ty = y + (DIG_H - (int)h) / 2;

  // cursor for GFX font is baseline-based
  tft.setCursor(tx - x1, ty - y1);
  tft.print(s);
}

void digit1(uint8_t number) { drawDigitBox(0, number); }
void digit2(uint8_t number) { drawDigitBox(1, number); }
void digit3(uint8_t number) { drawDigitBox(2, number); }
void digit4(uint8_t number) { drawDigitBox(3, number); }

void clearStatusArea() {
  // clear icon + message region only
  tft.fillRect(45, 5, 150, 120, ILI9341_WHITE);
  tft.fillRect(20, 180, 200, 35, ILI9341_WHITE);
}

void showLockState() {
  if (!firstLockDraw && lockState == lastLockState) return;

  firstLockDraw = false;
  lastLockState = lockState;

  clearStatusArea();

  tft.setFont(&FreeSansBold9pt7b);
  tft.setTextSize(1);

  if (lockState) {
    tft.drawRGBBitmap(68, 10, lockopen, 104, 97);

    tft.setCursor(50, 200);
    tft.setTextColor(ILI9341_GREEN);
    tft.print("Access Granted");
  } else {
    tft.drawRGBBitmap(68, 10, lockclose, 104, 103);

    tft.setCursor(50, 200);
    tft.setTextColor(ILI9341_RED);
    tft.print("Access Denied");
  }
}

void checkPasscode() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    lockState = false;
    showLockState();
    return;
  }

  WiFiClient client;
  HTTPClient http;

  http.begin(client, BACKEND_URL);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  char message[20] = {0};
  snprintf(message, sizeof(message), "passcode=%d%d%d%d", first, second, third, fourth);

  Serial.print("Sending passcode payload: ");
  Serial.println(message);

  int httpResponseCode = http.POST(message);

  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    String received = http.getString();
    Serial.print("HTTP Response body: ");
    Serial.println(received);

    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, received);

    if (!err) {
      const char* status = doc["status"] | "";
      const char* data = doc["data"] | "";

      // Accept either field so it matches your backend response shape.
      if (strcmp(status, "complete") == 0 || strcmp(data, "complete") == 0) {
        lockState = true;
      } else {
        lockState = false;
      }

      showLockState();
    } else {
      Serial.print("JSON parse failed: ");
      Serial.println(err.c_str());
      lockState = false;
      showLockState();
    }
  } else {
    Serial.print("HTTP POST failed, code: ");
    Serial.println(httpResponseCode);
    lockState = false;
    showLockState();
  }

  http.end();
}
