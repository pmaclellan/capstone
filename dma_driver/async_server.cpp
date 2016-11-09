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
#include <iostream>
#include <pthread.h>

#define CTRLPORT 10001
#define BACKLOG 5

using namespace std;

int getBit(int n, int bitNum);
void error(const char *msg);
void *control_task(void *);
void *data_task(void *);

int client_fd, socket_fd;
int adc_channels[34];
int numChannels;

RequestWrapper request_wrapper = RequestWrapper();
StartRequest start_request = StartRequest();
StopRequest stop_request = StopRequest();
SampleRateRequest sample_rate_request = SampleRateRequest();
SensitivityRequest sensitivity_request = SensitivityRequest();

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    pthread_t threadA[3];
    
    for (int i = 0; i < 34; i++)
    {
	adc_channels[i] = 1;
    }
    
    struct sockaddr_in server;
    struct sockaddr_in dest;
    socklen_t size;
    int yes = 1;

    // Set up socket for data
    if ((socket_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    {
	error("ERROR socket failure");
    }
    if (setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) 
    {
	error("ERROR setsockopt");
    }
    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(CTRLPORT);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd, (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }

    // Listen for control socket
    if (listen(socket_fd, BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    int thread_num = 0;
    // While loop waiting for connection
    while (thread_num < 3)
    {
	if ((client_fd = accept(socket_fd, (struct sockaddr *)&dest, &size)) < 0)
	{
	    error("ERROR acception failure");
	}
	printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));

	// Give first, control connection to thread 0
	if (thread_num == 0)
	{
	    pthread_create(&threadA[thread_num], NULL, control_task, NULL);
	}
	// Give second, data connection to thread 1
	else if (thread_num == 1)
	{
	    pthread_create(&threadA[thread_num], NULL, data_task, NULL);
	}
	
	thread_num++;
    }

    for (int i = 0; i < 3; i++)
    {
	pthread_join(threadA[i], NULL);
    }

    close(client_fd);
    close(socket_fd);
    return 0;
}

void *control_task(void *dummy)
{
    cout << "Thread No: " << pthread_self() << endl;
    int data_port = 10001;
    std::string ackString;
    uint16_t ackSize;
    while(1)
    {
	// Read incoming message
	uint16_t messagesize = 0;
	int receive = recv(client_fd, &messagesize, sizeof(messagesize), 0);
	if (receive < 0)
	{
	    error("ERROR reading failure");
	}
	else if (receive == 0)
	{
	    continue;
	}
	printf("Received size=%d\n", messagesize);
	vector<char> buffer(messagesize);
	if (recv(client_fd, buffer.data(), buffer.size(), 0) < 0)
	{
	    error("ERROR reading failure");
	}
	if (request_wrapper.ParseFromArray(buffer.data(), buffer.size()) == false)
	{
	    throw exception();
	}
	printf("Received wrapper with sequence=%d\n", request_wrapper.sequence());
	// Complete functions based on which request was sent
	if (request_wrapper.has_start()) // Start Request
	{
	    start_request = request_wrapper.start();
	    printf("With port=%d and channels=%d\n", start_request.port(), start_request.channels());
	
	    // Parse active channels to find which are active and how many
	    numChannels = 0;
	    for (int i = 0; i < 32; i++)
	    {
		if (getBit(start_request.channels(), i) == 1)
		{
	    	    numChannels++;
	    	    adc_channels[i+2] = 1;
		}
		else
		{
	    	    adc_channels[i+2] = 0;
		}
	    }
	    printf("Number of channels=%d\n", numChannels);

	    // Send size of port number string over control socket
	    start_request.set_port(data_port);
	    request_wrapper.set_allocated_start(&start_request);
	    request_wrapper.SerializeToString(&ackString);
	    ackSize = strlen(ackString.c_str());
	    printf("size = %d\n", ackSize);
	    if (send(client_fd, &ackSize, sizeof(ackSize), 0) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd);
		return NULL;
	    }
	    // Send port number of streaming socket over control socket
	    printf("Sending port number %d\n", start_request.port());
	    if (send(client_fd, ackString.data(), strlen(ackString.c_str()), 0) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd);
		return NULL;
	    }
	}
	else if (request_wrapper.has_stop()) // Stop Request
	{
	    stop_request = request_wrapper.stop();
	    printf("With port=%d and channels=%d\n", stop_request.port(), stop_request.channels());
	}
	else if (request_wrapper.has_rate()) // Sample Rate Request
	{
	    sample_rate_request = request_wrapper.rate();
	    printf("With rate=%d\n", sample_rate_request.rate());
	}
	else if (request_wrapper.has_sens()) // Sensitivity Request
	{
	    sensitivity_request = request_wrapper.sens();
	}
    }
}

void *data_task(void *dummy)
{
    cout << "Thread No: " << pthread_self() << endl;
    const char * myfifo = "/tmp/dma-fifo";
    int fd;
    int counter = 0;
    uint16_t buf;
    while(1)
    {
        bool send_data = false;	// send_data set only when buffer reads 0xDEAD
	fd = open(myfifo, O_RDONLY);
	// Try to read 34 bytes of data (DEAD, timestamp, 32 channels)
	for(int i = 0; i < 34; i++)
    	{
	    read(fd, &buf, sizeof(buf));
	    // If read buffer is 0xDEAD, set sending flag to true
	    // Then check if 0xDEAD is at beginning of data segment
	    if (buf == 57005 && (counter % (numChannels+2) == 0))
	    {
		send_data = true;
	    }
	    // Send the buffer to client as it is received if adc channel is active
	    if (send_data && (adc_channels[i] == 1))
	    {
		printf("Sending: %d\n", buf);
	        if (send(client_fd, &buf, sizeof(buf), 0) < 0)
		{
		    fprintf(stderr, "Failure Sending Messages\n");
		    close(client_fd);
		    return NULL;
		}
		counter++;
	    }
	    // If sending flag is false, skip over buffer
	    else
	    {
		printf("skip\n");
	    }
	}
	close(fd);
	//counter++;
    }
    close(fd);
}

int getBit(int n, int bitNum)
{
    int mask = 1 << bitNum;
    int masked_n = n & mask;
    int bit = masked_n >> bitNum;
    return abs(bit);
}

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

