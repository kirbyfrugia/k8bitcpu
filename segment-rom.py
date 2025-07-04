# Creates a ROM that will decode a one byte value into a 7-segment display.

# The ROM basically is a lookup for a digit. Given the address in A0-A10,
# the value at that address in the ROM will be the value to feed the 7-segment display.
# Handles 3 digits and a sign indicator (for signed values).

# A10 - A8 are used to select the digit.
#    000 - 1's place
#    001 - 10's place
#    010 - 100's place
#    011 - Negative indicator
# A7 - A0 is the value being displayed on the 7-segment display.

# So to display a value on a 4 digit 7-segment display, you would
# lookup each digit in the ROM.

# Example, showing the digit 123 on the display
# 01111011 is the value for 123 in binary.

# 000 01111011 - This addr in the ROM will contain a 3 for 123
# 001 01111011 - This addr in the ROM will contain a 2 for 123
# 010 01111011 - This addr in the ROM will contain a 1 for 123
# 011 01111011 - This addr in the ROM will contain a 0 for 123, since it is positive.

# The ROM is 2048 bytes in size, with 256 bytes for each digit.
# The first 1024 bytes are used for unsigned values, and the second 1024 bytes
# are used for signed values.
# 0 - 255 1's place, unsigned
# 256 - 511 10's place, unsigned
# 512 - 767 100's place, unsigned
# 768 - 1023 Negative indicator, always 0 for unsigned
# 1024 - 1279 1's place, signed
# 1280 - 1535 10's place, signed
# 1536 - 1791 100's place, signed
# 1792 - 2047 Negative indicator, signed, 0 if positive, 1 if negative.



# Digits for a 7-segment cathode display. Each bit in each byte represents
# a segment in the display
segment_digits = [0b01111110, 0b00110000, 0b01101101, 0b01111001, 0b00110011,
                  0b01011011, 0b01011111, 0b01110000, 0b01111111, 0b01111011]

rom_data = bytearray(2048)

# Fill the ROM with the segment data for unsigned values
for i in range(256):
  rom_data[i] = segment_digits[i % 10]  # Mod 10 to get the 1's digit
  rom_data[i + 256] = segment_digits[(i // 10) % 10]  # Divide by 10 then mod 10 to get the 10's digit
  rom_data[i + 512] = segment_digits[(i // 100) % 10]  # Divide by 100 then mod 10 to get the 100's digit
  rom_data[i + 768] = 0  # Negative indicator, always 0 for unsigned

# Fill the ROM with the segment data for signed values
for val in range(-128, 128):
  i = val & 0xFF  # two's complement representation
  abs_val = abs(val)
  rom_data[i + 1024] = segment_digits[abs_val % 10]
  rom_data[i + 1280] = segment_digits[(abs_val // 10) % 10]
  rom_data[i + 1536] = segment_digits[(abs_val // 100) % 10]
  rom_data[i + 1792] = 1 if val < 0 else 0

# test_value = 123
# print("Negative indicator for unsigned (hex):", hex(rom_data[768 + test_value]))
# print("Hundreds for unsigned (hex):", hex(rom_data[512 + test_value]))
# print("Tens for unsigned (hex):", hex(rom_data[256 + test_value]))
# print("Ones for unsigned (hex):", hex(rom_data[test_value]))

# test_value_abs = abs(-123 & 0xFF)
# print("Negative indicator for signed (hex):", hex(rom_data[1792 + test_value_abs]))
# print("Hundreds for signed (hex):", hex(rom_data[1536 + test_value_abs]))
# print("Tens for signed (hex):", hex(rom_data[1280 + test_value_abs]))
# print("Ones for signed (hex):", hex(rom_data[1024 + test_value_abs]))

# Write rom file
with open("segment-rom.bin", "wb") as f:
  f.write(rom_data)
