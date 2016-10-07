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

#define PORT 10001
#define BACKLOG 5

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

int main()
{
    struct sockaddr_in server;
    struct sockaddr_in dest;
    int socket_fd, client_fd, num, n;
    socklen_t size;

    char buffer[256];
    char *buff;
    int yes = 1;

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
    server.sin_port = htons(PORT);
    server.sin_addr.s_addr = INADDR_ANY; 
    if (bind(socket_fd, (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)   
    { 
	error("ERROR binding failure");
    }

    if (listen(socket_fd, BACKLOG) < 0)
    {
	error("ERROR listening failure");
    }

    while(1) 
    {
        size = sizeof(struct sockaddr_in);  

        if ((client_fd = accept(socket_fd, (struct sockaddr *)&dest, &size)) < 0) 
	{
	    error("ERROR acception failure");
        }
        printf("Server got connection from client %s\n", inet_ntoa(dest.sin_addr));

        while(1) 
	{
/*
	    n = read(client_fd, buffer, 255);
	    if (n < 0)
	    {
	        printf("Error reading from socket\n");
	        break;
	    }
	    else if (n == 0)
	    {
		printf("Connection closed\n");
	    	break;
	    }
	    printf("Here is the message: %s\n", buffer);

	    bzero(buffer, 256);

	    if (send(client_fd, buffer, strlen(buffer), 0) < 0)
	    {
		fprintf(stderr, "Failure Sending Messages\n");
		close(client_fd);
		break;
	    }
	}
*/

            if ((num = recv(client_fd, buffer, 10240, 0)) < 0) 
	    {
		error("ERROR receiving error");
            }   
	
            else if (num == 0) 
	    {
            	printf("Connection closed\n");
            	break;
            }

	    else
	    {
	    	buffer[num] = '\0';
	    	printf("Client says: %s", buffer);
	    }

	    if (send(client_fd, buffer, strlen(buffer), 0) < 0)
	    {
	    	fprintf(stderr, "Failure Sending Messages\n");
	    	close(client_fd);
	    	break;
            }
	}

	close(client_fd);
    }
    close(socket_fd); 
    return 0;
}
