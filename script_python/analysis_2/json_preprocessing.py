import datetime as dt
import statistics
import emilio_function as my
import re
import time
import glob
import sys

relay = 0  # 0,1,2
path_pc = "./"
path_media = "/media/emilio/BLE/"
file_name = "../json_file/test_2020_02_01/test_20_02_01-09_17_46.json"
path = path_pc + file_name

preprocessing_path = file_name[:-5] + "_preprocessing.json"
analysis_path = file_name[:-5] + "_analysis.json"
path_1 = path_media + file_name[:-5] + "_preprocessing.json"

regular_expression_mex = "^[S|R|E|I|O|W],[0-9]{1,5},[*|0-9]$"
regular_expression_time = "^[T],[0-9]{1,5},[*]$"
regular_expression_final = "^[F],[0],[0]$"
find_all_matches = "[S|R|E|I|O|W|T|F],[0-9]{1,5},[*|0-9]"


def preprocessing(data):
    print("- {}".format(preprocessing.__name__))
    my_time = list()
    mex_correct = list()
    wrong_mex = dict()
    end_sent = ""
    for i, mex in enumerate(data['messages']):
        if re.match(regular_expression_mex, mex['message_id']):
            # MEX string
            string = mex['message_id']
            string = string.split(',')
            mex_correct.append({'mex_id': int(
                string[1]), 'type_mex': string[0], 'ttl': string[2], 'time': mex['time']})
        elif re.match(regular_expression_time, mex['message_id']):
            # DELAY check WIFI string
            string = mex['message_id']
            string = string.split(',')
            my_time.append(
                {'type_mex': string[0], 'delay': int(string[1]), 'time': mex['time']})
        elif re.match(regular_expression_final, mex['message_id']):
            end_sent = {'type_mex': string[0], 'time': mex['time']}
        else:
            # wrong saving
            match = re.findall(find_all_matches, mex['message_id'])
            wrong_mex[i] = {'datetime': mex['time'],
                            'valid_mex_found': match, 'string': mex['message_id']}

    new_wrong_mex = dict()
    for index in wrong_mex:
        try:
            string = wrong_mex[index]['string']
            datetime = wrong_mex[index]['datetime']
            if len(wrong_mex[index]['valid_mex_found']) > 0:
                for m in wrong_mex[index]['valid_mex_found']:
                    string = string.replace(m, '')
                    m1 = m.split(',')
                    if re.match(regular_expression_mex, m):
                        mex_correct.append(
                            {'mex_id': int(m1[1]), 'type_mex': m1[0], 'ttl': m1[2], 'time': datetime})
                    elif re.match(regular_expression_time, m):
                        my_time.append(
                            {'type_mex': m1[0], 'delay': int(m1[1]), 'time': datetime})
                    elif re.match(regular_expression_final, m):
                        end_sent = {'type_mex': m1[0], 'time': datetime}
                if len(string) > 0:
                    new_wrong_mex[index] = {'datetime': datetime, 'string': string}
            else:
                new_wrong_mex[index] = {'datetime': datetime, 'string': string}
        except Exception:
            print("Erore index: ", index)

    # 1. creo una lista contenente tutte le strings con k propedeutici (23,24,25)
    # 2. appena trovo un numero che non è immediatamente consecutivo agli elementi in key_list, analizzo la string creata
    # 3. cerco tutti i possibili match con (mex, time, etc) e procedo a sistemare il tutto
    string = ""
    time_list = list()
    key_list = list()
    for k, v in new_wrong_mex.items():
        if key_list:
            if abs(k - key_list[-1]) != 1:
                match = re.findall(find_all_matches, string)
                i = 0
                for m in match:
                    string = string.replace(m, '')
                    m1 = m.split(',')
                    if re.match(regular_expression_mex, m):
                        mex_correct.append(
                            {'mex_id': int(m1[1]), 'type_mex': m1[0], 'ttl': m1[2], 'time': time_list[i]})
                    elif re.match(regular_expression_time, m):
                        my_time.append(
                            {'type_mex': m1[0], 'delay': int(m1[1]), 'time': time_list[i]})
                    elif re.match(regular_expression_final, m):
                        end_sent = {'type_mex': m1[0], 'time': time_list[i]}
                    i += 1
                key_list.clear()
                time_list.clear()
        if string == "":
            string = str(v['string'])
            if v['datetime'] == "2020-02-01 09:16:59.943322":
                print(string)
        else:
            string += str(v['string'])
            if v['datetime'] == "2020-02-01 09:16:59.943322":
                print(string)
        key_list.append(k)
        time_list.append(v['datetime'])

    # TODO PER GESTIRE L'ULTIMO ELEMENTO NELLA LISTA DEGLI ERRORI
    if string != "":
        match = re.findall(find_all_matches, string)
        i = 0
        for m in match:
            string = string.replace(m, '')
            m1 = m.split(',')
            if re.match(regular_expression_mex, m):
                mex_correct.append(
                    {'mex_id': int(m1[1]), 'type_mex': m1[0], 'ttl': m1[2], 'time': time_list[i]})
            elif re.match(regular_expression_time, m):
                my_time.append(
                    {'type_mex': m1[0], 'delay': int(m1[1]), 'time': time_list[i]})
            elif re.match(regular_expression_final, m):
                end_sent = {'type_mex': m1[0], 'time': time_list[i]}
            i += 1

    # TODO Sort given list of dictionaries by date
    mex_correct.sort(key=lambda x: dt.datetime.strptime(
        x['time'], '%Y-%m-%d %H:%M:%S.%f'))
    my_time.sort(key=lambda x: dt.datetime.strptime(
        x['time'], '%Y-%m-%d %H:%M:%S.%f'))

    # PRINT MEX
    start = dt.datetime.strptime(
        mex_correct[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_sent_ = dt.datetime.strptime(end_sent['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_test = dt.datetime.strptime(mex_correct[-1]['time'], '%Y-%m-%d %H:%M:%S.%f')
    diff = end_test - start
    diff_ = end_sent_ - start
    h1, m1, s1 = my.convert_timedelta(diff)
    h2, m2, s2 = my.convert_timedelta(diff_)
    print("Start: {}".format(start))
    print("End_sent: {}".format(end_sent_))
    print("End_test: {}".format(end_test))
    print("Sent: {}:{}.{} [mm:s.us]".format(m2, s2, diff_.total_seconds()))
    print("Test: {}:{}.{} [mm:s.us]".format(m1, s1, diff.total_seconds()))

    # Salvare Preprocessing
    t1 = str(h2) + ":" + str(m2) + "." + str(s2) + " [h:m.s]"
    t2 = str(h1) + ":" + str(m1) + "." + str(s1) + " [h:m.s]"
    my_data = dict()
    my_data['_command'] = data['_command']
    my_data['_info'] = {'start': start, 'end_sent': end_sent_, 'end_test': end_test, 'time_send': t1, 'time_test': t2}
    my_data['_mex'] = mex_correct
    my_data['_time'] = my_time

    # TODO saving
    print("Saving Preprocessing File")
    my.save_json_data_elegant(path=preprocessing_path, data=my_data)

    hash_table = dict()
    length = len(mex_correct)
    for i in range(length):
        k = mex_correct[i]['mex_id']
        if k in hash_table:
            hash_table[k].append(i)
        else:
            hash_table[k] = list()
            hash_table[k].append(i)

    word_info = dict()
    info_statistic = {'send_ble': 0, 'receive_ble': 0, 'error_ble': 0, 'lost_ble': 0, 'double_sent': 0,
                      'send_wifi': 0, 'receive_wifi': 0, 'error_wifi': 0, 'lost_wifi': 0, 'sent_received': 0}
    ttl_receive = 3 - int(data['_command']['relay'])
    list_wait = list()
    error_1 = list()
    error_2 = list()
    diff_ble = list()
    latency_ble = list()
    diff_wifi = list()
    latency_wifi = list()
    hash_json_data = dict()
    set_1 = set()
    set_2 = set()
    for k, v in hash_table.items():
        for i in v:
            word_info, info_statistic = my.look_into_it(word_info, info_statistic, mex_correct[i])
            if mex_correct[i]['type_mex'] == "O":
                set_1.add(mex_correct[i]['mex_id'])
            if not k in hash_json_data:
                hash_json_data[k] = []
            hash_json_data[k].append(mex_correct[i])
        # BLE
        if 'receive_ble' in word_info:
            if not int(word_info['send_ble']['ttl']) == 3:
                print(
                    '\x1b[1;31;40m' + ' Error analysis_ttl --> send_: ' + word_info['send_ble']['time'] + '\x1b[0m')
                error_1.append(
                    {'k': k, 'time': word_info['send_ble']['time']})
            if not int(word_info['receive_ble']['ttl']) == ttl_receive:
                print('\x1b[1;31;40m' + ' Error analysis_ttl --> receive_: ' +
                      word_info['receive_ble']['time'] + '\x1b[0m')
                error_2.append(
                    {'k': k, 'time': word_info['send_ble']['time']})

            sent = dt.datetime.strptime(
                word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            receive = dt.datetime.strptime(
                word_info['receive_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            difference = receive - sent
            diff_ble.append(difference.total_seconds())
            latency_ble.append(difference.total_seconds() / 2)
            info_statistic['sent_received'] += 1
            hash_json_data[k].append(
                {'ble': {'send_time': sent, 'status_time': receive, 'difference': difference.total_seconds(),
                         'latency': (difference.total_seconds() / 2)}})
        elif 'error_ble' in word_info:
            info_statistic['send_ble'] -= 1
        else:
            info_statistic['lost_ble'] += 1
        # WIFI
        if 'send_wifi' in word_info:
            if 'receive_wifi' in word_info:
                sent = dt.datetime.strptime(
                    word_info['send_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
                receive = dt.datetime.strptime(
                    word_info['receive_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
                difference = receive - sent
                diff_wifi.append(difference.total_seconds())
                latency_wifi.append(difference.total_seconds() / 2)
                info_statistic['sent_received'] += 1
                hash_json_data[k].append(
                    {'wifi': {'send_time': sent, 'status_time': receive, 'difference': difference.total_seconds(),
                              'latency': (difference.total_seconds() / 2)}})
                set_2.add(word_info['receive_wifi']['mex_id'])
            elif 'error_wifi' in word_info:
                info_statistic['send_wifi'] -= 1
            else:
                info_statistic['lost_wifi'] += 1
            # waiting
            sent_1 = dt.datetime.strptime(
                word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            sent_2 = dt.datetime.strptime(
                word_info['send_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
            wait = sent_2 - sent_1
            list_wait.append(wait.total_seconds())
            hash_json_data[k].append({'wait': {'send_ble': sent_1, 'send_wifi': sent_2, 'wait': wait.total_seconds()}})
        if 'receive_ble' in word_info and 'send_wifi' in word_info:
            info_statistic['double_sent'] += 1
        word_info.clear()

    print("---------------")
    print("[relay: {} -> ttl: {}]".format(data['_command']['relay'], ttl_receive))
    print("Changing Delay: {}".format(len(my_time)))
    print("---------------")
    if len(error_1) > 0 or len(error_2) > 0:
        raise Exception('\x1b[1;31;40m' +
                        ' Error TTL: sent: ' + len(error_1) + ' --> received: ' + len(error_2) + ' \x1b[0m')

    print("Media DIff BLE: {}s".format(statistics.mean(diff_ble)))
    print("Media Latency BLE: {}s".format(statistics.mean(latency_ble)))
    print("Media Diff WIFI: {}s".format(statistics.mean(diff_wifi)))
    print("Media Latency WIFI: {}s".format(statistics.mean(latency_wifi)))
    print("Media Waiting BLE -> WIFI: {}s".format(statistics.mean(list_wait)))

    info_statistic['valid_mex'] = info_statistic['sent_received'] - info_statistic['double_sent']
    print("Total Send -> [{}]".format(data['_command']['n_mex']))
    print("S (ble) -> {}".format(info_statistic['send_ble']))
    print("R (ble) -> {}".format(info_statistic['receive_ble']))
    print("E (ble) -> {}".format(info_statistic['error_ble']))  # not_sent_ble
    print("Lost BLE: {}".format(info_statistic['lost_ble']))
    print("I (wifi) -> {}".format(info_statistic['send_wifi']))
    print("O (wifi) -> {}".format(info_statistic['receive_wifi']))
    print("W (wifi) -> {}".format(info_statistic['error_wifi']))  # not_sent_wifi
    print("Lost WiFi: {}".format(info_statistic['lost_wifi']))
    print("Double Sent -> {}".format(info_statistic['double_sent']))
    print("Sent & Received -> {}".format(info_statistic['sent_received']))
    print("Valid Mex -> {}".format(info_statistic['valid_mex']))

    # Check statistics
    if data['_command']['n_mex'] - info_statistic['send_ble'] - info_statistic['error_ble'] != 0:
        raise Exception('\x1b[1;31;40m Error BLE: mex number [T-S-E] \x1b[0m')
    elif info_statistic['send_ble'] - info_statistic['receive_ble'] != info_statistic['lost_ble']:
        raise Exception('\x1b[1;31;40m Error BLE: mex number [S-R] \x1b[0m')
    elif info_statistic['send_wifi'] - info_statistic['lost_wifi'] != info_statistic['receive_wifi']:
        print(set_2.difference(set_1))
        print(set_1.difference(set_2))
        raise Exception('\x1b[1;31;40m Error WIFI: mex number [I-O] \x1b[0m')
    elif info_statistic['valid_mex'] > data['_command']['n_mex']:
        raise Exception('\x1b[1;31;40m Error MEX: Valid Mex \x1b[0m')
    else:
        print('\x1b[1;31;42m Check OK \x1b[0m')
    my_data_2 = dict()
    my_data_2['_command'] = my_data['_command']
    my_data_2['_info'] = my_data['_info']
    my_data_2['_info_2'] = {'mean': {'ble_mean_diff': statistics.mean(diff_ble),
                                     'ble_mean_latency': statistics.mean(latency_ble),
                                     'wifi_mean_diff': statistics.mean(diff_wifi),
                                     'wifi_mean_latency': statistics.mean(latency_wifi),
                                     'wait_mean': statistics.mean(list_wait)},
                            'mex_': {'ble': {'send_ble': info_statistic['send_ble'],
                                             'receive_ble': info_statistic['receive_ble'],
                                             'not_send_ble': info_statistic['error_ble'],
                                             'lost_ble': info_statistic['lost_ble']},
                                     'wifi': {'send_wifi': info_statistic['send_wifi'],
                                              'receive_wifi': info_statistic['receive_wifi'],
                                              'not_send_wifi': info_statistic['error_wifi'],
                                              'lost_wifi': info_statistic['lost_wifi']},
                                     'double_sent': info_statistic['double_sent'],
                                     'valid_mex': info_statistic['valid_mex'],
                                     'sent_received_total': info_statistic['sent_received']
                                     }}
    my_data_2['_time'] = my_data['_time']
    my_data_2['_mex'] = hash_json_data
    print("Saving Analysis File")
    my.save_json_data_elegant(path=analysis_path, data=my_data_2)


def call_preprocessing():
    data = my.open_file_and_return_data(path=path)
    preprocessing(data=data)


def group_files():
    global preprocessing_path
    global analysis_path
    list_of_files = glob.glob("./../json_file/test_2020_01_31/*.json")
    list_of_files.sort()

    for i in range(len(list_of_files)):
        name = list_of_files[i]
        data = my.open_file_and_return_data(path=name)
        preprocessing_path = name[2:-5] + "_preprocessing.json"
        analysis_path = name[2:-5] + "_analysis.json"
        preprocessing(data=data)
        time.sleep(1)


def main():
    call_preprocessing()
    # group_files()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
