#include <Arduino.h>

const uint8_t MQ135_PIN = A0;
const uint8_t RELAY_PIN = 8;

const unsigned long READ_INTERVAL_MS = 2000;

unsigned long lastReadMs = 0;
String serialBuffer;

void handleSerialCommand(const String &command) {
  if (command == "ON") {
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println(F("Relay: ON"));
  } else if (command == "OFF") {
    digitalWrite(RELAY_PIN, LOW);
    Serial.println(F("Relay: OFF"));
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n' || incoming == '\r') {
      if (serialBuffer.length() > 0) {
        handleSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += incoming;
    }
  }

  const unsigned long now = millis();
  if (now - lastReadMs >= READ_INTERVAL_MS) {
    lastReadMs = now;

    const int raw = analogRead(MQ135_PIN);
    Serial.println(raw);
  }
}
