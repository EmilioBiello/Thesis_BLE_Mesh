import emilio_function as my
import datetime as dt
import numpy as np
import sys
import time

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 0  # 0..2
index_delay = 0  # 0..6
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
    delay[index_delay]) + "/*_analysis.json"
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"

# Variabili globali
my_dictionary = dict()


def statistics(data, run):
    mex = data['_mex']
    latency_ble = dict()
    outcomes = {'S': 0, 'R': 0, 'L': 0, 'L1': 0, 'E': 0}  # L comprende anche E --> L1 + E = L
    end_test = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    status_time = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    for index, list_of_value in mex.items():
        length = len(list_of_value)
        outcomes['S'] += 1
        if length == 1:
            outcomes['L'] += 1
            outcomes['L1'] += 1
        elif length == 2:
            outcomes['E'] += 1
            outcomes['L'] += 1
        elif length == 3:
            if 'ble' in list_of_value[(length - 1)]:
                outcomes['R'] += 1
                latency_ble[int(index)] = list_of_value[(length - 1)]['ble']['latency']
                status_time = dt.datetime.strptime(list_of_value[(length - 1)]['ble']['status_time'],
                                                   '%Y-%m-%d %H:%M:%S.%f')
            else:
                print("---")
                outcomes['L'] += 1
        else:
            print("- [" + str(len(list_of_value)) + "]", index, " -- ", list_of_value)

        if status_time > end_test:
            end_test = status_time

    counting = outcomes['E'] + outcomes['L1']
    if counting != outcomes['L']:
        raise Exception("Error counting:[E+L1->L] {} -- [{}] -- {}".format('ble', counting, outcomes))

    counting = outcomes['S'] - outcomes['R'] - outcomes['L']
    if counting != 0:
        raise Exception("Error counting: {} -- [{}] -- {}".format('ble', counting, outcomes))
    else:
        print(outcomes)

    l_ble = list(latency_ble.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)

    start_test = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = end_test - start_test
    # TODO BLE
    pdr_ble = outcomes['R'] / outcomes['S']
    goodput_ble = (outcomes['R'] * 2) / time_test.total_seconds()  # 2 byte di dati utili

    # TODO Save data about LATENCY, PDR, GOODPUT
    my_dictionary[str(run)] = {'_info': data['_info'],
                               'mex_': {'S': outcomes['S'], 'R': outcomes['R'],
                                        'L': outcomes['L'], 'E': outcomes['E']},
                               'statistic_': {'sample_size': len(l_ble),
                                              'pdr': pdr_ble,
                                              'goodput': goodput_ble,
                                              'latency': {'mean': ble_['mean'], 'std': ble_['std'],
                                                          'm_e': ble_['m_e'],
                                                          'low': ble_['low'],
                                                          'up': ble_['up']}}}
    return latency_ble


def summary_statistics():
    ble_mex = dict()
    terms = ['latency', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput']
    terms_2 = ['mean', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput']
    for k, run in my_dictionary.items():
        if k == '_command':
            continue
        if k == '1':
            for t in terms:
                ble_mex[t] = []
        i = 0
        for t in terms:
            if i < 5:
                value = run['statistic_']['latency'][terms_2[i]]
            elif 5 <= i <= 8:
                value = run['mex_'][terms_2[i]]
            else:
                value = run['statistic_'][terms_2[i]]
            ble_mex[t].append(value)
            i += 1

    ble = dict()
    for t in terms:
        ble[t] = np.mean(ble_mex[t])

    my_dictionary['summary'] = {
        'mex_': {'S': ble['S'], 'R': ble['R'], 'L': ble['L'], 'E': ble['E']},
        'statistic_': {'pdr': ble['pdr'],
                       'goodput': ble['goodput'],
                       'latency': {'mean': ble['latency'], 'std': ble['std'],
                                   'm_e': ble['m_e'],
                                   'low': ble['low'],
                                   'up': ble['up']}}}

    # Saving
    path_json = outcome_path + "delay_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def plot_1(ble):
    my_list = ble
    type_s = 'latency'

    if len(my_list) == 0:
        return

    for k, v in my_list.items():
        my.plot_latency(dataset=v, run=k, type='ble')
    title_str = "Relay_" + str(relay[index_relay]) + " Delay_" + str(delay[index_delay]) + "ms [ble]"
    path_graph = outcome_path + str(delay[index_delay]) + "_" + type_s + "_ble.png"
    my.save_plot_2(type='ble', title=title_str, path=path_graph, type_s=type_s)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    i = 1
    my_list_ble = dict()
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble = statistics(data=data, run=i)
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
