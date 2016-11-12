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

// GPIO Definitions
#define GPIO_TIMESTAMP_RST      0x41200000
#define GPIO_ADC_EN             0x41200008
#define GPIO_SCLK_FREQ          0x41210000
#define GPIO_SAMPLE_FREQ        0x41210008
#define GPIO_LEDS               0x41220000
#define GPIO_PACKETS_PER_FRAME  0x41220008
#define GPIO_OVERFLOW           0x41230000

#define SIZE_TIMESTAMP_RST      1
#define SIZE_ADC_EN             1
#define SIZE_SCLK_FREQ          16
#define SIZE_SAMPLE_FREQ        16
#define SIZE_LEDS               8
#define SIZE_PACKETS_PER_FRAME  16
#define SIZE_OVERFLOW           1

#endif /* SRC_AXI_GPIO_H_ */
