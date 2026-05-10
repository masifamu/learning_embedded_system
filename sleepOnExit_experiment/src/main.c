/******************************************************************************
 * STM32F051R8 - STM32F0 Discovery
 * SLEEPONEXIT Educational Demo
 *
 * REAL LIFE STORY:
 * Night Security Guard
 ******************************************************************************/

#include "stm32f0xx.h"
#include "nazengg.h"

/*----------------------------------------------------------
    SIMPLE DELAY
----------------------------------------------------------*/
void delay(volatile uint32_t d)
{
    while(d--);
}

/*----------------------------------------------------------
    PHONE CALL TIMER (SysTick Interrupt)
----------------------------------------------------------*/
void SysTick_Init(void)
{
    /*
        Interrupt every ~1 second
        assuming 8 MHz clock
    */

    SysTick->LOAD = 8000000 - 1;

    SysTick->VAL = 0;

    SysTick->CTRL =
          SysTick_CTRL_CLKSOURCE_Msk
        | SysTick_CTRL_TICKINT_Msk
        | SysTick_CTRL_ENABLE_Msk;
}

/*----------------------------------------------------------
    MAIN
----------------------------------------------------------*/
int main(void)
{
    nazengg_init();

    SysTick_Init();

    /*
    ==================================================
        COMPANY RULE:
        After emergency,
        immediately sleep again
    ==================================================
    */

    SCB->SCR |= SCB_SCR_SLEEPONEXIT_Msk;

    /*
        Guard starts night shift
    */

    while(1)
    {
        /*
            Guard is awake
            Room light ON
        */

        nazengg_ON_led();

        delay(1500000);

        /*
            Guard preparing to sleep
        */

        nazengg_OFF_led();

        delay(1500000);

        /*
        ==================================================
            GUARD SLEEPS
        ==================================================
        */

        __WFI();

        /*
            IMPORTANT:

            With SLEEPONEXIT enabled,
            CPU usually NEVER RETURNS HERE
        */
    }
}

/*----------------------------------------------------------
    INTERRUPT = PHONE RINGS
----------------------------------------------------------*/
void SysTick_Handler(void)
{
    /*
    ==================================================
        PHONE RINGS!
        Guard wakes up!
    ==================================================
    */

    nazengg_toggle_led();

    delay(500000);

    nazengg_toggle_led();

    /*
    ==================================================
        Emergency handled.
        Guard sleeps again automatically.
    ==================================================
    */
}