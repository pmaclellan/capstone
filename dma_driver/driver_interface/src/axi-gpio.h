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

// Function prototypes
void configGpio(const char * gpioNumber, const char * direction,
        const int value);

#endif /* SRC_AXI_GPIO_H_ */
