#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdint.h>

#define REGISTER_COUNT 8

int main()
{
    // Define the file paths to write to
    char* dmaFifoPath = "/tmp/dma-fifo";
    uint16_t buf;
    int fd;

    /* open, read, and display the message from the FIFO */
    while(1) {
        fd = open(dmaFifoPath, O_RDONLY);
        read(fd, &buf, sizeof(buf));
        printf("Received : %d\n", buf); 
    }

    return 0;
}