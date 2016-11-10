///***************************** Include Files *********************************/
//
//#include "xaxidma.h"
//#include "xparameters.h"
//#include "xil_exception.h"
//#include "xdebug.h"
//
//#ifdef XPAR_UARTNS550_0_BASEADDR
//#include "xuartns550_l.h"       /* to use uartns550 */
//#endif
//
//#ifdef XPAR_INTC_0_DEVICE_ID
//#include "xintc.h"
//#else
//#include "xscugic.h"
//#endif
//
///************************** Constant Definitions *****************************/
//
///*
// * Device hardware build related constants.
// */
//
//#define DMA_DEV_ID		XPAR_AXIDMA_0_DEVICE_ID
//
//#ifdef XPAR_AXI_7SDDR_0_S_AXI_BASEADDR
//#define DDR_BASE_ADDR		XPAR_AXI_7SDDR_0_S_AXI_BASEADDR
//#elif XPAR_MIG7SERIES_0_BASEADDR
//#define DDR_BASE_ADDR	XPAR_MIG7SERIES_0_BASEADDR
//#elif XPAR_MIG_0_BASEADDR
//#define DDR_BASE_ADDR	XPAR_MIG_0_BASEADDR
//#elif XPAR_PSU_DDR_0_S_AXI_BASEADDR
//#define DDR_BASE_ADDR	XPAR_PSU_DDR_0_S_AXI_BASEADDR
//#endif
//
//#ifndef DDR_BASE_ADDR
//#warning CHECK FOR THE VALID DDR ADDRESS IN XPARAMETERS.H, \
//		DEFAULT SET TO 0x01000000
//#define MEM_BASE_ADDR		0x01000000
//#else
//#define MEM_BASE_ADDR		(DDR_BASE_ADDR + 0x1000000)
//#endif
//
//#ifdef XPAR_INTC_0_DEVICE_ID
//#define RX_INTR_ID		XPAR_INTC_0_AXIDMA_0_S2MM_INTROUT_VEC_ID
//#define TX_INTR_ID		XPAR_INTC_0_AXIDMA_0_MM2S_INTROUT_VEC_ID
//#else
//#define RX_INTR_ID		XPAR_FABRIC_AXIDMA_0_S2MM_INTROUT_VEC_ID
//#define TX_INTR_ID		XPAR_FABRIC_AXIDMA_0_MM2S_INTROUT_VEC_ID
//#endif
//
//#define TX_BUFFER_BASE		(MEM_BASE_ADDR + 0x00100000)
//#define RX_BUFFER_BASE		(MEM_BASE_ADDR + 0x00300000)
//#define RX_BUFFER_HIGH		(MEM_BASE_ADDR + 0x004FFFFF)
//
//#ifdef XPAR_INTC_0_DEVICE_ID
//#define INTC_DEVICE_ID          XPAR_INTC_0_DEVICE_ID
//#else
//#define INTC_DEVICE_ID          XPAR_SCUGIC_SINGLE_DEVICE_ID
//#endif
//
//#ifdef XPAR_INTC_0_DEVICE_ID
//#define INTC		XIntc
//#define INTC_HANDLER	XIntc_InterruptHandler
//#else
//#define INTC		XScuGic
//#define INTC_HANDLER	XScuGic_InterruptHandler
//#endif
//
///* Timeout loop counter for reset
// */
//#define RESET_TIMEOUT_COUNTER	10000
//
//#define TEST_START_VALUE	0xC
///*
// * Buffer and Buffer Descriptor related constant definition
// */
//#define MAX_PKT_LEN		0x100
//
//#define NUMBER_OF_TRANSFERS	10
//
///* The interrupt coalescing threshold and delay timer threshold
// * Valid range is 1 to 255
// *
// * We set the coalescing threshold to be the total number of packets.
// * The receive side will only get one completion interrupt for this example.
// */
//
///**************************** Type Definitions *******************************/
//
///***************** Macros (Inline Functions) Definitions *********************/
//
///************************** Function Prototypes ******************************/
//#ifndef DEBUG
//extern void xil_printf(const char *format, ...);
//#endif
//
//static void TxIntrHandler(void *Callback);
//static void RxIntrHandler(void *Callback);
//
//static int SetupIntrSystem(INTC * IntcInstancePtr, XAxiDma * AxiDmaPtr,
//		u16 TxIntrId, u16 RxIntrId);
//static void DisableIntrSystem(INTC * IntcInstancePtr, u16 TxIntrId,
//		u16 RxIntrId);
//
///************************** Variable Definitions *****************************/
///*
// * Device instance definitions
// */
//
//static XAxiDma AxiDma; /* Instance of the XAxiDma */
//
//static INTC Intc; /* Instance of the Interrupt Controller */
//
///*
// * Flags interrupt handlers use to notify the application context the events.
// */
//volatile int TxDone;
//volatile int RxDone;
//volatile int Error;
//
///*****************************************************************************/
//int XAxiDma_IntrInitialize()
//{
//
//	Config = XAxiDma_LookupConfig(DMA_DEV_ID);
//	if (!Config)
//	{
//		xil_printf("No config found for %d\r\n", DMA_DEV_ID);
//
//		return XST_FAILURE;
//	}
//
//	/* Initialize DMA engine */
//	Status = XAxiDma_CfgInitialize(&AxiDma, Config);
//
//	if (Status != XST_SUCCESS)
//	{
//		xil_printf("Initialization failed %d\r\n", Status);
//		return XST_FAILURE;
//	}
//
//
//	Status = SetupIntrSystem(&Intc, &AxiDma, TX_INTR_ID, RX_INTR_ID);
//	if (Status != XST_SUCCESS) {
//
//		xil_printf("Failed intr setup\r\n");
//		return XST_FAILURE;
//	}
//
//	/* Disable all interrupts before setup */
//
//	XAxiDma_IntrDisable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,
//						XAXIDMA_DMA_TO_DEVICE);
//
//	XAxiDma_IntrDisable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,
//				XAXIDMA_DEVICE_TO_DMA);
//
//	/* Enable all interrupts */
//	XAxiDma_IntrEnable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,
//							XAXIDMA_DMA_TO_DEVICE);
//
//
//	XAxiDma_IntrEnable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,
//							XAXIDMA_DEVICE_TO_DMA);
//
//	/* Initialize flags before start transfer test  */
//	TxDone = 0;
//	RxDone = 0;
//	Error = 0;
//
//
//}
//
//static void RxIntrHandler(void *Callback)
//{
//	u32 IrqStatus;
//	int TimeOut;
//	XAxiDma *AxiDmaInst = (XAxiDma *) Callback;
//
//	/* Read pending interrupts */
//	IrqStatus = XAxiDma_IntrGetIrq(AxiDmaInst, XAXIDMA_DEVICE_TO_DMA);
//
//	/* Acknowledge pending interrupts */
//	XAxiDma_IntrAckIrq(AxiDmaInst, IrqStatus, XAXIDMA_DEVICE_TO_DMA);
//
//	/*
//	 * If no interrupt is asserted, we do not do anything
//	 */
//	if (!(IrqStatus & XAXIDMA_IRQ_ALL_MASK))
//	{
//		return;
//	}
//
//	/*
//	 * If error interrupt is asserted, raise error flag, reset the
//	 * hardware to recover from the error, and return with no further
//	 * processing.
//	 */
//	if ((IrqStatus & XAXIDMA_IRQ_ERROR_MASK))
//	{
//
//		Error = 1;
//
//		/* Reset could fail and hang
//		 * NEED a way to handle this or do not call it??
//		 */
//		XAxiDma_Reset(AxiDmaInst);
//
//		TimeOut = RESET_TIMEOUT_COUNTER;
//
//		while (TimeOut)
//		{
//			if (XAxiDma_ResetIsDone(AxiDmaInst))
//			{
//				break;
//			}
//
//			TimeOut -= 1;
//		}
//
//		return;
//	}
//
//	/*
//	 * If completion interrupt is asserted, then set RxDone flag
//	 */
//	if ((IrqStatus & XAXIDMA_IRQ_IOC_MASK))
//	{
//
//		RxDone = 1;
//	}
//}
