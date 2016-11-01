#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include "control_signals.pb.h"
#include <google/protobuf/text_format.h>
#include <google/protobuf/message_lite.h>
#include <iostream>

#define CTRLPORT 10001
#define DATAPORT 10002
#define BACKLOG 5

using namespace std;

int getBit(int n, int bitNum);
void error(const char *msg);

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    StartRequest start_request = StartRequest();

    int fd;
    const char * myfifo = "/tmp/dma-fifo";
    uint16_t deadhead, timestamp, buf;
    uint64_t adc0_channels[8];
    uint64_t adc1_channels[8];
    uint64_t adc2_channels[8];
    uint64_t adc3_channels[8];
    int adc_channels[34];
    for (int i = 0; i < 34; i++)
    {
	adc_channels[i] = 1;
    }

    int data_port = 10002;
    //std::string start;
    std::string ackString;
    uint16_t ackSize;
    uint32_t active_channels;
    
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socket_fd[2], client_fd[2];
    socklen_t size;

    int yes = 1;

    // Set up socket 0 for control data
    if ((socket_fd[0] = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    {
	error("ERROR socket failure");
    }
    if (setsockopt(socket_fd[0], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) 
    {
	error("ERROR setsockopt");
    }
    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(CTRLPORT);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd[0], (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }

    // Set up socket 1 for streaming data
    if ((socket_fd[1] = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    {
	error("ERROR socket failure");
    }
    if (setsockopt(socket_fd[1], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) 
    {
	error("ERROR setsockopt");
    }
    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(DATAPORT);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd[1], (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }

    // Listen for control socket
    if (listen(socket_fd[0], BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    struct sockaddr_in sin;
    size = sizeof(sin);

    // Accept and connect to control socket
    if ((client_fd[0] = accept(socket_fd[0], (struct sockaddr *)&dest, &size)) < 0)
    {
	error("ERROR acception failure");
    }
    printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));

    // Read size of incoming message
    uint16_t messagesize;
    if (recv(client_fd[0], &messagesize, sizeof(messagesize), 0) < 0)
    {
	error("ERROR reading failure");
    }

    // Read start request - port number, active channels
    vector<char> start(messagesize);
    if (recv(client_fd[0], start.data(), start.size(), 0) < 0)
    {
	error("ERROR reading failure");
    }
    if (start_request.ParseFromArray(start.data(), start.size()) == false)
    {
	error("ERROR parsing failure");
    }
    printf("Received start request with port=%d and channels=%d\n", start_request.port(), start_request.channels());

    // Parse active channels to find which are active and how many
    int numChannels = 32; //*** =0 ***//
/*    for (int i = 2; i < 34; i++)
    {
	if (getBit(start_request.channels(), i) == 1)
	{
	    numChannels++;
	    adc_channels[i] = 1;
	}
	else
	{
	    adc_channels[i] = 0;
	}
    }*/

    // Send size of port number string over control socket
    start_request.set_port(data_port);
    start_request.SerializeToString(&ackString);
    ackSize = strlen(ackString.c_str());
    if (send(client_fd[0], &ackSize, sizeof(ackSize), 0) < 0)
    {
	fprintf(stderr, "Failure Sending Messages\n");
	close(client_fd[0]);
	return -1;
    }

    // Send port number of streaming socket over control socket
    printf("Sending port number %d\n", start_request.port());
    if (send(client_fd[0], ackString.data(), strlen(ackString.c_str()), 0) < 0)
    {
	fprintf(stderr, "Failure Sending Messages\n");
	close(client_fd[0]);
	return -1;
    }

    // Listen on data socket for client to connect
    if (listen(socket_fd[1], BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    size = sizeof(struct sockaddr_in);  

    // Connect to client over data socket
    if ((client_fd[1] = accept(socket_fd[1], (struct sockaddr *)&dest, &size)) < 0) 
    {
        error("ERROR acception failure");
    }
    printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));
	
    // Open file descriptor to read DMA data
    fd = open(myfifo, O_RDONLY);
    int counter = 0;
    while(1)
    {
        bool send_data = false;	// send_data set only when buffer reads 0xDEAD
	// Try to read 34 bytes of data (DEAD, timestamp, 32 channels)
	for(int i = 0; i < 34; i++)
    	{
	    read(fd, &buf, sizeof(buf));
	    // If read buffer is 0xDEAD, set sending flag to true
	    // Then check if 0xDEAD is at beginning of data segment
	    if ((buf == 57005) && (counter % numChannels == 0))
	    {
		send_data = true;
	    }
	    // Send the buffer to client as it is received if adc channel is active
	    if (send_data && (adc_channels[i] == 1))
	    {
		printf("Sending: %d\n", buf);
	        send(client_fd[1], &buf, sizeof(buf), 0);
	    }
	    // If sending flag is false, skip over buffer
	    else
	    {
		break;
	    }
	}
	counter++;
    }
    close(fd);

    close(client_fd[0]);
    close(client_fd[1]);
    close(socket_fd[0]); 
    close(socket_fd[1]);
    return 0;
}

int getBit(int n, int bitNum)
{
    int mask = 1 << bitNum;
    int masked_n = n & mask;
    int bit = masked_n >> bitNum;
    return bit;
}

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

