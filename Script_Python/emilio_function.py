import json
import datetime as dt
import glob
import os


def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def get_file_from_directory(my_dir):
    list_of_files = glob.glob(my_dir)
    latest_file = max(list_of_files, key=os.path.getctime)
    print("Path: {}".format(latest_file))
    return latest_file


def save_json_data(path, data):
    print(path)
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)


def print_data_as_json(data):
    print(json.dumps(data, default=convert_timestamp, ensure_ascii=False, sort_keys=True))


def define_directory(info):
    path = "./json_file/test_" + str(info) + str(dt.datetime.strftime(dt.datetime.now(), "%Y_%m_%d"))
    if not os.path.exists(path=path):
        os.makedirs(path)
    return path


def get_same_element_index(list_of_items, value_to_find):
    list_of_keys = list()
    for i, dic in enumerate(list_of_items):
        if dic['message_id'] == value_to_find:
            list_of_keys.append(i)
    return list_of_keys


def test_fun_2(path):
    with open(path) as json_file:
        data = json.load(json_file)
        messages = data['messages']

    list_of_m_id = list()
    for item in messages:
        list_of_m_id.append(item['message_id'])

    list_of_m_id = list(dict.fromkeys(list_of_m_id))  # definisco una lista contenente i message_id
    if '0' in list_of_m_id:
        list_of_m_id.remove('0')

    for m_id in list_of_m_id:
        couple = get_same_element_index(messages, m_id)  # individuo le coppie di messaggi

        if len(couple) == 2:
            print("m_id: {} --> {}".format(m_id, couple))
        elif len(couple) == 1:
            size_messages = len(messages)
            if couple[0] + 1 < size_messages:
                next_mex = messages[couple[0] + 1]
                data['error_second_analysis'].append({'index': m_id, 'next_mex': {'message_id': next_mex['message_id'],
                                                                                  'type_mex': next_mex['type_mex']
                                                                                  },
                                                      'string': 'TimeOut or message not sent'})
            else:
                data['error_second_analysis'].append({'index': m_id, 'string': 'TimeOut or message not sent'})

            print("m_id: {} --> TimeOut or message not sent".format(m_id))
    print(data['error_second_analysis'])
    save_json_data(path=path, data=data)


def test_fun_3(path):
    with open(path) as json_file:
        data = json.load(json_file)
    errors = data['error_second_analysis']

    lost = 0
    not_sent = 0
    last = int(errors[0]['index'])
    list_lost = list()
    list_not_sent = list()
    for i, item in enumerate(errors):
        if int(item['index']) - last == 1:
            if int(item['next_mex']['message_id']) == 0:
                not_sent += 1
                print("Packet {} --> not sent".format(item['index']))
                data['error_second_analysis'][i]['string'] = "Message not sent"
                list_not_sent.append(int(item['index']))
            else:
                lost += 1
                print("Packet {} --> TIMEOUT".format(item['index']))
                data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
                list_lost.append(int(item['index']))
        else:
            lost += 1
            print("Packet {} --> TIMEOUT".format(item['index']))
            data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
            list_lost.append(int(item['index']))
        last = int(item['index'])

    data['analysis']['list_lost'] = list_lost
    data['analysis']['list_not_sent'] = list_not_sent

    if int(data['analysis']['sent_mex']) - int(data['analysis']['received_mex']) - int(
            data['analysis']['lost_packet']) == 0:
        print("Correct analysis")
    else:
        print("Error about counting")

    save_json_data(path=path, data=data)


def main3():
    path = "./json_file/json_data_19-12-03_12-47.json"
    print(path)
    x = input("fun1")
    if x == 'y':
        test_fun_2(path)

    x = input("fun2")
    if x == 'y':
        test_fun_3(path)
