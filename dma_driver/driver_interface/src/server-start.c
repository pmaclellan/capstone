/*
 * server-start.c
 *
 *  Created on: Nov 12, 2016
 *      Author: dominic
 */

#include <stdint.h>
#include <unistd.h>
#include <inttypes.h>
#include <fcntl.h>

int serverStart()
{
    int sampleFrequency = -1;
    uint64_t command;

    // Open the communication pipe
    int server2ControlFd = open("/tmp/server2control", O_RDONLY);
    // Block here while we await a command
    if (read(server2ControlFd, &command, sizeof(uint64_t)))
    {
        // Successfully read something... lets check it

    }

    return sampleFrequency;
}

