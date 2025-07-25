import pprint
import copy
import csv

# This file is used to build two control ROMs for the 8-bit CPU from Ben Eater's design,
# with some modifications.

# The CPU has a program counter, memory address register, instruction register, A/B registers, an ALU, and RAM.

# The ROMs are used to control the CPU's operations by setting control bits in three 8-bit control
# words for each instruction and step. Each clock tick increments the step counter. There are 5 steps per instruction.

# A typical instruction cycle consists of the following steps:
# Step 1 - Put the current value of the program counter onto the bus, load it into the memory address register (MAR).
# Step 2 - Take whatever is stored in RAM at the address in the MAR and load it into the instruction register. Increment the program counter.
# Steps 3-5 - Steps specific to the operation being performed, e.g. ADD or LDA.
# Goto step 1 to fetch the next instruction.

# The instruction register is an 8-bit register. Some operations have an opcode and an operand,
# which is split into two bytes in memory.

# The original idea (and Ben Eater's design) was to have a single control ROM that could be used
# for both the left and right halves of the control words. However, I added an extra bit for
# instructions (5 vs 4 bits). I also added a 3rd control rom.This meant that there were no more addresses left to
# select between the control roms. Therefore, I could no longer use a single control ROM and use byte select
# to choose.
# Instead, words 2 and 1 are using the same ROM, with byte select hard-wired to 0 for word 2 and 1 for word 1.
# Word 0 is a separate ROM.

# The below is how things work for words 2 and 1.
# The opcode is fed from the instruction register into the control ROMs and ORed with the current step to form the address for the control ROMs.
# Format:
#   0XXXXXYYY where bit 7 isn't used, XXXXX is the opcode, and YYY is the step.
# So for example, step 0 of all instructions is to load the memory address register (MAR) with the current program counter (PC) value.
# The ROM address for step 0 for LDA would be:
#   00 0 00001 000
#   Bit 10 is the zero flag
#   Bit 9 is the carry flag
#   Bit 8 is Byte Select (BS), hard-wired to 0 for the word 2 rom, 1 for word 1 rom
#   Bits 7-3 are the opcode for the instruction, LDA, which is 0001
#   Bits 2-0 are the step number, which is 000 for the first step

# Word 0 is the same as above, except byte select is hard-wired to 0 for word 0.

# Control bits for the control words ROM, word 2:
# HLT MI RI RO IO II AI AO
HL = 0b100000000000000000000000  # Halt the CPU
MI = 0b010000000000000000000000  # Load memory address register
RI = 0b001000000000000000000000  # RAM Input
RO = 0b000100000000000000000000  # RAM Output
TR = 0b000010000000000000000000  # t-state reset, reset the step counter
II = 0b000001000000000000000000  # Instruction Register Input
AI = 0b000000100000000000000000  # A Register Input
AO = 0b000000010000000000000000  # A Register Output

# Control bits for the control words ROM, word 1:
# EO SU BI OI CE CO J FL
EO = 0b000000001000000000000000  # Sum output
SU = 0b000000000100000000000000  # Subtraction flag
BI = 0b000000000010000000000000  # Register B Input
OI = 0b000000000001000000000000  # Output to decimal display
CE = 0b000000000000100000000000  # Resets the program counter
CO = 0b000000000000010000000000  # Program counter output
J  = 0b000000000000001000000000  # Jump
FI = 0b000000000000000100000000  # Flag Input

# Control bits for the control words ROM, word 0:
# BO UC SC CB
BO = 0b000000000000000010000000  # Register B Output
UC = 0b000000000000000001000000  # Use Carry
SC = 0b000000000000000000100000  # Set Carry (for INC/DEC, ADD/SUB)
CB = 0b000000000000000000010000  # Clear Register B
C3 = 0b000000000000000000001000  # Control Bit 3, unused so far
C2 = 0b000000000000000000000100  # Control Bit 2, unused so far
C1 = 0b000000000000000000000010  # Control Bit 1, unused so far
C0 = 0b000000000000000000000001  # Control Bit 0, unused so far

# How we do addition, subtraction, and increment/decrement, considering the carry flag.
# Use Carry (UC) is used to determine if the carry flag should be used in the operation.
#   If so, the carry flag is added to carry_in on the ALU.
#   If not, the carry flag is ignored and SC (set carry) determines what is fed into carry_in
# SU (subtract) is used to determine if the ALU should perform addition or subtraction.
#   Basically, it inverts the B register.
# CB clears the B register, which is used for all these operations.
# SC is used for INC/DEC and ADD/SUB operations to set the carry flag for those ops,
#   ignoring if the actual ALU carry flag is set or not.

# ADC
#   A = A + B + C
#   CB = 0, SU = 0, UC = 1, SC = 0
# SBC
#   A = A + ~B + C
#   CB = 0, SU = 1, UC = 1, SC = 0
# INC
#   A = A + 0 + 1
#   CB = 1, SU = 0, UC = 0, SC = 1
# DEC
#   A = A + ~0
#   CB = 1, SU = 1, UC = 0, SC = 0
# ADD
#   A = A + B
#   CB = 0, SU = 0, UC = 0, SC = 0
# SUB
#   A = A + ~B + 1
#   CB = 0, SU = 1, UC = 0, SC = 1

FLAGS_Z0C0 = 0b00
FLAGS_Z0C1 = 0b01
FLAGS_Z1C0 = 0b10
FLAGS_Z1C1 = 0b11

JCS = 0b00000111 # Jump if carry set (carry flag set)
JZS = 0b00001000 # Jump if equal (zero flag set)

instructions = [
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 00000 - NOP
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          RO|AI,          TR,             0,  0], # 00001 - LDA - Load A Register from RAM
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          RO|BI,          EO|AI|FI,       TR, 0], # 00010 - ADD - Add RAM to A Register
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          RO|BI,          SU|SC|EO|AI|FI, TR, 0], # 00011 - SUB - Subtract RAM from A Register
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          AO|RI,          TR,             0,  0], # 00100 - STA - Store A Register to RAM
  [MI|CO, RO|II|CE, CO|MI,             RO|AI|CE,          TR,             0,              0,  0], # 00101 - LDI - Load Immediate to A Register
  [MI|CO, RO|II|CE, CO|MI,             RO|J,              TR,             0,              0,  0], # 00110 - JMP - Jump to address
  [MI|CO, RO|II|CE, CE,                TR,                0,              0,              0,  0], # 00111 - JCS - Jump if carry set
  [MI|CO, RO|II|CE, CE,                TR,                0,              0,              0,  0], # 01000 - JZS - Jump if zero set
  [MI|CO, RO|II|CE, CO|MI,             RO|BI|CE,          EO|AI|FI,       TR,             0,  0], # 01001 - ADI - Add Immediate to A Register
  [MI|CO, RO|II|CE, CO|MI,             RO|BI|CE,          SC|SU|EO|AI|FI, TR,             0,  0], # 01010 - SUI - Subtract Immediate from A Register
  [MI|CO, RO|II|CE, MI,                RI,                J,              TR,             0,  0], # 01011 - PRG - Program mode
  [MI|CO, RO|II|CE, CB|SU|SC|FI,       TR,                0,              0,              0,  0], # 01100 - SEC - Set Carry
  [MI|CO, RO|II|CE, CB|FI,             TR,                0,              0,              0,  0], # 01101 - CLC - Clear Carry
  [MI|CO, RO|II|CE, AO|OI,             TR,                0,              0,              0,  0], # 01110 - OUT - Output A Register to display
  [MI|CO, RO|II|CE, HL,                HL,                0,              0,              0,  0], # 01111 - HLT - Halt the CPU
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          RO|BI,          UC|EO|AI|FI,    TR, 0], # 10000 - ADC - Add with carry
  [MI|CO, RO|II|CE, CO|MI,             RO|MI|CE,          RO|BI,          UC|SU|EO|AI|FI, TR, 0], # 10001 - SBC - Subtract with carry
  [MI|CO, RO|II|CE, CB|SC|EO|AI|FI,    TR,                0,              0,              0,  0], # 10010 - INC - Increment A Register
  [MI|CO, RO|II|CE, CB|SU|EO|AI|FI,    TR,                0,              0,              0,  0], # 10011 - DEC - Decrement A Register
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 10100 - O14
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 10101 - O15
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 10110 - O16
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 10111 - O17
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11000 - O18
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11001 - O19
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11010 - O1A
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11011 - O1B
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11100 - O1C
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11101 - O1D
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11110 - O1E
  [MI|CO, RO|II|CE, TR,                0,                 0,              0,              0,  0], # 11111 - O1F
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
rom_data_word0 = bytearray(2048)

address = 0
for address in range(2048):
  flags       = (address & 0b11000000000) >> 9
  byte_select = (address & 0b00100000000) >> 8
  instruction = (address & 0b00011111000) >> 3
  step        = (address & 0b00000000111)
  if byte_select:
    control_word = (instructions_by_flag[flags][instruction][step] >> 8) & 0xFF
    print(f"Word 1 Addr: {address:04x} - Flags: {flags}, Instruction: {instruction}, Step: {step} - Control Word: {control_word:08b}")
    rom_data[address] = control_word
  else:
    control_word = (instructions_by_flag[flags][instruction][step] >> 16) & 0xFF
    print(f"Word 2 Addr: {address:04x} - Flags: {flags}, Instruction: {instruction}, Step: {step} - Control Word: {control_word:08b}")
    rom_data[address] = control_word
  
  control_word = (instructions_by_flag[flags][instruction][step] >> 0) & 0xFF
  print(f"Word 0 Addr: {address:04x} - Flags: {flags}, Instruction: {instruction}, Step: {step} - Control Word: {control_word:08b}")
  rom_data_word0[address] = control_word

with open("control-words-rom.bin", "wb") as f:
  f.write(rom_data)

with open("control-words-rom-word0.bin", "wb") as f:
  f.write(rom_data_word0)

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
  (BO, "BO"),
  (UC, "UC"),
  (SC, "SC"),
  (CB, "CB"),
  (C3, "C3"),
  (C2, "C2"),
  (C1, "C1"),
  (C0, "C0"),
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
      "JZS", "ADI", "SUI", "PRG", "SEC", "CLC", "OUT", "HLT",
      "ADC", "SBC", "INC", "DEC", "O14", "O15", "O16", "O17",
      "O18", "O19", "O1A", "O1B", "O1C", "O1D", "O1E", "O1F"
    ]
    row = [mnemonics[opcode], f"{opcode:04b}"] + [decode_control_word(step) for step in steps]
    writer.writerow(row)



