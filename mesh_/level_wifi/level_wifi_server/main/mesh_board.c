//
// Created by emilio on 11/01/20.
//

#include <stdio.h>
#include "string.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"
#include "esp_err.h"
#include "esp_mesh.h"

#include "include/mesh_board.h"

#include "driver/uart.h"
#include "soc/uart_struct.h"

#define TAG "uart_events"


/*******************************************************
 *                Variable Definitions
 *******************************************************/
static bool s_light_inited = false;

struct _led_state led_state[2] = {
        {LED_OFF, LED_OFF, LED_BLE,   "red"},
        {LED_OFF, LED_OFF, LED_BLE_1, "white"},
};

/*******************************************************
 *                Function Definitions Light
 *******************************************************/
void board_led_operation(uint8_t pin, uint8_t status_led) {
    for (int i = 0; i < 2; i++) {
        if (led_state[i].pin != pin) {
            continue;
        }
        if (status_led == led_state[i].previous) {
            ESP_LOGW(TAG, "led %s is already %s",
                     led_state[i].name, (status_led ? "on" : "off"));
            return;
        }
        gpio_set_level(pin, status_led);
        led_state[i].previous = status_led;
        return;
    }

    ESP_LOGE(TAG, "LED is not found!");
}

void board_led_operation_wifi(uint8_t pin, uint8_t status_led) {
    gpio_set_level(pin, status_led);
}

esp_err_t mesh_light_init(void) {
    if (s_light_inited == true) {
        return ESP_OK;
    }
    s_light_inited = true;
    for (int i = 0; i < 2; i++) {
        gpio_pad_select_gpio(led_state[i].pin);
        gpio_set_direction(led_state[i].pin, GPIO_MODE_OUTPUT);
        gpio_set_level(led_state[i].pin, LED_OFF);
        led_state[i].previous = LED_OFF;
    }

    gpio_pad_select_gpio(LED_WIFI);
    gpio_set_direction(LED_WIFI, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_WIFI, LED_OFF);

    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_ON);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    gpio_set_level(LED_BLE, LED_ON);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    gpio_set_level(LED_BLE_1, LED_ON);

    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_OFF);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    gpio_set_level(LED_BLE, LED_OFF);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    gpio_set_level(LED_BLE_1, LED_OFF);

    return ESP_OK;
}

void mesh_connected_indicator(int layer) {
    for (int i = 0; i < layer; ++i) {
        gpio_set_level(LED_WIFI, LED_ON);
        vTaskDelay(200 / portTICK_PERIOD_MS);

        gpio_set_level(LED_WIFI, LED_OFF);
        vTaskDelay(200 / portTICK_PERIOD_MS);
    }
    ESP_LOGW("LIGHT", "Warning Light --- mesh_connected_indicator\n");
}

void mesh_disconnected_indicator(void) {
    for (int i = 0; i < 2; ++i) {
        gpio_set_level(LED_WIFI, LED_ON);
        vTaskDelay(500 / portTICK_PERIOD_MS);

        gpio_set_level(LED_WIFI, LED_OFF);
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }
    ESP_LOGW("LIGHT", "Warning Light --- mesh_disconnected_indicator\n");
}