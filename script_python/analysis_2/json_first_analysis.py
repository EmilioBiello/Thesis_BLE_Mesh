import emilio_function as my
import datetime as dt
import glob
import numpy as np
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_topic = 2  # 0..2
index_delay = 4  # 0..8
################################################################
topic = [0, 1, 2]
delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/delay_" + str(
    delay[index_delay]) + "/*_analysis.json"
outcome_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/outcomes/"

# Variabili globali
my_dictionary = dict()


def statistics(data, run):
    mex = data['_mex']
    latency_ble = dict()
    latency_wifi = dict()
    waits = dict()

    for index, list_of_value in mex.items():
        for v in list_of_value:
            if 'ble' in v or 'wifi' in v:
                if 'ble' in v:
                    latency_ble[int(index)] = v['ble']['latency']
                if 'wifi' in v:
                    latency_wifi[int(index)] = v['wifi']['latency']
                if 'wait' in v:
                    waits[int(index)] = v['wait']['wait']

    l_ble = list(latency_ble.values())
    l_wifi = list(latency_wifi.values())
    ble_ = my.intervalli_di_confidenza(dataset=l_ble)
    wifi_ = my.intervalli_di_confidenza(dataset=l_wifi)

    start_test = dt.datetime.strptime(data['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
    end_test = dt.datetime.strptime(data['_info']['end_test'], '%Y-%m-%d %H:%M:%S.%f')
    time_test = end_test - start_test
    # TODO BLE
    pdr_ble = float(
        data['_info_2']['mex_']['ble']['receive_ble'] / data['_info_2']['mex_']['ble']['send_ble'])
    pdr_ble_2 = float(
        data['_info_2']['mex_']['ble']['receive_ble'] / data['_command']['n_mex'])
    goodput_ble = (data['_info_2']['mex_']['ble'][
                       'receive_ble'] * 2) / time_test.total_seconds()  # 2 byte di dati utili
    # TODO WIFI
    start_test = start_test + dt.timedelta(0, 40)  # aggiungo 40 secondi
    time_test = end_test - start_test
    pdr_wifi = float(
        data['_info_2']['mex_']['wifi']['receive_wifi'] / data['_info_2']['mex_']['wifi']['send_wifi'])
    goodput_wifi = (data['_info_2']['mex_']['wifi'][
                        'receive_wifi'] * 2) / time_test.total_seconds()  # 2 byte di dati utili

    # TODO Save data about LATENCY, PDR, GOODPUT
    m = data['_info_2']['mex_']
    my_dictionary[str(run)] = {'_info': data['_info'],
                               'mex_': {'ble': {'sent': m['ble']['send_ble'], 'received': m['ble']['receive_ble'],
                                                'lost': m['ble']['lost_ble'], 'not_sent': m['ble']['not_send_ble']},
                                        'wifi': {'sent': m['wifi']['send_wifi'], 'received': m['wifi']['receive_wifi'],
                                                 'lost': m['wifi']['lost_wifi'],
                                                 'not_sent': m['wifi']['not_send_wifi']},
                                        'extra': {'double_sent': m['double_sent'],
                                                  'sent_received_total': m['sent_received_total'],
                                                  'valid_mex': m['valid_mex']}},
                               'statistic_': {'ble': {'sample_size': len(l_ble),
                                                      'pdr': pdr_ble,
                                                      'goodput': goodput_ble,
                                                      'latency': {'mean': ble_['mean'], 'std': ble_['std'],
                                                                  'error_margin': ble_['e_m'],
                                                                  'lower': ble_['low'],
                                                                  'upper': ble_['up'], 'min_value': np.min(l_ble),
                                                                  'max_value': np.max(l_ble)
                                                                  }},
                                              'wifi': {'sample_size': len(l_wifi),
                                                       'pdr': pdr_wifi,
                                                       'goodput': goodput_wifi,
                                                       'latency': {'mean': wifi_['mean'], 'std': wifi_['std'],
                                                                   'error_margin': wifi_['e_m'],
                                                                   'lower': wifi_['low'],
                                                                   'upper': wifi_['up'], 'min_value': np.min(l_wifi),
                                                                   'max_value': np.max(l_wifi)
                                                                   }}}}
    return latency_ble, latency_wifi


def summary_statistics():
    ble_mex = dict()
    wifi_mex = dict()
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
        wifi_mex['std'].append(run['statistic_']['wifi']['latency']['mean'])
        wifi_mex['m_e'].append(run['statistic_']['wifi']['latency']['mean'])
        wifi_mex['lower'].append(run['statistic_']['wifi']['latency']['lower'])
        wifi_mex['upper'].append(run['statistic_']['wifi']['latency']['upper'])
        wifi_mex['sent'].append(run['mex_']['wifi']['sent'])
        wifi_mex['received'].append(run['mex_']['wifi']['received'])
        wifi_mex['lost'].append(run['mex_']['wifi']['lost'])
        wifi_mex['not_sent'].append(run['mex_']['wifi']['not_sent'])
        wifi_mex['pdr'].append(run['statistic_']['wifi']['pdr'])
        wifi_mex['goodput'].append(run['statistic_']['wifi']['goodput'])

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

    my_dictionary['summary'] = {
        'mex_': {'ble': {'sent': mex_ble_S, 'received': mex_ble_R, 'lost': mex_ble_L, 'not_sent': mex_ble_NS},
                 'wifi': {'sent': mex_wifi_S, 'received': mex_wifi_R, 'lost': mex_wifi_L, 'not_sent': mex_wifi_NS}},
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
                                            }}}}


def save_statistics_data():
    path_json = outcome_path + "delay_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    i = 1
    my_list_ble = dict()
    my_list_wifi = dict()
    for item in files:
        print("\x1b[1;30;43m " + str(i) + " \x1b[1;34;40m " + item[28:] + " \x1b[0m ")
        data = my.open_file_and_return_data(path=item)
        if i == 1:
            my_dictionary['_command'] = data['_command']
        l_ble, l_wifi = statistics(data=data, run=i)
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
        path_graph = outcome_path + "latencies_" + str(delay[index_delay]) + "_" + str(tech) + ".png"
        my.save_plot(type=tech, title_str=title_str, path_graph=path_graph)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
sys.exit()
