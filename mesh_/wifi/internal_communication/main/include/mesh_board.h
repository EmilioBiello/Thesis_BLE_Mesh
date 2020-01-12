//
// Created by emilio on 11/01/20.
//

#ifndef _MESH_BOARD_H_
#define _MESH_BOARD_H_

#include "driver/gpio.h"
#include "esp_err.h"

/*******************************************************
 *                Constants
 *******************************************************/

#define LED_WIFI GPIO_NUM_26
#define LED_BLUETOOTH GPIO_NUM_27

#define BUF_SIZE (128)
#define ECHO_TEST_TXD (GPIO_NUM_23)
#define ECHO_TEST_RXD (GPIO_NUM_22)

#define  MESH_TOKEN_ID       (0x0)
#define  MESH_TOKEN_VALUE    (0xbeef)
#define  MESH_CONTROL_CMD    (0x2)

/*******************************************************
 *                Type Definitions
 *******************************************************/
#define LED_ON 1
#define LED_OFF 0
/*******************************************************
 *                Structures
 *******************************************************/
typedef struct {
    uint8_t cmd;
    bool on;
    uint8_t token_id;
    uint16_t token_value;
} mesh_light_ctl_t;

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
esp_err_t mesh_light_process(mesh_addr_t *from, uint8_t *buf, uint16_t len);
void mesh_connected_indicator(int layer);
void mesh_disconnected_indicator(void);
void board_led_operation(uint8_t pin, uint8_t status_led);

void uart_init(void);

#endif //_MESH_BOARD_H_
