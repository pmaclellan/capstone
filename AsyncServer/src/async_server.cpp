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
        bool stopFlag = false;

        // Create a control task and and start it
        ControlTask controlTask(&stopFlag, &driverInterface);
        controlTask.startControlTask();

        // Create a data task and start
        DataTask dataTask(&stopFlag);
        dataTask.startDataTask();

        while(1)
        {
            if (stopFlag)
            {
                printf("Processing stop flag\n");
                // close the ports
                controlTask.closeControlTaskConnection();
                dataTask.closeDataTaskConnection();

                // join the threads
                controlTask.stopControlTask();
                dataTask.stopDataTask();
                break;
            }
            else
            {
                sleep(1);
            }
        }
    }

    return 0;
}

