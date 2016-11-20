/*
 * driver_interface_ipc.h
 *
 *  Created on: Nov 19, 2016
 *      Author: dominic
 */

#ifndef SRC_DRIVER_INTERFACE_IPC_H_
#define SRC_DRIVER_INTERFACE_IPC_H_

#include <string.h>
#include <sys/un.h>
#include <sys/socket.h>
#include <stdint.h>

class DriverInterfaceIPC
{
private:
    struct sockaddr_un remote;
    int socketFd;
public:
    DriverInterfaceIPC();
    void connectDriverInterface();
    void sendStop();
    uint64_t sendStart(uint64_t sampleRate);
};



#endif /* SRC_DRIVER_INTERFACE_IPC_H_ */
