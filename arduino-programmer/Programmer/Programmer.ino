// Purpose: to assemble, load, and execute a program on the ben eater 8-bit cpu via an Arduino instead of dip switches.
//
// WARNING: I updated my roms to have 5 bits for the instruction, which deviates from Ben Eater's. So
//          you will need to modify accordingly. I also use the 5 lsb on the instruction register
//          instead of the 4 msb.
//
// Not really worth it unless you have 256 bytes of ram, but if you have a long program it can help.
//
// Getting started:
//   Add a PRG opcode 01011. You can use a different one, but that's the one I used.
//   Wire up the Arduino. See the pins listed below (opcode pins, step pins, data pins, inverted clock)
//   Put your CPU in program mode by programming opcode 1011 at address zero on your CPU.
//   If your rom looks different than mine, adjust the #defines below
//
// PRG should look like this if you upgraded to 256 bytes and implemented the t-state reset:
// MI|CO, RO|II|CE, MI, RI, J, TR, 0, 0
//
// How it works:
//   This arduino code watches for when we're at the address for opcode 01011 (PRG) and on steps 2 to 4.
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

const char OPCODE_PINS[] = { 31,33,35,37,39};
const char STEP_PINS[] = {41,43,45};
const char DATA_PINS[] = {30,32,34,36,38,40,42,44}; // D7 to D0

#define INVERTED_CLOCK 3

uint8_t opcode[5];
uint8_t steps[3];
uint8_t data[8];

#define NOP 0b00000000
#define LDA 0b00000001
#define ADD 0b00000010
#define SUB 0b00000011
#define STA 0b00000100
#define LDI 0b00000101
#define JMP 0b00000110
#define JCS 0b00000111
#define JZS 0b00001000
#define ADI 0b00001001
#define SUI 0b00001010
#define PRG 0b00001011
#define OPC 0b00001100
#define OPD 0b00001101
#define OUT 0b00001110
#define HLT 0b00001111

static const char* opcodeMnemonics[] = {
  "NOP", "LDA", "ADD", "SUB", "STA", "LDI", "JMP", "JCS",
  "JZS", "ADI", "SUI", "PRG", "O0C", "O0D", "OUT", "HLT",
  "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17",
  "O18", "O19", "O1A", "O1B", "O1C", "O1D", "O1E", "O1F"
};

uint8_t programData[256][4];
uint8_t programSize = 0; 

volatile uint8_t currentAddress = 0;
volatile uint8_t opcodeRead;
volatile uint8_t stepRead;
volatile uint8_t dataRead;
volatile bool done = false;
volatile bool isOutputting = false;

void byteToBitsInBuf(uint8_t theData, char *buf) {
  buf[0] = (char)(48+((theData & 0b10000000) >> 7));
  buf[1] = (char)(48+((theData & 0b01000000) >> 6));
  buf[2] = (char)(48+((theData & 0b00100000) >> 5));
  buf[3] = (char)(48+((theData & 0b00010000) >> 4));
  buf[4] = (char)(48+((theData & 0b00001000) >> 3));
  buf[5] = (char)(48+((theData & 0b00000100) >> 2));
  buf[6] = (char)(48+((theData & 0b00000010) >> 1));
  buf[7] = (char)(48+((theData & 0b00000001)));
}

void writeData(uint8_t step, uint8_t theData) {
  setDataPinsToOutput();
  uint8_t output = theData;
  // Write D0 to D7 (reverse order from the array)
  for (int i = 7; i >= 0; --i) {
    digitalWrite(DATA_PINS[i], output & 0b00000001);
    output = output >> 1;
  }

  char buf[45];
  sprintf(buf, "WRITING STEP: %d, D:          ", step);
  byteToBitsInBuf(theData, buf+20);
  Serial.println(buf);
}

void readInstruction() {
  //delayMicroseconds(5);
  int opcodeR = 0;
  for (int i = 0; i < 5; ++i) {
    opcode[i] = digitalRead(OPCODE_PINS[i]);
    opcodeR = (opcodeR << 1) | opcode[i];
  }

  opcodeRead = opcodeR;

  int stepR = 0;
  for (int i = 0; i < 3; ++i) {
    steps[i] = digitalRead(STEP_PINS[i]);
    stepR = (stepR << 1) | steps[i];
  }

  stepRead = stepR;

  char buf[45];
  sprintf(buf, "READ OPCODE: %d%d%d%d%d (%s) STEP:%d", 
          opcode[0], opcode[1], opcode[2], opcode[3], opcode[4], opcodeMnemonics[opcodeR],
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
    ++currentAddress;
  }
}


// Read the instruction after the negative clock tick
void invertedClockTick() {
  readInstruction();
  decodeInstruction();
}

void addTwoByteInstruction(uint8_t instrOpcode, uint8_t instrOperand, uint8_t jumpOpcode, uint8_t jumpOperand) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = instrOpcode;
  programData[currentAddress][2] = jumpOpcode;
  programData[currentAddress][3] = 1;

  ++currentAddress;

  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = instrOperand;
  programData[currentAddress][2] = jumpOperand;
  programData[currentAddress][3] = 0;

  ++currentAddress;
}

void addOneByteInstruction(uint8_t instrOpcode, uint8_t jump) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = instrOpcode;
  programData[currentAddress][2] = jump;
  programData[currentAddress][3] = 1;

  ++currentAddress;
}

void addData(uint8_t rawData, uint8_t jump) {
  programData[currentAddress][0] = currentAddress;
  programData[currentAddress][1] = rawData;
  programData[currentAddress][2] = jump;
  programData[currentAddress][3] = 0;

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
  addTwoByteInstruction(JZS, 0b00000000, 0, 0);
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
  for (int i = 0; i < 8; ++i) {
    pinMode(DATA_PINS[i], OUTPUT);
  }
  isOutputting = true;
}

void floatDataPins() {
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
    char buf[45];
    sprintf(buf, "%3d:          ", programData[i][0]);
    uint8_t progData = programData[i][1];
    byteToBitsInBuf(progData, buf+5);

    char * opcodeBuf = buf+14;
    // If this is an opcode, print the opcode
    if(programData[i][3] == 1 && progData < 32) {
      sprintf(opcodeBuf, "(%s)", opcodeMnemonics[progData]);
    }
    // for (int j = 0; j < 8; ++j) {
    //   Serial.print("progData: ");
    //   Serial.println(progData);
    //   Serial.print("progData & (7 - j): ");
    //   Serial.println(progData & (7 - j));
    //   char theChar = (char)(48+((progData & (7 - j)) >> (7 - j)));
    //   Serial.print("char: ");
    //   Serial.println(theChar);
    //   buf[j+6] = theChar;
    // }
    Serial.println(buf);
  }

  for (int i = 0; i < 5; ++i) {
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
