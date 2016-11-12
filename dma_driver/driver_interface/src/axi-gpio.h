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

#endif /* SRC_AXI_GPIO_H_ */
