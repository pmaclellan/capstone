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

#define CTRLPORT 10001
#define DATAPORT 10002
#define BACKLOG 5

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

int main()
{
    int fd, active_channels;
    const char * myfifo = "/tmp/dma-fifo";
    uint16_t deadhead, timestamp, buf;
    uint64_t adc0_channels[8];
    uint64_t adc1_channels[8];
    uint64_t adc2_channels[8];
    uint64_t adc3_channels[8];

    int data_port = 10002;
    
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

    size = sizeof(struct sockaddr_in);

    // Accept and connect to control socket
    if ((client_fd[0] = accept(socket_fd[0], (struct sockaddr *)&dest, &size)) < 0)
    {
	error("ERROR acception failure");
    }
    printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));

    // Send port number of streaming socket over control socket
    if (send(client_fd[0], &data_port, sizeof(data_port), 0) < 0)
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
	
    // Conect to client over data socket
    if ((client_fd[1] = accept(socket_fd[1], (struct sockaddr *)&dest, &size)) < 0) 
    {
        error("ERROR acception failure");
    }
    printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));
	
    // Open file descriptor to read DMA data
    fd = open(myfifo, O_RDONLY);
    while(1)
    {
        bool send_data = false;	// send_data set only when buffer reads 0xDEAD
	// Try to read 34 bytes of data (DEAD, timestamp, 32 channels)
	for(int i = 0; i < 34; i++)
    	{
	    read(fd, &buf, sizeof(buf));
	    // If read buffer is 0xDEAD, set sending flag to true
	    if (buf == 57005)
	    {
		send_data = true;
	    }
	    // Send the buffer to client as it is received
	    if (send_data)
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
    }
    close(fd);

    close(client_fd[0]);
    close(client_fd[1]);
    close(socket_fd[0]); 
    close(socket_fd[1]);
    return 0;
}
