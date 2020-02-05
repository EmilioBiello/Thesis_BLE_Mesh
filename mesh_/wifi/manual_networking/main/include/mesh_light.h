/* Mesh Manual Networking Example

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/

#ifndef __MESH_LIGHT_H__
#define __MESH_LIGHT_H__

#include "esp_err.h"

/*******************************************************
 *                Constants
 *******************************************************/
#define LED_WIFI GPIO_NUM_25
#define LED_BLE GPIO_NUM_26
#define LED_BLE_1 GPIO_NUM_27

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
 *                Variables Declarations
 *******************************************************/

/*******************************************************
 *                Function Definitions
 *******************************************************/
esp_err_t mesh_light_init(void);

void mesh_connected_indicator(int layer);

void mesh_disconnected_indicator(void);

void board_led_operation(uint8_t pin, uint8_t status_led);

void board_led_operation_wifi(uint8_t status_led);

#endif /* __MESH_LIGHT_H__ */
