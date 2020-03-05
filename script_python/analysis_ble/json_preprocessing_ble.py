import datetime as dt
import statistics
import emilio_function as my
import re
import time
import sys

path_pc = "./"
path_media = "/media/emilio/BLE/"
file_name = "../json_file/test_ble_relay_2/test_19_12_27-19_08_00.json"
path = path_pc + file_name

preprocessing_path = file_name[:-5] + "_preprocessing.json"
analysis_path = file_name[:-5] + "_analysis.json"
path_get_preprocessing = path_media + file_name[3:-5] + "_preprocessing.json"

regular_expression_mex = "^[S|R|P|E],[0-9]{1,5},[*|0-9]$"
find_all_matches = "[S|R|P|E],[0-9]{1,5},[*|0-9]"


def print_info(data):
    print("\x1b[1;34;40m addr:{a}, delay:{d} n_mex:{n} [RELAY: {r}]\x1b[0m".format(a=data['addr'],
                                                                                   d=data['delay'],
                                                                                   n=data['n_mex'],
                                                                                   r=data['relay']))


def first_analysis(path):
    print("- {}".format(first_analysis.__name__))
    data = my.open_file_and_return_data(code=0, path=path)

    mex_correct = data['_mex']
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
    statistic = {'send_ble': 0, 'receive_ble': 0, 'error_ble': 0, 'lost_ble': 0}
    ttl_receive = 3 - int(data['_command']['relay'])
    double_mex = list()
    error_1 = list()
    error_2 = list()
    diff_ble = list()
    latency_ble = list()
    hash_json_data = dict()
    start = ""
    end_send = ""
    end_test = ""
    for k, v in hash_table.items():
        for i in v:
            word_info, statistic, double_mex = my.look_into_it(word_info, statistic, mex_correct[i], double_mex)
            if not k in hash_json_data:
                hash_json_data[k] = []
            hash_json_data[k].append(mex_correct[i])
        # BLE
        if 'send_ble' in word_info:
            time = dt.datetime.strptime(word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            if start == '' and end_send == '':
                start = time
                end_send = start
            elif time > end_send:
                end_send = time
        if 'receive_ble' in word_info:
            if not int(word_info['send_ble']['ttl']) == 3:
                print('\x1b[1;31;40m Error analysis_ttl --> send_: ' + word_info['send_ble']['time'] + '\x1b[0m')
                error_1.append({'k': k, 'time': word_info['send_ble']['time']})
            if not int(word_info['receive_ble']['ttl']) == ttl_receive:
                print('\x1b[1;31;40m Error analysis_ttl --> receive_: ' + word_info['receive_ble']['time'] + '\x1b[0m')
                error_2.append({'k': k, 'time': word_info['send_ble']['time']})

            sent = dt.datetime.strptime(word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            receive_ble = dt.datetime.strptime(word_info['receive_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            difference = receive_ble - sent
            diff_ble.append(abs(difference.total_seconds()))
            latency_ble.append(abs(difference.total_seconds()) / 2)
            hash_json_data[k].append(
                {'ble': {'send_time': sent, 'status_time': receive_ble, 'difference': abs(difference.total_seconds()),
                         'latency': (abs(difference.total_seconds()) / 2)}})
            if end_test == '' or receive_ble > end_test:
                end_test = receive_ble
        elif 'error_ble' in word_info:
            statistic['send_ble'] -= 1
        else:
            statistic['lost_ble'] += 1
        word_info.clear()

    if len(double_mex) != 0:
        for k in double_mex:
            print(hash_json_data[k])
        raise Exception('Indici Duplicati, esempio R,34,2 - R,34,1 --> Rimuovere R,34,2')

    if len(error_1) > 0 or len(error_2) > 0:
        raise Exception(
            '\x1b[1;31;40m Error TTL: sent: ' + str(len(error_1)) + ' --> received: ' + str(len(error_2)) + ' \x1b[0m')

    print("Media DIff BLE: {}s".format(statistics.mean(diff_ble)))
    print("Media Latency BLE: {}s".format(statistics.mean(latency_ble)))

    print("Total Send -> [{}]".format(data['_command']['n_mex']))
    print("S (ble) -> {}".format(statistic['send_ble']))
    print("R (ble) -> {}".format(statistic['receive_ble']))
    print("E (ble) -> {}".format(statistic['error_ble']))  # not_sent_ble
    print("Lost BLE: {}".format(statistic['lost_ble']))

    # Check statistics
    if data['_command']['n_mex'] - statistic['send_ble'] - statistic['error_ble'] != 0:
        raise Exception('\x1b[1;31;40m Error BLE: mex number [T-S-E] \x1b[0m')
    elif statistic['send_ble'] - statistic['receive_ble'] != statistic['lost_ble']:
        raise Exception('\x1b[1;31;40m Error BLE: mex number [S-R] \x1b[0m')
    else:
        print('\x1b[1;31;42m Check OK \x1b[0m')

    # Time definition
    diff_ = end_send - start
    h2, m2, s2 = my.convert_timedelta(diff_)
    diff = end_test - start
    h1, m1, s1 = my.convert_timedelta(diff)
    t1 = str(h2) + ":" + str(m2) + "." + str(s2) + " [h:m.s]"
    t2 = str(h1) + ":" + str(m1) + "." + str(s1) + " [h:m.s]"
    print("Start: {}".format(start))
    print("End_sent: {}".format(end_send))
    print("End_test: {}".format(end_test))
    print("Sent: {}:{}.{} [mm:s.us]".format(m2, s2, diff_.total_seconds()))
    print("Test: {}:{}.{} [mm:s.us]".format(m1, s1, diff.total_seconds()))

    my_data = dict()
    my_data['_command'] = data['_command']
    my_data['_info'] = {'start': start, 'end_sent': end_send, 'end_test': end_test, 'time_send': t1, 'time_test': t2}
    my_data['_info_2'] = {'mean': {'ble_mean_diff': statistics.mean(diff_ble),
                                   'ble_mean_latency': statistics.mean(latency_ble)},
                          'mex_': {'ble': {'send_ble': statistic['send_ble'],
                                           'receive_ble': statistic['receive_ble'],
                                           'not_send_ble': statistic['error_ble'],
                                           'lost_ble': statistic['lost_ble']}}}
    my_data['_mex'] = hash_json_data
    print_info(data['_command'])
    return my_data


def preprocessing(path):
    print("- {}".format(preprocessing.__name__))
    data = my.open_file_and_return_data(code=0, path=path)

    wrong_mex = dict()
    mex_correct = list()
    for i, mex in enumerate(data['messages']):
        string = mex['message_id']
        string = string.split(',')
        if re.match(regular_expression_mex, mex['message_id']):
            # MEX string
            mex_correct.append({'mex_id': int(string[1]), 'type_mex': string[0], 'ttl': string[2], 'time': mex['time']})
        else:
            # wrong saving
            match = re.findall(find_all_matches, mex['message_id'])
            wrong_mex[i] = {'datetime': mex['time'], 'valid_mex_found': match, 'string': mex['message_id']}

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
                        mex_correct.append({'mex_id': int(m1[1]), 'type_mex': m1[0], 'ttl': m1[2], 'time': datetime})
                if len(string) > 0:
                    new_wrong_mex[index] = {'datetime': datetime, 'string': string}
            else:
                new_wrong_mex[index] = {'datetime': datetime, 'string': string}
        except Exception:
            print("Erore index: ", index)

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
                    i += 1
                key_list.clear()
                time_list.clear()
        if string == "":
            string = str(v['string'])
        else:
            string += str(v['string'])
        key_list.append(k)
        time_list.append(v['datetime'])

    if string != "":
        match = re.findall(find_all_matches, string)
        i = 0
        for m in match:
            string = string.replace(m, '')
            m1 = m.split(',')
            if re.match(regular_expression_mex, m):
                mex_correct.append(
                    {'mex_id': int(m1[1]), 'type_mex': m1[0], 'ttl': m1[2], 'time': time_list[i]})
            i += 1
    mex_correct.sort(key=lambda x: dt.datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S.%f'))
    my_data = dict()
    my_data['_command'] = data['_command']
    my_data['_mex'] = mex_correct
    print_info(data['_command'])
    return my_data


def change_ttl_from_7_to_3(path):
    print("- {}".format(change_ttl_from_7_to_3.__name__))
    data = my.open_file_and_return_data(code=0, path=path)

    mex = data['messages']
    i = 0
    saving = False
    ttl = 7 - data['_command']['relay']
    re_ttl = str("P,[0-9]{1,5}," + str(ttl))
    replace_ttl = 3 - data['_command']['relay']
    for k in mex:
        if re.match(re_ttl, k['message_id']):
            saving = True
            s = k['message_id'].split(',')
            new_s = str(s[0] + "," + s[1] + "," + str(replace_ttl))
            data['messages'][i]['message_id'] = new_s
        i += 1
    if saving:
        my.save_json_data_2(path=path, data=data)


def main():
    # TODO usare solo quando ttl è uguale a 7, 6, 5
    if True:
        change_ttl_from_7_to_3(path=path)
        time.sleep(1)
    my_data = preprocessing(path=path)
    my.save_json_data_elegant(path=preprocessing_path, data=my_data)

    time.sleep(1)

    my_data = first_analysis(path=path_get_preprocessing)
    my.save_json_data_elegant(path=analysis_path, data=my_data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
