import serial
import time
from threading import Thread, Event
import sys
import datetime as dt
# Regular Expression
import re
# EMILIO FUNCTION
import emilio_function as my

port = "/dev/ttyUSB0"
baud = 115200
data = {}
event = Event()
regular_expresion_command = "^(e|p|q)$"
regular_expresion_set_get = "^@,addr:(((0x){1}[a-fA-F-0-9]{4})|([0-9]{1,2}))(,level:[0-9]{1,5}(,ack:[0|1]){0,1}){0,1}$"
regular_expresion_rule = "^&,n_mex:[0-9]{1,5},addr:([0-9]{1,2}|0x[a-fA-F-0-9]{4}),delay:[0-9]{1,6}$"
regular_expresion_log = "^#,log:(0|1)$"

save_data = False
update_my_dictionary = False

esp32 = serial.Serial(port, baud, timeout=0.000001)
time.sleep(1)  # give the connection a second to settle
if esp32.isOpen():
    print(esp32.name + " is open...")


def reading():
    print('\x1b[0;33;40m' + "******" + '\x1b[0m')
    print(" - Rule: { &,n_mex:10,addr:0x0004,delay:1000 (ms)}")
    print(" - GET mex: {@,addr:0x0004}")
    print(" - SET_UNACK mex: { @,addr:0x0004,level:1 }")
    print(" - SET mex: { @,addr:0x0004,level:1,ack:0 }")
    print(" - send LOG to PC: {#,log:1}")
    print("*** " + '\x1b[0;33;40m' + "print JSON data" + '\x1b[0m' + ": \'" +
          '\x1b[1;31;40m' + "p" + '\x1b[0m' + "\' ***")
    print("*** " + '\x1b[0;33;40m' + "save and exit" + '\x1b[0m' + ": \'" +
          '\x1b[1;31;40m' + "q" + '\x1b[0m' + "\' ***")
    print("*** " + '\x1b[0;33;40m' + "exit" + '\x1b[0m' + ": \'" +
          '\x1b[1;31;40m' + "e" + '\x1b[0m' + "\' ***\n")


def write_on_serial():
    global save_data

    while True:
        reading()
        try:
            command = input("Insert command to send to esp32: \n")

            if re.match(regular_expresion_command, command) or re.match(regular_expresion_set_get, command) or \
                    re.match(regular_expresion_rule, command) or re.match(regular_expresion_log, command):
                if command == 'q' or command == 'e':
                    if command == 'q':
                        save_data = True
                        print("Waiting for Save")
                    event.set()
                    break
                elif command == 'p':
                    my.print_data_as_json(data)
                else:
                    esp32.write(command.encode())
                    add_command_to_dictionary(command)
                    print('\x1b[0;33;40m' + "******" + '\x1b[0m' + "\n")
            else:
                print('\x1b[6;30;41m' + "Wrong command" + '\x1b[0m')

        except KeyboardInterrupt:
            event.set()
            break


def read_from_serial():
    count = 0
    while True:
        received_data = esp32.readline()
        if len(received_data) > 0:
            update_dictionary(dt.datetime.now(), received_data.decode("utf-8"))
            count += 1
            if count % 50 == 0:
                print("************ " + str(count))
            # print('\x1b[1;31;40m' + "************" + '\x1b[0m   ')
            # print("Receiving...\n" + received_data.decode("utf-8"))

        if event.is_set():
            if save_data:
                if not bool(data):
                    print('\x1b[6;30;43m' + " Dictionary is empty! " + '\x1b[0m')
                else:
                    print('\x1b[6;30;42m' + " Saved! " + '\x1b[0m')
                    directory = my.define_directory(info="")
                    path = directory + '/test_' + dt.datetime.now().strftime("%y_%m_%d-%H_%M_%S") + '.json'
                    print(path)
                    my.save_json_data_elegant(path=path, data=data)
            else:
                print("goodbye")
            break


def add_command_to_dictionary(command):
    global update_my_dictionary
    if re.match(regular_expresion_rule, command):
        command_list = command.split(",")

        data['analysis_status'] = 0
        data['_command'] = {
            'first_char': command_list[0],
            'n_mex': int(command_list[1].split(":")[1]),
            'addr': command_list[2].split(":")[1],
            'delay': int(command_list[3].split(":")[1])
        }
        data['messages'] = []
        update_my_dictionary = True
    elif update_my_dictionary:
        update_my_dictionary = False


def update_dictionary(now, message):
    if update_my_dictionary:
        data['messages'].append({
            'message_id': message,
            'time': now
        })


def main():
    t1 = Thread(target=write_on_serial, )
    t1.start()
    read_from_serial()
    t1.join()
    esp32.close()
    sys.exit()


if __name__ == "__main__":
    main()
