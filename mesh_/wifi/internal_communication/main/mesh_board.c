//
// Created by emilio on 11/01/20.
//

#include <stdio.h>
#include "string.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"
#include "esp_err.h"
#include "esp_mesh.h"

#include "mesh_board.h"

#include "driver/uart.h"
#include "soc/uart_struct.h"

#define TAG "uart_events"


/*******************************************************
 *                Variable Definitions
 *******************************************************/
static bool s_light_inited = false;

static bool is_running = true;

extern uint8_t data_tx;

struct _led_state led_array = {LED_OFF, LED_OFF, LED_BLUETOOTH, "ble_mesh"};

extern void emilio_tx(void);

/*******************************************************
 *                Function Definitions Light
 *******************************************************/
esp_err_t mesh_light_init(void) {
    if (s_light_inited == true) {
        return ESP_OK;
    }
    s_light_inited = true;

    gpio_pad_select_gpio(LED_BLUETOOTH);
    gpio_set_direction(LED_BLUETOOTH, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_BLUETOOTH, LED_OFF);

    gpio_pad_select_gpio(LED_WIFI);
    gpio_set_direction(LED_WIFI, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_WIFI, LED_OFF);
    return ESP_OK;
}

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
            printf("Turning on the LED\n");
            gpio_set_level(LED_WIFI, LED_ON);
        } else {
            printf("Turning off the LED\n");
            gpio_set_level(LED_WIFI, LED_OFF);
        }
    }
    return ESP_OK;
}

void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_array.pin != pin) {
        ESP_LOGE(TAG, "LED is not found!");
        return;
    }

    if (status_led == led_array.previous) {
        ESP_LOGW(TAG, "Led %s is already %s",
                 led_array.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_array.previous = status_led;
}

/*******************************************************
 *                Function Definitions UART
 *******************************************************/
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

            fflush(stdout);
            uart_flush_input(uart_num);

            //Write data back to UART
            //uart_write_bytes(uart_num, (const char *) data_uart, len);
            vTaskDelay(10);
            emilio_tx();
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

/*******************************************************
 *                Function Definitions Semaphore
 *******************************************************/
SemaphoreHandle_t xSemaphore = NULL;

// Interrupt service routine, called when the button is pressed
void IRAM_ATTR gpio_isr_handler(void *arg) {
    // notify the button task
    xSemaphoreGiveFromISR(xSemaphore, NULL);
}

void semaphore_task(void *arg) {
    is_running = true;
    while (is_running) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY) == pdTRUE) {
            data_tx++;
            emilio_tx();
        }
    }
}

void semaphore_init(void) {
    printf("- %s\n", __func__);
    //Create the binary semaphore
    xSemaphore = xSemaphoreCreateBinary();
    // Enable interrupt on falling (Fronte di discesa, ovvero quando si passa 1->0) edge for button pin
    gpio_set_intr_type(2, GPIO_INTR_NEGEDGE);
    // start the task that will handle the button
    xTaskCreate(semaphore_task, "semaphore_task", 3072, NULL, 5, NULL);

    // install ISR service with default configuration
    gpio_install_isr_service(0);

    //attach the interrupt service routine
    gpio_isr_handler_add(2, gpio_isr_handler, NULL);
    // alla pressione del tasto viene eseguita la funzione  button_isr_handler(void* arg)
}