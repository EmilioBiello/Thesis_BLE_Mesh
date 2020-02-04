import sys
import emilio_function as my
import matplotlib.pyplot as plt

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_topic = 0  # 0..2
# index_delay = 8  # 0..8
################################################################
topic = [0, 1, 2]
delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]


def plot(dataset, type):
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

    if type == 'BLE':
        plt.scatter(pxs, pys, color="blue", s=5)
    else:
        plt.scatter(pxs, pys, color="green", s=5)
    plt.title(type)
    plt.xlabel('x - packets')
    plt.ylabel('y - latency [seconds]')
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


def main():
    my_list_ble = dict()
    my_list_wifi = dict()
    for index_delay in range(len(delay)):
        source_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/delay_" + str(
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
        main()
    except Exception as e:
        print(e)
    sys.exit()
