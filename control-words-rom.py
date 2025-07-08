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
#   0 0001 000
#   Bit 7 is 0 (not used)
#   Bits 6-3 are the opcode for the instruction, LDA, which is 0001
#   Bits 2-0 are the step number, which is 000 for the first step


lt_rom_data = bytearray(2048)
rt_rom_data = bytearray(2048)

# Control bits for the control words ROM, left side:
# HLT MI RI RO IO II AI AO
HL = 0b10000000  # Halt the CPU
MI = 0b01000000  # Load memory address register
RI = 0b00100000  # RAM Input
RO = 0b00010000  # RAM Output
IO = 0b00001000  # Instruction Register Output
II = 0b00000100  # Instruction Register Input
AI = 0b00000010  # A Register Input
AO = 0b00000001  # A Register Output

# Control bits for the control words ROM, right side:
# EO SU BI OI CE CO J FL
EO = 0b10000000  # Sum output
SU = 0b01000000  # Subtraction flag
BI = 0b00100000  # Register B Input
OI = 0b00010000  # Output to decimal display
CE = 0b00001000  # Resets the program counter
CO = 0b00000100  # Program counter output
J  = 0b00000010  # Jump
FL = 0b00000001  # Flag

NIL = 0b00000000  # No control bits set


# Opcodes for the CPU instructions
NOP  = 0b00000000  # No operation
LDA  = 0b00001000  # Loads an address from memory into the memory address register (MAR)
ADD  = 0b00010000  # Adds a value from memory to the value in the A register
SUB  = 0b00011000  # Sutracts a value from memory from the value in the A register
STA  = 0b00100000  # Stores the value in the A register into memory
LDI  = 0b00101000  # Loads an immediate 4-bit value into the A register
JMP  = 0b00110000  # Jumps to the address in the program counter
OP7  = 0b00111000  # Placeholder for a seventh operation
OP8  = 0b01000000  # Placeholder for an eighth operation
OP9  = 0b01001000  # Placeholder for a ninth operation, not used
OP10 = 0b01010000  # Placeholder for a tenth operation
OP11 = 0b01011000  # Placeholder for an eleventh operation
OP12 = 0b01100000  # Placeholder for a twelfth operation
OP13 = 0b01101000  # Placeholder for a thirteenth operation
OUT  = 0b01110000  # Outputs the value in the A register to decimal display
HLT  = 0b01111000  # Halts the CPU

# Steps
STEP0 = 0b00000000  # First step of an instruction
STEP1 = 0b00000001  # Second step of an instruction
STEP2 = 0b00000010  # Third step of an instruction
STEP3 = 0b00000011  # Fourth step of an instruction
STEP4 = 0b00000100  # Fifth step of an instruction

# NOP instruction
lt_rom_data[NOP | STEP0] = MI      ; rt_rom_data[NOP | STEP0] = CO
lt_rom_data[NOP | STEP1] = RO | II ; rt_rom_data[NOP | STEP1] = CE
lt_rom_data[NOP | STEP2] = NIL     ; rt_rom_data[NOP | STEP2] = NIL
lt_rom_data[NOP | STEP3] = NIL     ; rt_rom_data[NOP | STEP3] = NIL
lt_rom_data[NOP | STEP4] = NIL     ; rt_rom_data[NOP | STEP4] = NIL

# LDA instruction
lt_rom_data[LDA | STEP0] = MI      ; rt_rom_data[LDA | STEP0] = CO
lt_rom_data[LDA | STEP1] = RO | II ; rt_rom_data[LDA | STEP1] = CE
lt_rom_data[LDA | STEP2] = MI | IO ; rt_rom_data[LDA | STEP2] = NIL # Put the instruction address onto the bus and load it into the MAR (4 lsb)
lt_rom_data[LDA | STEP3] = RO | AI ; rt_rom_data[LDA | STEP3] = NIL # Output the RAM value onto the bus, load it into the A register
lt_rom_data[LDA | STEP4] = NIL     ; rt_rom_data[LDA | STEP4] = NIL


# ADD instruction
lt_rom_data[ADD | STEP0] = MI      ; rt_rom_data[ADD | STEP0] = CO
lt_rom_data[ADD | STEP1] = RO | II ; rt_rom_data[ADD | STEP1] = CE
lt_rom_data[ADD | STEP2] = MI | IO ; rt_rom_data[ADD | STEP2] = NIL # Put the instruction address onto the bus and load it into the MAR
lt_rom_data[ADD | STEP3] = RO      ; rt_rom_data[ADD | STEP3] = BI  # Load the B register with the value at the address in the instruction register
lt_rom_data[ADD | STEP4] = AI      ; rt_rom_data[ADD | STEP4] = EO  # Output the sum of the A and B registers to the bus, load it into the A register

# SUB instruction
lt_rom_data[SUB | STEP0] = MI      ; rt_rom_data[SUB | STEP0] = CO
lt_rom_data[SUB | STEP1] = RO | II ; rt_rom_data[SUB | STEP1] = CE
lt_rom_data[SUB | STEP2] = MI | IO ; rt_rom_data[SUB | STEP2] = NIL     # Load the instruction register with the address to subtract
lt_rom_data[SUB | STEP3] = RO      ; rt_rom_data[SUB | STEP3] = BI      # Put the RAM value onto the bus, load B register
lt_rom_data[SUB | STEP4] = AI      ; rt_rom_data[SUB | STEP4] = EO | SU # Output the difference of the A and B registers to the bus, load it into the A register

# STA instruction
lt_rom_data[STA | STEP0] = MI      ; rt_rom_data[STA | STEP0] = CO
lt_rom_data[STA | STEP1] = RO | II ; rt_rom_data[STA | STEP1] = CE
lt_rom_data[STA | STEP2] = IO | MI ; rt_rom_data[STA | STEP2] = NIL # Load the instruction register with the address to store (4 lsb)
lt_rom_data[STA | STEP3] = AO | RI ; rt_rom_data[STA | STEP3] = NIL
lt_rom_data[STA | STEP4] = NIL     ; rt_rom_data[STA | STEP4] = NIL

# LDI instruction
lt_rom_data[LDI | STEP0] = MI      ; rt_rom_data[LDI | STEP0] = CO
lt_rom_data[LDI | STEP1] = RO | II ; rt_rom_data[LDI | STEP1] = CE
lt_rom_data[LDI | STEP2] = IO | AI ; rt_rom_data[LDI | STEP2] = NIL # Load the A register with the 4 lsb of the instruction register (immediate value)
lt_rom_data[LDI | STEP3] = NIL     ; rt_rom_data[LDI | STEP3] = NIL
lt_rom_data[LDI | STEP4] = NIL     ; rt_rom_data[LDI | STEP4] = NIL

# JMP instruction
lt_rom_data[JMP | STEP0] = MI      ; rt_rom_data[JMP | STEP0] = CO
lt_rom_data[JMP | STEP1] = RO | II ; rt_rom_data[JMP | STEP1] = CE
lt_rom_data[JMP | STEP2] = IO      ; rt_rom_data[JMP | STEP2] = J
lt_rom_data[JMP | STEP3] = NIL     ; rt_rom_data[JMP | STEP3] = NIL
lt_rom_data[JMP | STEP4] = NIL     ; rt_rom_data[JMP | STEP4] = NIL

# OP7 instruction
lt_rom_data[OP7 | STEP0] = MI      ; rt_rom_data[OP7 | STEP0] = CO
lt_rom_data[OP7 | STEP1] = RO | II ; rt_rom_data[OP7 | STEP1] = CE
lt_rom_data[OP7 | STEP2] = NIL     ; rt_rom_data[OP7 | STEP2] = NIL
lt_rom_data[OP7 | STEP3] = NIL     ; rt_rom_data[OP7 | STEP3] = NIL
lt_rom_data[OP7 | STEP4] = NIL     ; rt_rom_data[OP7 | STEP4] = NIL

# OP8 instruction
lt_rom_data[OP8 | STEP0] = MI      ; rt_rom_data[OP8 | STEP0] = CO
lt_rom_data[OP8 | STEP1] = RO | II ; rt_rom_data[OP8 | STEP1] = CE
lt_rom_data[OP8 | STEP2] = NIL     ; rt_rom_data[OP8 | STEP2] = NIL
lt_rom_data[OP8 | STEP3] = NIL     ; rt_rom_data[OP8 | STEP3] = NIL
lt_rom_data[OP8 | STEP4] = NIL     ; rt_rom_data[OP8 | STEP4] = NIL

# OP9 instruction
lt_rom_data[OP9 | STEP0] = MI      ; rt_rom_data[OP9 | STEP0] = CO
lt_rom_data[OP9 | STEP1] = RO | II ; rt_rom_data[OP9 | STEP1] = CE
lt_rom_data[OP9 | STEP2] = NIL     ; rt_rom_data[OP9 | STEP2] = NIL
lt_rom_data[OP9 | STEP3] = NIL     ; rt_rom_data[OP9 | STEP3] = NIL
lt_rom_data[OP9 | STEP4] = NIL     ; rt_rom_data[OP9 | STEP4] = NIL

# OP10 instruction
lt_rom_data[OP10 | STEP0] = MI      ; rt_rom_data[OP10 | STEP0] = CO
lt_rom_data[OP10 | STEP1] = RO | II ; rt_rom_data[OP10 | STEP1] = CE
lt_rom_data[OP10 | STEP2] = NIL     ; rt_rom_data[OP10 | STEP2] = NIL
lt_rom_data[OP10 | STEP3] = NIL     ; rt_rom_data[OP10 | STEP3] = NIL
lt_rom_data[OP10 | STEP4] = NIL     ; rt_rom_data[OP10 | STEP4] = NIL

# OP11 instruction
lt_rom_data[OP11 | STEP0] = MI      ; rt_rom_data[OP11 | STEP0] = CO
lt_rom_data[OP11 | STEP1] = RO | II ; rt_rom_data[OP11 | STEP1] = CE
lt_rom_data[OP11 | STEP2] = NIL     ; rt_rom_data[OP11 | STEP2] = NIL
lt_rom_data[OP11 | STEP3] = NIL     ; rt_rom_data[OP11 | STEP3] = NIL
lt_rom_data[OP11 | STEP4] = NIL     ; rt_rom_data[OP11 | STEP4] = NIL

# OP12 instruction
lt_rom_data[OP12 | STEP0] = MI      ; rt_rom_data[OP12 | STEP0] = CO
lt_rom_data[OP12 | STEP1] = RO | II ; rt_rom_data[OP12 | STEP1] = CE
lt_rom_data[OP12 | STEP2] = NIL     ; rt_rom_data[OP12 | STEP2] = NIL
lt_rom_data[OP12 | STEP3] = NIL     ; rt_rom_data[OP12 | STEP3] = NIL
lt_rom_data[OP12 | STEP4] = NIL     ; rt_rom_data[OP12 | STEP4] = NIL

# OP13 instruction
lt_rom_data[OP13 | STEP0] = MI      ; rt_rom_data[OP13 | STEP0] = CO
lt_rom_data[OP13 | STEP1] = RO | II ; rt_rom_data[OP13 | STEP1] = CE
lt_rom_data[OP13 | STEP2] = NIL     ; rt_rom_data[OP13 | STEP2] = NIL
lt_rom_data[OP13 | STEP3] = NIL     ; rt_rom_data[OP13 | STEP3] = NIL
lt_rom_data[OP13 | STEP4] = NIL     ; rt_rom_data[OP13 | STEP4] = NIL

# OUT instruction
lt_rom_data[OUT | STEP0] = MI      ; rt_rom_data[OUT | STEP0] = CO
lt_rom_data[OUT | STEP1] = RO | II ; rt_rom_data[OUT | STEP1] = CE
lt_rom_data[OUT | STEP2] = AO      ; rt_rom_data[OUT | STEP2] = OI
lt_rom_data[OUT | STEP3] = NIL     ; rt_rom_data[OUT | STEP3] = NIL
lt_rom_data[OUT | STEP4] = NIL     ; rt_rom_data[OUT | STEP4] = NIL

# HLT instruction
lt_rom_data[HLT | STEP0] = MI      ; rt_rom_data[HLT | STEP0] = CO
lt_rom_data[HLT | STEP1] = RO | II ; rt_rom_data[HLT | STEP1] = CE
lt_rom_data[HLT | STEP2] = HL      ; rt_rom_data[HLT | STEP2] = NIL
lt_rom_data[HLT | STEP3] = NIL     ; rt_rom_data[HLT | STEP3] = NIL
lt_rom_data[HLT | STEP4] = NIL     ; rt_rom_data[HLT | STEP4] = NIL

# Write rom files
with open("control-words-rom-left.bin", "wb") as f:
  f.write(lt_rom_data)
  
with open("control-words-rom-right.bin", "wb") as f:
  f.write(rt_rom_data)