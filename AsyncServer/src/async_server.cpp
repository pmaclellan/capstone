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

    while(1)
    {

        // Create a control task and and start it
        ControlTask controlTask(&driverInterface);
        controlTask.startControlTask();

        // Create a data task and start
        DataTask dataTask;
        dataTask.startDataTask();

        while(1)
        {
            // Don't let the main process die
            sleep(1);
        }
    }

    return 0;
}

