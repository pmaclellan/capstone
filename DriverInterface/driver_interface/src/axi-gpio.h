/*
 * axi-gpio.h
 *
 *  Created on: Nov 11, 2016
 *      Author: dominic
 *      Description: Contains data structures and methods used for configuring
 *      AXI GPIOs
 */

#ifndef SRC_AXI_GPIO_H_
#define SRC_AXI_GPIO_H_

#include <stdint.h>
#include <inttypes.h>

// Function prototypes
void configGpio(int address, int size, int value);

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

// GPIO Definitions
#define GPIO_ADC_EN             0x41200000
#define GPIO_TIMESTAMP_RST      0x41200008
#define GPIO_SCLK_FREQ          0x41210000
#define GPIO_SAMPLE_FREQ        0x41210008
#define GPIO_PACKETS_PER_FRAME  0x41220000
#define GPIO_FIFO_COUNT         0x41220008
#define GPIO_OVERFLOW           0x41230000

// Note: devmem requires factors of 8 for size!
#define SIZE_TIMESTAMP_RST      8
#define SIZE_ADC_EN             8
#define SIZE_SCLK_FREQ          16
#define SIZE_SAMPLE_FREQ        16
#define SIZE_PACKETS_PER_FRAME  16
#define SIZE_OVERFLOW           8

#endif /* SRC_AXI_GPIO_H_ */
