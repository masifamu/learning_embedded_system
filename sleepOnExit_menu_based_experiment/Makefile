# ---------------------------------------------------------------
#  Nazeer Dynamics -- STM32 Bare-Metal Makefile
#  Core: F0   CPU: cortex-m0   Macro: STM32F051x8
# ---------------------------------------------------------------

# -- Toolchain ---------------------------------------------------
CC      = arm-none-eabi-gcc
OBJDUMP = arm-none-eabi-objdump
OBJCOPY = arm-none-eabi-objcopy
SIZE    = arm-none-eabi-size
NM      = arm-none-eabi-nm
READELF = arm-none-eabi-readelf

# -- Compiler flags ----------------------------------------------
#   -mcpu / -mthumb          : target the exact Cortex-M core
#   -ffunction-sections      : one ELF section per function
#   -fdata-sections          : one ELF section per variable
#   (both enable --gc-sections dead-code elimination in the linker)
#   -Os                      : optimise for size
#   -g2                      : full debug info
#   -DSTM32F051x8          : selects the correct ST register-map header
CFLAGS = -mcpu=cortex-m0 -mthumb \
         -Wall -Wextra -Werror -Wundef -Wshadow -Wdouble-promotion \
         -Wformat-truncation -fno-common -Wconversion \
         -g2 -Os -ffunction-sections -fdata-sections \
         -Iinclude -Ilib/nazengg -Ilib/ST -Ilib/ARM \
         -DSTM32F051x8

# -- Linker flags ------------------------------------------------
#   -T                 : our custom linker script (memory layout)
#   -specs=nano.specs  : tiny Newlib-nano C library (saves flash)
#   -specs=nosys.specs : stub syscalls (no OS underneath us)
#   --gc-sections      : discard unused functions / data
#   --cref             : cross-reference table in the map file
#   --Map=             : human-readable map of every symbol placed
LDFLAGS = -Tlib/ST/stm32.ld \
          -specs=nano.specs -specs=nosys.specs -lc -lgcc \
          -Wl,--gc-sections,--cref,--Map=build/output.map

# -- Sources -----------------------------------------------------
SRC  = $(wildcard src/*.c)
SRC += $(wildcard lib/ST/system_*.c)
ASRC = $(wildcard lib/ST/startup_*.s)

OBJ    = $(SRC:.c=.o) $(ASRC:.s=.o)
LIBAMB = lib/nazengg/libnazengg.a
TARGET = build/main.elf
BIN    = build/main.bin
HEX    = build/main.hex

# -- Build -------------------------------------------------------
all: $(LIBAMB) $(TARGET)

$(LIBAMB):
	$(MAKE) -C lib/nazengg

$(TARGET): $(OBJ) $(LIBAMB)
	mkdir -p build
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# GCC can assemble .s files when given -x assembler-with-cpp
%.o: %.s
	$(CC) $(CFLAGS) -x assembler-with-cpp -c $< -o $@

# -- Analysis targets (great for learning!) ----------------------
# Section sizes: text = flash used, data+bss = RAM used
size: $(TARGET)
	@echo ""
	@echo "  text + data  =  total FLASH usage"
	@echo "  data + bss   =  total RAM  usage"
	$(SIZE) $(TARGET)
	@ls -lh $(TARGET)
	@echo ""

# Annotated disassembly -- read the machine code your C compiles to
disasm: $(TARGET)
	$(OBJDUMP) -h -d $(TARGET) > build/main.disasm.s
	@echo "[OK]  Disassembly   -> build/main.disasm.s"

# All symbols sorted by address -- see where each function lives in flash
symbols: $(TARGET)
	$(NM) -n $(TARGET) > build/symbols.txt
	@echo "[OK]  Symbols       -> build/symbols.txt"

# Symbols sorted by size -- find the biggest contributors to flash usage
symbolsize: $(TARGET)
	$(NM) --print-size --size-sort $(TARGET) > build/symbolsize.txt
	@echo "[OK]  By size       -> build/symbolsize.txt"

# Undefined symbols -- things the linker resolves from libc or startup
symbols_undef: $(TARGET)
	$(NM) -u $(TARGET) > build/symbols_undef.txt
	@echo "[OK]  Undefined     -> build/symbols_undef.txt"

# Full ELF section dump -- understand the ELF binary format
readelf: $(TARGET)
	$(READELF) -a $(TARGET) > build/elf_headers.txt
	@echo "[OK]  ELF headers   -> build/elf_headers.txt"

# The linker map is produced automatically by the --Map= flag above
linkermap: $(TARGET)
	@echo "[OK]  Linker map    -> build/output.map"

# Raw binary (needed by st-flash and some other tools)
bin: $(TARGET)
	$(OBJCOPY) -O binary $(TARGET) $(BIN)
	@echo "[OK]  Binary        -> $(BIN)"

# Intel HEX (used by other programmers)
hex: $(TARGET)
	$(OBJCOPY) -O ihex $(TARGET) $(HEX)
	@echo "[OK]  HEX file      -> $(HEX)"

# Strip debug info for a smaller production ELF
strip: $(TARGET)
	arm-none-eabi-strip $(TARGET) -o build/main_stripped.elf
	@echo "[OK]  Stripped ELF  -> build/main_stripped.elf"

# Flash the board via ST-Link (SWD)
flash: $(BIN)
	st-flash write $(BIN) 0x08000000

# Host-side unit tests using native gcc
test:
	mkdir -p build
	gcc -Iinclude -Ilib/nazengg tests/test_main.c -o build/test
	./build/test

clean:
	rm -rf build *.o src/*.o lib/ST/*.o
	$(MAKE) -C lib/nazengg clean

help:
	@echo ""
	@echo "  Available targets:"
	@grep -E '^[a-zA-Z0-9_-]+:' Makefile | grep -v '\.' | \
	  cut -d: -f1 | sort | uniq | awk '{printf "    make %-16s\n", $$1}'
	@echo ""

.PHONY: all clean flash test size disasm symbols symbolsize \
        symbols_undef readelf linkermap bin hex strip help
