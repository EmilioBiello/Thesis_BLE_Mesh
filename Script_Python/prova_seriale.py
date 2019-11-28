import serial
import time
from threading import Thread, Event
import sys
import datetime as dt


port = "/dev/ttyUSB1"
baud = 115200
data = {}
event = Event()

esp32 = serial.Serial(port, baud, timeout=0)
time.sleep(1)  # give the connection a second to settle
if esp32.isOpen():
    print(esp32.name + " is open...")


def write_on_serial():
    while True:
        print('\x1b[0;33;40m' + "************" + '\x1b[0m')
        print('*** addr:status --> {1:on, 2:off}')
        print("* " + '\x1b[0;33;40m' + "exit" + '\x1b[0m' + ": \'" +
              '\x1b[1;31;40m' + "q" + '\x1b[0m' + "\' *\n")

        try:
            command = input("Insert command to send to esp32: \n")

            if command == 'q':
                event.set()
                print("Waiting for Save, max 5 s")
                break
            else:
                esp32.write(command.encode())
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
            break


def main():
    t1 = Thread(target=write_on_serial, )
    t1.start()
    read_from_serial()
    t1.join()
    esp32.close()
    sys.exit()


if __name__ == "__main__":
    main()
