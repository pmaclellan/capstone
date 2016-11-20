/*
 * axi-gpio.c
 *
 *  Created on: Nov 11, 2016
 *      Author: dominic
 */

#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdio.h>
#include "axi-gpio.h"

void configGpio(int address, int size, int value)
{
    char command[100];
    sprintf(command, "/sbin/devmem 0x%08X %d %d", address, size, value);
    system(command);
}

void readGpio(int address, int size)
{
    char command[100];
    sprintf(command, "/sbin/devmem 0x%08X %d", address, size);
}
