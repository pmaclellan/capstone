/*
 * data_task.h
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#ifndef SRC_DATA_TASK_H_
#define SRC_DATA_TASK_H_

#include <stdint.h>
#include <sys/socket.h>

class DataTask
{
private:
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socketFd;

    // DMA Data Sizes
    // TODO: These are defined both in this server and in the driver_interface...
    // The server really should send these values to the interface for the driver
    // to configure the DMA
    static int NUM_PACKETS = 24;
    static int LINES_PER_PACKET = 9;
    static int MAX_SEND_SIZE = 8000;
    static int DATA_PORT = 10002;
    static int BACKLOG = 5;

    void bindToSocket();
    int acceptDataConnection();
    void readData(int clientFd);
public:
    DataTask();
    void * processDataTask(void *);
};

#endif /* SRC_DATA_TASK_H_ */
