/*
 * data_task.cpp
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#include <cstdlib> // for exit... should probably get rid of this
#include <stdio.h>
#include <iostream>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <string.h>
#include <arpa/inet.h> // inet_ntoa
#include <unistd.h>
#include "data_task.h"

DataTask::DataTask():
    socketFd(-1),
    clientFd(-1),
    myThread(),
    NUM_PACKETS(24),
    LINES_PER_PACKET(9),
    MAX_SEND_SIZE(8000),
    DATA_PORT(10002),
    BACKLOG(5)
{
}

void DataTask::bindToSocket()
{
    // Create a socket
    if((this->socketFd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("Error in data socket creation");
        exit(1);
    }

    // set SO_REUSEADDR on a socket to true (1):
    int optval = 1;
    if(setsockopt(this->socketFd, SOL_SOCKET, SO_REUSEADDR, &optval,
            sizeof(int)) < 0)
    {
        perror("Error setting socket options in data task");
        exit(1);
    }

    memset(&this->server, 0, sizeof(this->server));
    memset(&this->dest, 0, sizeof(this->dest));
    this->server.sin_family = AF_INET;
    this->server.sin_port = htons(DATA_PORT);
    this->server.sin_addr.s_addr = INADDR_ANY;
    if(bind(this->socketFd, (struct sockaddr *) &this->server,
            sizeof(struct sockaddr)) < 0)
    {
        perror("Error binding data socket");
        exit(1);
    }
}

void DataTask::acceptDataConnection()
{
    socklen_t addressLength = sizeof(struct sockaddr);
    // Listen for data socket
    if(listen(this->socketFd, BACKLOG) < 0)
    {
        perror("Error in data task listen on socket");
        exit(1);
    }
    printf("Listening for data connection\n");
    if((this->clientFd = accept(this->socketFd, (struct sockaddr *) &this->dest,
            &addressLength)) < 0)
    {
        perror("Error in data task accept connection");
        exit(1);
    }
    printf("Server got connection from data client %s\n",
            inet_ntoa(dest.sin_addr));
}

void DataTask::readData()
{
    // Notes: The DMA will create a buffer that is 1.5 packets bigger than you
    // configure. This is a bug but we'll hack it here and disregard the last 2
    // packets.

    // Create a buffer to put our DMA data into:
    //      size = (NUM_PACKETS + 2) x (LINES_PER_PACKET) x (8 bytes / line)
    //      Note: Conceptually, a line is 8 bytes. However for the purposes of
    //      only sending active channels, the array of data is broken down into
    //      uint16_t
    uint64_t * buf;
    size_t readSize = (NUM_PACKETS + 2) * LINES_PER_PACKET * sizeof(uint64_t);
    size_t garbageSize = 2 * LINES_PER_PACKET * sizeof(uint64_t);

    buf = static_cast<uint64_t *>(malloc(readSize));

    // Open the DMA
    int axiDmaFd = open("/dev/axidma_RX", O_RDONLY);
    printf("Opened DMA driver...\n");

    // Assume connected to start
    bool connectionStatus = true;
    while(connectionStatus)
    {
        read(axiDmaFd, buf, readSize);
        if(send(this->clientFd, buf, readSize - garbageSize, 0) < 0)
        {
            printf("Error data client disconnected\n");
            connectionStatus = false;
        }
    }

    // Free malloced memory
    free(buf);
}

void DataTask::startDataTask()
{
    pthread_create(&this->myThread, NULL, DataTask::staticProcessDataTask, this);
}

void DataTask::stopDataTask()
{
    pthread_join(this->myThread, NULL);
}

void DataTask::closeDataTaskConnection()
{
    close(this->clientFd);
    close(this->socketFd);
}

void * DataTask::staticProcessDataTask(void * c)
{
    ((DataTask *) c)->processDataTask();
    return NULL;
}

void DataTask::processDataTask()
{
    while(1)
    {
        // Bind the socket
        this->bindToSocket();
        // Accept a connection
        this->acceptDataConnection();
        // Read some data
        this->readData();

        // If readData returns, we must have disconnected. Close the FDs and
        // try to reconnect.
        this->closeDataTaskConnection();
    }
}
