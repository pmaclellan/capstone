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
#include <sys/socket.h>
#include "axi-dma.h"
#include "process-ipc.h"

// Function prototypes
void initDMA();

int main(void)
{
    int clientSock;
    uint64_t currentTime;
    uint64_t buf;

    // DMA is initially unused
    Status = UNUSED;
    initDMA(); // Set DMA config values
    // DMA is configured
    Status = EMBRYO;

    // Connect to the server
    clientSock = setupConnection();

    while (1)
    {
        buf = readFromServer(clientSock);

        if (((buf >> 32) == 0) && (Status == EMBRYO))
        {
            // This is a start request
            currentTime = processStartRequest(buf);
            // Send the current time to the server
            sendToServer(clientSock, currentTime);
            // Set the status as running
            Status = RUNNING;
        }
        else if (((buf >> 32) == 1) && (Status == RUNNING))
        {
            // This is a stop request
            processStopRequest();
            // Send stopped message to server
            sendToServer(clientSock, 0x0000000000000001); // 1 = ACK
            // Set the status as EMBRYO again
            Status = EMBRYO;
        }
    }

    close(clientSock);
    return 0;
}


