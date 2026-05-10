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
    printf("All tests passed.\n");
    return 0;
}
