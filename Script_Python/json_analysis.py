import json
import datetime as dt
import statistics
import os
import glob


def get_file_from_directory():
    list_of_files = glob.glob('json_file/*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    print("Path: {}".format(latest_file))
    return latest_file


def get_same_element_index(list_of_items, value_to_find):
    list_of_keys = list()
    for i, dic in enumerate(list_of_items):
        if dic['message_id'] == value_to_find:
            list_of_keys.append(i)
    return list_of_keys


def print_dict_as_json(my_dictionary):
    print(json.dumps(my_dictionary, default=convert_timestamp, ensure_ascii=False, sort_keys=True))


def third_analysis(path):
    with open(path) as json_file:
        data = json.load(json_file)
        errors = data['error_second_analysis']

    if data['status_analysis'] != 2:
        raise BaseException('Phase 3 already executed')

    lost = 0
    not_sent = 0
    last = int(errors[0]['index'])
    for i, item in enumerate(errors):
        if int(item['index']) - last == 1:
            not_sent += 1
            print("Packet {} --> not sent".format(item['index']))
            # data['error_second_analysis'][i]['string'] = "Message not sent"
        else:
            lost += 1
            print("Packet {} --> TIMEOUT".format(item['index']))
            # data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
        last = int(item['index'])

    analysis = data['analysis']
    analysis['sent_mex'] = int(int(analysis['sent_mex']) - not_sent)
    analysis['lost_packet'] = int(int(analysis['lost_packet']) - lost)
    data['analysis'] = analysis

    # print_dict_as_json(data)
    data['status_analysis'] = 3
    return data


def second_analysis(path):
    check_utente = False
    with open(path) as json_file:
        data = json.load(json_file)
        command = data['command']
        messages = data['messages']

    if data['status_analysis'] != 1:
        raise BaseException('Phase 2 already executed')

    sent_mex = command['n_mex']
    # received_mex = len(messages) - int(sent_mex)
    received_mex = 0

    list_of_m_id = list()
    for item in messages:
        list_of_m_id.append(item['message_id'])

    list_of_m_id = list(dict.fromkeys(list_of_m_id))  # definisco una lista contenente i message_id
    if '0' in list_of_m_id:
        list_of_m_id.remove('0')

    differences = list()
    latencies = list()
    dict_analysis = dict()
    data['error_second_analysis'] = []
    for m_id in list_of_m_id:
        couple = get_same_element_index(messages, m_id)  # individuo le coppie di messaggi

        if len(couple) == 2:
            received_mex += 1
            send_time = messages[couple[0]]['time']
            receive_time = messages[couple[1]]['time']

            send_datetime = dt.datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S.%f')
            receive_datetime = dt.datetime.strptime(receive_time, '%Y-%m-%d %H:%M:%S.%f')

            # timedelta output (days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            # 1 millisecond --> 1000 microseconds
            difference = receive_datetime - send_datetime
            differences.append(difference.total_seconds())
            latencies.append(difference.total_seconds() / 2)

            dict_analysis[m_id] = {
                'time_send': send_time,
                'time_ack': receive_time,
                'difference': difference.total_seconds(),
                'latency': (difference.total_seconds() / 2)
            }
            print("m_id: {} --> {}".format(m_id, dict_analysis[m_id]['difference']))
        elif len(couple) == 1:
            if not check_utente:
                check_utente = True
            data['error_second_analysis'].append({'index': m_id, 'string': 'TimeOut or message not sent'})
            print("m_id: {} --> TimeOut or message not sent".format(m_id))

    data['second_analysis'] = dict_analysis
    lost_packets = int(sent_mex) - int(received_mex)
    print("--- Summit ---")
    print("Sent messages: {}, Received messages: {}, Losts: {}".format(sent_mex, received_mex, lost_packets))
    print("Average difference send & receive: {}s - {}ms".format(statistics.mean(differences),
                                                                 statistics.mean(differences) * 1000))
    data['analysis'] = {
        'sent_mex': int(sent_mex),
        'received_mex': int(received_mex),
        'lost_packet': int(lost_packets),
        'average_diff': statistics.mean(differences) * 1000,  # milliseconds
        'average_latency': statistics.mean(latencies) * 1000  # milliseconds
    }
    data['status_analysis'] = 2
    return data, check_utente


def first_analysis(path):
    check_utene = False
    with open(path) as json_file:
        data = json.load(json_file)

        if data['status_analysis'] != 0:
            raise BaseException('Phase 1 already executed')

        data['error_first_analysis'] = []
        for mex in data['messages']:
            if mex['len'] != 5 and mex['len'] != 6:
                data['error_first_analysis'].append({'time': mex['time'], 'string': mex['message_id']})
                if not check_utene:
                    check_utene = True
            else:
                m_id = mex['message_id'].split(',')[1]
                type_mex = mex['message_id'].split(',')[0]
                ttl_mex = mex['message_id'].split(',')[2]

                mex['message_id'] = m_id
                mex['type_mex'] = type_mex
                mex['ttl'] = ttl_mex

        data['status_analysis'] = 1
        return data, check_utene


def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def save_json_data(path, data):
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)


def main():
    checks = False
    path = get_file_from_directory()

    try:
        my_data, checks = first_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        input("Richiesto intervento poiché c'è un errore, analizzare \'error_first_analysis\'")
    else:
        print("Fase 1 completata")

    try:
        my_data, checks = second_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        print("Ci sono dei pacchetti persi, analizzare \'error_second_analysis\'")
    else:
        print("Fase 1 completata")


def main2():
    path = "./json_file/json_data_19-12-03_13-01.json"
    checks = False

    try:
        my_data, checks = first_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        input("Richiesto intervento poiché c'è un errore, analizzare \'error_first_analysis\'")
    else:
        print("Fase 1 completata")

    try:
        my_data, checks = second_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        print("Ci sono dei pacchetti persi, analizzare \'error_second_analysis\'")
    else:
        print("Fase 2 completata")

    try:
        my_data = third_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)
    print("Fase 3 completata")


if __name__ == "__main__":
    main2()
