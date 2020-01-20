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
/* WIFI */
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

uint8_t status_led_ble = 1;
uint8_t status_led_wifi = 1;

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

mesh_light_ctl_t light_on = {
        .cmd = MESH_CONTROL_CMD,
        .on = 1,
        .token_id = MESH_TOKEN_ID,
        .token_value = MESH_TOKEN_VALUE,
};

mesh_light_ctl_t light_off = {
        .cmd = MESH_CONTROL_CMD,
        .on = 0,
        .token_id = MESH_TOKEN_ID,
        .token_value = MESH_TOKEN_VALUE,
};

/*******************************************************
 *                Variable Definitions BLE
 *******************************************************/
extern struct _led_state led_state[2];

static uint8_t dev_uuid[16] = {0xdd, 0xdd};

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

ESP_BLE_MESH_MODEL_PUB_DEFINE(level_pub_0, 2 + 3, ROLE_NODE);
static esp_ble_mesh_gen_onoff_srv_t level_server_0 = {
        .rsp_ctrl.get_auto_rsp = ESP_BLE_MESH_SERVER_AUTO_RSP,
        .rsp_ctrl.set_auto_rsp = ESP_BLE_MESH_SERVER_AUTO_RSP,
};

ESP_BLE_MESH_MODEL_PUB_DEFINE(level_pub_1, 2 + 3, ROLE_NODE);
static esp_ble_mesh_gen_onoff_srv_t level_server_1 = {
        .rsp_ctrl.get_auto_rsp = ESP_BLE_MESH_SERVER_RSP_BY_APP,
        .rsp_ctrl.set_auto_rsp = ESP_BLE_MESH_SERVER_RSP_BY_APP,
};

static esp_ble_mesh_model_t root_models[] = {
        ESP_BLE_MESH_MODEL_CFG_SRV(&config_server),
        ESP_BLE_MESH_MODEL_GEN_LEVEL_SRV(&level_pub_0, &level_server_0),
};

static esp_ble_mesh_model_t extend_model_0[] = {
        ESP_BLE_MESH_MODEL_GEN_LEVEL_SRV(&level_pub_1, &level_server_1),
};


static esp_ble_mesh_elem_t elements[] = {
        ESP_BLE_MESH_ELEMENT(0, root_models, ESP_BLE_MESH_MODEL_NONE),
        ESP_BLE_MESH_ELEMENT(0, extend_model_0, ESP_BLE_MESH_MODEL_NONE),
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
void esp_mesh_p2p_tx_main(void *arg) {
    int i;
    esp_err_t err;
    int send_count = 0;
    mesh_addr_t route_table[CONFIG_MESH_ROUTE_TABLE_SIZE];
    int route_table_size = 0;
    mesh_data_t data;
    data.data = tx_buf;
    data.size = sizeof(tx_buf);
    data.proto = MESH_PROTO_BIN;
    data.tos = MESH_TOS_P2P;
    is_running = true;

    while (is_running) {
        /* non-root do nothing but print */
        if (!esp_mesh_is_root()) {
            ESP_LOGI(TAG_WIFI, "Layer:%d, rtableSize:%d, %s", mesh_layer,
                     esp_mesh_get_routing_table_size(),
                     (is_mesh_connected && esp_mesh_is_root()) ? "ROOT" : is_mesh_connected ? "NODE" : "DISCONNECT");
            vTaskDelay(10 * 1000 / portTICK_RATE_MS);
            continue;
        }
        esp_mesh_get_routing_table((mesh_addr_t *) &route_table, CONFIG_MESH_ROUTE_TABLE_SIZE * 6, &route_table_size);
        if (send_count && !(send_count % 100)) {
            ESP_LOGI(TAG_WIFI, "size:%d/%d,send_count:%d", route_table_size, esp_mesh_get_routing_table_size(),
                     send_count);
        }
        send_count++;
        tx_buf[25] = (send_count >> 24) & 0xff;
        tx_buf[24] = (send_count >> 16) & 0xff;
        tx_buf[23] = (send_count >> 8) & 0xff;
        tx_buf[22] = (send_count >> 0) & 0xff;

        if (send_count % 2) {
            memcpy(tx_buf, (uint8_t *) &light_on, sizeof(light_on));
        } else {
            memcpy(tx_buf, (uint8_t *) &light_off, sizeof(light_off));
        }

        ESP_LOGI(TAG_WIFI, "[L:%d][table_size:%d][parent: "
                MACSTR
                "][me: "
                MACSTR
                "]\n", mesh_layer, esp_mesh_get_routing_table_size(), MAC2STR(mesh_parent_addr.addr),
                 MAC2STR(route_table[0].addr));
        for (i = 0; i < route_table_size; i++) {
            err = esp_mesh_send(&route_table[i], &data, MESH_DATA_P2P, NULL, 0);
            if (err) {
                ESP_LOGE(TAG_WIFI,
                         "[ROOT-2-UNICAST:%d][L:%d]parent:"
                                 MACSTR
                                 " to "
                                 MACSTR
                                 ", heap:%d[err:0x%x, proto:%d, tos:%d]",
                         send_count, mesh_layer, MAC2STR(mesh_parent_addr.addr),
                         MAC2STR(route_table[i].addr), esp_get_free_heap_size(),
                         err, data.proto, data.tos);
            } else if (!(send_count % 100)) {
                ESP_LOGW(TAG_WIFI,
                         "[ROOT-2-UNICAST:%d][L:%d][rtableSize:%d]parent:"
                                 MACSTR
                                 " to "
                                 MACSTR
                                 ", heap:%d[err:0x%x, proto:%d, tos:%d]",
                         send_count, mesh_layer,
                         esp_mesh_get_routing_table_size(),
                         MAC2STR(mesh_parent_addr.addr),
                         MAC2STR(route_table[i].addr), esp_get_free_heap_size(),
                         err, data.proto, data.tos);
            } else {
                ESP_LOGI("Mex_Sent", "[#TX:%d][to: "
                        MACSTR
                        "]\n", send_count, MAC2STR(route_table[i].addr));
            }
        }
        /* if route_table_size is less than 10, add delay to avoid watchdog in this task. */
        if (route_table_size < 5) {
            vTaskDelay(10 * 1000 / portTICK_RATE_MS);
        }
    }
    vTaskDelete(NULL);
}

void send_data(mesh_addr_t from, mesh_data_t data) {
    esp_err_t err;
    err = esp_mesh_send(&from, &data, MESH_DATA_P2P, NULL, 0);
    if (err) {
        ESP_LOGE(TAG_WIFI, "[ROOT-2-UNICAST][L:%d] from: "
                MACSTR
                ", heap:%d[err:0x%x, proto:%d, tos:%d]",
                 mesh_layer, MAC2STR(from.addr), esp_get_free_heap_size(), err, data.proto, data.tos);
    } else {
        ESP_LOGW("SEND_MEX", "To: "
                MACSTR
                " ", MAC2STR(from.addr));
    }
}

void esp_mesh_p2p_rx_main(void *arg) {
    esp_err_t err;
    mesh_addr_t from;
    // int value = 0;
    mesh_data_t data;
    int flag = 0;
    data.data = rx_buf;
    data.size = RX_SIZE;
    is_running = true;

    while (is_running) {
        data.size = RX_SIZE;
        err = esp_mesh_recv(&from, &data, portMAX_DELAY, &flag, NULL, 0);
        if (err != ESP_OK || !data.size) {
            ESP_LOGE(TAG_WIFI, "err:0x%x, size:%d", err, data.size);
            continue;
        }
        /* extract value */
//        if (data.size >= sizeof(value)) {
//            value = (data.data[25] << 24) | (data.data[24] << 16) | (data.data[23] << 8) | data.data[22];
//        }

        /* ACK */
        send_data(from, data);

        /* process light control */
        //mesh_light_process(&from, data.data, data.size);
        board_led_operation_wifi(LED_WIFI, status_led_wifi);

        status_led_wifi = !status_led_wifi;
//        ESP_LOGW(TAG_WIFI,
//                 "[#RX:%d][L:%d] parent:"
//                         MACSTR
//                         ", receive from "
//                         MACSTR
//                         ", size:%d, heap:%d, flag:%d[err:0x%x, proto:%d, tos:%d]",
//                 value, mesh_layer, MAC2STR(mesh_parent_addr.addr), MAC2STR(from.addr), data.size,
//                 esp_get_free_heap_size(), flag, err, data.proto, data.tos);
    }
    vTaskDelete(NULL);
}

esp_err_t esp_mesh_comm_p2p_start(void) {
    static bool is_comm_p2p_started = false;
    if (!is_comm_p2p_started) {
        is_comm_p2p_started = true;
        // xTaskCreate(esp_mesh_p2p_tx_main, "MPTX", 3072, NULL, 5, NULL);
        xTaskCreate(esp_mesh_p2p_rx_main, "MPRX", 3072, NULL, 5, NULL);
    }
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
        }
            break;
        case MESH_EVENT_CHILD_DISCONNECTED: {
            mesh_event_child_disconnected_t *child_disconnected = (mesh_event_child_disconnected_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_CHILD_DISCONNECTED>aid:%d, "
                    MACSTR
                    "",
                     child_disconnected->aid,
                     MAC2STR(child_disconnected->mac));
        }
            break;
        case MESH_EVENT_ROUTING_TABLE_ADD: {
            mesh_event_routing_table_change_t *routing_table = (mesh_event_routing_table_change_t *) event_data;
            ESP_LOGW(TAG_WIFI, "<MESH_EVENT_ROUTING_TABLE_ADD>add %d, new:%d",
                     routing_table->rt_size_change,
                     routing_table->rt_size_new);
        }
            break;
        case MESH_EVENT_ROUTING_TABLE_REMOVE: {
            mesh_event_routing_table_change_t *routing_table = (mesh_event_routing_table_change_t *) event_data;
            ESP_LOGW(TAG_WIFI, "<MESH_EVENT_ROUTING_TABLE_REMOVE>remove %d, new:%d",
                     routing_table->rt_size_change,
                     routing_table->rt_size_new);
        }
            break;
        case MESH_EVENT_NO_PARENT_FOUND: {
            mesh_event_no_parent_found_t *no_parent = (mesh_event_no_parent_found_t *) event_data;
            ESP_LOGI(TAG_WIFI, "<MESH_EVENT_NO_PARENT_FOUND>scan times:%d",
                     no_parent->scan_times);
        }
            /* TODO handler for the failure */
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
            esp_mesh_comm_p2p_start();
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
    ESP_ERROR_CHECK(esp_mesh_set_ap_assoc_expire(10));
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
    ESP_ERROR_CHECK(esp_mesh_set_ap_authmode(CONFIG_MESH_AP_AUTHMODE));
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

    //inizializzo WIFI
    vTaskDelay(10000 / portTICK_PERIOD_MS);
    my_wifi_init();
}

static void example_change_led_state(esp_ble_mesh_model_t *model, esp_ble_mesh_msg_ctx_t *ctx) {
    uint16_t primary_addr = esp_ble_mesh_get_primary_element_address();
    uint8_t elem_count = esp_ble_mesh_get_element_count();
    struct _led_state *led = NULL;
    uint8_t i;
    //printf("%s - [src: %hu dst: %hu ttl: %hhu] --> status: %hhu\n", __func__, ctx->addr, ctx->recv_dst, ctx->recv_ttl, status_led_ble);

    if (ESP_BLE_MESH_ADDR_IS_UNICAST(ctx->recv_dst)) {
        for (i = 0; i < elem_count; i++) {
            if (ctx->recv_dst == (primary_addr + i)) {
                led = &led_state[i];
                board_led_operation(led->pin, status_led_ble);
            }
        }
    } else if (ESP_BLE_MESH_ADDR_IS_GROUP(ctx->recv_dst)) {
        if (esp_ble_mesh_is_model_subscribed_to_group(model, ctx->recv_dst)) {
            led = &led_state[model->element->element_addr - primary_addr];
            board_led_operation(led->pin, status_led_ble);
        }
    } else if (ctx->recv_dst == 0xFFFF) {
        led = &led_state[model->element->element_addr - primary_addr];
        board_led_operation(led->pin, status_led_ble);
    }

    status_led_ble = !status_led_ble;
}

static void example_handle_gen_level_msg(esp_ble_mesh_model_t *model, esp_ble_mesh_msg_ctx_t *ctx,
                                         esp_ble_mesh_server_recv_gen_level_set_t *set) {
    esp_ble_mesh_gen_level_srv_t *srv = model->user_data;

    switch (ctx->recv_op) {
        case ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_GET:
            esp_ble_mesh_server_model_send_msg(model, ctx, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_STATUS,
                                               sizeof(srv->state.level), (uint8_t *) &srv->state.level);

            break;
        case ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET:
        case ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK:
//            if (set->op_en == false) {
//                srv->state.level = set->level;
//            } else {
//                /* TODO: Delay and state transition */
//                srv->state.level = set->level;
//            }

            srv->state.level = set->level;
//            if (ctx->recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET) {
//                esp_ble_mesh_server_model_send_msg(model, ctx, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_STATUS,
//                                                   sizeof(srv->state.level), (uint8_t *) &srv->state.level);
//                ESP_LOGI("MessaggioRicevuto", "LEVEL_SET, level %d --> ttl: %d - %d", srv->state.level, ctx->recv_ttl,
//                         ctx->send_ttl);
//            }

            ctx->send_ttl = 3;
            esp_ble_mesh_server_model_send_msg(model, ctx, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_STATUS,
                                               sizeof(srv->state.level), (uint8_t *) &srv->state.level);
            printf("PC: level: %d, ttl: %d\n", srv->state.level, ctx->recv_ttl);

//            if (model->pub->publish_addr != ESP_BLE_MESH_ADDR_UNASSIGNED) {
//                esp_ble_mesh_model_publish(model, ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_STATUS, sizeof(srv->state.level),
//                                           (uint8_t *) &srv->state.level, ROLE_NODE);
//            }
            example_change_led_state(model, ctx);
            break;
        default:
            printf("%s --> DEFAULT STATE", __func__);
            break;
    }
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
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_PROV_RESET_EVT");
            break;
        case ESP_BLE_MESH_NODE_SET_UNPROV_DEV_NAME_COMP_EVT:
            ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_NODE_SET_UNPROV_DEV_NAME_COMP_EVT, err_code %d",
                     param->node_set_unprov_dev_name_comp.err_code);
            break;
        default:
            break;
    }
}


static void example_ble_mesh_generic_server_cb(esp_ble_mesh_generic_server_cb_event_t event,
                                               esp_ble_mesh_generic_server_cb_param_t *param) {
    printf("----\n");
    ESP_LOGI(TAG_BLE, "event 0x%02x, opcode 0x%04x, src 0x%04x, dst 0x%04x recv_ttl 0x%04x",
             event, param->ctx.recv_op, param->ctx.addr, param->ctx.recv_dst, param->ctx.recv_ttl);

    switch (event) {
        case ESP_BLE_MESH_GENERIC_SERVER_STATE_CHANGE_EVT:
            // Messaggio Ricevuto da tutti i nodi
            if (param->ctx.recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET ||
                param->ctx.recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK) {
                example_change_led_state(param->model, &param->ctx);
                ESP_LOGI(TAG_BLE, "STATE_CHANGE_EVT --> Level %d", param->value.state_change.level_set.level);
            }
            break;
        case ESP_BLE_MESH_GENERIC_SERVER_RECV_GET_MSG_EVT:
            if (param->ctx.recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_GET) {
                example_handle_gen_level_msg(param->model, &param->ctx, NULL);
            }
            ESP_LOGI(TAG_BLE, "GET_MSG_EVT");
            break;
        case ESP_BLE_MESH_GENERIC_SERVER_RECV_SET_MSG_EVT:
            // MEssaggio Ricevuto all'indirizzo specifico
            if (param->ctx.recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET ||
                param->ctx.recv_op == ESP_BLE_MESH_MODEL_OP_GEN_LEVEL_SET_UNACK) {
                example_handle_gen_level_msg(param->model, &param->ctx, &param->value.set.level);
                // ESP_LOGI(TAG_BLE, "LEVEL %d, tid %d", param->value.set.level.level, param->value.set.level.tid);
                if (param->value.set.level.op_en) {
                    ESP_LOGI(TAG_BLE, "trans_time 0x%02x, delay 0x%02x", param->value.set.level.trans_time,
                             param->value.set.level.delay);
                }
            }
            ESP_LOGI(TAG_BLE, "SET_MSG_EVT");
            break;
        default:
            ESP_LOGE(TAG_BLE, "Unknown Generic Server event 0x%02x", event);
            break;
    }
    printf("----\n");
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
                break;
            case ESP_BLE_MESH_MODEL_OP_MODEL_SUB_ADD:
                ESP_LOGI(TAG_BLE, "ESP_BLE_MESH_MODEL_OP_MODEL_SUB_ADD");
                ESP_LOGI(TAG_BLE, "elem_addr 0x%04x, sub_addr 0x%04x, cid 0x%04x, mod_id 0x%04x",
                         param->value.state_change.mod_sub_add.element_addr,
                         param->value.state_change.mod_sub_add.sub_addr,
                         param->value.state_change.mod_sub_add.company_id,
                         param->value.state_change.mod_sub_add.model_id);
                break;
            default:
                break;
        }
    }
}

static esp_err_t ble_mesh_init(void) {
    esp_err_t err;

    // is used to register callback function used to handle provisioning and networking related events
    esp_ble_mesh_register_prov_callback(example_ble_mesh_provisioning_cb);
    // is used to register callback function used to handle Configuration Server Model related events
    esp_ble_mesh_register_config_server_callback(example_ble_mesh_config_server_cb);
    //
    esp_ble_mesh_register_generic_server_callback(example_ble_mesh_generic_server_cb);

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
