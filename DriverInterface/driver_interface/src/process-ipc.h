/*
 * process-ipc.h
 *
 *  Created on: Nov 13, 2016
 *      Author: dominic
 */

#ifndef SRC_PROCESS_IPC_H_
#define SRC_PROCESS_IPC_H_

int setupConnection();
uint64_t readFromServer(int clientSocket);
void sendToServer(int clientSocket, uint64_t value);
uint64_t processStartRequest(uint64_t buf);
void processStopRequest();

typedef enum
{
    CONNECTED,
    DISCONNECTED
} SERVER_STATUS;

extern SERVER_STATUS ServerStatus; // Global DMA status

#endif /* SRC_PROCESS_IPC_H_ */
