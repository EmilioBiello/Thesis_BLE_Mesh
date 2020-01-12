//
// Created by emilio on 11/01/20.
//

#include <stdio.h>
#include "string.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"

#include "board.h"

#include "driver/uart.h"
#include "soc/uart_struct.h"

#define TAG "uart_events"


#define BUF_SIZE (1024)
#define ECHO_TEST_TXD (GPIO_NUM_23)
#define ECHO_TEST_RXD (GPIO_NUM_22)

static bool is_running = true;

struct _led_state led_state = {LED_OFF, LED_OFF, LED_G, "green"};

extern void emilio_tx(uint8_t index);

extern uint8_t data_tx;

/**
 * MY FUNCTION
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

void command_received() {
    emilio_tx(0);
}

/**
 * LED
 */

static void board_led_init(void) {
    gpio_pad_select_gpio(led_state.pin);
    gpio_set_direction(led_state.pin, GPIO_MODE_OUTPUT);
    gpio_set_level(led_state.pin, LED_OFF);
    led_state.previous = LED_OFF;
}

void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_state.pin != pin) {
        ESP_LOGE(TAG, "LED is not found!");
        return;
    }

    if (status_led == led_state.previous) {
        ESP_LOGW(TAG, "Led %s is already %s",
                 led_state.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_state.previous = status_led;
}

/**
 * UART
 */
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

    printf("UART init\n");

    uint8_t *data_uart = (uint8_t *) malloc(BUF_SIZE);
    uint32_t input;
    is_running = true;

    while (is_running) {
        //Read data from UART
        int len = uart_read_bytes(uart_num, data_uart, BUF_SIZE, 1000 / portTICK_RATE_MS);
        if (len > 0) {
            data_uart[len] = '\0';
            ESP_LOGI("UART", "Read %d bytes: '%s'", len, data_uart);

            input = strtoul((const char *) data_uart, NULL, 10);
            data_tx = input & 0xFFFF;

            //Write data back to UART
            //uart_write_bytes(uart_num, (const char *) data_uart, len);
            vTaskDelay(1);
            ESP_LOGI("UART", "Input: [0x%08x - %d] Data Received: [0x%04x - %d]", input, input, data_tx, data_tx);
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

/**
 * Init
 */
void board_init(void) {
    board_led_init();
    //A uart read/write example without event queue;
    xTaskCreate(uart_task, "uart_task", 1024, NULL, 5, NULL);
}