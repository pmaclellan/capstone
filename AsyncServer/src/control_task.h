/*
 * control_task.h
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#ifndef SRC_CONTROL_TASK_H_
#define SRC_CONTROL_TASK_H_

#include <pthread.h>
#include <stdint.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include "control_signals.pb.h"
#include "driver_interface_ipc.h"

class ControlTask
{
private:
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socketFd;
    int clientFd;
    pthread_t myThread;

    DriverInterfaceIPC * driverInterface;

    RequestWrapper requestWrapper;

    int NUM_CHANNELS;
    int CONTROL_PORT;
    int DATA_PORT;
    int BACKLOG;

    void bindToSocket();
    void acceptControlConnection();
    bool recvMessage();
    void processStart();
    void processStop();
    void processSens();

    void processControlTask();
    static void * staticProcessControlTask(void * c);

public:
    ControlTask(DriverInterfaceIPC * driverInterface);
    void startControlTask();
    void stopControlTask();
    void closeControlTaskConnection();
};


#endif /* SRC_CONTROL_TASK_H_ */
