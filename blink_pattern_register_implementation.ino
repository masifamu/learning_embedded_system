void setup()
{
    /* Configure PB5 (Arduino Pin 13) as OUTPUT */
    DDRB |= (1 << DDB5);
}

void loop()
{
    /* 1. Slow Blink */
    PORTB |= (1 << PORTB5);   // LED ON
    delay(1000);

    PORTB &= ~(1 << PORTB5);  // LED OFF
    delay(1000);

    /* 2. Fast Blink using TOGGLE */
    for (uint8_t i = 0; i < 10; i++)
    {
        PORTB ^= (1 << PORTB5);   // Toggle LED
        delay(100);
    }

    /* 3. Double Flash */
    PORTB |= (1 << PORTB5);
    delay(150);
    PORTB &= ~(1 << PORTB5);
    delay(150);

    PORTB |= (1 << PORTB5);
    delay(150);
    PORTB &= ~(1 << PORTB5);

    /* 4. Pause */
    delay(1000);
}

