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

void configGpio(const char * gpioNumber, const char * direction,
        const int value)
{
    int exportFd;
    int directionFd;
    int valueFd;

    // Base path for gpios
    const char * basePath = "/sys/class/gpio/";

    // Build the path of the export file
    char * exportPath;
    exportPath = malloc(strlen(basePath) + strlen("export"));
    strcpy(exportPath, basePath);
    strcat(exportPath, "export");
    // Open export file
    exportFd = open(exportPath, O_WRONLY);
    if (exportFd < 0)
    {
        printf("Cannot open GPIO to export it!\n");
    }
    // Write which gpio we want to export
    write(exportFd, gpioNumber, 4);
    close(exportFd);
    free(exportPath);

    // Build the path for the direction file
    char * directionPath;
    directionPath = malloc(
            strlen(basePath) + strlen("gpio") + strlen(gpioNumber)
                    + strlen("/direction"));
    strcpy(directionPath, basePath);
    strcat(directionPath, "gpio");
    strcat(directionPath, gpioNumber);
    strcat(directionPath, "/direction");
    // Update the direction of the GPIO to be an output
    directionFd = open(directionPath, O_RDWR);
    if (directionFd < 0)
    {
        printf("Cannot open GPIO direction it\n");
        exit(1);
    }

    write(directionFd, direction, 4);
    close(directionFd);
    free(directionPath);

    // Build the path for the value file
    char * valuePath;
    valuePath = malloc(
            strlen(basePath) + strlen("gpio") + strlen(gpioNumber)
                    + strlen("/value"));
    strcpy(valuePath, basePath);
    strcat(valuePath, "gpio");
    strcat(valuePath, gpioNumber);
    strcat(valuePath, "/value");
    // Write the value
    valueFd = open(valuePath, O_RDWR);
    if (valueFd < 0)
    {
        printf("Cannot open GPIO value\n");
        exit(1);
    }

    write(valueFd, value, 4);
    close(valueFd);
    free(valuePath);
}
