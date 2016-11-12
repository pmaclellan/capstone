/*
 ============================================================================
 Name        : driver_interface.c
 Author      : Dominic Harkness
 Version     :
 Copyright   : Copyright Dominic Harkness
 Description : main function for DMA Driver Interface application
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <inttypes.h>
#include <fcntl.h>
#include "axi-gpio.h"
#include "server-start.h"

#define NUM_PACKETS         4 // 4 packets
#define LINES_PER_PACKET    9 // 1 header and 8 lines of data

int main(void)
{
    /*
     * GPIOs are used to configure the dma. The addresses and their
     * configuration values are the following:
     *
     * ADDRESS      SIZE/DIRECTION  DESCRIPTION
     * 0x41200000   1/out           Timestamp reset
     * 0x41200008   1/out           ADC Enable
     * 0x41210000   16/out          SPI Clock Frequency (value = 2 = 25MHz)
     * 0x41210008   16/out          Sampling frequency (Freq = 100MHz / value)
     * 0x41220000   8/out           Zedboard LEDs
     * 0x41220008   16/out          Data packets per frame
     * 0x41230000   1/in            Internal buffer overflow
     */

    // Begin actual config
    printf("Initial DMA Configuration...\n");
    // Before config starts, set everything to 0
    configGpio(GPIO_TIMESTAMP_RST, SIZE_TIMESTAMP_RST, 0);
    configGpio(GPIO_ADC_EN, SIZE_ADC_EN, 0);
    configGpio(GPIO_SCLK_FREQ, SIZE_SCLK_FREQ, 0);
    configGpio(GPIO_SAMPLE_FREQ, SIZE_SAMPLE_FREQ, 0);
    configGpio(GPIO_LEDS, SIZE_LEDS, 0);
    configGpio(GPIO_PACKETS_PER_FRAME,  SIZE_PACKETS_PER_FRAME, 0);

    // Set config values
    configGpio(GPIO_SCLK_FREQ, SIZE_SCLK_FREQ, 2);
    configGpio(GPIO_SAMPLE_FREQ, SIZE_SAMPLE_FREQ, 1000);
    configGpio(GPIO_PACKETS_PER_FRAME, SIZE_PACKETS_PER_FRAME, NUM_PACKETS);
    configGpio(GPIO_TIMESTAMP_RST, SIZE_TIMESTAMP_RST, 1);
    configGpio(GPIO_TIMESTAMP_RST, SIZE_TIMESTAMP_RST, 0);
    configGpio(GPIO_ADC_EN, SIZE_ADC_EN, 1);

    // Await start command from server
    printf("Awaiting server start command...\n");
    // TODO: 11/13

    // Create a buffer to put our DMA data into
    // Note: Add 2 to the number of packets because DMA will give 2 extra
    // packets (with garbage) for the number you configure
    uint64_t * buf;
    size_t bufSize = (NUM_PACKETS + 2) * LINES_PER_PACKET * sizeof(uint64_t);
    buf = malloc(bufSize);

    // Open the axidma device
    int axiDmaFd = open("/dev/axidma_rx", O_RDONLY);

    // Print some data for debugging
    int count = 0;
    while(count < 4)
    {
        read(axiDmaFd, buf, bufSize);
        printf("Buffer contents are:\n");
        int i;
        for (i = 0; i < (NUM_PACKETS * LINES_PER_PACKET); i++)
        {
            if (i % 9 == 0)
            {
                printf("buf[%d] = 0x%" PRIx64 "\n", i, buf[i]);
            }
        }
        count++;
    }

    close(axiDmaFd);
    free(buf);

    return 0;
}
