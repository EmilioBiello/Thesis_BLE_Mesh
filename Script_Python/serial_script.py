import serial
import time
from threading import Thread, Event
import sys
# JSON
import json
import datetime as dt
# Regular Expression
import re

port = "/dev/ttyUSB1"
baud = 115200
data = {}
event = Event()
regular_expresion_set = "^addr:([0-9]{1,2}|0x[a-fA-F-0-9]{4}),status:[0-9],opcode:[2,3]$"
regular_expresion_get = "^addr:([0-9]{1,2}|0x[a-fA-F-0-9]{4}),opcode:1$"
regular_expresion_command = "^(e|p|q)$"
regular_expresion_log = "^log:(0|1)$"

save_data = False
default_0 = "addr:0x0003,status:0,opcode:2"
default_1 = "addr:0x0003,status:1,opcode:2"
command_send = ""

esp32 = serial.Serial(port, baud, timeout=0)
time.sleep(1)  # give the connection a second to settle
if esp32.isOpen():
    print(esp32.name + " is open...")


def write_on_serial():
    global save_data
    global command_send
    counter = 0
    while True:
        print('\x1b[0;33;40m' + "******" + '\x1b[0m')
        print(" ******\taddr:0x0004,status:1,opcode:3\t******")
        print("- remote_addr: {0xFFFF, 0xc001, 3, 0x0004}")
        print("- status: {0 --> off, 1 --> on}")
        print("- opcode: {1 --> GET, 2 --> SET, 3 --> SET_UNACK}")
        print("*** " + '\x1b[0;33;40m' + "print JSON data" + '\x1b[0m' + ": \'" +
              '\x1b[1;31;40m' + "p" + '\x1b[0m' + "\' ***")
        print("*** " + '\x1b[0;33;40m' + "save and exit" + '\x1b[0m' + ": \'" +
              '\x1b[1;31;40m' + "q" + '\x1b[0m' + "\' ***")
        print("*** " + '\x1b[0;33;40m' + "exit" + '\x1b[0m' + ": \'" +
              '\x1b[1;31;40m' + "e" + '\x1b[0m' + "\' ***\n")

        try:
            command = input("Insert command to send to esp32: \n")

            if re.search(regular_expresion_set, command) or re.search(regular_expresion_get, command) or re.search(
                    regular_expresion_command, command) or re.search(regular_expresion_log, command):
                if command == 'q' or command == 'e':
                    if command == 'q':
                        save_data = True
                        print("Waiting for Save")
                    event.set()
                    break
                elif command == 'p':
                    print_data_as_json()
                else:
                    esp32.write(command.encode())
                    command_send = command
                    counter += 1
                    print('\x1b[0;33;40m' + "******" + str(counter) + '\x1b[0m' + "\n")
            else:
                print('\x1b[6;30;41m' + "Wrong command" + '\x1b[0m')

        except KeyboardInterrupt:
            event.set()
            break


def read_from_serial():
    while True:
        received_data = esp32.readline()
        if len(received_data) > 0:
            # print('\x1b[1;31;40m' + "************" + '\x1b[0m   ')
            # print("Receiving...\n" + received_data.decode("utf-8"))
            update_dictionary(dt.datetime.now(), received_data.decode("utf-8"))
            print('\x1b[1;31;40m' + "************" + '\x1b[0m')

        if event.is_set():
            if save_data:
                if not bool(data):
                    print('\x1b[6;30;43m' + " Dictionary is empty! " + '\x1b[0m')
                else:
                    print('\x1b[6;30;42m' + " Saved! " + '\x1b[0m')
                    save_json_data()
            else:
                print("goodbye")
            break


def update_dictionary(now, message):
    mex_list = message.split(",")
    mex_list[0] = mex_list[0].replace("-", "")
    size = len(mex_list)

    if not bool(data):
        data['message'] = []

    data['message'].append({
        'command': command_send,
        'receiver': '' if size < 1 else mex_list[0],
        'status': '' if size < 2 else mex_list[1],
        'type_mex': '' if size < 3 else mex_list[2],
        'message_id': '' if size < 4 else mex_list[3],
        'time': now
    })


# Allow to serialize datetime into JSON string
def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def save_json_data():
    path = './json_file/json_data_' + dt.datetime.now().strftime("%y-%m-%d_%H-%M") + '.json'
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)


def print_data_as_json():
    data_json = json.dumps(data, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)
    print(data_json)


def main():
    t1 = Thread(target=write_on_serial, )
    t1.start()
    read_from_serial()
    t1.join()
    esp32.close()
    sys.exit()


if __name__ == "__main__":
    main()
