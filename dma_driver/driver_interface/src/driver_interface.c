/*
 ============================================================================
 Name        : driver_interface.c
 Author      : Dominic Harkness
 Version     :
 Copyright   : Copyright Dominic Harkness
 Description : main function for DMA Driver Interface application
 ============================================================================
 */

// The following commands from the console setup the GPIO to be
// exported, set the direction of it to an output and write a 1
// to the GPIO.
//
// bash> echo 240 > /sys/class/gpio/export
// bash> echo out > /sys/class/gpio/gpio240/direction
// bash> echo 1 > /sys/class/gpio/gpio240/value
// GPIO Configuration is as follows:
//XGpio: /amba_pl/gpio@41200000: registered, base is 905
//XGpio: /amba_pl/gpio@41200000: dual channel registered, base is 904
//XGpio: /amba_pl/gpio@41210000: registered, base is 888
//XGpio: /amba_pl/gpio@41210000: dual channel registered, base is 872
//XGpio: /amba_pl/gpio@41220000: registered, base is 864
//XGpio: /amba_pl/gpio@41220000: dual channel registered, base is 848
//XGpio: /amba_pl/gpio@41230000: registered, base is 847
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>

int main(void) {
    int fdLEDValue;
    int fdLEDExport;
    int fdLEDDirection;

    printf("Begin DMA Configuration\n");

    fdLEDExport = open("/sys/class/gpio/export", O_WRONLY);
    if (fdLEDExport < 0) {
        printf("Cannot open GPIO to export it!\n");
    }

    // LED GPIO is 864
    write(fdLEDExport, "864", 4);
    close(fdLEDExport);

    printf("GPIO exported successfully\n");

    // Update the direction of the GPIO to be an output
    fdLEDDirection = open("/sys/class/gpio/gpio864/direction", O_RDWR);
    if (fdLEDDirection < 0) {
        printf("Cannot open GPIO direction it\n");
        exit(1);
    }

    write(fdLEDDirection, "out", 4);
    close(fdLEDDirection);

    printf("GPIO direction set as output successfully\n");

    // Get the GPIO value ready to be toggled

    fdLEDValue = open("/sys/class/gpio/gpio864/value", O_RDWR);
    if (fdLEDValue < 0) {
        printf("Cannot open GPIO value\n");
        exit(1);
    }

    printf("GPIO value opened, now toggling...\n");

    // toggle the GPIO as fast a possible forever, a control c is needed
    // to stop it

    while (1) {
        write(fdLEDValue, "1", 2);
        write(fdLEDValue, "0", 2);
    }

    return 0;
}
