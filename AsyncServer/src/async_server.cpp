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
#include <iostream>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <inttypes.h>

#include "control_signals.pb.h"

#define CTRLPORT 10001
#define DATAPORT 10002
#define BACKLOG 5
#define SOCK_PATH "/tmp/controller.sock"
#define NUM_CHANNELS 32
#define MAX_SEND_SIZE 8000

// DMA Data Sizes
// TODO: These are defined both in this server and in the driver_interface...
// The server really should send these values to the interface for the driver
// to configure the DMA
#define NUM_PACKETS         24       // 4 packets
#define LINES_PER_PACKET    9       // 1 header and 8 lines of data

using namespace std;

int getBit(int n, int bitNum);
void error(const char *msg);
void *control_task(void *);
void *data_task(void *);
void connect_to_controller();

int client_fd[2], socket_fd[2], socket_control;
int adc_channels[NUM_CHANNELS+4];
int numChannels;
bool read_data;

RequestWrapper request_wrapper = RequestWrapper();
StartRequest start_request = StartRequest();
StopRequest stop_request = StopRequest();
SensitivityRequest sensitivity_request = SensitivityRequest();

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    struct sockaddr_in server, dest;

    // Server allows 3 separate pairs of control/data connections
    pthread_t threadA[3];

    for(int i = 0; i < NUM_CHANNELS+4; i++)
    {
        adc_channels[i] = 1;
    }

    // Give first, control connection to thread 0
    pthread_create(&threadA[0], NULL, control_task, NULL);

    // Give second, data connection to thread 1
    pthread_create(&threadA[1], NULL, data_task, NULL);

    for(int i = 0; i < 3; i++)
    {
        pthread_join(threadA[i], NULL);
    }

    close(client_fd[0]);
    close(client_fd[1]);
    close(socket_fd[0]);
    close(socket_fd[1]);
    return 0;
}

void *control_task(void *)
{
    int yes = 1;
    struct sockaddr_in server, dest;
    socklen_t size;

    // Set up socket 0 for control data
    if((socket_fd[0] = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        error("ERROR socket failure");
    }
    if(setsockopt(socket_fd[0], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0)
    {
        error("ERROR setsockopt");
    }
    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(CTRLPORT);
    server.sin_addr.s_addr = INADDR_ANY;
    if(bind(socket_fd[0], (struct sockaddr *) &server, sizeof(struct sockaddr)) < 0)
    {
        error("ERROR binding failure");
    }

    //connect_to_controller();
    int data_port = 10002;
    std::string ackString;
    uint16_t ackSize;

    while(1)
    {
        // Listen for control socket
        if(listen(socket_fd[0], BACKLOG) < 0)
        {
            error("ERROR listening failure");
        }
        printf("Listening for control connection\n");
        if((client_fd[0] = accept(socket_fd[0], (struct sockaddr *) &dest, &size)) < 0)
        {
            error("ERROR acception failure");
        }
        printf("Server got connection from control client %s\n", inet_ntoa(dest.sin_addr));

        while(1)
        {
            // Read incoming message
            uint16_t messagesize;
            int receive = recv(client_fd[0], &messagesize, sizeof(messagesize), 0);
            if(receive < 0)
            {
                error("ERROR reading failure");
            }
            else if(receive == 0)
            {
                printf("ERROR control client disconnected\n");
                // Send stop to fifo
                uint64_t code = 0x0000000100000000;
                send(socket_control, &code, sizeof(uint64_t), 0);

                // Read ack from controller
                uint64_t buff;
                recv(socket_control, &buff, sizeof(buff), 0);
                break;
            }
            vector<char> buffer(messagesize);
            if(recv(client_fd[0], buffer.data(), buffer.size(), 0) < 0)
            {
                error("ERROR reading failure");
            }
            if(request_wrapper.ParseFromArray(buffer.data(), buffer.size()) == false)
            {
                throw exception();
            }
            printf("Received wrapper with sequence #%d\n", request_wrapper.sequence());

            // Complete functions based on which request was sent
            if(request_wrapper.has_start()) // Start Request
            {
                printf("Start Request\n");
                start_request = request_wrapper.start();
                //printf("With port=%d and channels=%d\n", start_request.port(), start_request.channels());

                // Parse active channels to find which are active and how many
                numChannels = 0;
                for(int i = 0; i < NUM_CHANNELS; i++)
                {
                    if(getBit(start_request.channels(), i) == 1)
                    {
                        numChannels++;
                        adc_channels[i+4] = 1;
                    }
                    else
                    {
                        adc_channels[i+4] = 0;
                    }
                }
                /*printf("Active channels: ");
                for(int i = 0; i < 36; i++)
                {
                    cout<<adc_channels[i]; 
                }*/

                // Send sample rate to controller
                uint64_t code = 0;
                uint64_t sample_rate = static_cast<uint64_t>(start_request.rate());
                uint64_t sr_and_code = sample_rate;
                send(socket_control, &sr_and_code, sizeof(sr_and_code), 0);

                // Read timestamp from controller
                uint64_t buff;
                recv(socket_control, &buff, sizeof(buff), 0);
                start_request.set_timestamp(buff);
                //printf("Sending timestamp %lu\n", request_wrapper.start().timestamp());
                
                // Send size of port number string over control socket
                start_request.set_port(data_port);
                request_wrapper.set_allocated_start(&start_request);
                request_wrapper.SerializeToString(&ackString);
                ackSize = strlen(ackString.c_str());
                if(send(client_fd[0], &ackSize, sizeof(ackSize), 0) < 0)
                {
                    fprintf(stderr, "Failure Sending Messages\n");
                    close(client_fd[0]);
                    return NULL;
                }
                // Send port number of streaming socket over control socket
                if(send(client_fd[0], ackString.data(), strlen(ackString.c_str()), 0) < 0)
                {
                    fprintf(stderr, "Failure Sending Messages\n");
                    close(client_fd[0]);
                    return NULL;
                }

                request_wrapper.release_start();

                read_data = true;
            }
            
            else if(request_wrapper.has_stop()) // Stop Request
            {
                printf("Stop Request\n");
                stop_request = request_wrapper.stop();
                read_data = false;

                // Send stop to fifo
                uint64_t code = 0x0000000100000000;
                send(socket_control, &code, sizeof(uint64_t), 0);

                // Read ack from controller
                uint64_t buff;
                recv(socket_control, &buff, sizeof(buff), 0);

                if(buff == 1)
                {
                    // Send ACK back to client
                    request_wrapper.SerializeToString(&ackString);
                    ackSize = strlen(ackString.c_str());
                    if(send(client_fd[0], &ackSize, sizeof(ackSize), 0) < 0)
                    {
                        fprintf(stderr, "Failure Sending Messages\n");
                        close(client_fd[0]);
                        return NULL;
                    }
                    //printf("Sending stop\n");
                    if(send(client_fd[0], ackString.data(), strlen(ackString.c_str()), 0) < 0)
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

            else if(request_wrapper.has_sens()) // Sensitivity Request
            {
                sensitivity_request = request_wrapper.sens();

                request_wrapper.release_sens();
            }
        }
    }
}

void *data_task(void *)
{
    int yes = 1;
    struct sockaddr_in server, dest;
    socklen_t size;

    // Set up socket 1 for signal data
    if((socket_fd[1] = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        error("ERROR socket failure");
    }
    if(setsockopt(socket_fd[1], SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0)
    {
        error("ERROR setsockopt");
    }
    memset(&server, 0, sizeof(server));
    memset(&dest, 0, sizeof(dest));
    server.sin_family = AF_INET;
    server.sin_port = htons(DATAPORT);
    server.sin_addr.s_addr = INADDR_ANY;
    if(bind(socket_fd[1], (struct sockaddr *) &server, sizeof(struct sockaddr)) < 0)
    {
        error("ERROR binding failure");
    }

    // Notes: The DMA will create a buffer that is 1.5 packets bigger than you
    // configure. This is a bug but we'll hack it here and disregard the last 2
    // packets.

    // Create a buffer to put our DMA data into:
    //      size = (NUM_PACKETS + 2) x (LINES_PER_PACKET) x (8 bytes / line)
    //      Note: Conceptually, a line is 8 bytes. However for the purposes of
    //      only sending active channels, the array of data is broken down into
    //      uint16_t
    uint64_t * readBuf;
    uint64_t * sendBuf;
    size_t readSize = (NUM_PACKETS + 2) * LINES_PER_PACKET * sizeof(uint64_t);
    size_t readFrameSize = NUM_PACKETS * LINES_PER_PACKET * sizeof(uint64_t);

    // Send size should be as many frames as we can up to the max send size
    int framesToSend = MAX_SEND_SIZE / readFrameSize;

    size_t sendSize = framesToSend * readFrameSize;

    readBuf = static_cast<uint64_t *>(malloc(readSize));
    sendBuf = static_cast<uint64_t *>(malloc(sendSize));

    // Open the DMA
    int axiDmaFd = open("/dev/axidma_RX", O_RDONLY);
    printf("Opened DMA driver...\n");
    int sendcheck;
    bool connection_status;
    while(1)
    {
        // Listen for data socket
        if(listen(socket_fd[1], BACKLOG) < 0)
        {
            error("ERROR listening failure");
        }
        printf("Listening for data connection\n");
        if((client_fd[1] = accept(socket_fd[1], (struct sockaddr *) &dest, &size)) < 0)
        {
            error("ERROR acception failure");
        }
        printf("Server got connection from data client %s\n", inet_ntoa(dest.sin_addr));
        connection_status = true;

        bool sendFrame = false;
        size_t sendFrameCurrentSize = 0;
        uint64_t * sendFramePosition = sendBuf;
        while(1)
        {
            if(sendFrame)
            {
                // Send the data
                if(send(client_fd[1], sendBuf, sendSize, 0) < 0)
                {
                    printf("ERROR data client disconnected\n");
                    // Send stop to fifo
                    uint64_t code = 0x0000000100000000;
                    send(socket_control, &code, sizeof(uint64_t), 0);

                    // Read ack from controller
                    uint64_t buff;
                    recv(socket_control, &buff, sizeof(buff), 0);

                    connection_status = false;
                }
                sendFramePosition = sendBuf; // Reset our position back to the
                                             // beginning of the send frame
            }
            else
            {
                // Keep building the send buffer
                read(axiDmaFd, sendFramePosition, readFrameSize);
                sendFrameCurrentSize += readFrameSize;
                sendFramePosition += (readFrameSize / 2);
                if(sendFrameCurrentSize == sendSize)
                {
                    sendFrame = true;
                }
            }

            if(!connection_status)
            {
                break;
            }
        }
    }

    free (sendBuf);
    close(axiDmaFd);
}

void connect_to_controller()
{
    int len;
    struct sockaddr_un remote;
    if((socket_control = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
    {
        perror("socket");
        exit(1);
    }
    printf("Trying to connect...\n");

    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, SOCK_PATH);
    len = strlen(remote.sun_path) + sizeof(remote.sun_family);
    if(connect(socket_control, (struct sockaddr *) &remote, len) < 0)
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
