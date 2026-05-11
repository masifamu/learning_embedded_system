#include "stm32f0xx.h"

/*=========================================================
                    GLOBAL FLAGS
=========================================================*/

volatile uint8_t timer_enable = 1;
volatile uint8_t analog_mode_enabled = 0;
volatile uint8_t low_clock_mode = 0;
volatile uint8_t high_baud = 0;

/*=========================================================
                    UART HELPERS
=========================================================*/

void UART_SendChar(char c)
{
    while(!(USART1->ISR & USART_ISR_TXE));
    USART1->TDR = c;
}

void UART_SendString(char *s)
{
    while(*s)
    {
        UART_SendChar(*s++);
    }
}

/*=========================================================
                    CLOCK SETUP
=========================================================*/

void Clock_48MHz(void)
{
    /* Enable HSI */
    RCC->CR |= RCC_CR_HSION;

    while(!(RCC->CR & RCC_CR_HSIRDY));

    /* PLL source = HSI/2 */
    RCC->CFGR &= ~RCC_CFGR_PLLSRC;

    /* PLL MUL = x12
       4 MHz x 12 = 48 MHz
    */
    RCC->CFGR &= ~RCC_CFGR_PLLMUL;
    RCC->CFGR |= RCC_CFGR_PLLMUL12;

    /* Enable PLL */
    RCC->CR |= RCC_CR_PLLON;

    while(!(RCC->CR & RCC_CR_PLLRDY));

    /* Select PLL as system clock */
    RCC->CFGR &= ~RCC_CFGR_SW;
    RCC->CFGR |= RCC_CFGR_SW_PLL;

    while((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL);

    SystemCoreClockUpdate();
}

void Clock_2MHz(void)
{
    /* Use HSI directly */
    RCC->CR |= RCC_CR_HSION;

    while(!(RCC->CR & RCC_CR_HSIRDY));

    /* Switch to HSI */
    RCC->CFGR &= ~RCC_CFGR_SW;
    RCC->CFGR |= RCC_CFGR_SW_HSI;

    while((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI);

    /* Disable PLL */
    RCC->CR &= ~RCC_CR_PLLON;

    /* AHB Prescaler /4
       8 MHz / 4 = 2 MHz
    */
    RCC->CFGR &= ~RCC_CFGR_HPRE;
    RCC->CFGR |= RCC_CFGR_HPRE_DIV4;

    SystemCoreClockUpdate();
}
/*=========================================================
                    GPIO
=========================================================*/

void GPIO_Init(void)
{
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN;
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

    /* PC9 LED */
    GPIOC->MODER |= (1 << (9*2));

    /* PA0 button input */
    GPIOA->MODER &= ~(3U << (0U*2U));
}

void UnusedPins_Analog(void)
{
    /* Example:
       Make PB pins analog
    */

    RCC->AHBENR |= RCC_AHBENR_GPIOBEN;

    GPIOB->MODER = 0xFFFFFFFF;

    analog_mode_enabled = 1;
}

void RestorePins_Digital(void)
{
    GPIOB->MODER = 0x00000000;

    analog_mode_enabled = 0;
}

/*=========================================================
                    USART1
=========================================================*/

void UART_SetBaud(uint32_t baud)
{
    USART1->BRR = SystemCoreClock / baud;
}

void UART_Init(uint32_t baud)
{
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN;

    RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

    /* PA9 TX, PA10 RX AF1 */

    GPIOA->MODER |= (2 << (9*2));
    GPIOA->MODER |= (2 << (10*2));

    GPIOA->AFR[1] |= (1 << ((9-8)*4));
    GPIOA->AFR[1] |= (1 << ((10-8)*4));

    UART_SetBaud(baud);

    USART1->CR1 =
        USART_CR1_TE |
        USART_CR1_RE |
        USART_CR1_RXNEIE |
        USART_CR1_UE;

    NVIC_EnableIRQ(USART1_IRQn);
}

/*=========================================================
                    TIMER
=========================================================*/

void TIM14_Init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM14EN;

    TIM14->PSC = 48000 - 1;
    TIM14->ARR = 500 - 1;

    TIM14->DIER |= TIM_DIER_UIE;

    TIM14->CR1 |= TIM_CR1_CEN;

    NVIC_EnableIRQ(TIM14_IRQn);
}

/*=========================================================
                    BUTTON INTERRUPT
=========================================================*/

void EXTI_ButtonInit(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_SYSCFGCOMPEN;

    SYSCFG->EXTICR[0] &= ~SYSCFG_EXTICR1_EXTI0;

    EXTI->IMR |= EXTI_IMR_MR0;
    EXTI->RTSR |= EXTI_RTSR_TR0;

    NVIC_EnableIRQ(EXTI0_1_IRQn);
}

/*=========================================================
                    PRINT MENU
=========================================================*/

void Print_Menu(void)
{
    UART_SendString("\r\n=== SLEEPONEXIT LAB ===\r\n");
    UART_SendString("s : Enable SLEEPONEXIT\r\n");
    UART_SendString("w : Disable SLEEPONEXIT\r\n");
    UART_SendString("t : Enable timer\r\n");
    UART_SendString("y : Disable timer\r\n");
    UART_SendString("a : Unused GPIO Analog\r\n");
    UART_SendString("d : Restore GPIO Digital\r\n");
    UART_SendString("c : 2MHz Clock\r\n");
    UART_SendString("f : 48MHz Clock\r\n");
    UART_SendString("b : 230400 baud\r\n");
    UART_SendString("n : 115200 baud\r\n");
    UART_SendString("p : Print status\r\n");
}

/*=========================================================
                    STATUS
=========================================================*/

void Print_Status(void)
{
    UART_SendString("\r\nSTATUS\r\n");

    if(SCB->SCR & SCB_SCR_SLEEPONEXIT_Msk)
        UART_SendString("SLEEPONEXIT: ON\r\n");
    else
        UART_SendString("SLEEPONEXIT: OFF\r\n");

    if(timer_enable)
        UART_SendString("Timer: ON\r\n");
    else
        UART_SendString("Timer: OFF\r\n");

    if(analog_mode_enabled)
        UART_SendString("Unused GPIO: ANALOG\r\n");
    else
        UART_SendString("Unused GPIO: DIGITAL\r\n");

    if(low_clock_mode)
        UART_SendString("Clock: 2MHz\r\n");
    else
        UART_SendString("Clock: 48MHz\r\n");
}

/*=========================================================
                    TIMER ISR
=========================================================*/

void TIM14_IRQHandler(void)
{
    if(TIM14->SR & TIM_SR_UIF)
    {
        TIM14->SR &= ~TIM_SR_UIF;

        GPIOC->ODR ^= (1 << 9);
    }
}

/*=========================================================
                    BUTTON ISR
=========================================================*/

void EXTI0_1_IRQHandler(void)
{
    if(EXTI->PR & EXTI_PR_PR0)
    {
        EXTI->PR |= EXTI_PR_PR0;

        UART_SendString("Button Wakeup\r\n");
    }
}

/*=========================================================
                    UART ISR
=========================================================*/

void USART1_IRQHandler(void)
{
    if(USART1->ISR & USART_ISR_RXNE)
    {
        char c = (char)USART1->RDR;

        switch(c)
        {
            case 'h':
                Print_Menu();
                break;

            case 's':
                SCB->SCR |= SCB_SCR_SLEEPONEXIT_Msk;
                UART_SendString("SLEEPONEXIT ENABLED\r\n");
                break;

            case 'w':
                SCB->SCR &= ~SCB_SCR_SLEEPONEXIT_Msk;
                UART_SendString("SLEEPONEXIT DISABLED\r\n");
                break;

            case 't':
                TIM14->CR1 |= TIM_CR1_CEN;
                timer_enable = 1;
                break;

            case 'y':
                TIM14->CR1 &= ~TIM_CR1_CEN;
                timer_enable = 0;
                break;

            case 'a':
                UnusedPins_Analog();
                break;

            case 'd':
                RestorePins_Digital();
                break;

            case 'c':
                Clock_2MHz();
                low_clock_mode = 1;
                UART_SetBaud(115200);
                break;

            case 'f':
                Clock_48MHz();
                low_clock_mode = 0;
                UART_SetBaud(115200);
                break;

            case 'b':
                UART_SetBaud(230400);
                high_baud = 1;
                break;

            case 'n':
                UART_SetBaud(115200);
                high_baud = 0;
                break;

            case 'p':
                Print_Status();
                break;
        }
    }
}

/*=========================================================
                    MAIN
=========================================================*/

int main(void)
{
    Clock_48MHz();

    GPIO_Init();

    UART_Init(115200);

    TIM14_Init();

    EXTI_ButtonInit();

    Print_Menu();

    UART_SendString("\r\nCPU RUNNING...\r\n");

    while(1)
    {
        __WFI();
    }
}