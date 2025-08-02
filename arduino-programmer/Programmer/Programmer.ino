// Purpose: to assemble, load, and execute a program on the ben eater 8-bit cpu via an Arduino instead of dip switches.
//   Not really worth it unless you have 256 bytes of ram, but if you have a long program it can help.
//
// WARNING: I updated my roms to have 5 bits for the instruction, which deviates from Ben Eater's. So
//          you will need to modify accordingly. I also use the 5 lsb on the instruction register
//          instead of the 4 msb.
//
//
// Getting started:
//   Add a PRG opcode 01011. You can use a different one, but that's the one I used.
//   Wire up the Arduino. See the pins listed below (vcc/gnd, opcode pins, step pins, data pins, inverted clock)
//     Wire up an 8-bit dip switch to two 74ls157s on the B input. Wire the opcode and step pins to the A input.
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
// How to write a program for your CPU
//   Call addTwoByteInstruction() for every two byte instruction if you upgraded to 256 bytes, e.g. LDA
//   Call addOneByteInstruction() for every one byte instruction.
//   Call addData() for every raw byte of data you want to write.
//   See examples to see what to do before and after calling the above functions.
//
// How to run:
//   * In this code:
//     * Write your programs, and assign it an id. This will correspond to what
//       you set on the dip switch. In setup, add to the long if-else blocks.
//   * On the arduino, select the program via the dip switch.
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

const char PROG_PINS[]   = {A4,A3,A2,A1,A0,A5,12,11}; // same pins as opcode and step
const char OPCODE_PINS[] = {A4,A3,A2,A1,A0};
const char STEP_PINS[]   = {A5,12,11};
const char DATA_PINS[]   = {10,9,8,7,6,5,4,3}; // D7 to D0

#define INVERTED_CLOCK 2
#define INPUT_SELECT_PIN 13

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
#define SEC 0b00001100
#define CLC 0b00001101
#define OUT 0b00001110
#define HLT 0b00001111
#define ADC 0b00010000
#define SBC 0b00010001
#define INC 0b00010010
#define DEC 0b00010011

static const char* opcodeMnemonics[] = {
  "NOP", "LDA", "ADD", "SUB", "STA", "LDI", "JMP", "JCS",
  "JZS", "ADI", "SUI", "PRG", "SEC", "CLC", "OUT", "HLT",
  "ADC", "SBC", "INC", "DEC", "O14", "O15", "O16", "O17",
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

int readProgram() {
  int program = 0;
  for (int i = 0; i < 8; ++i) {
    program = (program << 1) | digitalRead(PROG_PINS[i]);
  }
  Serial.print(F("Read Program ID: "));
  Serial.println(program);
  return program;
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
    Serial.println(F("Finished programming"));
    done = true;
    return;
  }

  // If we got to the end of the program, now send the first instruction to overwrite PRG and execute
  if (currentAddress == programSize) {
    Serial.println(F("Programmed last instruction, now programming first"));
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

// Multiplies two numbers, stored at 25,26.
// Result is at 42. Result is outputted
void loadMultiplyProgram() {
  Serial.println(F("Loading multiplyProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00000000, 13, 0); // jump straight to halt as debug
  addTwoByteInstruction(STA, 0b00011001, 0, 0);
  addTwoByteInstruction(LDA, 0b00011010, 0, 0);
  addTwoByteInstruction(SUI, 0b00000001, 0, 0);
  addTwoByteInstruction(JCS, 0b00001110, 0, 0);
  addTwoByteInstruction(LDA, 0b00011001, 0, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(HLT, 0);
  addTwoByteInstruction(STA, 0b00011010, 0, 0); // 00001110
  addTwoByteInstruction(LDA, 0b00011001, 0, 0);
  addTwoByteInstruction(ADD, 0b00011011, 0, 0);
  addTwoByteInstruction(STA, 0b00011001, 0, 0);
  addOneByteInstruction(OUT, 0);
  addTwoByteInstruction(JMP, 0b00000100, 0, 0);
  addData(0b00000000, 0); // A: 24, 0b00011001 result
  addData(0b00000111, 0); // A: 25, 0b00011010 x = 7
  addData(0b00000110, 0); // A: 26, 0b00011011 y = 6
  programSize = currentAddress;
  currentAddress = 1;
}

void loadCountProgram() {
  Serial.println(F("Loading countProgram"));
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

void loadSimpleProgram() {
  Serial.println(F("Loading simpleProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00101010, 0, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(HLT, 0);
  programSize = currentAddress;
  currentAddress = 1;
}

void loadDECINCTestProgram() {
  Serial.println(F("Loading DECINCProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00101010, 0, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(DEC, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(INC, 0);
  addOneByteInstruction(OUT, 0);
  addOneByteInstruction(HLT, 0);
  programSize = currentAddress;
  currentAddress = 1;
}

// Loads 42, subtracts 15 and displays it. Then adds 15.
void loadSUBADDTestProgram() {
  Serial.println(F("Loading SUBADDProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00101010, 0, 0); // A:0,1
  addOneByteInstruction(OUT, 0);                // A:2
  addTwoByteInstruction(SUB, 0b00001010, 0, 0); // A:3,4
  addOneByteInstruction(OUT, 0);                // A:5
  addTwoByteInstruction(ADD, 0b00001010, 0, 0); // A:6,7
  addOneByteInstruction(OUT, 0);                // A:8
  addOneByteInstruction(HLT, 0);                // A:9
  addData(15, 0);                               // A:10
  programSize = currentAddress;
  currentAddress = 1;
}

// Loads 31, sets carry, adds 10. Output is 42.
void load8bitADCProgram() {
  Serial.println(F("Loading 8bitADCProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b00011111, 0, 0); // A: 0,1
  addOneByteInstruction(OUT, 0);                // A: 2
  addOneByteInstruction(SEC, 0);                // A: 3
  addTwoByteInstruction(ADC, 0b00001000, 0, 0); // A: 4,5
  addOneByteInstruction(OUT, 0);                // A: 6
  addOneByteInstruction(HLT, 0);                // A: 7
  addData(0b00001010, 0);                       // A: 8
  programSize = currentAddress;
  currentAddress = 1;
}

// Loads 64, sets carry, subtracts 22, outputs 42
void load8bitSBCProgram() {
  Serial.println(F("Loading 8bitSBCProgram"));
  currentAddress = 0;
  addTwoByteInstruction(LDI, 0b01000000, 0, 0); // A: 0,1
  addOneByteInstruction(OUT, 0);                // A: 2
  addOneByteInstruction(SEC, 0);                // A: 3
  addTwoByteInstruction(SBC, 0b00001000, 0, 0); // A: 4,5
  addOneByteInstruction(OUT, 0);                // A: 6
  addOneByteInstruction(HLT, 0);                // A: 7
  addData(0b00010110, 0);                       // A: 8
  programSize = currentAddress;
  currentAddress = 1;
}

// Adds two 16-bit integers.
// 0x11CC + 0x22BB = 0x3487  (hex) 
// lo byte result stored at address 24, hi at 25
// Outputs the lo byte (135 dec) then the hi byte (52 dec)
void load16bitADCProgram() {
  Serial.println(F("Loading 16bitADCProgram"));
  currentAddress = 0;
  addOneByteInstruction(CLC, 0);        // A: 0
  addTwoByteInstruction(LDA, 20, 0, 0); // A: 1,2
  addTwoByteInstruction(ADC, 22, 0, 0); // A: 3,4
  addTwoByteInstruction(STA, 24, 0, 0); // A: 5,6
  addTwoByteInstruction(LDA, 21, 0, 0); // A: 7,8
  addTwoByteInstruction(ADC, 23, 0, 0); // A: 9,10
  addTwoByteInstruction(STA, 25, 0, 0); // A: 11,12
  addTwoByteInstruction(LDA, 24, 0, 0); // A: 13,14
  addOneByteInstruction(OUT, 0);        // A: 15
  addTwoByteInstruction(LDA, 25, 0, 0);  // A: 16,17
  addOneByteInstruction(OUT, 0);        // A: 18
  addOneByteInstruction(HLT, 0);        // A: 19
  addData(0xCC, 0);                     // A: 20 lo byte of first argument
  addData(0x11, 0);                     // A: 21 hi byte of first argument
  addData(0xBB, 0);                     // A: 22 lo byte of second argument
  addData(0x22, 0);                     // A: 23 hi byte of second argument
                                        // A: 24,25 lo/hi of result
  programSize = currentAddress;
  currentAddress = 1;
}

// Subtracts two 16-bit integers.
// 0xFFDD - 0xCCBB = 0x3322  (hex) 
// lo byte result stored at address 24, hi at 25
// Outputs the lo byte (34 dec) then the hi byte (51 dec)
void load16bitSBCProgram() {
  Serial.println(F("Loading 16bitSBCProgram"));
  currentAddress = 0;
  addOneByteInstruction(SEC, 0);        // A: 0
  addTwoByteInstruction(LDA, 20, 0, 0); // A: 1,2
  addTwoByteInstruction(SBC, 22, 0, 0); // A: 3,4
  addTwoByteInstruction(STA, 24, 0, 0); // A: 5,6
  addTwoByteInstruction(LDA, 21, 0, 0); // A: 7,8
  addTwoByteInstruction(SBC, 23, 0, 0); // A: 9,10
  addTwoByteInstruction(STA, 25, 0, 0); // A: 11,12
  addTwoByteInstruction(LDA, 24, 0, 0); // A: 13,14
  addOneByteInstruction(OUT, 0);        // A: 15
  addTwoByteInstruction(LDA, 25, 0, 0);  // A: 16,17
  addOneByteInstruction(OUT, 0);        // A: 18
  addOneByteInstruction(HLT, 0);        // A: 19
  addData(0xDD, 0);                     // A: 20 lo byte of first argument
  addData(0xFF, 0);                     // A: 21 hi byte of first argument
  addData(0xBB, 0);                     // A: 22 lo byte of second argument
  addData(0xCC, 0);                     // A: 23 hi byte of second argument
                                        // A: 24,25 lo/hi of result
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
  Serial.println(F("Started"));

  for (int i = 0; i < 5; ++i) {
    pinMode(OPCODE_PINS[i], INPUT);
  }
  for (int i = 0; i < 3; ++i) {
    pinMode(STEP_PINS[i], INPUT);
  }

  // Let's first read in the program to load, so set
  // inputs to the dip switch that selects the program
  pinMode(INPUT_SELECT_PIN, OUTPUT);
  digitalWrite(INPUT_SELECT_PIN, HIGH); // set the 47LS157's to select B input (dip switches)

  int program = readProgram();

  if (program == 0) loadSimpleProgram();
  else if (program == 1) loadCountProgram();
  else if (program == 2) loadMultiplyProgram();
  else if (program == 3) loadSUBADDTestProgram();
  else if (program == 4) loadDECINCTestProgram();
  else if (program == 5) load8bitADCProgram();
  else if (program == 6) load8bitSBCProgram();
  else if (program == 7) load16bitADCProgram();
  else if (program == 8) load16bitSBCProgram();
  else loadSimpleProgram();
  
  Serial.print(F("Program size: "));
  Serial.print(programSize);
  Serial.println(F(" bytes, code:"));

  // Now switch the inputs to be coming from the 8 bit cpu
  digitalWrite(INPUT_SELECT_PIN, LOW); // set the 47LS157's to select A input (dip switches)

  for(int i = 0; i < programSize; ++i) {
    char buf[45];
    sprintf(buf, "%3d:          ", programData[i][0]);
    uint8_t progData = programData[i][1];
    byteToBitsInBuf(progData, buf+5);

    // If this is an opcode, print the opcode
    if(programData[i][3] == 1 && progData < 32) {
      sprintf(buf+14, "(%s)", opcodeMnemonics[progData]);
    }

    Serial.println(buf);
  }

  floatDataPins();

  pinMode(INVERTED_CLOCK, INPUT);
  readInstruction();
  attachInterrupt(digitalPinToInterrupt(INVERTED_CLOCK), invertedClockTick, RISING);

}

void loop() {

}
