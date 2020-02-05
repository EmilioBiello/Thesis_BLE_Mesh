#include <stdio.h>
#include <string.h>

#include "esp_log.h"
#include "nvs_flash.h"
/* WIFI */
#include "esp_wifi.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_mesh.h"
#include "esp_mesh_internal.h"
/* BLE */
#include "esp_ble_mesh_defs.h"
#include "esp_ble_mesh_common_api.h"
#include "esp_ble_mesh_networking_api.h"
#include "esp_ble_mesh_provisioning_api.h"
#include "esp_ble_mesh_config_model_api.h"
#include "esp_ble_mesh_generic_model_api.h"
#include "esp_ble_mesh_local_data_operation_api.h"
/* INCLUDE */
#include "include/mesh_board.h"
#include "include/ble_mesh_demo_init.h"
#include "include/my_queue.h"

/*******************************************************
 *                Macros
 *******************************************************/
#define TAG_WIFI "WIFI"

/*******************************************************
 *                Constants
 *******************************************************/
#define RX_SIZE          (1500)
#define TX_SIZE          (1460)
#define CID_ESP 0x02E5

/*******************************************************
 *                Variable Definitions WIFI
 *******************************************************/
static const uint8_t MESH_ID[6] = {0x77, 0x77, 0x77, 0x77, 0x77, 0x77};
static uint8_t tx_buf[TX_SIZE] = {0,};
static uint8_t rx_buf[RX_SIZE] = {0,};
static bool is_running = true;
static bool is_mesh_connected = false;
static mesh_addr_t mesh_parent_addr;
static int mesh_layer = -1;

mesh_addr_t my_route_table[CONFIG_MESH_ROUTE_TABLE_SIZE];
int my_route_table_size = 0;
int index_wifi = 0;

/*******************************************************
 *                Variable Definitions BLE
 *******************************************************/
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

/*******************************************************
 *                Function Definitions WIFI
 *******************************************************/
//void esp_mesh_p2p_tx_main(void *arg) {
//    int i;
//    esp_err_t err;
//    int send_count = 0;
//    mesh_addr_t route_table[CONFIG_MESH_ROUTE_TABLE_SIZE];
//    int route_table_size = 0;
//    mesh_data_t data;
//    data.data = tx_buf;
//    data.size = sizeof(tx_buf);
//    data.proto = MESH_PROTO_BIN;
//    data.tos = MESH_TOS_P2P;
//    is_running = true;
//
//    while (is_running) {
//        /* non-root do nothing but print */
//        if (!esp_mesh_is_root()) {
//            ESP_LOGI(TAG_WIFI, "Layer:%d, rtableSize:%d, %s", mesh_layer,
//                     esp_mesh_get_routing_table_size(),
//                     (is_mesh_connected && esp_mesh_is_root()) ? "ROOT" : is_mesh_connected ? "NODE" : "DISCONNECT");
//            vTaskDelay(10 * 1000 / portTICK_RATE_MS);
//            continue;
//        }
//        esp_mesh_get_routing_table((mesh_addr_t *) &route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6, &route_table_size);
//        if (send_count && !(send_count % 100)) {
//            ESP_LOGI(TAG_WIFI, "size:%d/%d,send_count:%d", route_table_size, esp_mesh_get_routing_table_size(),
//                     send_count);
//        }
//        send_count++;
//        tx_buf[25] = (send_count >> 24) & 0xff;
//        tx_buf[24] = (send_count >> 16) & 0xff;
//        tx_buf[23] = (send_count >> 8) & 0xff;
//        tx_buf[22] = (send_count >> 0) & 0xff;
//
//        if (send_count % 2) {
//            memcpy(tx_buf, (uint8_t *) &light_on, sizeof(light_on));
//        } else {
//            memcpy(tx_buf, (uint8_t *) &light_off, sizeof(light_off));
//        }
//
//        ESP_LOGI(TAG_WIFI, "[L:%d][table_size:%d][parent: "
//                MACSTR
//                "][me: "
//                MACSTR
//                "]\n", mesh_layer, esp_mesh_get_routing_table_size(), MAC2STR(mesh_parent_addr.addr),
//                 MAC2STR(route_table[0].addr));
//        for (i = 0; i < route_table_size; i++) {
//            err = esp_mesh_send(&route_table[i], &data, MESH_DATA_P2P, NULL, 0);
//            if (err) {
//                ESP_LOGE(TAG_WIFI,
//                         "[ROOT-2-UNICAST:%d][L:%d]parent:"
//                                 MACSTR
//                                 " to "
//                                 MACSTR
//                                 ", heap:%d[err:0x%x, proto:%d, tos:%d]",
//                         send_count, mesh_layer, MAC2STR(mesh_parent_addr.addr),
//                         MAC2STR(route_table[i].addr), esp_get_free_heap_size(),
//                         err, data.proto, data.tos);
//            } else if (!(send_count % 100)) {
//                ESP_LOGW(TAG_WIFI,
//                         "[ROOT-2-UNICAST:%d][L:%d][rtableSize:%d]parent:"
//                                 MACSTR
//                                 " to "
//                                 MACSTR
//                                 ", heap:%d[err:0x%x, proto:%d, tos:%d]",
//                         send_count, mesh_layer,
//                         esp_mesh_get_routing_table_size(),
//                         MAC2STR(mesh_parent_addr.addr),
//                         MAC2STR(route_table[i].addr), esp_get_free_heap_size(),
//                         err, data.proto, data.tos);
//            } else {
//                ESP_LOGI("Mex_Sent", "[#TX:%d][to: "
//                        MACSTR
//                        "]\n", send_count, MAC2STR(route_table[i].addr));
//            }
//        }
//        /* if route_table_size is less than 10, add delay to avoid watchdog in this task. */
//        if (route_table_size < 5) {
//            vTaskDelay(10 * 1000 / portTICK_RATE_MS);
//        }
//    }
//    vTaskDelete(NULL);
//}

void send_mex_wifi_to_all(int16_t data_tx) {
    printf("- %s\n", __func__);
    esp_err_t err;
    mesh_addr_t route_table[CONFIG_MESH_ROUTE_TABLE_SIZE];
    int route_table_size = 0;
    int i = 0;
    mesh_data_t data;
    data.data = tx_buf;
    data.size = sizeof(tx_buf);
    data.proto = MESH_PROTO_BIN;
    data.tos = MESH_TOS_P2P;

    /* Get Routing Table*/
    esp_mesh_get_routing_table((mesh_addr_t *) &route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6, &route_table_size);

    tx_buf[25] = (data_tx >> 24) & 0xff;
    tx_buf[24] = (data_tx >> 16) & 0xff;
    tx_buf[23] = (data_tx >> 8) & 0xff;
    tx_buf[22] = (data_tx >> 0) & 0xff;

    ESP_LOGI(TAG_WIFI, "[L:%d][table_size:%d][parent: "
            MACSTR
            "][me: "
            MACSTR
            "]\n", mesh_layer, esp_mesh_get_routing_table_size(), MAC2STR(mesh_parent_addr.addr),
             MAC2STR(route_table[0].addr));
    /* SEND DATA */
    for (i = 0; i < route_table_size; i++) {
        err = esp_mesh_send(&route_table[i], &data, MESH_DATA_P2P, NULL, 0);
        if (err) {
            ESP_LOGE(TAG_WIFI,
                     "[ROOT-2-UNICAST:%d][L:%d]parent:"
                             MACSTR
                             " to "
                             MACSTR
                             ", heap:%d[err:0x%x, proto:%d, tos:%d]",
                     data_tx, mesh_layer, MAC2STR(mesh_parent_addr.addr),
                     MAC2STR(route_table[i].addr), esp_get_free_heap_size(),
                     err, data.proto, data.tos);
        } else {
            ESP_LOGI("Mex_Sent_WIFI", "[#TX:%d][to: "
                    MACSTR
                    "] [index: %d]\n", data_tx, MAC2STR(route_table[i].addr), i);
        }
        vTaskDelay(200 / portTICK_PERIOD_MS);
    }
}

void send_mex_wifi(int16_t data_tx) {
    esp_err_t err;
    mesh_data_t data;
    data.data = tx_buf;
    data.size = sizeof(tx_buf);
    data.proto = MESH_PROTO_BIN;
    data.tos = MESH_TOS_P2P;

    /* Get Routing Table*/
//    esp_mesh_get_routing_table((mesh_addr_t *) &route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6, &route_table_size);

    tx_buf[25] = (data_tx >> 24) & 0xff;
    tx_buf[24] = (data_tx >> 16) & 0xff;
    tx_buf[23] = (data_tx >> 8) & 0xff;
    tx_buf[22] = (data_tx >> 0) & 0xff;

    /* SEND DATA */
    err = esp_mesh_send(&my_route_table[index_wifi], &data, MESH_DATA_P2P, NULL, 0);
    char level[7];
    sprintf(level, "%d", data_tx);
    if (err) {
        create_message_rapid("W", level, "*", 1);
    } else {
        create_message_rapid("I", level, "*", 1);
        queue_operation('a', 'w', data_tx);
    }
}

void esp_mesh_p2p_rx_main(void *arg) {
    esp_err_t err;
    mesh_addr_t from;
    int value = 0;
    mesh_data_t data;
    int flag = 0;
    data.data = rx_buf;
    data.size = RX_SIZE;
    is_running = true;
    char level[7];

    while (is_running) {
        data.size = RX_SIZE;
        err = esp_mesh_recv(&from, &data, portMAX_DELAY, &flag, NULL, 0);
        if (err != ESP_OK || !data.size) {
            ESP_LOGE(TAG_WIFI, "err:0x%x, size:%d", err, data.size);
            continue;
        }
        /* extract value */
        if (data.size >= sizeof(value)) {
            value = (data.data[25] << 24) | (data.data[24] << 16) | (data.data[23] << 8) | data.data[22];
        }

        /* process light control */
        // mesh_light_process(&from, data.data, data.size);
        sprintf(level, "%d", value);
        create_message_rapid("O", level, "*", 0);
        queue_operation('d', 'w', value);
        ESP_LOGW("PC", "[status: O, level: %s from: "
                MACSTR
                "]", level, MAC2STR(from.addr));
    }
    vTaskDelete(NULL);
}

void define_mesh_address(int index) {
    index_wifi = index;
}

esp_err_t esp_mesh_comm_p2p_start_3(void) {
    uart_init();
    xTaskCreate(esp_mesh_p2p_rx_main, "MPRX", 3072, NULL, 4, NULL);
    return ESP_OK;
}

void mesh_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
    mesh_addr_t id = {{0},};
    static uint8_t last_layer = 0;

    switch (event_id) {
        case MESH_EVENT_STARTED: {
            esp_mesh_get_id(&id);
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_MESH_STARTED>ID:"
                    MACSTR
                    "", MAC2STR(id.addr));
            is_mesh_connected = false;
            mesh_layer = esp_mesh_get_layer();
        }
            break;
        case MESH_EVENT_STOPPED: {
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_STOPPED>");
            is_mesh_connected = false;
            mesh_layer = esp_mesh_get_layer();
        }
            break;
        case MESH_EVENT_CHILD_CONNECTED: {
            mesh_event_child_connected_t *child_connected = (mesh_event_child_connected_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_CHILD_CONNECTED>aid:%d, "
                    MACSTR
                    "",
                     child_connected->aid,
                     MAC2STR(child_connected->mac));
            /* Get Routing Table*/
            esp_mesh_get_routing_table((mesh_addr_t *) &my_route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6,
                                       &my_route_table_size);

        }
            break;
        case MESH_EVENT_CHILD_DISCONNECTED: {
            mesh_event_child_disconnected_t *child_disconnected = (mesh_event_child_disconnected_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_CHILD_DISCONNECTED>aid:%d, "
                    MACSTR
                    "",
                     child_disconnected->aid,
                     MAC2STR(child_disconnected->mac));
            /* Get Routing Table*/
            esp_mesh_get_routing_table((mesh_addr_t *) &my_route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6,
                                       &my_route_table_size);

        }
            break;
        case MESH_EVENT_ROUTING_TABLE_ADD: {
            mesh_event_routing_table_change_t *routing_table = (mesh_event_routing_table_change_t *) event_data;
            ESP_LOGW(TAG_WIFI, "<MESH_EVENT_ROUTING_TABLE_ADD>add %d, new:%d",
                     routing_table->rt_size_change,
                     routing_table->rt_size_new);
            /* Get Routing Table*/
            esp_mesh_get_routing_table((mesh_addr_t *) &my_route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6,
                                       &my_route_table_size);
            if (my_route_table_size - index_wifi != 1) {
                index_wifi = my_route_table_size - 1;
                ESP_LOGW("TABLE", "Add -- index: %d --> addr: "
                        MACSTR, index_wifi, MAC2STR(my_route_table[index_wifi].addr));
                char index[7];
                sprintf(index, "%d", index_wifi);
                create_message_rapid("N", index, "1", 1); // 1 as append
            }
        }
            break;
        case MESH_EVENT_ROUTING_TABLE_REMOVE: {
            mesh_event_routing_table_change_t *routing_table = (mesh_event_routing_table_change_t *) event_data;
            ESP_LOGW(TAG_WIFI, "<MESH_EVENT_ROUTING_TABLE_REMOVE>remove %d, new:%d",
                     routing_table->rt_size_change,
                     routing_table->rt_size_new);
            /* Get Routing Table*/
            esp_mesh_get_routing_table((mesh_addr_t *) &my_route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6,
                                       &my_route_table_size);
            if (index_wifi >= my_route_table_size) {
                index_wifi = my_route_table_size - 1;
                ESP_LOGW("TABLE", "Add -- index: %d --> addr: "
                        MACSTR, index_wifi, MAC2STR(my_route_table[index_wifi].addr));
                char index[7];
                sprintf(index, "%d", index_wifi);
                create_message_rapid("N", index, "0", 1); // 0 as remove
            }
        }
            break;
        case MESH_EVENT_NO_PARENT_FOUND: {
            mesh_event_no_parent_found_t *no_parent = (mesh_event_no_parent_found_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_NO_PARENT_FOUND>scan times:%d",
                     no_parent->scan_times);
        }
            break;
        case MESH_EVENT_PARENT_CONNECTED: {
            mesh_event_connected_t *connected = (mesh_event_connected_t *) event_data;
            esp_mesh_get_id(&id);
            mesh_layer = connected->self_layer;
            memcpy(&mesh_parent_addr.addr, connected->connected.bssid, 6);
            ESP_LOGI(TAG_WIFI,
                     "<MESH_EVENT_PARENT_CONNECTED>layer:%d-->%d, parent:"
                             MACSTR
                             "%s, ID:"
                             MACSTR
                             "",
                     last_layer, mesh_layer, MAC2STR(mesh_parent_addr.addr),
                     esp_mesh_is_root() ? "<ROOT>" :
                     (mesh_layer == 2) ? "<layer2>" : "", MAC2STR(id.addr));
            last_layer = mesh_layer;
            mesh_connected_indicator(mesh_layer);
            is_mesh_connected = true;
            if (esp_mesh_is_root()) {
                tcpip_adapter_dhcpc_start(TCPIP_ADAPTER_IF_STA);
            }
            // TODO cambiare in base al dispositivo
            esp_mesh_comm_p2p_start_3();
        }
            break;
        case MESH_EVENT_PARENT_DISCONNECTED: {
            mesh_event_disconnected_t *disconnected = (mesh_event_disconnected_t *) event_data;
            ESP_LOGI(TAG_WIFI,
                     "<MESH_EVENT_PARENT_DISCONNECTED>reason:%d",
                     disconnected->reason);
            is_mesh_connected = false;
            mesh_disconnected_indicator();
            mesh_layer = esp_mesh_get_layer();
        }
            break;
        case MESH_EVENT_LAYER_CHANGE: {
            mesh_event_layer_change_t *layer_change = (mesh_event_layer_change_t *) event_data;
            mesh_layer = layer_change->new_layer;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_LAYER_CHANGE>layer:%d-->%d%s",
                     last_layer, mesh_layer,
                     esp_mesh_is_root() ? "<ROOT>" :
                     (mesh_layer == 2) ? "<layer2>" : "");
            last_layer = mesh_layer;
            mesh_connected_indicator(mesh_layer);
        }
            break;
        case MESH_EVENT_ROOT_ADDRESS: {
            mesh_event_root_address_t *root_addr = (mesh_event_root_address_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_ROOT_ADDRESS>root address:"
                    MACSTR
                    "",
                     MAC2STR(root_addr->addr));
        }
            break;
        case MESH_EVENT_VOTE_STARTED: {
            mesh_event_vote_started_t *vote_started = (mesh_event_vote_started_t *) event_data;
            ESP_LOGI(TAG_WIFI,
                     "<MESH_EVENT_VOTE_STARTED>attempts:%d, reason:%d, rc_addr:"
                             MACSTR
                             "",
                     vote_started->attempts,
                     vote_started->reason,
                     MAC2STR(vote_started->rc_addr.addr));
        }
            break;
        case MESH_EVENT_VOTE_STOPPED: {
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_VOTE_STOPPED>");
            break;
        }
        case MESH_EVENT_ROOT_SWITCH_REQ: {
            mesh_event_root_switch_req_t *switch_req = (mesh_event_root_switch_req_t *) event_data;
            ESP_LOGI(TAG_WIFI,
                     "<MESH_EVENT_ROOT_SWITCH_REQ>reason:%d, rc_addr:"
                             MACSTR
                             "",
                     switch_req->reason,
                     MAC2STR(switch_req->rc_addr.addr));
        }
            break;
        case MESH_EVENT_ROOT_SWITCH_ACK: {
            /* new root */
            mesh_layer = esp_mesh_get_layer();
            esp_mesh_get_parent_bssid(&mesh_parent_addr);
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_ROOT_SWITCH_ACK>layer:%d, parent:"
                    MACSTR
                    "", mesh_layer, MAC2STR(mesh_parent_addr.addr));
        }
            break;
        case MESH_EVENT_TODS_STATE: {
            mesh_event_toDS_state_t *toDs_state = (mesh_event_toDS_state_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_TODS_REACHABLE>state:%d", *toDs_state);
        }
            break;
        case MESH_EVENT_ROOT_FIXED: {
            mesh_event_root_fixed_t *root_fixed = (mesh_event_root_fixed_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_ROOT_FIXED>%s",
                     root_fixed->is_fixed ? "fixed" : "not fixed");
        }
            break;
        case MESH_EVENT_ROOT_ASKED_YIELD: {
            mesh_event_root_conflict_t *root_conflict = (mesh_event_root_conflict_t *) event_data;
            ESP_LOGI(TAG_WIFI,
                     "<MESH_EVENT_ROOT_ASKED_YIELD>"
                             MACSTR
                             ", rssi:%d, capacity:%d",
                     MAC2STR(root_conflict->addr),
                     root_conflict->rssi,
                     root_conflict->capacity);
        }
            break;
        case MESH_EVENT_CHANNEL_SWITCH: {
            mesh_event_channel_switch_t *channel_switch = (mesh_event_channel_switch_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_CHANNEL_SWITCH>new channel:%d", channel_switch->channel);
        }
            break;
        case MESH_EVENT_SCAN_DONE: {
            mesh_event_scan_done_t *scan_done = (mesh_event_scan_done_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_SCAN_DONE>number:%d",
                     scan_done->number);
        }
            break;
        case MESH_EVENT_NETWORK_STATE: {
            mesh_event_network_state_t *network_state = (mesh_event_network_state_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_NETWORK_STATE>is_rootless:%d",
                     network_state->is_rootless);
        }
            break;
        case MESH_EVENT_STOP_RECONNECTION: {
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_STOP_RECONNECTION>");
        }
            break;
        case MESH_EVENT_FIND_NETWORK: {
            mesh_event_find_network_t *find_network = (mesh_event_find_network_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_FIND_NETWORK>new channel:%d, router BSSID:"
                    MACSTR
                    "",
                     find_network->channel, MAC2STR(find_network->router_bssid));
        }
            break;
        case MESH_EVENT_ROUTER_SWITCH: {
            mesh_event_router_switch_t *router_switch = (mesh_event_router_switch_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_ROUTER_SWITCH>new router:%s, channel:%d, "
                    MACSTR
                    "",
                     router_switch->ssid, router_switch->channel, MAC2STR(router_switch->bssid));
        }
            break;
        default:
            ESP_LOGI(TAG_WIFI, "unknown id:%d", event_id);
            break;
    }
}

void ip_event_handler(void *arg, esp_event_base_t event_base,
                      int32_t event_id, void *event_data) {
    ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
    ESP_LOGI(TAG_WIFI, "<IP_EVENT_STA_GOT_IP>IP:%s", ip4addr_ntoa(&event->ip_info.ip));
}

void my_wifi_init() {
    ESP_LOGI("WIFI_INIT", "Initializing...WIFI...");

    /*  tcpip initialization */
    tcpip_adapter_init();
    /* for mesh
     * stop DHCP server on softAP interface by default
     * stop DHCP client on station interface by default
     * */
    ESP_ERROR_CHECK(tcpip_adapter_dhcps_stop(TCPIP_ADAPTER_IF_AP));
    ESP_ERROR_CHECK(tcpip_adapter_dhcpc_stop(TCPIP_ADAPTER_IF_STA));
    /*  event initialization */
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    /*  wifi initialization */
    wifi_init_config_t config = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&config));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &ip_event_handler, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_FLASH));
    ESP_ERROR_CHECK(esp_wifi_start());
    /*  mesh initialization */
    ESP_ERROR_CHECK(esp_mesh_init());
    ESP_ERROR_CHECK(esp_event_handler_register(MESH_EVENT, ESP_EVENT_ANY_ID, &mesh_event_handler, NULL));
    ESP_ERROR_CHECK(esp_mesh_set_max_layer(CONFIG_MESH_MAX_LAYER));
    ESP_ERROR_CHECK(esp_mesh_set_vote_percentage(1));
    ESP_ERROR_CHECK(esp_mesh_set_ap_assoc_expire(30));
    mesh_cfg_t cfg = MESH_INIT_CONFIG_DEFAULT();
    /* mesh ID */
    memcpy((uint8_t *) &cfg.mesh_id, MESH_ID, 6);
    /* router */
    cfg.channel = CONFIG_MESH_CHANNEL;
    cfg.router.ssid_len = strlen(CONFIG_MESH_ROUTER_SSID);
    memcpy((uint8_t *) &cfg.router.ssid, CONFIG_MESH_ROUTER_SSID, cfg.router.ssid_len);
    memcpy((uint8_t *) &cfg.router.password, CONFIG_MESH_ROUTER_PASSWD,
           strlen(CONFIG_MESH_ROUTER_PASSWD));
    /* mesh softAP */
    ESP_ERROR_CHECK(esp_mesh_set_ap_authmode(CONFIG_MESH_AP_AUTHMODE6));
    cfg.mesh_ap.max_connection = CONFIG_MESH_AP_CONNECTIONS;
    memcpy((uint8_t *) &cfg.mesh_ap.password, CONFIG_MESH_AP_PASSWD,
           strlen(CONFIG_MESH_AP_PASSWD));
    ESP_ERROR_CHECK(esp_mesh_set_config(&cfg));
    /* mesh start */
    ESP_ERROR_CHECK(esp_mesh_start());
    ESP_LOGI("WIFI_INIT", "Mesh starts successfully, heap:%d, %s\n", esp_get_free_heap_size(),
             esp_mesh_is_root_fixed() ? "root fixed" : "root not fixed");

}

/*******************************************************
 *                Function Definitions BLE
 *******************************************************/
static void prov_complete(uint16_t net_idx, uint16_t addr, uint8_t flags, uint32_t iv_index) {
    ESP_LOGI(TAG_BLE, "net_idx: 0x%04x, addr: 0x%04x", net_idx, addr);
    ESP_LOGI(TAG_BLE, "flags: 0x%02x, iv_index: 0x%08x", flags, iv_index);
    board_led_operation(LED_BLE, LED_OFF);
    node_net_idx = net_idx;

    //inizializzo WIFI
    vTaskDelay(10000 / portTICK_PERIOD_MS);
    my_wifi_init();
}

static void example_ble_mesh_provisioning_cb(esp_ble_mesh_prov_cb_event_t event,
                                             esp_ble_mesh_prov_cb_param_t *param) {
    switch (event) {
        case ESP_BLE_MESH_PROV_REGISTER_COMP_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_PROV_REGISTER_COMP_EVT, err_code %d",
                     param->prov_register_comp.err_code);
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
    common.msg_timeout = 0; /* 0 indicates that timeout value from menuconfig will be used */ /* The default value (4 seconds) would be applied if the parameter msg_timeout is set to 0. */
    common.msg_role = ROLE_NODE;

    set.level_set.op_en = false;
    set.level_set.level = level;
    set.level_set.tid = msg_tid++;
    my_info_level = level;

    err = esp_ble_mesh_generic_client_set_state(&common, &set);
    if (err) {
        ESP_LOGE(TAG_BLE, "%s: Generic Level Set failed [%d]", __func__, level);
    }
    char level_c[7];
    sprintf(level_c, "%d", level);
    create_message_rapid("S", level_c, "3", 1);
    queue_operation('a', 'b', level);
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
