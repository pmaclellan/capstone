#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>

int main (char argc, char* argv)
{
    int fd;
    void* file_memory;

    /* Prepare a file large enough to hold an unsigned integer.  */
    fd = open("dmaPipe", O_RDWR | O_CREAT, S_IRUSR | S_IWUSR);

    //Make the file big enough
    lseek (fd, 64, SEEK_SET);
    write (fd, "", 1);
    lseek (fd, 0, SEEK_SET);

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
