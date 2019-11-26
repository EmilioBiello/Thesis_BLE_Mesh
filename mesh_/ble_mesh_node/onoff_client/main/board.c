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

#include "iot_button.h"
#include "board.h"
#include "assert.h"

#define TAG "BOARD"

#define BUTTON_IO_NUM           2
#define  ESP_INTR_FLAG_DEFAULT 0

#define UART_BUF_SIZE (128)
#define TXD_PIN (GPIO_NUM_23)
#define RXD_PIN (GPIO_NUM_22)

extern void example_ble_mesh_send_gen_onoff_set(void);

extern uint8_t send_message_unack(uint16_t, uint32_t);

extern void send_message(uint16_t, uint32_t, uint8_t);

extern bool get_info_provisioning(void);

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
 * Utilizzo UART
 */
void uart_init() {
    uart_config_t uart_config = {
            .baud_rate = 115200,
            .data_bits = UART_DATA_8_BITS,
            .parity = UART_PARITY_DISABLE,
            .stop_bits = UART_STOP_BITS_1,
            .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };

    uart_param_config(UART_NUM_1, &uart_config);
    uart_set_pin(UART_NUM_1, TXD_PIN, RXD_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_NUM_1, UART_BUF_SIZE * 2, 0, 0, NULL, 0);
}

int writeData(const char *logName, const char *data) {
    const int len = strlen(data);
    const int txBytes = uart_write_bytes(UART_NUM_1, data, len);
    ESP_LOGI(logName, "Wrote %d bytes", txBytes);
    return txBytes;
}

char **str_split(char *a_str, const char a_delim) {
    char **result = 0;
    size_t count = 0;
    char *tmp = a_str;
    char *last_comma = 0;
    char delim[2];
    delim[0] = a_delim;
    delim[1] = 0;

    /* Count how many elements will be extracted. */
    while (*tmp) {
        if (a_delim == *tmp) {
            count++;
            last_comma = tmp;
        }
        tmp++;
    }
    /* Add space for trailing token. */
    count += last_comma < (a_str + strlen(a_str) - 1);

    /* Add space for terminating null string so caller
       knows where the list of returned strings ends. */
    count++;

    result = malloc(sizeof(char *) * count);

    if (result) {
        size_t idx = 0;
        char *token = strtok(a_str, delim);

        while (token) {
            assert(idx < count);
            *(result + idx++) = strdup(token);
            token = strtok(0, delim);
        }
        assert(idx == count - 1);
        *(result + idx) = 0;
    }
    return result;
}

void set_message(char **tokens) {
    /** remote_addr:3,status:{0,1},opcode:{1,2,3}**/
    char **remote_addr_char = str_split(tokens[0], ':');
    char **status_char = str_split(tokens[1], ':');
    char **opcode_char = str_split(tokens[2], ':');

    uint16_t remote_addr = strtoul((const char *) remote_addr_char[1], NULL, 16);
    uint8_t status = strtoul((const char *) status_char[1], NULL, 16);
    uint32_t opcode = strtoul((const char *) opcode_char[1], NULL, 16);

    free(remote_addr_char);
    free(status_char);
    free(opcode_char);

    // (remote_addr > 0x0002 && remote_addr <= 0xFFFF) &&
    if (get_info_provisioning()) {
        switch (opcode) {
            case 1:
                ESP_LOGI("SEND_MESSAGE", "GET");
                //send_message(remote_addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_GET, status);
                break;
            case 2:
                ESP_LOGI("SEND_MESSAGE", "SET");
                send_message(remote_addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET, status);
                break;
            case 3:
                ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
                send_message(remote_addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET_UNACK, status);
                break;
            default:
                break;
        }
        ESP_LOGI("SEND_MESSAGE", "[addr: 0x%04x, status: %d, opcode: %d]", remote_addr, status, opcode);
    } else {
        ESP_LOGE("MESSAGE", "Node not provisioned or Address not in range");
    }
}

static void uart_task(void *args) {
    static const char *RX_TASK_TAG = "RX_TASK";
    esp_log_level_set(RX_TASK_TAG, ESP_LOG_INFO);

    uint8_t *data = calloc(1, UART_BUF_SIZE);


    while (1) {
        //Read data from the UART
        int len = uart_read_bytes(UART_NUM_1, data, UART_BUF_SIZE, 100 / portTICK_RATE_MS);

        if (len > 0) {
            printf("-------------\n");
            data[len] = 0;
            ESP_LOGI(RX_TASK_TAG, "Read %d bytes: '%s'", len, data);
            ESP_LOG_BUFFER_HEXDUMP(RX_TASK_TAG, data, len, ESP_LOG_INFO);

            char **tokens = str_split((char *) data, ',');
            set_message(tokens);

            //writeData("SEND_DATA", "Ciao mondo!\n");
            memset(data, 0, UART_BUF_SIZE);
            printf("-------------\n");
        }
    }
    vTaskDelete(NULL);
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
    uint16_t remote_array[4] = {0xFFFF, 0xC001, 0x0003, 0x0004};
    uint8_t index = 0;
    bool onoff = false;
    while (1) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE) {
            printf("Send Message:\n");
            //send_ble_set(ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET, remote_address);
            board_led_operation(LED_G,
                                send_message_unack(remote_array[index], ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET_UNACK));
            if (onoff) {
                onoff = false;
                (index == 3 ? index = 0 : index++);
            } else
                onoff = true;
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

    uart_init();
    xTaskCreate(uart_task, "uart_task", 2048, NULL, 5, NULL);
}
