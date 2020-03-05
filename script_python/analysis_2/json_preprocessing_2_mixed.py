import datetime as dt
import emilio_function as my
import re
import pandas as pd
import matplotlib.pyplot as plt
import statistics
import numpy as np
import xlsxwriter
import seaborn as sns
import scipy as sc
from scipy.interpolate import interp1d
import sys

# TODO mixed_rule
# TODO dividere i dati per caso [ble, ble+wifi, wifi, ble+wifi, ble]
path_pc = "./"
path_media = "/media/emilio/BLE/"
file_name = "../json_file/test_mixed_r_2/test_20_02_08-17_32_47.json"
path = path_pc + file_name

preprocessing_path = file_name[:-5] + "_preprocessing.json"
analysis_path = file_name[:-5] + "_analysis.json"
analysis_path_2 = file_name[:-5] + "_analysis_2.json"  # without duplicate mex [remove wifi in case of duplicate]
path_1 = path_media + file_name[:-5] + "_preprocessing.json"

regular_expression_mex = "^[S|R|E|I|O|W],[0-9]{1,5},[*|0-9]$"
regular_expression_time = "^[T],[0-9]{1,5},[*]$"
regular_expression_final = "^[F],[0-9],[0-9]$"
find_all_matches = "[S|R|E|I|O|W|T|F],[0-9]{1,5},[*|0-9]"


def preprocessing(data):
    print("- {}".format(preprocessing.__name__))
    wrong_mex = dict()
    time_change = list()
    mex_correct = list()
    status_change = list()
    for i, mex in enumerate(data['messages']):
        string = mex['message_id']
        string = string.split(',')
        if re.match(regular_expression_mex, mex['message_id']):
            # MEX string
            mex_correct.append({'mex_id': int(
                string[1]), 'type_mex': string[0], 'ttl': string[2], 'time': mex['time']})
        elif re.match(regular_expression_time, mex['message_id']):
            # DELAY check WIFI string
            time_change.append(
                {'type_mex': string[0], 'delay': int(string[1]), 'time': mex['time']})
        elif re.match(regular_expression_final, mex['message_id']):
            status_change.append(
                {'type_mex': string[0], 'case': int(string[1]), 'status': int(string[2]), 'time': mex['time']})
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
                        time_change.append(
                            {'type_mex': m1[0], 'delay': int(m1[1]), 'time': datetime})
                    elif re.match(regular_expression_final, m):
                        status_change.append(
                            {'type_mex': m1[0], 'case': int(m1[1]), 'status': int(m1[2]), 'time': datetime})
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
                        time_change.append(
                            {'type_mex': m1[0], 'delay': int(m1[1]), 'time': time_list[i]})
                    elif re.match(regular_expression_final, m):
                        status_change.append(
                            {'type_mex': m1[0], 'case': int(m1[1]), 'status': int(m1[2]), 'time': time_list[i]})
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
                time_change.append(
                    {'type_mex': m1[0], 'delay': int(m1[1]), 'time': time_list[i]})
            elif re.match(regular_expression_final, m):
                status_change.append(
                    {'type_mex': m1[0], 'case': int(m1[1]), 'status': int(m1[2]), 'time': time_list[i]})
            i += 1

    # TODO Sort given list of dictionaries by date
    mex_correct.sort(key=lambda x: dt.datetime.strptime(
        x['time'], '%Y-%m-%d %H:%M:%S.%f'))
    time_change.sort(key=lambda x: dt.datetime.strptime(
        x['time'], '%Y-%m-%d %H:%M:%S.%f'))
    status_change.sort(key=lambda x: dt.datetime.strptime(
        x['time'], '%Y-%m-%d %H:%M:%S.%f'))

    my_data = dict()
    my_data['_command'] = data['_command']
    my_data['_mex'] = mex_correct
    my_data['_time'] = time_change
    my_data['_status'] = status_change

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
    double_set = set()
    received_ble_set = set()
    sent_wifi_set = set()
    received_wifi_set = set()
    double = list()
    for k, v in hash_table.items():
        for i in v:
            word_info, info_statistic, double = my.look_into_it(word_info, info_statistic, mex_correct[i], double)
            if not k in hash_json_data:
                hash_json_data[k] = []
            hash_json_data[k].append(mex_correct[i])
        # BLE
        if 'receive_ble' in word_info:
            received_ble_set.add(int(k))
            # check TTL BLE
            if not int(word_info['send_ble']['ttl']) == 3:
                print(
                    '\x1b[1;31;40m' + ' Error analysis_ttl --> send_: ' + word_info['send_ble']['time'] + '\x1b[0m')
                error_1.append({'k': k, 'time': word_info['send_ble']['time']})
            if not int(word_info['receive_ble']['ttl']) == ttl_receive:
                print('\x1b[1;31;40m' + ' Error analysis_ttl --> receive_: ' +
                      word_info['receive_ble']['time'] + '\x1b[0m')
                error_2.append(
                    {'k': k, 'time': word_info['send_ble']['time']})

            sent = dt.datetime.strptime(word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            receive = dt.datetime.strptime(word_info['receive_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            difference = abs(receive - sent)
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
            sent_wifi_set.add(int(k))
            if 'receive_wifi' in word_info:
                received_wifi_set.add(int(k))
                sent = dt.datetime.strptime(word_info['send_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
                receive = dt.datetime.strptime(word_info['receive_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
                difference = abs(receive - sent)
                diff_wifi.append(difference.total_seconds())
                latency_wifi.append(difference.total_seconds() / 2)
                info_statistic['sent_received'] += 1
                hash_json_data[k].append(
                    {'wifi': {'send_time': sent, 'status_time': receive, 'difference': difference.total_seconds(),
                              'latency': (difference.total_seconds() / 2)}})
            elif 'error_wifi' in word_info:
                info_statistic['send_wifi'] -= 1
            else:
                info_statistic['lost_wifi'] += 1

        # waiting
        if 'send_ble' in word_info and 'send_wifi' in word_info:
            # t0 -> S BLE
            # t1 -> S WiFi
            # t2 -> R WiFi
            # (t2-t1)/2
            send_ble = dt.datetime.strptime(word_info['send_ble']['time'], '%Y-%m-%d %H:%M:%S.%f')
            send_wifi = dt.datetime.strptime(word_info['send_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
            wait = abs(send_wifi - send_ble)
            list_wait.append(wait.total_seconds())

            if 'receive_wifi' in word_info:
                rc_wifi = dt.datetime.strptime(word_info['receive_wifi']['time'], '%Y-%m-%d %H:%M:%S.%f')
                diff_1 = abs(rc_wifi - send_ble)  # latency_ble+wifi
                diff_2 = abs(rc_wifi - send_wifi)  # latency_wifi
                hash_json_data[k].append({'ble_wifi': {
                    'send_ble': send_ble, 'send_wifi': send_wifi, 'receive_wifi': rc_wifi,
                    'wait': wait.total_seconds(),
                    'latency_1': (diff_1.total_seconds() / 2),
                    'latency_2': (wait.total_seconds() + (diff_2.total_seconds() / 2))
                }})
            else:
                print('packet_lost: ', k)

        if 'receive_ble' in word_info and 'send_wifi' in word_info:
            double_set.add(int(k))
            info_statistic['double_sent'] += 1
        word_info.clear()

    if len(double) != 0:
        for k in double:
            print(hash_json_data[k])
        raise Exception('Indici Duplicati, esempio R,34,2 - R,34,1 --> Rimuovere R,34,2')

    if len(error_1) > 0 or len(error_2) > 0:
        raise Exception('\x1b[1;31;40m' +
                        ' Error TTL: sent: ' + str(len(error_1)) + ' --> received: ' + str(len(error_2)) + ' \x1b[0m')

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

    print("Intesezione: Received BLE Sent Wifi {}".format(received_ble_set.intersection(sent_wifi_set)))
    print("double: {}".format(double_set))

    my_data_2 = dict()
    my_data_2['_command'] = my_data['_command']
    my_data_2['_time'] = my_data['_time']
    my_data_2['_status'] = my_data['_status']
    my_data_2['_mex'] = hash_json_data
    print("Saving Analysis File")
    my.save_json_data_elegant(path=analysis_path, data=my_data_2)


def call_preprocessing():
    data = my.open_file_and_return_data(path=path)
    preprocessing(data=data)


def remove_double():
    source_path = my.path_media + file_name[3:-5] + "_analysis.json"
    data = my.open_file_and_return_data(path=source_path)
    double = False
    for k, v in data['_mex'].items():
        if len(v) == 7:
            double = True
            x = list()
            for e in v:
                if 'ble' in e:
                    x.append(e)
                elif 'type_mex' in e:
                    if e['type_mex'] == 'S' or e['type_mex'] == 'R':
                        x.append(e)
            data['_mex'][k] = x

    if double:
        my.save_json_data_elegant(path=analysis_path_2, data=data)


def plot_time(times, filename):
    source_path = my.path_media + file_name[3:-5] + "_analysis.json"
    data = my.open_file_and_return_data(path=source_path)
    pxs = []
    pys = []
    step = []
    info = {'relay': data['_command']['relay'], 'packets': data['_command']['n_mex'],
            'delay': data['_command']['delay']}
    delay = info['delay'] / 1000
    my_time = data['_time']
    my_time.sort(key=lambda x: dt.datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S.%f'))
    i = 1
    for v in my_time:
        # send_time = dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f')
        pxs.append(i)
        pys.append((v['delay'] * delay))
        i += 1
        # if times['ble_wifi_2']['start'] <= send_time <= times['ble_wifi_2']['end_t']:
        #     step.append('ble_wifi_2')
        # elif times['ble_wifi_4']['start'] <= send_time <= times['ble_wifi_2']['end_t']:
        #     step.append('ble_wifi_4')

    df = pd.DataFrame({'k': pxs, 'time': pys})
    print(df.head())

    sns.lmplot(x="k", y='time', palette='muted', data=df, fit_reg=False, ci=None, height=5,
               aspect=2, scatter_kws={"s": 5}, )
    plt.xlabel("Time change delay (ms)")
    plt.ylabel("Delay (s)")
    title = "TIME relay_" + str(info['relay']) + ", " + str(info['packets']) + " packet (1m), delay " + str(
        info['delay']) + " ms"
    plt.title(title)
    filename = filename + ".png"
    print("\x1b[1;32;40m Saving Graph: {}\x1b[0m".format(filename))
    # plt.savefig(filename, dpi=600)
    plt.show()


def plot_statistics(outcomes, info):
    print(outcomes)

    pxs = []
    pys = []
    tech = 'pdr'
    if tech == 'latency':
        y_label = 'Latency (s)'
        txt = 'Latency'
    elif tech == 'pdr':
        y_label = 'Packet Delivery Ratio'
        txt = y_label
    elif tech == 'goodput':
        y_label = 'Goodput (byte/s)'
        txt = 'Goodput'
    else:
        y_label = ''
        txt = ''

    for k, v in outcomes.items():
        pxs.append(k)
        pys.append(v[tech])

    df = pd.DataFrame({'x': pxs, 'y': pys})
    sns.lmplot(x="x", y='y', palette='muted', data=df, fit_reg=False, ci=None, height=5, aspect=2,
               scatter_kws={"s": 5},
               legend_out=False)
    plt.plot(pxs, pys, color='#4878D0')  # blue

    plt.xlabel("Phases")
    plt.ylabel(y_label)
    title = txt + " [Relay " + str(info['relay']) + " Delay " + str(info['delay']) + "]"
    plt.title(title)
    # plt.savefig(filename, dpi=600)
    plt.show()


def my_plot(df, info, filename):
    # define_base_plot()
    print(df.head())

    # sns.lmplot(x="k", y='latency', hue='step', palette='muted', data=df, ci=None, order=8, aspect=3, truncate=True, scatter_kws={"s": 2})  # lmplot_2
    sns.lmplot(x="k", y='y_data', hue='type', palette='muted', data=df, fit_reg=False, ci=None, height=5,
               aspect=2, scatter_kws={"s": 5}, legend_out=False)  # lmplot_1
    plt.xlabel("Packets")
    plt.ylabel("Latency (s)")
    title = "Mixed relay_" + str(info['relay']) + ", " + str(info['packets']) + " packet (1m), delay " + str(
        info['delay']) + " ms"
    plt.title(title)
    filename = filename + ".png"
    print("\x1b[1;32;40m Saving Graph: {}\x1b[0m".format(filename))
    # plt.savefig(filename, dpi=600)
    plt.show()


def save_xlsx(dataset, info, filename):
    filename = filename + ".xlsx"
    workbook = xlsxwriter.Workbook(filename=filename)

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    bold.set_center_across()
    cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    cell_format.set_center_across()

    worksheet = workbook.add_worksheet(name="Relay_" + str(info['relay']))
    row = 0
    col = 0
    title = "Rilevazione_Mixed_r" + str(info['relay']) + "_p_" + str(info['packets'])
    worksheet.write(row, col, title, cell_format)
    worksheet.write(row + 1, col, "Step", bold)
    worksheet.write(row + 1, col + 2, "S", bold)
    worksheet.write(row + 1, col + 3, "R", bold)
    worksheet.write(row + 1, col + 4, "L", bold)
    worksheet.write(row + 1, col + 5, "E", bold)
    worksheet.write(row + 1, col + 7, "Latency_mean", bold)
    worksheet.write(row + 1, col + 8, "Latency_std", bold)
    worksheet.write(row + 1, col + 9, "Latency_m_e", bold)
    worksheet.write(row + 1, col + 10, "Latency_lower", bold)
    worksheet.write(row + 1, col + 11, "Latency_upper", bold)
    worksheet.write(row + 1, col + 13, "PDR", bold)
    worksheet.write(row + 1, col + 14, "Goodput", bold)
    row = 2
    col = 0
    for step in dataset:
        worksheet.write(row + 1, col, step)
        worksheet.write(row + 1, col + 2, dataset[step]['S'])
        worksheet.write(row + 1, col + 3, dataset[step]['R'])
        worksheet.write(row + 1, col + 4, dataset[step]['L'])
        worksheet.write(row + 1, col + 5, dataset[step]['E'])
        worksheet.write(row + 1, col + 7, dataset[step]['latency'])
        worksheet.write(row + 1, col + 8, dataset[step]['std'])
        worksheet.write(row + 1, col + 9, dataset[step]['m_e'])
        worksheet.write(row + 1, col + 10, dataset[step]['low'])
        worksheet.write(row + 1, col + 11, dataset[step]['up'])
        worksheet.write(row + 1, col + 13, dataset[step]['pdr'])
        worksheet.write(row + 1, col + 14, dataset[step]['goodput'])
        row = row + 1
    print("\x1b[1;32;40m Saving {}\x1b[0m".format(filename))
    workbook.close()


def calculate_statistics(dataframe, times):
    outcomes = {'ble_1': {'latency': 0, 'std': 0, 'm_e': 0, 'low': 0, 'up': 0, 'pdr': 0, 'goodput': 0},
                'ble_wifi_2': {'latency': 0, 'std': 0, 'm_e': 0, 'low': 0, 'up': 0, 'pdr': 0, 'goodput': 0},
                'wifi_3': {'latency': 0, 'std': 0, 'm_e': 0, 'low': 0, 'up': 0, 'pdr': 0, 'goodput': 0},
                'ble_wifi_4': {'latency': 0, 'std': 0, 'm_e': 0, 'low': 0, 'up': 0, 'pdr': 0, 'goodput': 0},
                'ble_5': {'latency': 0, 'std': 0, 'm_e': 0, 'low': 0, 'up': 0, 'pdr': 0, 'goodput': 0}}
    for step in dataframe:
        l_ = dataframe[step]['latency']
        latency = my.intervalli_di_confidenza(dataset=l_)
        pdr = dataframe[step]['R'] / dataframe[step]['S']
        goodput = (dataframe[step]['R'] * 2) / 60  # TODO time test 1 minute
        outcomes[step]['latency'] = latency['mean']
        outcomes[step]['std'] = latency['std']
        outcomes[step]['m_e'] = latency['m_e']
        outcomes[step]['low'] = latency['low']
        outcomes[step]['up'] = latency['up']
        outcomes[step]['pdr'] = pdr
        outcomes[step]['goodput'] = goodput

    for k, v in outcomes.items():
        outcomes[k]['S'] = dataframe[k]['S']
        outcomes[k]['R'] = dataframe[k]['R']
        outcomes[k]['L'] = dataframe[k]['L']
        outcomes[k]['E'] = dataframe[k]['E']
    return outcomes


def catalogue_data_2():
    source_path = my.path_media + file_name[3:-5] + "_analysis_2.json"
    data = my.open_file_and_return_data(path=source_path)
    pxs = []
    pys = []
    step = []
    increment = data['_command']['n_mex']
    start_1 = 1
    end_1 = start_1 - 1 + increment
    start_2 = end_1 + 1
    end_2 = end_1 + increment
    start_3 = end_2 + 1
    end_3 = end_2 + increment
    start_4 = end_3 + 1
    end_4 = end_3 + increment
    start_5 = end_4 + 1
    end_5 = end_4 + increment

    cases = {'ble_1': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_wifi_2': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'wifi_3': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_wifi_4': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_5': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []}}
    packets_limit = {'ble_1': {'start': start_1, 'end_s': end_1, 'end_t': end_1},
                     'ble_wifi_2': {'start': start_2, 'end_s': end_2, 'end_t': end_2},
                     'wifi_3': {'start': start_3, 'end_s': end_3, 'end_t': end_3},
                     'ble_wifi_4': {'start': start_4, 'end_s': end_4, 'end_t': end_4},
                     'ble_5': {'start': start_5, 'end_s': end_5, 'end_t': end_5}}

    for k, v in data['_mex'].items():
        send_time = dt.datetime.strptime(v[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
        length = len(v)
        case = ''
        string = ''
        t = ''
        mex_type = list()
        if start_1 <= int(k) <= end_1:
            case = 'ble_1'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3 and 'ble' in v[length - 1]:
                mex_type.append('R')
                t = 'ble'
                string = 'ble_1'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_2 <= int(k) <= end_2:
            case = 'ble_wifi_2'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2 or length == 4:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                if 'ble' in v[length - 1]:
                    mex_type.append('R')
                    t = 'ble'
                    string = 'ble_2'
                else:
                    mex_type.append('L')
            elif length == 5 and 'ble_wifi' in v[length - 1]:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_2'
            elif length == 6 and 'ble_wifi' in v[length - 1]:
                mex_type.append('E')
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_2'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_3 <= int(k) <= end_3:
            case = 'wifi_3'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_3'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_4 <= int(k) <= end_4:
            case = 'ble_wifi_4'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2 or length == 4:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                if 'ble' in v[length - 1]:
                    mex_type.append('R')
                    t = 'ble'
                    string = 'ble_4'
                else:
                    mex_type.append('L')
            elif length == 5 and 'ble_wifi' in v[length - 1]:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_4'
            elif length == 6 and 'ble_wifi' in v[length - 1]:
                mex_type.append('E')
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_4'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_5 <= int(k) <= end_5:
            case = 'ble_5'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3 and 'ble' in v[length - 1]:
                mex_type.append('R')
                t = 'ble'
                string = 'ble_5'
            else:
                print(case, " -- ", length, " -- ", k)
        else:
            print("Error: ", k)

        for i in mex_type:
            cases[case][i] += 1
            if i == 'R':
                if string == 'wifi_2' or string == 'wifi_4':
                    l = v[length - 1]['ble_wifi']['latency_2']  # TODO latency_1 or latency_2
                else:
                    l = v[length - 1][t]['latency']

                if string == 'wifi_2' or string == 'ble_2':
                    string = 'ble_wifi_2'
                elif string == 'wifi_4' or string == 'ble_4':
                    string = 'ble_wifi_4'

                cases[case]['latency'].append(l)
                pxs.append(int(k))
                pys.append(l)
                step.append(string)

    df = pd.DataFrame({'k': pxs, 'y_data': pys, 'type': step})
    info = {'relay': data['_command']['relay'], 'packets': data['_command']['n_mex'],
            'delay': data['_command']['delay']}

    return df, info, cases


def catalogue_data():
    source_path = my.path_media + file_name[3:-5] + "_analysis_2.json"
    data = my.open_file_and_return_data(path=source_path)
    start_1 = dt.datetime.strptime(data['_status'][0]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_1 = dt.datetime.strptime(data['_status'][1]['time'], '%Y-%m-%d %H:%M:%S.%f')
    start_2 = dt.datetime.strptime(data['_status'][2]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_2 = dt.datetime.strptime(data['_status'][3]['time'], '%Y-%m-%d %H:%M:%S.%f')
    start_3 = dt.datetime.strptime(data['_status'][4]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_3 = dt.datetime.strptime(data['_status'][5]['time'], '%Y-%m-%d %H:%M:%S.%f')
    start_4 = dt.datetime.strptime(data['_status'][6]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_4 = dt.datetime.strptime(data['_status'][7]['time'], '%Y-%m-%d %H:%M:%S.%f')
    start_5 = dt.datetime.strptime(data['_status'][8]['time'], '%Y-%m-%d %H:%M:%S.%f')
    end_5 = dt.datetime.strptime(data['_status'][9]['time'], '%Y-%m-%d %H:%M:%S.%f')

    pxs = []
    pys = []
    step = []

    cases = {'ble_1': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_wifi_2': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'wifi_3': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_wifi_4': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []},
             'ble_5': {'S': 0, 'R': 0, 'L': 0, 'E': 0, 'latency': []}}
    times = {'ble_1': {'start': start_1, 'end_s': end_1, 'end_t': end_1},
             'ble_wifi_2': {'start': start_2, 'end_s': end_2, 'end_t': end_2},
             'wifi_3': {'start': start_3, 'end_s': end_3, 'end_t': end_3},
             'ble_wifi_4': {'start': start_4, 'end_s': end_4, 'end_t': end_4},
             'ble_5': {'start': start_5, 'end_s': end_5, 'end_t': end_5}}
    for k, v in data['_mex'].items():
        send_time = dt.datetime.strptime(v[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
        length = len(v)
        case = ''
        string = ''
        t = ''
        mex_type = list()
        if start_1 <= send_time <= end_1:
            case = 'ble_1'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3 and 'ble' in v[length - 1]:
                mex_type.append('R')
                t = 'ble'
                string = 'ble_1'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_2 <= send_time <= end_2:
            case = 'ble_wifi_2'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2 or length == 4:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                if 'ble' in v[length - 1]:
                    mex_type.append('R')
                    t = 'ble'
                    string = 'ble_2'
                else:
                    mex_type.append('L')
            elif length == 5 and 'ble_wifi' in v[length - 1]:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_2'
            elif length == 6 and 'ble_wifi' in v[length - 1]:
                mex_type.append('E')
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_2'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_3 <= send_time <= end_3:
            case = 'wifi_3'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_3'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_4 <= send_time <= end_4:
            case = 'ble_wifi_4'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2 or length == 4:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3:
                if 'ble' in v[length - 1]:
                    mex_type.append('R')
                    t = 'ble'
                    string = 'ble_4'
                else:
                    mex_type.append('L')
            elif length == 5 and 'ble_wifi' in v[length - 1]:
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_4'
            elif length == 6 and 'ble_wifi' in v[length - 1]:
                mex_type.append('E')
                mex_type.append('R')
                t = 'wifi'
                string = 'wifi_4'
            else:
                print(case, " -- ", length, " -- ", k)
        elif start_5 <= send_time <= end_5:
            case = 'ble_5'
            mex_type.append('S')
            if length == 1:
                mex_type.append('L')
            elif length == 2:
                mex_type.append('E')
                mex_type.append('L')
            elif length == 3 and 'ble' in v[length - 1]:
                mex_type.append('R')
                t = 'ble'
                string = 'ble_5'
            else:
                print(case, " -- ", length, " -- ", k)

        for i in mex_type:
            cases[case][i] += 1
            if i == 'R':
                if string == 'wifi_2' or string == 'wifi_4':
                    l = v[length - 1]['ble_wifi']['latency_2']  # TODO latency_1 or latency_2
                    rc_time = dt.datetime.strptime(v[length - 1]['ble_wifi']['receive_wifi'], '%Y-%m-%d %H:%M:%S.%f')
                else:
                    l = v[length - 1][t]['latency']
                    rc_time = dt.datetime.strptime(v[length - 1][t]['status_time'], '%Y-%m-%d %H:%M:%S.%f')

                if string == 'wifi_2' or string == 'ble_2':
                    string = 'ble_wifi_2'
                elif string == 'wifi_4' or string == 'ble_4':
                    string = 'ble_wifi_4'

                cases[case]['latency'].append(l)
                pxs.append(int(k))
                pys.append(l)
                step.append(string)
                if rc_time > times[case]['end_t']:
                    times[case]['end_t'] = rc_time

    df = pd.DataFrame({'k': pxs, 'y_data': pys, 'type': step})
    info = {'relay': data['_command']['relay'], 'packets': data['_command']['n_mex'],
            'delay': data['_command']['delay']}
    return df, info, cases, times


def plot_and_statistics():
    # df, info, cases, times = catalogue_data()  # calcolo latency, PDR e Goodput
    df, info, cases = catalogue_data_2()  # calcolo latency, PDR e Goodput
    outcomes = calculate_statistics(cases, "")
    # source_path = my.path_media + file_name[3:-5]
    # filename = source_path + "_r_" + str(info['relay']) + "_p_" + str(info['packets'])
    # save_xlsx(outcomes, info, filename)
    # my_plot(df, info, filename)  # grafico i dati
    # filename = source_path + "_TIME_r_" + str(info['relay']) + "_p_" + str(info['packets'])
    # plot_time(times="", filename=filename)
    plot_statistics(outcomes, info)


def plot_combo():
    global file_name
    pxs = []
    pys = []
    pzs = []
    y_data = {'k': [], '50': [], '100': []}
    tech = 'pdr'
    for file_name in ["../json_file/test_mixed_r_2/test_20_02_08-17_39_43.json",
                      "../json_file/test_mixed_r_2/test_20_02_08-17_16_02.json"]:
        df, info, cases = catalogue_data_2()
        outcomes = calculate_statistics(cases, "")
        for k, v in outcomes.items():
            pxs.append(k)
            pys.append(v[tech])
            pzs.append(('delay_' + str(info['delay'])))
            if info['delay'] == 50:
                y_data['k'].append(k)
                y_data['50'].append(v[tech])
            else:
                y_data['100'].append(v[tech])

    df = pd.DataFrame({'x': pxs, 'y': pys, 'type': pzs})
    sns.lmplot(x="x", y='y', hue='type', palette='muted', data=df, fit_reg=False, ci=None, height=5, aspect=2,
               scatter_kws={"s": 45},
               legend_out=False)

    plt.plot(y_data['k'], y_data['100'], '--', color='#4878D0')  # blue
    plt.plot(y_data['k'], y_data['50'], '--', color='#EE854A')  # orange

    if tech == 'latency':
        y_label = 'Latency (s)'
        txt = 'Latency'
    elif tech == 'pdr':
        y_label = 'Packet Delivery Ratio'
        txt = y_label
    elif tech == 'goodput':
        y_label = 'Goodput (byte/s)'
        txt = 'Goodput'
    else:
        y_label = ''
        txt = ''

    plt.xlabel("Phases")
    plt.ylabel(y_label)
    title = txt + " [Relay " + str(info['relay']) + " Delay 50 - 100]"
    plt.title(title)
    # plt.savefig(filename, dpi=600)
    plt.show()


def main():
    # call_preprocessing()  # aggiusto i mex
    # remove_double()  # rimuovo eventuali duplicati
    plot_and_statistics()


if __name__ == "__main__":
    try:
        # main()
        plot_combo()
    except Exception as e:
        print(e)
    sys.exit()
