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
//
//XGpio: /amba_pl/gpio@41200000: registered, base is 905
//XGpio: /amba_pl/gpio@41200000: dual channel registered, base is 904
//XGpio: /amba_pl/gpio@41210000: registered, base is 888
//XGpio: /amba_pl/gpio@41210000: dual channel registered, base is 872
//XGpio: /amba_pl/gpio@41220000: registered, base is 864
//XGpio: /amba_pl/gpio@41220000: dual channel registered, base is 848
//XGpio: /amba_pl/gpio@41230000: registered, base is 847
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <inttypes.h>
#include <fcntl.h>
#include "axi-gpio.h"
#include "server-start.h"

int main(void)
{
    // Before config starts, set everything to 0
    configGpio("905", "out", "0");
    configGpio("904", "out", "0");
    configGpio("888", "out", "0");
    configGpio("872", "out", "0");
    configGpio("864", "out", "0");
    configGpio("848", "out", "0");

    // Begin actual config
    printf("Begin DMA Configuration\n");

    // (GPIO 888) Configure SPI clock:
    //      2 = 25MHz
    // (GPIO 872) Configure Sample Frequency:
    //      Sample freq = 100MHz / value (ex. 100MHz / 1000 = 100kHz)
    // (GPIO 848) Configure the number of packets / frame:
    //      NOTE: Setting this to 4 will actually make it send 5.5 packets. The
    //      last 1.5 packets are garbage that this app will need to throw out.
    // (GPIO 905) Timestamp reset:
    //      Set high, then low to reset the timestamp
    // (GPIO 904) ADC Enable:
    //      Set high to enable ADC
    configGpio("888", "out", "2");
    configGpio("872", "out", "1000");
    configGpio("848", "out", "4");
    configGpio("904", "out", "1");
    configGpio("905", "out", "1");
    configGpio("905", "out", "0");

    // Await start command from server
    printf("Awaiting server start command...\n");



    // Create a buffer to put our DMA data into:
    //      size = (6 packets) x (9 lines / packet) x (8 bytes / line)
    uint64_t * buf;
    size_t bufSize = 6 * 9 * 8;
    buf = malloc(bufSize);

    // Open the axidma device
    int axiDmaFd = open("/dev/axidma_rx", O_RDONLY);

    // Toggle LED to signal successful DMA config
    while(1)
    {
        read(axiDmaFd, buf, bufSize);
        printf("Buffer contents are:\n");
        int i;
        for (i = 0; i < (36); i++)
        {
            printf("buf[%d] = 0x%" PRIx64 "\n", i, buf[i]);
        }

        configGpio("864", "out", "0");
        sleep(1);
        configGpio("864", "out", "1");
        sleep(1);
    }

    close(axiDmaFd);
    free(buf);

    return 0;
}
