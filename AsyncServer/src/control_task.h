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
    pthread_t myThread;

    DriverInterfaceIPC * driverInterface;

    RequestWrapper requestWrapper;

    int NUM_CHANNELS;
    int CONTROL_PORT;
    int DATA_PORT;
    int BACKLOG;

    void bindToSocket();
    int acceptControlConnection();
    bool recvMessage(int clientFd);
    void processStart(int clientFd);
    void processStop(int clientFd);
    void processSens();

    void processControlTask();
    static void * staticProcessControlTask(void * c);

public:
    ControlTask(DriverInterfaceIPC * driverInterface);
    void startControlTask();
    void stopControlTask();
};


#endif /* SRC_CONTROL_TASK_H_ */
