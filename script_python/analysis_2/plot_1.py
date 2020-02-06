import sys
import emilio_function as my
import matplotlib.pyplot as plt

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
approach = 1  # 0 -> normal, 1-> cuts
index_relay = 2  # 0..2
# index_delay = 8  # 0..8
################################################################
relay = [0, 1, 2]
# delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
delay = [50, 100, 150, 200, 250, 500, 1000]
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/cuts/"


def plot(dataset, tech):
    pxs = []
    pys = []
    for index in delay:
        print("index: {}".format(index))
        for run in dataset[index]:
            x = index
            y = dataset[x][run]
            for e in y:
                pxs.append(x)
                pys.append(e)
            print("run: {}".format(run))

    if tech == 'BLE':
        plt.scatter(pxs, pys, color="blue", s=5)
    else:
        plt.scatter(pxs, pys, color="green", s=5)
    text = tech + " relay_" + str(index_relay)
    plt.title(text)
    plt.xlabel('x - Frequencies')
    plt.ylabel('y - latency [seconds]')
    plt.xticks(delay, delay)

    path_graph = outcome_path + "_" + str(tech) + "_relay_" + str(relay[index_relay]) + "__latencies.png"
    print("\x1b[1;32;40m Saving Graph {}: {}\x1b[0m".format(tech, path_graph))
    plt.savefig(path_graph)
    plt.show()


def get_all_value(dataset):
    l_ble = list()
    l_wifi = list()
    for index, value in dataset.items():
        for v in value:
            if 'ble' in v or 'wifi' in v:
                if 'ble' in v:
                    l_ble.append(v['ble']['latency'])
                if 'wifi' in v:
                    l_wifi.append(v['wifi']['latency'])
    return l_ble, l_wifi


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


def main_cut():
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
    plot(my_list_wifi, "WiFi")


def main():
    my_list_ble = dict()
    my_list_wifi = dict()
    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/delay_" + str(
            delay[index_delay]) + "/*_analysis.json"
        files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
        my_list_ble[delay[index_delay]] = dict()
        my_list_wifi[delay[index_delay]] = dict()
        i = 1
        for item in files:
            data = my.open_file_and_return_data(path=item)['_mex']
            l_ble, l_wifi = get_all_value(dataset=data)
            my_list_ble[delay[index_delay]][i] = l_ble
            my_list_wifi[delay[index_delay]][i] = l_wifi
            i += 1
    plot(my_list_ble, "BLE")
    plot(my_list_wifi, "WiFi")


if __name__ == "__main__":
    try:
        if approach:
            main_cut()
        else:
            main()
    except Exception as e:
        print(e)
    sys.exit()
