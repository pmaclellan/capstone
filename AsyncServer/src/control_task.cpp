/*
 * control_task.cpp
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#include <vector>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <netinet/in.h>
#include "control_task.h"
#include "control_signals.pb.h"

int adc_channels[32];

int getBit(int n, int bitNum);

void ControlTask::bindToSocket()
{
    // Create a socket
    if((this->socketFd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("Error in control socket creation");
        exit(1);
    }

    // set SO_REUSEADDR on a socket to true (1):
    int optval = 1;
    if(setsockopt(this->socketFd, SOL_SOCKET, SO_REUSEADDR, &optval,
            sizeof(int)) < 0)
    {
        perror("Error setting socket options in control task");
        exit(1);
    }

    memset(&this->server, 0, sizeof(this->server));
    memset(&this->dest, 0, sizeof(this->dest));
    this->server.sin_family = AF_INET;
    this->server.sin_port = htons(CONTROL_PORT);
    this->server.sin_addr.s_addr = INADDR_ANY;
    if(bind(this->socketFd, (struct sockaddr *) &this->server,
            sizeof(struct sockaddr)) < 0)
    {
        perror("Error binding control socket");
        exit(1);
    }
}

int ControlTask::acceptControlConnection()
{
    int clientFd;
    socklen_t addressLength = sizeof(struct sockaddr);
    // Listen for data socket
    if(listen(this->socketFd, BACKLOG) < 0)
    {
        perror("Error in control task listen on socket");
        exit(1);
    }
    printf("Listening for control connection\n");
    if((clientFd = accept(this->socketFd, (struct sockaddr *) &this->dest,
            &addressLength)) < 0)
    {
        perror("Error in control task accept connection");
        exit(1);
    }
    printf("Server got connection from control client %s\n",
            inet_ntoa(dest.sin_addr));

    return clientFd;
}

bool ControlTask::recvMessage(int clientFd)
{
    bool retValue = true;
    this->requestWrapper = RequestWrapper();
    // Read incoming message size
    uint16_t messageSize;
    int receive = recv(clientFd, &messageSize, sizeof(uint16_t), 0);
    if(receive < 0)
    {
        perror("Error receiving control message size");
        retValue = false;
    }
    else if(receive == 0)
    {
        printf("Error control task client disconnected\n");
        // Send stop to fifo
        uint64_t stopCode = 0x0000000100000000;
        send(socket_control, &stopCode, sizeof(uint64_t), 0);

        // Read ack from controller
        uint64_t ack;
        recv(socket_control, &ack, sizeof(uint64_t), 0);
    }

    std::vector<char> buffer(messageSize);

    // Now that we know the size, receive the message
    if(recv(clientFd, buffer.data(), buffer.size(), 0) < 0)
    {
        perror("Error receiving control message");
        retValue = false;
    }
    if(this->requestWrapper.ParseFromArray(buffer.data(), buffer.size()) == false)
    {
        perror("Error parsing from protobuf");
        retValue = false;
    }
    printf("Received wrapper with sequence #%d\n", this->requestWrapper.sequence());

    return retValue;
}

void ControlTask::processStart(int clientFd)
{
    StartRequest startRequest = this->requestWrapper.start();
    std::string ackString;
    uint16_t ackSize;
    printf("Processing start request with port=%d and channels=%d\n",
            startRequest.port(), startRequest.channels());

    // Parse active channels to find which are active and how many
    for(int i = 0; i < NUM_CHANNELS; i++)
    {
        if(getBit(startRequest.channels(), i) == 1)
        {
            adc_channels[i] = 1;
        }
        else
        {
            adc_channels[i] = 0;
        }
    }

    // Send sample rate to controller
    // Start code is 0, so leave the upper 32 bits as 0
    uint64_t sampleRate = static_cast<uint64_t>(startRequest.rate());
    send(socket_control, &sampleRate, sizeof(uint64_t), 0);

    // Read timestamp from controller
    uint64_t timestamp;
    recv(socket_control, &timestamp, sizeof(uint64_t), 0);
    startRequest.set_timestamp(timestamp);

    // Send size of port number string over control socket
    startRequest.set_port(DATA_PORT);
    this->requestWrapper.set_allocated_start(&startRequest);
    this->requestWrapper.SerializeToString(&ackString);
    ackSize = strlen(ackString.c_str());
    // Send the ack size to the client
    printf("Control task sending ack size to controller\n");
    if(send(clientFd, &ackSize, sizeof(ackSize), 0) < 0)
    {
        perror("Error sending start request ack size in control task\n");
        close(clientFd);
    }
    // Send port number of streaming socket over control socket
    printf("Control task sending port number %d\n", startRequest.port());
    if(send(clientFd, ackString.data(), strlen(ackString.c_str()), 0) < 0)
    {
        perror("Error sending start request ack in control task");
        close(clientFd);
    }

    this->requestWrapper.release_start();
}

void ControlTask::processStop(int clientFd)
{
    StopRequest stopRequest = this->requestWrapper.stop();
    std::string ackString;
    uint16_t ackSize;
    printf("Process stop request in control task\n");

    // Send stop to dma controller
    uint64_t stopCode = 0x0000000100000000;
    send(socket_control, &stopCode, sizeof(uint64_t), 0);

    // Read ack from controller
    uint64_t ack;
    recv(socket_control, &ack, sizeof(uint64_t), 0);

    // Send ack back to client
    this->requestWrapper.SerializeToString(&ackString);
    ackSize = strlen(ackString.c_str());
    printf("Sending ack size to client\n");
    if(send(clientFd, &ackSize, sizeof(ackSize), 0) < 0)
    {
        perror("Error sending stop request ack size to client in control task\n");
        close(clientFd);
    }
    printf("Sending stop\n");
    if(send(clientFd, ackString.data(), strlen(ackString.c_str()), 0) < 0)
    {
        perror("Sending stop request ack to client\n");
        close(clientFd);
    }

    this->requestWrapper.release_stop();
}

void ControlTask::processSens()
{
    SensitivityRequest sensitivityRequest = this->requestWrapper.sens();


    this->requestWrapper.release_sens();
}

void * ControlTask::processControlTask(void *)
{
    // Bind to the socket
    this->bindToSocket();
    // connect to the controller
    connect_to_controller();
    // Accept the connection
    int clientFd = this->acceptControlConnection();
    // Read messages
    while(this->recvMessage(clientFd))
    {
        // Process the message
        if(this->requestWrapper.has_start())
        {
            this->processStart(clientFd);
        }
        else if(this->requestWrapper.has_stop())
        {
            this->processStop(clientFd);
        }
        else if(this->requestWrapper.has_sens())
        {
            this->processSens();
        }
    }

    return NULL;
}

int getBit(int n, int bitNum)
{
    int mask = 1 << bitNum;
    int masked_n = n & mask;
    int bit = masked_n >> bitNum;
    return abs(bit);
}
