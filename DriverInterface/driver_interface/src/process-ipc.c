/*
 * process-ipc.c
 *
 *  Created on: Nov 13, 2016
 *      Author: dominic
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <inttypes.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include "axi-dma.h"

#define BILLION 1000000000L
#define DMA_TIMER_FREQ 0x5F5E100 // 100MHz
#define MAX_CONNECTIONS 5
#define SOCK_PATH "/tmp/controller.sock"

int setupConnection()
{
    int serverSock;
    int clientSock;
    int len;
    socklen_t t;
    struct sockaddr_un local;
    struct sockaddr_un remote;

    // Create the socket
    if ((serverSock = socket(AF_UNIX, SOCK_STREAM, 0)) == -1)
    {
        perror("Error creating controller socket");
        exit(1);
    }

    // Setup socket path
    local.sun_family = AF_UNIX;
    strcpy(local.sun_path, SOCK_PATH);
    unlink(local.sun_path);
    len = strlen(local.sun_path) + sizeof(local.sun_family);

    // Bind the socket
    if (bind(serverSock, (struct sockaddr *) &local, len) == -1)
    {
        perror("Error binding controller socket");
        exit(1);
    }

    // Listen for connections
    if (listen(serverSock, MAX_CONNECTIONS) == -1)
    {
        perror("Error listening for socket connections");
        exit(1);
    }

    printf("Waiting for a connection...\n");
    t = (socklen_t)sizeof(remote);
    if ((clientSock = accept(serverSock, (struct sockaddr *)&remote, &t))
            == -1)
    {
        perror("Error accepting socket connection");
        exit(1);
    }

    printf("Connected.\n");
    return clientSock;
}

uint64_t readFromServer(int clientSocket)
{
    int size;
    uint64_t retValue;

    size = recv(clientSocket, &retValue, sizeof(uint64_t), 0);

    if (size != sizeof(uint64_t))
    {
        perror("Error reading data from server.\n");
        exit(1);
    }

    printf("Received 0x%" PRIx64 "\n", retValue);

    return retValue;
}

void sendToServer(int clientSocket, uint64_t value)
{
    int size;

    printf("Sending 0x%" PRIX64 "\n", value);
    size = send(clientSocket, &value, sizeof(uint64_t), 0);
    if(size != sizeof(uint64_t))
    {
        perror("Error sending data to server.\n");
        exit(1);
    }
}

uint64_t processStartRequest(uint64_t buf)
{
    uint64_t retValue;
    struct timespec currentTime;

    // Get the current time
    clock_gettime(CLOCK_REALTIME, &currentTime);

    // Convert time to a uint64_t
    retValue = BILLION * currentTime.tv_sec + currentTime.tv_nsec;

    // Get the sample frequency from the request
    uint32_t sampleFreq = (uint32_t)(buf & 0xFFFFFFFF);

    // Sample frequency is in Hz... convert according to:
    // configValue = 100MHz / sampleFreq
    uint16_t configValue = (uint16_t)(DMA_TIMER_FREQ / sampleFreq);

    // Start the DMA
    printf("Configuring dma with 0x%04x\n", configValue);
    startDMA(configValue);

    // TODO: Await started status from DMA

    // Return the time
    return (uint64_t)retValue;
}

void processStopRequest()
{
    // Stop the DMA
    stopDMA();

    // TODO: Await stopped status from DMA
}









