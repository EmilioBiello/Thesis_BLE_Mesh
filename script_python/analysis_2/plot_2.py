import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import sys
import emilio_function as my
import glob

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
approach = 1  # 0 -> normal, 1-> cuts
index_relay = 0  # 0..2
# index_delay = 8  # 0..8
################################################################
relay = [0, 1, 2]
# delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
delay = [50, 100, 150, 200, 250, 500, 1000]
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/cuts/"


def define_base_plot():
    plt.style.use('seaborn-whitegrid')
    paper_rc = {'lines.linewidth': 1, 'lines.markersize': 5}
    sns.set_context("paper", rc=paper_rc)
    sns.set(style='ticks', palette='muted')


def plot(dataset, tech):
    pxs = []
    pys = []
    for x in delay:
        print("Delay: ", x)
        for run in dataset[x]:
            y = dataset[x][run]
            for e in y:
                pxs.append(x)
                pys.append(e)

    data = {'delay': pxs, 'latency': pys}
    df = pd.DataFrame(data)
    print(df.head())

    sns.lmplot(x="delay",
               y="latency",
               palette='muted',
               fit_reg=False,
               data=df)

    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("Latency (s)")
    title = tech + "_relay_" + str(relay[index_relay])
    plt.title(title)
    plt.show()


def get_all_value_cuts(dataset, run, cut):
    min_index_ble = cut[str(run)]['ble']['lower']
    max_index_ble = cut[str(run)]['ble']['upper']
    min_index_wifi = cut[str(run)]['wifi']['lower']
    max_index_wifi = cut[str(run)]['wifi']['upper']

    l_ble = list()
    l_wifi = list()
    for index, value in dataset.items():
        for v in value:
            if min_index_ble <= int(index) <= max_index_ble:
                if 'ble' in v:
                    l_ble.append(v['ble']['latency'])
            if min_index_wifi <= int(index) <= max_index_wifi:
                if 'wifi' in v:
                    l_wifi.append(v['wifi']['latency'])
    return l_ble, l_wifi


def main():
    my_list_ble = dict()
    my_list_wifi = dict()
    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/delay_" + str(
            delay[index_delay]) + "/*_analysis.json"
        cuts_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/cuts/delay_x_" + str(
            delay[index_delay]) + ".json"
        files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
        cuts = my.open_file_and_return_data(path=cuts_path)

        i = 1
        my_list_ble[delay[index_delay]] = dict()
        my_list_wifi[delay[index_delay]] = dict()
        for item in files:
            data = my.open_file_and_return_data(path=item)['_mex']
            l_ble, l_wifi = get_all_value_cuts(dataset=data, run=i, cut=cuts)
            my_list_ble[delay[index_delay]][i] = l_ble
            my_list_wifi[delay[index_delay]][i] = l_wifi
            i += 1
    plot(my_list_ble, "BLE")


def plot_2(df):
    sns.lmplot(x="delay", y="pdr", palette='muted', hue='type', fit_reg=False, data=df)

    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("Latency (s)")
    title = "PDR" + " relay_" + str(relay[index_relay])
    plt.title(title)
    plt.show()


# TODO plot latency, PDR e goodput
def main2():
    source_path_2 = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/cuts/delay_X_*.json"
    list_of_files = glob.glob(source_path_2)
    tech = ['ble', 'wifi', 'combine']

    pxs = []
    pys = []
    pzs = []
    for i in range(len(list_of_files)):
        name = list_of_files[i]
        data = my.open_file_and_return_data(name)
        for t in tech:
            pxs.append(data['_command']['delay'])
            pys.append(data['summary']['statistic_'][t]['pdr'])
            pzs.append(t)

    dataframe = {'delay': pxs, 'pdr': pys, 'type': pzs}
    df = pd.DataFrame(dataframe)
    print(df.head())
    define_base_plot()
    plot_2(df)


if __name__ == "__main__":
    try:
        main2()
    except Exception as e:
        print(e)
    sys.exit()
