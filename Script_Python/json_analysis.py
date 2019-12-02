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


def second_analysis(path):
    with open(path) as json_file:
        data = json.load(json_file)
        command = data['command']
        messages = data['messages']

    if data['status_analysis'] != 1:
        raise BaseException('Phase 2 already executed')

    sent_mex = command['n_mex']
    received_mex = len(messages) - int(sent_mex)

    list_of_m_id = list()
    for item in messages:
        list_of_m_id.append(item['message_id'])

    list_of_m_id = list(dict.fromkeys(list_of_m_id))

    new_mex = dict()
    differences = list()
    latencies = list()
    for m_id in list_of_m_id:
        couple = get_same_element_index(messages, m_id)

        if len(couple) == 2:
            set_time = messages[couple[0]]['time']
            status_time = messages[couple[1]]['time']

            set_datetime = dt.datetime.strptime(set_time, '%Y-%m-%d %H:%M:%S.%f')
            status_datetime = dt.datetime.strptime(status_time, '%Y-%m-%d %H:%M:%S.%f')

            # timedelta output (days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            # 1 millisecond --> 1000 microseconds
            difference = status_datetime - set_datetime
            differences.append(difference.total_seconds())
            latencies.append(difference.total_seconds() / 2)

            new_mex[m_id] = {
                'time_send': set_time,
                'time_ack': status_time,
                'difference': difference
            }

        print("m_id: {} --> {}  --> {}".format(m_id, couple, new_mex[m_id]['difference']))

    print("--- Summit ---")
    print("Sent messages: {}, Received messages: {}".format(sent_mex, received_mex))
    print("Average difference send & receive: {}s - {}ms".format(statistics.mean(differences),
                                                                 statistics.mean(differences) * 1000))
    data['analysis'] = {
        'sent_mex': int(sent_mex),
        'received_mex': int(received_mex),
        'average_diff': statistics.mean(differences) * 1000,  # milliseconds
        'average_latency': statistics.mean(latencies) * 1000  # milliseconds
    }
    data['status_analysis'] = 2
    return data


def first_analysis(path):
    with open(path) as json_file:
        data = json.load(json_file)

        if data['status_analysis'] != 0:
            raise BaseException('Phase 1 already executed')

        for mex in data['messages']:
            m_id = mex['message_id'].split(',')[1]
            type_mex = mex['message_id'].split(',')[0]

            mex['message_id'] = m_id
            mex['type_mex'] = type_mex
            # print("len: {}".format(mex['len']))
            # print("message_id: {}".format(mex['message_id']))
            # print("time: {}".format(mex['time']))
            # print("type_mex: {}".format(mex['type_mex']))
            # print('')
        data['status_analysis'] = 1
        return data


def convert_timestamp(item_data_object):
    if isinstance(item_data_object, dt.datetime):
        return item_data_object.__str__()


def save_json_data(path, data):
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, default=convert_timestamp, ensure_ascii=False, sort_keys=True, indent=4)


def main():
    #path = "./json_file/json_data_19-12-02_18-12.json"
    path = get_file_from_directory()

    try:
        my_data = first_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    try:
        my_data = second_analysis(path=path)
        save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)


if __name__ == "__main__":
    main()
