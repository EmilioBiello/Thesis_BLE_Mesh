//
// Created by emilio on 11/01/20.
//

#include <stdio.h>
#include "string.h"
#include <stddef.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"
#include "esp_err.h"
#include "esp_mesh.h"

#include "include/mesh_board.h"

#include "driver/uart.h"
#include "soc/uart_struct.h"

#define TAG "uart_events"

extern void send_message(uint16_t addr, uint32_t opcode, int16_t level, bool ack);

struct _led_state led_array = {LED_OFF, LED_OFF, LED_BLE, "ble_mesh"};

extern void emilio_tx(int16_t data_tx);

/*******************************************************
 *                Variable Definitions
 *******************************************************/
struct Rule_Message {
    uint16_t n_mex_s;
    uint8_t addr_s;
    uint16_t delay_s;
    bool ack_s;
} m1;

struct Message_Set {
    uint8_t addr_s;
    uint16_t level_s;
    uint32_t opcode_s;
    bool ack_s;
} m2;

static bool s_light_inited = false;

static bool is_running = true;

char *command;

/*******************************************************
 *                Function Definitions Light
 *******************************************************/
void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_array.pin != pin) {
        ESP_LOGE(TAG, "LED is not found!");
        return;
    }

    if (status_led == led_array.previous) {
        ESP_LOGW(TAG, "led %s is already %s",
                 led_array.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_array.previous = status_led;
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

    //---------------------------------------- TEST 1 second
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_ON);
    gpio_set_level(LED_BLE, LED_ON);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_OFF);
    gpio_set_level(LED_BLE, LED_OFF);
    //---------------------------------------- TEST 1 second

    return ESP_OK;
}

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
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

esp_err_t mesh_light_process(mesh_addr_t *from, uint8_t *buf, uint16_t len) {
    mesh_light_ctl_t *in = (mesh_light_ctl_t *) buf;
    if (!from || !buf || len < sizeof(mesh_light_ctl_t)) {
        return ESP_FAIL;
    }
    if (in->token_id != MESH_TOKEN_ID || in->token_value != MESH_TOKEN_VALUE) {
        return ESP_FAIL;
    }
    if (in->cmd == MESH_CONTROL_CMD) {
        if (in->on) {
            printf("Turning on the LED WIFI\n");
            gpio_set_level(LED_WIFI, LED_ON);
        } else {
            printf("Turning off the LED WIFI\n");
            gpio_set_level(LED_WIFI, LED_OFF);
        }
    }
    return ESP_OK;
}

/*******************************************************
 *                Function Definitions Command
 *******************************************************/
void decoding_string(char tokens0, char *token1, char *token2, char *token3) {
    char **t1_char = str_split(token1, ':');
    char **t2_char = str_split(token2, ':');
    char **t3_char = str_split(token3, ':');

    if (tokens0 == '@') {
        m2.addr_s = strtoul((const char *) t1_char[1], NULL, 16);
        m2.level_s = strtoul((const char *) t2_char[1], NULL, 10);
        if (strcmp(t3_char[0], "unack") == 0) {
            m2.opcode_s = ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK;
            m2.ack_s = 0;
        } else {
            m2.opcode_s = ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET;
            m2.ack_s = strtoul((const char *) t3_char[1], NULL, 2);
        }
    } else if (tokens0 == '&') {
        m1.n_mex_s = strtoul((const char *) t1_char[1], NULL, 10);
        m1.addr_s = strtoul((const char *) t2_char[1], NULL, 16);
        m1.delay_s = strtoul((const char *) t3_char[1], NULL, 10);
        m1.ack_s = 0;
    }

    free(t1_char);
    free(t2_char);
    free(t3_char);
}

void command_received(char **tokens, int count) {
    count = count - 2;
    switch (tokens[0][0]) {
        case '#': {
            char **t1_char = str_split(tokens[1], ':');
            uint16_t level = strtoul((const char *) t1_char[1], NULL, 10);
            emilio_tx(level);
            printf("WIFI send mex\n");
        }
            break;
        case '@':
            if (count == 2) {
                decoding_string('@', tokens[1], tokens[2], "unack");
                send_message(m2.addr_s, m2.opcode_s, m2.level_s, false);
                ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
            } else if (count == 3) {
                decoding_string('@', tokens[1], tokens[2], tokens[3]);
                send_message(m2.addr_s, m2.opcode_s, m2.level_s, m2.ack_s);
                ESP_LOGI("SEND_MESSAGE", "SET");
            }
            printf("BLE send mex\n");
            break;
        default:
            printf("Comando Errato\n");
            break;
    }
}


/*******************************************************
 *                Function Definitions UART
 *******************************************************/
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

static void uart_task(void *args) {
    const int uart_num = UART_NUM_1;
    uart_config_t uart_config = {
            .baud_rate = 115200,
            .data_bits = UART_DATA_8_BITS,
            .parity = UART_PARITY_DISABLE,
            .stop_bits = UART_STOP_BITS_1,
            .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
            .rx_flow_ctrl_thresh = 122,
    };

    //Configure UART1 parameters
    uart_param_config(uart_num, &uart_config);
    //Set UART1 pins(TX: IO4, RX: I05)
    uart_set_pin(uart_num, ECHO_TEST_TXD, ECHO_TEST_RXD, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    //Install UART driver (we don't need an event queue here)
    //In this example we don't even use a buffer for sending data.
    uart_driver_install(uart_num, BUF_SIZE * 2, 0, 0, NULL, 0);

    printf("*** UART init\n");

    uint8_t *data_uart = (uint8_t *) malloc(BUF_SIZE);
    is_running = true;

    while (is_running) {
        //Read data from UART
        int len = uart_read_bytes(uart_num, data_uart, BUF_SIZE, 1000 / portTICK_RATE_MS);
        if (len > 0) {
            data_uart[len] = '\0';
            ESP_LOGI("UART", "Read %d bytes: '%s'", len, data_uart);

            size_t count = count_tokens((char *) data_uart, ',');
            char **tokens = str_split((char *) data_uart, ',');
            command_received(tokens, count);

            fflush(stdout);
            uart_flush_input(uart_num);
        }
    }
}

void uart_trasmitting(const char *test_str) {
    const int len = strlen(test_str);
    const int txBytes = uart_write_bytes(UART_NUM_1, test_str, len);
    ESP_LOGI("UART_TX", "Wrote %d bytes", txBytes);
}

void uart_init(void) {
    printf("- %s\n", __func__);
    xTaskCreate(uart_task, "uart_task", 3072, NULL, 4, NULL);
}