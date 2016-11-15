/*
 * axi-dma.h
 *
 *  Created on: Nov 11, 2016
 *      Author: dominic
 */

#ifndef SRC_AXI_DMA_H_
#define SRC_AXI_DMA_H_

#define SCLK_FREQUENCY      2       // 2 = 25MHz
#define NUM_PACKETS         4       // 4 packets
#define LINES_PER_PACKET    9       // 1 header and 8 lines of data

typedef enum
{
    UNUSED,
    EMBRYO,
    RUNNING
} DMA_STATUS;

extern DMA_STATUS Status; // Global DMA status

void initDMA();
void startDMA(uint16_t sampleFreq);
void stopDMA();

#endif /* SRC_AXI_DMA_H_ */
