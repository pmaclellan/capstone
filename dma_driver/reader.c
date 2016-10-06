#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

int main()
{
    int fd;
    char * myfifo = "./myfifo";
    int buf;

    /* open, read, and display the message from the FIFO */
    while(1) {
        fd = open(myfifo, O_RDONLY);
        read(fd, &buf, sizeof(buf));
        printf("Received: %d\n", buf);
        close(fd);
    }

    return 0;
}