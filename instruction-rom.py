lt_rom_data = bytearray(2048)
rt_rom_data = bytearray(2048)

# Control bits for the instruction ROM, left side:
# HLT MI RI RO IO II AI AO
HL = 0b10000000  # Halt the CPU
MI = 0b01000000  # Load memory address register
RI = 0b00100000  # RAM Input
RO = 0b00010000  # RAM Output
IO = 0b00001000  # Instruction Register Output
II = 0b00000100  # Instruction Register Input
AI = 0b00000010  # A Register Input
AO = 0b00000001  # A Register Output

# Control bits for the instruction ROM, right side:
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

# Instructions:
# format of an instruction
# 0xxxxyyy - where xxxx is the opcode and yy is the step (micro-instruction)
# Instructions have micro-instructions that are executed in steps.
# Each micro-instruction sets up to 16 control bits. The 8 msb control bits
# are stored in the left side ROM, and the 8 lsb control bits are stored in the right side ROM.

# Instructions
# Format is 0bAAAAxxx where AAAA is the opcode and xxx is the step.
# The step is used to determine which micro-instruction to execute.
NOP  = 0b00000000  # No operation
LDA  = 0b00001000  # Loads an address from memory into the memory address register (MAR)
ADD  = 0b00010000  # Adds a value from memory to the value in the A register
OP3  = 0b00011000  # Placeholder for a third operation
OP4  = 0b00100000  # Placeholder for a fourth operation
OP5  = 0b00101000  # Placeholder for a fifth operation
OP6  = 0b00110000  # Placeholder for a sixth operation
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

# The first two steps of all instructions is a fetch.
# Step 1 - Load the program counter into the memory address register (MAR)
# Step 2 - Load the instruction register (IR) with the value at the address in the MAR. Increment program counter by 1.

# NOP instruction
lt_rom_data[NOP | STEP0] = MI      ; rt_rom_data[NOP | STEP0] = CO
lt_rom_data[NOP | STEP1] = RO | II ; rt_rom_data[NOP | STEP1] = CE
lt_rom_data[NOP | STEP2] = NIL     ; rt_rom_data[NOP | STEP2] = NIL
lt_rom_data[NOP | STEP3] = NIL     ; rt_rom_data[NOP | STEP3] = NIL
lt_rom_data[NOP | STEP4] = NIL     ; rt_rom_data[NOP | STEP4] = NIL

# LDA instruction
lt_rom_data[LDA | STEP0] = MI      ; rt_rom_data[LDA | STEP0] = CO
lt_rom_data[LDA | STEP1] = RO | II ; rt_rom_data[LDA | STEP1] = CE
lt_rom_data[LDA | STEP2] = MI | IO ; rt_rom_data[LDA | STEP2] = NIL
lt_rom_data[LDA | STEP3] = RO | AI ; rt_rom_data[LDA | STEP3] = NIL
lt_rom_data[LDA | STEP4] = NIL     ; rt_rom_data[LDA | STEP4] = NIL


# ADD instruction
lt_rom_data[ADD | STEP0] = MI      ; rt_rom_data[ADD | STEP0] = CO
lt_rom_data[ADD | STEP1] = RO | II ; rt_rom_data[ADD | STEP1] = CE
lt_rom_data[ADD | STEP2] = MI | IO ; rt_rom_data[ADD | STEP2] = NIL
lt_rom_data[ADD | STEP3] = RO      ; rt_rom_data[ADD | STEP3] = BI
lt_rom_data[ADD | STEP4] = AI      ; rt_rom_data[ADD | STEP4] = EO

# OP3 instruction
lt_rom_data[OP3 | STEP0] = MI      ; rt_rom_data[OP3 | STEP0] = CO
lt_rom_data[OP3 | STEP1] = RO | II ; rt_rom_data[OP3 | STEP1] = CE
lt_rom_data[OP3 | STEP2] = NIL     ; rt_rom_data[OP3 | STEP2] = NIL
lt_rom_data[OP3 | STEP3] = NIL     ; rt_rom_data[OP3 | STEP3] = NIL
lt_rom_data[OP3 | STEP4] = NIL     ; rt_rom_data[OP3 | STEP4] = NIL

# OP4 instruction
lt_rom_data[OP4 | STEP0] = MI      ; rt_rom_data[OP4 | STEP0] = CO
lt_rom_data[OP4 | STEP1] = RO | II ; rt_rom_data[OP4 | STEP1] = CE
lt_rom_data[OP4 | STEP2] = NIL     ; rt_rom_data[OP4 | STEP2] = NIL
lt_rom_data[OP4 | STEP3] = NIL     ; rt_rom_data[OP4 | STEP3] = NIL
lt_rom_data[OP4 | STEP4] = NIL     ; rt_rom_data[OP4 | STEP4] = NIL

# OP5 instruction
lt_rom_data[OP5 | STEP0] = MI      ; rt_rom_data[OP5 | STEP0] = CO
lt_rom_data[OP5 | STEP1] = RO | II ; rt_rom_data[OP5 | STEP1] = CE
lt_rom_data[OP5 | STEP2] = NIL     ; rt_rom_data[OP5 | STEP2] = NIL
lt_rom_data[OP5 | STEP3] = NIL     ; rt_rom_data[OP5 | STEP3] = NIL
lt_rom_data[OP5 | STEP4] = NIL     ; rt_rom_data[OP5 | STEP4] = NIL

# OP6 instruction
lt_rom_data[OP6 | STEP0] = MI      ; rt_rom_data[OP6 | STEP0] = CO
lt_rom_data[OP6 | STEP1] = RO | II ; rt_rom_data[OP6 | STEP1] = CE
lt_rom_data[OP6 | STEP2] = NIL     ; rt_rom_data[OP6 | STEP2] = NIL
lt_rom_data[OP6 | STEP3] = NIL     ; rt_rom_data[OP6 | STEP3] = NIL
lt_rom_data[OP6 | STEP4] = NIL     ; rt_rom_data[OP6 | STEP4] = NIL

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
with open("left-instruction-rom.bin", "wb") as f:
  f.write(lt_rom_data)
  
with open("right-instruction-rom.bin", "wb") as f:
  f.write(rt_rom_data)