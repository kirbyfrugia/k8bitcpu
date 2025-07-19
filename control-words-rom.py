import pprint
import copy
import csv

# This file is used to build two control ROMs for the 8-bit CPU from Ben Eater's design,
# with some modifications.

# The CPU has a program counter, memory address register, instruction register, A/B registers, an ALU, and RAM.

# The ROMs are used to control the CPU's operations by setting control bits in two 8-bit control
# words for each instruction and step. Each clock tick increments the step counter. There are 5 steps per instruction.

# A typical instruction cycle consists of the following steps:
# Step 1 - Put the current value of the program counter onto the bus, load it into the memory address register (MAR).
# Step 2 - Take whatever is stored in RAM at the address in the MAR and load it into the instruction register. Increment the program counter.
# Steps 3-5 - Steps specific to the operation being performed, e.g. ADD or LDA.
# Goto step 1 to fetch the next instruction.

# The instruction register is an 8-bit register.
# The 4 most significant bits (msb) are the opcode, and the 4 least significant bits (lsb) are the operand.
# When outputting the instruction register, it only outputs the 4 lsb.

# The operand usually contains the address of the data to be operated on, or a value to be used in the operation.
# For example, the operand for the LDA instruction is the address of the data to be loaded into the A register.
# For the LDI opcode, the operand is the value to be loaded into the A register directly.

# The opcode is fed from the instruction register into the control ROMs and ORed with the current step to form the address for the control ROMs.
# Format:
#   0XXXXYYY where bit 7 isn't used, XXXX is the opcode, and YYY is the step.
# So for example, step 0 of all instructions is to load the memory address register (MAR) with the current program counter (PC) value.
# The ROM address for step 0 for LDA would be:
#   00 0 0001 000
#   Bit 9 is the zero flag
#   Bit 8 is the carry flag
#   Bit 7 is Byte Select (BS), hard-wired to 0 for msb control words rom, 1 for lsb control word rom
#   Bits 6-3 are the opcode for the instruction, LDA, which is 0001
#   Bits 2-0 are the step number, which is 000 for the first step


# Control bits for the control words ROM, left side:
# HLT MI RI RO IO II AI AO
HL = 0b1000000000000000  # Halt the CPU
MI = 0b0100000000000000  # Load memory address register
RI = 0b0010000000000000  # RAM Input
RO = 0b0001000000000000  # RAM Output
TR = 0b0000100000000000  # t-state reset, reset the step counter
II = 0b0000010000000000  # Instruction Register Input
AI = 0b0000001000000000  # A Register Input
AO = 0b0000000100000000  # A Register Output

# Control bits for the control words ROM, right side:
# EO SU BI OI CE CO J FL
EO = 0b0000000010000000  # Sum output
SU = 0b0000000001000000  # Subtraction flag
BI = 0b0000000000100000  # Register B Input
OI = 0b0000000000010000  # Output to decimal display
CE = 0b0000000000001000  # Resets the program counter
CO = 0b0000000000000100  # Program counter output
J  = 0b0000000000000010  # Jump
FI = 0b0000000000000001  # Flag Input

FLAGS_Z0C0 = 0b00
FLAGS_Z0C1 = 0b01
FLAGS_Z1C0 = 0b10
FLAGS_Z1C1 = 0b11

JCS = 0b00000111 # Jump if carry set (carry flag set)
JZS = 0b00001000 # Jump if equal (zero flag set)

# Note: this differs from Ben Eater's design and sets the flags on the
# inverse clock to deal with a timing issue.

instructions = [
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 00000 - NOP
  [MI|CO, RO|II|CE, CO|MI, RO|MI|CE,        RO|AI,       TR,       0,  0], # 00001 - LDA
  [MI|CO, RO|II|CE, CO|MI, RO|MI|CE,        RO|BI|FI,    EO|AI,    TR, 0], # 00010 - ADD
  [MI|CO, RO|II|CE, CO|MI, RO|MI|CE,        RO|BI|SU|FI, EO|AI|SU, TR, 0], # 00011 - SUB
  [MI|CO, RO|II|CE, CO|MI, RO|MI|CE,        AO|RI,       TR,       0,  0], # 00100 - STA
  [MI|CO, RO|II|CE, CO|MI, RO|AI|CE,        TR,          0,        0,  0], # 00101 - LDI
  [MI|CO, RO|II|CE, CO|MI, RO|J,            TR,          0,        0,  0], # 00110 - JMP
  [MI|CO, RO|II|CE, CE,    TR,              0,           0,        0,  0], # 00111 - JCS
  [MI|CO, RO|II|CE, CE,    TR,              0,           0,        0,  0], # 01000 - JZS
  [MI|CO, RO|II|CE, CO|MI, RO|BI|CE|FI,     EO|AI,       TR,       0,  0], # 01001 - ADI
  [MI|CO, RO|II|CE, CO|MI, RO|BI|SU|CE|FI,  EO|AI|SU,    TR,       0,  0], # 01010 - SUI
  [MI|CO, RO|II|CE, MI,    RI,              J,           TR,       0,  0], # 01011 - PRG
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 01100 - O0C
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 01101 - O0D
  [MI|CO, RO|II|CE, AO|OI, TR,              0,           0,        0,  0], # 01110 - OUT
  [MI|CO, RO|II|CE, HL,    HL,              0,           0,        0,  0], # 01111 - HLT
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10000 - O10
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10001 - O11
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10010 - O12
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10011 - O13
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10100 - O14
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10101 - O15
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10110 - O16
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 10111 - O17
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11000 - O18
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11001 - O19
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11010 - O1A
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11011 - O1B
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11100 - O1C
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11101 - O1D
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11110 - O1E
  [MI|CO, RO|II|CE, TR,    0,               0,           0,        0,  0], # 11111 - O1F
]

# create four copies of the instructions, for each combination
# of the zero flag (Z) and carry flag (C)
# Index 0 is Z=0, C=0
# Index 1 is Z=0, C=1
# Index 2 is Z=1, C=0
# Index 3 is Z=1, C=1
instructions_by_flag = [copy.deepcopy(instructions) for _ in range(4)]

instructions_by_flag[FLAGS_Z0C1][JCS][2] = CO|MI
instructions_by_flag[FLAGS_Z0C1][JCS][3] = RO|J
instructions_by_flag[FLAGS_Z0C1][JCS][4] = TR

instructions_by_flag[FLAGS_Z1C1][JCS][2] = CO|MI
instructions_by_flag[FLAGS_Z1C1][JCS][3] = RO|J
instructions_by_flag[FLAGS_Z1C1][JCS][4] = TR

instructions_by_flag[FLAGS_Z1C0][JZS][2] = CO|MI
instructions_by_flag[FLAGS_Z1C0][JZS][3] = RO|J
instructions_by_flag[FLAGS_Z1C0][JZS][4] = TR

instructions_by_flag[FLAGS_Z1C1][JZS][2] = CO|MI
instructions_by_flag[FLAGS_Z1C1][JZS][3] = RO|J
instructions_by_flag[FLAGS_Z1C1][JZS][4] = TR

rom_data = bytearray(2048)

address = 0
for address in range(2048):
  flags       = (address & 0b11000000000) >> 9
  byte_select = (address & 0b00100000000) >> 8
  instruction = (address & 0b00011111000) >> 3
  step        = (address & 0b00000000111)
  if byte_select:
    control_word = instructions_by_flag[flags][instruction][step] & 0xFF
    print(f"Right Address  {address:04x} - Flags: {flags}, Instruction: {instruction}, Step: {step} - Control Word: {control_word:08b}")
    rom_data[address] = control_word
  else:
    control_word = instructions_by_flag[flags][instruction][step] >> 8
    print(f"Left Address {address:04x} - Flags: {flags}, Instruction: {instruction}, Step: {step} - Control Word: {control_word:08b}")
    rom_data[address] = control_word

with open("control-words-rom.bin", "wb") as f:
  f.write(rom_data)

# Helper to decode control word bits into names
CONTROL_BITS = [
  (HL, "HL"),
  (MI, "MI"),
  (RI, "RI"),
  (RO, "RO"),
  (TR, "TR"),
  (II, "II"),
  (AI, "AI"),
  (AO, "AO"),
  (EO, "EO"),
  (SU, "SU"),
  (BI, "BI"),
  (OI, "OI"),
  (CE, "CE"),
  (CO, "CO"),
  (J,  "J"),
  (FI, "FI"),
]

def decode_control_word(word):
  if word == 0:
    return ""
  names = []
  for bit, name in CONTROL_BITS:
    if word & bit:
      names.append(name)
  return "|".join(names)

with open("instructions.csv", "w", newline="") as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(["Mnemonic", "Opcode", "Step 0", "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7"])
  for opcode, steps in enumerate(instructions):
    mnemonics = [
      "NOP", "LDA", "ADD", "SUB", "STA", "LDI", "JMP", "JCS",
      "JZS", "ADI", "SUI", "PRG", "O0C", "O0D", "OUT", "HLT",
      "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17",
      "O18", "O19", "O1A", "O1B", "O1C", "O1D", "O1E", "O1F"
    ]
    row = [mnemonics[opcode], f"{opcode:04b}"] + [decode_control_word(step) for step in steps]
    writer.writerow(row)