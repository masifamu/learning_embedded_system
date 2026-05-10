#!/usr/bin/env python3
"""
Nazeer Dynamics Embedded Project Generator
==========================================
Educational CLI tool for generating bare-metal STM32 / AVR projects.
Teaches every layer: toolchain, linker scripts, CMSIS, Makefiles, and more.

Usage:
  python3 nazeer_gen.py            — interactive project wizard
  python3 nazeer_gen.py --help     — show this help
  python3 nazeer_gen.py --about    — what this tool does & why
  python3 nazeer_gen.py --check    — check all required tools
"""

import os
import subprocess
import shutil
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  ANSI colour / style helpers
# ─────────────────────────────────────────────────────────────────────────────
class C:
    RESET    = "\033[0m";  BOLD     = "\033[1m";  DIM    = "\033[2m"
    RED      = "\033[31m"; GREEN    = "\033[32m";  YELLOW = "\033[33m"
    BLUE     = "\033[34m"; MAGENTA  = "\033[35m";  CYAN   = "\033[36m"
    BRED     = "\033[91m"; BGREEN   = "\033[92m";  BYELLOW= "\033[93m"
    BBLUE    = "\033[94m"; BMAGENTA = "\033[95m";  BCYAN  = "\033[96m"
    BWHITE   = "\033[97m"

def col(color, text):   return f"{color}{text}{C.RESET}"
def ok(msg):            print(f"  {col(C.BGREEN,  '✅')} {msg}")
def err(msg):           print(f"  {col(C.BRED,    '❌')} {col(C.BRED, msg)}")
def warn(msg):          print(f"  {col(C.BYELLOW, '⚠️ ')} {col(C.BYELLOW, msg)}")
def info(msg):          print(f"  {col(C.BCYAN,   'ℹ')}  {msg}")
def tip(msg):           print(f"  {col(C.BMAGENTA,'💡')} {col(C.BMAGENTA, msg)}")
def step(msg):          print(f"\n{col(C.BOLD+C.BBLUE,'━━▶')} {col(C.BOLD+C.BWHITE, msg)}")
def section(title):
    width = 64
    bar   = col(C.CYAN, "─" * width)
    print(f"\n{bar}")
    print(f"{col(C.BOLD+C.BCYAN,'  ' + title)}")
    print(bar)

def teach(lines):
    """Print a coloured educational callout box."""
    width = 62
    print(f"\n  {col(C.YELLOW,'┌' + '─'*width + '┐')}")
    print(f"  {col(C.YELLOW,'│')} {col(C.BYELLOW+C.BOLD,' 📚  WHY THIS MATTERS' + ' '*(width-21))}{col(C.YELLOW,'│')}")
    print(f"  {col(C.YELLOW,'├' + '─'*width + '┤')}")
    for line in lines:
        chunks = [line[i:i+width-2] for i in range(0, max(len(line),1), width-2)]
        for chunk in chunks:
            pad = width - 2 - len(chunk)
            print(f"  {col(C.YELLOW,'│')}  {col(C.DIM, chunk)}{' '*pad}  {col(C.YELLOW,'│')}")
    print(f"  {col(C.YELLOW,'└' + '─'*width + '┘')}\n")

# ─────────────────────────────────────────────────────────────────────────────
#  Global state (kept as module-level to match original design)
# ─────────────────────────────────────────────────────────────────────────────
stm32_core = ""
mcu_macro  = ""

# ─────────────────────────────────────────────────────────────────────────────
#  Banner
# ─────────────────────────────────────────────────────────────────────────────
def print_banner():
    ts      = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    version = "v2.0.0"
    print(col(C.CYAN, """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ███╗   ██╗ █████╗ ███████╗███████╗███████╗██████╗      ║
║      ████╗  ██║██╔══██╗╚══███╔╝██╔════╝██╔════╝██╔══██╗     ║
║      ██╔██╗ ██║███████║  ███╔╝ █████╗  █████╗  ██████╔╝     ║
║      ██║╚██╗██║██╔══██║ ███╔╝  ██╔══╝  ██╔══╝  ██╔══██╗     ║
║      ██║ ╚████║██║  ██║███████╗███████╗███████╗██║  ██║     ║
║      ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝     ║
║                                                              ║
║          Embedded Systems Project Generator                  ║
║          STM32 · AVR · CMSIS · Bare-Metal                   ║"""))
    print(col(C.CYAN, f"║          {ts}   {version}              ║"))
    print(col(C.CYAN, """╚══════════════════════════════════════════════════════════════╝"""))
    print(f"\n  {col(C.DIM,'Type')} {col(C.BCYAN,'--help')} {col(C.DIM,'for options,')} "
          f"{col(C.BCYAN,'--about')} {col(C.DIM,'to learn what this tool teaches,')} "
          f"{col(C.BCYAN,'--check')} {col(C.DIM,'to audit your toolchain.')}\n")

# ─────────────────────────────────────────────────────────────────────────────
#  About / Educational overview
# ─────────────────────────────────────────────────────────────────────────────
ABOUT_TEXT = [
    ("What does this tool build?",
     "A complete bare-metal embedded project — no Arduino, no HAL magic.\n"
     "You get: Makefile/CMake build system, CMSIS headers fetched from\n"
     "official ST & ARM repos, a real linker script you configure, startup\n"
     "assembly, and a tiny HAL-free LED-blink skeleton to build on."),

    ("Why bare-metal / CMSIS-only?",
     "ST's HAL is great for products, but it hides *how* the hardware works.\n"
     "Bare-metal forces you to understand: memory maps, vector tables,\n"
     "clock trees, peripheral registers, and the GNU linker — skills every\n"
     "serious embedded engineer needs."),

    ("What is CMSIS?",
     "Cortex Microcontroller Software Interface Standard — ARM's portable\n"
     "C headers that give you named register structs and IRQ numbers for\n"
     "every Cortex-M device, without depending on vendor HAL layers."),

    ("What is a linker script?",
     "A .ld file that tells the linker where to place each section (.text,\n"
     ".data, .bss) in your target's memory map.  Without it the linker\n"
     "cannot produce a runnable binary for your specific MCU."),

    ("What is the startup file?",
     "Assembly (.s) or C code that runs *before* main().  It sets the\n"
     "initial stack pointer, copies .data from FLASH→RAM, zeroes .bss,\n"
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
    section("📖  ABOUT  —  What This Tool Teaches")
    for title, body in ABOUT_TEXT:
        print(f"\n  {col(C.BOLD+C.BBLUE,'●')} {col(C.BOLD+C.BWHITE, title)}")
        for line in body.split("\n"):
            print(f"      {col(C.DIM, line)}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
#  Tool definitions & checker
# ─────────────────────────────────────────────────────────────────────────────
TOOLS = {
    # name: (description, required_for, apt_pkg, brew_pkg, install_note)
    "git": (
        "Version control & used to clone CMSIS repos from GitHub",
        "all targets",
        "git",
        "git",
        None,
    ),
    "make": (
        "GNU Make — drives the build via Makefile",
        "Make-based projects",
        "make",
        "make",
        None,
    ),
    "cmake": (
        "CMake — alternative meta-build system",
        "CMake-based projects",
        "cmake",
        "cmake",
        None,
    ),
    "arm-none-eabi-gcc": (
        "ARM bare-metal cross-compiler — turns your C into Cortex-M machine code",
        "STM32 projects",
        "gcc-arm-none-eabi",
        "arm-none-eabi-gcc",
        "On Ubuntu 22+: sudo apt install gcc-arm-none-eabi binutils-arm-none-eabi",
    ),
    "arm-none-eabi-gdb": (
        "ARM GDB — source-level debugger for Cortex-M targets",
        "STM32 debugging",
        "gdb-arm-none-eabi",
        "arm-none-eabi-gdb",
        None,
    ),
    "avr-gcc": (
        "AVR cross-compiler — turns your C into ATmega machine code",
        "AVR projects",
        "gcc-avr",
        "avr-gcc",
        "Also install: avr-libc (sudo apt install avr-libc)",
    ),
    "avrdude": (
        "AVR flash programmer — uploads .hex to your AVR board",
        "AVR flashing",
        "avrdude",
        "avrdude",
        None,
    ),
    "st-flash": (
        "ST-Link flash tool — programs STM32 via USB SWD/JTAG",
        "STM32 flashing",
        "stlink-tools",
        "stlink",
        "https://github.com/stlink-org/stlink",
    ),
    "openocd": (
        "Open On-Chip Debugger — GDB server + flash programmer",
        "STM32/AVR debugging",
        "openocd",
        "open-ocd",
        None,
    ),
}

def check_one_tool(name):
    """Returns True if found on PATH."""
    return shutil.which(name) is not None

def print_tool_status(name, found, desc):
    status = col(C.BGREEN, "✅  FOUND  ") if found else col(C.BRED, "❌  MISSING")
    print(f"  {status}  {col(C.BOLD, name.ljust(26))} {col(C.DIM, desc)}")

def check_all_tools(quiet=False):
    """Audit every tool. Returns dict {name: bool}."""
    section("🔧  TOOLCHAIN AUDIT")
    results = {}
    for name, (desc, req, apt, brew, note) in TOOLS.items():
        found = check_one_tool(name)
        results[name] = found
        if not quiet or not found:
            print_tool_status(name, found, f"[{req}]  {desc}")
    missing = [n for n, ok in results.items() if not ok]
    if not missing:
        print(f"\n  {col(C.BGREEN+C.BOLD, '🎉  All tools found!  Your system is ready.')}\n")
    else:
        print(f"\n  {col(C.BYELLOW+C.BOLD, f'⚠️   {len(missing)} tool(s) missing.')}")
        _offer_install(missing)
    return results

def _offer_install(missing):
    """Offer guided apt install for missing tools."""
    apt_pkgs = []
    extras   = []
    for name in missing:
        _, _, apt, _, note = TOOLS[name]
        if apt:
            apt_pkgs.append(apt)
        if note:
            extras.append((name, note))

    if apt_pkgs:
        cmd = "sudo apt install -y " + " ".join(apt_pkgs)
        print(f"\n  {col(C.BCYAN, 'To install all missing tools on Ubuntu/Debian, run:')}")
        print(f"\n    {col(C.BOLD+C.BGREEN, cmd)}\n")
        choice = input(col(C.BYELLOW, "  → Run this command now? [y/N]: ")).strip().lower()
        if choice == "y":
            step("Running apt install...")
            ret = subprocess.run(cmd, shell=True)
            if ret.returncode == 0:
                ok("Installation complete — re-run the tool to verify.")
            else:
                err("apt install failed. Check your internet connection or run manually.")
        else:
            tip("Run the command above whenever you're ready, then restart the generator.")

    for name, note in extras:
        tip(f"{name}: {note}")

def require_tools_for_mcu(mcu, build_system):
    """Check only the tools needed for the chosen MCU — exit if critical ones missing."""
    needed = ["git", build_system]
    if mcu == "stm32":
        needed += ["arm-none-eabi-gcc"]
    elif mcu == "avr":
        needed += ["avr-gcc"]

    missing = [t for t in needed if not check_one_tool(t)]
    if missing:
        section("❌  CRITICAL TOOLS MISSING")
        for t in missing:
            desc = TOOLS.get(t, ("unknown tool", "", "", "", None))[0]
            print_tool_status(t, False, desc)
        _offer_install(missing)
        print()
        err("Cannot continue until required tools are installed.")
        sys.exit(1)

    # Warn-only for optional tools
    optional = []
    if mcu == "stm32":
        optional = ["st-flash", "openocd", "arm-none-eabi-gdb"]
    elif mcu == "avr":
        optional = ["avrdude", "openocd"]
    for t in optional:
        if not check_one_tool(t):
            warn(f"Optional tool '{t}' not found — some Makefile targets will not work.")

# ─────────────────────────────────────────────────────────────────────────────
#  Interactive helpers
# ─────────────────────────────────────────────────────────────────────────────
def ask(prompt, options, descriptions=None):
    """Numbered menu. descriptions is optional list of explanation strings."""
    print(f"\n  {col(C.BOLD+C.BWHITE, prompt)}")
    for i, opt in enumerate(options, 1):
        desc = f"  {col(C.DIM, '—  ' + descriptions[i-1])}" if descriptions else ""
        print(f"    {col(C.BCYAN, str(i) + '.')}  {col(C.BOLD, opt)}{desc}")
    while True:
        try:
            raw = input(col(C.BYELLOW, "\n  Choice [1-{}]: ".format(len(options)))).strip()
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                chosen = options[idx]
                ok(f"Selected: {col(C.BOLD, chosen)}")
                return chosen
        except (ValueError, KeyboardInterrupt):
            pass
        warn("Invalid choice. Please enter a number shown above.")

def ask_text(prompt, default=None):
    """Prompt for free-form text with an optional default."""
    hint = f" [{col(C.DIM, default)}]" if default else ""
    raw  = input(f"\n  {col(C.BOLD+C.BWHITE, prompt)}{hint}: ").strip()
    value = raw if raw else default
    if value:
        ok(f"Using: {col(C.BOLD, str(value))}")
    return value

def ask_numbered_files(prompt, files, teach_lines=None, min_select=1, max_select=None):
    """
    Show a numbered list of files and let the user pick one or more.
    teach_lines: educational note shown before the list.
    Returns list of selected Path objects.
    """
    if teach_lines:
        teach(teach_lines)
    max_select = max_select or len(files)
    print(f"\n  {col(C.BOLD+C.BWHITE, prompt)}")
    for i, f in enumerate(files, 1):
        print(f"    {col(C.BCYAN, str(i) + '.')}  {f.name}")

    range_str = f"1-{max_select}" if max_select > 1 else "1"
    tip(f"Enter comma-separated numbers (e.g.  1  or  1,3)  — choose {min_select}–{max_select}")
    while True:
        try:
            raw     = input(col(C.BYELLOW, f"\n  Selection: ")).strip()
            indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
            if (min_select <= len(indices) <= max_select and
                    all(0 <= i < len(files) for i in indices)):
                selected = [files[i] for i in indices]
                for s in selected:
                    ok(f"Selected: {s.name}")
                return selected
        except (ValueError, KeyboardInterrupt):
            pass
        warn(f"Please pick between {min_select} and {max_select} valid numbers.")

# ─────────────────────────────────────────────────────────────────────────────
#  Project structure & shared files
# ─────────────────────────────────────────────────────────────────────────────
def create_structure(base_path):
    dirs = ["src", "include", "tests", "build",
            "toolchain", "lib/nazengg", "lib/ARM", "lib/ST", "docs"]
    for d in dirs:
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
src/          — your application C files
include/      — shared headers
lib/nazengg/  — thin portable HAL built by this project
lib/ST/       — ST CMSIS-Device files (startup, system, register defs)
lib/ARM/      — ARM CMSIS-Core headers (core_cm*.h etc.)
tests/        — host-side unit tests compiled with native gcc
build/        — generated artefacts (.elf, .bin, .hex, map …)
toolchain/    — CMake toolchain files (if CMake build chosen)
docs/         — documentation
```

## Learning resources

- [CMSIS docs](https://arm-software.github.io/CMSIS_5/Core/html/index.html)
- [GNU linker manual](https://sourceware.org/binutils/docs/ld/)
- [OpenOCD docs](https://openocd.org/doc/html/index.html)
"""
    (base_path / "README.md").write_text(readme)
    (base_path / ".gitignore").write_text(
        "build/\nbin/\n*.o\n*.elf\n*.bin\n*.hex\n*.map\n*.a\n"
    )
    ok("README.md and .gitignore written.")

# ─────────────────────────────────────────────────────────────────────────────
#  STM32 application skeleton
# ─────────────────────────────────────────────────────────────────────────────
def write_main_c_stm32(base_path):
    code = '''\
#include "nazengg.h"

/* ─── Simple busy-wait delay (not accurate, just for blink demo) ─────────── */
static void delay(volatile unsigned int count) {
    while (count--) {
        __asm__ volatile ("nop");   /* tell compiler not to optimise away */
    }
}

int main(void) {
    nazengg_init();         /* configure the LED GPIO */

    while (1) {
        nazengg_toggle_led();
        delay(1000000UL);   /* ~0.5 s at 8 MHz HSI, tune to taste */
    }

    /* Bare-metal main() must never return — the MCU has nowhere to go. */
    return 0;
}
'''
    (base_path / "src" / "main.c").write_text(code)
    ok("src/main.c written  (STM32 LED blink skeleton).")

# ─────────────────────────────────────────────────────────────────────────────
#  AVR application skeleton
# ─────────────────────────────────────────────────────────────────────────────
def write_main_c_avr(base_path):
    code = '''\
#include <avr/io.h>
#include <util/delay.h>
#include "nazengg.h"

int main(void) {
    nazengg_init();           /* set PB5 (Arduino pin 13) as output */

    while (1) {
        nazengg_toggle_led();
        _delay_ms(500);       /* 500 ms hardware delay — accurate, no busy-wait */
    }

    return 0;   /* never reached on AVR either */
}
'''
    (base_path / "src" / "main.c").write_text(code)
    ok("src/main.c written  (AVR LED blink skeleton).")

# ─────────────────────────────────────────────────────────────────────────────
#  Unit-test stub (runs on host with native gcc)
# ─────────────────────────────────────────────────────────────────────────────
def write_unit_test_stub(base_path):
    content = '''\
/*
 * Host-side unit tests — compiled with native gcc, NOT the cross-compiler.
 * "make test" builds and runs this file on your development machine.
 *
 * WHY: Cross-compiled tests need an emulator or real hardware.  Pure-logic
 * functions (CRC, state-machines, protocol parsers) can be tested here
 * without any target hardware.
 */
#include <assert.h>
#include <stdio.h>

/* Example: test a pure-logic helper */
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
'''
    (base_path / "tests" / "test_main.c").write_text(content)
    ok("tests/test_main.c written  (host-side unit-test stub).")

# ─────────────────────────────────────────────────────────────────────────────
#  nazengg library — STM32 version
# ─────────────────────────────────────────────────────────────────────────────
def write_nazengg_lib_stm32(base_path, mcpu, macro):
    lib = base_path / "lib" / "nazengg"

    (lib / "nazengg.h").write_text('''\
#pragma once
/*
 * nazengg — minimal portable LED driver for STM32.
 * Replace the body of nazengg.c to target a different GPIO pin.
 */
void nazengg_init(void);
void nazengg_toggle_led(void);
''')

    # Use the device-specific header pulled in by the per-device header
    (lib / "nazengg.c").write_text(f'''\
#include "nazengg.h"
/*
 * The device header (e.g. stm32f030x6.h) includes cmsis_gcc.h → core_cm0.h
 * giving us the CMSIS register structs for RCC, GPIO, etc.
 *
 * PC9 is the green LED on the STM32F0-Discovery board.
 * Change GPIOC/RCC_AHBENR_GPIOCEN/GPIO_ODR_9 for your own board.
 */
#include "{macro}.h"    /* e.g. stm32f030x6.h */

void nazengg_init(void) {{
    /* 1. Gate the GPIO clock — without this the peripheral is dead */
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

    /* 2. Set PC9 as general-purpose output (MODER = 0b01) */
    GPIOC->MODER &= ~GPIO_MODER_MODER9;    /* clear both bits first */
    GPIOC->MODER |=  GPIO_MODER_MODER9_0;  /* bit0=1 → output mode  */

    /* 3. Output type: push-pull (OTYPER bit = 0, which is the reset default) */
    GPIOC->OTYPER &= ~GPIO_OTYPER_OT_9;

    /* 4. No pull-up / pull-down (PUPDR = 00, reset default) */
    GPIOC->PUPDR  &= ~GPIO_PUPDR_PUPDR9;
}}

void nazengg_toggle_led(void) {{
    /* XOR the output bit — atomic read-modify-write on ODR */
    GPIOC->ODR ^= GPIO_ODR_9;
}}
''')

    (lib / "Makefile").write_text(f'''\
# nazengg sub-library Makefile
# Compiled separately so the top-level build only re-links when this changes.

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
    ok("lib/nazengg/  STM32 library sources written.")

# ─────────────────────────────────────────────────────────────────────────────
#  nazengg library — AVR version
# ─────────────────────────────────────────────────────────────────────────────
def write_nazengg_lib_avr(base_path, mmcu="atmega328p"):
    lib = base_path / "lib" / "nazengg"

    (lib / "nazengg.h").write_text('''\
#pragma once
/*
 * nazengg — minimal portable LED driver for AVR (ATmega328P / Arduino UNO).
 * PB5 = Arduino pin 13 = the built-in LED.
 */
void nazengg_init(void);
void nazengg_toggle_led(void);
''')

    (lib / "nazengg.c").write_text('''\
#include <avr/io.h>
#include "nazengg.h"

/*
 * AVR register-level GPIO:
 *   DDRx  — Data Direction Register  (1=output, 0=input)
 *   PORTx — Output Data Register     (write output value)
 *   PINx  — Input register           (read; writing 1 toggles on many AVRs)
 *
 * PB5 is bit 5 of PORTB (Arduino pin 13 / built-in LED).
 */
void nazengg_init(void) {
    DDRB  |= (1 << DDB5);    /* set PB5 as output */
    PORTB &= ~(1 << PORTB5); /* start LED off      */
}

void nazengg_toggle_led(void) {
    PINB = (1 << PINB5);     /* writing to PINB toggles the output (AVR hardware feature) */
}
''')

    (lib / "Makefile").write_text(f'''\
# nazengg sub-library Makefile — AVR

SRC     = $(wildcard *.c)
OBJ     = $(SRC:.c=.o)
INCLUDE = -I.

CFLAGS  = -mmcu={mmcu} -Wall -Wextra -Os $(INCLUDE)

all: libnazengg.a

%.o: %.c
\tavr-gcc $(CFLAGS) -c $< -o $@

libnazengg.a: $(OBJ)
\tavr-ar rcs $@ $^

clean:
\trm -f *.o libnazengg.a
''')
    ok("lib/nazengg/  AVR library sources written.")

# ─────────────────────────────────────────────────────────────────────────────
#  STM32 Makefile
# ─────────────────────────────────────────────────────────────────────────────
CORE_TO_MCPU = {
    "F0": "cortex-m0",   "F1": "cortex-m3",  "F2": "cortex-m3",
    "F3": "cortex-m4",   "F4": "cortex-m4",  "F7": "cortex-m7",
    "G0": "cortex-m0plus","G4": "cortex-m4", "H7": "cortex-m7",
    "L0": "cortex-m0plus","L1": "cortex-m3", "L4": "cortex-m4",
    "L5": "cortex-m33",  "U5": "cortex-m33",
}

def write_makefile_stm32(base_path, mcpu, macro, use_nazengg):
    nazengg_link = "$(LIBAMB)" if use_nazengg else ""
    nazengg_dep  = f"\n$(LIBAMB):\n\t$(MAKE) -C lib/nazengg\n" if use_nazengg else ""
    content = f'''\
# ─────────────────────────────────────────────────────────────
#  Nazeer Dynamics — STM32 Bare-Metal Makefile
#  Core:   {stm32_core}   CPU: {mcpu}   Macro: {macro}
# ─────────────────────────────────────────────────────────────

MCU       = stm32
CORE      = {stm32_core}

# ── Toolchain ────────────────────────────────────────────────
CC        = arm-none-eabi-gcc
OBJDUMP   = arm-none-eabi-objdump
OBJCOPY   = arm-none-eabi-objcopy
SIZE      = arm-none-eabi-size
NM        = arm-none-eabi-nm
READELF   = arm-none-eabi-readelf

# ── Compiler flags ───────────────────────────────────────────
#   -mcpu / -mthumb   : target the exact Cortex-M core
#   -ffunction-sections / -fdata-sections : enable dead-code stripping by linker
#   -Os               : optimise for size (important for small flash)
#   -g2               : full debug info (strip later for release)
#   -D{macro}         : selects the correct register definitions in the ST headers
CFLAGS  = -mcpu={mcpu} -mthumb \\
           -Wall -Wextra -Werror -Wundef -Wshadow -Wdouble-promotion \\
           -Wformat-truncation -fno-common -Wconversion \\
           -g2 -Os -ffunction-sections -fdata-sections \\
           -Iinclude -Ilib/nazengg -Ilib/ST -Ilib/ARM \\
           -D{macro}

# ── Linker flags ─────────────────────────────────────────────
#   -T                : use our custom linker script (memory layout)
#   -specs=nano.specs : tiny Newlib-nano C library (saves flash)
#   -specs=nosys.specs: stub syscalls (no OS underneath us)
#   --gc-sections     : drop unused functions/data (dead-code elimination)
#   --cref            : cross-reference table in map (who calls what)
#   --Map=            : human-readable linker map file
LDFLAGS = -Tlib/ST/stm32.ld \\
           -specs=nano.specs -specs=nosys.specs -lc -lgcc \\
           -Wl,--gc-sections,--cref,--Map=build/output.map

# ── Sources ──────────────────────────────────────────────────
SRC      = $(wildcard src/*.c)
SRC     += $(wildcard lib/ST/system_*.c)
# Startup assembly file is compiled like a C file via GCC
ASRC     = $(wildcard lib/ST/startup_*.s)

OBJ      = $(SRC:.c=.o) $(ASRC:.s=.o)
LIBAMB   = lib/nazengg/libnazengg.a
TARGET   = build/main.elf
BIN      = build/main.bin
HEX      = build/main.hex

# ── Targets ──────────────────────────────────────────────────
all: $(LIBAMB) $(TARGET)
{nazengg_dep}
$(TARGET): $(OBJ) {nazengg_link}
\tmkdir -p build
\t$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

# Assemble startup file (GCC can handle .s via -x assembler-with-cpp)
%.o: %.s
\t$(CC) $(CFLAGS) -x assembler-with-cpp -c $< -o $@

# ── Analysis targets (great for learning!) ───────────────────
# Shows section sizes: text=flash, data+bss=RAM
size: $(TARGET)
\t@echo ""
\t@echo "  text+data = total FLASH usage"
\t@echo "  data+bss  = total RAM  usage"
\t$(SIZE) $(TARGET)
\t@echo ""
\t@ls -lh $(TARGET)

# Human-readable assembly listing of your compiled binary
disasm: $(TARGET)
\t$(OBJDUMP) -h -d $(TARGET) > build/main.disasm.s
\t@echo "✅  Disassembly → build/main.disasm.s"

# All symbols sorted by address (find where functions live in flash)
symbols: $(TARGET)
\t$(NM) -n $(TARGET) > build/symbols.txt
\t@echo "✅  Symbols     → build/symbols.txt"

# Symbols sorted by size (quickly spot the memory hogs)
symbolsize: $(TARGET)
\t$(NM) --print-size --size-sort --size-sort $(TARGET) > build/symbolsize.txt
\t@echo "✅  By size      → build/symbolsize.txt"

# Undefined symbols — things the linker needs to resolve from libc/startup
symbols_undef: $(TARGET)
\t$(NM) -u $(TARGET) > build/symbols_undef.txt
\t@echo "✅  Undefined   → build/symbols_undef.txt"

# Full ELF section/header dump — learn the ELF binary format
readelf: $(TARGET)
\t$(READELF) -a $(TARGET) > build/elf_headers.txt
\t@echo "✅  ELF info    → build/elf_headers.txt"

# Cross-reference map — who calls whom
linkermap: $(TARGET)
\t@echo "✅  Linker map  → build/output.map  (already generated by -Map flag)"

# Convert ELF → raw binary (used by some flash tools)
bin: $(TARGET)
\t$(OBJCOPY) -O binary $(TARGET) $(BIN)
\t@echo "✅  Binary      → $(BIN)"

# Convert ELF → Intel HEX (used by other flash tools)
hex: $(TARGET)
\t$(OBJCOPY) -O ihex $(TARGET) $(HEX)
\t@echo "✅  HEX file    → $(HEX)"

# Strip debug info → smaller ELF for production
strip: $(TARGET)
\tarm-none-eabi-strip $(TARGET) -o build/main_stripped.elf
\t@echo "✅  Stripped ELF → build/main_stripped.elf"

# Flash via ST-Link SWD
flash: $(BIN)
\tst-flash write $(BIN) 0x08000000

# Run host-side unit tests with native gcc
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
\t@grep -E '^[a-zA-Z0-9_-]+:' Makefile | grep -v '\\.' | cut -d: -f1 | sort | uniq | \\
\t  awk '{{printf "    make %-16s\\n", $$1}}'
\t@echo ""

.PHONY: all clean flash test size disasm symbols symbolsize \\
        symbols_undef readelf linkermap bin hex strip help
'''
    (base_path / "Makefile").write_text(content)
    ok("Makefile written  (STM32, with ELF analysis targets).")

# ─────────────────────────────────────────────────────────────────────────────
#  AVR Makefile
# ─────────────────────────────────────────────────────────────────────────────
def write_makefile_avr(base_path, mmcu, f_cpu, use_nazengg):
    nazengg_link = "$(LIBAMB)" if use_nazengg else ""
    nazengg_dep  = "\n$(LIBAMB):\n\t$(MAKE) -C lib/nazengg\n" if use_nazengg else ""
    content = f'''\
# ─────────────────────────────────────────────────────────────
#  Nazeer Dynamics — AVR Bare-Metal Makefile
#  MCU: {mmcu}   F_CPU: {f_cpu} Hz
# ─────────────────────────────────────────────────────────────

MMCU      = {mmcu}
F_CPU     = {f_cpu}

CC        = avr-gcc
OBJCOPY   = avr-objcopy
OBJDUMP   = avr-objdump
SIZE      = avr-size
NM        = avr-nm

# ── Compiler flags ───────────────────────────────────────────
#   -mmcu          : selects the exact AVR core & memory map
#   -DF_CPU        : makes delay macros in <util/delay.h> accurate
#   -Os            : optimise for size
CFLAGS = -mmcu=$(MMCU) -DF_CPU=$(F_CPU)UL \\
          -Wall -Wextra -Os -g \\
          -Iinclude -Ilib/nazengg

SRC      = $(wildcard src/*.c)
OBJ      = $(SRC:.c=.o)
LIBAMB   = lib/nazengg/libnazengg.a
TARGET   = build/main.elf
HEX      = build/main.hex

all: $(LIBAMB) $(TARGET) $(HEX) size
{nazengg_dep}
$(TARGET): $(OBJ) {nazengg_link}
\tmkdir -p build
\t$(CC) $(CFLAGS) -o $@ $^ -L lib/nazengg -lnazengg

$(HEX): $(TARGET)
\t$(OBJCOPY) -O ihex -R .eeprom $(TARGET) $(HEX)
\t@echo "✅  HEX file → $(HEX)"

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

size: $(TARGET)
\t@echo ""
\t$(SIZE) --format=avr --mcu=$(MMCU) $(TARGET)
\t@echo ""

disasm: $(TARGET)
\t$(OBJDUMP) -h -d $(TARGET) > build/main.disasm.s
\t@echo "✅  Disassembly → build/main.disasm.s"

symbols: $(TARGET)
\t$(NM) -n $(TARGET) > build/symbols.txt
\t@echo "✅  Symbols     → build/symbols.txt"

# Flash via avrdude (Arduino UNO / programmer — adjust -c and -P as needed)
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
\t@grep -E '^[a-zA-Z0-9_-]+:' Makefile | grep -v '\\.' | cut -d: -f1 | sort | uniq | \\
\t  awk '{{printf "    make %-16s\\n", $$1}}'
\t@echo ""

.PHONY: all clean flash test size disasm symbols help
'''
    (base_path / "Makefile").write_text(content)
    ok("Makefile written  (AVR, atmega328p / Arduino).")

# ─────────────────────────────────────────────────────────────────────────────
#  CMake (both MCUs)
# ─────────────────────────────────────────────────────────────────────────────
def write_cmake(base_path, mcu, mcpu_or_mmcu):
    if mcu == "stm32":
        compiler  = "arm-none-eabi-gcc"
        c_flags   = f"-mcpu={mcpu_or_mmcu} -mthumb -Os -g -Wall -ffunction-sections"
    else:
        compiler  = "avr-gcc"
        c_flags   = f"-mmcu={mcpu_or_mmcu} -DF_CPU=16000000UL -Os -g -Wall"

    tc = base_path / "toolchain" / f"{mcu}_toolchain.cmake"
    tc.write_text(f"""\
# Cross-compiler toolchain file for {mcu.upper()}
# Pass to CMake with: cmake -DCMAKE_TOOLCHAIN_FILE=../toolchain/{mcu}_toolchain.cmake ..

set(CMAKE_SYSTEM_NAME      Generic)
set(CMAKE_SYSTEM_PROCESSOR {mcpu_or_mmcu})

set(CMAKE_C_COMPILER   {compiler})
set(CMAKE_C_FLAGS_INIT "{c_flags}")

# Prevent CMake from testing the compiler with a host-side link step
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
""")

    (base_path / "CMakeLists.txt").write_text(f"""\
cmake_minimum_required(VERSION 3.16)
project({base_path.name} C ASM)

include_directories(include lib/nazengg lib/ST lib/ARM)
file(GLOB SOURCES "src/*.c" "lib/ST/system_*.c" "lib/ST/startup_*.s")

add_executable(main.elf ${{SOURCES}})

# Host-side unit tests (compiled with the host compiler, not cross-compiler)
enable_testing()
add_executable(test_main tests/test_main.c)
target_include_directories(test_main PRIVATE include lib/nazengg)
add_test(NAME unit_tests COMMAND test_main)
""")
    ok("CMakeLists.txt and toolchain file written.")

# ─────────────────────────────────────────────────────────────────────────────
#  Linker script wizard (STM32-specific)
# ─────────────────────────────────────────────────────────────────────────────
def write_linker_script(base_path):
    section("⚙️   LINKER SCRIPT WIZARD")
    teach([
        "The linker script (.ld) is the bridge between your C code and the",
        "physical memory of your MCU.  It tells the GNU linker:",
        "  • Where FLASH starts and how big it is  (your program lives here)",
        "  • Where RAM starts and how big it is    (stack, heap, .bss, .data)",
        "  • How to order sections: .isr_vector → .text → .data → .bss",
        "  • The address of the initial stack pointer (_estack)",
        "Without this file the linker cannot produce a runnable binary.",
    ])

    info("Check your MCU datasheet or reference manual for memory addresses.")
    print(f"  {col(C.DIM, 'Example: STM32F030x6 → FLASH=0x08000000/32K, RAM=0x20000000/4K')}")

    entry      = ask_text("Entry point symbol (matches 2nd vector in startup .s)", "Reset_Handler")
    flash_org  = ask_text("FLASH origin address", "0x08000000")
    flash_len  = ask_text("FLASH length (e.g. 32K, 64K, 256K)", "64K")
    ram_org    = ask_text("RAM origin address",   "0x20000000")
    ram_len    = ask_text("RAM length (e.g. 4K, 20K, 128K)",  "20K")

    content = f'''\
/*
 * Linker script for {base_path.name}
 * Generated by Nazeer Dynamics Project Generator
 *
 * MEMORY layout for your specific MCU:
 *   FLASH: read-only, program code + read-only data live here
 *   RAM  : read-write, stack + heap + .bss + .data live here
 *
 * _estack: initial stack pointer = top of RAM
 *          (ARM Cortex-M stacks grow downward)
 */

ENTRY({entry})

MEMORY
{{
    FLASH (rx)  : ORIGIN = {flash_org}, LENGTH = {flash_len}
    RAM   (rwx) : ORIGIN = {ram_org},   LENGTH = {ram_len}
}}

_estack = ORIGIN(RAM) + LENGTH(RAM);   /* top of RAM = initial stack pointer */

SECTIONS
{{
    /*
     * .isr_vector — must be first in FLASH.
     * The Cortex-M hardware reads the vector table from address 0x08000000
     * at reset to get _estack (word 0) and Reset_Handler address (word 1).
     */
    .isr_vector :
    {{
        KEEP(*(.isr_vector))
    }} > FLASH

    /*
     * .text — all executable code and read-only data.
     * _etext marks the end; used by startup to know where .data LMA starts.
     */
    .text :
    {{
        *(.text)
        *(.text*)
        *(.glue_7)          /* ARM/Thumb interworking stubs */
        *(.glue_7t)
        *(.eh_frame)
        KEEP(*(.init))
        KEEP(*(.fini))
        *(.rodata*)
        . = ALIGN(4);
        _etext = .;
    }} > FLASH

    /*
     * .data — initialised global/static variables.
     * VMA (run address) is RAM; LMA (load address) is FLASH.
     * The startup file copies it from FLASH → RAM using _sidata/_sdata/_edata.
     */
    .data :
    {{
        . = ALIGN(4);
        _sdata = .;         /* RAM destination start */
        *(.data*)
        . = ALIGN(4);
        _edata = .;         /* RAM destination end   */
    }} > RAM AT > FLASH

    _sidata = LOADADDR(.data);  /* FLASH source start */

    /*
     * .bss — uninitialised globals/statics.
     * The linker reserves space in RAM; startup zeroes it (_sbss → _ebss).
     * Not stored in FLASH at all — saves flash space.
     */
    .bss :
    {{
        . = ALIGN(4);
        _sbss = .;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    }} > RAM
}}
'''
    dst = base_path / "lib" / "ST" / "stm32.ld"
    dst.write_text(content.strip())
    ok(f"Linker script written → lib/ST/stm32.ld")
    teach([
        "FLASH AT > RAM  means:",
        "  VMA (Virtual Memory Address) = runtime location in RAM",
        "  LMA (Load Memory Address)    = stored in FLASH",
        "The startup code copies .data from LMA→VMA at boot.",
    ])

# ─────────────────────────────────────────────────────────────────────────────
#  Ask for STM32 core series
# ─────────────────────────────────────────────────────────────────────────────
def ask_stm32_core():
    global stm32_core
    section("🎯  STM32 CORE SERIES")
    teach([
        "The core series (F0, F4, G0 …) determines:",
        "  • The ARM Cortex-M CPU revision  (M0, M4, M7 …)",
        "  • Which -mcpu= GCC flag to use",
        "  • Which CMSIS-Device repo to clone from ST's GitHub",
        "Supported: F0 F1 F2 F3 F4 F7 G0 G4 H7 L0 L1 L4 L5 U5",
    ])
    while True:
        raw = ask_text("STM32 core series (e.g. F0, F4, G0)", "F0")
        core = raw.upper()
        if core in CORE_TO_MCPU:
            stm32_core = core
            ok(f"Core: {core}  →  CPU: {CORE_TO_MCPU[core]}")
            return CORE_TO_MCPU[core]
        err(f"'{core}' not recognised.  Valid cores: {', '.join(CORE_TO_MCPU.keys())}")

# ─────────────────────────────────────────────────────────────────────────────
#  Clone ST CMSIS-Device repo and let user pick files
# ─────────────────────────────────────────────────────────────────────────────
def macro_from_startup_file(name: str) -> str:
    """'startup_stm32f030x6.s'  →  'STM32F030x6'"""
    stem = Path(name).stem
    if not stem.startswith("startup_"):
        raise ValueError(f"Expected 'startup_' prefix, got: {name}")
    device = stem[len("startup_"):]            # stm32f030x6
    return device.upper().replace("X", "x")   # STM32F030x6  (preserve lowercase x)

def setup_stm32_device_files(base_path: Path) -> str:
    """Clone cmsis-device-<core>, copy startup + system + headers.  Returns macro string."""
    global stm32_core, mcu_macro
    section("📦  CLONING ST CMSIS-DEVICE FILES")
    teach([
        "ST publishes official CMSIS-Device packs on GitHub:",
        "  github.com/STMicroelectronics/cmsis-device-<series>",
        "",
        "We need THREE things from this repo:",
        "  1. startup_stm32*.s  — assembly code that runs before main()",
        "  2. system_stm32*.c   — SystemInit(), clock setup",
        "  3. stm32*.h headers  — register struct definitions (RCC, GPIO …)",
    ])

    repo_url   = f"https://github.com/STMicroelectronics/cmsis-device-{stm32_core.lower()}.git"
    clone_dir  = base_path / "temp_st_repo"
    st_dir     = base_path / "lib" / "ST"
    st_dir.mkdir(exist_ok=True)

    info(f"Cloning {repo_url} (shallow clone — fast) …")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err("git clone failed:")
        print(result.stderr)
        err("Check your internet connection, or verify the core series is correct.")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)
    ok("Repository cloned.")

    # ── 1. Startup file ──────────────────────────────────────────────────────
    startup_dir = clone_dir / "Source" / "Templates" / "gcc"
    startup_files = sorted(startup_dir.glob("startup_*.s"))
    if not startup_files:
        err("No startup files found in cloned repo.")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)

    selected_startup = ask_numbered_files(
        "Select the startup file for your exact STM32 device:",
        startup_files,
        teach_lines=[
            "startup_stm32*.s  —  This is the FIRST code that runs on your MCU.",
            "It sets the vector table, initialises the stack, copies .data from",
            "FLASH to RAM, zeroes .bss, calls SystemInit(), then jumps to main().",
            "",
            "Pick the variant that matches your chip (e.g. stm32f030x6 for F030).",
            "Check the device name printed on your MCU or in your datasheet.",
        ],
        min_select=1, max_select=1
    )[0]

    mcu_macro = macro_from_startup_file(selected_startup.name)
    shutil.copy(selected_startup, st_dir / selected_startup.name)
    ok(f"Startup file copied.   Derived macro: {col(C.BOLD, mcu_macro)}")

    # ── 2. System source file ─────────────────────────────────────────────────
    system_files = sorted((clone_dir / "Source" / "Templates").glob("system_*.c"))
    if system_files:
        selected_system = ask_numbered_files(
            "Select the system initialisation source file:",
            system_files,
            teach_lines=[
                "system_stm32*.c  —  Implements SystemInit() which is called by",
                "the startup file before main().  It configures the system clock",
                "(HSI/HSE/PLL) and sets SystemCoreClock — the reference variable",
                "used by delay functions and peripheral drivers to know the CPU speed.",
            ],
            min_select=1, max_select=1
        )[0]
        shutil.copy(selected_system, st_dir / selected_system.name)
        ok(f"System source copied:  {selected_system.name}")
    else:
        warn("No system_*.c file found — you may need to add SystemInit() manually.")

    # ── 3. Header files ───────────────────────────────────────────────────────
    include_dir  = clone_dir / "Include"
    header_files = sorted(include_dir.glob("*.h"))
    if not header_files:
        err("No header files found in Include/.")
        shutil.rmtree(clone_dir, ignore_errors=True)
        sys.exit(1)

    selected_headers = ask_numbered_files(
        "Select header files to copy (you need the device header + stm32Fxx.h + stm32_assert.h if present):",
        header_files,
        teach_lines=[
            "Three key headers are needed:",
            f"  1. {mcu_macro.lower()}.h      — register map for your exact chip",
            f"     (e.g. stm32f030x6.h): peripheral base addresses, IRQ numbers,",
            "     bit-field masks like GPIO_MODER_MODER9, RCC_AHBENR_GPIOCEN …",
            f"  2. stm32{stm32_core.lower()}xx.h  — family umbrella header,",
            "     picks the right device header based on the -D{macro} flag",
            "  3. stm32_assert.h  — optional but useful for assert() in drivers",
            "",
            "Select all that apply — typically 2-4 files for most families.",
        ],
        min_select=1, max_select=len(header_files)
    )
    for h in selected_headers:
        shutil.copy(h, st_dir / h.name)
        ok(f"Header copied:         {h.name}")

    shutil.rmtree(clone_dir, ignore_errors=True)
    ok("Temporary ST repo removed.")
    return mcu_macro

# ─────────────────────────────────────────────────────────────────────────────
#  Clone ARM CMSIS-Core repo and let user pick files
# ─────────────────────────────────────────────────────────────────────────────
def setup_arm_core_files(base_path: Path):
    section("📦  CLONING ARM CMSIS-CORE FILES")
    teach([
        "ARM publishes CMSIS_5 on GitHub (ARM-software/CMSIS_5).",
        "We need the CPU-level headers from CMSIS/Core/Include/:",
        "",
        "  core_cm0.h / core_cm4.h / core_cm7.h",
        "    — Cortex-M CPU register structures (SysTick, NVIC, SCB …)",
        "    — Intrinsic functions (__WFI, __enable_irq, __NOP …)",
        "",
        "  cmsis_gcc.h   — GCC-specific compiler intrinsics",
        "  cmsis_version.h, cmsis_compiler.h  — portability layer",
        "",
        "These are ARCHITECTURE headers, not vendor-specific.",
        "Same file works for every STM32 with the same Cortex-M core.",
    ])

    repo_url  = "https://github.com/ARM-software/CMSIS_5.git"
    clone_dir = base_path / "temp_cmsis5"
    arm_dir   = base_path / "lib" / "ARM"
    arm_dir.mkdir(exist_ok=True)

    info("Cloning ARM CMSIS_5 @ tag 5.9.0 (shallow — only the tip) …")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", "5.9.0",
         repo_url, str(clone_dir)],
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

    mcpu = CORE_TO_MCPU.get(stm32_core, "cortex-m0")
    core_num = mcpu.replace("cortex-m", "").replace("plus", "").replace("+","")
    suggested = f"core_cm{core_num}.h"
    tip(f"For your {stm32_core} series ({mcpu}), you need: "
        f"{col(C.BOLD, suggested)}, cmsis_gcc.h, cmsis_compiler.h, cmsis_version.h")

    selected = ask_numbered_files(
        "Select ARM CMSIS-Core headers to copy:",
        header_files,
        min_select=1, max_select=len(header_files)
    )
    for h in selected:
        shutil.copy(h, arm_dir / h.name)
        ok(f"ARM header copied:     {h.name}")

    shutil.rmtree(clone_dir, ignore_errors=True)
    ok("Temporary ARM repo removed.")

# ─────────────────────────────────────────────────────────────────────────────
#  AVR: no external repos needed — avr-libc ships with avr-gcc
# ─────────────────────────────────────────────────────────────────────────────
def setup_avr_info():
    section("ℹ️   AVR HEADERS")
    teach([
        "Unlike STM32, AVR projects don't need a separately cloned header pack.",
        "The avr-libc package (installed alongside avr-gcc) provides:",
        "",
        "  <avr/io.h>        — register definitions for your -mmcu target",
        "                      (DDRx, PORTx, PINx, UDRx, SPIx, …)",
        "  <util/delay.h>    — accurate _delay_ms() / _delay_us() based on F_CPU",
        "  <avr/interrupt.h> — ISR() macro for writing interrupt handlers",
        "  <avr/pgmspace.h>  — store constant data in FLASH (PROGMEM)",
        "",
        "These headers are automatically found when you pass -mmcu=<device>.",
    ])
    ok("AVR headers handled by avr-libc — no cloning needed.")

# ─────────────────────────────────────────────────────────────────────────────
#  Git init
# ─────────────────────────────────────────────────────────────────────────────
def init_git(base_path: Path):
    section("🗂️   GIT INITIALISATION")
    result = subprocess.run(["git", "init"], cwd=base_path,
                            capture_output=True, text=True)
    if result.returncode == 0:
        ok(f"Git repository initialised in {base_path}")
    else:
        warn(f"git init failed: {result.stderr.strip()}")

# ─────────────────────────────────────────────────────────────────────────────
#  Final summary
# ─────────────────────────────────────────────────────────────────────────────
def print_summary(base_path: Path, mcu: str, build_system: str, use_nazengg: bool):
    section("🎉  PROJECT READY")
    print(f"""
  {col(C.BOLD+C.BWHITE, 'Location:')}  {base_path}
  {col(C.BOLD+C.BWHITE, 'MCU:     ')}  {mcu.upper()}
  {col(C.BOLD+C.BWHITE, 'Build:   ')}  {build_system}
  {col(C.BOLD+C.BWHITE, 'nazengg:')}  {'yes' if use_nazengg else 'no'}
""")
    print(f"  {col(C.BCYAN+C.BOLD, 'Quick-start commands:')}\n")
    print(f"    {col(C.BGREEN, 'cd ' + base_path.name)}")
    if build_system == "make":
        print(f"    {col(C.BGREEN, 'make')}                  {col(C.DIM,'# build everything')}")
        print(f"    {col(C.BGREEN, 'make size')}             {col(C.DIM,'# check flash / RAM usage')}")
        print(f"    {col(C.BGREEN, 'make disasm')}           {col(C.DIM,'# view assembly output')}")
        print(f"    {col(C.BGREEN, 'make flash')}            {col(C.DIM,'# program the board')}")
        print(f"    {col(C.BGREEN, 'make test')}             {col(C.DIM,'# run host unit tests')}")
        print(f"    {col(C.BGREEN, 'make help')}             {col(C.DIM,'# list all targets')}")
    else:
        print(f"    {col(C.BGREEN, 'mkdir build && cd build')}")
        print(f"    {col(C.BGREEN, f'cmake .. -DCMAKE_TOOLCHAIN_FILE=../toolchain/{mcu}_toolchain.cmake')}")
        print(f"    {col(C.BGREEN, 'cmake --build .')}")
        print(f"    {col(C.BGREEN, 'ctest')}")

    if mcu == "stm32":
        print(f"\n  {col(C.BYELLOW+C.BOLD, 'Next steps:')}")
        print(f"  {col(C.DIM, '1. Edit lib/ST/stm32.ld if you need to adjust memory sizes.')}")
        print(f"  {col(C.DIM, '2. Update the -D macro in lib/nazengg/Makefile if needed.')}")
        print(f"  {col(C.DIM, '3. Adjust nazengg.c GPIO pin to match your board LED.')}")
        print(f"  {col(C.DIM, '4. Run: make size  to see your first flash/RAM footprint.')}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
#  Main wizard
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Nazeer Dynamics Embedded Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--about",  action="store_true", help="Show educational overview")
    parser.add_argument("--check",  action="store_true", help="Audit all required tools")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    args = parser.parse_args()

    if args.no_color:
        for attr in vars(C):
            if not attr.startswith("_"):
                setattr(C, attr, "")

    print_banner()

    if args.about:
        print_about()
        return

    if args.check:
        check_all_tools(quiet=False)
        return

    # ── First-run tool check ─────────────────────────────────────────────────
    section("🔍  PRE-FLIGHT TOOLCHAIN CHECK")
    info("Checking commonly needed tools before we start …")
    results = check_all_tools(quiet=True)

    # ── Project basics ───────────────────────────────────────────────────────
    section("📁  PROJECT SETUP")
    project_name = ask_text("Project name (will create a directory)", "my_mcu_project")
    if not project_name:
        err("Project name cannot be empty."); sys.exit(1)

    mcu = ask(
        "Target microcontroller architecture:",
        ["stm32", "avr"],
        [
            "ARM Cortex-M (STM32Fxx/Gxx/Hxx/Lxx) — uses arm-none-eabi-gcc + CMSIS",
            "Atmel/Microchip AVR (ATmega328P/Arduino) — uses avr-gcc + avr-libc",
        ]
    )

    build_system = ask(
        "Build system:",
        ["make", "cmake"],
        [
            "GNU Make  — simpler, widely used in embedded, full ELF analysis targets",
            "CMake     — cross-platform, IDE-friendly, generates Makefiles/Ninja/etc",
        ]
    )

    use_nazengg = ask(
        "Include the 'nazengg' thin HAL library?",
        ["yes", "no"],
        [
            "Yes — adds lib/nazengg/ with GPIO init & LED toggle (good starting point)",
            "No  — bare src/main.c only; you write everything from scratch",
        ]
    ) == "yes"

    # ── Validate tools for chosen MCU ───────────────────────────────────────
    require_tools_for_mcu(mcu, build_system)

    # ── AVR extra config ─────────────────────────────────────────────────────
    avr_mmcu  = "atmega328p"
    avr_fcpu  = "16000000"
    if mcu == "avr":
        section("🔧  AVR DEVICE CONFIGURATION")
        teach([
            "-mmcu=<device> tells avr-gcc the exact chip so it can:",
            "  • Link the correct startup code and I/O definitions",
            "  • Set the correct memory model (flash/RAM sizes)",
            "  • Generate correct EEPROM / fuse access code",
            "",
            "F_CPU must match your crystal/oscillator so _delay_ms() is accurate.",
            "Arduino UNO uses 16 MHz. ATtiny85 @ internal = 8 MHz (or 1 MHz).",
        ])
        avr_mmcu = ask_text("AVR device (-mmcu)", "atmega328p")
        avr_fcpu = ask_text("CPU frequency in Hz (F_CPU)", "16000000")

    # ── STM32 core ───────────────────────────────────────────────────────────
    mcpu = ""
    if mcu == "stm32":
        mcpu = ask_stm32_core()

    # ── Create project ───────────────────────────────────────────────────────
    base_path = Path(project_name).resolve()
    base_path.mkdir(exist_ok=True)

    section(f"🏗️   BUILDING PROJECT: {project_name}")
    create_structure(base_path)
    write_common_files(base_path, project_name, mcu)

    if mcu == "stm32":
        write_main_c_stm32(base_path)
    else:
        write_main_c_avr(base_path)

    write_unit_test_stub(base_path)

    # ── MCU-specific setup ───────────────────────────────────────────────────
    if mcu == "stm32":
        setup_stm32_device_files(base_path)   # clones ST repo, sets mcu_macro
        setup_arm_core_files(base_path)       # clones ARM CMSIS-Core repo

        if use_nazengg:
            write_nazengg_lib_stm32(base_path, mcpu, mcu_macro)

        if build_system == "make":
            write_makefile_stm32(base_path, mcpu, mcu_macro, use_nazengg)
        else:
            write_cmake(base_path, mcu, mcpu)

        write_linker_script(base_path)

    else:  # avr
        setup_avr_info()

        if use_nazengg:
            write_nazengg_lib_avr(base_path, avr_mmcu)

        if build_system == "make":
            write_makefile_avr(base_path, avr_mmcu, avr_fcpu, use_nazengg)
        else:
            write_cmake(base_path, mcu, avr_mmcu)

    # ── Git ─────────────────────────────────────────────────────────────────
    init_git(base_path)

    # ── Done ─────────────────────────────────────────────────────────────────
    print_summary(base_path, mcu, build_system, use_nazengg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {col(C.BYELLOW, '⚠️   Interrupted by user.  Partial project may exist.')}\n")
        sys.exit(0)