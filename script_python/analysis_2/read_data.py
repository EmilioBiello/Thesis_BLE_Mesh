import sys
import emilio_function as my
import pandas as pd

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 0  # 0..2
index_delay = 0  # 0..6
tech = 'ble_output'
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
elements = ['1', '2', '3', '4', '5', 'summary']


def main():
    info = {'delay': [], 'run': [], 'S': [], 'R': [], 'L': [], 'pdr': [], 'goodput': [], 'latency': []}
    type_ = 0  # 1 -> normal, 0 -> cuts
    for d in delay:
        if type_:
            path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/outcomes/delay_" + str(
                d) + ".json"
        else:
            path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/x/delay_XXX_" + str(
                d) + ".json"
        data = my.open_file_and_return_data(path=path)
        for item in elements:
            info['delay'].append(d)
            info['run'].append(item)
            if tech == 'ble_wifi_output':
                info['S'].append(data[item]['mex_']['total']['S'])
                info['R'].append(data[item]['mex_']['total']['R'])
                info['L'].append(data[item]['mex_']['total']['L'])
                info['pdr'].append(data[item]['statistic_']['total']['pdr'])
                info['goodput'].append(data[item]['statistic_']['total']['goodput'])
                info['latency'].append(data[item]['statistic_']['total']['latency']['mean'])
            else:
                info['S'].append(data[item]['mex_']['S'])
                info['R'].append(data[item]['mex_']['R'])
                info['L'].append(data[item]['mex_']['L'])
                info['pdr'].append(data[item]['statistic_']['pdr'])
                info['goodput'].append(data[item]['statistic_']['goodput'])
                info['latency'].append(data[item]['statistic_']['latency']['mean'])

    df = pd.DataFrame(info)
    df.sort_values(['delay', 'run'])
    print(df)


def main_summary():
    info = {'relay': [], 'delay': [], 'S': [], 'R': [], 'L': [], 'pdr': [], 'goodput': [], 'latency': []}
    type_ = 0  # 1 -> normal, 0 -> cuts
    for r in relay:
        for d in delay:
            if type_:
                path = my.path_media + "json_file/" + tech + "/relay_" + str(r) + "/outcomes/delay_" + str(d) + ".json"
            else:
                path = my.path_media + "json_file/" + tech + "/relay_" + str(r) + "/x/delay_XXX_" + str(d) + ".json"
            data = my.open_file_and_return_data(path=path)

            info['relay'].append(r)
            info['delay'].append(d)
            if tech == 'ble_wifi_output':
                info['S'].append(data['summary']['mex_']['total']['S'])
                info['R'].append(data['summary']['mex_']['total']['R'])
                info['L'].append(data['summary']['mex_']['total']['L'])
                info['pdr'].append(data['summary']['statistic_']['total']['pdr'])
                info['goodput'].append(data['summary']['statistic_']['total']['goodput'])
                info['latency'].append(data['summary']['statistic_']['total']['latency']['mean'])
            else:
                info['S'].append(data['summary']['mex_']['S'])
                info['R'].append(data['summary']['mex_']['R'])
                info['L'].append(data['summary']['mex_']['L'])
                info['pdr'].append(data['summary']['statistic_']['pdr'])
                info['goodput'].append(data['summary']['statistic_']['goodput'])
                info['latency'].append(data['summary']['statistic_']['latency']['mean'])

    df = pd.DataFrame(info)
    print(df.sort_values(by=['delay', 'relay']))


if __name__ == "__main__":
    try:
        # main()
        main_summary()
    except Exception as e:
        print(e)
    sys.exit()
