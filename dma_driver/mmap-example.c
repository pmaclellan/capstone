#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>

int main (char argc, char* argv)
{
    int fd;
    void* file_memory;

    /* Open /dev/mem file */
    fd = open ("/dev/mem", O_RDWR);
    if (fd < 1) {
        perror(argv[0]);
        return -1;
    }
    /* mmap the device into memory */
    page_addr = (gpio_addr & (~(page_size-1)));
    page_offset = gpio_addr - page_addr;
    ptr = mmap(NULL, page_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, page_addr);

    /* Create the memory mapping.  */
    file_memory = mmap(0, 64, PROT_WRITE, MAP_SHARED, fd, 0);
    close (fd);

    int i = 0;
    while(1)
    {
        /* Write a random integer to memory-mapped area.  */
        sprintf((char*) file_memory, "%d\n", i);
        i++;
        if (i == 0xFFFFFFFF)
        {
            i = 0;
        }
    }

    /* Release the memory (unnecessary because the program exits).  */
    munmap (file_memory, 4 * 10);

}
