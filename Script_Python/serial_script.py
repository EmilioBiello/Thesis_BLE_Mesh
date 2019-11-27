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
regular_expresion = "^remote_addr:(0x)[a-fA-F0-9]{4}|[0-9]{0,2},status:[0,1],opcode:[1-3]"

esp32 = serial.Serial(port, baud, timeout=0)
time.sleep(1)  # give the connection a second to settle
if esp32.isOpen():
    print(esp32.name + " is open...")


def write_on_serial():
    ran_thread = True
    while ran_thread:
        print('\x1b[0;33;40m' + "************" + '\x1b[0m')
        print("String characteristic:")
        print(" ******\tremote_addr:3,status:0,opcode:1\t******")
        print("- remote_addr:{0xFFFF, 0xc001, 3, 0x0004}")
        print("- status:{0 --> off, 1 --> on}")
        print("- opcode:{1 --> GET, 2 --> SET, 3 --> SET_UNACK}")
        print("* " + '\x1b[0;33;40m' + "save " + '\x1b[0m' +
              "JSON data and " + '\x1b[0;33;40m' + "exit" + '\x1b[0m' + ": \'" +
              '\x1b[1;31;40m' + "q" + '\x1b[0m' + "\' *\n")

        try:
            command = input("Insert command to send to esp32: \n")

            if command == 'q':
                event.set()
                ran_thread = False
                print("Waiting for Save, max 5 s")
            else:
                if re.search(regular_expresion, command):
                    esp32.write(command.encode())
                else:
                    print('\x1b[6;30;41m' + "Wrong command" + '\x1b[0m')
            print(dt.datetime.now())
            print('\x1b[0;33;40m' + "************" + '\x1b[0m' + "\n")
        except KeyboardInterrupt:
            event.set()
            break


def read_from_serial():
    while True:
        received_data = esp32.readline()
        if len(received_data) > 0:
            print('\x1b[1;31;40m' + "************" + '\x1b[0m   ')
            print(dt.datetime.now())
            print("Receiving...\n" + received_data.decode("utf-8"))
            print('\x1b[1;31;40m' + "************" + '\x1b[0m')

        if event.is_set():
            if not bool(data):
                print('\x1b[6;30;43m' + " Dictionary is empty! " + '\x1b[0m')
            else:
                print('\x1b[6;30;42m' + " Saved! " + '\x1b[0m')
                save_json_data()
            break


def save_json_data():
    file_name = 'json_file/json_data_' + dt.datetime.now().strftime("%y-%m-%d_%H-%M") + '.json'
    print("Path: {path}".format(path=file_name))
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, sort_keys=True, indent=4)


def main():
    t1 = Thread(target=write_on_serial, )
    t1.start()
    read_from_serial()
    t1.join()
    esp32.close()
    sys.exit()


if __name__ == "__main__":
    main()
