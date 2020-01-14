//
// Created by emilio on 14/01/20.
//

#ifndef INTERNAL_COMMUNICATION_BLE_MESH_DEMO_INIT_H
#define INTERNAL_COMMUNICATION_BLE_MESH_DEMO_INIT_H

#define TAG_BLE "BLE"

void ble_mesh_get_dev_uuid(uint8_t *dev_uuid);

esp_err_t bluetooth_init(void);

#endif //INTERNAL_COMMUNICATION_BLE_MESH_DEMO_INIT_H
