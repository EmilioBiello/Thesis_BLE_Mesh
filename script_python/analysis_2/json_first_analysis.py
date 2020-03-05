import emilio_function as my
import datetime as dt
import numpy as np
import sys
import time

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 1  # 0..2
index_delay = 0  # 0..6
################################################################
relay = [0, 1, 2]
# delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
    delay[index_delay]) + "/*_analysis.json"
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"

# Variabili globali
my_dictionary = dict()


def statistics(data, run):
    mex = data['_mex']
    latency_ble = dict()
    latency_wifi = dict()
    latency = dict()
    outcomes = {'ble': {'S': 0, 'R': 0, 'L': 0, 'E': 0},
                'wifi': {'S': 0, 'R': 0, 'L': 0, 'E': 0},
                'total': {'S': 0, 'R': 0, 'L': 0}}
    end_test = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    status_time = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    for index, list_of_value in mex.items():
        length = len(list_of_value)
        outcomes['ble']['S'] += 1
        if length == 1:
            outcomes['ble']['L'] += 1
            outcomes['total']['L'] += 1
        elif length == 2:
            outcomes['ble']['E'] += 1
            outcomes['total']['L'] += 1
        elif length == 3:
            if 'ble' in list_of_value[(length - 1)]:
                outcomes['ble']['R'] += 1
                latency_ble[int(index)] = list_of_value[(length - 1)]['ble']['latency']
                latency[int(index)] = list_of_value[(length - 1)]['ble']['latency']
                status_time = dt.datetime.strptime(list_of_value[(length - 1)]['ble']['status_time'],
                                                   '%Y-%m-%d %H:%M:%S.%f')
            else:
                outcomes['ble']['L'] += 1
                outcomes['wifi']['S'] += 1
                outcomes['wifi']['L'] += 1
                outcomes['total']['L'] += 1
        elif length == 4:
            outcomes['ble']['E'] += 1
            outcomes['wifi']['S'] += 1
            outcomes['wifi']['L'] += 1
            outcomes['total']['L'] += 1
        elif length == 5 or length == 6:
            if length == 6:
                outcomes['ble']['E'] += 1
            else:
                outcomes['ble']['L'] += 1
            outcomes['wifi']['S'] += 1
            outcomes['wifi']['R'] += 1
            latency_wifi[int(index)] = list_of_value[(length - 2)]['wifi']['latency']
            latency[int(index)] = list_of_value[(length - 1)]['ble_wifi']['latency_1']
            status_time = dt.datetime.strptime(list_of_value[(length - 1)]['ble_wifi']['receive_wifi'],
                                               '%Y-%m-%d %H:%M:%S.%f')
        else:
            print("- [" + str(len(list_of_value)) + "]", index, " -- ", list_of_value)

        if status_time > end_test:
            end_test = status_time

    if outcomes['ble']['S'] - outcomes['ble']['R'] - outcomes['ble']['L'] - outcomes['ble']['E'] != 0:
        raise Exception("Error counting: {} -- {}".format('ble', outcomes['ble']))

    if outcomes['wifi']['S'] - outcomes['wifi']['R'] - outcomes['wifi']['L'] - outcomes['wifi']['E'] != 0:
        raise Exception("Error counting: {} -- {}".format('wifi', outcomes['wifi']))

    outcomes['total']['S'] = outcomes['ble']['S']
    outcomes['total']['R'] = outcomes['ble']['R'] + outcomes['wifi']['R']
    if outcomes['total']['S'] - outcomes['total']['R'] - outcomes['total']['L'] != 0:
        raise Exception("Error counting: {} -- {}".format('total', outcomes['total']))

    l_ble = list(latency_ble.values())
    l_wifi = list(latency_wifi.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)
    wifi_ = my.intervalli_di_confidenza(dataset=l_wifi)

    l_ = list(latency.values())
    latency_ = my.intervalli_di_confidenza(dataset=l_)

    start_test = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = end_test - start_test
    # TODO BLE
    pdr_ble = outcomes['ble']['R'] / outcomes['ble']['S']
    goodput_ble = (outcomes['ble']['R'] * 2) / time_test.total_seconds()  # 2 byte di dati utili
    # TODO WIFI
    start_test = start_test + dt.timedelta(0, 40)  # aggiungo 40 secondi
    time_test = end_test - start_test
    pdr_wifi = outcomes['wifi']['R'] / outcomes['wifi']['S']
    goodput_wifi = (outcomes['wifi']['R'] * 2) / time_test.total_seconds()  # 2 byte di dati utili

    # TODO General
    pdr = outcomes['total']['R'] / outcomes['total']['S']
    goodput = outcomes['total']['R'] * 2 / time_test.total_seconds()  # 2 byte di dati utili

    if data['_info_2']['mex_']['double_sent'] != 0:
        raise Exception('Double Sent n. {}'.format(data['_info_2']['mex_']['double_sent']))

    # TODO Save data about LATENCY, PDR, GOODPUT
    my_dictionary[str(run)] = {'_info': data['_info'],
                               'mex_': {'ble': {'S': outcomes['ble']['S'], 'R': outcomes['ble']['R'],
                                                'L': outcomes['ble']['L'], 'E': outcomes['ble']['E']},
                                        'wifi': {'S': outcomes['wifi']['S'], 'R': outcomes['wifi']['R'],
                                                 'L': outcomes['wifi']['L'], 'E': outcomes['wifi']['E']},
                                        'total': {'S': outcomes['total']['S'], 'R': outcomes['total']['R'],
                                                  'L': outcomes['total']['L']}},
                               'statistic_': {'ble': {'sample_size': len(l_ble),
                                                      'pdr': pdr_ble,
                                                      'goodput': goodput_ble,
                                                      'latency': {'mean': ble_['mean'], 'std': ble_['std'],
                                                                  'm_e': ble_['m_e'],
                                                                  'low': ble_['low'],
                                                                  'up': ble_['up']}},
                                              'wifi': {'sample_size': len(l_wifi),
                                                       'pdr': pdr_wifi,
                                                       'goodput': goodput_wifi,
                                                       'latency': {'mean': wifi_['mean'], 'std': wifi_['std'],
                                                                   'm_e': wifi_['m_e'],
                                                                   'low': wifi_['low'],
                                                                   'up': wifi_['up']
                                                                   }},
                                              'total': {'sample_size': len(l_),
                                                        'pdr': pdr,
                                                        'goodput': goodput,
                                                        'latency': {'mean': latency_['mean'], 'std': latency_['std'],
                                                                    'm_e': latency_['m_e'],
                                                                    'low': latency_['low'],
                                                                    'up': latency_['up']
                                                                    }}}}
    return latency_ble, latency_wifi, latency


def summary_statistics():
    ble_mex = dict()
    wifi_mex = dict()
    total_mex = dict()
    terms = ['latency', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput']
    terms_2 = ['mean', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput']
    for k, run in my_dictionary.items():
        if k == '_command':
            continue
        if k == '1':
            for t in terms:
                ble_mex[t] = []
                wifi_mex[t] = []
                if t != 'E':
                    total_mex[t] = []
        i = 0
        for t in terms:
            if i < 5:
                ble_mex[t].append(run['statistic_']['ble']['latency'][terms_2[i]])
                wifi_mex[t].append(run['statistic_']['wifi']['latency'][terms_2[i]])
                total_mex[t].append(run['statistic_']['total']['latency'][terms_2[i]])
            elif 5 <= i <= 8:
                ble_mex[t].append(run['mex_']['ble'][terms_2[i]])
                wifi_mex[t].append(run['mex_']['wifi'][terms_2[i]])
                if t != 'E':
                    total_mex[t].append(run['mex_']['total'][terms_2[i]])
            else:
                ble_mex[t].append(run['statistic_']['ble'][terms_2[i]])
                wifi_mex[t].append(run['statistic_']['wifi'][terms_2[i]])
                total_mex[t].append(run['statistic_']['total'][terms_2[i]])
            i += 1

    ble = dict()
    wifi = dict()
    total = dict()
    for t in terms:
        ble[t] = np.mean(ble_mex[t])
        wifi[t] = np.mean(wifi_mex[t])
        if t != 'E':
            total[t] = np.mean(total_mex[t])

    my_dictionary['summary'] = {
        'mex_': {'ble': {'S': ble['S'], 'R': ble['R'], 'L': ble['L'], 'E': ble['E']},
                 'wifi': {'S': wifi['S'], 'R': wifi['R'], 'L': wifi['L'], 'E': wifi['E']},
                 'total': {'S': total['S'], 'R': total['R'], 'L': total['L']}},
        'statistic_': {'ble': {'pdr': ble['pdr'],
                               'goodput': ble['goodput'],
                               'latency': {'mean': ble['latency'], 'std': ble['std'],
                                           'm_e': ble['m_e'],
                                           'low': ble['low'],
                                           'up': ble['up']}},
                       'wifi': {'pdr': wifi['pdr'],
                                'goodput': wifi['goodput'],
                                'latency': {'mean': wifi['latency'], 'std': wifi['std'],
                                            'm_e': wifi['m_e'],
                                            'low': wifi['low'],
                                            'up': wifi['up']}},
                       'total': {'pdr': total['pdr'],
                                 'goodput': total['goodput'],
                                 'latency': {'mean': total['latency'], 'std': total['std'],
                                             'm_e': total['m_e'],
                                             'low': total['low'],
                                             'up': total['up']}}}}


def get_times_change_delay(dataset, delay, info):
    s = dt.datetime.strptime(info['start'], '%Y-%m-%d %H:%M:%S.%f')
    e = dt.datetime.strptime(info['end_test'], '%Y-%m-%d %H:%M:%S.%f')
    test_time = abs(e - s)
    delay = int(delay) / 1000

    times = dict()
    times_1 = dict()
    i = 1
    for v in dataset:
        times[i] = v['delay'] * delay
        # times[v['time']] = v['delay'] # index as datatime
        t = dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f')
        diff = abs(t - s)
        index = diff.total_seconds() * 100 / test_time.total_seconds()
        times_1[index] = v['delay'] * delay
        i += 1
    return times, times_1


def save_statistics_data():
    path_json = outcome_path + "delay_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def plot_1(ble, wifi, total, times, times_1):
    types = ['ble', 'wifi', 'ble_wifi', 'delay_wifi', 'delay_wifi_1']
    for tech in types:
        if tech == 'ble':
            my_list = ble
            type_s = 'latency'
        elif tech == 'wifi':
            my_list = wifi
            type_s = 'latency'
        elif tech == 'ble_wifi':
            my_list = total
            type_s = 'latency'
        elif tech == 'delay_wifi':
            if len(times[1]) == 0:
                continue
            my_list = times
            type_s = 'time'
        elif tech == 'delay_wifi_1':
            if len(times_1[1]) == 0:
                continue
            my_list = times_1
            type_s = 'time'
        else:
            my_list = []
            type_s = ''

        if len(my_list) == 0:
            continue

        for k, v in my_list.items():
            my.plot_latency(dataset=v, run=k, type=tech)
        title_str = "Relay_" + str(relay[index_relay]) + " Delay_" + str(delay[index_delay]) + "ms [" + str(tech) + "]"
        path_graph = outcome_path + str(delay[index_delay]) + "_" + type_s + "_" + str(tech) + ".png"
        my.save_plot_2(type=tech, title=title_str, path=path_graph, type_s=type_s)


def group_main():
    global index_delay
    global index_relay
    global source_path
    global outcome_path
    for r in range(len(relay)):
        for d in range(len(delay)):
            index_relay = r
            index_delay = d
            source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
                delay[index_delay]) + "/*_analysis.json"
            outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"
            main()
            time.sleep(1)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    i = 1
    my_list_ble = dict()
    my_list_wifi = dict()
    my_list_total = dict()
    my_list_times = dict()  # cambio delay_wifi_send
    my_list_times_1 = dict()  # cambio delay_wifi_send
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble, l_wifi, latency = statistics(data=data, run=i)
        t, t1 = get_times_change_delay(data['_time'], data['_command']['delay'], data['_info'])
        my_list_ble[i] = l_ble
        my_list_wifi[i] = l_wifi
        my_list_total[i] = latency
        my_list_times[i] = t
        my_list_times_1[i] = t1
        i += 1

    # Summary
    summary_statistics()
    save_statistics_data()

    # PLOT
    plot_1(my_list_ble, my_list_wifi, my_list_total, my_list_times, my_list_times_1)


if __name__ == "__main__":
    try:
        main()
        # group_main()
    except Exception as e:
        print(e)
    sys.exit()
