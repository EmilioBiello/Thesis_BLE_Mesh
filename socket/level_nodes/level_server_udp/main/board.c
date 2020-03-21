/* board.c - Board-specific hooks */

/*
 * Copyright (c) 2017 Intel Corporation
 * Additional Copyright (c) 2018 Espressif Systems (Shanghai) PTE LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "board.h"

#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "tcpip_adapter.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>
#include "connect.h"

#define TAG "BOARD"

/*******************************************************
 *                Variable Definitions
 *******************************************************/
static bool s_light_inited = false;

struct _led_state led_state[2] = {
        {LED_OFF, LED_OFF, LED_BLE,   "green"},
        {LED_OFF, LED_OFF, LED_BLE_1, "blue"},
};

char rx_buffer[128];
char addr_str[128];
int addr_family;
int ip_protocol;
struct sockaddr_in dest_addr;
int sock;
int err;
bool is_running_wifi = false;
uint8_t status_led_wifi = 1;

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

void test_LED() {
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

    test_LED();

    return ESP_OK;
}

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
void create_socket() {
    dest_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(PORT);
    addr_family = AF_INET;
    ip_protocol = IPPROTO_IP;
    inet_ntoa_r(dest_addr.sin_addr, addr_str, sizeof(addr_str) - 1);
    while (1) {
        sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
        } else {
            ESP_LOGI(TAG, "Socket created");
            err = bind(sock, (struct sockaddr *) &dest_addr, sizeof(dest_addr));
            if (err < 0) {
                ESP_LOGE(TAG, "Socket unable to bind: errno %d", errno);
            } else {
                ESP_LOGI(TAG, "Socket bound, port %d", PORT);
                is_running_wifi = true;
                break;
            }
        }
    }
    board_led_operation_wifi(LED_WIFI, LED_OFF);
}

void send_mex_wifi(int len, struct sockaddr_in source_addr) {
    err = sendto(sock, rx_buffer, len, 0, (struct sockaddr *) &source_addr, sizeof(source_addr));
    if (err < 0) {
        ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
    }
}

static void udp_server_task(void *pvParameters) {
    struct sockaddr_in source_addr; // IPv4
    socklen_t socklen = sizeof(source_addr);


    ESP_LOGI(TAG, "Waiting for data");
    while (is_running_wifi) {
        int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer) - 1, 0, (struct sockaddr *) &source_addr, &socklen);

        // Error occurred during receiving
        if (len < 0) {
            ESP_LOGE(TAG, "recvfrom failed: errno %d", errno);
            break;
        } else {
            // Get the sender's ip address as string
            inet_ntoa_r(((struct sockaddr_in *) &source_addr)->sin_addr.s_addr, addr_str, sizeof(addr_str) - 1);

            rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string...
            ESP_LOGW(TAG, "Received %d bytes from %s: [%s]", len, addr_str, rx_buffer);

            send_mex_wifi(len, source_addr);
            board_led_operation_wifi(LED_WIFI, status_led_wifi);
            status_led_wifi = !status_led_wifi;
        }
    }
    if (sock != -1) {
        ESP_LOGE(TAG, "Shutting down socket and restarting...");
        shutdown(sock, 0);
        close(sock);
    }
    vTaskDelete(NULL);
}

void wifi_init() {
    ESP_ERROR_CHECK(nvs_flash_init());
    tcpip_adapter_init();
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    create_socket();

    xTaskCreate(udp_server_task, "udp_server", 2048, NULL, 3, NULL);
}