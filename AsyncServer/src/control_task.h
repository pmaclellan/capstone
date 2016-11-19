/*
 * control_task.h
 *
 *  Created on: Nov 18, 2016
 *      Author: dominic
 */

#ifndef SRC_CONTROL_TASK_H_
#define SRC_CONTROL_TASK_H_

#include <stdint.h>
#include <sys/socket.h>

class ControlTask
{
private:
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socketFd;

    RequestWrapper requestWrapper;

    static int NUM_CHANNELS = 32;
    static int CONTROL_PORT = 10001;
    static int DATA_PORT = 10002;
    static int BACKLOG = 5;

    void bindToSocket();
    int acceptControlConnection();
    bool recvMessage(int clientFd);
    void processStart(int clientFd);
    void processStop(int clientFd);
    void processSens();
public:
    ControlTask();
    void * processControlTask(void *);
};


#endif /* SRC_CONTROL_TASK_H_ */
