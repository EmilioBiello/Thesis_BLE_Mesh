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

#include "driver/uart.h"
#include "assert.h"

#define TAG "BOARD"

#define UART_BUF_SIZE (128)
#define TXD_PIN (GPIO_NUM_23)
#define RXD_PIN (GPIO_NUM_22)

extern void send_message(uint16_t addr, uint32_t opcode, int16_t level);

extern void send_get_message(uint16_t addr);

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

void send_data_to_pc(const char *data) {
    const int len = strlen(data);
    uart_write_bytes(UART_NUM_1, data, len);
}

void create_message_rapid(char *opcode, char *level) {
    char *str3 = malloc(1 + 1 + strlen(opcode) + strlen(level));// 1 end char; 1 for comma

    strcpy(str3, opcode);
    strcat(str3, ",");
    strcat(str3, level);

    send_data_to_pc(str3);
    free(str3);
    ESP_LOGI("PC", "[opcode: %s, level: %s]", opcode, level);
}

uint8_t count_tokens(char *a_str, const char a_delim) {
    size_t count = 0;
    char *tmp = a_str;
    char *last_comma = 0;
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

    return count;
}

char **str_split(char *a_str, const char a_delim) {
    char **result = 0;
    size_t count = 0;
    char delim[2];
    delim[0] = a_delim;
    delim[1] = 0;

    count = count_tokens(a_str, a_delim);

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

void execute_rule(uint16_t n_mex, uint8_t addr, uint16_t delay) {
    int16_t level = 1;
    char level_c[16];
    const TickType_t xDelay = delay / portTICK_PERIOD_MS;
    printf("DELAY: %d\n", xDelay);

    for (int i = 0; i < n_mex; ++i) {
        send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET, level);
        sprintf(level_c, "%d", level);

        create_message_rapid("S", (char *) level_c);
        level += 1;
        vTaskDelay(xDelay); // delay is milliseconds
    }
}

void config_rule(char *n_mex_c, char *addr_c, char *delay_c) {
    char **n_mex_char = str_split(n_mex_c, ':');
    char **addr_char = str_split(addr_c, ':');
    char **delay_char = str_split(delay_c, ':');

    uint16_t n_mex = strtoul((const char *) n_mex_char[1], NULL, 10);
    uint8_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    uint16_t delay = strtoul((const char *) delay_char[1], NULL, 10);

    printf("n_mex: %hu\n", n_mex);
    printf("addr: %hhu\n", addr);
    printf("delay: %u\n", delay);

    free(n_mex_char);
    free(addr_char);
    free(delay_char);

    execute_rule(n_mex, addr, delay);
}

void config_single_mex_set(char *addr_c, char *level_c, char *opcode_c) {
    char **addr_char = str_split(addr_c, ':');
    char **level_char = str_split(level_c, ':');
    char **opcode_char = str_split(opcode_c, ':');

    uint16_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    int16_t level = strtoul((const char *) level_char[1], NULL, 10);
    uint32_t opcode = strtoul((const char *) opcode_char[1], NULL, 10);

    printf("addr: %hu\n", addr);
    printf("level: %hd\n", level);
    printf("opcode: %u\n", opcode);

    if (opcode == 2) {
        ESP_LOGI("SEND_MESSAGE", "SET");
        send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET, level);
    } else if (opcode == 3) {
        ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
        send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level);
    }

    free(addr_char);
    free(level_char);
    free(opcode_char);
}

void config_single_mex_get(char *addr_c) {
    char **addr_char = str_split(addr_c, ':');

    uint16_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    printf("addr: %hu\n", addr);

    send_get_message(addr);

    free(addr_char);
}

void command_received(char **tokens, int count) {
    count = count - 2;
    printf("First char: %c, count: %d\n", tokens[0][0], count);
    switch (tokens[0][0]) {
        case '#':
            //config_my_log(tokens[1]);
            printf("LOG\n");
            break;

        case '@':
            if (count == 1) {
                config_single_mex_get(tokens[1]);
                printf("GET\n");
            } else if (count == 3) {
                //config_single_mex_set(tokens[1], tokens[2], tokens[3]);
                printf("SET\n");
            }
            printf("Single_mex\n");
            break;

        case '&':
            config_rule(tokens[1], tokens[2], tokens[3]);
            printf("Rule\n");
            break;

        default:
            printf("Errore\n");
            break;
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
            //ESP_LOG_BUFFER_HEXDUMP(RX_TASK_TAG, data, len, ESP_LOG_INFO);

            size_t count = count_tokens((char *) data, ',');
            char **tokens = str_split((char *) data, ',');
            command_received(tokens, count);

            memset(data, 0, UART_BUF_SIZE);
            printf("-------------\n");
        }
    }
    vTaskDelete(NULL);
}

/**
 * Init
 */
void board_init(void) {
    board_led_init();

    uart_init();
    xTaskCreate(uart_task, "uart_task", 2048, NULL, 5, NULL);
}
