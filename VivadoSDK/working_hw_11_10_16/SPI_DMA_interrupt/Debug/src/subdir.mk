################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
LD_SRCS += \
../src/lscript.ld 

C_SRCS += \
../src/adc.c \
../src/dac.c \
../src/dma_intr.c \
../src/dma_passthrough.c \
../src/main.c \
../src/platform.c 

OBJS += \
./src/adc.o \
./src/dac.o \
./src/dma_intr.o \
./src/dma_passthrough.o \
./src/main.o \
./src/platform.o 

C_DEPS += \
./src/adc.d \
./src/dac.d \
./src/dma_intr.d \
./src/dma_passthrough.d \
./src/main.d \
./src/platform.d 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc -Wall -O0 -g3 -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -I../../SPI_DMA_bsp_5/ps7_cortexa9_0/include -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


