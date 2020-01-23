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

#include "include/my_queue.h"

#define TAG "uart_events"

extern void send_message_BLE(uint16_t addr, uint32_t opcode, int16_t level, bool send_rel);

extern void send_mex_wifi(int16_t data_tx);

extern void define_mesh_address(int index);

struct _led_state led_array = {LED_OFF, LED_OFF, LED_BLE, "ble_mesh"};

extern void send_mex_wifi_to_all(int16_t data_tx);

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

bool running_rule = false;

struct MyQueue *q_ble;
struct MyQueue *q_wifi;

int sent_wifi;
int received_wifi;
int received_ble;
int16_t level_sent = 1;
double delay_buffer = 0;
double delay_min_buff = 0;
int delay_buff_init = 0;
bool change_delay = false;

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
void queue_operation(char operation, char tech, int key) {
    switch (operation) {
        case 'a':
            // Add mex in queue
            if (tech == 'b') {
                enQueue(q_ble, key);
                // ESP_LOGW("Q_BLE", "ADD %d", key);
            } else if (tech == 'w') {
                enQueue(q_wifi, key);
                sent_wifi += 1;
                // ESP_LOGW("Q_WIFI", "ADD %d", key);
            }
            break;
        case 'd':
            // Delete mex from queue
            if (running_rule) {
                if (tech == 'b') {
                    int value = delete_node(q_ble, key);
                    if (value > 0) {
                        // ESP_LOGW("Q_BLE", "DELETE %d", key);
                        received_ble += 1;
                    } else {
                        ESP_LOGE("DOUBLE_BLE", "Value not present in the list: [%d]\n", key);
                    }
                    update_delay_buffer(key);
                } else {
                    int value = delete_node(q_wifi, key);
                    if (value > 0) {
                        // ESP_LOGW("Q_WIFI", "DELETE %d", key);
                        received_wifi += 1;
                    }
                }
            }
            break;
        default:
            ESP_LOGE("QUEUE", "Error operation");
            break;
    }
}

void initialize_variables() {
    sent_wifi = 0;
    received_wifi = 0;
    received_ble = 0;
    running_rule = false;
    change_delay = false;
    level_sent = 1;
    delay_buffer = (40 * 1000) / m1.delay_s; // 40 seconds --> (30*1000 / DELAY) --> 600 packets
    delay_min_buff = (1 * 1000) / m1.delay_s; // delay minimo 1 s
    delay_buff_init = (int) delay_buffer;
    printf("Initial Delay: %f, min_delay: %f", delay_buffer, delay_min_buff);
    // 1 minute express and number of packets -> (1*60*1000)/ DELAY
    // [1 minute - 50 ms frequency = 1200 packet]
}

void update_delay_buffer(int key) {
    if (change_delay) {
        // TODO [Emilio] delay_1 = delay_0 + alpha*(R - delay_0)
        // TODO [Emilio] delay_1 = alpha*R + (1-alpha) * delay_0
        // TODO alpha = 0.05 --> 1-alpha = 0.95
        int diff = level_sent - key;
        double new_delay = (0.1 * diff) + (0.9 * delay_buffer);

        int last_delay = (int) delay_buffer;
        if (new_delay >= delay_min_buff && new_delay <= delay_buff_init) {
            delay_buffer = new_delay; // a <= delay <= b
        } else if (new_delay > delay_buff_init) {
            delay_buffer = delay_buff_init; // delay > b
        } else {
            delay_buffer = delay_min_buff; // delay < a
        }

        if (last_delay != (int) delay_buffer) {
            int delay = (int) delay_buffer;
            char new[7];
            sprintf(new, "%d", delay);
            create_message_rapid("T", new, "*");
            ESP_LOGE("TIME", "Change Delay: %d --> %d", last_delay, delay);
        }
    }
}

void re_send_mex() {
    int front_value = get_front_mex(q_ble);
    if (front_value > 0) {
        if ((level_sent - front_value) > (int) delay_buffer) {
            int value = deQueue(q_ble);
            send_mex_wifi(value);
            ESP_LOGE("WIFI", "SEND %d [%d - %d]", value, level_sent, front_value);
        }
    }
}

void info_test() {
    ESP_LOGE("END", "Received BLE: %d", received_ble);
    ESP_LOGE("END", "Sent wifi: %d Received wifi: %d --- diff: %d", sent_wifi, received_wifi,
             (received_wifi - sent_wifi));
    ESP_LOGE("END", "TOTALE Received: %d", (received_ble + received_wifi));

    for (int j = 0; j < 5; ++j) {
        gpio_set_level(LED_BLE, LED_ON);
        gpio_set_level(LED_WIFI, LED_ON);
        vTaskDelay(m1.delay_s / portTICK_PERIOD_MS);
        gpio_set_level(LED_BLE, LED_OFF);
        gpio_set_level(LED_WIFI, LED_OFF);
    }

    int i = empty_queue(q_ble);
    ESP_LOGE("END", "Element in Queue BLE: %d", i);
    i = empty_queue(q_wifi);
    ESP_LOGE("END", "Element in Queue WIFI: %d", i);
}

void execute_rule() {
    initialize_variables();
    q_ble = create_queue();
    q_wifi = create_queue();
    running_rule = true;

    const TickType_t xDelay = m1.delay_s / portTICK_PERIOD_MS;
    printf("Start after first delay: %d --> delay loop: %d\n", m1.delay_s, xDelay);
    printf("Delay_Buffer :%d [min: %d]\n", (int) delay_buffer, (int) delay_min_buff);
    vTaskDelay(1000 / portTICK_PERIOD_MS);


//    TickType_t xStart;
//    TickType_t xEnd;
//    TickType_t xDifference;

    TickType_t xLastWakeTime = xTaskGetTickCount();;

    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        // xStart = xTaskGetTickCount();
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);

        if (level_sent >= delay_buff_init) {
            re_send_mex();
            if (!change_delay) {
                change_delay = true;
            }
        }

        level_sent += 1;

//        xEnd = xTaskGetTickCount();
//        xDifference = xDelay - (xEnd - xStart);
//        //ESP_LOGW("TIME", "start: %d, end: %d --> diff: %d", xStart, xEnd, xDifference);
//        if (xDifference > 0) {
//            if (xDifference > xDelay) {
//                vTaskDelay(xDelay); // delay is milliseconds
//            } else {
//                vTaskDelay(xDifference);// delay is milliseconds
//            }
//        } else {
//            vTaskDelay(0);
//        }
    }
    create_message_rapid("F", "0", "0");
    ESP_LOGE("RULE", "End send");
    info_test();
}

void decoding_string(char tokens0, char *token1, char *token2, char *token3, char *token4) {
    char **t1_char = str_split(token1, ':');
    char **t2_char = str_split(token2, ':');
    char **t3_char = str_split(token3, ':');
    char **t4_char = str_split(token4, ':');

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
        define_mesh_address((int) strtoul((const char *) t4_char[1], NULL, 10));
        m1.ack_s = 0;
    }

    free(t1_char);
    free(t2_char);
    free(t3_char);
    free(t4_char);
}

void command_received(char **tokens, int count) {
    count = count - 2;
    switch (tokens[0][0]) {
        case '#':
            running_rule = false;
            char **t1_char = str_split(tokens[1], ':');
            uint16_t level = strtoul((const char *) t1_char[1], NULL, 10);
            send_mex_wifi_to_all(level);
            printf("WIFI send mex\n");
            break;
        case '@':
            running_rule = false;
            if (count == 2) {
                decoding_string('@', tokens[1], tokens[2], "unack", "*");
                send_message_BLE(m2.addr_s, m2.opcode_s, m2.level_s, false);
                ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
            } else if (count == 3) {
                decoding_string('@', tokens[1], tokens[2], tokens[3], "*");
                send_message_BLE(m2.addr_s, m2.opcode_s, m2.level_s, m2.ack_s);
                ESP_LOGI("SEND_MESSAGE", "SET");
            }
            printf("BLE send mex\n");
            break;
        case '&':
            decoding_string('&', tokens[1], tokens[2], tokens[3], tokens[4]);
            printf("n_mex: %hu\n", m1.n_mex_s);
            printf("addr: %hhu\n", m1.addr_s);
            printf("delay: %u\n", m1.delay_s);
            execute_rule();
            printf("End Rule\n");
            break;
        default:
            printf("Comando Errato\n");
            break;
    }
}


/*******************************************************
 *                Function Definitions UART
 *******************************************************/
void create_message_rapid(char *status, char *level, char *ttl) {
    char *str3 = malloc(1 + 2 + strlen(status) + strlen(level) + strlen(status));// 1 end char; 1 for comma

    strcpy(str3, status);
    strcat(str3, ",");
    strcat(str3, level);
    strcat(str3, ",");
    strcat(str3, ttl);

    uart_trasmitting(str3);
    free(str3);

    if (strcmp(status, "I") == 0 || strcmp(status, "S") == 0) {
        ESP_LOGI("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
    } else if (strcmp(status, "R") == 0 || strcmp(status, "O") == 0) {
        ESP_LOGW("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
    } else {
        ESP_LOGE("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
    }
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
    uart_write_bytes(UART_NUM_1, test_str, len);
}

void uart_init(void) {
    printf("- %s\n", __func__);
    xTaskCreate(uart_task, "uart_task", 3072, NULL, 5, NULL);
}