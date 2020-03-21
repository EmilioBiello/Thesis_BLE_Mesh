/* board.h - Board-specific hooks */

/*
 * Copyright (c) 2017 Intel Corporation
 * Additional Copyright (c) 2018 Espressif Systems (Shanghai) PTE LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef _BOARD_H_
#define _BOARD_H_

#include "driver/gpio.h"
#include "esp_ble_mesh_defs.h"

#define LED_G GPIO_NUM_27
#define BUTTON_PIN 2
#define ESP_INTR_FLAG_DEFAULT 0

#define LED_ON  1
#define LED_OFF 0

struct _led_state {
    uint8_t current;
    uint8_t previous;
    uint8_t pin;
    char *name;
};

void board_led_operation(uint8_t pin, uint8_t status_led);

void board_init(void);

void board_rule_init(void);

#endif
