/*
 * axi-dma.c
 *
 *  Created on: Nov 13, 2016
 *      Author: dominic
 */

#include <stdio.h>
#include "axi-gpio.h"
#include "axi-dma.h"

DMA_STATUS DmaStatus = UNUSED;

void initDMA()
{
    printf("Initial DMA Configuration...\n");
    // Reset GPIOs
    configGpio(GPIO_TIMESTAMP_RST, SIZE_TIMESTAMP_RST, 1);
    configGpio(GPIO_ADC_EN, SIZE_ADC_EN, 0);
    configGpio(GPIO_SCLK_FREQ, SIZE_SCLK_FREQ, 0);
    configGpio(GPIO_SAMPLE_FREQ, SIZE_SAMPLE_FREQ, 0);
    configGpio(GPIO_PACKETS_PER_FRAME,  SIZE_PACKETS_PER_FRAME, 0);

    // Set config values
    configGpio(GPIO_SCLK_FREQ, SIZE_SCLK_FREQ, SCLK_FREQUENCY);
    configGpio(GPIO_PACKETS_PER_FRAME, SIZE_PACKETS_PER_FRAME, NUM_PACKETS);
}

void startDMA(uint16_t sampleFreq)
{
    printf("Starting DMA...\n");
    // Set the sample frequency
    configGpio(GPIO_SAMPLE_FREQ, SIZE_SAMPLE_FREQ, sampleFreq);
    // Toggle the timestamp reset
    configGpio(GPIO_TIMESTAMP_RST, SIZE_TIMESTAMP_RST, 0);
    // Enable the ADC
    configGpio(GPIO_ADC_EN, SIZE_ADC_EN, 1);
}

void stopDMA()
{
    printf("Stopping DMA...\n");
    // Disable the ADC
    initDMA();
}
