# sleepOnExit_experiment

Auto-generated bare-metal STM32 project by Nazeer Dynamics Generator.

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
