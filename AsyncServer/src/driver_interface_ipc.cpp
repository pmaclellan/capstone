/*
 * driver_interface_ipc.cpp
 *
 *  Created on: Nov 19, 2016
 *      Author: dominic
 */

#include <cstdlib> // for exit... should probably get rid of this
#include <stdio.h>
#include <sys/socket.h>
#include "driver_interface_ipc.h"

DriverInterfaceIPC::DriverInterfaceIPC() :
        remote(), socketFd(-1)
{

}

void DriverInterfaceIPC::connectDriverInterface()
{
    int len;
    if((this->socketFd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
    {
        perror("Error creating the driver interface socket");
        exit(1);
    }

    printf("Trying to connect to driver interface socket...\n");

    this->remote.sun_family = AF_UNIX;
    strcpy(this->remote.sun_path, "/tmp/controller.sock");
    len = strlen(this->remote.sun_path) + sizeof(this->remote.sun_family);
    if(connect(this->socketFd, (struct sockaddr *) &this->remote, len) < 0)
    {
        perror("Error connecting to the driver interface socket");
        exit(1);
    }
    printf("Connected to driver interface socket\n");
}

void DriverInterfaceIPC::sendStop()
{
    // Send stop to fifo
    uint64_t stopCode = 0x0000000100000000;
    send(this->socketFd, &stopCode, sizeof(uint64_t), 0);

    // Read ack from controller
    uint64_t ack;
    recv(this->socketFd, &ack, sizeof(uint64_t), 0);
}

// Takes the sample rate and returns a timestamp
uint64_t DriverInterfaceIPC::sendStart(uint64_t sampleRate)
{
    // Start code is 0, so leave the upper 32 bits as 0
    send(this->socketFd, &sampleRate, sizeof(uint64_t), 0);

    // Read timestamp from controller
    uint64_t time;
    recv(this->socketFd, &time, sizeof(uint64_t), 0);

    return time;
}
