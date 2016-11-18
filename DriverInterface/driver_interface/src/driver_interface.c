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
    int clientSock = -1;
    uint64_t currentTime;
    uint64_t buf;

    // DMA is initially unused
    DmaStatus = UNUSED;
    initDMA(); // Set DMA config values
    // DMA is configured
    DmaStatus = EMBRYO;

    // Connect to the server
    while(clientSock < 0)
    {
        clientSock = setupConnection();
    }

    while (1)
    {
        buf = readFromServer(clientSock);

        if (ServerStatus == CONNECTED)
        {
            if (((buf >> 32) == 0) && (DmaStatus == EMBRYO))
            {
                // This is a start request
                currentTime = processStartRequest(buf);
                // Send the current time to the server
                sendToServer(clientSock, currentTime);
                // Set the status as running
                DmaStatus = RUNNING;
            }
            else if (((buf >> 32) == 1) && (DmaStatus == RUNNING))
            {
                // This is a stop request
                processStopRequest();
                // Send stopped message to server
                sendToServer(clientSock, 0x0000000000000001); // 1 = ACK
                // Set the status as EMBRYO again
                DmaStatus = EMBRYO;
            }
        }
        else
        {
            // Server disconnected... reconnect
            clientSock = -1;
            while (clientSock < 0)
            {
                clientSock = setupConnection();
            }
            DmaStatus = EMBRYO;
        }
    }

    close(clientSock);
    return 0;
}


