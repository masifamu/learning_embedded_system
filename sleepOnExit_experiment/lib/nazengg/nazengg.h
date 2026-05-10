#pragma once
/*
 * nazengg -- minimal portable LED driver for STM32.
 * Edit nazengg.c to retarget to a different GPIO pin.
 */
void nazengg_init(void);
void nazengg_toggle_led(void);
void nazengg_ON_led(void);
void nazengg_OFF_led(void);
