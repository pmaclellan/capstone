#include <pthread.h>
#include <sys/socket.h>
#include "control_signals.pb.h"
#include "control_task.h"
#include "data_task.h"

#define SOCK_PATH "/tmp/controller.sock"

// DMA Data Sizes
// TODO: These are defined both in this server and in the driver_interface...
// The server really should send these values to the interface for the driver
// to configure the DMA
#define NUM_PACKETS         24       // 4 packets
#define LINES_PER_PACKET    9       // 1 header and 8 lines of data

void connect_to_controller();

RequestWrapper request_wrapper = RequestWrapper();
StartRequest start_request = StartRequest();
StopRequest stop_request = StopRequest();
SensitivityRequest sensitivity_request = SensitivityRequest();

int socket_control;

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Create a control thread and a data thread
    pthread_t controlThread;
    pthread_t dataThread;

    // Create a control task and a data task
    ControlTask controlTask;
    DataTask dataTask;

    // Give first, control connection to thread 0
    pthread_create(&controlThread, NULL, controlTask.processControlTask, NULL);

    // Give second, data connection to thread 1
    pthread_create(&dataThread, NULL, dataTask.processDataTask, NULL);


    pthread_join(controlThread, NULL);
    pthread_join(dataThread, NULL);

    return 0;
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

