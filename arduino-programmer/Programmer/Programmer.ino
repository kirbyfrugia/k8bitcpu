const char OPCODE_PINS[] = { 31,33,35,37};
const char STEP_PINS[] = {39,41, 43};
const char DATA_PINS[] = {30,32,34,36,38,40,42,44}; // D7 to D0

#define CLOCK_NEG 3

uint8_t opcodes[4];
uint8_t steps[3];
uint8_t data[8];

#define NOP 0b0000
#define LDA 0b0001
#define ADD 0b0010
#define SUB 0b0011
#define STA 0b0100
#define LDI 0b0101
#define JMP 0b0110
#define JCS 0b0111
#define JEQ 0b1000
#define ADI 0b1001
#define SUI 0b1010
#define PRG 0b1011
#define OPC 0b1100
#define OPD 0b1101
#define OUT 0b1110
#define HLT 0b1111

static const char* opcodeMnemonics[] = {
  "NOP", "LDA", "ADD", "SUB", "STA", "LDI", "JMP", "JCS",
  "JEQ", "ADI", "SUI", "PRG", "OPC", "OPD", "OUT", "HLT"
};

uint8_t programData[256][3];
uint8_t programSize = 0; 

volatile uint8_t currentAddress = 0;
volatile uint8_t opcodeRead;
volatile uint8_t stepRead;
volatile uint8_t dataRead;
volatile bool done = false;
volatile bool isOutputting = false;

void writeData(uint8_t step, uint8_t theData) {
  setDataPinsToOutput();
  uint8_t output = theData;
  // Write D0 to D7 (reverse order from the array)
  for (int i = 7; i >= 0; --i) {
    digitalWrite(DATA_PINS[i], output & 0b00000001);
    output = output >> 1;
  }

  char out[30];
  sprintf(out, "W S: %d, D: %d", step, theData);
  Serial.println(out);

}

void readInstruction() {
  delayMicroseconds(5);
  int opcodeR = 0;
  for (int i = 0; i < 4; ++i) {
    opcodes[i] = digitalRead(OPCODE_PINS[i]);
    opcodeR = (opcodeR << 1) | opcodes[i];
  }

  opcodeRead = opcodeR;

  int stepR = 0;
  for (int i = 0; i < 3; ++i) {
    steps[i] = digitalRead(STEP_PINS[i]);
    stepR = (stepR << 1) | steps[i];
  }

  stepRead = stepR;

  char buf[150];
  sprintf(buf, "OPCODE: %d%d%d%d %s Step:%d", 
          opcodes[0], opcodes[1], opcodes[2], opcodes[3], opcodeMnemonics[opcodeR],
          stepR);

  Serial.println(buf);
}

void decodeInstruction() {
  if (done || opcodeRead != PRG || stepRead < 2 || stepRead > 4) {
    if (isOutputting) floatDataPins();
    return;
  }

  Serial.print("Decoding ");
  Serial.print("address: ");
  Serial.print(currentAddress);
  Serial.print(", step: ");
  Serial.print(stepRead);
  Serial.print(", data: ");
  Serial.println(programData[currentAddress][stepRead - 2]);
  writeData(stepRead, programData[currentAddress][stepRead - 2]);

  // If we finish overwriting PRG with our program's first byte,
  // then we're done
  if (currentAddress == 0 && stepRead == 4) {
    Serial.println("Finished programming");
    done = true;
    return;
  }

  // If we got to the end of the program, now send the first instruction to overwrite PRG and execute
  if (currentAddress == programSize) {
    Serial.println("Programmed last instruction, now programming first");
    currentAddress = 0;
    return;
  }

  if(stepRead == 4) {
    Serial.println("Incrementing current address");
    ++currentAddress;
  }
  
}


// Read the instruction after the negative clock tick
void clockTickNeg() {
  readInstruction();
  decodeInstruction();
}

void addTwoByteInstruction(uint8_t opcode, uint8_t operand, uint8_t jumpOpcode, uint8_t jumpOperand) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = opcode << 4;
  programData[currentAddress][2] = jumpOpcode;

  ++currentAddress;

  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = operand;
  programData[currentAddress][2] = jumpOperand;

  ++currentAddress;
}

void addOneByteInstruction(uint8_t opcode, uint8_t jump) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = opcode << 4;
  programData[currentAddress][2] = jump;

  ++currentAddress;
}

void addData(uint8_t rawData, uint8_t jump) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = rawData;
  programData[currentAddress][2] = jump;

  ++currentAddress;
}

void initializeMultiplyProgram() {
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00000000, 13, 0); // jump straight to halt as debug
  addTwoByteInstruction(STA, 0b00011000, 0, 0);
  addTwoByteInstruction(LDA, 0b00011001, 0, 0);
  addTwoByteInstruction(SUI, 0b00000001, 0, 0);
  addTwoByteInstruction(JCS, 0b00001110, 0, 0);
  addTwoByteInstruction(LDA, 0b00011000, 0, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(HLT, 0);
  addTwoByteInstruction(STA, 0b00011001, 0, 0);
  addTwoByteInstruction(LDA, 0b00011000, 0, 0);
  addTwoByteInstruction(ADD, 0b00011010, 0, 0);
  addTwoByteInstruction(STA, 0b00011000, 0, 0);
  addTwoByteInstruction(JMP, 0b00000100, 0, 0);
  addData(0b00000000, 0);
  addData(0b00000011, 0); // test multiply, x = 3
  addData(0b00000101, 0); // test multiply, x = 5
  programSize = currentAddress;
  currentAddress = 1;
}

void initializeCountProgram() {
  currentAddress = 0;
  addOneByteInstruction(OUT, 0);
  addTwoByteInstruction(ADI, 0b00000001, 0, 0);
  addTwoByteInstruction(JCS, 0b00000111, 0, 0);
  addTwoByteInstruction(JMP, 0b00000000, 0, 0);
  addTwoByteInstruction(SUI, 0b00000001, 0, 0);
  addOneByteInstruction(OUT, 0);
  addTwoByteInstruction(JEQ, 0b00000000, 0, 0);
  addTwoByteInstruction(JMP, 0b00000111, 0, 0);
  programSize = currentAddress;
  currentAddress = 1;
}

void initializeSimpleProgram() {
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00101010, 0, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(HLT, 0);
  programSize = currentAddress;
  currentAddress = 1;
}

void setDataPinsToOutput() {
  Serial.println("Outputting data pins");
  for (int i = 0; i < 8; ++i) {
    pinMode(DATA_PINS[i], OUTPUT);
  }
  isOutputting = true;
}

void floatDataPins() {
  Serial.println("Floating data pins");
  for (int i = 0; i < 8; ++i) {
    digitalWrite(DATA_PINS[i], 0);
    pinMode(DATA_PINS[i], INPUT);
  }
}

void setup() {
  Serial.begin(57600);
  Serial.println("Started");

  initializeCountProgram();
  Serial.println("Program size: ");
  Serial.println(programSize);

  for(int i = 0; i < programSize; ++i) {
    Serial.print(i);
    Serial.print(": ");
    Serial.print(programData[i][0]);
    Serial.print(",");
    Serial.print(programData[i][1]);
    Serial.print(",");
    Serial.print(programData[i][2]);
    Serial.println();
  }

  for (int i = 0; i < 4; ++i) {
    pinMode(OPCODE_PINS[i], INPUT);
  }
  for (int i = 0; i < 3; ++i) {
    pinMode(STEP_PINS[i], INPUT);
  }

  floatDataPins();

  pinMode(CLOCK_NEG, INPUT);
  readInstruction();
  attachInterrupt(digitalPinToInterrupt(CLOCK_NEG), clockTickNeg, RISING);

}

void loop() {

}
