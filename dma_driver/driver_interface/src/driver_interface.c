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
    configGpio(0x41200000, 8, 0);
    configGpio(0x41200008, 8, 0);
    configGpio(0x41210000, 8, 0);
    configGpio(0x41210008, 8, 0);
    configGpio(0x41220000, 8, 0);
    configGpio(0x41220008, 8, 0);

    // Begin actual config
    printf("Begin DMA Configuration\n");

    // (0x41210000) Configure SPI clock:
    //      2 = 25MHz
    // (0x41210008) Configure Sample Frequency:
    //      Sample freq = 100MHz / value (ex. 100MHz / 1000 = 100kHz)
    // (0x41220008) Configure the number of packets / frame:
    //      NOTE: Setting this to 4 will actually make it send 5.5 packets. The
    //      last 1.5 packets are garbage that this app will need to throw out.
    // (0x41200000) Timestamp reset:
    //      Set high, then low to reset the timestamp
    // (0x41200008) ADC Enable:
    //      Set high to enable ADC
    configGpio(0x41210000, 16, 2);
    configGpio(0x41210008, 16, 1000);
    configGpio(0x41220008, 16, 4);
    configGpio(0x41200000, 8, 1);
    configGpio(0x41200000, 8, 0);
    configGpio(0x41200008, 8, 1);

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
    int count = 0;
    while(count < 4)
    {
        read(axiDmaFd, buf, bufSize);
        printf("Buffer contents are:\n");
        int i;
        for (i = 0; i < (36); i++)
        {
            if (i % 9 == 0)
            {
                printf("buf[%d] = 0x%" PRIx64 "\n", i, buf[i]);
            }
        }
        count++;
    }

    printf("\n\n RESETTING \n\n");
    configGpio(0x41200008, 8, 0);
    configGpio(0x41200008, 8, 1);
    configGpio(0x41200000, 8, 1);
    configGpio(0x41200000, 8, 0);

    count = 0;
    while(count < 4)
    {
        read(axiDmaFd, buf, bufSize);
        printf("Buffer contents are:\n");
        int i;
        for (i = 0; i < (36); i++)
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
