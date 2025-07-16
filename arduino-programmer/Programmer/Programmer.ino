// Purpose: to assemble, load, and execute a program on the ben eater 8-bit cpu via an Arduino instead of dip switches.
//
// Not really worth it unless you have 256 bytes of ram, but if you have a long program it can help.
//
// Getting started:
//   Add a PRG opcode 1011. You can use a different one, but that's the one I used.
//   Wire up the Arduino. See the pins listed below (opcode pins, step pins, data pins, inverted clock)
//   Put your CPU in program mode by programming opcode 1011 at address zero on your CPU.
//   If your rom looks different than mine, adjust the #defines below
//
// PRG should look like this if you upgraded to 256 bytes and implemented the t-state reset:
// MI|CO, RO|II|CE, MI, RI, J, TR, 0, 0
//
// How it works:
//   This arduino code watches for when we're at the address for opcode 1011 (PRG) and on steps 2 to 3.
//   On Step 2, it will output an address for a line in your program.
//   On Step 3, it will output the data for that line in your program.
//   On Step 4, it will jump back to Zero, so that the cpu awaits another instruction via PRG.
//   After Step 4, it increments to the next address in your program. The next time it sees
//     a PRG, it repeats the above.
//   When writing the program out, it writes from address 1 to N before zero. This prevents it from
//     overwriting PRG until it has done everything else. Then it writes address zero and jmps there.
//   So all you really need to do is write your program here, put your cpu in PRG mode, and go.
//
// How to write a program for your CPU (see examples below, e.g. initializeCountProgram):
//   Call addTwoByteInstruction() for every two byte instruction if you upgraded to 256 bytes, e.g. LDA
//   Call addOneByteInstruction() for every one byte instruction.
//   Call addData() for every raw byte of data you want to write.
//   See examples to see what to do before and after calling the above functions.
//
// How to run:
//   * In this code:
//     * In setup() call the appropriate initializeXYZProgram that you want to program on your cpu
//   * On your cpu:
//     * Manually program opcode PRG at memory location zero.
//     * Reset the arduino
//     * Reset your cpu.
//     * Your program should load into memory and then execute
//
// Note: For debugging, I wanted a way to not immediately jump back to zero and execute the program.
//   So for the addXByteInstruction functions, you can pass in the address you want to jump to
//   after each byte of the  instruction is written to RAM on your cpu. So, for example, the multiply
//   program below will jump to byte 13, which is a HLT in the program instead of starting at the beginning.

const char OPCODE_PINS[] = { 31,33,35,37};
const char STEP_PINS[] = {39,41, 43};
const char DATA_PINS[] = {30,32,34,36,38,40,42,44}; // D7 to D0

#define INVERTED_CLOCK 3

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
  //delayMicroseconds(5);
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
void invertedClockTick() {
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

  pinMode(INVERTED_CLOCK, INPUT);
  readInstruction();
  attachInterrupt(digitalPinToInterrupt(INVERTED_CLOCK), invertedClockTick, RISING);

}

void loop() {

}
