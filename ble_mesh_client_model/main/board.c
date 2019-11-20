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
#include "freertos/event_groups.h"

#include "esp_log.h"

#include "esp_ble_mesh_provisioning_api.h"
#include "board.h"
#include "freertos/semphr.h"

#define TAG "BOARD"
#define SIZE_LEDS 6


extern uint16_t remote_addr;

struct _led_state led_state[3] = {
        {LED_OFF, LED_OFF, LED_R, "red"},
        {LED_OFF, LED_OFF, LED_G, "green"},
        {LED_OFF, LED_OFF, LED_B, "blue"},
};

void board_output_number(esp_ble_mesh_output_action_t action, uint32_t number) {
    ESP_LOGI(TAG, "Board output number %d", number);
}

void board_prov_complete(void) {
    board_led_operation(LED_G, LED_OFF);
}

void board_led_operation(uint8_t pin, uint8_t onoff) {
    for (int i = 0; i < ARRAY_SIZE(led_state); i++) {
        if (led_state[i].pin != pin) {
            continue;
        }
        if (onoff == led_state[i].previous) {
            ESP_LOGW(TAG, "led %s is already %s",
                     led_state[i].name, (onoff ? "on" : "off"));
            return;
        }
        gpio_set_level(pin, onoff);
        led_state[i].previous = onoff;
        return;
    }
    ESP_LOGE(TAG, "LED is not found!");
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
    uint32_t leds[SIZE_LEDS] = {3, 4, 5, 6, 7, 8};
    uint8_t index = 0;

    while (1) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE) {
            remote_addr = leds[index] & 0xFFFF;
            printf("%s: Define remote_addr! input: %u, remote address: %hu\n", __func__, leds[index], remote_addr);
            if (index == SIZE_LEDS - 1) index = 0; else index++;
        }
    }
}

static void board_emilio_init() {
    //Create the binary semaphore
    xSemaphore = xSemaphoreCreateBinary();
    // Enable interrupt on falling (Fronte di discesa, ovvero quando si passa 1->0) edge for button pin
    gpio_set_intr_type(BUTTON_PIN, GPIO_INTR_NEGEDGE);
    // start the task that will handle the button
    xTaskCreate(board_emilio_task, "board_emilio_task", 2048, NULL, 10, NULL);

    // install ISR service with default configuration
    gpio_install_isr_service(ESP_INTR_FLAG_DEFAULT);

    //attach the interrupt service routine
    gpio_isr_handler_add(BUTTON_PIN, gpio_isr_handler, NULL);
    // alla pressione del tasto viene eseguita la funzione  button_isr_handler(void* arg)
}

static void board_led_init(void) {
    for (int i = 0; i < ARRAY_SIZE(led_state); i++) {
        gpio_pad_select_gpio(led_state[i].pin);
        gpio_set_direction(led_state[i].pin, GPIO_MODE_OUTPUT);
        gpio_set_level(led_state[i].pin, LED_OFF);
        led_state[i].previous = LED_OFF;
    }
}


void board_init(void) {
    board_led_init();
    board_emilio_init();
    printf("------ %s ------", __func__);
}
