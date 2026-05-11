#include "nazengg.h"
/*
 * Include the FAMILY umbrella header (e.g. stm32f0xx.h), not the
 * device-specific one directly.  The umbrella reads the -DSTM32F051x8
 * flag and pulls in the correct chip header automatically.
 *
 * PC9 is the green LED on the STM32F0-Discovery board.
 * Change GPIOC / RCC_AHBENR_GPIOCEN / GPIO_ODR_9 for your own board.
 */
#include "stm32f0xx.h"

void nazengg_init(void) {
    /* 1. Gate the GPIO clock -- without this the peripheral is dead */
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

    /* 2. Set PC9 as general-purpose output (MODER = 0b01) */
    GPIOC->MODER &= ~GPIO_MODER_MODER9;    /* clear both bits first */
    GPIOC->MODER |=  GPIO_MODER_MODER9_0;  /* bit0=1 -> output mode  */

    /* 3. Output type: push-pull (reset default, explicit for clarity) */
    GPIOC->OTYPER &= ~GPIO_OTYPER_OT_9;

    /* 4. No pull-up / pull-down (reset default) */
    GPIOC->PUPDR  &= ~GPIO_PUPDR_PUPDR9;
}

void nazengg_toggle_led(void) {
    GPIOC->ODR ^= GPIO_ODR_9;   /* XOR -- atomic read-modify-write on ODR */
}
