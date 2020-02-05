#ifndef __BLE_MESH_INIT_H__
#define __BLE_MESH_INIT_H__
#define TAG_BLE "BLE"

void ble_mesh_get_dev_uuid(uint8_t *dev_uuid);

esp_err_t bluetooth_init(void);

#endif //MANUAL_NETWORKING_BLE_MESH_INIT_H
