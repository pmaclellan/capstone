#include <pthread.h>
#include <unistd.h>
#include <stdio.h>
#include "control_signals.pb.h"
#include "driver_interface_ipc.h"
#include "control_task.h"
#include "data_task.h"

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Create and connect to the driver interface
    DriverInterfaceIPC driverInterface;
    driverInterface.connectDriverInterface();

    // Create a control task and and start it
    printf("Starting control task\n");
    ControlTask controlTask(&driverInterface);
    controlTask.startControlTask();

    // Create a data task and start
    printf("Starting data task\n");
    DataTask dataTask;
    dataTask.startDataTask();

    // Stop the tasks. SHOULD NOT HAPPEN
    dataTask.stopDataTask();
    controlTask.stopControlTask();

    return 0;
}

