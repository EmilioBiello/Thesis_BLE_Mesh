//
// Created by emilio on 29/01/20.
//

#ifndef LEVEL_CLIENT_UDP_CONNECT_H
#define LEVEL_CLIENT_UDP_CONNECT_H

#include <lwip/ip4_addr.h>
#include "esp_err.h"

/**
 * @brief Configure Wi-Fi connect, wait for IP
 *
 * @return ESP_OK on successful connection
 */
esp_err_t ESP_connect(void);

/**
 * Counterpart to example_connect, de-initializes Wi-Fi or Ethernet
 */
esp_err_t ESP_disconnect(void);

#endif //LEVEL_CLIENT_UDP_CONNECT_H
