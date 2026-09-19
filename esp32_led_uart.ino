#include <Arduino.h>

// ---------- CONFIG ----------
#define LED_PIN 2          // Built-in LED on most ESP32 dev boards
#define BAUD_RATE 115200
// ----------------------------

String buffer = "";

void setup() {
  Serial.begin(BAUD_RATE);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);   // start with LED off

  delay(500);
  Serial.println("ESP32 ready. Send ON or OFF.");
}

void loop() {
  // Read incoming characters one by one
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        handleCommand(buffer);
        buffer = "";
      }
    } else {
      buffer += c;
    }
  }

  // (optional) Send a heartbeat every 5 seconds
  // static unsigned long lastBeat = 0;
  // if (millis() - lastBeat > 5000) {
  //   lastBeat = millis();
  //   Serial.println("alive");
  // }
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "ON") {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("LED is ON");
  }
  else if (cmd == "OFF") {
    digitalWrite(LED_PIN, LOW);
    Serial.println("LED is OFF");
  }
  else if (cmd == "STATUS") {
    Serial.print("LED state: ");
    Serial.println(digitalRead(LED_PIN) ? "ON" : "OFF");
  }
  else {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}
