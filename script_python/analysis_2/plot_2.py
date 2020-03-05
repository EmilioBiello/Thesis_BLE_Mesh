import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import sys
import emilio_function as my
import glob
from scipy.optimize import curve_fit

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
    paper_rc = {'lines.linewidth': 1, 'lines.markersize': 10}
    sns.set_context("paper", rc=paper_rc)
    sns.set(style='ticks', palette='muted')


def plot_boxplot(df):
    sns.boxplot(x='delay', y='latency', data=df, hue='type', palette='muted', width=0.3, dodge=False)
    plt.title('Box plot - ')
    plt.xlabel("Time between pkt sent (ms)")
    plt.ylabel("Latency (s)")
    sns.despine(offset=10, trim=True)
    plt.show()


def plot_regplot(df):
    sns.regplot(x='delay', y='latency', data=df, fit_reg=False)
    plt.title("regplot with uncertainty")
    plt.xticks(delay)
    plt.xlabel("Time between pkt sent (ms)")
    plt.ylabel("Latency (s)")
    plt.show()


def plot_with_error(df, tech, metric):
    plt.errorbar(x='delay', y=str(metric), data=df, yerr=0, markersize=3, fmt='o', color='red', ecolor='black',
                 capsize=2, barsabove=False, alpha=0.1)

    plt.title("Scatter plot with error bars - " + str(tech))
    plt.xticks(delay)
    plt.xlabel("Time between pkt sent (ms)")
    plt.ylabel("Latency (s)")
    plt.show()


def plot(df, tech, metric):
    print(df.head())

    # plt.figure(figsize=(10, 10))
    sns.scatterplot(x="delay", y=str(metric), palette='muted', data=df)

    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("Latency (s)")
    title = tech + " relay_" + str(relay[index_relay])
    plt.title(title)
    plt.show()


def smooth_interpolation(df, tech, metric):
    sns.lmplot(x='delay', y=str(metric), data=df, ci=None, order=5, height=10, aspect=2, truncate=True,
               scatter_kws={"s": 0.5})
    plt.title("Smooted line plot - " + str(tech))
    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("Latency (s)")

    plt.show()

    sns.lmplot(x='delay', y=str(metric), data=df, ci=95, order=5, height=10, aspect=2, truncate=True, legend_out=True,
               scatter_kws={"s": 5})
    plt.title("Smooted line plot with CI- " + str(tech))
    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("Latency (s)")


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


def get_list_and_return_df(dataset, tech, metric):
    pxs = []
    pys = []
    for x in delay:
        print("Delay: ", x)
        for run in dataset[x]:
            y = dataset[x][run]
            for e in y:
                pxs.append(x)
                pys.append(e)

    data = {'delay': pxs, str(metric): pys}
    df = pd.DataFrame(data)
    return df


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

    df = get_list_and_return_df(my_list_ble, 'ble', 'latency')
    define_base_plot()
    # plot(df, "BLE", 'latency')
    smooth_interpolation(df, 'ble', 'latency')


def plot_2(df):
    sns.lmplot(x="delay", y="pdr", palette='muted', hue='type', fit_reg=False, data=df)

    plt.xticks(delay)
    plt.xlabel("Time between packet sent (ms)")
    plt.ylabel("PDR")
    title = "PDR" + " relay_" + str(relay[index_relay])
    plt.title(title)
    plt.show()


# TODO plot latency, PDR e goodput
def main2():
    pxs = []
    pys = []
    pzs = []
    margin_error = []

    global index_relay
    for index_relay in relay:
        source_path_2 = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/delay_XXX_*.json"
        list_of_files = glob.glob(source_path_2)
        for name in list_of_files:
            data = my.open_file_and_return_data(name)
            pzs.append(('relay_' + str(data['_command']['relay'])))
            pxs.append(data['_command']['delay'])
            pys.append(data['summary']['statistic_']['total']['latency']['mean'])
            margin_error.append(data['summary']['statistic_']['total']['latency']['m_e'])

    dataframe = {'delay': pxs, 'latency': pys, 'type': pzs, 'm_e': margin_error}
    df = pd.DataFrame(dataframe)
    print(df.head())
    #plot_boxplot(df)

    # define_base_plot()
    plot_with_error(df, 'type', 'latency')
    # plot_2(df)


if __name__ == "__main__":
    try:
        main2()
    except Exception as e:
        print(e)
    sys.exit()
