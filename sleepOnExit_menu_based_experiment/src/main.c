/*
===============================================================================
 STM32F051R8 - SLEEPONEXIT POWER LAB
 Board : STM32F0 Discovery
 MCU   : STM32F051R8T6

 CMSIS Register-Level Educational Example

===============================================================================

LAB GOALS
---------
1. Measure RUN current
2. Measure SLEEP current
3. Understand __WFI()
4. Understand SLEEPONEXIT
5. Observe interrupt wakeups
6. Compare clock frequencies
7. Observe peripheral impact on current
8. Observe GPIO analog mode optimization

===============================================================================

LED USAGE
---------
PC8  -> BLUE LED
        ON  = RUN-oriented system
        OFF = Sleep cycle active

PC9  -> GREEN LED
        User-controlled load

BUTTON
------
PA0 -> User Button

UART
----
USART1
PA9  -> TX
PA10 -> RX

IMPORTANT
---------
STM32F0 Discovery usually needs external USB-UART adapter.

===============================================================================
*/

#include "stm32f0xx.h"
#include <stdint.h>

/*==============================================================================
                                SYSTEM STATE
==============================================================================*/

typedef enum
{
    MODE_RUN = 0,
    MODE_SLEEP

}SystemMode_t;

/*==============================================================================
                                GLOBALS
==============================================================================*/

volatile SystemMode_t current_mode = MODE_RUN;

volatile uint8_t sleep_request         = 0;
volatile uint8_t sleep_cycle_active    = 0;

volatile uint8_t timer_enable          = 0;
volatile uint8_t analog_mode_enabled   = 0;
volatile uint8_t low_clock_mode        = 0;
volatile uint8_t high_baud_mode        = 0;
volatile uint8_t sleep_on_exit_enabled = 0;

/*==============================================================================
                                DELAY
==============================================================================*/

void Delay(volatile uint32_t d)
{
    while(d--);
}

/*==============================================================================
                                UART
==============================================================================*/

void UART_SendChar(char c)
{
    while(!(USART1->ISR & USART_ISR_TXE));

    USART1->TDR = (uint8_t)c;
}

void UART_SendString(const char *s)
{
    while(*s)
    {
        UART_SendChar(*s++);
    }
}

/*==============================================================================
                                LED CONTROL
==============================================================================*/

void BlueLED_ON(void)
{
    GPIOC->ODR |= (1UL << 8U);
}

void BlueLED_OFF(void)
{
    GPIOC->ODR &= ~(1UL << 8U);
}

void GreenLED_ON(void)
{
    GPIOC->ODR |= (1UL << 9U);
}

void GreenLED_OFF(void)
{
    GPIOC->ODR &= ~(1UL << 9U);
}

/*==============================================================================
                        WAKEUP EVENT HANDLER
==============================================================================*/

void HandleWakeupEvent(const char *source)
{
    if(sleep_cycle_active)
    {
        sleep_cycle_active = 0;

        current_mode = MODE_RUN;

        BlueLED_ON();

        UART_SendString("\r\nCPU WAKEUP : ");
        UART_SendString(source);
        UART_SendString("\r\n");
    }
}

/*==============================================================================
                                CLOCK
==============================================================================*/

void Clock_48MHz(void)
{
    /*
        Enable HSI
    */

    RCC->CR |= RCC_CR_HSION;

    while(!(RCC->CR & RCC_CR_HSIRDY));

    /*
        PLL source = HSI/2
        4 MHz input
    */

    RCC->CFGR &= ~RCC_CFGR_PLLSRC;

    /*
        PLL x12
        4 MHz x 12 = 48 MHz
    */

    RCC->CFGR &= ~RCC_CFGR_PLLMUL;
    RCC->CFGR |= RCC_CFGR_PLLMUL12;

    /*
        Enable PLL
    */

    RCC->CR |= RCC_CR_PLLON;

    while(!(RCC->CR & RCC_CR_PLLRDY));

    /*
        Select PLL
    */

    RCC->CFGR &= ~RCC_CFGR_SW;
    RCC->CFGR |= RCC_CFGR_SW_PLL;

    while((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL);

    /*
        No prescaler
    */

    RCC->CFGR &= ~RCC_CFGR_HPRE;

    SystemCoreClockUpdate();
}

void Clock_8MHz(void)
{
    /*
        Use HSI directly
    */

    RCC->CR |= RCC_CR_HSION;

    while(!(RCC->CR & RCC_CR_HSIRDY));

    RCC->CFGR &= ~RCC_CFGR_SW;
    RCC->CFGR |= RCC_CFGR_SW_HSI;

    while((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI);

    /*
        Disable PLL
    */

    RCC->CR &= ~RCC_CR_PLLON;

    RCC->CFGR &= ~RCC_CFGR_HPRE;

    SystemCoreClockUpdate();
}

/*==============================================================================
                                GPIO
==============================================================================*/

void GPIO_Init(void)
{
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN;
    RCC->AHBENR |= RCC_AHBENR_GPIOBEN;
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

    /*
        PC8 = BLUE LED
        PC9 = GREEN LED
    */

    GPIOC->MODER &= ~(3UL << (8U * 2U));
    GPIOC->MODER |=  (1UL << (8U * 2U));

    GPIOC->MODER &= ~(3UL << (9U * 2U));
    GPIOC->MODER |=  (1UL << (9U * 2U));

    /*
        Initial states
    */

    BlueLED_ON();

    GreenLED_OFF();

    /*
        PA0 = Button input
    */

    GPIOA->MODER &= ~(3UL << (0U * 2U));
}

/*==============================================================================
                        UNUSED GPIO ANALOG MODE
==============================================================================*/

void UnusedGPIO_Analog(void)
{
    /*
        Keep UART pins untouched
        Keep button untouched
    */

    GPIOB->MODER = 0xFFFFFFFFUL;

    analog_mode_enabled = 1;
}

void RestoreGPIO_Digital(void)
{
    GPIOB->MODER = 0x00000000UL;

    analog_mode_enabled = 0;
}

/*==============================================================================
                                UART INIT
==============================================================================*/

void UART_SetBaud(uint32_t baud)
{
    USART1->BRR = SystemCoreClock / baud;
}

void UART_Init(uint32_t baud)
{
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN;

    /*
        PA9  -> TX
        PA10 -> RX
        AF1
    */

    GPIOA->MODER &= ~(3UL << (9U  * 2U));
    GPIOA->MODER &= ~(3UL << (10U * 2U));

    GPIOA->MODER |=  (2UL << (9U  * 2U));
    GPIOA->MODER |=  (2UL << (10U * 2U));

    GPIOA->AFR[1] &= ~(0xFUL << ((9U  - 8U) * 4U));
    GPIOA->AFR[1] &= ~(0xFUL << ((10U - 8U) * 4U));

    GPIOA->AFR[1] |=  (1UL << ((9U  - 8U) * 4U));
    GPIOA->AFR[1] |=  (1UL << ((10U - 8U) * 4U));

    UART_SetBaud(baud);

    USART1->CR1 =
        USART_CR1_TE       |
        USART_CR1_RE       |
        USART_CR1_RXNEIE   |
        USART_CR1_UE;

    NVIC_EnableIRQ(USART1_IRQn);
}

/*==============================================================================
                                TIMER
==============================================================================*/

void TIM14_Init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM14EN;

    /*
        1 second interrupt @48MHz
    */

    TIM14->PSC = 48000U - 1U;
    TIM14->ARR = 1000U  - 1U;

    TIM14->DIER |= TIM_DIER_UIE;

    NVIC_EnableIRQ(TIM14_IRQn);
}

/*==============================================================================
                                BUTTON EXTI
==============================================================================*/

void Button_EXTI_Init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_SYSCFGCOMPEN;

    SYSCFG->EXTICR[0] &= ~SYSCFG_EXTICR1_EXTI0;

    EXTI->IMR  |= EXTI_IMR_MR0;
    EXTI->RTSR |= EXTI_RTSR_TR0;

    NVIC_EnableIRQ(EXTI0_1_IRQn);
}

/*==============================================================================
                                STATUS
==============================================================================*/

void Print_Status(void)
{
    UART_SendString("\r\n========== STATUS ==========\r\n");

    if(current_mode == MODE_RUN)
    {
        UART_SendString("MODE            : RUN\r\n");
    }
    else
    {
        UART_SendString("MODE            : SLEEP\r\n");
    }

    if(sleep_on_exit_enabled)
    {
        UART_SendString("SLEEPONEXIT     : ON\r\n");
    }
    else
    {
        UART_SendString("SLEEPONEXIT     : OFF\r\n");
    }

    if(timer_enable)
    {
        UART_SendString("TIMER           : ON\r\n");
    }
    else
    {
        UART_SendString("TIMER           : OFF\r\n");
    }

    if(analog_mode_enabled)
    {
        UART_SendString("GPIO MODE       : ANALOG\r\n");
    }
    else
    {
        UART_SendString("GPIO MODE       : DIGITAL\r\n");
    }

    if(low_clock_mode)
    {
        UART_SendString("CLOCK           : 8 MHz\r\n");
    }
    else
    {
        UART_SendString("CLOCK           : 48 MHz\r\n");
    }

    if(high_baud_mode)
    {
        UART_SendString("UART BAUD       : 230400\r\n");
    }
    else
    {
        UART_SendString("UART BAUD       : 115200\r\n");
    }

    UART_SendString("============================\r\n");
}

/*==============================================================================
                                MENU
==============================================================================*/

void Print_Menu(void)
{
    UART_SendString("\r\n");
    UART_SendString("====================================\r\n");
    UART_SendString(" STM32 POWER LAB\r\n");
    UART_SendString("====================================\r\n");

    UART_SendString("h : Help Menu\r\n");
    UART_SendString("p : Print Status\r\n");

    UART_SendString("\r\n");

    UART_SendString("z : Enter Sleep Mode\r\n");

    UART_SendString("\r\n");

    UART_SendString("s : Enable SLEEPONEXIT\r\n");
    UART_SendString("w : Disable SLEEPONEXIT\r\n");

    UART_SendString("\r\n");

    UART_SendString("t : Enable Timer Wakeup\r\n");
    UART_SendString("y : Disable Timer Wakeup\r\n");

    UART_SendString("\r\n");

    UART_SendString("l : GREEN LED ON\r\n");
    UART_SendString("k : GREEN LED OFF\r\n");

    UART_SendString("\r\n");

    UART_SendString("a : GPIO Analog Mode\r\n");
    UART_SendString("d : GPIO Digital Restore\r\n");

    UART_SendString("\r\n");

    UART_SendString("c : Clock = 8 MHz\r\n");
    UART_SendString("f : Clock = 48 MHz\r\n");

    UART_SendString("\r\n");

    UART_SendString("b : UART = 230400\r\n");
    UART_SendString("n : UART = 115200\r\n");

    UART_SendString("====================================\r\n");
}

/*==============================================================================
                                TIMER ISR
==============================================================================*/

void TIM14_IRQHandler(void)
{
    if(TIM14->SR & TIM_SR_UIF)
    {
        TIM14->SR &= ~TIM_SR_UIF;

        HandleWakeupEvent("TIMER");

        UART_SendString("TIMER EVENT\r\n");
    }
}

/*==============================================================================
                                BUTTON ISR
==============================================================================*/

void EXTI0_1_IRQHandler(void)
{
    if(EXTI->PR & EXTI_PR_PR0)
    {
        EXTI->PR |= EXTI_PR_PR0;

        HandleWakeupEvent("BUTTON");

        UART_SendString("BUTTON EVENT\r\n");
    }
}

/*==============================================================================
                                UART ISR
==============================================================================*/

void USART1_IRQHandler(void)
{
    if(USART1->ISR & USART_ISR_RXNE)
    {
        char c;

        HandleWakeupEvent("UART");

        c = (char)USART1->RDR;

        UART_SendString("\r\n> ");
        UART_SendChar(c);
        UART_SendString("\r\n");

        switch(c)
        {
            case 'h':

                Print_Menu();

                break;

            case 'p':

                Print_Status();

                break;

            case 's':

                SCB->SCR |= SCB_SCR_SLEEPONEXIT_Msk;

                sleep_on_exit_enabled = 1;

                UART_SendString(
                    "SLEEPONEXIT ENABLED\r\n"
                    "EXPECTED:\r\n"
                    "- CPU sleeps after ISR\r\n"
                    "- Less thread execution\r\n"
                );

                break;

            case 'w':

                SCB->SCR &= ~SCB_SCR_SLEEPONEXIT_Msk;

                sleep_on_exit_enabled = 0;

                UART_SendString(
                    "SLEEPONEXIT DISABLED\r\n"
                    "EXPECTED:\r\n"
                    "- CPU returns to main\r\n"
                );

                break;

            case 't':

                TIM14->CNT = 0U;

                TIM14->CR1 |= TIM_CR1_CEN;

                timer_enable = 1;

                UART_SendString(
                    "TIMER ENABLED\r\n"
                    "EXPECTED:\r\n"
                    "- Periodic wakeups\r\n"
                );

                break;

            case 'y':

                TIM14->CR1 &= ~TIM_CR1_CEN;

                timer_enable = 0;

                UART_SendString(
                    "TIMER DISABLED\r\n"
                    "EXPECTED:\r\n"
                    "- No periodic wakeups\r\n"
                );

                break;

            case 'l':

                GreenLED_ON();

                UART_SendString(
                    "GREEN LED ON\r\n"
                    "EXPECTED:\r\n"
                    "- Higher current\r\n"
                );

                break;

            case 'k':

                GreenLED_OFF();

                UART_SendString(
                    "GREEN LED OFF\r\n"
                    "EXPECTED:\r\n"
                    "- Lower current\r\n"
                );

                break;

            case 'a':

                UnusedGPIO_Analog();

                UART_SendString(
                    "GPIO ANALOG MODE\r\n"
                    "EXPECTED:\r\n"
                    "- Lower leakage current\r\n"
                );

                break;

            case 'd':

                RestoreGPIO_Digital();

                UART_SendString(
                    "GPIO DIGITAL RESTORE\r\n"
                    "EXPECTED:\r\n"
                    "- Slightly higher leakage\r\n"
                );

                break;

            case 'c':

                Clock_8MHz();

                UART_SetBaud(115200U);

                low_clock_mode = 1;

                UART_SendString(
                    "CLOCK = 8 MHz\r\n"
                    "EXPECTED:\r\n"
                    "- Lower power\r\n"
                    "- Lower performance\r\n"
                );

                break;

            case 'f':

                Clock_48MHz();

                UART_SetBaud(115200U);

                low_clock_mode = 0;

                UART_SendString(
                    "CLOCK = 48 MHz\r\n"
                    "EXPECTED:\r\n"
                    "- Higher performance\r\n"
                    "- Higher power\r\n"
                );

                break;

            case 'b':

                UART_SetBaud(230400U);

                high_baud_mode = 1;

                UART_SendString(
                    "UART = 230400\r\n"
                );

                break;

            case 'n':

                UART_SetBaud(115200U);

                high_baud_mode = 0;

                UART_SendString(
                    "UART = 115200\r\n"
                );

                break;

            case 'z':

                sleep_request = 1;

                UART_SendString(
                    "SLEEP REQUESTED\r\n"
                    "EXPECTED:\r\n"
                    "- Blue LED OFF\r\n"
                    "- Lower current\r\n"
                    "- Wake using UART/button/timer\r\n"
                );

                break;

            default:

                UART_SendString(
                    "UNKNOWN COMMAND\r\n"
                );

                break;
        }
    }
}

/*==============================================================================
                                MAIN
==============================================================================*/

int main(void)
{
    /*
        Disable SysTick
        Better current measurements
    */

    SysTick->CTRL = 0U;

    /*
        Start at 48 MHz
    */

    Clock_48MHz();

    /*
        Initialize peripherals
    */

    GPIO_Init();

    UART_Init(115200U);

    TIM14_Init();

    Button_EXTI_Init();

    /*
        Startup message
    */

    UART_SendString("\r\n");
    UART_SendString("====================================\r\n");
    UART_SendString(" STM32 POWER LAB READY\r\n");
    UART_SendString("====================================\r\n");

    UART_SendString(
        "INITIAL STATE:\r\n"
        "- RUN MODE\r\n"
        "- BLUE LED ON\r\n"
        "- GREEN LED OFF\r\n"
        "- TIMER OFF\r\n"
        "- Measure RUN current now\r\n"
    );

    Print_Menu();

    /*
        Main Loop
    */

    while(1)
    {
        if(sleep_request)
        {
            sleep_request = 0;

            sleep_cycle_active = 1;

            current_mode = MODE_SLEEP;

            /*
                Blue LED OFF
            */

            BlueLED_OFF();

            UART_SendString(
                "\r\nCPU ENTERING SLEEP\r\n"
            );

            /*
                Wait for UART complete
            */

            while(!(USART1->ISR & USART_ISR_TC));

            Delay(100000U);

            /*
                ENTER SLEEP
            */

            __WFI();
        }
    }
}