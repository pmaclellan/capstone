#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

#define REGISTER_COUNT 8

int main()
{
    // Define the file paths to write to
    char* dmaFifoPaths[] = {
        "/tmp/dma-register-1",
        "/tmp/dma-register-2",
        "/tmp/dma-register-3",
        "/tmp/dma-register-4",
        "/tmp/dma-register-5",
        "/tmp/dma-register-6",
        "/tmp/dma-register-7",
        "/tmp/dma-register-8"
    };
    int buf;
    int fd;
    int i;

    /* open, read, and display the message from the FIFO */
    while(1) {
        for(i = 0; i < REGISTER_COUNT; i++)
        {
            fd = open(dmaFifoPaths[i], O_RDONLY);
            read(fd, &buf, sizeof(buf));
            printf("Received from register %d: %d\n", i, buf);
            close(fd); 
        }

    }

    return 0;
}