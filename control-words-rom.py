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
IO = 0b0000100000000000  # Instruction Register Output
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
JEQ = 0b00001000 # Jump if equal (zero flag set)

# Note: this differs from Ben Eater's design and sets the flags on the
# inverse clock to deal with a timing issue.

instructions = [
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 0000 - NOP
  [MI|CO, RO|II|CE, MI|IO, RO|AI,       0,        0, 0, 0], # 0001 - LDA
  [MI|CO, RO|II|CE, MI|IO, RO|BI|FI,    AI|EO,    0, 0, 0], # 0010 - ADD
  [MI|CO, RO|II|CE, MI|IO, RO|BI|SU|FI, AI|EO|SU, 0, 0, 0], # 0011 - SUB
  [MI|CO, RO|II|CE, MI|IO, AO|RI,       0,        0, 0, 0], # 0100 - STA
  [MI|CO, RO|II|CE, IO|AI, 0,           0,        0, 0, 0], # 0101 - LDI
  [MI|CO, RO|II|CE, IO|J,  0,           0,        0, 0, 0], # 0110 - JMP
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 0111 - JCS
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1000 - JEQ
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1001 - OP9
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1010 - OP10
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1011 - OP11
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1100 - OP12
  [MI|CO, RO|II|CE, 0,     0,           0,        0, 0, 0], # 1101 - OP13
  [MI|CO, RO|II|CE, AO|OI, 0,           0,        0, 0, 0], # 1110 - OUT
  [MI|CO, RO|II|CE, HL,    0,           0,        0, 0, 0], # 1111 - HLT
]

# create four copies of the instructions, for each combination
# of the zero flag (Z) and carry flag (C)
# Index 0 is Z=0, C=0
# Index 1 is Z=0, C=1
# Index 2 is Z=1, C=0
# Index 3 is Z=1, C=1
instructions_by_flag = [copy.deepcopy(instructions) for _ in range(4)]

# print ("JCS (0,0): ", instructions_by_flag[FLAGS_Z0C0][JCS][2])
# print ("JCS (0,1): ", instructions_by_flag[FLAGS_Z0C1][JCS][2])
# print ("JCS (1,0): ", instructions_by_flag[FLAGS_Z1C0][JCS][2])
# print ("JCS (1,1): ", instructions_by_flag[FLAGS_Z1C1][JCS][2])

# print("Flags Z0C0: ", FLAGS_Z0C0)
# print("Flags Z0C1: ", FLAGS_Z0C1)
# print("Flags Z1C0: ", FLAGS_Z1C0)
# print("Flags Z1C1: ", FLAGS_Z1C1)
instructions_by_flag[FLAGS_Z0C1][JCS][2] = IO|J # Jump if carry set
instructions_by_flag[FLAGS_Z1C1][JCS][2] = IO|J # Jump if carry set

instructions_by_flag[FLAGS_Z1C0][JEQ][2] = IO|J # Jump if equal
instructions_by_flag[FLAGS_Z1C1][JEQ][2] = IO|J # Jump if equal

# print ("JCS (0,0): ", instructions_by_flag[FLAGS_Z0C0][JCS][2])
# print ("JCS (0,1): ", instructions_by_flag[FLAGS_Z0C1][JCS][2])
# print ("JCS (1,0): ", instructions_by_flag[FLAGS_Z1C0][JCS][2])
# print ("JCS (1,1): ", instructions_by_flag[FLAGS_Z1C1][JCS][2])

rom_data = bytearray(2048)

address = 0
for address in range(1024):
  flags       = (address & 0b1100000000) >> 8
  byte_select = (address & 0b0010000000) >> 7
  instruction = (address & 0b0001111000) >> 3
  step        = (address & 0b0000000111)
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
  (HL, "HLT"),
  (MI, "MI"),
  (RI, "RI"),
  (RO, "RO"),
  (IO, "IO"),
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
  writer.writerow(["Opcode", "Step 0", "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7"])
  for opcode, steps in enumerate(instructions):
    row = [f"{opcode:04b}"] + [decode_control_word(step) for step in steps]
    writer.writerow(row)