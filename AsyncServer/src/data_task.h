/*
 * data_task.h
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#ifndef SRC_DATA_TASK_H_
#define SRC_DATA_TASK_H_

#include <pthread.h>
#include <stdint.h>
#include <netinet/in.h>
#include <sys/socket.h>

class DataTask
{
private:
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socketFd;
    int clientFd;

    pthread_t myThread;

    // DMA Data Sizes
    // TODO: These are defined both in this server and in the driver_interface...
    // The server really should send these values to the interface for the driver
    // to configure the DMA
    int NUM_PACKETS;
    int LINES_PER_PACKET;
    int MAX_SEND_SIZE;
    int DATA_PORT;
    int BACKLOG;

    void bindToSocket();
    void acceptDataConnection();
    void readData();

    static void * staticProcessDataTask(void * c);
    void processDataTask();
public:
    DataTask();
    void startDataTask();
    void stopDataTask();
    void closeDataTaskConnection();
};

#endif /* SRC_DATA_TASK_H_ */
