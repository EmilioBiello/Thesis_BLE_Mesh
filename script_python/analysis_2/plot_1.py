import sys
import emilio_function as my
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import scipy as sc
from scipy.interpolate import interp1d
import numpy as np

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
approach = 1  # 0 -> normal, 1-> cuts
index_relay = 1  # 0..2
tech = 'ble_wifi_output'
# index_delay = 0  # 0..6
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
outcome_path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/outcomes/"
outcome_path_x = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/x/"


def plot(dataset, tech):
    pxs = []
    pys = []
    for index in delay:
        print("delay: {}".format(index))
        for run in dataset[index]:
            x = index
            y = dataset[x][run]
            for e in y:
                pxs.append(x)
                pys.append(e)

    if tech == 'BLE':
        plt.scatter(pxs, pys, color="blue", s=5)
    elif tech == 'WiFi':
        plt.scatter(pxs, pys, color="green", s=5)
    else:
        plt.scatter(pxs, pys, color="red", s=5)

    text = tech + " relay_" + str(index_relay)
    plt.title(text)
    plt.xlabel('x - Frequencies')
    plt.ylabel('y - latency [seconds]')
    plt.xticks(delay, delay)

    if approach:
        path_graph = outcome_path_x + "_latencies_X_" + str(tech) + "_relay_" + str(relay[index_relay]) + ".png"
    else:
        path_graph = outcome_path + "_latencies_" + str(tech) + "_relay_" + str(relay[index_relay]) + ".png"
    print("\x1b[1;32;40m Saving Graph {}: {}\x1b[0m".format(tech, path_graph))
    plt.savefig(path_graph)
    plt.show()


def get_all_value_cuts_ble(dataset, run, cut):
    min_index = cut[str(run)]['smaller']
    max_index = cut[str(run)]['bigger']

    l_ble = list()
    for index, value in dataset.items():
        if min_index <= int(index) <= max_index:
            for v in value:
                if 'ble' in v:
                    l_ble.append(v['ble']['latency'])
    return l_ble


def get_all_value_ble(dataset):
    l_ble = list()
    for index, value in dataset.items():
        for v in value:
            if 'ble' in v:
                l_ble.append(v['ble']['latency'])
    return l_ble


def get_all_value(dataset):
    l_ble = list()
    l_wifi = list()
    l_total = list()
    for index, value in dataset.items():
        for v in value:
            if 'ble' in v or 'wifi' in v or 'ble_wifi' in v:
                if 'ble' in v:
                    l_ble.append(v['ble']['latency'])
                    l_total.append(v['ble']['latency'])
                if 'wifi' in v:
                    l_wifi.append(v['wifi']['latency'])
                if 'ble_wifi' in v and 'latency_1' in v['ble_wifi']:
                    l_total.append(v['ble_wifi']['latency_1'])

    return l_ble, l_wifi, l_total


def get_all_value_cuts(dataset, run, cut):
    min_index = cut[str(run)]['smaller']
    max_index = cut[str(run)]['bigger']

    l_ble = list()
    l_wifi = list()
    l_total = list()
    for index, value in dataset.items():
        if min_index <= int(index) <= max_index:
            for v in value:
                if 'ble' in v:
                    l_ble.append(v['ble']['latency'])
                    l_total.append(v['ble']['latency'])
                if 'wifi' in v:
                    l_wifi.append(v['wifi']['latency'])
                if 'ble_wifi' in v and 'latency_1' in v['ble_wifi']:
                    l_total.append(v['ble_wifi']['latency_1'])
    return l_ble, l_wifi, l_total


def get_all_value_2(dataset, run, cut):
    min_index = cut[str(run)]['smaller']
    max_index = cut[str(run)]['bigger']
    delay = dataset['_command']['delay']
    pxs = []
    pys = []
    pzs = []
    for index, value in dataset['_mex'].items():
        if min_index <= int(index) <= max_index:
            for v in value:
                if 'ble' in v or 'wifi' in v or 'ble_wifi' in v:
                    if 'ble' in v:
                        pxs.append(delay)
                        pys.append(v['ble']['latency'])
                        pzs.append('ble')
                    if 'ble_wifi' in v and 'latency_1' in v['ble_wifi']:
                        pxs.append(delay)
                        pys.append(v['ble_wifi']['latency_1'])
                        pzs.append('wifi')
    return pxs, pys, pzs


def plot_2(df):
    sns.lmplot(x="delay", y="latency", palette='muted', hue='type', ci=None, data=df, order=5,
               scatter_kws={"s": 5})

    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("latency [s]")
    title = "Latencies" + " relay_" + str(relay[index_relay])
    plt.title(title)
    plt.show()


def plot_with(x, y):
    f2 = sc.interpolate.interp1d(x, y, kind='cubic')
    alpha = np.linspace(min(x), max(y, 100))

    plt.plot(x, y, 'o')
    plt.plot(alpha, f2(alpha), '--')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.show()


# lmplot
def plot_3(df, dictionary, y_label, title):
    sns.lmplot(x='delay', y='y_data', data=df, hue='type', palette='muted', fit_reg=False, ci=None, height=5,
               aspect=2, scatter_kws={"s": 45}, legend_out=False)

    xs_0 = np.linspace(min(dictionary[0]['x']), max(dictionary[0]['x']), 100)
    xs_1 = np.linspace(min(dictionary[1]['x']), max(dictionary[1]['x']), 100)
    xs_2 = np.linspace(min(dictionary[2]['x']), max(dictionary[2]['x']), 100)

    # spl_0 = sc.interpolate.UnivariateSpline(dictionary[0]['x'], dictionary[0]['y'])
    # spl_1 = sc.interpolate.UnivariateSpline(dictionary[1]['x'], dictionary[1]['y'])
    # spl_2 = sc.interpolate.UnivariateSpline(dictionary[2]['x'], dictionary[2]['y'])
    # spl_0.set_smoothing_factor(0.01)
    # spl_1.set_smoothing_factor(0.01)
    # spl_2.set_smoothing_factor(0.01)
    # plt.plot(xs_0, spl_0(xs_0), '--', label='spline', color='lightblue')
    # plt.plot(xs_1, spl_1(xs_1), '--', label='spline', color='orange')
    # plt.plot(xs_2, spl_2(xs_2), '--', label='spline', color='green')

    f1 = sc.interpolate.interp1d(dictionary[0]['x'], dictionary[0]['y'], kind='linear')
    f2 = sc.interpolate.interp1d(dictionary[1]['x'], dictionary[1]['y'], kind='linear')
    f3 = sc.interpolate.interp1d(dictionary[2]['x'], dictionary[2]['y'], kind='linear')
    # f1 = sc.interpolate.interp1d(x, y, kind='cubic')
    # f2 = sc.interpolate.interp1d(x, y, kind='linear')
    # f5 = sc.interpolate.interp1d(x, y, kind='slinear')
    # f6 = sc.interpolate.interp1d(x, y, kind='quadratic')
    plt.plot(xs_0, f1(xs_0), '--', color='#4878D0')  # blue
    plt.plot(xs_1, f2(xs_1), '--', color='#EE854A')  # orange
    plt.plot(xs_2, f3(xs_2), '--', color='#6ACC64')  # green
    # plt.legend(loc='best')
    plt.xticks(delay, rotation=30)

    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel(y_label)
    plt.title(title)
    sns.despine()  # is a function that removes the spines from the right and upper portion of the plot by default.
    plt.show()


def main_4():
    x = list()
    y = list()
    z = list()

    directory = ['ble_wifi_output', 'ble_output']
    dictionary = dict()

    type_graph = 'latency'

    if type_graph == 'latency':
        y_label = 'Latency (s)'
        title = 'Latency'
    elif type_graph == 'pdr':
        y_label = 'Packet Delivery Ratio'
        title = y_label
    else:
        y_label = 'Goodput (byte/s)'
        title = 'Goodput'
    for d1 in directory:
        if d1 == 'ble_wifi_output':
            hue = 'ble_wifi'
        else:
            hue = 'ble'
        dictionary[hue] = dict()
        for r in range(len(relay)):
            dictionary[hue][r] = {'x': list(), 'y': list()}
            for d in range(len(delay)):
                path = my.path_media + "json_file/" + d1 + "/relay_" + str(relay[r]) + "/x/delay_XXX_" + str(
                    delay[d]) + ".json"

                files = my.get_grouped_files(source_path=path, delay=delay, index_delay=d)

                i = 1
                for item in files:
                    data = my.open_file_and_return_data(path=item)
                    t = hue + ' relay_' + str(r)

                    if hue == 'ble_wifi':
                        if type_graph == 'latency':
                            value = data['summary']['statistic_']['total'][type_graph]['mean']
                        else:
                            value = data['summary']['statistic_']['total'][type_graph]
                    else:
                        if type_graph == 'latency':
                            value = data['summary']['statistic_'][type_graph]['mean']
                        else:
                            value = data['summary']['statistic_'][type_graph]

                    x.append(data['_command']['delay'])
                    y.append(value)
                    z.append(t)
                    dictionary[hue][r]['x'].append(data['_command']['delay'])
                    dictionary[hue][r]['y'].append(value)
                    i += 1

    dataframe = {'delay': x, 'latency': y, 'type': z}
    df = pd.DataFrame(dataframe)
    print(df.head())
    # colors = ['#4878D0', '#EE854A', '#6ACC64', '#D65F5F', '#82C6E2', '#D5BB67']
    # sns.set_palette(sns.color_palette(colors))
    sns.lmplot(x='delay', y='latency', data=df, hue='type', palette='muted', fit_reg=False, ci=None, height=5,
               aspect=2, scatter_kws={"s": 45}, legend_out=False)
    xs_b_0 = np.linspace(min(dictionary['ble'][0]['x']), max(dictionary['ble'][0]['x']), 100)
    xs_b_1 = np.linspace(min(dictionary['ble'][1]['x']), max(dictionary['ble'][1]['x']), 100)
    xs_b_2 = np.linspace(min(dictionary['ble'][2]['x']), max(dictionary['ble'][2]['x']), 100)
    xs_bw_0 = np.linspace(min(dictionary['ble_wifi'][0]['x']), max(dictionary['ble_wifi'][0]['x']), 100)
    xs_bw_1 = np.linspace(min(dictionary['ble_wifi'][1]['x']), max(dictionary['ble_wifi'][1]['x']), 100)
    xs_bw_2 = np.linspace(min(dictionary['ble_wifi'][2]['x']), max(dictionary['ble_wifi'][2]['x']), 100)

    f_b_0 = sc.interpolate.interp1d(dictionary['ble'][0]['x'], dictionary['ble'][0]['y'], kind='linear')
    f_b_1 = sc.interpolate.interp1d(dictionary['ble'][1]['x'], dictionary['ble'][1]['y'], kind='linear')
    f_b_2 = sc.interpolate.interp1d(dictionary['ble'][2]['x'], dictionary['ble'][2]['y'], kind='linear')
    f_bw_0 = sc.interpolate.interp1d(dictionary['ble_wifi'][0]['x'], dictionary['ble_wifi'][0]['y'], kind='linear')
    f_bw_1 = sc.interpolate.interp1d(dictionary['ble_wifi'][1]['x'], dictionary['ble_wifi'][1]['y'], kind='linear')
    f_bw_2 = sc.interpolate.interp1d(dictionary['ble_wifi'][2]['x'], dictionary['ble_wifi'][2]['y'], kind='linear')

    plt.plot(xs_b_0, f_b_0(xs_b_0), '--', color='#D65F5F')  # red
    plt.plot(xs_b_1, f_b_1(xs_b_1), '--', color='#956CB4')  # purple
    plt.plot(xs_b_2, f_b_2(xs_b_2), '--', color='#8C613C')  # brown
    plt.plot(xs_bw_0, f_bw_0(xs_bw_0), '--', color='#4878D0')  # blue
    plt.plot(xs_bw_1, f_bw_1(xs_bw_1), '--', color='#EE854A')  # orange
    plt.plot(xs_bw_2, f_bw_2(xs_bw_2), '--', color='#6ACC64')  # green
    # plt.legend(loc='best')
    plt.xticks(delay, rotation=30)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel(y_label)
    plt.title(title)
    sns.despine()  # is a function that removes the spines from the right and upper portion of the plot by default.
    plt.show()


# TODO plot all relay for ble and for ble-wifi (cuts)
def main_3():
    x = list()
    y = list()
    z = list()
    directory = 'ble_wifi_output'
    tech = " - [BLE - WiFi]"
    type_graph = 'goodput_1'
    dictionary = dict()

    if type_graph == 'latency':
        y_label = 'Latency (s)'
        title = 'Latency' + tech
    elif type_graph == 'pdr':
        y_label = 'Packet Delivery Ratio'
        title = y_label + tech
    else:
        y_label = 'Goodput (byte/s)'
        title = 'Goodput' + tech

    for r in range(len(relay)):
        dictionary[r] = {'x': list(), 'y': list()}
        for d in range(len(delay)):
            path = my.path_media + "json_file/" + directory + "/relay_" + str(relay[r]) + "/x/delay_XXX_" + str(
                delay[d]) + ".json"
            files = my.get_grouped_files(source_path=path, delay=delay, index_delay=d)

            i = 1
            for item in files:
                data = my.open_file_and_return_data(path=item)
                t = 'relay_' + str(r)
                z.append(t)
                x.append(data['_command']['delay'])
                dictionary[r]['x'].append(data['_command']['delay'])

                if directory == 'ble_wifi_output':
                    if type_graph == 'latency':
                        value = data['summary']['statistic_']['total'][type_graph]['mean']
                    else:
                        value = data['summary']['statistic_']['total'][type_graph]
                else:
                    if type_graph == 'latency':
                        value = data['summary']['statistic_'][type_graph]['mean']
                    else:
                        value = data['summary']['statistic_'][type_graph]

                y.append(value)
                dictionary[r]['y'].append(value)
                i += 1

    dataframe = {'delay': x, 'y_data': y, 'type': z}
    df = pd.DataFrame(dataframe)
    # sns.lmplot(x="delay", y="latency", palette='muted', hue='type', ci=None, data=df, order=5,height=5, aspect=2,
    #            scatter_kws={"s": 50},legend_out=False)

    plot_3(df, dictionary, y_label, title)


def main_2():
    my_list = {'delay': list(), 'latency': list(), 'type': list()}
    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/ble_wifi_output/relay_" + str(relay[index_relay]) + "/" + str(
            delay[index_delay]) + "/*_analysis.json"
        cuts_path = my.path_media + "json_file/ble_wifi_output/relay_" + str(relay[index_relay]) + "/x/delay_x_" + str(
            delay[index_delay]) + ".json"

        files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
        cuts = my.open_file_and_return_data(path=cuts_path)
        i = 1
        for item in files:
            data = my.open_file_and_return_data(path=item)
            pxs, pys, pzs = get_all_value_2(dataset=data, run=i, cut=cuts)
            my_list['delay'].append(pxs)
            my_list['latency'].append(pys)
            my_list['type'].append(pzs)
            i += 1

    pxs = list()
    pys = list()
    pzs = list()
    runs = len(my_list['delay'])
    for r in range(runs):
        item = len(my_list['delay'][r])
        for i in range(item):
            pxs.append(my_list['delay'][r][i])
            pys.append(my_list['latency'][r][i])
            pzs.append(my_list['type'][r][i])

    dataframe = {'delay': pxs, 'y_data': pys, 'type': pzs}
    df = pd.DataFrame(dataframe)
    print(df.head())
    plot_with(pxs, pys)


# TODO plot latency about all single mex (CUT)
def main_cut():
    my_list_ble = dict()
    if tech == 'ble_wifi_output':
        my_list_wifi = dict()
        my_list_total = dict()

    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/" + str(
            delay[index_delay]) + "/*_analysis.json"
        cuts_path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/x/delay_x_" + str(
            delay[index_delay]) + ".json"
        files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
        cuts = my.open_file_and_return_data(path=cuts_path)

        i = 1
        my_list_ble[delay[index_delay]] = dict()
        if tech == 'ble_wifi_output':
            my_list_wifi[delay[index_delay]] = dict()
            my_list_total[delay[index_delay]] = dict()

        for item in files:
            data = my.open_file_and_return_data(path=item)['_mex']
            if tech == 'ble_wifi_output':
                l_ble, l_wifi, l_total = get_all_value_cuts(dataset=data, run=i, cut=cuts)
                my_list_ble[delay[index_delay]][i] = l_ble
                my_list_wifi[delay[index_delay]][i] = l_wifi
                my_list_total[delay[index_delay]][i] = l_total
            else:
                l_ble = get_all_value_cuts_ble(dataset=data, run=i, cut=cuts)
                my_list_ble[delay[index_delay]][i] = l_ble
            i += 1

    plot(my_list_ble, "BLE")
    plot(my_list_wifi, "WiFi")
    plot(my_list_total, "BLE - WiFi")


# TODO plot latency about all single mex
def main():
    my_list_ble = dict()
    if tech == 'ble_wifi_output':
        my_list_wifi = dict()
        my_list_total = dict()

    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/" + tech + "/relay_" + str(relay[index_relay]) + "/" + str(
            delay[index_delay]) + "/*_analysis.json"
        files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)

        my_list_ble[delay[index_delay]] = dict()
        if tech == 'ble_wifi_output':
            my_list_wifi[delay[index_delay]] = dict()
            my_list_total[delay[index_delay]] = dict()

        i = 1
        for item in files:
            data = my.open_file_and_return_data(path=item)['_mex']
            if tech == 'ble_wifi_output':
                l_ble, l_wifi, l_total = get_all_value(dataset=data)
                my_list_ble[delay[index_delay]][i] = l_ble
                my_list_wifi[delay[index_delay]][i] = l_wifi
                my_list_total[delay[index_delay]][i] = l_total
            else:
                l_ble = get_all_value_ble(dataset=data)
                my_list_ble[delay[index_delay]][i] = l_ble
            i += 1

    plot(my_list_ble, "BLE")
    if tech == 'ble_wifi_output':
        plot(my_list_wifi, "WiFi")
        plot(my_list_total, "BLE - WiFi")


if __name__ == "__main__":
    try:
        # if approach:
        #     main_cut()
        # else:
        #     main()
        main_3()
        # main_4()
    except Exception as e:
        print(e)
    sys.exit()
