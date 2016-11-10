
//////////////////////////////////////////////////////////////////////////////////
//
// Company:        Xilinx
// Engineer:       bwiec
// Create Date:    30 June 2015, 02:37:56 PM
// App Name:       Interrupt-mode AXI DMA Demonstration
// File Name:      helloworld.c
// Target Devices: Zynq
// Tool Versions:  2015.1
// Description:    Implementation of AXI DMA passthrough in interrupt mode
// Dependencies:
//   - xuartps_hw.h - Driver version v3.0
//   - xllfifo.h    - Driver version v4.0
//   - adc.h        - Driver version v1.0
//   - dac.h        - Driver version v1.0
// Revision History:
//   - v1.0
//     * Initial release
//     * Tested on ZC702 and Zedboard
// Additional Comments:
//   - UART baud rate is 115200
//   - In this design, the 'ADC' and 'DAC' devices are simply emulating such
//     hardware (using a GPIO for control). Their purpose is to showcase a
//     middleware driver sitting on top of the dma_passthrough driver. The ADC and
//     DAC drivers will surely need to be re-written for the specific application.
//
//////////////////////////////////////////////////////////////////////////////////
 
// Includes
#define _STDC_FORMAT_MACROS
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include "platform.h"
#include "xuartps_hw.h"
//#include "xllfifo.h"
#include "xil_cache.h"
#include "adc.h"
#include "dac.h"
#include "sleep.h"
#include "time.h"

// Defines
// Int every 5ms, at 200kHz -> 200000 * 0.005 * 9
#define PACKETS_PER_FRAME  12
#define SAMPLES_PER_PACKET 9
#define BYTES_PER_SAMPLE   8

#define SCLK_DIVIDER       2
#define SAMPLE_FREQUENCY   1000 	// freq = 100MHz / SAMPLE_FREQUENCY


#define ADC_BASE_ADDR 0x43C00000;

// Main entry point
int main()
{
	// Local variables
	int     	status;
	adc_t*  	p_adc_inst;
	uint64_t    rcv_buf[SAMPLES_PER_PACKET*PACKETS_PER_FRAME];

	// Setup UART and caches
    init_platform();
    xil_printf("%c[2J", 27);
    xil_printf("\fHello World!\n\r");
    xil_printf("%X \n\r", rcv_buf);


    // Create ADC object
    p_adc_inst = adc_create
    (
    	XPAR_GPIO_0_DEVICE_ID,
		XPAR_GPIO_1_DEVICE_ID,
		XPAR_GPIO_2_DEVICE_ID,
    	XPAR_AXIDMA_0_DEVICE_ID,
    	XPAR_PS7_SCUGIC_0_DEVICE_ID,
		XPAR_FABRIC_AXI_DMA_0_S2MM_INTROUT_INTR,
		BYTES_PER_SAMPLE
    );


    if (p_adc_inst == NULL)
    {
    	xil_printf("ERROR! Failed to create ADC instance.\n\r");
    	return -1;
    }

    // Set the desired parameters for the ADC/DAC objects
    adc_set_bytes_per_sample(p_adc_inst, BYTES_PER_SAMPLE);
    adc_set_samples_per_frame(p_adc_inst, SAMPLES_PER_PACKET*PACKETS_PER_FRAME);


//    adc_test_leds(p_adc_inst);

	// Make sure the buffers are clear before we populate it (generally don't need to do this, but for proving the DMA working, we do it anyway)
	memset(rcv_buf, 0, SAMPLES_PER_PACKET*PACKETS_PER_FRAME*BYTES_PER_SAMPLE);


	// Enable/initialize adc
//	adc_config_axi(p_adc_inst);
//	adc_get_config_axi(p_adc_inst);
	adc_config_gpio(p_adc_inst, SCLK_DIVIDER, SAMPLE_FREQUENCY, PACKETS_PER_FRAME);
	adc_enable(p_adc_inst);

	// Process data

	int i = 0;
	int t;

	while(1)
	{
		status = adc_get_frame(p_adc_inst, rcv_buf);
		if (status != ADC_SUCCESS)
		{
			xil_printf("ERROR! Failed to get a new frame of data from the ADC.\n\r");
			return -1;
		}
	}

	adc_disable(p_adc_inst);
	adc_destroy(p_adc_inst);

    return 0;
}


