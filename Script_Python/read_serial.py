import serial
import time
import sys
# JSON
import json
import datetime as dt

port = "/dev/ttyUSB0"
baud = 115200
data = {'messages': []}

esp32 = serial.Serial(port, baud, timeout=0.005)
time.sleep(1)  # give the connection a second to settle
if esp32.isOpen():
    print(esp32.name + " is open...")


def update_dictionary(now, message):
    if "PC:" in message:
        print("Size: ", len(message))
        data['messages'].append({
            'type_mex': message,
            'message_id': message,
            'len': len(message),
            'time': now
        })


def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def save_json_data():
    path = './json_file/json_data_' + dt.datetime.now().strftime("%y-%m-%d_%H-%M") + '.json'
    print(path)
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)


def read_from_serial():
    while True:
        try:
            received_data = esp32.readline()
            if len(received_data) > 0:
                update_dictionary(dt.datetime.now(), received_data.decode("utf-8"))
                print("- ", received_data.decode("utf-8"))
        except KeyboardInterrupt:
            save_json_data()
            print("Goodbye")
            break


def main():
    read_from_serial()
    esp32.close()
    sys.exit()


if __name__ == "__main__":
    main()
