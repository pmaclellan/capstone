
// Includes
#include <stdlib.h>
#include "adc.h"
#include "xgpio.h"
#include "dma_passthrough.h"

// Private data
typedef struct adc_periphs
{
	dma_passthrough_t* p_dma_passthrough_inst;
	XGpio              gpio_inst_0;
	XGpio              gpio_inst_1;
	XGpio              gpio_inst_2;
} adc_periphs_t;

// Object definition
typedef struct adc
{
	adc_periphs_t periphs;
	int           samples_per_frame;
	int           bytes_per_sample;
} adc_t;

// Private functions
static int init_gpio(XGpio* p_gpio_inst_0, int gpio_device_id_0, XGpio* p_gpio_inst_1, int gpio_device_id_1, XGpio* p_gpio_inst_2, int gpio_device_id_2)
{

	// Local variables
	int status = 0;

	// Initialize driver
	status = XGpio_Initialize(p_gpio_inst_0, gpio_device_id_0);
	if (status != XST_SUCCESS)
	{
		xil_printf("ERROR! Initialization of AXI GPIO instance failed.\n\r");
		return ADC_GPIO_INIT_FAIL;
	}

	status = XGpio_Initialize(p_gpio_inst_1, gpio_device_id_1);
	if (status != XST_SUCCESS)
	{
		xil_printf("ERROR! Initialization of AXI GPIO instance failed.\n\r");
		return ADC_GPIO_INIT_FAIL;
	}

	status = XGpio_Initialize(p_gpio_inst_2, gpio_device_id_2);
	if (status != XST_SUCCESS)
	{
		xil_printf("ERROR! Initialization of AXI GPIO instance failed.\n\r");
		return ADC_GPIO_INIT_FAIL;
	}

	// Set value to 0 in case set some other way by previous run
	XGpio_DiscreteWrite(p_gpio_inst_0, 1, 0);
	XGpio_DiscreteWrite(p_gpio_inst_0, 2, 0);
	XGpio_DiscreteWrite(p_gpio_inst_1, 1, 0);
	XGpio_DiscreteWrite(p_gpio_inst_1, 2, 0);
	XGpio_DiscreteWrite(p_gpio_inst_2, 1, 0);
	XGpio_DiscreteWrite(p_gpio_inst_2, 2, 0);

	return ADC_SUCCESS;

}

// Public functions
adc_t* adc_create(int gpio_device_id_0, int gpio_device_id_1, int gpio_device_id_2, int dma_device_id, int intc_device_id, int s2mm_intr_id,
		          int bytes_per_sample)
{

	// Local variables
	int    status;
	adc_t* p_obj;

	// Allocate memory for ADC object
	p_obj = (adc_t*) malloc(sizeof(adc_t));
	if (p_obj == NULL)
	{
		xil_printf("ERROR! Failed to allocate memory for ADC object.\n\r");
		return NULL;
	}

	// Create DMA Passthrough object to be used by the ADC
	p_obj->periphs.p_dma_passthrough_inst = dma_passthrough_create
	(
		dma_device_id,
		intc_device_id,
		s2mm_intr_id,
		bytes_per_sample
	);
	if (p_obj->periphs.p_dma_passthrough_inst == NULL)
	{
		xil_printf("ERROR! Failed to create DMA Passthrough object for use by the ADC.\n\r");
		return NULL;
	}

	// Register and initialize peripherals
	status = init_gpio(&p_obj->periphs.gpio_inst_0, gpio_device_id_0, &p_obj->periphs.gpio_inst_1, gpio_device_id_1, &p_obj->periphs.gpio_inst_2, gpio_device_id_2);
	if (status != XST_SUCCESS)
	{
		xil_printf("ERROR! Failed to initialize GPIO.\n\r");
		adc_destroy(p_obj);
		return NULL;
	}

	// Initialize ADC parameters
	adc_set_samples_per_frame(p_obj, 1024);
	adc_set_bytes_per_sample(p_obj, bytes_per_sample);

	return p_obj;

}

void adc_destroy(adc_t* p_adc_inst)
{
	dma_passthrough_destroy(p_adc_inst->periphs.p_dma_passthrough_inst);
	free(p_adc_inst);
}


void adc_set_samples_per_frame(adc_t* p_adc_inst, int samples_per_frame)
{
	p_adc_inst->samples_per_frame = samples_per_frame;
	dma_passthrough_set_buf_length(p_adc_inst->periphs.p_dma_passthrough_inst, samples_per_frame);
}


int adc_get_samples_per_frame(adc_t* p_adc_inst)
{
	return (p_adc_inst->samples_per_frame);
}

void adc_set_bytes_per_sample(adc_t* p_adc_inst, int bytes_per_sample)
{
	p_adc_inst->bytes_per_sample = bytes_per_sample;
	dma_passthrough_set_sample_size_bytes(p_adc_inst->periphs.p_dma_passthrough_inst, bytes_per_sample);
}

int adc_get_bytes_per_sample(adc_t* p_adc_inst)
{
	return (p_adc_inst->bytes_per_sample);
}

void adc_enable(adc_t* p_adc_inst)
// The implementation of this function is specific to this hardware where a GPIO
// is used to emulate a data source. This function would obviously be implemented
// completely differently if there were an actual ADC in the system.
{
	dma_passthrough_reset(p_adc_inst->periphs.p_dma_passthrough_inst); // Reset DMA to flush those 4 extra samples that are accepted before DMA configuration
//	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst, 1, adc_get_samples_per_frame(p_adc_inst));     // Assert the reset on the hardware counter
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_0, 2, 1);     // Release the reset on the hardware counter
}



void adc_test_leds(adc_t* p_adc_inst)
{
	int i;

	for(i = 0; i < 256; i++)
	{
		XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_2, 1, i);
		usleep(800);
	}

	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_2, 1, 0);

}


void adc_reset_timestamp(adc_t* p_adc_inst)
{
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_0, 1, 1);
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_0, 1, 0);
}

void adc_config_gpio(adc_t* p_adc_inst, int sclk_frequency, int sample_frequency, int packet_size)
{
	// Configure sample frequency and clock frequency.
	// Upper 16 bits are SCLK divider:
	// 				0x0002 = 2 = 25 MHz
	// Lower 16 bits are sample frequency:
	//				0x03E8 = 1000 = 100 kHz
	// 			    0x01F4 = 500 = 200 kHz
	//				0x07D0 = 2000 = 50 kHz

	// SCLK - gpio1 channel 1
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_1, 1, 0x00000002);
	// Sample Frequency - gpio1 channel 2
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_1, 2, 0x000007D0);
	// Packet Configuration - gpio2 channel 2
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_2, 2, packet_size - 2);
}

void adc_config_axi(adc_t* p_adc_inst)
{
	// Configure sample frequency and clock frequency.
	// Upper 16 bits are SCLK divider:
	// 				0x0002 = 2 = 25 MHz
	// Lower 16 bits are sample frequency:
	//				0x07D0 = 2000 = 50 kHz
	//				0x03E8 = 1000 = 100 kHz
	// 			    0x01F4 = 500 = 200 kHz

	Xil_Out32(0x43C00000, 0x00007D0);
	Xil_Out32(0x43C00000+4, 0x00000002);
}

void adc_get_config_axi(adc_t* p_adc_inst)
{
	int temp1;
	int temp2;
	// Configure sample frequency and clock frequency.
	// Upper 16 bits are SCLK divider:
	// 				0x0002 = 2 = 25 MHz
	// Lower 16 bits are sample frequency:
	//				0x07D0 = 2000 = 50 kHz
	//				0x03E8 = 1000 = 100 kHz
	// 			    0x01F4 = 500 = 200 kHz

	temp1 = Xil_In32(0x43C00000);
	temp2 = Xil_In32(0x43C00000+4);

	return 0;
}


void adc_disable(adc_t* p_adc_inst)
// The implementation of this function is specific to this hardware where a GPIO
// is used to emulate a data source. This function would obviously be implemented
// completely differently if there were an actual ADC in the system.
{
//	dma_passthrough_reset(p_adc_inst->periphs.p_dma_passthrough_inst); // Reset DMA to flush those 4 extra samples that are accepted before DMA configuration
//	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst, 1, adc_get_samples_per_frame(p_adc_inst));     // Assert the reset on the hardware counter
	XGpio_DiscreteSet(&p_adc_inst->periphs.gpio_inst_0, 2, 0);     // Release the reset on the hardware counter
}

int adc_get_frame(adc_t* p_adc_inst, void* buf)
{

	// Local variables
	int status;

	dma_passthrough_set_rcv_buf(p_adc_inst->periphs.p_dma_passthrough_inst, buf);
	status = dma_passthrough_rcv(p_adc_inst->periphs.p_dma_passthrough_inst, p_adc_inst);
	if (status != DMA_PASSTHROUGH_SUCCESS)
	{
		xil_printf("ERROR! DMA Passthrough error occurred when trying to get data.\n\r");
		return ADC_DMA_FAIL;
	}

	return ADC_SUCCESS;

}

