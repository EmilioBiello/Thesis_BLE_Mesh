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

#include "driver/uart.h"
#include "esp_log.h"
#include "assert.h"

#include "board.h"

#define TAG "BOARD"

extern void send_message(uint16_t addr, uint32_t opcode, int16_t level, bool ack);

struct _led_state led_state = {LED_OFF, LED_OFF, LED_G, "green"};

void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_state.pin != pin) {
        ESP_LOGE(TAG, "LED is not found!");
        return;
    }

    if (status_led == led_state.previous) {
        ESP_LOGW(TAG, "led %s is already %s",
                 led_state.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_state.previous = status_led;
}

static void board_led_init(void) {
    gpio_pad_select_gpio(led_state.pin);
    gpio_set_direction(led_state.pin, GPIO_MODE_OUTPUT);
    gpio_set_level(led_state.pin, LED_OFF);
    led_state.previous = LED_OFF;
}

/**
 *  Button
 */

// Utilizzo semaforo per gestire l'evento legato al bottone
SemaphoreHandle_t xSemaphore = NULL;

// Interrupt service routine, called when the button is pressed
void IRAM_ATTR gpio_isr_handler(void *arg) {
    // notify the button task
    xSemaphoreGiveFromISR(xSemaphore, NULL);
}

static void board_emilio_task(void *p) {
    int16_t level = 1;
    bool cycle = true;

    const TickType_t xDelay = (10 * 1000) / portTICK_PERIOD_MS;
    printf("BOARD --- init --- \n");
    vTaskDelay(30 * 1000 / portTICK_PERIOD_MS);

    printf("BOARD --- start --- \n");
    TickType_t xLastWakeTime = xTaskGetTickCount();
    while (cycle) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message(4, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level, 0);
        ESP_LOGI("SEND_MESSAGE", "SET_UNACK -> %d", level);
        level += 1;
    }
    vTaskDelete(NULL);
}
void board_rule_init(){
    xTaskCreate(board_emilio_task, "board_emilio_task", 2048, NULL, 5, NULL);
}


void board_init(void) {
    board_led_init();
}
