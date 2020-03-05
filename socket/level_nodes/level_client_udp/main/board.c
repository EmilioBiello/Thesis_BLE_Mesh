/* board.c - Board-specific hooks */

/*
 * Copyright (c) 2017 Intel Corporation
 * Additional Copyright (c) 2018 Espressif Systems (Shanghai) PTE LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "tcpip_adapter.h"

#include "board.h"

#include "driver/uart.h"
#include "assert.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

#include "my_queue.h"
#include "connect.h"

extern void send_message_BLE(uint16_t addr, uint32_t opcode, int16_t level, bool send_rel);

char **str_split(char *a_str, char a_delim);

uint8_t count_tokens(char *a_str, char a_delim);

void decoding_string(char tokens0, char *token1, char *token2, char *token3);

void command_received(char **tokens, int count);

void update_delay_buffer(int key);

void uart_trasmitting(const char *test_str);

struct _led_state led_array = {LED_OFF, LED_OFF, LED_BLE, "ble_mesh"};

void init_wifi();

/*******************************************************
 *                Variable Definitions
 *******************************************************/
//#define HOST_IP_ADDR "192.168.43.253"
#define HOST_IP_ADDR "192.168.43.136"
#define PORT 3333
#define TAG "WIFI"

char payload[7];
char rx_buffer[128];
char addr_str[128];
int addr_family;
int ip_protocol;
struct sockaddr_in dest_addr;
int sock;
bool is_running_wifi = false;

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

static bool is_running_uart = true;

static bool is_running_rule = false;

char *command;


struct MyQueue *q_ble;

int sent_wifi;
int received_wifi;
int received_ble;
int double_sent;
int16_t level_sent = 1;
double delay_buffer = 0;
double delay_min_buff = 0;
int delay_buff_init = 0;
bool change_delay = false;
char mystatus = '0';

/*******************************************************
 *                Function Definitions Light
 *******************************************************/
void board_led_operation(uint8_t pin, uint8_t status_led) {
    if (led_array.pin != pin) {
        ESP_LOGE("LED", "LED is not found!");
        return;
    }

    if (status_led == led_array.previous) {
        ESP_LOGW("LED", "led %s is already %s",
                 led_array.name, (status_led ? "on" : "off"));
        return;
    }
    gpio_set_level(pin, status_led);
    led_array.previous = status_led;
}

void test_LED(void) {
    //---------------------------------------- TEST 1 second
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_ON);
    gpio_set_level(LED_BLE, LED_ON);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    gpio_set_level(LED_WIFI, LED_OFF);
    gpio_set_level(LED_BLE, LED_OFF);
    //---------------------------------------- TEST 1 second
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

    test_LED();

    return ESP_OK;
}

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
void wifi_led(uint8_t pin, uint8_t status_led) {
    gpio_set_level(pin, status_led);
}

void create_socket() {
    dest_addr.sin_addr.s_addr = inet_addr(HOST_IP_ADDR);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(PORT);
    addr_family = AF_INET;
    ip_protocol = IPPROTO_IP;
    inet_ntoa_r(dest_addr.sin_addr, addr_str, sizeof(addr_str) - 1);
    while (1) {
        sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
        }
        ESP_LOGI(TAG, "Socket created, sending to %s:%d", HOST_IP_ADDR, PORT);
        is_running_wifi = true;
        break;
    }
    wifi_led(LED_WIFI, LED_OFF);
}

void re_send_mex() {
    int front_value = get_front_mex(q_ble);
    if (front_value > 0) {
        if ((level_sent - front_value) > (int) delay_buffer) {
            int value = deQueue(q_ble);
            send_mex_wifi(value);
            //ESP_LOGE("WIFI", "SEND WIFI_: %d --- BLE_: %d, delay: %d", value, level_sent, (int) delay_buffer);
        }
    }
}

void send_mex_wifi(int16_t value) {
    sprintf(payload, "%d", value);
    int err = sendto(sock, payload, strlen(payload), 0, (struct sockaddr *) &dest_addr, sizeof(dest_addr));
    if (err < 0) {
        ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
        create_message_rapid("W", payload, "*", 1);
    } else {
        create_message_rapid("I", payload, "*", 1);
        queue_operation('a', 'w', value);
//        queue_op_mixed('a', 'w', value);
    }
}

static void udp_client_sent(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xDelay = m1.delay_s / portTICK_PERIOD_MS;

    while (is_running_rule) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        if (level_sent >= delay_buff_init) {
            re_send_mex();
            if (!change_delay) {
                change_delay = true;
            }
        }
    }

    vTaskDelete(NULL);
}

static void udp_client_receive(void *pvParameters) {
    struct sockaddr_in source_addr; // Large enough for both IPv4 or IPv6
    socklen_t socklen = sizeof(source_addr);

    while (is_running_wifi) {
        int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer) - 1, 0, (struct sockaddr *) &source_addr, &socklen);

        // Error occurred during receiving
        if (len < 0) {
            ESP_LOGE(TAG, "recvfrom failed: errno %d", errno);
        } else {
            rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string
            create_message_rapid("O", rx_buffer, "*", 1);
            queue_operation('d', 'w', (int) rx_buffer);
//            queue_op_mixed('d', 'w', (int) rx_buffer);
        }
    }
    if (sock != -1) {
        ESP_LOGE(TAG, "Shutting down socket and restarting...");
        shutdown(sock, 0);
        close(sock);
    }

    vTaskDelete(NULL);
}

/*******************************************************
 *                Function Definitions Command
 *******************************************************/
void queue_op_mixed(char operation, char tech, int key) {
    switch (operation) {
        case 'a':
            // Add mex in queue
            if (mystatus == '2' && tech == 'b') {
                enQueue(q_ble, key);
            }
            break;
        case 'd':
            // Remove mex from queue
            if (mystatus == '2' && tech == 'b') {
                delete_node(q_ble, key);
                update_delay_buffer(key);
            }
            break;
        default:
            ESP_LOGE("QUEUE", "Error operation");
            break;
    }
}

void queue_operation(char operation, char tech, int key) {
    switch (operation) {
        case 'a':
            // Add mex in queue
            if (is_running_rule) {
                if (tech == 'b') {
                    enQueue(q_ble, key);
                    // ESP_LOGW("Q_BLE", "ADD %d", key);
                } else if (tech == 'w') {
                    sent_wifi += 1;
                    // ESP_LOGW("Q_WIFI", "ADD %d", key);
                }
            } else {
                ESP_LOGI("TEST", "Sent_mex %d", key);
            }
            break;
        case 'd':
            // Delete mex from queue
            if (is_running_rule) {
                if (tech == 'b') {
                    int value = delete_node(q_ble, key);
                    if (value > 0) {
                        // ESP_LOGW("Q_BLE", "DELETE %d", key);
                        received_ble += 1;
                    } else {
                        ESP_LOGE("DOUBLE_BLE", "Value not present in the list: [%d]\n", key);
                        double_sent += 1;
                    }
                    update_delay_buffer(key);
                } else {
                    // ESP_LOGW("Q_WIFI", "DELETE %d", key);
                    received_wifi += 1;
                }
            } else {
                ESP_LOGI("TEST", "Received_mex %d", key);
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
    double_sent = 0;
    is_running_rule = false;
    change_delay = false;
    level_sent = 1;
    delay_buffer = (40 * 1000) / m1.delay_s; // 40 seconds --> (30*1000 / DELAY) --> 600 packets
    delay_min_buff = (1 * 1000) / m1.delay_s; // delay minimo 1 s
    delay_buff_init = (int) delay_buffer;
    printf("Initial Delay: %f, min_delay: %f", delay_buffer, delay_min_buff);
    // 1 minute express and number of packets -> (1*60*1000)/ DELAY
    // [1 minute - 50 ms frequency = 1200 packet]
}

void info_test() {
    is_running_rule = false;
    ESP_LOGE("END", "Received BLE: %d", received_ble);
    ESP_LOGE("END", "Sent wifi: %d Received wifi: %d --- diff: %d", sent_wifi, received_wifi,
             (received_wifi - sent_wifi));
    ESP_LOGE("END", "TOTALE Received: %d", (received_ble + received_wifi));
    ESP_LOGE("END", "Double sent: %d", double_sent);

    for (int j = 0; j < 5; ++j) {
        gpio_set_level(LED_BLE, LED_ON);
        gpio_set_level(LED_WIFI, LED_ON);
        vTaskDelay(m1.delay_s / portTICK_PERIOD_MS);
        gpio_set_level(LED_BLE, LED_OFF);
        gpio_set_level(LED_WIFI, LED_OFF);
    }

    int i = empty_queue(q_ble);
    ESP_LOGE("END", "Element in Queue BLE: %d", i);
}

void mixed_rule() {
    is_running_rule = false;
    change_delay = false;
    level_sent = 1;
    delay_buffer = (40 * 1000) / m1.delay_s; // 40 seconds --> (30*1000 / DELAY) --> 600 packets
    delay_min_buff = (1 * 1000) / m1.delay_s; // delay minimo 1 s
    delay_buff_init = (int) (10 * 1000) / m1.delay_s; //10 seconds
    printf("Initial Delay: %f, min_delay: %f", delay_buffer, delay_min_buff);

    q_ble = create_queue();

    const TickType_t xDelay = m1.delay_s / portTICK_PERIOD_MS;
    ESP_LOGW("TIME", "Start after first delay: %d --> delay loop: %d\n", m1.delay_s, xDelay);
    ESP_LOGW("TIME", "Delay_Buffer :%d [min: %d]\n", (int) delay_buffer, (int) delay_min_buff);

    is_running_rule = true;
    vTaskDelay(1000 / portTICK_PERIOD_MS);

    // TODO BLE
    mystatus = '1';
    TickType_t xLastWakeTime = xTaskGetTickCount();
    create_message_rapid("F", "1", "0", 1);
    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);
        level_sent += 1;
    }
    create_message_rapid("F", "1", "1", 1);
    is_running_rule = false;
    vTaskDelay(10000 / portTICK_PERIOD_MS);

    // TODO BLE + WIFI
    mystatus = '2';
    is_running_rule = true;
    change_delay = false;
    xTaskCreate(udp_client_sent, "udp_sent_mixed", 2048, NULL, 2, NULL);
    xLastWakeTime = xTaskGetTickCount();
    create_message_rapid("F", "2", "0", 1);
    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);
        level_sent += 1;
    }
    create_message_rapid("F", "2", "1", 1);
    is_running_rule = false;
    delay_buffer = (40 * 1000) / m1.delay_s; // 40 seconds --> (30*1000 / DELAY) --> 600 packets
    empty_queue(q_ble);
    change_delay = false;
    vTaskDelay(10000 / portTICK_PERIOD_MS);

    // TODO WIFI
    mystatus = '3';
    is_running_rule = true;
    xLastWakeTime = xTaskGetTickCount();
    create_message_rapid("F", "3", "0", 1);
    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_mex_wifi(level_sent);
        level_sent += 1;
    }
    create_message_rapid("F", "3", "1", 1);
    is_running_rule = false;
    vTaskDelay(10000 / portTICK_PERIOD_MS);

    // TODO BLE + WIFI
    mystatus = '2';
    is_running_rule = true;
    change_delay = true;
    xTaskCreate(udp_client_sent, "udp_sent_mixed", 2048, NULL, 2, NULL);
    xLastWakeTime = xTaskGetTickCount();
    create_message_rapid("F", "4", "0", 1);
    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);
        level_sent += 1;
    }
    create_message_rapid("F", "4", "1", 1);
    is_running_rule = false;
    empty_queue(q_ble);
    change_delay = false;
    vTaskDelay(10000 / portTICK_PERIOD_MS);

    // TODO BLE
    mystatus = '1';
    xLastWakeTime = xTaskGetTickCount();
    create_message_rapid("F", "5", "0", 1);
    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);
        level_sent += 1;
    }
    create_message_rapid("F", "5", "1", 1);
    is_running_rule = false;
    create_message_rapid("F", "0", "0", 1);
}

void execute_rule() {
    initialize_variables();
    q_ble = create_queue();

    const TickType_t xDelay = m1.delay_s / portTICK_PERIOD_MS;
    ESP_LOGW("TIME", "Start after first delay: %d --> delay loop: %d\n", m1.delay_s, xDelay);
    ESP_LOGW("TIME", "Delay_Buffer :%d [min: %d]\n", (int) delay_buffer, (int) delay_min_buff);

    is_running_rule = true;
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    xTaskCreate(udp_client_sent, "udp_sent", 2048, NULL, 2, NULL);

    TickType_t xLastWakeTime = xTaskGetTickCount();

    for (int i = 0; i < m1.n_mex_s; ++i) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_message_BLE(m1.addr_s, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK, level_sent, m1.ack_s);
        level_sent += 1;
    }
    create_message_rapid("F", "0", "0", 1);
    ESP_LOGE("RULE", "End send");
    info_test();
}

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
        case '#':
            is_running_rule = false;
            char **t1_char = str_split(tokens[1], ':');
            uint16_t level = strtoul((const char *) t1_char[1], NULL, 10);
            send_mex_wifi(level);
            printf("WIFI send mex\n");
            break;
        case '@':
            is_running_rule = false;
            if (count == 2) {
                decoding_string('@', tokens[1], tokens[2], "unack");
                send_message_BLE(m2.addr_s, m2.opcode_s, m2.level_s, false);
                ESP_LOGI("SEND_MESSAGE", "SET_UNACK");
            } else if (count == 3) {
                decoding_string('@', tokens[1], tokens[2], tokens[3]);
                send_message_BLE(m2.addr_s, m2.opcode_s, m2.level_s, m2.ack_s);
                ESP_LOGI("SEND_MESSAGE", "SET");
            }
            printf("BLE send mex\n");
            break;
        case '&':
            decoding_string('&', tokens[1], tokens[2], tokens[3]);
            printf("n_mex: %hu\n", m1.n_mex_s);
            printf("addr: %hhu\n", m1.addr_s);
            printf("delay: %u\n", m1.delay_s);
            execute_rule();
            //mixed_rule();
            break;
        default:
            printf("Comando Errato\n");
            break;
    }
}

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
void update_delay_buffer(int key) {
    if (change_delay) {
        // TODO [Emilio] delay_1 = delay_0 + alpha*(R - delay_0)
        // TODO [Emilio] delay_1 = alpha*R + (1-alpha) * delay_0
        // TODO alpha = 0.05 --> 1-alpha = 0.95
        int diff = level_sent - key;
        double new_delay = 1.1 * ((0.2 * diff) + (0.8 * delay_buffer));

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
            create_message_rapid("T", new, "*", 0);
            ESP_LOGE("TIME", "Change Delay: %d --> %d", last_delay, delay);
        }
    }
}


/*******************************************************
 *                Function Definitions UART
 *******************************************************/
void create_message_rapid(char *status, char *level, char *ttl, uint8_t show_log) {
    char *str3 = malloc(1 + 2 + strlen(status) + strlen(level) + strlen(status));// 1 end char; 1 for comma

    strcpy(str3, status);
    strcat(str3, ",");
    strcat(str3, level);
    strcat(str3, ",");
    strcat(str3, ttl);

    uart_trasmitting(str3);
    free(str3);

    if (show_log == 1) {
        if (strcmp(status, "I") == 0 || strcmp(status, "S") == 0) {
            ESP_LOGI("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
        } else if (strcmp(status, "R") == 0 || strcmp(status, "O") == 0) {
            ESP_LOGW("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
        } else {
            ESP_LOGE("PC", "[status: %s, level: %s ttl: %s]", status, level, ttl);
        }
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
    uart_config_t uart_config = {
            .baud_rate = 115200,
            .data_bits = UART_DATA_8_BITS,
            .parity = UART_PARITY_DISABLE,
            .stop_bits = UART_STOP_BITS_1,
            .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
            .rx_flow_ctrl_thresh = 122,
    };

    //Configure UART1 parameters
    uart_param_config(UART_NUM_1, &uart_config);
    //Set UART1 pins(TX: IO4, RX: I05)
    uart_set_pin(UART_NUM_1, ECHO_TEST_TXD, ECHO_TEST_RXD, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    //Install UART driver (we don't need an event queue here)
    //In this example we don't even use a buffer for sending data.
    uart_driver_install(UART_NUM_1, BUF_SIZE * 2, 0, 0, NULL, 0);

    printf("*** UART init\n");

    uint8_t *data_uart = (uint8_t *) malloc(BUF_SIZE + 1);
    is_running_rule = true;

    while (is_running_uart) {
        //Read data from UART
        const int rxBytes = uart_read_bytes(UART_NUM_1, data_uart, BUF_SIZE, 1000 / portTICK_RATE_MS);
        if (rxBytes > 0) {
            data_uart[rxBytes] = '\0';
            ESP_LOGI("UART", "Read %d bytes: '%s'", rxBytes, data_uart);

            size_t count = count_tokens((char *) data_uart, ',');
            char **tokens = str_split((char *) data_uart, ',');
            command_received(tokens, count);

            fflush(stdout);
            uart_flush_input(UART_NUM_1);
        }
    }
}

void uart_trasmitting(const char *test_str) {
    const int len = strlen(test_str);
    uart_write_bytes(UART_NUM_1, test_str, len);
}

void init_wifi() {
    xTaskCreate(udp_client_sent, "udp_sent", 2048, NULL, 2, NULL);
}

void board_init(void) {
    tcpip_adapter_init();
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    create_socket();

    xTaskCreate(udp_client_receive, "udp_receive", 2048, NULL, 2, NULL);

    xTaskCreate(uart_task, "uart_task", 3072, NULL, 4, NULL);
}
