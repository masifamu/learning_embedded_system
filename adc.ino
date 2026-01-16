/*
 * Register-level ADC example for Arduino Uno (ATmega328P)
 * Reads:
 * 1. Internal temperature sensor
 * 2. Internal 1.1V bandgap reference
 * 3. External potentiometer on ADC channel 1 (A1)
 */

#include <Arduino.h>

/* Function prototypes */
void ADC_init(void);
uint16_t ADC_read(uint8_t channel);
float read_internal_temperature(void);
float read_internal_reference(void);

void setup()
{
    /* Initialize UART for output */
    Serial.begin(9600);

    /* Initialize ADC at register level */
    ADC_init();
}

void loop()
{
    uint16_t pot_raw;
    float temperature_c;
    float vcc_voltage;

    /* Read potentiometer connected to ADC1 (A1) */
    pot_raw = ADC_read(1);

    /* Read internal temperature sensor */
    temperature_c = read_internal_temperature();

    /* Read internal reference (used to calculate VCC) */
    vcc_voltage = read_internal_reference();

    /* Display results */
    Serial.print("Potentiometer (ADC1 Raw): ");
    Serial.println(pot_raw);

    Serial.print("Internal Temperature (approx C): ");
    Serial.println(temperature_c);

    Serial.print("Calculated VCC (V): ");
    Serial.println(vcc_voltage);

    Serial.println("-----------------------------");

    delay(1000);
}

/*--------------------------------------------------
 * ADC Initialization (Register Level)
 *--------------------------------------------------*/
void ADC_init(void)
{
    /*
     * ADMUX Register:
     * - REFS1:0 = 01 → AVcc with external capacitor at AREF
     * - ADLAR = 0 → Right-adjust result
     */
    ADMUX = (1 << REFS0);

    /*
     * ADCSRA Register:
     * - ADEN  = 1 → Enable ADC
     * - ADPS2:0 = 111 → Prescaler = 128
     *   ADC clock = 16 MHz / 128 = 125 kHz
     */
    ADCSRA = (1 << ADEN) |
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

    /*
     * Disable digital input buffers on ADC pins
     * to reduce power consumption
     */
    DIDR0 = 0x3F;   // Disable ADC0–ADC5 digital input buffers
}

/*--------------------------------------------------
 * Generic ADC Read Function
 * channel: 0–7  → External ADC pins
 *          8    → Internal temperature sensor
 *          14   → Internal 1.1V bandgap reference
 *--------------------------------------------------*/
uint16_t ADC_read(uint8_t channel)
{
    /* Clear previous channel selection */
    ADMUX &= 0xF0;

    /* Select new ADC channel */
    ADMUX |= (channel & 0x0F);

    /*
     * Start ADC conversion
     */
    ADCSRA |= (1 << ADSC);

    /*
     * Wait until conversion completes
     * ADSC bit becomes 0 again
     */
    while (ADCSRA & (1 << ADSC));

    /*
     * ADC result is in ADCL (low byte) and ADCH (high byte)
     * Must read ADCL first
     */
    return ADC;
}

/*--------------------------------------------------
 * Read Internal Temperature Sensor
 *--------------------------------------------------*/
float read_internal_temperature(void)
{
    uint16_t raw;

    /*
     * Select internal 1.1V reference
     * Required for temperature sensor
     */
    ADMUX = (1 << REFS1) | (1 << REFS0);

    /*
     * Select temperature sensor channel (ADC8)
     */
    ADMUX |= (1 << MUX3);

    delay(2);  // Allow reference to settle

    raw = ADC_read(8);

    /*
     * Temperature calculation (approximate)
     * Datasheet typical values:
     *  - 1 LSB ≈ 1.22 mV
     *  - 25°C ≈ 314 ADC counts
     */
    float temperature = (raw - 314.0) / 1.22 + 25.0;

    return temperature;
}

/*--------------------------------------------------
 * Measure Internal 1.1V Reference to Calculate VCC
 *--------------------------------------------------*/
float read_internal_reference(void)
{
    uint16_t raw;

    /*
     * Select AVcc as reference
     */
    ADMUX = (1 << REFS0);

    /*
     * Select internal 1.1V bandgap (ADC14)
     * MUX[3:0] = 1110
     */
    ADMUX |= (1 << MUX3) | (1 << MUX2) | (1 << MUX1);

    delay(2);  // Reference settling time

    raw = ADC_read(14);

    /*
     * VCC calculation:
     * VCC = (1.1V * 1023) / ADC_reading
     */
    float vcc = (1.1 * 1023.0) / raw;

    return vcc;
}

