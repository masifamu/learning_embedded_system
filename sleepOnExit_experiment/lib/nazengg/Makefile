SRC     = $(wildcard *.c)
OBJ     = $(SRC:.c=.o)
INCLUDE = -I. -I../../lib/ST -I../../lib/ARM

CFLAGS  = -mcpu=cortex-m0 -mthumb -g2 -Wall -Wextra -Os $(INCLUDE) -DSTM32F051x8

all: libnazengg.a

%.o: %.c
	arm-none-eabi-gcc $(CFLAGS) -c $< -o $@

libnazengg.a: $(OBJ)
	arm-none-eabi-ar rcs $@ $^

clean:
	rm -f *.o libnazengg.a
