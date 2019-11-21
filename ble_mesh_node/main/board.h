/* board.h - Board-specific hooks */

/*
 * Copyright (c) 2017 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef _BOARD_H_
#define _BOARD_H_

#include "driver/gpio.h"
#include "esp_ble_mesh_defs.h"

#define LED_R GPIO_NUM_25
#define LED_G GPIO_NUM_26
#define LED_B GPIO_NUM_27

#define LED_ON  1
#define LED_OFF 0

struct _led_state {
    uint8_t current;
    uint8_t previous;
    uint8_t pin;
    char *name;
};

void board_output_number(esp_ble_mesh_output_action_t action, uint32_t number);

void board_led_operation(uint8_t pin, uint8_t onoff);

void board_init(void);

#endif
