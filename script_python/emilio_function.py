import json
import datetime as dt
import glob
import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt

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


def save_json_data_2(path, data):
    print("\x1b[1;32;40m Saving: {}\x1b[0m".format(path))
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, indent=3)


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


def open_file_and_return_data(path, code=0):
    if code == 1:
        path = get_path_media_or_PC(path_1=path)
    with open(path) as json_file:
        data = json.load(json_file)
    return data


def print_data_as_json(data):
    print(json.dumps(data, default=convert_timestamp, ensure_ascii=False, sort_keys=True))


def print_info_as_json(info):
    print(json.dumps(info, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=3))


def define_directory(directory):
    if not os.path.exists(path=directory):
        os.makedirs(directory)
    return directory


def get_path_media_or_PC(path_1):
    media = "/media/emilio/BLE/"
    sub_dir = path_1.split('/')[2]
    file_name = path_1.split('/')[3]

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


def get_grouped_files(source_path, delay, index_delay):
    list_of_files = glob.glob(source_path)
    list_of_files.sort()

    for i in range(len(list_of_files)):
        name = list_of_files[i]
        data = open_file_and_return_data(name)
        if data['_command']['delay'] != delay[index_delay]:
            raise Exception(
                "\x1b[1;31;40m File Error in this directory. [{}] --> {} ]\x1b[0m".format(delay[index_delay], name))
    return list_of_files


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


def look_into_it(word_info, info_s, e):
    s = e['type_mex']
    my_type = ['send_ble', 'receive_ble', 'error_ble',
               'send_wifi', 'receive_wifi', 'error_wifi']
    if re.match("^[S]$", s):
        index = 0
    elif re.match("^[R]$", s):
        index = 1
    elif re.match("^[E]$", s):
        index = 2
    elif re.match("^[I]$", s):
        index = 3
    elif re.match("^[O]$", s):
        index = 4
    elif re.match("^[W]$", s):
        index = 5
    if my_type[index] in word_info:
        raise Exception("Double {} -> {}".format(my_type[index], e))
    word_info[my_type[index]] = e
    info_s[my_type[index]] += 1
    return word_info, info_s


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


###################################
# TODO STATISTICS
##################################
def intervalli_di_confidenza(dataset):
    # Intervallo di Confidenza al 95%
    # FORMULA: Za/2*q/sqrt(n)
    mean = np.mean(dataset)
    std = np.std(dataset)
    sample_size = len(dataset)
    quantile = 1.96
    margine_errore = quantile * (std / np.sqrt(sample_size))
    value_1 = mean - margine_errore
    value_2 = mean + margine_errore

    value = {'mean': mean, 'std': std, 'e_m': margine_errore, 'low': value_1, 'up': value_2}
    return value


###################################
# TODO PLOT
##################################
def plot_latency(dataset, run, type):
    if type == 'ble':
        if run == 1:
            color = "green"
        elif run == 2:
            color = "red"
        elif run == 3:
            color = "blue"
        elif run == 4:
            color = "orange"
        elif run == 5:
            color = "purple"
        else:
            color = "black"
    else:
        if run == 1:
            color = "tab:green"
        elif run == 2:
            color = "tab:red"
        elif run == 3:
            color = "tab:blue"
        elif run == 4:
            color = "tab:orange"
        elif run == 5:
            color = "tab:purple"
        else:
            color = "tab:black"

    text = type + " - run " + str(run)
    plt.scatter(dataset.keys(), dataset.values(), label=text, color=color, s=5)


# def save_plot(type):
#     title_str = "Relay_" + str(topic[index_topic]) + " Delay_" + str(delay[index_delay]) + "ms [" + type + "]"
#     plt.title(title_str)
#     plt.xlabel('x - packets')
#     plt.ylabel('y - latency [seconds]')
#     plt.legend()
#
#     path_graph = outcome_path + "latencies_" + str(delay[index_delay]) + "_" + type + ".png"
#     print("\x1b[1;32;40m Saving Graph {}: {}\x1b[0m".format(type, path_graph))
#     plt.savefig(path_graph)
#     plt.show()

def save_plot(type, title_str, path_graph):
    plt.title(title_str)
    plt.xlabel('x - packets')
    plt.ylabel('y - latency [seconds]')
    plt.legend()

    print("\x1b[1;32;40m Saving Graph {}: {}\x1b[0m".format(type, path_graph))
    plt.savefig(path_graph)
    plt.show()
