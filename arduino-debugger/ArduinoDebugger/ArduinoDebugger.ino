const char OPCODE_PINS[] = { 31,33,35,37};
const char STEP_PINS[] = {39,41, 43};
const char DATA[] = {30,32,34,36,38,40,42,44};

#define CLOCK 2
#define ZERO_FLAG 49
#define CARRY_FLAG 47

char opcodes[4];
char steps[3];
char data[8];

static const char* const instructions[16][8] = {
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 0000 - NOP
  {"MI|CO", "RO|II|CE", "MI|IO", "RO|AI", "",            "", "", ""}, // 0001 - LDA
  {"MI|CO", "RO|II|CE", "MI|IO", "RO|BI", "AI|EO|FI",    "", "", ""}, // 0010 - ADD
  {"MI|CO", "RO|II|CE", "MI|IO", "RO|BI", "AI|EO|SU|FI", "", "", ""}, // 0011 - SUB
  {"MI|CO", "RO|II|CE", "MI|IO", "AO|RI", "",            "", "", ""}, // 0100 - STA
  {"MI|CO", "RO|II|CE", "IO|AI", "",      "",            "", "", ""}, // 0101 - LDI
  {"MI|CO", "RO|II|CE", "IO|J",  "",      "",            "", "", ""}, // 0110 - JMP
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 0111 - JCS
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1000 - JEQ
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1001 - OP9
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1010 - OP10
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1011 - OP11
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1100 - OP12
  {"MI|CO", "RO|II|CE", "",      "",      "",            "", "", ""}, // 1101 - OP13
  {"MI|CO", "RO|II|CE", "AO|OI", "",      "",            "", "", ""}, // 1110 - OUT
  {"MI|CO", "RO|II|CE", "HL",    "",      "",            "", "", ""}  // 1111 - HLT
};

static const char* opcodeMnemonics[] = {
  "NOP", "LDA", "ADD", "SUB", "STA", "LDI", "JMP", "JCS",
  "JEQ", "OP9", "OPA", "OPB", "OPC", "OPD", "OUT", "HLT"
};

void clockTick() {
  delayMicroseconds(10);
  int zero = digitalRead(ZERO_FLAG);
  int carry = digitalRead(CARRY_FLAG);
  int opcode = 0;
  for (int i = 0; i < 4; ++i) {
    opcodes[i] = digitalRead(OPCODE_PINS[i]);
    opcode = (opcode << 1) | opcodes[i];
  }

  int step = 0;
  for (int i = 0; i < 3; ++i) {
    steps[i] = digitalRead(STEP_PINS[i]);
    step = (step << 1) | steps[i];
  }

  for (int i = 0; i < 8; ++i) {
    data[i] = digitalRead(DATA[i]);
  }

  char controlWord[16];
  sprintf(controlWord, "%s", instructions[opcode][step]);

  char buf[150];
  sprintf(buf, "Z:%d C:%d OPCODE: %d%d%d%d %s Step:%d CW:%s D:%d%d%d%d%d%d%d%d", zero, carry, 
          opcodes[0], opcodes[1], opcodes[2], opcodes[3], opcodeMnemonics[opcode],
          step,
          controlWord,
          data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);

  Serial.println(buf);
}

void setup() {
  pinMode(CLOCK, INPUT);
  attachInterrupt(digitalPinToInterrupt(CLOCK), clockTick, RISING);

  pinMode(CARRY_FLAG, INPUT);
  for (int i = 0; i < 4; ++i) {
    pinMode(OPCODE_PINS[i], INPUT);
  }
  for (int i = 0; i < 3; ++i) {
    pinMode(STEP_PINS[i], INPUT);
  }

  for (int i = 0; i < 3; ++i) {
    pinMode(DATA[i], INPUT);
  }

  Serial.begin(57600);
}

void loop() {
}
