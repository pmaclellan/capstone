#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#define READ_ADDR 100 // 100 for test

int main (int argc, char* argv[])
{
    int fd, fifoFd;
    unsigned gpio_addr;
    int value = 0;
    char * myfifo = "./myfifo";
    
    unsigned page_addr, page_offset;
    void *ptr;
    unsigned page_size=sysconf(_SC_PAGESIZE);

    /* Open /dev/mem file */
    fd = open ("/dev/mem", O_RDWR);
    if (fd < 1) {
        perror(argv[0]);
        return -1;
    }

    // strtoul take are startaddr and returns a pointer
    // TODO: This might not be necessary, but idk what it does
    gpio_addr=READ_ADDR;

    /* mmap the device into memory */
    page_addr = (gpio_addr & (~(page_size-1)));
    page_offset = gpio_addr - page_addr;
    ptr = mmap(NULL, page_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, page_addr);


    // Make a FIFO to talk to other processes
    mkfifo(myfifo, 0666);

    while(1)
    {
        /* Read value from the device register */
        value = *((unsigned *)(ptr + page_offset));
        printf("Data here is: %08x\n",value);

        // Write data to fifo
        fifoFd = open(myfifo, O_WRONLY);
        write(fifoFd, & value, sizeof(value));
        close(fifoFd);

        /* Put data into a pipe */
        sleep(1);
    }

    munmap(ptr, page_size);
    return 0;

}
