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

/*******************************************************
 *                Constants
 *******************************************************/

#define LED_WIFI GPIO_NUM_25
#define LED_BLE GPIO_NUM_26

/*******************************************************
 *                Type Definitions
 *******************************************************/
#define LED_ON 1
#define LED_OFF 0
/*******************************************************
 *                Structures
 *******************************************************/
struct _led_state {
    uint8_t current;
    uint8_t previous;
    uint8_t pin;
    char *name;
};

/*******************************************************
 *                Function Declarations
 *******************************************************/
esp_err_t mesh_light_init(void);

void board_led_operation(uint8_t pin, uint8_t status_led);

void wifi_led(uint8_t pin, uint8_t status_led);

void board_init(void);

void send_mex_wifi(int16_t value);

#endif
