//
// Created by emilio on 11/01/20.
//

#ifndef _BOARD_H_
#define _BOARD_H_

#include "driver/gpio.h"

#define LED_G GPIO_NUM_27

#define LED_ON 1
#define LED_OFF 0

struct _led_state {
    uint8_t current;
    uint8_t previous;
    uint8_t pin;
    char *name;
};

void board_led_operation(uint8_t pin, uint8_t status_led);

void board_init(void);

#endif //_BOARD_H_
