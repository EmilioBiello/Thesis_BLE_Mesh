import emilio_function as my
import datetime as dt
import time
import numpy as np
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 0  # 0..2
index_delay = 0  # 0..6
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
    delay[index_delay]) + "/*_analysis.json"
cuts_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/delay_x_" + str(
    delay[index_delay]) + ".json"
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/"

my_dictionary = dict()


def statistics(data, run, x):
    mex = data['_mex']
    min_index = x[str(run)]['smaller']
    max_index = x[str(run)]['bigger']
    latency_ble = dict()
    outcomes = {'S': 0, 'R': 0, 'L': 0, 'L1': 0, 'E': 0}
    end_test = dt.datetime.strptime(x[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    end_send = dt.datetime.strptime(x[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    for index, list_of_value in mex.items():
        for v in list_of_value:
            if min_index <= int(index) <= max_index:
                if 'type_mex' in v and v['type_mex'] == "S":
                    outcomes['S'] += 1
                if 'type_mex' in v and v['type_mex'] == "E":
                    outcomes['E'] += 1

                if 'ble' in v:
                    outcomes['R'] += 1
                    latency_ble[int(index)] = v['ble']['latency']
                    rcv = dt.datetime.strptime(v['ble']['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                    if rcv > end_test:
                        end_test = rcv

    outcomes['L1'] = outcomes['S'] - outcomes['R'] - outcomes['E']
    outcomes['L'] = outcomes['S'] - outcomes['R']

    if outcomes['S'] - outcomes['R'] - outcomes['L'] != 0:
        raise Exception("Error counting: {} -- {}".format('ble', outcomes))

    if outcomes['S'] != x[str(run)]['S'] or outcomes['R'] != x[str(run)]['R'] or outcomes['L'] != x[str(run)]['L']:
        raise Exception('Error counting: {} -- {}\n{}'.format('total', outcomes, x[str(run)]))

    if len(latency_ble) != outcomes['R']:
        raise Exception(
            'Error counting: size_total: {} -- total_R: {}'.format(len(latency_ble), outcomes['R']))

    l_ble = list(latency_ble.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)

    start_test = dt.datetime.strptime(x[str(run)]['time']['new_start'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = abs(end_test - start_test)
    time_ = abs(end_send - start_test)
    # TODO BLE
    pdr_ble = outcomes['R'] / outcomes['S']
    goodput_ble = (outcomes['R'] * 2) / time_test.total_seconds()  # 2 byte di dati utili
    goodput_ble_1 = (outcomes['R'] * 2) / time_.total_seconds()  # 2 byte di dati utili

    h, m, s = my.convert_timedelta(time_)
    time_send_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"
    h, m, s = my.convert_timedelta(time_test)
    time_test_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"

    my_dictionary[str(run)] = {'_info_0': data['_info'],
                               '_info_1': {'end_sent': x[str(run)]['time']['new_end'], 'end_test': end_test,
                                           'start': x[str(run)]['time']['new_start'], 'time_send': time_send_,
                                           'time_test': time_test_},
                               'mex_': {'S': outcomes['S'], 'R': outcomes['R'], 'L': outcomes['L'], 'E': outcomes['E']},
                               'statistic_': {'sample_size': len(l_ble),
                                              'pdr': pdr_ble,
                                              'goodput': goodput_ble,
                                              'goodput_1': goodput_ble_1,
                                              'latency': {'mean': ble_['mean'], 'std': ble_['std'],
                                                          'm_e': ble_['m_e'],
                                                          'low': ble_['low'],
                                                          'up': ble_['up']}}}
    return latency_ble


def summary_statistics():
    ble_mex = dict()
    terms = ['latency', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput', 'goodput_1']
    terms_2 = ['mean', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput', 'goodput_1']
    for k, run in my_dictionary.items():
        if k == '_command':
            continue
        if k == '1':
            for t in terms:
                ble_mex[t] = []
        i = 0
        for t in terms:
            if i < 5:
                ble_mex[t].append(run['statistic_']['latency'][terms_2[i]])
            elif 5 <= i <= 8:
                ble_mex[t].append(run['mex_'][terms_2[i]])
            else:
                ble_mex[t].append(run['statistic_'][terms_2[i]])
            i += 1

    ble = dict()
    for t in terms:
        ble[t] = np.mean(ble_mex[t])

    my_dictionary['summary'] = {
        'mex_': {'S': ble['S'], 'R': ble['R'], 'L': ble['L'], 'E': ble['E']},
        'statistic_': {'pdr': ble['pdr'],
                       'goodput': ble['goodput'],
                       'goodput_1': ble['goodput_1'],
                       'latency': {'mean': ble['latency'], 'std': ble['std'],
                                   'm_e': ble['m_e'],
                                   'low': ble['low'],
                                   'up': ble['up']}}}

    path_json = outcome_path + "delay_XXX_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def plot_1(my_list):
    type_s = 'latency'

    if len(my_list) == 0:
        return

    for k, v in my_list.items():
        my.plot_latency(dataset=v, run=k, type='ble')
    title_str = "Relay_" + str(relay[index_relay]) + " Delay_" + str(delay[index_delay]) + "ms [ble] XXX"
    path_graph = outcome_path + str(delay[index_delay]) + "_XXX_" + type_s + "_ble.png"
    my.save_plot_2(type='ble', title=title_str, path=path_graph, type_s=type_s)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    cuts = my.open_file_and_return_data(path=cuts_path)
    i = 1
    my_list_ble = dict()
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble = statistics(data=data, run=i, x=cuts)
        my_list_ble[i] = l_ble
        i += 1

    # Summary
    summary_statistics()

    # PLOT
    plot_1(my_list_ble)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
