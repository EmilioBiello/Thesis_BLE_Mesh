import json
import datetime as dt
import glob
import os
import re
import sys

path_media = "/media/emilio/BLE/"


def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def get_file_from_directory(my_dir):
    list_of_files = glob.glob(my_dir)
    latest_file = max(list_of_files, key=os.path.getctime)
    print("Path: {}".format(latest_file))
    return latest_file


def save_json_data(path, data):
    print("\x1b[1;32;40m Saving: {}\x1b[0m".format(path))
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False)


def save_json_data_elegant(path, data):
    done, path_2 = get_path_media_or_PC(path_1=path)
    if done:
        path = path_2
        device = "on media/emilio/BLE"
    else:
        path = path_2
        device = "on PC"

    print("\x1b[1;32;40m Saving {}: {}\x1b[0m".format(device, path))
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=3)


def open_file_and_return_data(code, path):
    if code == 1:
        path = get_path_media_or_PC(path_1=path)
    with open(path) as json_file:
        data = json.load(json_file)
    return data


def print_data_as_json(data):
    print(json.dumps(data, default=convert_timestamp, ensure_ascii=False, sort_keys=True))


def define_directory(info):
    path = "./json_file/test_" + str(info) + str(dt.datetime.strftime(dt.datetime.now(), "%Y_%m_%d"))
    if not os.path.exists(path=path):
        os.makedirs(path)
    return path


def get_path_media_or_PC(path_1):
    media = "/media/emilio/BLE/"
    sub_dir = path_1.split('/')[1]
    file_name = path_1.split('/')[2]

    if os.path.exists(path=media):
        directory = media + "json_file/" + sub_dir + "/"
        path = directory + file_name
        done = True
    else:
        sub_dir = path_1.split('/')[2]
        file_name = path_1.split('/')[3]
        directory = "./json_file/" + sub_dir + "/"
        path = directory + file_name
        done = False

    if not os.path.exists(directory):
        os.makedirs(directory)

    return done, path


def get_mex_couple(list_of_items, value_to_find):
    list_of_keys = list()
    for i, dic in enumerate(list_of_items):
        if dic['message_id'] == value_to_find:
            list_of_keys.append(i)
    return list_of_keys


# verifico se l'elemento ha i campi (message_id,ttl,type_mex) settati in modo correttto
def look_into_element(e):
    match = False
    send = False
    if re.match("^[0-9]+", e['message_id']) and re.match("^[0-9|*]$", e['ttl']) and re.match("^[R|S|P|E]$",
                                                                                             e['type_mex']):
        match = True
        if re.match("^[S]$", e['type_mex']):
            send = True
    return match, e['message_id'], send


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds


def get_argument():
    re_path = "^json_file\/test_[0-9]{4}(_[0-9]{1,2}){2}\/test(_[0-9]{2}){3}-([0-9]{2}(_){0,1}){3}.json$"
    if len(sys.argv) != 2:
        raise Exception('\x1b[1;31;40m' + ' Wrong Arguments! ' + '\x1b[0m')
    elif not re.match(re_path, str(sys.argv[1])):
        raise Exception('\x1b[1;31;40m' + ' Wrong Path! ' + '\x1b[0m')
    else:
        print("Correct path!")
        return "./" + str(sys.argv[1])
