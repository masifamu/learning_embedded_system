#!/usr/bin/env python3
"""
Nazeer Dynamics Embedded Project Generator
==========================================
Educational CLI tool for generating bare-metal STM32 / AVR projects.
Teaches every layer: toolchain, linker scripts, CMSIS, Makefiles, and more.

Usage:
  python3 nazeer_gen.py            -- interactive project wizard
  python3 nazeer_gen.py --help     -- show this help
  python3 nazeer_gen.py --about    -- what this tool does & why
  python3 nazeer_gen.py --check    -- check all required tools
"""

import subprocess
import shutil
import sys
import argparse
from pathlib import Path
from datetime import datetime

# -----------------------------------------------------------------------------
#  ANSI colour / style helpers
# -----------------------------------------------------------------------------
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m";  DIM     = "\033[2m"
    RED     = "\033[31m"; GREEN   = "\033[32m";  YELLOW  = "\033[33m"
    BLUE    = "\033[34m"; MAGENTA = "\033[35m";  CYAN    = "\033[36m"
    BRED    = "\033[91m"; BGREEN  = "\033[92m";  BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"; BMAGENTA= "\033[95m";  BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"

def col(color, text):  return f"{color}{text}{C.RESET}"
def ok(msg):           print(f"  {col(C.BGREEN,   '[OK]')} {msg}")
def err(msg):          print(f"  {col(C.BRED,     '[!!]')} {col(C.BRED, msg)}")
def warn(msg):         print(f"  {col(C.BYELLOW,  '[??]')} {col(C.BYELLOW, msg)}")
def info(msg):         print(f"  {col(C.BCYAN,    '[--]')} {msg}")
def tip(msg):          print(f"  {col(C.BMAGENTA, '[>>]')} {col(C.BMAGENTA, msg)}")

def section(title):
    width = 64
    bar = col(C.CYAN, "─" * width)
    print(f"\n{bar}")
    print(f"{col(C.BOLD + C.BCYAN, '  ' + title)}")
    print(bar)

def teach(lines):
    """Print a coloured educational callout box."""
    width = 80
    print(f"\n  {col(C.YELLOW,'┌' + '─'*width + '┐')}")
    print(f"  {col(C.YELLOW,'│')} {col(C.BYELLOW+C.BOLD,' WHY THIS MATTERS' + ' '*(width-18))}{col(C.YELLOW,'│')}")
    print(f"  {col(C.YELLOW,'├' + '─'*width + '┤')}")
    for line in lines:
        chunks = [line[i:i + width - 2] for i in range(0, max(len(line), 1), width - 2)]
        for chunk in chunks:
            pad = width - 2 - len(chunk)
            print(f"  {col(C.YELLOW,'│')}  {col(C.DIM, chunk)}{' '*pad}  {col(C.YELLOW,'│')}")
    print(f"  {col(C.YELLOW,'└' + '─'*width + '┘')}\n")

# -----------------------------------------------------------------------------
#  Global state
# -----------------------------------------------------------------------------
stm32_core = ""
mcu_macro  = ""

# -----------------------------------------------------------------------------
#  Banner
# -----------------------------------------------------------------------------
def print_banner():
    ts      = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    version = "v2.0.0"
    print(col(C.CYAN, """
╬══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ███╭   ██╮ █████╮ ███████╮███████╮███████╮██████╮       ║
║      ████╭  ██║██╔══██╮╚══███╌██╔════╝██╔════╝██╔══██╮       ║
║      ██╔██╭ ██║███████║  ███╌ █████╮  █████╮  ██████╌┘       ║
║      ██║╚██╭██║██╔══██║ ███╌  ██╔══╝  ██╔══╝  ██╔══██╮       ║
║      ██║ ╚████║██║  ██║███████╮███████╮███████╮██║  ██║      ║
║      ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝      ║
║                                                              ║
║          Embedded Systems Project Generator                  ║
║          STM32 · AVR · CMSIS · Bare-Metal                    ║"""))
    print(col(C.CYAN, f"║          {ts}   {version}                       ║"))
    print(col(C.CYAN, "╚══════════════════════════════════════════════════════════════╝"))
    print(f"\n  {col(C.DIM,'Type')}\n  {col(C.BCYAN,'--help')} {col(C.DIM,'for options,')} "
          f"\n  {col(C.BCYAN,'--about')} {col(C.DIM,'to learn what this tool teaches,')} "
          f"\n  {col(C.BCYAN,'--check')} {col(C.DIM,'to audit your toolchain.')}\n")
# -----------------------------------------------------------------------------
#  About / Educational overview
# -----------------------------------------------------------------------------
ABOUT_TEXT = [
    ("What does this tool build?",
     "A complete bare-metal embedded project -- no Arduino, no HAL magic.\n"
     "You get: Makefile/CMake build system, CMSIS headers fetched from\n"
     "official ST & ARM repos, a real linker script you configure, startup\n"
     "assembly, and a tiny HAL-free LED-blink skeleton to build on."),

    ("Why bare-metal / CMSIS-only?",
     "ST's HAL is great for products, but it hides *how* the hardware works.\n"
     "Bare-metal forces you to understand: memory maps, vector tables,\n"
     "clock trees, peripheral registers, and the GNU linker -- skills every\n"
     "serious embedded engineer needs."),

    ("What is CMSIS?",
     "Cortex Microcontroller Software Interface Standard -- ARM's portable\n"
     "C headers that give you named register structs and IRQ numbers for\n"
     "every Cortex-M device, without depending on vendor HAL layers."),

    ("What is a linker script?",
     "A .ld file that tells the linker where to place each section (.text,\n"
     ".data, .bss) in your target's memory map.  Without it the linker\n"
     "cannot produce a runnable binary for your specific MCU."),

    ("What is the startup file?",
     "Assembly (.s) or C code that runs *before* main().  It sets the\n"
     "initial stack pointer, copies .data from FLASH to RAM, zeroes .bss,\n"
     "calls SystemInit(), and finally jumps to main()."),

    ("Layers this tool teaches",
     "1. Cross-compiler toolchain (arm-none-eabi-gcc / avr-gcc)\n"
     "2. CMSIS Core (ARM) + CMSIS-Device (ST): headers & startup\n"
     "3. GNU Linker scripts & memory layout\n"
     "4. Makefile multi-target build, ELF analysis (nm, objdump, size)\n"
     "5. Flash programming via st-flash / avrdude\n"
     "6. Debug stack: OpenOCD + GDB + Telnet"),
]

def print_about():
    section("ABOUT -- What This Tool Teaches")
    for title, body in ABOUT_TEXT:
        print(f"\n  {col(C.BOLD+C.BBLUE,'●')} {col(C.BOLD + C.BWHITE, title)}")
        for line in body.split("\n"):
            print(f"      {col(C.DIM, line)}")
    print()

# -----------------------------------------------------------------------------
#  Tool definitions & checker
# -----------------------------------------------------------------------------
TOOLS = {
    "git": (
        "Version control & used to clone CMSIS repos from GitHub",
        "all targets",
        "git",
        None,
    ),
    "make": (
        "GNU Make -- drives the build via Makefile",
        "Make-based projects",
        "make",
        None,
    ),
    "cmake": (
        "CMake -- alternative meta-build system",
        "CMake-based projects",
        "cmake",
        None,
    ),
    "arm-none-eabi-gcc": (
        "ARM bare-metal cross-compiler -- turns your C into Cortex-M machine code",
        "STM32 projects",
        "gcc-arm-none-eabi binutils-arm-none-eabi",
        None,
    ),
    "arm-none-eabi-gdb": (
        "ARM GDB -- source-level debugger for Cortex-M targets",
        "STM32 debugging",
        "gdb-arm-none-eabi",
        None,
    ),
    "avr-gcc": (
        "AVR cross-compiler -- turns your C into ATmega machine code",
        "AVR projects",
        "gcc-avr avr-libc",
        None,
    ),
    "avrdude": (
        "AVR flash programmer -- uploads .hex to your AVR board",
        "AVR flashing",
        "avrdude",
        None,
    ),
    "st-flash": (
        "ST-Link flash tool -- programs STM32 via USB SWD/JTAG",
        "STM32 flashing",
        "stlink-tools",
        "See also: https://github.com/stlink-org/stlink",
    ),
    "openocd": (
        "Open On-Chip Debugger -- GDB server + flash programmer",
        "STM32/AVR debugging",
        "openocd",
        None,
    ),
}

def check_one_tool(name):
    return shutil.which(name) is not None

def print_tool_status(name, found, desc):
    status = col(C.BGREEN, "[OK]     ") if found else col(C.BRED, "[MISSING]")
    print(f"  {status}  {col(C.BOLD, name.ljust(26))} {col(C.DIM, desc)}")

def check_all_tools(quiet=False):
    """Audit every tool. Returns dict {name: bool}."""
    section("TOOLCHAIN AUDIT")
    results = {}
    for name, (desc, req, apt, note) in TOOLS.items():
        found = check_one_tool(name)
        results[name] = found
        if not quiet or not found:
            print_tool_status(name, found, f"[{req}]  {desc}")
    missing = [n for n, found in results.items() if not found]
    if not missing:
        print(f"\n  {col(C.BGREEN + C.BOLD, 'All tools found!  Your system is ready.')}\n")
    else:
        print(f"\n  {col(C.BYELLOW + C.BOLD, str(len(missing)) + ' tool(s) missing.')}")
        _offer_install(missing)
    return results

def _offer_install(missing):
    apt_pkgs = []
    notes    = []
    for name in missing:
        _, _, apt, note = TOOLS[name]
        if apt:
            apt_pkgs.extend(apt.split())
        if note:
            notes.append((name, note))

    # De-duplicate while preserving order
    seen = set()
    apt_pkgs = [p for p in apt_pkgs if not (p in seen or seen.add(p))]

    if apt_pkgs:
        cmd = "sudo apt install -y " + " ".join(apt_pkgs)
        print(f"\n  {col(C.BCYAN, 'To install all missing tools on Ubuntu/Debian, run:')}")
        print(f"\n    {col(C.BOLD + C.BGREEN, cmd)}\n")
        choice = input(col(C.BYELLOW, "  --> Run this command now? [y/N]: ")).strip().lower()
        if choice == "y":
            ret = subprocess.run(cmd, shell=True)
            if ret.returncode == 0:
                ok("Installation complete -- re-run the tool to verify.")
            else:
                err("apt install failed. Check your internet connection or run manually.")
        else:
            tip("Run the command above whenever you are ready, then restart the generator.")

    for name, note in notes:
        tip(f"{name}: {note}")

def require_tools_for_mcu(mcu, build_system):
    needed = ["git", build_system]
    if mcu == "stm32":
        needed += ["arm-none-eabi-gcc"]
    elif mcu == "avr":
        needed += ["avr-gcc"]

    missing = [t for t in needed if not check_one_tool(t)]
    if missing:
        section("CRITICAL TOOLS MISSING")
        for t in missing:
            desc = TOOLS.get(t, ("unknown tool", "", "", None))[0]
            print_tool_status(t, False, desc)
        _offer_install(missing)
        print()
        err("Cannot continue until required tools are installed.")
        sys.exit(1)

    optional = []
    if mcu == "stm32":
        optional = ["st-flash", "openocd", "arm-none-eabi-gdb"]
    elif mcu == "avr":
        optional = ["avrdude", "openocd"]
    for t in optional:
        if not check_one_tool(t):
            warn(f"Optional tool '{t}' not found -- some Makefile targets will not work.")

# -----------------------------------------------------------------------------
#  Interactive helpers
# -----------------------------------------------------------------------------
def ask(prompt, options, descriptions=None):
    print(f"\n  {col(C.BOLD + C.BWHITE, prompt)}")
    for i, opt in enumerate(options, 1):
        desc = f"  {col(C.DIM, '--  ' + descriptions[i - 1])}" if descriptions else ""
        print(f"    {col(C.BCYAN, str(i) + '.')}  {col(C.BOLD, opt)}{desc}")
    while True:
        try:
            raw = input(col(C.BYELLOW, f"\n  Choice [1-{len(options)}]: ")).strip()
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                chosen = options[idx]
                ok(f"Selected: {col(C.BOLD, chosen)}")
                return chosen
        except (ValueError, KeyboardInterrupt):
            pass
        warn("Invalid choice. Please enter a number shown above.")

def ask_text(prompt, default=None):
    hint  = f" [{col(C.DIM, default)}]" if default else ""
    raw   = input(f"\n  {col(C.BOLD + C.BWHITE, prompt)}{hint}: ").strip()
    value = raw if raw else default
    if value:
        ok(f"Using: {col(C.BOLD, str(value))}")
    return value

def ask_numbered_files(prompt, files, teach_lines=None, min_select=1, max_select=None):
    if teach_lines:
        teach(teach_lines)
    max_select = max_select or len(files)
    print(f"\n  {col(C.BOLD + C.BWHITE, prompt)}")
    for i, f in enumerate(files, 1):
        print(f"    {col(C.BCYAN, str(i) + '.')}  {f.name}")
    tip(f"Enter comma-separated numbers -- choose {min_select} to {max_select}  (e.g.  1  or  1,3)")
    while True:
        try:
            raw     = input(col(C.BYELLOW, "\n  Selection: ")).strip()
            indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
            if (min_select <= len(indices) <= max_select
                    and all(0 <= i < len(files) for i in indices)):
                selected = [files[i] for i in indices]
                for s in selected:
                    ok(f"Selected: {s.name}")
                return selected
        except (ValueError, KeyboardInterrupt):
            pass
        warn(f"Please pick between {min_select} and {max_select} valid numbers.")

# -----------------------------------------------------------------------------
#  Project structure & common files
# -----------------------------------------------------------------------------
def create_structure(base_path):
    for d in ["src", "include", "tests", "build",
              "toolchain", "lib/nazengg", "lib/ARM", "lib/ST", "docs"]:
        (base_path / d).mkdir(parents=True, exist_ok=True)
    ok("Directory tree created.")

def write_common_files(base_path, project_name, mcu):
    readme = f"""# {project_name}

Auto-generated bare-metal {mcu.upper()} project by Nazeer Dynamics Generator.

## Quick start

```bash
make          # build
make size     # check flash/RAM usage
make flash    # program the board (requires st-flash / avrdude)
make help     # list all targets
```

## Project layout

```
src/          -- your application C files
include/      -- shared headers
lib/nazengg/  -- thin portable HAL built by this project
lib/ST/       -- ST CMSIS-Device files (startup, system, register defs)
lib/ARM/      -- ARM CMSIS-Core headers (core_cm*.h etc.)
tests/        -- host-side unit tests compiled with native gcc
build/        -- generated artefacts (.elf, .bin, .hex, map ...)
toolchain/    -- CMake toolchain files (if CMake build chosen)
docs/         -- documentation
```

## Learning resources

- CMSIS docs:        https://arm-software.github.io/CMSIS_5/Core/html/index.html
- GNU linker manual: https://sourceware.org/binutils/docs/ld/
- OpenOCD docs:      https://openocd.org/doc/html/index.html
"""
    (base_path / "README.md").write_text(readme)
    (base_path / ".gitignore").write_text("build/\nbin/\n*.o\n*.elf\n*.bin\n*.hex\n*.map\n*.a\n")
    ok("README.md and .gitignore written.")

# -----------------------------------------------------------------------------
#  Application skeletons
# -----------------------------------------------------------------------------
def write_main_c_stm32(base_path):
    (base_path / "src" / "main.c").write_text('''\
#include "nazengg.h"

/* Simple busy-wait delay (not accurate, just for blink demo) */
static void delay(volatile unsigned int count) {
    while (count--) {
        __asm__ volatile ("nop");   /* tell the compiler not to optimise away */
    }
}

int main(void) {
    nazengg_init();         /* configure the LED GPIO */

    while (1) {
        nazengg_toggle_led();
        delay(1000000UL);   /* ~0.5 s at 8 MHz HSI -- tune to taste */
    }

    /* Bare-metal main() must never return -- the MCU has nowhere to go. */
    return 0;
}
''')
    ok("src/main.c written  (STM32 LED blink skeleton).")

def write_main_c_avr(base_path):
    (base_path / "src" / "main.c").write_text('''\
#include <avr/io.h>
#include <util/delay.h>
#include "nazengg.h"

int main(void) {
    nazengg_init();           /* set PB5 (Arduino pin 13) as output */

    while (1) {
        nazengg_toggle_led();
        _delay_ms(500);       /* 500 ms hardware delay -- accurate, no busy-wait */
    }

    return 0;   /* never reached */
}
''')
    ok("src/main.c written  (AVR LED blink skeleton).")

def write_unit_test_stub(base_path):
    (base_path / "tests" / "test_main.c").write_text('''\
/*
 * Host-side unit tests -- compiled with native gcc, NOT the cross-compiler.
 * "make test" builds and runs this file on your development machine.
 *
 * WHY: Cross-compiled tests need an emulator or real hardware.  Pure-logic
 * functions (CRC, state-machines, protocol parsers) can be tested here
 * without any target hardware present.
 */
#include <assert.h>
#include <stdio.h>

static int clamp(int v, int lo, int hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

int main(void) {
    assert(clamp(5,  0, 10) == 5);
    assert(clamp(-1, 0, 10) == 0);
    assert(clamp(99, 0, 10) == 10);
    printf("All tests passed.\\n");
    return 0;
}
''')
    ok("tests/test_main.c written  (host-side unit-test stub).")

# -----------------------------------------------------------------------------
#  nazengg library -- STM32
# -----------------------------------------------------------------------------
def write_nazengg_lib_stm32(base_path, mcpu, macro):
    lib = base_path / "lib" / "nazengg"

    # Use the FAMILY umbrella header (e.g. stm32f0xx.h for F0 series).
    # It reads the -D<macro> compiler flag and pulls in the correct device
    # header automatically -- the case is always right and nazengg.c stays
    # device-agnostic within the whole family.
    umbrella = f"stm32{stm32_core.lower()}xx.h"

    (lib / "nazengg.h").write_text('''\
#pragma once
/*
 * nazengg -- minimal portable LED driver for STM32.
 * Edit nazengg.c to retarget to a different GPIO pin.
 */
void nazengg_init(void);
void nazengg_toggle_led(void);
''')

    (lib / "nazengg.c").write_text(f'''\
#include "nazengg.h"
/*
 * Include the FAMILY umbrella header (e.g. stm32f0xx.h), not the
 * device-specific one directly.  The umbrella reads the -D{macro}
 * flag and pulls in the correct chip header automatically.
 *
 * PC9 is the green LED on the STM32F0-Discovery board.
 * Change GPIOC / RCC_AHBENR_GPIOCEN / GPIO_ODR_9 for your own board.
 */
#include "{umbrella}"

void nazengg_init(void) {{
    /* 1. Gate the GPIO clock -- without this the peripheral is dead */
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

    /* 2. Set PC9 as general-purpose output (MODER = 0b01) */
    GPIOC->MODER &= ~GPIO_MODER_MODER9;    /* clear both bits first */
    GPIOC->MODER |=  GPIO_MODER_MODER9_0;  /* bit0=1 -> output mode  */

    /* 3. Output type: push-pull (reset default, explicit for clarity) */
    GPIOC->OTYPER &= ~GPIO_OTYPER_OT_9;

    /* 4. No pull-up / pull-down (reset default) */
    GPIOC->PUPDR  &= ~GPIO_PUPDR_PUPDR9;
}}

void nazengg_toggle_led(void) {{
    GPIOC->ODR ^= GPIO_ODR_9;   /* XOR -- atomic read-modify-write on ODR */
}}
''')

    (lib / "Makefile").write_text(f'''\
SRC     = $(wildcard *.c)
OBJ     = $(SRC:.c=.o)
INCLUDE = -I. -I../../lib/ST -I../../lib/ARM

CFLAGS  = -mcpu={mcpu} -mthumb -g2 -Wall -Wextra -Os $(INCLUDE) -D{macro}

all: libnazengg.a

%.o: %.c
\tarm-none-eabi-gcc $(CFLAGS) -c $< -o $@

libnazengg.a: $(OBJ)
\tarm-none-eabi-ar rcs $@ $^

clean:
\trm -f *.o libnazengg.a
''')
    ok("lib/nazengg/  STM32 library written.")

# -----------------------------------------------------------------------------
#  nazengg library -- AVR
# -----------------------------------------------------------------------------
def write_nazengg_lib_avr(base_path, mmcu="atmega328p"):
    lib = base_path / "lib" / "nazengg"

    (lib / "nazengg.h").write_text('''\
#pragma once
/*
 * nazengg -- minimal portable LED driver for AVR (ATmega328P / Arduino UNO).
 * PB5 = Arduino pin 13 = the built-in LED.
 */
void nazengg_init(void);
void nazengg_toggle_led(void);
''')

    (lib / "nazengg.c").write_text('''\
#include <avr/io.h>
#include "nazengg.h"

/*
 * AVR GPIO registers:
 *   DDRx  -- Data Direction (1=output, 0=input)
 *   PORTx -- Output value
 *   PINx  -- Input read; writing 1 here toggles the pin (AVR hardware feature)
 *
 * PB5 = bit 5 of PORTB = Arduino pin 13 / built-in LED.
 */
void nazengg_init(void) {
    DDRB  |=  (1 << DDB5);    /* set PB5 as output */
    PORTB &= ~(1 << PORTB5);  /* start LED off     */
}

void nazengg_toggle_led(void) {
    PINB = (1 << PINB5);      /* write to PINB -> hardware toggles the output */
}
''')

    (lib / "Makefile").write_text(f'''\
SRC     = $(wildcard *.c)
OBJ     = $(SRC:.c=.o)

CFLAGS  = -mmcu={mmcu} -Wall -Wextra -Os -I.

all: libnazengg.a

%.o: %.c
\tavr-gcc $(CFLAGS) -c $< -o $@

libnazengg.a: $(OBJ)
\tavr-ar rcs $@ $^

clean:
\trm -f *.o libnazengg.a
''')
    ok("lib/nazengg/  AVR library written.")

# -----------------------------------------------------------------------------
#  STM32 Makefile
# -----------------------------------------------------------------------------
CORE_TO_MCPU = {
    "F0": "cortex-m0",    "F1": "cortex-m3",    "F2": "cortex-m3",
    "F3": "cortex-m4",    "F4": "cortex-m4",    "F7": "cortex-m7",
    "G0": "cortex-m0plus","G4": "cortex-m4",    "H7": "cortex-m7",
    "L0": "cortex-m0plus","L1": "cortex-m3",    "L4": "cortex-m4",
    "L5": "cortex-m33",   "U5": "cortex-m33",
}

def write_makefile_stm32(base_path, mcpu, macro, use_nazengg):
    nazengg_link = "$(LIBAMB)" if use_nazengg else ""
    nazengg_dep  = "\n$(LIBAMB):\n\t$(MAKE) -C lib/nazengg\n" if use_nazengg else ""

    (base_path / "Makefile").write_text(f'''\
# ---------------------------------------------------------------
#  Nazeer Dynamics -- STM32 Bare-Metal Makefile
#  Core: {stm32_core}   CPU: {mcpu}   Macro: {macro}
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
#   -D{macro}          : selects the correct ST register-map header
CFLAGS = -mcpu={mcpu} -mthumb \\
         -Wall -Wextra -Werror -Wundef -Wshadow -Wdouble-promotion \\
         -Wformat-truncation -fno-common -Wconversion \\
         -g2 -Os -ffunction-sections -fdata-sections \\
         -Iinclude -Ilib/nazengg -Ilib/ST -Ilib/ARM \\
         -D{macro}

# -- Linker flags ------------------------------------------------
#   -T                 : our custom linker script (memory layout)
#   -specs=nano.specs  : tiny Newlib-nano C library (saves flash)
#   -specs=nosys.specs : stub syscalls (no OS underneath us)
#   --gc-sections      : discard unused functions / data
#   --cref             : cross-reference table in the map file
#   --Map=             : human-readable map of every symbol placed
LDFLAGS = -Tlib/ST/stm32.ld \\
          -specs=nano.specs -specs=nosys.specs -lc -lgcc \\
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
{nazengg_dep}
$(TARGET): $(OBJ) {nazengg_link}
\tmkdir -p build
\t$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

# GCC can assemble .s files when given -x assembler-with-cpp
%.o: %.s
\t$(CC) $(CFLAGS) -x assembler-with-cpp -c $< -o $@

# -- Analysis targets (great for learning!) ----------------------
# Section sizes: text = flash used, data+bss = RAM used
size: $(TARGET)
\t@echo ""
\t@echo "  text + data  =  total FLASH usage"
\t@echo "  data + bss   =  total RAM  usage"
\t$(SIZE) $(TARGET)
\t@ls -lh $(TARGET)
\t@echo ""

# Annotated disassembly -- read the machine code your C compiles to
disasm: $(TARGET)
\t$(OBJDUMP) -h -d $(TARGET) > build/main.disasm.s
\t@echo "[OK]  Disassembly   -> build/main.disasm.s"

# All symbols sorted by address -- see where each function lives in flash
symbols: $(TARGET)
\t$(NM) -n $(TARGET) > build/symbols.txt
\t@echo "[OK]  Symbols       -> build/symbols.txt"

# Symbols sorted by size -- find the biggest contributors to flash usage
symbolsize: $(TARGET)
\t$(NM) --print-size --size-sort $(TARGET) > build/symbolsize.txt
\t@echo "[OK]  By size       -> build/symbolsize.txt"

# Undefined symbols -- things the linker resolves from libc or startup
symbols_undef: $(TARGET)
\t$(NM) -u $(TARGET) > build/symbols_undef.txt
\t@echo "[OK]  Undefined     -> build/symbols_undef.txt"

# Full ELF section dump -- understand the ELF binary format
readelf: $(TARGET)
\t$(READELF) -a $(TARGET) > build/elf_headers.txt
\t@echo "[OK]  ELF headers   -> build/elf_headers.txt"

# The linker map is produced automatically by the --Map= flag above
linkermap: $(TARGET)
\t@echo "[OK]  Linker map    -> build/output.map"

# Raw binary (needed by st-flash and some other tools)
bin: $(TARGET)
\t$(OBJCOPY) -O binary $(TARGET) $(BIN)
\t@echo "[OK]  Binary        -> $(BIN)"

# Intel HEX (used by other programmers)
hex: $(TARGET)
\t$(OBJCOPY) -O ihex $(TARGET) $(HEX)
\t@echo "[OK]  HEX file      -> $(HEX)"

# Strip debug info for a smaller production ELF
strip: $(TARGET)
\tarm-none-eabi-strip $(TARGET) -o build/main_stripped.elf
\t@echo "[OK]  Stripped ELF  -> build/main_stripped.elf"

# Flash the board via ST-Link (SWD)
flash: $(BIN)
\tst-flash write $(BIN) 0x08000000

# Host-side unit tests using native gcc
test:
\tmkdir -p build
\tgcc -Iinclude -Ilib/nazengg tests/test_main.c -o build/test
\t./build/test

clean:
\trm -rf build *.o src/*.o lib/ST/*.o
\t$(MAKE) -C lib/nazengg clean

help:
\t@echo ""
\t@echo "  Available targets:"
\t@grep -E '^[a-zA-Z0-9_-]+:' Makefile | grep -v '\\.' | \\
\t  cut -d: -f1 | sort | uniq | awk '{{printf "    make %-16s\\n", $$1}}'
\t@echo ""

.PHONY: all clean flash test size disasm symbols symbolsize \\
        symbols_undef readelf linkermap bin hex strip help
''')
    ok("Makefile written  (STM32, with full ELF analysis targets).")

# -----------------------------------------------------------------------------
#  AVR Makefile
# -----------------------------------------------------------------------------
def write_makefile_avr(base_path, mmcu, f_cpu, use_nazengg):
    nazengg_link = "-L lib/nazengg -lnazengg" if use_nazengg else ""
    nazengg_dep  = "\n$(LIBAMB):\n\t$(MAKE) -C lib/nazengg\n" if use_nazengg else ""
    libamb_dep   = "$(LIBAMB)" if use_nazengg else ""

    (base_path / "Makefile").write_text(f'''\
# ---------------------------------------------------------------
#  Nazeer Dynamics -- AVR Bare-Metal Makefile
#  MCU: {mmcu}   F_CPU: {f_cpu} Hz
# ---------------------------------------------------------------

MMCU  = {mmcu}
F_CPU = {f_cpu}

CC      = avr-gcc
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
SIZE    = avr-size
NM      = avr-nm

# -- Compiler flags ----------------------------------------------
#   -mmcu   : selects exact AVR core, memory model, I/O header
#   -DF_CPU : makes _delay_ms() / _delay_us() accurate
#   -Os     : optimise for size
CFLAGS = -mmcu=$(MMCU) -DF_CPU=$(F_CPU)UL \\
         -Wall -Wextra -Os -g \\
         -Iinclude -Ilib/nazengg

SRC    = $(wildcard src/*.c)
OBJ    = $(SRC:.c=.o)
LIBAMB = lib/nazengg/libnazengg.a
TARGET = build/main.elf
HEX    = build/main.hex

all: {libamb_dep} $(TARGET) $(HEX) size
{nazengg_dep}
$(TARGET): $(OBJ) {libamb_dep}
\tmkdir -p build
\t$(CC) $(CFLAGS) -o $@ $(OBJ) {nazengg_link}

$(HEX): $(TARGET)
\t$(OBJCOPY) -O ihex -R .eeprom $(TARGET) $(HEX)
\t@echo "[OK]  HEX file -> $(HEX)"

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

size: $(TARGET)
\t@echo ""
\t$(SIZE) --format=avr --mcu=$(MMCU) $(TARGET)
\t@echo ""

disasm: $(TARGET)
\t$(OBJDUMP) -h -d $(TARGET) > build/main.disasm.s
\t@echo "[OK]  Disassembly -> build/main.disasm.s"

symbols: $(TARGET)
\t$(NM) -n $(TARGET) > build/symbols.txt
\t@echo "[OK]  Symbols     -> build/symbols.txt"

# Adjust -c (programmer) and -P (port) for your setup
flash: $(HEX)
\tavrdude -p $(MMCU) -c arduino -P /dev/ttyUSB0 -b 115200 -U flash:w:$(HEX):i

test:
\tmkdir -p build
\tgcc -Iinclude -Ilib/nazengg tests/test_main.c -o build/test
\t./build/test

clean:
\trm -rf build *.o src/*.o
\t$(MAKE) -C lib/nazengg clean

help:
\t@echo ""
\t@echo "  Available targets:"
\t@grep -E '^[a-zA-Z0-9_-]+:' Makefile | grep -v '\\.' | \\
\t  cut -d: -f1 | sort | uniq | awk '{{printf "    make %-16s\\n", $$1}}'
\t@echo ""

.PHONY: all clean flash test size disasm symbols help
''')
    ok("Makefile written  (AVR).")

# -----------------------------------------------------------------------------
#  CMake (both MCUs)
# -----------------------------------------------------------------------------
def write_cmake(base_path, mcu, mcpu_or_mmcu):
    if mcu == "stm32":
        compiler = "arm-none-eabi-gcc"
        cflags   = f"-mcpu={mcpu_or_mmcu} -mthumb -Os -g -Wall -ffunction-sections"
    else:
        compiler = "avr-gcc"
        cflags   = f"-mmcu={mcpu_or_mmcu} -DF_CPU=16000000UL -Os -g -Wall"

    tc = base_path / "toolchain" / f"{mcu}_toolchain.cmake"
    tc.write_text(f"""\
# Cross-compiler toolchain for {mcu.upper()}
# cmake -DCMAKE_TOOLCHAIN_FILE=../toolchain/{mcu}_toolchain.cmake ..

set(CMAKE_SYSTEM_NAME      Generic)
set(CMAKE_SYSTEM_PROCESSOR {mcpu_or_mmcu})
set(CMAKE_C_COMPILER       {compiler})
set(CMAKE_C_FLAGS_INIT     "{cflags}")

# Prevent CMake from probing the compiler with a host-side link step
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
""")

    (base_path / "CMakeLists.txt").write_text(f"""\
cmake_minimum_required(VERSION 3.16)
project({base_path.name} C ASM)

include_directories(include lib/nazengg lib/ST lib/ARM)
file(GLOB SOURCES "src/*.c" "lib/ST/system_*.c" "lib/ST/startup_*.s")
add_executable(main.elf ${{SOURCES}})

enable_testing()
add_executable(test_main tests/test_main.c)
target_include_directories(test_main PRIVATE include lib/nazengg)
add_test(NAME unit_tests COMMAND test_main)
""")
    ok("CMakeLists.txt and toolchain file written.")

# -----------------------------------------------------------------------------
#  Linker script wizard (STM32 only)
# -----------------------------------------------------------------------------
def write_linker_script(base_path):
    section("LINKER SCRIPT WIZARD")
    teach([
        "The linker script (.ld) tells the GNU linker the physical memory map",
        "of your specific MCU and how to arrange your binary inside it.",
        "",
        "  FLASH : read-only, your code and constants live here",
        "  RAM   : read-write, stack, heap, .bss, .data live here",
        "",
        "Key symbols the startup file depends on:",
        "  _estack  -- initial stack pointer (top of RAM)",
        "  _sdata / _edata / _sidata -- used to copy .data FLASH→RAM at boot",
        "  _sbss  / _ebss            -- used to zero .bss at boot",
        "",
        "Without this file the linker cannot place your binary correctly.",
    ])

    info("Check your MCU datasheet / reference manual for exact addresses.")
    print(f"  {col(C.DIM, 'Example: STM32F030x6 -> FLASH 0x08000000 / 32K,  RAM 0x20000000 / 4K')}")

    entry     = ask_text("Entry point symbol (2nd word in the vector table)", "Reset_Handler")
    flash_org = ask_text("FLASH origin address", "0x08000000")
    flash_len = ask_text("FLASH length  (e.g. 32K, 64K, 256K)", "64K")
    ram_org   = ask_text("RAM origin address",   "0x20000000")
    ram_len   = ask_text("RAM length    (e.g. 4K, 20K, 128K)", "20K")

    dst = base_path / "lib" / "ST" / "stm32.ld"
    dst.write_text(f'''\
/*
 * Linker script for {base_path.name}
 * Generated by Nazeer Dynamics Project Generator
 *
 * FLASH : program code + read-only data (read-only)
 * RAM   : stack + heap + .bss + initialised .data (read-write)
 *
 * _estack = top of RAM = initial stack pointer value.
 * Cortex-M stacks grow downward, so the stack starts at the top.
 */

ENTRY({entry})

MEMORY
{{
    FLASH (rx)  : ORIGIN = {flash_org}, LENGTH = {flash_len}
    RAM   (rwx) : ORIGIN = {ram_org},   LENGTH = {ram_len}
}}

_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{{
    /*
     * .isr_vector -- MUST be first in FLASH.
     * At reset the Cortex-M hardware reads:
     *   word 0: initial stack pointer (_estack)
     *   word 1: address of Reset_Handler
     * from the very start of the FLASH region.
     */
    .isr_vector :
    {{
        KEEP(*(.isr_vector))
    }} > FLASH

    /*
     * .text -- all executable code and read-only data (.rodata).
     * _etext is used by the startup file to locate where .data is
     * stored in FLASH (its Load Memory Address).
     */
    .text :
    {{
        *(.text*)
        *(.glue_7)      /* ARM/Thumb interworking stubs */
        *(.glue_7t)
        *(.eh_frame)
        KEEP(*(.init))
        KEEP(*(.fini))
        *(.rodata*)
        . = ALIGN(4);
        _etext = .;
    }} > FLASH

    /*
     * .data -- initialised global and static variables.
     *
     * VMA (Virtual Memory Address) = run-time location in RAM
     * LMA (Load Memory Address)    = stored location in FLASH
     *
     * The startup file copies bytes [_sidata .. _sidata + (_edata-_sdata)]
     * from FLASH into RAM before main() runs.
     */
    .data :
    {{
        . = ALIGN(4);
        _sdata = .;         /* start of RAM destination */
        *(.data*)
        . = ALIGN(4);
        _edata = .;         /* end of RAM destination   */
    }} > RAM AT > FLASH

    _sidata = LOADADDR(.data);  /* start of FLASH source */

    /*
     * .bss -- uninitialised globals and statics.
     * The linker reserves space in RAM only (nothing stored in FLASH).
     * The startup file zeroes this region (_sbss to _ebss) before main().
     */
    .bss :
    {{
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    }} > RAM
}}
''')
    ok("Linker script written -> lib/ST/stm32.ld")
    teach([
        "'.data > RAM AT > FLASH' means:",
        "  VMA (runtime address) is in RAM  -- where the CPU reads/writes it",
        "  LMA (load address)    is in FLASH -- where it is stored in the image",
        "The startup file copies .data from its LMA to its VMA before main().",
        "Omitting this copy is one of the most common bare-metal boot bugs.",
    ])

# -----------------------------------------------------------------------------
#  STM32 core series prompt
# -----------------------------------------------------------------------------
def ask_stm32_core():
    global stm32_core
    section("STM32 CORE SERIES")
    teach([
        "The core series (F0, F4, G0 ...) determines three things:",
        "  1. The ARM Cortex-M revision and the -mcpu= compiler flag",
        "  2. Which CMSIS-Device GitHub repo to clone  (cmsis-device-f0 etc.)",
        "  3. Which startup file and register headers belong to your chip",
        "",
        "Supported series: F0 F1 F2 F3 F4 F7 G0 G4 H7 L0 L1 L4 L5 U5",
    ])
    while True:
        raw  = ask_text("STM32 core series (e.g. F0, F4, G0)", "F0")
        core = raw.upper()
        if core in CORE_TO_MCPU:
            stm32_core = core
            ok(f"Core: {core}  ->  CPU: {CORE_TO_MCPU[core]}")
            return CORE_TO_MCPU[core]
        err(f"'{core}' not recognised.  Valid: {', '.join(CORE_TO_MCPU.keys())}")

# -----------------------------------------------------------------------------
#  ST CMSIS-Device files
# -----------------------------------------------------------------------------
def macro_from_startup_file(name: str) -> str:
    """'startup_stm32f030x6.s'  →  'STM32F030x6'"""
    stem = Path(name).stem
    if not stem.startswith("startup_"):
        raise ValueError(f"Expected 'startup_' prefix, got: {name}")
    device = stem[len("startup_"):]          # stm32f030x6
    return device.upper().replace("X", "x") # STM32F030x6  (lowercase x preserved)

def setup_stm32_device_files(base_path: Path) -> str:
    global stm32_core, mcu_macro
    section("CLONING ST CMSIS-DEVICE FILES")
    teach([
        "ST publishes official CMSIS-Device packs on GitHub:",
        "  github.com/STMicroelectronics/cmsis-device-<series>",
        "",
        "We need three things from this repo:",
        "  1. startup_stm32*.s  -- the first code that runs on your MCU",
        "  2. system_stm32*.c   -- SystemInit() and clock configuration",
        "  3. Register-map headers (stm32*.h) -- peripheral structs and bit masks",
    ])

    repo_url  = f"https://github.com/STMicroelectronics/cmsis-device-{stm32_core.lower()}.git"
    clone_dir = base_path / "temp_st_repo"
    st_dir    = base_path / "lib" / "ST"
    st_dir.mkdir(exist_ok=True)

    info(f"Cloning {repo_url} (shallow) ...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err("git clone failed:")
        print(result.stderr)
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)
    ok("Repository cloned.")

    # -- 1. Startup file ------------------------------------------------------
    startup_dir   = clone_dir / "Source" / "Templates" / "gcc"
    startup_files = sorted(startup_dir.glob("startup_*.s"))
    if not startup_files:
        err("No startup files found in the cloned repo.")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)

    selected_startup = ask_numbered_files(
        "Select the startup file for your exact STM32 device:",
        startup_files,
        teach_lines=[
            "startup_stm32*.s -- the FIRST code executed on your MCU at power-on.",
            "",
            "It does five things before main() ever runs:",
            "  1. Places the vector table at the start of FLASH",
            "  2. Sets the initial stack pointer",
            "  3. Copies .data from FLASH into RAM (_sidata → RAM)",
            "  4. Zeroes the .bss region in RAM",
            "  5. Calls SystemInit(), then jumps to main()",
            "",
            "Match the file to your exact part number -- e.g. for an STM32F030C6",
            "pick startup_stm32f030x6.s  (x6 covers all 32-pin F030 variants).",
            "The part number is printed on the chip itself.",
        ],
        min_select=1, max_select=1
    )[0]

    mcu_macro = macro_from_startup_file(selected_startup.name)
    shutil.copy(selected_startup, st_dir / selected_startup.name)
    ok(f"Startup file copied.  Derived compiler macro: {col(C.BOLD, mcu_macro)}")

    # -- 2. System source + companion header ----------------------------------
    # system_stm32*.c and system_stm32*.h always travel together.
    # We auto-copy the .h so it never appears again in the header-selection step.
    system_files = sorted((clone_dir / "Source" / "Templates").glob("system_*.c"))
    if system_files:
        if len(system_files) == 1:
            selected_system = system_files[0]
            ok(f"System source (only one available, auto-selected): {selected_system.name}")
        else:
            selected_system = ask_numbered_files(
                "Select the system initialisation source file:",
                system_files,
                teach_lines=[
                    "system_stm32*.c implements two things:",
                    "",
                    "  SystemInit()       -- called by the startup file before main().",
                    "                        Resets the clock registers to a safe state",
                    "                        using the internal HSI oscillator.",
                    "",
                    "  SystemCoreClock    -- a global uint32_t that holds the current",
                    "                        CPU frequency.  Peripheral drivers and",
                    "                        delay functions read this at runtime.",
                    "",
                    "You can later modify SystemInit() to switch to a faster PLL clock.",
                ],
                min_select=1, max_select=1
            )[0]

        shutil.copy(selected_system, st_dir / selected_system.name)
        ok(f"System source copied:  {selected_system.name}")

        # Auto-copy the companion .h (avoids showing it again below)
        companion_h = clone_dir / "Include" / (selected_system.stem + ".h")
        if companion_h.exists():
            shutil.copy(companion_h, st_dir / companion_h.name)
            ok(f"System header auto-copied: {companion_h.name}")
    else:
        warn("No system_*.c found -- add SystemInit() manually if needed.")

    # -- 3. Register-map headers (system_*.h excluded) ------------------------
    all_headers  = sorted((clone_dir / "Include").glob("*.h"))
    header_files = [h for h in all_headers if not h.name.startswith("system_")]

    if not header_files:
        err("No header files found in Include/.")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)

    umbrella = f"stm32{stm32_core.lower()}xx.h"
    device_h = f"{mcu_macro.lower()}.h"

    selected_headers = ask_numbered_files(
        "Select register-map headers to copy  (system_*.h already handled):",
        header_files,
        teach_lines=[
            "Two headers are essential here (system_*.h was already copied above):",
            "",
            f"  {device_h}",
            "    The register map for your exact chip.  Defines every peripheral",
            "    base address, every IRQ number, and every bit-field mask such as",
            "    GPIO_MODER_MODER9, RCC_AHBENR_GPIOCEN, GPIO_ODR_9 ...",
            "",
            f"  {umbrella}",
            "    The FAMILY umbrella header.  It reads the -D{mcu_macro}",
            "    compiler flag and pulls in the correct device header automatically.",
            "    Your source files include this one -- not the device header directly.",
            "",
            "  stm32_assert.h  (if listed) -- optional, useful for driver assertions.",
            "",
            "Tip: select all files listed -- they are small and cost nothing extra.",
        ],
        min_select=1, max_select=len(header_files)
    )
    for h in selected_headers:
        shutil.copy(h, st_dir / h.name)
        ok(f"Header copied:  {h.name}")

    shutil.rmtree(clone_dir, ignore_errors=True)
    ok("Temporary ST repo removed.")
    return mcu_macro

# -----------------------------------------------------------------------------
#  ARM CMSIS-Core files
# -----------------------------------------------------------------------------
def setup_arm_core_files(base_path: Path):
    section("CLONING ARM CMSIS-CORE FILES")
    teach([
        "ARM publishes CMSIS_5 on GitHub (ARM-software/CMSIS_5).",
        "We need the architecture-level headers from CMSIS/Core/Include/:",
        "",
        "  core_cm0.h / core_cm4.h / core_cm7.h  (match your Cortex-M revision)",
        "    -- CPU register structures: SysTick, NVIC, SCB, MPU ...",
        "    -- Intrinsic functions: __WFI(), __enable_irq(), __NOP() ...",
        "",
        "  cmsis_gcc.h      -- GCC-specific compiler intrinsics and attributes",
        "  cmsis_compiler.h -- compiler-portability layer",
        "  cmsis_version.h  -- CMSIS version constants",
        "",
        "These headers are ARCHITECTURE-level, not vendor-specific.",
        "The same core_cm4.h works for every STM32F4, every NXP LPC43xx, etc.",
    ])

    repo_url  = "https://github.com/ARM-software/CMSIS_5.git"
    clone_dir = base_path / "temp_cmsis5"
    arm_dir   = base_path / "lib" / "ARM"
    arm_dir.mkdir(exist_ok=True)

    info("Cloning ARM CMSIS_5 @ tag 5.9.0 (shallow) ...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", "5.9.0", repo_url, str(clone_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err("git clone failed:")
        print(result.stderr)
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)
    ok("ARM CMSIS_5 cloned.")

    include_dir  = clone_dir / "CMSIS" / "Core" / "Include"
    header_files = sorted(include_dir.glob("*.h"))
    if not header_files:
        err("Could not find CMSIS/Core/Include/*.h")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)

    mcpu     = CORE_TO_MCPU.get(stm32_core, "cortex-m0")
    core_num = mcpu.replace("cortex-m", "").replace("plus", "").replace("+", "")
    tip(f"For {stm32_core} ({mcpu}) you typically need: "
        f"{col(C.BOLD, 'core_cm' + core_num + '.h')}, "
        f"cmsis_gcc.h, cmsis_compiler.h, cmsis_version.h")

    selected = ask_numbered_files(
        "Select ARM CMSIS-Core headers to copy:",
        header_files,
        teach_lines=[
            "Pick the core header matching your CPU revision plus the three",
            "support headers that every GCC-based build needs:",
            "",
            f"  core_cm{core_num}.h    -- register structs for Cortex-M{core_num}",
            "  cmsis_gcc.h       -- GCC intrinsics (__attribute__, __asm, ...)",
            "  cmsis_compiler.h  -- compiler-neutral portability macros",
            "  cmsis_version.h   -- version constants used by device headers",
            "",
            "You can safely select all files -- the compiler only compiles what",
            "is actually included, so extras do not increase binary size.",
        ],
        min_select=1, max_select=len(header_files)
    )
    for h in selected:
        shutil.copy(h, arm_dir / h.name)
        ok(f"ARM header copied:  {h.name}")

    shutil.rmtree(clone_dir, ignore_errors=True)
    ok("Temporary ARM repo removed.")

# -----------------------------------------------------------------------------
#  AVR: no cloning needed
# -----------------------------------------------------------------------------
def setup_avr_info():
    section("AVR HEADERS")
    teach([
        "Unlike STM32, AVR projects do not need a separately cloned header pack.",
        "The avr-libc package (installed alongside avr-gcc) provides everything:",
        "",
        "  <avr/io.h>        -- register definitions for your -mmcu target",
        "                       (DDRx, PORTx, PINx, UCSRx, SPIx ...)",
        "  <util/delay.h>    -- accurate _delay_ms() / _delay_us() via F_CPU",
        "  <avr/interrupt.h> -- ISR() macro for writing interrupt handlers",
        "  <avr/pgmspace.h>  -- store constants in FLASH with PROGMEM",
        "",
        "The compiler finds these automatically when you pass -mmcu=<device>.",
        "No manual header management required.",
    ])
    ok("AVR headers supplied by avr-libc -- no cloning needed.")

# -----------------------------------------------------------------------------
#  Git
# -----------------------------------------------------------------------------
def init_git(base_path: Path):
    section("GIT INITIALISATION")
    result = subprocess.run(
        ["git", "init"], cwd=base_path, capture_output=True, text=True
    )
    if result.returncode == 0:
        ok(f"Git repository initialised in {base_path}")
    else:
        warn(f"git init failed: {result.stderr.strip()}")

# -----------------------------------------------------------------------------
#  Final summary
# -----------------------------------------------------------------------------
def print_summary(base_path: Path, mcu: str, build_system: str, use_nazengg: bool):
    section("PROJECT READY")
    print(f"""
  {col(C.BOLD + C.BWHITE, 'Location:')}  {base_path}
  {col(C.BOLD + C.BWHITE, 'MCU:     ')}  {mcu.upper()}
  {col(C.BOLD + C.BWHITE, 'Build:   ')}  {build_system}
  {col(C.BOLD + C.BWHITE, 'nazengg:')}  {'yes' if use_nazengg else 'no'}
""")
    print(f"  {col(C.BCYAN + C.BOLD, 'Quick-start commands:')}\n")
    print(f"    {col(C.BGREEN, 'cd ' + base_path.name)}")
    if build_system == "make":
        print(f"    {col(C.BGREEN, 'make')}                  {col(C.DIM, '# build everything')}")
        print(f"    {col(C.BGREEN, 'make size')}             {col(C.DIM, '# check flash / RAM usage')}")
        print(f"    {col(C.BGREEN, 'make disasm')}           {col(C.DIM, '# view annotated assembly')}")
        print(f"    {col(C.BGREEN, 'make flash')}            {col(C.DIM, '# program the board')}")
        print(f"    {col(C.BGREEN, 'make test')}             {col(C.DIM, '# run host unit tests')}")
        print(f"    {col(C.BGREEN, 'make help')}             {col(C.DIM, '# list all targets')}")
    else:
        print(f"    {col(C.BGREEN, 'mkdir build && cd build')}")
        print(f"    {col(C.BGREEN, f'cmake .. -DCMAKE_TOOLCHAIN_FILE=../toolchain/{mcu}_toolchain.cmake')}")
        print(f"    {col(C.BGREEN, 'cmake --build .')}")
        print(f"    {col(C.BGREEN, 'ctest')}")

    if mcu == "stm32":
        print(f"\n  {col(C.BYELLOW + C.BOLD, 'Before you build:')}")
        print(f"  {col(C.DIM, '1. Verify the FLASH/RAM sizes in lib/ST/stm32.ld match your chip.')}")
        print(f"  {col(C.DIM, '2. Check lib/nazengg/nazengg.c -- PC9 may not be your board LED.')}")
        print(f"  {col(C.DIM, '3. Run  make size  to see your first flash and RAM footprint.')}")
    print()

# -----------------------------------------------------------------------------
#  Main wizard
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Nazeer Dynamics Embedded Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--about",    action="store_true", help="Show educational overview")
    parser.add_argument("--check",    action="store_true", help="Audit all required tools")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    args = parser.parse_args()

    if args.no_color:
        for attr in list(vars(C).keys()):
            if not attr.startswith("_"):
                setattr(C, attr, "")

    print_banner()

    if args.about:
        print_about()
        return

    if args.check:
        check_all_tools(quiet=False)
        return

    # -- Pre-flight tool check ------------------------------------------------
    section("PRE-FLIGHT TOOLCHAIN CHECK")
    info("Checking commonly needed tools before we start ...")
    check_all_tools(quiet=True)

    # -- Project basics -------------------------------------------------------
    section("PROJECT SETUP")
    project_name = ask_text("Project name (will create a directory)", "my_mcu_project")
    if not project_name:
        err("Project name cannot be empty.")
        sys.exit(1)

    mcu = ask(
        "Target microcontroller architecture:",
        ["stm32", "avr"],
        [
            "ARM Cortex-M  (STM32Fxx/Gxx/Hxx/Lxx) -- arm-none-eabi-gcc + CMSIS",
            "Atmel AVR     (ATmega328P / Arduino)  -- avr-gcc + avr-libc",
        ]
    )

    build_system = ask(
        "Build system:",
        ["make", "cmake"],
        [
            "GNU Make  -- simpler, widely used in embedded, includes ELF analysis targets",
            "CMake     -- cross-platform, IDE-friendly, generates Makefiles / Ninja",
        ]
    )

    use_nazengg = ask(
        "Include the 'nazengg' thin HAL library?",
        ["yes", "no"],
        [
            "Yes -- adds lib/nazengg/ with GPIO init & LED toggle (good starting point)",
            "No  -- bare src/main.c only; write every register access yourself",
        ]
    ) == "yes"

    # -- Validate tools -------------------------------------------------------
    require_tools_for_mcu(mcu, build_system)

    # -- AVR extra config -----------------------------------------------------
    avr_mmcu = "atmega328p"
    avr_fcpu = "16000000"
    if mcu == "avr":
        section("AVR DEVICE CONFIGURATION")
        teach([
            "-mmcu=<device> tells avr-gcc the exact chip so it can:",
            "  * Link the correct I/O definitions and startup code",
            "  * Apply the correct flash and RAM memory model",
            "  * Generate correct EEPROM and fuse-bit access",
            "",
            "F_CPU must match your crystal or oscillator frequency.",
            "Arduino UNO = 16 MHz.  ATtiny85 internal RC = 8 MHz (or 1 MHz).",
            "Getting F_CPU wrong makes _delay_ms() run at the wrong speed.",
        ])
        avr_mmcu = ask_text("AVR device (-mmcu)", "atmega328p")
        avr_fcpu = ask_text("CPU frequency in Hz (F_CPU)", "16000000")

    # -- STM32 core -----------------------------------------------------------
    mcpu = ""
    if mcu == "stm32":
        mcpu = ask_stm32_core()

    # -- Create project tree --------------------------------------------------
    base_path = Path(project_name).resolve()
    base_path.mkdir(exist_ok=True)

    section(f"BUILDING PROJECT: {project_name}")
    create_structure(base_path)
    write_common_files(base_path, project_name, mcu)

    if mcu == "stm32":
        write_main_c_stm32(base_path)
    else:
        write_main_c_avr(base_path)

    write_unit_test_stub(base_path)

    # -- MCU-specific steps ---------------------------------------------------
    if mcu == "stm32":
        setup_stm32_device_files(base_path)
        setup_arm_core_files(base_path)

        if use_nazengg:
            write_nazengg_lib_stm32(base_path, mcpu, mcu_macro)

        if build_system == "make":
            write_makefile_stm32(base_path, mcpu, mcu_macro, use_nazengg)
        else:
            write_cmake(base_path, mcu, mcpu)

        write_linker_script(base_path)

    else:
        setup_avr_info()

        if use_nazengg:
            write_nazengg_lib_avr(base_path, avr_mmcu)

        if build_system == "make":
            write_makefile_avr(base_path, avr_mmcu, avr_fcpu, use_nazengg)
        else:
            write_cmake(base_path, mcu, avr_mmcu)

    # -- Git ------------------------------------------------------------------
    init_git(base_path)

    # -- Done -----------------------------------------------------------------
    print_summary(base_path, mcu, build_system, use_nazengg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {col(C.BYELLOW, '[!!] Interrupted by user.  Partial project may exist.')}\n")
        sys.exit(0)