#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdint.h>

int main()
{
    // Define the file path to read from
    char* dmaFifoPath = "/tmp/dma-fifo";
    uint16_t buf;
    int fd;

    /* open, read, and display the message from the FIFO */
    fd = open(dmaFifoPath, O_RDONLY);
    while(1) {
        read(fd, &buf, sizeof(buf));
        printf("Received : %d\n", buf);
    }
    close(fd);

    return 0;
}