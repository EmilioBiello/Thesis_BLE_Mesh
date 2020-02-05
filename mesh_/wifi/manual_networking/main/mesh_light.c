/* Mesh Manual Networking Example

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/

#include <string.h>
#include <esp_log.h>
#include "esp_err.h"
#include "esp_mesh.h"
#include "include/mesh_light.h"
#include "driver/gpio.h"
#include "driver/ledc.h"

/*******************************************************
 *                Constants
 *******************************************************/
struct _led_state led_state[2] = {
        {LED_OFF, LED_OFF, LED_BLE,   "ble"},
        {LED_OFF, LED_OFF, LED_BLE_1, "ble_1"},
};

/*******************************************************
 *                Variable Definitions
 *******************************************************/
static bool s_light_inited = false;

/*******************************************************
 *                Function Definitions
 *******************************************************/
void test_led();

esp_err_t mesh_light_init(void) {
    if (s_light_inited == true) {
        return ESP_OK;
    }
    s_light_inited = true;

    gpio_pad_select_gpio(LED_WIFI);
    gpio_set_direction(LED_WIFI, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_WIFI, LED_OFF);

    gpio_pad_select_gpio(LED_BLE);
    gpio_set_direction(LED_BLE, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_BLE, LED_OFF);

    gpio_pad_select_gpio(LED_BLE_1);
    gpio_set_direction(LED_BLE_1, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_BLE_1, LED_OFF);
    test_led();
    return ESP_OK;
}

void test_led() {
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

void board_led_operation_wifi(uint8_t status_led) {
    gpio_set_level(LED_BLE, status_led);
}

void board_led_operation(uint8_t pin, uint8_t status_led) {
    for (int i = 0; i < 2; i++) {
        if (led_state[i].pin != pin) {
            continue;
        }
        if (status_led == led_state[i].previous) {
            ESP_LOGW("BLE", "led %s is already %s",
                     led_state[i].name, (status_led ? "on" : "off"));
            return;
        }
        gpio_set_level(pin, status_led);
        led_state[i].previous = status_led;
        return;
    }

    ESP_LOGE("BLE", "LED is not found!");
}
