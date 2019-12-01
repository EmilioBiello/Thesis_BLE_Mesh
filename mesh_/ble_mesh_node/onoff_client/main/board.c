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

extern uint8_t send_message(uint16_t, uint32_t, uint8_t);

extern void send_get_message(uint16_t addr);

extern bool get_info_provisioning(void);

extern bool my_log;

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

void send_data_to_pc(const char *data) {
    const int len = strlen(data);
    uart_write_bytes(UART_NUM_1, data, len);
}

void create_message_pc(char *addr, char *status, char *opcode, char *m_id) {
    char *str3 = malloc(1 + 4 + strlen(addr) + strlen(status) + strlen(opcode) + strlen(m_id));

    strcpy(str3, "-");
    strcat(str3, addr);
    strcat(str3, ",");
    strcat(str3, status);
    strcat(str3, ",");
    strcat(str3, opcode);
    strcat(str3, ",");
    strcat(str3, m_id);

    send_data_to_pc(str3);
    free(str3);
    ESP_LOGI("LOG", "[addr: %s, status: %s, opcode: %s, id: %s]", addr, status, opcode, m_id);
}

void create_message_rapid(char *opcode, char *m_id) {
    char *str3 = malloc(1 + 1 + strlen(opcode) + strlen(m_id));// 1 end char; 1 for comma

    strcpy(str3, opcode);
    strcat(str3, ",");
    strcat(str3, m_id);

    send_data_to_pc(str3);
    free(str3);
    ESP_LOGI("PC", "[opcode: %s, id: %s]", opcode, m_id);
}

void register_received_message(uint16_t addr, uint8_t status, uint32_t opcode) {
    char addr_c[10];
    char opcode_c[10];
    char status_c[10];
    sprintf(addr_c, "%d", addr);
    sprintf(opcode_c, "%d", opcode);
    sprintf(status_c, "%d", status);
    create_message_pc(addr_c, status_c, opcode_c, "-");
}

/**
 * Conta il numero di virgole presenti nella regola ricevuta e aggiunge 2 valori in più per end char
 * @param a_str
 * @param a_delim
 * @return
 */
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

void config_my_log(char *tokens) {
    char **log_char = str_split(tokens, ':');
    my_log = strtoul((const char *) log_char[1], NULL, 2) == 1;
    free(log_char);
}

void execute_rule(uint16_t n_mex, uint8_t addr, uint8_t delay) {
    uint8_t status = 1;
    uint8_t m_id = 0;
    char id_c[8];
    char addr_c[8];
    sprintf(addr_c, "%d", addr);

    for (int i = 0; i < n_mex; ++i) {
        //printf("[addr: %hhu, status: %hhu, opcode: SET, id: %d]\n", addr, status, i);

        m_id = send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET, status);
        sprintf(id_c, "%d", m_id);

        create_message_rapid("SET", (char *) id_c);

        if (status == 0) {
            status = 1;
        } else {
            status = 0;
        }
        vTaskDelay(delay * 1000 / portTICK_PERIOD_MS);
    }
}

void config_rule(char *n_mex_c, char *addr_c, char *delay_c) {
    char **n_mex_char = str_split(n_mex_c, ':');
    char **addr_char = str_split(addr_c, ':');
    char **delay_char = str_split(delay_c, ':');

    uint16_t n_mex = strtoul((const char *) n_mex_char[1], NULL, 10);
    uint8_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    uint32_t delay = strtoul((const char *) delay_char[1], NULL, 10);

    printf("n_mex: %hu\n", n_mex);
    printf("addr: %hhu\n", addr);
    printf("delay: %u\n", delay);

    free(n_mex_char);
    free(addr_char);
    free(delay_char);

    execute_rule(n_mex, addr, delay);
}

void config_single_mex_set(char *addr_c, char *status_c, char *opcode_c) {
    char **addr_char = str_split(addr_c, ':');
    char **status_char = str_split(status_c, ':');
    char **opcode_char = str_split(opcode_c, ':');

    uint16_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    uint8_t status = strtoul((const char *) status_char[1], NULL, 10);
    uint32_t opcode = strtoul((const char *) opcode_char[1], NULL, 10);

    printf("addr: %hu\n", addr);
    printf("status: %hhu\n", status);
    printf("opcode: %u\n", opcode);

    if (get_info_provisioning()) {
        uint8_t m_id = 0;
        if (opcode == 2) {
            ESP_LOGI("SEND_MESSAGE", "SET");
            m_id = send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET, status);
        } else if (opcode == 3) {
            ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
            m_id = send_message(addr, ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET_UNACK, status);
        }

        if (my_log) {
            char id[10];
            sprintf(id, "%d", m_id);
            create_message_pc(addr_char[1], status_char[1], opcode_char[1], (char *) id);
        }
    } else {
        ESP_LOGE("MESSAGE", "Node not provisioned or Address not in range");
    }

    free(addr_char);
    free(status_char);
    free(opcode_char);
}

void config_single_mex_get(char *addr_c) {
    char **addr_char = str_split(addr_c, ':');

    uint16_t addr = strtoul((const char *) addr_char[1], NULL, 16);
    printf("addr: %hu\n", addr);

    if (get_info_provisioning()) {
        send_get_message(addr);
        if (my_log) {
            create_message_pc(addr_char[1], "1", "1", "0");
        }
    }

    free(addr_char);
}

void find_strarted_char(char **tokens, int count) {
    count = count - 2;
    printf("First char: %c, count: %d\n", tokens[0][0], count);
    switch (tokens[0][0]) {
        case '#':
            config_my_log(tokens[1]);
            printf("LOG\n");
            break;

        case '@':
            if (count == 1) {
                config_single_mex_get(tokens[1]);
                printf("GET\n");
            } else if (count == 3) {
                config_single_mex_set(tokens[1], tokens[2], tokens[3]);
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
            find_strarted_char(tokens, count);

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
                                send_message_unack(remote_array[index], ESP_BLE_MESH_MODEL_OP_GEN_ONOFF_SET));
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
