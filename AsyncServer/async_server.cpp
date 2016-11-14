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
#include <sys/stat.h>
#include <sys/un.h>

#define CTRLPORT 10001
#define DATAPORT 10002
#define BACKLOG 5
#define SOCK_PATH "/tmp/controller.sock"

using namespace std;

int getBit(int n, int bitNum);
void error(const char *msg);
void *control_task(void *);
void *data_task(void *);
void connect_to_controller();

int client_fd[2], socket_fd[2], socket_control;
int adc_channels[34];
int numChannels;
bool read_data;

RequestWrapper request_wrapper = RequestWrapper();
StartRequest start_request = StartRequest();
StopRequest stop_request = StopRequest();
SensitivityRequest sensitivity_request = SensitivityRequest();

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Server allows 3 separate pairs of control/data connections
    pthread_t threadA[3];
    
    for (int i = 0; i < 34; i++)
    {
	adc_channels[i] = 1;
    }
    
    struct sockaddr_in server;
    struct sockaddr_in dest;
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
    // Set up socket 1 for signal data
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
    // Listen for data socket
    if (listen(socket_fd[1], BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    int thread_num = 0;
    // While loop waiting for connection
    while (thread_num < 3)
    {
	printf("Listening for control connection\n");
	if ((client_fd[0] = accept(socket_fd[0], (struct sockaddr *)&dest, &size)) < 0)
	{
	    error("ERROR acception failure");
	}
	printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));

	// Give first, control connection to thread 0
	pthread_create(&threadA[thread_num], NULL, control_task, NULL);
	
	printf("Listening for data connection\n");
	if ((client_fd[1] = accept(socket_fd[1], (struct sockaddr *)&dest, &size)) < 0)
	{
	    error("ERROR acception failure");
	}
	printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));
	
	// Give second, data connection to thread 1
	pthread_create(&threadA[thread_num], NULL, data_task, NULL);
	
	thread_num++;
    }

    for (int i = 0; i < 3; i++)
    {
	pthread_join(threadA[i], NULL);
    }

    close(client_fd[0]);
    close(client_fd[1]);
    close(socket_fd[0]);
    close(socket_fd[1]);
    return 0;
}

void *control_task(void *dummy)
{
    connect_to_controller();
    int data_port = 10002;
    std::string ackString;
    uint16_t ackSize;

    while(1)
    {
	// Read incoming message
	uint16_t messagesize;
	int receive = recv(client_fd[0], &messagesize, sizeof(messagesize), 0);
	if (receive < 0)
	{
	    error("ERROR reading failure");
	}
	else if (receive == 0)
	{
	    continue;
	}
	vector<char> buffer(messagesize);
	if (recv(client_fd[0], buffer.data(), buffer.size(), 0) < 0)
	{
	    error("ERROR reading failure");
	}
	if (request_wrapper.ParseFromArray(buffer.data(), buffer.size()) == false)
	{
	    throw exception();
	}
	printf("Received wrapper with sequence #%d\n", request_wrapper.sequence());

	// Complete functions based on which request was sent
	if (request_wrapper.has_start()) // Start Request
	{
	    printf("Start Request\n");
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

	    // Send sample rate to controller
	    uint32_t code = 0;
	    uint32_t sample_rate = start_request.rate();
	    uint64_t sr_and_code = code<<32 + sample_rate;
	    send(socket_control, &sr_and_code, sizeof(sr_and_code), 0);
	    
	    // Read timestamp from controller
	    uint64_t buff;
	    recv(socket_control, &buff, sizeof(buff), 0);
	    start_request.set_timestamp(buff);

	    // Send size of port number string over control socket
	    start_request.set_port(data_port);
	    request_wrapper.set_allocated_start(&start_request);
	    request_wrapper.SerializeToString(&ackString);
	    ackSize = strlen(ackString.c_str());
	    if (send(client_fd[0], &ackSize, sizeof(ackSize), 0) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd[0]);
		return NULL;
	    }
	    // Send port number of streaming socket over control socket
	    printf("Sending port number %d\n", start_request.port());
	    if (send(client_fd[0], ackString.data(), strlen(ackString.c_str()), 0) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd[0]);
		return NULL;
	    }
	    
	    request_wrapper.release_start();

	    read_data = true;
	}
	else if (request_wrapper.has_stop()) // Stop Request
	{
	    printf("Stop Request\n");
	    stop_request = request_wrapper.stop();
	    read_data = false;

	    // Send stop to fifo
	    uint32_t code = 1;
	    uint32_t sample_rate = start_request.rate();
	    uint64_t stop = code<<32 + sample_rate;
	    send(socket_control, &stop, sizeof(stop), 0);

	    // Read ack from controller
	    uint64_t buff;
	    recv(socket_control, &buff, sizeof(buff), 0);
	    
	    if (buff == 1)
	    {
		// Send ACK back to client
		request_wrapper.SerializeToString(&ackString);
	        ackSize = strlen(ackString.c_str());
	        if (send(client_fd[0], &ackSize, sizeof(ackSize), 0) < 0)
	        {
		    fprintf(stderr, "Failure Sending Messages\n");
		    close(client_fd[0]);
		    return NULL;
	    	}
	    }
	    else 
	    {
		// Do something
	    }

	    request_wrapper.release_stop();
	}
	else if (request_wrapper.has_sens()) // Sensitivity Request
	{
	    sensitivity_request = request_wrapper.sens();

	    request_wrapper.release_sens();
	}
    }
}

void *data_task(void *dummy)
{
    const char * myfifo = "/tmp/dma-fifo";
    int fd;
    int counter = 0;
    uint16_t buf;
    while(1)
    {
        bool send_data = false;	// send_data set only when buffer reads 0xDEAD
	fd = open(myfifo, O_RDONLY);
	if (read_data)
	{
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
	            if (send(client_fd[1], &buf, sizeof(buf), 0) < 0)
		    {
		    	fprintf(stderr, "Failure Sending Messages\n");
		    	close(client_fd[1]);
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
	}
    }
}

void connect_to_controller()
{
    int len;
    struct sockaddr_un remote;
    if ((socket_control = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
    {
	perror("socket");
	exit(1);
    }
    printf("Trying to connect...\n");

    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, SOCK_PATH);
    len = strlen(remote.sun_path) + sizeof(remote.sun_family);
    if (connect(socket_control, (struct sockaddr *)&remote, len) < 0)
    {
	perror("connect");
	exit(1);
    }
    printf("Connected\n");
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

