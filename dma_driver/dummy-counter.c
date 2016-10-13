#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#define REGISTER_COUNT 8
#define VALUES_SIZE 34
#define MESSAGE_HEADER 0xDEAD
#define MASK_ADC0 0xFFFF000000000000
#define MASK_ADC1 0x0000FFFF00000000
#define MASK_ADC2 0x00000000FFFF0000
#define MASK_ADC3 0x000000000000FFFF

int main (int argc, char* argv[])
{
    // Define the file paths to write to
    char* dmaFifoPath = "/tmp/dma-fifo";

    // Define registers to read from
    unsigned registers[] = {
        0xb7758000,
        0xb7758000,
        0xb7758000,
        0xb7758000,
        0xb7758000,
        0xb7758000,
        0xb7758000,
        0xb7758000
    };

    uint64_t value;
    uint16_t values[VALUES_SIZE]; // 32 channels plus timestamp and header
    
    int fd;
    int fifoFd;
    int i;
    unsigned gpio_addr;
    unsigned page_addr;
    unsigned page_offsets[REGISTER_COUNT];
    unsigned page_size=sizeof(uint64_t);

    /* Open /dev/mem file */
    fd = open("/dev/mem", O_RDWR);
    if (fd < 1) {
        perror(argv[0]);
        return -1;
    }

    // Make a bunch of fifos and initialize mmap
    void* ptrs[REGISTER_COUNT];
    for(i = 0; i < REGISTER_COUNT; i++)
    {
        mkfifo(dmaFifoPath, 0666);
        gpio_addr = registers[i];
        page_addr = (gpio_addr & (~(page_size-1)));
        page_offsets[i] = gpio_addr - page_addr;
        ptrs[i] = mmap(NULL, page_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, page_addr);
    }

    uint16_t counter = 0;
    while(1)
    {
        // prepare the packet with a header and timestamp
        values[0] = MESSAGE_HEADER;
        values[1] = 0x0000; // TODO: this should be the timestamp
        for(i = 2; i < VALUES_SIZE; i++)
        {
            values[i] = counter;
            counter++;
            if(counter > 100)
            {
                counter = 0;
            }
        }
        // When reading the register, you get 4 channel values:
        // REGISTER 1: 0.0  1.0  2.0  3.0
        // REGISTER 2: 0.1  1.1  2.1  3.1
        // ....
        // REGISTER 3: 0.7  1.7  2.7  3.7
        // We want to transmit in the following format:
        // HEADER, TIMESTAMP, 0.0, 0.1, ... , 3.6, 3.7
        // First set the offsets for the ADC's
        // int adc0 = 2;   // index 2 corresponds to the 0.0 spot
        // int adc1 = 10;  // index 10 corresponds to the 1.0 spot
        // int adc2 = 18;  // index 18 corresponds to the 2.0 spot
        // int adc3 = 26;  // index 26 corresponds to the 3.0 spot
        // int registerNumber = 0;

        // // Read registers and put our data into values
        // while(registerNumber <  REGISTER_COUNT)
        // {
        //     // Read the register
        //     value = *((uint64_t *)(ptrs[i] + page_offsets[i]));

        //     // Get adc values
        //     values[adc0] = (uint16_t)((MASK_ADC0 & value) >> 48);
        //     values[adc1] = (uint16_t)((MASK_ADC1 & value) >> 32);
        //     values[adc2] = (uint16_t)((MASK_ADC2 & value) >> 16);
        //     values[adc3] = (uint16_t)(MASK_ADC3 & value);

        //     // Write data to fifo
        //     write(fifoFd, &value, sizeof(values));
        //     close(fifoFd);

        //     // Increment counters
        //     adc0++;
        //     adc1++;
        //     adc2++;
        //     adc3++;
        //     registerNumber++;
        // }

        // Write to the fifo
        i = 0;
        fifoFd = open(dmaFifoPath, O_WRONLY);
        while(i < VALUES_SIZE)
        {
            write(fifoFd, &values[i], sizeof(uint16_t));
            printf("Writing: %d\n", values[i]);
            i++;
        }
        close(fifoFd);
        sleep(1);
    }

    for (i = 0; i < REGISTER_COUNT; i++)
    {
        munmap(ptrs[i], page_size);
    }

    return 0;
}