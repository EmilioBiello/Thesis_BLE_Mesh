import emilio_function as my
import datetime as dt
import glob
import numpy as np
import matplotlib.pyplot as plt
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_topic = 2  # 0..2
index_delay = 2  # 0..6
################################################################
topic = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/delay_" + str(
    delay[index_delay]) + "/*_analysis.json"
cuts_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/outcomes/cuts/delay_x_" + str(
    delay[index_delay]) + ".json"
outcome_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/outcomes/"

my_dictionary = dict()


def statistics(data, run, cut):
    mex = data['_mex']
    min_index_ble = cut[str(run)]['ble']['lower']
    max_index_ble = cut[str(run)]['ble']['upper']
    min_index_wifi = cut[str(run)]['wifi']['lower']
    max_index_wifi = cut[str(run)]['wifi']['upper']
    latency_ble = dict()
    latency_wifi = dict()
    info_ble = {'sent': 0, 'received': 0, 'lost': 0, 'error': 0}
    info_wifi = {'sent': 0, 'received': 0, 'lost': 0, 'error': 0}
    end_test = dt.datetime.strptime(cut[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    for index, list_of_value in mex.items():
        for v in list_of_value:
            if min_index_ble <= int(index) <= max_index_ble:
                if 'type_mex' in v and v['type_mex'] == "S":
                    info_ble['sent'] += 1
                if 'type_mex' in v and v['type_mex'] == "E":
                    info_ble['error'] += 1
                if 'ble' in v:
                    info_ble['received'] += 1
                    latency_ble[int(index)] = v['ble']['latency']
                    rcv = dt.datetime.strptime(v['ble']['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                    if rcv > end_test:
                        end_test = rcv

            if min_index_wifi <= int(index) <= max_index_wifi:
                if 'type_mex' in v and v['type_mex'] == "I":
                    info_wifi['sent'] += 1
                if 'type_mex' in v and v['type_mex'] == "W":
                    info_wifi['error'] += 1
                if 'wifi' in v:
                    info_wifi['received'] += 1
                    latency_wifi[int(index)] = v['wifi']['latency']
                    rcv = dt.datetime.strptime(v['wifi']['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                    if rcv > end_test:
                        end_test = rcv

    info_ble['lost'] = info_ble['sent'] - info_ble['received'] - info_ble['error']
    info_wifi['lost'] = info_wifi['sent'] - info_wifi['received'] - info_wifi['error']
    info_combine = {'sent': info_ble['sent'] + info_wifi['sent'],
                    'received': info_ble['received'] + info_wifi['received'],
                    'lost': info_ble['lost'] + info_wifi['lost'],
                    'error': info_ble['error'] + info_wifi['error']}
    l_ble = list(latency_ble.values())
    l_wifi = list(latency_wifi.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)
    wifi_ = my.intervalli_di_confidenza(dataset=l_wifi)
    combine_ = my.intervalli_di_confidenza(dataset=l_ble + l_wifi)
    start_test = dt.datetime.strptime(cut[str(run)]['time']['new_start'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = end_test - start_test

    ble_['pdr'] = float(info_ble['received'] / info_ble['sent'])
    wifi_['pdr'] = float(info_wifi['received'] / info_wifi['sent'])
    ble_['goodput'] = info_ble['received'] * 2 / time_test.total_seconds()
    wifi_['goodput'] = info_wifi['received'] * 2 / time_test.total_seconds()

    combine_['pdr'] = float(info_combine['received'] / (info_combine['sent']))
    combine_['goodput'] = (info_combine['received'] * 2) / time_test.total_seconds()

    end_send = dt.datetime.strptime(cut[str(run)]['time']['new_end'], '%Y-%m-%d %H:%M:%S.%f')
    h, m, s = my.convert_timedelta((end_send - start_test))
    time_send_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"
    h, m, s = my.convert_timedelta(time_test)
    time_test_ = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"

    my_dictionary[str(run)] = {'_info_0': data['_info'],
                               '_info_1': {'end_sent': cut[str(run)]['time']['new_end'], 'end_test': end_test,
                                           'start': cut[str(run)]['time']['new_start'], 'time_send': time_send_,
                                           'time_test': time_test_},
                               'mex_': {'ble': {'sent': info_ble['sent'], 'received': info_ble['received'],
                                                'lost': info_ble['lost'], 'not_sent': info_ble['error']},
                                        'wifi': {'sent': info_wifi['sent'], 'received': info_wifi['received'],
                                                 'lost': info_wifi['lost'], 'not_sent': info_wifi['error']},
                                        'combine': {'sent': info_combine['sent'], 'received': info_combine['received'],
                                                    'lost': info_combine['lost'], 'not_sent': info_combine['error']}},
                               'statistic_': {'ble': {'sample_size': len(l_ble),
                                                      'pdr': ble_['pdr'],
                                                      'goodput': ble_['goodput'],
                                                      'latency': {'mean': ble_['mean'], 'std': ble_['std'],
                                                                  'error_margin': ble_['e_m'],
                                                                  'lower': ble_['low'],
                                                                  'upper': ble_['up'], 'min_value': np.min(l_ble),
                                                                  'max_value': np.max(l_ble)
                                                                  }},
                                              'wifi': {'sample_size': len(l_wifi),
                                                       'pdr': wifi_['pdr'],
                                                       'goodput': wifi_['goodput'],
                                                       'latency': {'mean': wifi_['mean'], 'std': wifi_['std'],
                                                                   'error_margin': wifi_['e_m'],
                                                                   'lower': wifi_['low'],
                                                                   'upper': wifi_['up'], 'min_value': np.min(l_wifi),
                                                                   'max_value': np.max(l_wifi)
                                                                   }},
                                              'combine': {'sample_size': len(l_ble) + len(l_wifi),
                                                          'pdr': combine_['pdr'],
                                                          'goodput': combine_['goodput'],
                                                          'latency': {'mean': combine_['mean'], 'std': combine_['std'],
                                                                      'error_margin': combine_['e_m'],
                                                                      'lower': combine_['low'],
                                                                      'upper': combine_['up']
                                                                      }}}}
    return latency_ble, latency_wifi


def summary_statistics():
    ble_mex = dict()
    wifi_mex = dict()
    combine_mex = dict()
    for k, run in my_dictionary.items():
        if k == '_command':
            continue
        if k == '1':
            ble_mex['latency'] = []
            ble_mex['std'] = []
            ble_mex['m_e'] = []
            ble_mex['lower'] = []
            ble_mex['upper'] = []
            ble_mex['sent'] = []
            ble_mex['received'] = []
            ble_mex['lost'] = []
            ble_mex['not_sent'] = []
            ble_mex['pdr'] = []
            ble_mex['goodput'] = []
            wifi_mex['latency'] = []
            wifi_mex['std'] = []
            wifi_mex['m_e'] = []
            wifi_mex['lower'] = []
            wifi_mex['upper'] = []
            wifi_mex['sent'] = []
            wifi_mex['received'] = []
            wifi_mex['lost'] = []
            wifi_mex['not_sent'] = []
            wifi_mex['pdr'] = []
            wifi_mex['goodput'] = []
            combine_mex['latency'] = []
            combine_mex['std'] = []
            combine_mex['m_e'] = []
            combine_mex['lower'] = []
            combine_mex['upper'] = []
            combine_mex['sent'] = []
            combine_mex['received'] = []
            combine_mex['lost'] = []
            combine_mex['not_sent'] = []
            combine_mex['pdr'] = []
            combine_mex['goodput'] = []
        # BLE
        ble_mex['latency'].append(run['statistic_']['ble']['latency']['mean'])
        ble_mex['std'].append(run['statistic_']['ble']['latency']['std'])
        ble_mex['m_e'].append(run['statistic_']['ble']['latency']['error_margin'])
        ble_mex['lower'].append(run['statistic_']['ble']['latency']['lower'])
        ble_mex['upper'].append(run['statistic_']['ble']['latency']['upper'])
        ble_mex['sent'].append(run['mex_']['ble']['sent'])
        ble_mex['received'].append(run['mex_']['ble']['received'])
        ble_mex['lost'].append(run['mex_']['ble']['lost'])
        ble_mex['not_sent'].append(run['mex_']['ble']['not_sent'])
        ble_mex['pdr'].append(run['statistic_']['ble']['pdr'])
        ble_mex['goodput'].append(run['statistic_']['ble']['goodput'])
        # WIFI
        wifi_mex['latency'].append(run['statistic_']['wifi']['latency']['mean'])
        wifi_mex['std'].append(run['statistic_']['wifi']['latency']['std'])
        wifi_mex['m_e'].append(run['statistic_']['wifi']['latency']['error_margin'])
        wifi_mex['lower'].append(run['statistic_']['wifi']['latency']['lower'])
        wifi_mex['upper'].append(run['statistic_']['wifi']['latency']['upper'])
        wifi_mex['sent'].append(run['mex_']['wifi']['sent'])
        wifi_mex['received'].append(run['mex_']['wifi']['received'])
        wifi_mex['lost'].append(run['mex_']['wifi']['lost'])
        wifi_mex['not_sent'].append(run['mex_']['wifi']['not_sent'])
        wifi_mex['pdr'].append(run['statistic_']['wifi']['pdr'])
        wifi_mex['goodput'].append(run['statistic_']['wifi']['goodput'])
        # COMBINE
        combine_mex['latency'].append(run['statistic_']['combine']['latency']['mean'])
        combine_mex['std'].append(run['statistic_']['combine']['latency']['std'])
        combine_mex['m_e'].append(run['statistic_']['combine']['latency']['error_margin'])
        combine_mex['lower'].append(run['statistic_']['combine']['latency']['lower'])
        combine_mex['upper'].append(run['statistic_']['combine']['latency']['upper'])
        combine_mex['sent'].append(run['mex_']['combine']['sent'])
        combine_mex['received'].append(run['mex_']['combine']['received'])
        combine_mex['lost'].append(run['mex_']['combine']['lost'])
        combine_mex['not_sent'].append(run['mex_']['combine']['not_sent'])
        combine_mex['pdr'].append(run['statistic_']['combine']['pdr'])
        combine_mex['goodput'].append(run['statistic_']['combine']['goodput'])

    # BLE
    mean_L_ble = np.mean(ble_mex['latency'])
    mean_STD_ble = np.mean(ble_mex['std'])
    mean_ME_ble = np.mean(ble_mex['m_e'])
    mean_Lower_ble = np.mean(ble_mex['lower'])
    mean_Upper_ble = np.mean(ble_mex['upper'])
    mex_ble_S = np.mean(ble_mex['sent'])
    mex_ble_R = np.mean(ble_mex['received'])
    mex_ble_L = np.mean(ble_mex['lost'])
    mex_ble_NS = np.mean(ble_mex['not_sent'])
    mex_ble_pdr = np.mean(ble_mex['pdr'])
    mex_ble_goodput = np.mean(ble_mex['goodput'])

    # WIFI
    mean_L_wifi = np.mean(wifi_mex['latency'])
    mean_STD_wifi = np.mean(wifi_mex['std'])
    mean_ME_wifi = np.mean(wifi_mex['m_e'])
    mean_Lower_wifi = np.mean(wifi_mex['lower'])
    mean_Upper_wifi = np.mean(wifi_mex['upper'])
    mex_wifi_S = np.mean(wifi_mex['sent'])
    mex_wifi_R = np.mean(wifi_mex['received'])
    mex_wifi_L = np.mean(wifi_mex['lost'])
    mex_wifi_NS = np.mean(wifi_mex['not_sent'])
    mex_wifi_pdr = np.mean(wifi_mex['pdr'])
    mex_wifi_goodput = np.mean(wifi_mex['goodput'])

    # COMBINE
    mean_L_combine = np.mean(combine_mex['latency'])
    mean_STD_combine = np.mean(combine_mex['std'])
    mean_ME_combine = np.mean(combine_mex['m_e'])
    mean_Lower_combine = np.mean(combine_mex['lower'])
    mean_Upper_combine = np.mean(combine_mex['upper'])
    mex_combine_S = np.mean(combine_mex['sent'])
    mex_combine_R = np.mean(combine_mex['received'])
    mex_combine_L = np.mean(combine_mex['lost'])
    mex_combine_NS = np.mean(combine_mex['not_sent'])
    mex_combine_pdr = np.mean(combine_mex['pdr'])
    mex_combine_goodput = np.mean(combine_mex['goodput'])

    my_dictionary['summary'] = {
        'mex_': {'ble': {'sent': mex_ble_S, 'received': mex_ble_R, 'lost': mex_ble_L, 'not_sent': mex_ble_NS},
                 'wifi': {'sent': mex_wifi_S, 'received': mex_wifi_R, 'lost': mex_wifi_L, 'not_sent': mex_wifi_NS},
                 'combine': {'sent': mex_combine_S, 'received': mex_combine_R, 'lost': mex_combine_L,
                             'not_sent': mex_combine_NS}},
        'statistic_': {'ble': {'pdr': mex_ble_pdr,
                               'goodput': mex_ble_goodput,
                               'latency': {'mean': mean_L_ble, 'std': mean_STD_ble,
                                           'error_margin': mean_ME_ble,
                                           'lower': mean_Lower_ble,
                                           'upper': mean_Upper_ble}},
                       'wifi': {'pdr': mex_wifi_pdr,
                                'goodput': mex_wifi_goodput,
                                'latency': {'mean': mean_L_wifi, 'std': mean_STD_wifi,
                                            'error_margin': mean_ME_wifi,
                                            'lower': mean_Lower_wifi,
                                            'upper': mean_Upper_wifi
                                            }},
                       'combine': {'pdr': mex_combine_pdr,
                                   'goodput': mex_combine_goodput,
                                   'latency': {'mean': mean_L_combine, 'std': mean_STD_combine,
                                               'error_margin': mean_ME_combine,
                                               'lower': mean_Lower_combine,
                                               'upper': mean_Upper_combine
                                               }}
                       }}


def save_statistics_data():
    path_json = outcome_path + "cuts/delay_X_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    cuts = my.open_file_and_return_data(path=cuts_path)
    i = 1
    my_list_ble = dict()
    my_list_wifi = dict()
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble, l_wifi = statistics(data=data, run=i, cut=cuts)
        my_list_ble[i] = l_ble
        my_list_wifi[i] = l_wifi

        i += 1

    # Summary
    summary_statistics()
    save_statistics_data()

    # PLOT
    types = ['ble', 'wifi']
    for tech in types:
        if tech == 'ble':
            my_list = my_list_ble
        else:
            my_list = my_list_wifi
        for k, v in my_list.items():
            my.plot_latency(dataset=v, run=k, type=tech)
        title_str = "Relay_" + str(topic[index_topic]) + " Delay_" + str(delay[index_delay]) + "ms [" + str(tech) + "]"
        path_graph = outcome_path + "cuts/latencies_" + str(delay[index_delay]) + "_" + str(tech) + ".png"
        my.save_plot(type=tech, title_str=title_str, path_graph=path_graph)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
