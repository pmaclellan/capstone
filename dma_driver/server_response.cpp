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

#define PORT1 10001
#define PORT2 10002
#define PORT3 10003
#define BACKLOG 5

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

int main()
{
    int fd, active_channels;
    char * myfifo = "/tmp/dma-fifo";
    uint16_t dead_head;
    uint16_t buf;
    uint64_t adc0_channels[8];
    uint16_t adc0_channel0, adc0_channel1, adc0_channel2, adc0_channel3;
    uint16_t adc0_channel4, adc0_channel5, adc0_channel6, adc0_channel7;
    uint16_t adc1_channel0, adc1_channel1, adc1_channel2, adc1_channel3;
    uint16_t adc1_channel4, adc1_channel5, adc1_channel6, adc1_channel7;
    uint16_t adc2_channel0, adc2_channel1, adc2_channel2, adc2_channel3;
    uint16_t adc2_channel4, adc2_channel5, adc2_channel6, adc2_channel7;
    uint16_t adc3_channel0, adc3_channel1, adc3_channel2, adc3_channel3;
    uint16_t adc4_channel4, adc3_channel5, adc3_channel6, adc3_channel7;
    
    for(int i = 0; i < 1000; i++)
    {
	fd = open(myfifo, O_RDONLY);
	read(fd, &buf, sizeof(buf));
	printf("Received: %d\n", buf);
    }

    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socket_fd[2], client_fd[2], num, n;
    socklen_t size;

    char buffer[256];
    char *buff;
    int yes = 1;

    if ((socket_fd[0] = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    {
	error("ERROR socket failure");
    }
    /*if ((socket_fd[1] = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    {
	error("ERROR socket failure");
    }*/

    if (setsockopt(socket_fd[0], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) 
    {
	error("ERROR setsockopt");
    }

    /*if (setsockopt(socket_fd[1], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) 
    {
	error("ERROR setsockopt");
    }*/

    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT1);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd[0], (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }

    /*memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT2);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd[1], (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }*/

    if (listen(socket_fd[0], BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    /*if (listen(socket_fd[1], BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }*/

    while(1) 
    {
        size = sizeof(struct sockaddr_in);  

        if ((client_fd[0] = accept(socket_fd[0], (struct sockaddr *)&dest, &size)) < 0) 
	{
	    error("ERROR acception failure");
        }
        printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));
	
	uint16_t mock_data = 0;
	buf = buf/1000;
        while(1) 
	{
	    // READ from linux pipe
	    /*fd = open(myfifo, O_RDONLY);
	    //n = read(fd, &dead_head, sizeof(dead_head));
	    //if (n < 0)
	    //{
		//error("ERROR reading from linux pipe");
	    //}
	    //else if (dead_head != 0xDEAD)
	    //{
		//error("ERROR did not receive DEAD header");
	    //}
	    //else
	    //{
		//buf = dead_head;
		n = read(fd, &buf, sizeof(buf));
	    	if (n < 0)
	    	{
		    error("ERROR reading from linux pipe");
	    	}
	    	else
	    	{
		    printf("Received from DMA: %lu\n", buf);
	 	}
	    //}
	    close(fd);*/
	    /*for (int i = 0; i < sizeof(dmaFifoPaths); i++)
	    {
		fd = open(dmaFifoPaths[i], O_RDONLY);
		read(fd, &buf, sizeof(buf));
		close(fd);
		
		adc0_channels[i] = buf;
	    }

	    uint16_t send_channels[active_channels];
	    for (int i = 0; i < active_channels; i++)
	    {
		if (adc0_channels[i] != NULL)
		{
		    send_channels[i] = adc0_channels[i];
		    int j = i;
		}
		else if (adc1_channels[i-j-1] != NULL)
		{
		    send_channels[i] = adc1_channels[i-j-1];
		    int j = i;
		}
		else if (adc2_channels[i-j-1] != NULL)
		{
		    send_channels[i] = adc2_channels[i-j-1];
		    int j = i;
		}
		else if (adc3_channels[i-j-1] != NULL)
		{
		    send_channels[i] = adc3_channels[i-j-1];
		}
	    }

	    n = write(client_fd, &send_channels, sizeof(send_channels));*/
	    //fd = open(dmaFifoPaths[0], O_REDONLY);
	    //read(fd, &buf, sizeof(buf));
	    //close(fd);
	
	    //adc0_channel0 = (buf & 0xFFFF000000000000) >> 48;

	    //n = write(client_fd, &buf, 8);
	    //if (n < 0)
	    //{
		//error("ERROR receiving error");
	    //}

	    // READ from pete's client
	    /*n = read(client_fd, buffer, 8);
	    if (n < 0)
	    {
		error("ERROR receiving error");
	    }
	    else if (n == 0)
	    {
		printf("Connection closed\n");
	    	break;
	    }
	    else
	    {
		buffer[n] = '\0';
		printf("Here is the message: %s\n", buffer);
	    }*/

	    if (send(client_fd[0], &buf, 2, 0) < 0)
	    // (write(client_fd, buffer, sizeof(&buffer)) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd[0]);
		break;
	    }
	    printf("Buffer: %d\n", buf);
	    //buf = (buf / 1000);
	    //printf("Mock data: %d\n", mock_data);
	    mock_data = (mock_data + 1) % 512;
	    //bzero(&buf, 256);
	}

	close(client_fd[0]);
    }
    close(socket_fd[0]); 
    close(socket_fd[1]);
    return 0;
}
