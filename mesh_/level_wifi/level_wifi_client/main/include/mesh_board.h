//
// Created by emilio on 11/01/20.
//

#ifndef _MESH_BOARD_H_
#define _MESH_BOARD_H_

#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_ble_mesh_defs.h"
#include "include/my_queue.h"

/*******************************************************
 *                Constants
 *******************************************************/

#define LED_WIFI GPIO_NUM_25
#define LED_BLE GPIO_NUM_26

#define BUF_SIZE (128)
#define ECHO_TEST_TXD (GPIO_NUM_23)
#define ECHO_TEST_RXD (GPIO_NUM_22)

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

void uart_init(void);

void uart_trasmitting(const char *test_str);

void create_message_rapid(char *status, char *level, char *ttl, uint8_t show_log);

char **str_split(char *a_str, char a_delim);

uint8_t count_tokens(char *a_str, char a_delim);

void decoding_string(char tokens0, char *token1, char *token2, char *token3, char *token4);

void command_received(char **tokens, int count);

void update_delay_buffer(int key);

void queue_operation(char operation, char tech, int key);

void create_new_task_wifi();

#endif //_MESH_BOARD_H_
