#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "tcpip_adapter.h"
#include "protocol_examples_common.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>
#include "driver/gpio.h"

#define LED_WIFI GPIO_NUM_27
#define LED_ON 1
#define LED_OFF 0

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

void send_mex_wifi(int16_t value) {
    sprintf(payload, "%d", value);
    int err = sendto(sock, payload, strlen(payload), 0, (struct sockaddr *) &dest_addr, sizeof(dest_addr));
    if (err < 0) {
        ESP_LOGE("PC", "[status: W, level: %s ]", payload);
    } else {
        ESP_LOGI("PC", "[status: I, level: %s ]", payload);
    }
}

static void udp_client_send(void *pvParameters) {
    int level = 1;
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xDelay = 10 * 1000 / portTICK_PERIOD_MS;

    vTaskDelay(20 * 1000 / portTICK_PERIOD_MS);

    while (is_running_wifi) {
        vTaskDelayUntil(&xLastWakeTime, xDelay);
        send_mex_wifi(level);
        level += 1;
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
            ESP_LOGW("PC", "[status: O, level: %s ]", rx_buffer);
        }
    }
    if (sock != -1) {
        ESP_LOGE(TAG, "Shutting down socket and restarting...");
        shutdown(sock, 0);
        close(sock);
    }

    vTaskDelete(NULL);
}

void app_main() {
    wifi_led(LED_WIFI, LED_ON);
    ESP_ERROR_CHECK(nvs_flash_init());
    tcpip_adapter_init();
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    /* This helper function configures Wi-Fi or Ethernet, as selected in menuconfig.
     * Read "Establishing Wi-Fi or Ethernet Connection" section in
     * examples/protocols/README.md for more information about this function.
     */
    ESP_ERROR_CHECK(example_connect());

    create_socket();

    xTaskCreate(udp_client_send, "udp_sent", 2048, NULL, 5, NULL);
    xTaskCreate(udp_client_receive, "udp_receive", 2048, NULL, 5, NULL);
}
