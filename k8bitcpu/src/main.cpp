#include <Arduino.h>

const char DATA[] = {12, 11, 10, 9, 8, 7, 6, 5};
#define CLOCK 3

#define OUTPUT_ENABLE 2 // if low, output

bool outputEnabled = false;
byte counter = 0;


byte readBits();
void printBits(unsigned int);
void updateOutputEnabled();
void onClock();

void setup() {
  Serial.begin(57600);
  Serial.println(F("RUNNING"));

  for (int i = 0; i < 8; ++i) {
      pinMode(DATA[i], INPUT);
  }
  updateOutputEnabled();

  pinMode(OUTPUT_ENABLE, INPUT_PULLUP);

  pinMode(CLOCK, INPUT);
  attachInterrupt(digitalPinToInterrupt(CLOCK), onClock, RISING);
}

void loop() {
  updateOutputEnabled();

}

byte readBits() {
  unsigned int data = 0;
  for (int i = 0; i < 8; ++i) {
    int bit = digitalRead(DATA[i]) ? 1 : 0;
    data = (data << 1) + bit;
  }
  return data;
}

void printBits(unsigned int data) {
  for (int i = 7; i >= 0; --i) {
    int bit = data >> i;  
    bit = bit & 1 ? 1 : 0;
    Serial.print(bit);
  }
}

void updateOutputEnabled() {
  int enabled = digitalRead(OUTPUT_ENABLE) ? 0 : 1;
  if (enabled != outputEnabled) {
    outputEnabled = enabled;
    uint8_t mode = enabled ? OUTPUT : INPUT;
    for (int i = 0; i < 8; ++i) {
      pinMode(DATA[i], mode);
    }
  }
}

void onClock() {
  ++counter;

  if (outputEnabled) {
    byte data = counter;
    printBits(data);
    for (int i = 7; i >= 0; --i) {
      digitalWrite(DATA[i], data & 1);
      data = data >> 1;
    }
    Serial.print(" w");
    Serial.println();
  }
  else {
    byte data = readBits();
    printBits(data);
    Serial.print(" r");
    Serial.println();
  }
}
