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

#include "esp_log.h"

#include "board.h"


#define TAG "BOARD"

#define BUTTON_IO_NUM           2
#define  ESP_INTR_FLAG_DEFAULT 0


extern uint8_t send_message(uint16_t addr, uint32_t opcode, int16_t level);

struct _led_state led_state = {LED_OFF, LED_OFF, LED_G, "green"};

void board_led_operation(uint8_t pin, uint8_t onoff) {
    if (led_state.pin != pin) {
        ESP_LOGE(TAG, "LED is not found!");
        return;
    }

    if (onoff == led_state.previous) {
        ESP_LOGW(TAG, "led %s is already %s",
                 led_state.name, (onoff ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, onoff);
    led_state.previous = onoff;
}

static void board_led_init(void) {
    gpio_pad_select_gpio(led_state.pin);
    gpio_set_direction(led_state.pin, GPIO_MODE_OUTPUT);
    gpio_set_level(led_state.pin, LED_OFF);
    led_state.previous = LED_OFF;
}

/**
 * Utilizzo semaforo per gestire l'evento legato al bottone
 */
SemaphoreHandle_t xSemaphore = NULL;

// Interrupt service routine, called when the button is pressed
void IRAM_ATTR gpio_isr_handler(void *arg) {
    // notify the button task
    xSemaphoreGiveFromISR(xSemaphore, NULL);
}

static void board_emilio_task(void *p) {
    int level = INT_MAX;
    uint8_t addr = 0x0003;
    while (1) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE) {
            printf("Send Message:\n");
            printf("Level: %d", level);
            //send_ble_set(ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET, remote_address);
            board_led_operation(LED_G, send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level));
        }
    }
}

static void board_emilio_init() {
    //Create the binary semaphore
    xSemaphore = xSemaphoreCreateBinary();
    // Enable interrupt on falling (Fronte di discesa, ovvero quando si passa 1->0) edge for button pin
    gpio_set_intr_type(BUTTON_IO_NUM, GPIO_INTR_NEGEDGE);
    // start the task that will handle the button
    xTaskCreate(board_emilio_task, "board_emilio_task", 2048, NULL, 10, NULL);

    // install ISR service with default configuration
    gpio_install_isr_service(ESP_INTR_FLAG_DEFAULT);

    //attach the interrupt service routine
    gpio_isr_handler_add(BUTTON_IO_NUM, gpio_isr_handler, NULL);
    // alla pressione del tasto viene eseguita la funzione  button_isr_handler(void* arg)
}

void board_init(void) {
    board_led_init();
    board_emilio_init();
}
