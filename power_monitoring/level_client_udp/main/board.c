/* board.c - Board-specific hooks */

/*
 * Copyright (c) 2017 Intel Corporation
 * Additional Copyright (c) 2018 Espressif Systems (Shanghai) PTE LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "tcpip_adapter.h"

#include "board.h"

#include "driver/uart.h"
#include "assert.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

#include "my_queue.h"
#include "connect.h"

extern void send_message_BLE(uint16_t addr, uint32_t opcode, int16_t level, bool send_rel);

struct _led_state led_array = {LED_OFF, LED_OFF, LED_BLE, "ble_mesh"};

/*******************************************************
 *                Variable Definitions
 *******************************************************/
//#define HOST_IP_ADDR "192.168.43.253"
#define HOST_IP_ADDR "192.168.43.136"
#define PORT 3333
#define TAG "WIFI"

char payload[7];
char rx_buffer[128];
char addr_str[128];
int addr_family;
int ip_protocol;
struct sockaddr_in dest_addr;
int sock;

/*******************************************************
 *                Variable Definitions
 *******************************************************/
bool is_running_rule = false;

static bool s_light_inited = false;

static bool rule_ble = false;

int level = 1;

/*******************************************************
 *                Function Definitions Light
 *******************************************************/
void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_array.pin != pin) {
        ESP_LOGE("LED", "LED is not found!");
        return;
    }

    if (status_led == led_array.previous) {
        ESP_LOGW("LED", "led %s is already %s",
                 led_array.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_array.previous = status_led;
}

void test_LED(void) {
    //---------------------------------------- TEST 1 second
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_ON);
    gpio_set_level(LED_BLE, LED_ON);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_OFF);
    gpio_set_level(LED_BLE, LED_OFF);
    //---------------------------------------- TEST 1 second
}

esp_err_t mesh_light_init(void) {
    if (s_light_inited == true) {
        return ESP_OK;
    }
    s_light_inited = true;

    gpio_pad_select_gpio(LED_BLE);
    gpio_set_direction(LED_BLE, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_BLE, LED_OFF);

    gpio_pad_select_gpio(LED_WIFI);
    gpio_set_direction(LED_WIFI, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_WIFI, LED_OFF);

    test_LED();

    return ESP_OK;
}

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
void wifi_led(uint8_t pin, uint8_t status_led) {
    gpio_set_level(pin, status_led);
}

void create_socket() {
    dest_addr.sin_addr.s_addr = inet_addr(HOST_IP_ADDR);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(PORT);
    addr_family = AF_INET;
    ip_protocol = IPPROTO_IP;
    inet_ntoa_r(dest_addr.sin_addr, addr_str, sizeof(addr_str) - 1);
    while (1) {
        sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
        }
        ESP_LOGI(TAG, "Socket created, sending to %s:%d", HOST_IP_ADDR, PORT);
        break;
    }
    wifi_led(LED_WIFI, LED_OFF);
    is_running_rule = true;
}

void send_mex_wifi(int16_t value) {
    sprintf(payload, "%d", value);
    int err = sendto(sock, payload, strlen(payload), 0, (struct sockaddr *) &dest_addr, sizeof(dest_addr));
    if (err < 0) {
        ESP_LOGE("PC-WiFi", "[status: W, level: %s ]", payload);
    } else {
        ESP_LOGI("PC-WiFi", "[status: I, level: %s ]", payload);
    }
}

static void send_mex_udp_ble(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xDelay = 10 * 1000 / portTICK_PERIOD_MS;

    vTaskDelay(20 * 1000 / portTICK_PERIOD_MS);

    while (is_running_rule) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        if (rule_ble) {
            send_message_BLE(4, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level, 0);
        } else {
            send_mex_wifi(level);
        }

        if (level % 10 == 0) {
            rule_ble = !rule_ble;
            printf("Change Technology\n");
        }

        level += 1;
    }

    vTaskDelete(NULL);
}

static void udp_client_receive(void *pvParameters) {
    struct sockaddr_in source_addr; // Large enough for both IPv4 or IPv6
    socklen_t socklen = sizeof(source_addr);

    while (is_running_rule) {
        int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer) - 1, 0, (struct sockaddr *) &source_addr, &socklen);

        // Error occurred during receiving
        if (len < 0) {
            ESP_LOGE(TAG, "recvfrom failed: errno %d", errno);
        } else {
            rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string
            ESP_LOGW("PC-WiFi", "[status: O, level: %s ]", rx_buffer);
        }
    }
    if (sock != -1) {
        ESP_LOGE(TAG, "Shutting down socket and restarting...");
        shutdown(sock, 0);
        close(sock);
    }

    vTaskDelete(NULL);
}

void board_init(void) {
    tcpip_adapter_init();
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    create_socket();

    xTaskCreate(udp_client_receive, "udp_receive", 2048, NULL, 2, NULL);
    xTaskCreate(send_mex_udp_ble, "udp_ble_sent", 2048, NULL, 2, NULL);
}
