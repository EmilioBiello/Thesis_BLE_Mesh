/* main.c - Application main entry point */

/*
 * Copyright (c) 2017 Intel Corporation
 * Additional Copyright (c) 2018 Espressif Systems (Shanghai) PTE LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <string.h>

#include "esp_log.h"
#include "nvs_flash.h"

#include "esp_ble_mesh_common_api.h"
#include "esp_ble_mesh_provisioning_api.h"
#include "esp_ble_mesh_networking_api.h"
#include "esp_ble_mesh_config_model_api.h"
#include "esp_ble_mesh_generic_model_api.h"

#include "board.h"
#include "ble_mesh_demo_init.h"

#define CID_ESP 0x02E5

static uint8_t dev_uuid[16] = {0xdd, 0xdd};
static uint16_t node_net_idx = ESP_BLE_MESH_KEY_UNUSED;
static uint16_t node_app_idx = ESP_BLE_MESH_KEY_UNUSED;
static uint8_t msg_tid = 0x1;
int my_info_level = 0;

static esp_ble_mesh_client_t bleMeshClient;

static esp_ble_mesh_cfg_srv_t config_server = {
        .relay = ESP_BLE_MESH_RELAY_DISABLED,
        .beacon = ESP_BLE_MESH_BEACON_ENABLED,
#if defined(CONFIG_BLE_MESH_FRIEND)
        .friend_state = ESP_BLE_MESH_FRIEND_ENABLED,
#else
        .friend_state = ESP_BLE_MESH_FRIEND_NOT_SUPPORTED,
#endif
#if defined(CONFIG_BLE_MESH_GATT_PROXY_SERVER)
        .gatt_proxy = ESP_BLE_MESH_GATT_PROXY_ENABLED,
#else
        .gatt_proxy = ESP_BLE_MESH_GATT_PROXY_NOT_SUPPORTED,
#endif
        .default_ttl = 7,
        /* 3 transmissions with 20ms interval */
        .net_transmit = ESP_BLE_MESH_TRANSMIT(2, 20),
        .relay_retransmit = ESP_BLE_MESH_TRANSMIT(2, 20),
};

ESP_BLE_MESH_MODEL_PUB_DEFINE(cli_pub, 2 + 1, ROLE_NODE);

static esp_ble_mesh_model_t root_models[] = {
        ESP_BLE_MESH_MODEL_CFG_SRV(&config_server),
        ESP_BLE_MESH_MODEL_GEN_LEVEL_CLI(&cli_pub, &bleMeshClient),
};

static esp_ble_mesh_elem_t elements[] = {
        ESP_BLE_MESH_ELEMENT(0, root_models, ESP_BLE_MESH_MODEL_NONE),
};

static esp_ble_mesh_comp_t composition = {
        .cid = CID_ESP,
        .elements = elements,
        .element_count = ARRAY_SIZE(elements),
};

/* Disable OOB security for SILabs Android app */
static esp_ble_mesh_prov_t provision = {
        .uuid = dev_uuid,
#if 0
.output_size = 4,
.output_actions = ESP_BLE_MESH_DISPLAY_NUMBER,
.input_actions = ESP_BLE_MESH_PUSH,
.input_size = 4,
#else
        .output_size = 0,
        .output_actions = 0,
#endif
};

static void prov_complete(uint16_t net_idx, uint16_t addr, uint8_t flags, uint32_t iv_index) {
    ESP_LOGI(TAG_BLE, "net_idx: 0x%04x, addr: 0x%04x", net_idx, addr);
    ESP_LOGI(TAG_BLE, "flags: 0x%02x, iv_index: 0x%08x", flags, iv_index);
    board_led_operation(LED_BLE, LED_OFF);
    node_net_idx = net_idx;

    //inizializzo WIFI
    vTaskDelay(10000 / portTICK_PERIOD_MS);
    board_init();
}

static void example_ble_mesh_provisioning_cb(esp_ble_mesh_prov_cb_event_t event,
                                             esp_ble_mesh_prov_cb_param_t *param) {
    switch (event) {
        case ESP_BLE_MESH_PROV_REGISTER_COMP_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_PROV_REGISTER_COMP_EVT, err_code %d", param->prov_register_comp.err_code);
            break;
        case ESP_BLE_MESH_NODE_PROV_ENABLE_COMP_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_PROV_ENABLE_COMP_EVT, err_code %d",
                     param->node_prov_enable_comp.err_code);
            break;
        case ESP_BLE_MESH_NODE_PROV_LINK_OPEN_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_PROV_LINK_OPEN_EVT, bearer %s",
                     param->node_prov_link_open.bearer == ESP_BLE_MESH_PROV_ADV ? "PB-ADV" : "PB-GATT");
            break;
        case ESP_BLE_MESH_NODE_PROV_LINK_CLOSE_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_PROV_LINK_CLOSE_EVT, bearer %s",
                     param->node_prov_link_close.bearer == ESP_BLE_MESH_PROV_ADV ? "PB-ADV" : "PB-GATT");
            break;
        case ESP_BLE_MESH_NODE_PROV_COMPLETE_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_PROV_COMPLETE_EVT");
            prov_complete(param->node_prov_complete.net_idx, param->node_prov_complete.addr,
                          param->node_prov_complete.flags, param->node_prov_complete.iv_index);
            break;
        case ESP_BLE_MESH_NODE_PROV_RESET_EVT:
            break;
        case ESP_BLE_MESH_NODE_SET_UNPROV_DEV_NAME_COMP_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_SET_UNPROV_DEV_NAME_COMP_EVT, err_code %d",
                     param->node_set_unprov_dev_name_comp.err_code);
            break;
        default:
            break;
    }
}

void send_message_BLE(uint16_t addr, uint32_t opcode, int16_t level, bool send_rel) {
    esp_ble_mesh_generic_client_set_state_t set = {{0}};
    esp_ble_mesh_client_common_param_t common = {0};
    esp_err_t err;

    common.opcode = opcode;
    common.model = bleMeshClient.model;
    common.ctx.net_idx = node_net_idx;
    common.ctx.app_idx = node_app_idx;
    common.ctx.addr = addr;   /* 0xFFFF --> to all nodes */ /* 0xC001 myGroup*/
    common.ctx.send_ttl = 3;
    common.ctx.send_rel = send_rel;
    common.msg_timeout = 0; // 200    /* 0 indicates that timeout value from menuconfig will be used */ /* The default value (4 seconds) would be applied if the parameter msg_timeout is set to 0. */
    common.msg_role = ROLE_NODE;

    set.level_set.op_en = false;
    set.level_set.level = level;
    set.level_set.tid = msg_tid++;
    my_info_level = level;

    err = esp_ble_mesh_generic_client_set_state(&common, &set);
    if (err) {
        ESP_LOGE(TAG_BLE, "%s: Generic Level Set failed", __func__);
    }
    char level_c[7];
    sprintf(level_c, "%d", level);
    create_message_rapid("S", level_c, "3", 1);
    queue_operation('a', 'b', level);
    //queue_op_mixed('a', 'b', level);
}

static void example_ble_mesh_generic_client_cb(esp_ble_mesh_generic_client_cb_event_t event,
                                               esp_ble_mesh_generic_client_cb_param_t *param) {
    switch (event) {
        case ESP_BLE_MESH_GENERIC_CLIENT_GET_STATE_EVT:
            if (param->params->opcode == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_GET) {
                ESP_LOGI("MessaggioRicevuto", "LEVEL_GET, level %d receive_ttl: %d",
                         param->status_cb.level_status.present_level, param->params->ctx.recv_ttl);
            }
            ESP_LOGI(TAG_BLE, "--- GET_STATE_EVT");
            break;
        case ESP_BLE_MESH_GENERIC_CLIENT_SET_STATE_EVT: {

            if (param->params->opcode == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET) {
                char level[7];
                char ttl[4];
                sprintf(level, "%d", param->status_cb.level_status.present_level);
                sprintf(ttl, "%d", param->params->ctx.recv_ttl);
                // TODO [Emilio] scrittura su seriale
                //create_message_rapid("R", level, ttl,1);
                //update_queue_ble(param->status_cb.level_status.present_level);
            } else if (param->params->opcode == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK) {
                char info_level[7];
                sprintf(info_level, "%d", my_info_level);
                // TODO [Emilio] commentata scrittua su seriale
                create_message_rapid("E", info_level, "0", 1);
                // send_mex_wifi(my_info_level);
            }
            //ESP_LOGI(TAG_BLE, "--- SET_STATE_EVT 0x%x", param->params->opcode);
            break;
        }
        case ESP_BLE_MESH_GENERIC_CLIENT_PUBLISH_EVT: {
            char level[7];
            char ttl[4];
            sprintf(level, "%d", param->status_cb.level_status.present_level);
            sprintf(ttl, "%d", param->params->ctx.recv_ttl);
            // TODO [Emilio] commentata scrittua su seriale
            create_message_rapid("R", level, ttl, 1);
            queue_operation('d', 'b', param->status_cb.level_status.present_level);
//            queue_op_mixed('d', 'b', param->status_cb.level_status.present_level);
            break;
        }
        case ESP_BLE_MESH_GENERIC_CLIENT_TIMEOUT_EVT:
            /* If failed to receive the responses, these messages will be resend */
            //ESP_LOGI(TAG_BLE, "--- ESP_BLE_MESH_GENERIC_CLIENT_TIMEOUT_EVT");
            if (param->params->opcode == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET) {
                /* If failed to get the response of Generic Level Set, resend Generic Level Set  */
                send_mex_wifi(my_info_level);
                ESP_LOGE(TAG_BLE, "--- TIMEOUT_EVT");
            }
            break;
        default:
            ESP_LOGI(TAG_BLE, "--- DEFAULT opcode is 0x%x", param->params->opcode);
            break;
        case ESP_BLE_MESH_GENERIC_CLIENT_EVT_MAX:
            break;
    }
//    ESP_LOGW(TAG_BLE, "%s: event is %d, error code is %d, addr: 0x%04x opcode is 0x%x", __func__, event,
//             param->error_code,
//             param->params->ctx.addr, param->params->opcode);
}

static void example_ble_mesh_config_server_cb(esp_ble_mesh_cfg_server_cb_event_t event,
                                              esp_ble_mesh_cfg_server_cb_param_t *param) {

    if (event == ESP_BLE_MESH_CFG_SERVER_STATE_CHANGE_EVT) {
        switch (param->ctx.recv_op) {
            case ESP_BLE_MESH_MODEL_OP_APP_KEY_ADD:
                ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_MODEL_OP_APP_KEY_ADD");
                ESP_LOGI(TAG_BLE, "net_idx 0x%04x, app_idx 0x%04x",
                         param->value.state_change.appkey_add.net_idx,
                         param->value.state_change.appkey_add.app_idx);
                ESP_LOG_BUFFER_HEX("AppKey", param->value.state_change.appkey_add.app_key, 16);
                break;
            case ESP_BLE_MESH_MODEL_OP_MODEL_APP_BIND:
                ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_MODEL_OP_MODEL_APP_BIND");
                ESP_LOGI(TAG_BLE, "elem_addr 0x%04x, app_idx 0x%04x, cid 0x%04x, mod_id 0x%04x",
                         param->value.state_change.mod_app_bind.element_addr,
                         param->value.state_change.mod_app_bind.app_idx,
                         param->value.state_change.mod_app_bind.company_id,
                         param->value.state_change.mod_app_bind.model_id);
                if (param->value.state_change.mod_app_bind.company_id == 0xFFFF &&
                    param->value.state_change.mod_app_bind.model_id == ESP_BLE_MESH_MODEL_ID_GEN_LEVEL_CLI) {
                    node_app_idx = param->value.state_change.mod_app_bind.app_idx;
                }
                break;
            default:
                break;
        }
    }
}

static esp_err_t ble_mesh_init(void) {
    esp_err_t err = 0;

    // is used to register callback function used to handle provisioning and networking related events
    esp_ble_mesh_register_prov_callback(example_ble_mesh_provisioning_cb);
    // is used to register callback function used to handle Generic Client Models related events
    esp_ble_mesh_register_generic_client_callback(example_ble_mesh_generic_client_cb);
    // is used to register callback function used to handle Configuration Client Model related events
    esp_ble_mesh_register_config_server_callback(example_ble_mesh_config_server_cb);

    err = esp_ble_mesh_init(&provision, &composition);
    if (err) {
        ESP_LOGE(TAG_BLE, "Initializing mesh failed (err %d)", err);
        return err;
    }

    esp_ble_mesh_node_prov_enable(ESP_BLE_MESH_PROV_ADV | ESP_BLE_MESH_PROV_GATT);

    ESP_LOGI(TAG_BLE, "BLE Mesh Node initialized");

    board_led_operation(LED_BLE, LED_ON);
    wifi_led(LED_WIFI, LED_ON);

    return err;
}

/*******************************************************
 *                APP_MAIN
 *******************************************************/
void app_main(void) {
    esp_err_t err;

    ESP_ERROR_CHECK(mesh_light_init());
    ESP_ERROR_CHECK(nvs_flash_init());

    /* BLE */
    ESP_LOGI("APP_MAIN", "Initializing...BLE...");

    err = bluetooth_init();
    if (err) {
        ESP_LOGE("APP_MAIN", "esp32_bluetooth_init failed (err %d)", err);
        return;
    }

    ble_mesh_get_dev_uuid(dev_uuid);

    /* Initialize the Bluetooth Mesh Subsystem */
    err = ble_mesh_init();
    if (err) {
        ESP_LOGE("APP_MAIN", "Bluetooth mesh init failed (err %d)", err);
    }
}
