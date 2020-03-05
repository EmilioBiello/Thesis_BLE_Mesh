import emilio_function as my
import datetime as dt
import time
import numpy as np
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 1  # 0..2
index_delay = 0  # 0..6
# TODO scelta run... manuale o all_inclusive [0 -> single, 1 -> automatic]
approach = 0
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
    latency_wifi = dict()
    latency_total = dict()
    outcomes = {'ble': {'S': 0, 'R': 0, 'L': 0, 'E': 0},
                'wifi': {'S': 0, 'R': 0, 'L': 0, 'E': 0},
                'total': {'S': 0, 'R': 0, 'L': 0}}
    end_test = dt.datetime.strptime(x[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    for index, list_of_value in mex.items():
        ble = False
        wifi = False
        for v in list_of_value:
            if min_index <= int(index) <= max_index:
                if 'type_mex' in v and v['type_mex'] == "S":
                    outcomes['ble']['S'] += 1
                    outcomes['total']['S'] += 1
                if 'type_mex' in v and v['type_mex'] == "E":
                    outcomes['ble']['E'] += 1
                if 'type_mex' in v and v['type_mex'] == "I":
                    wifi = True
                    outcomes['wifi']['S'] += 1
                if 'type_mex' in v and v['type_mex'] == "W":
                    outcomes['wifi']['W'] += 1

                if 'ble' in v:
                    ble = True
                    outcomes['ble']['R'] += 1
                    outcomes['total']['R'] += 1
                    latency_ble[int(index)] = v['ble']['latency']
                    latency_total[int(index)] = v['ble']['latency']
                    rcv = dt.datetime.strptime(v['ble']['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                    if rcv > end_test:
                        end_test = rcv
                if 'wifi' in v:
                    outcomes['wifi']['R'] += 1
                    outcomes['total']['R'] += 1
                    latency_wifi[int(index)] = v['wifi']['latency']
                    rcv = dt.datetime.strptime(v['wifi']['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                    if rcv > end_test:
                        end_test = rcv
                if 'ble_wifi' in v and 'latency_1' in v['ble_wifi']:
                    latency_total[int(index)] = v['ble_wifi']['latency_1']
        if ble and wifi:
            raise Exception('Double Sent: {}'.format(index))

    outcomes['ble']['L'] = outcomes['ble']['S'] - outcomes['ble']['R'] - outcomes['ble']['E']
    outcomes['wifi']['L'] = outcomes['wifi']['S'] - outcomes['wifi']['R'] - outcomes['wifi']['L']

    outcomes['total']['L'] = outcomes['total']['S'] - outcomes['total']['R']

    if outcomes['ble']['S'] - outcomes['ble']['R'] - outcomes['ble']['L'] - outcomes['ble']['E'] != 0:
        raise Exception("Error counting: {} -- {}".format('ble', outcomes['ble']))

    if outcomes['wifi']['S'] - outcomes['wifi']['R'] - outcomes['wifi']['L'] - outcomes['wifi']['E'] != 0:
        raise Exception("Error counting: {} -- {}".format('wifi', outcomes['wifi']))

    if outcomes['total']['S'] != x[str(run)]['S'] or outcomes['total']['S'] != x[str(run)]['S'] or outcomes['total'][
        'S'] != \
            x[str(run)]['S']:
        raise Exception('Error counting: {} -- {}\n{}'.format('total', outcomes['total'], x[str(run)]))

    if len(latency_total) != outcomes['total']['R']:
        raise Exception(
            'Error counting: size_total: {} -- total_R: {}'.format(len(latency_total), outcomes['total']['R']))

    l_ble = list(latency_ble.values())
    l_wifi = list(latency_wifi.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)
    wifi_ = my.intervalli_di_confidenza(dataset=l_wifi)

    l_ = list(latency_total.values())
    latency_ = my.intervalli_di_confidenza(dataset=l_)

    start_test = dt.datetime.strptime(x[str(run)]['time']['new_start'], '%Y-%m-%d %H:%M:%S.%f')
    end_send = dt.datetime.strptime(x[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = abs(end_test - start_test)
    time_ = abs(end_send - start_test)

    # TODO BLE
    pdr_ble = outcomes['ble']['R'] / outcomes['ble']['S']
    goodput_ble = (outcomes['ble']['R'] * 2) / time_test.total_seconds()  # 2 byte di dati utili

    # TODO WIFI
    s_t = start_test + dt.timedelta(0, 40)  # aggiungo 40 secondi
    t_t = end_test - s_t
    pdr_wifi = outcomes['wifi']['R'] / outcomes['wifi']['S']
    goodput_wifi = (outcomes['wifi']['R'] * 2) / t_t.total_seconds()  # 2 byte di dati utili

    # TODO General
    pdr = outcomes['total']['R'] / outcomes['total']['S']
    goodput = outcomes['total']['R'] * 2 / time_test.total_seconds()  # 2 byte di dati utili
    goodput_1 = outcomes['total']['R'] * 2 / time_.total_seconds()  # 2 byte di dati utili

    h, m, s = my.convert_timedelta(time_)
    time_send_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"
    h, m, s = my.convert_timedelta(time_test)
    time_test_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"

    my_dictionary[str(run)] = {'_info_0': data['_info'],
                               '_info_1': {'end_sent': x[str(run)]['time']['new_end'], 'end_test': end_test,
                                           'start': x[str(run)]['time']['new_start'], 'time_send': time_send_,
                                           'time_test': time_test_},
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
                                                        'goodput_1': goodput_1,
                                                        'latency': {'mean': latency_['mean'], 'std': latency_['std'],
                                                                    'm_e': latency_['m_e'],
                                                                    'low': latency_['low'],
                                                                    'up': latency_['up']
                                                                    }}}}
    return latency_ble, latency_wifi, latency_total


def summary_statistics():
    print(summary_statistics.__name__)
    ble_mex = dict()
    wifi_mex = dict()
    total_mex = dict()
    terms = ['latency', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput', 'goodput_1']
    terms_2 = ['mean', 'std', 'm_e', 'low', 'up', 'S', 'R', 'L', 'E', 'pdr', 'goodput', 'goodput_1']
    for k, run in my_dictionary.items():
        if k == '_command':
            continue
        if k == '1':
            for t in terms:
                if t != 'goodput_1':
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
                if t != 'goodput_1':
                    ble_mex[t].append(run['statistic_']['ble'][terms_2[i]])
                    wifi_mex[t].append(run['statistic_']['wifi'][terms_2[i]])
                total_mex[t].append(run['statistic_']['total'][terms_2[i]])
            i += 1

    ble = dict()
    wifi = dict()
    total = dict()
    for t in terms:
        if t != 'goodput_1':
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
                                 'goodput_1': total['goodput_1'],
                                 'latency': {'mean': total['latency'], 'std': total['std'],
                                             'm_e': total['m_e'],
                                             'low': total['low'],
                                             'up': total['up']}}}}


def save_statistics_data():
    path_json = outcome_path + "delay_XXX_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def plot_1(ble, wifi, total):
    types = ['ble', 'wifi', 'ble_wifi']
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
        else:
            my_list = []
            type_s = ''

        if len(my_list) == 0:
            continue

        for k, v in my_list.items():
            my.plot_latency(dataset=v, run=k, type=tech)
        title_str = "Relay_" + str(relay[index_relay]) + " Delay_" + str(delay[index_delay]) + "ms [" + str(
            tech) + "] XXX"
        path_graph = outcome_path + str(delay[index_delay]) + "_XXX_" + type_s + "_" + str(tech) + ".png"
        my.save_plot_2(type=tech, title=title_str, path=path_graph, type_s=type_s)


def group_main():
    global index_delay
    global index_relay
    global source_path
    global cuts_path
    global outcome_path
    for d in range(len(delay)):
        index_delay = d
        source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
            delay[index_delay]) + "/*_analysis.json"
        cuts_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/delay_x_" + str(
            delay[index_delay]) + ".json"
        outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/"
        main()
        time.sleep(1)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    cuts = my.open_file_and_return_data(path=cuts_path)
    i = 1
    my_list_ble = dict()
    my_list_wifi = dict()
    my_list_total = dict()
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble, l_wifi, l_total = statistics(data=data, run=i, x=cuts)
        my_list_ble[i] = l_ble
        my_list_wifi[i] = l_wifi
        my_list_total[i] = l_total
        i += 1

    # Summary
    summary_statistics()
    save_statistics_data()

    # PLOT
    plot_1(ble=my_list_ble, wifi=my_list_wifi, total=my_list_total)


if __name__ == "__main__":
    try:
        if not approach:
            main()
        else:
            group_main()
    except Exception as e:
        print(e)
    sys.exit()
