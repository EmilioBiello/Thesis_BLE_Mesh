import emilio_function as my
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas.io.json import json_normalize
import glob
import datetime as dt
import time

path_media = "/media/emilio/BLE/"

topic = "2"  # Number of Relay
delay = "delay_500"
start_time = "11_54"
end_time = "13_50"  # ! minuto n più
path_analysis = path_media + "json_file/test_2019_12_14/*_analysis.json"

title = "Rilevazioni [relay: " + topic + " " + delay + " ms]"
file_name = "json_file/analysis_" + topic + "_Relay/" + delay + ".json"

my_dictionary = dict()
my_mean = list()
my_lower_bound = list()
my_upper_bound = list()
all_measurement = list()
packets_lost = list()


def detect_outlier(data_1):
    outliers = list()
    threshold = 3
    mean_1 = np.mean(data_1)
    std_1 = np.std(data_1)

    for y in data_1:
        z_score = (y - mean_1) / std_1
        if np.abs(z_score) > threshold:
            outliers.append(y)

    print("Mean: {} --- STD: {}".format(mean_1, std_1))
    return outliers


# IRQ: Interquartile Range
def IQR(dataset):
    # Sorting Dataset
    sorted(dataset)

    # Finding 1th Quartile and 3rd Quartile
    q1, q3 = np.percentile(dataset, [25, 75])

    # Finding IQR which is the difference between 3rd and 1st Quartile
    iqr = q3 - q1

    # Finding Lower and upper bound
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    return lower_bound, upper_bound, q1, q3, iqr


def statistcs(dataset):
    std_1 = np.std(dataset)
    mean_1 = np.mean(dataset)
    l_bound, u_bound, q1, q3, iqr = IQR(dataset)
    return mean_1, std_1, l_bound, u_bound, q1, q3, iqr


def outlier_element(data, l_bound_1, u_bound_1, l_bound_2, u_bound_2):
    valid_data_1 = 0
    outlier_1 = 0
    valid_data_2 = 0
    outlier_2 = 0
    for k, v in data['second_analysis'].items():
        if l_bound_1 <= v['difference'] <= u_bound_1:
            valid_data_1 += 1
        else:
            outlier_1 += 1

        if l_bound_2 <= v['latency'] <= u_bound_2:
            valid_data_2 += 1
        else:
            outlier_2 += 1

    return valid_data_1, outlier_1, valid_data_2, outlier_2


def statistcs_diff_latency(data, index, name):
    list_diff = list()
    list_latency = list()
    for key, value in data['second_analysis'].items():
        list_diff.append(value['difference'])
        list_latency.append(value['latency'])
        all_measurement.append(value['latency'])
        send_time_obj = dt.datetime.strptime(value['send_time'], '%Y-%m-%d %H:%M:%S.%f')
        receive_time_obj = dt.datetime.strptime(value['status_time'], '%Y-%m-%d %H:%M:%S.%f')
        diff = receive_time_obj - send_time_obj
        if diff.total_seconds() != value['difference']:
            print("\x1b[1;31;40m Value Difference: {} \x1b[0m {} - {}".format(key, diff, value['difference']))

        if diff.total_seconds() < 0:
            print("\x1b[1;31;40m Negative Value: {} \x1b[0m - {}".format(key, value))

    mean_1, std_1, l_b_1, u_b_1, q1_1, q3_1, iqr_1 = statistcs(dataset=list_diff)
    mean_2, std_2, l_b_2, u_b_2, q1_2, q3_2, iqr_2 = statistcs(dataset=list_latency)
    e_1, o_1, e_2, o_2 = outlier_element(data=data, l_bound_1=l_b_1, u_bound_1=u_b_1, l_bound_2=l_b_2, u_bound_2=u_b_2)

    # Packet Delivery Ratio
    packet_delivery_ratio = float(int(data["analysis"]["packet_received"]) / int(data["_command"]["n_mex"]))
    goodput = int(1000 / int(data["_command"]["delay"]) * 2)  # 2 byte di dati utili
    index = "rilevazione_" + str(index)
    # RTT: Round Trip Time
    my_dictionary[index] = {'analysis': data["analysis"], 'file_name': name,
                            'statistics_RTT': {
                                'media': mean_1,
                                'std': std_1,
                                'lower_bound': l_b_1,
                                'upper_bound': u_b_1,
                                'outlier_#': o_1,
                                'valid_data': e_1,
                                '1th_quartile': q1_1,
                                '3rd_quartile': q3_1,
                                'IQR': iqr_1,  # range Inter Quartile
                                'min_value': np.min(list_diff),
                                'max_value': np.max(list_diff)
                            },
                            'statistics_latency': {
                                'media': mean_2,
                                'std': std_2,
                                'lower_bound': l_b_2,
                                'upper_bound': u_b_2,
                                'outlier_#': o_2,
                                'valid_data': e_2,
                                '1th_quartile': q1_2,
                                '3rd_quartile': q3_2,
                                'IQR': iqr_2,  # range Inter Quartile
                                'min_value': np.min(list_latency),
                                'max_value': np.max(list_latency)
                            },
                            'graph': {
                                'PDR': packet_delivery_ratio,  # Pacchetti Ricevuti / Pacchetti Inviati
                                'goodput': goodput,  # bytes/s
                                'latency_mean': mean_2
                            }}
    my_mean.append(mean_2)
    my_lower_bound.append(l_b_2)
    my_upper_bound.append(u_b_2)
    packets_lost.append(data["analysis"]["packet_lost"])


def my_outlier(index, data, name):
    index = index + 1
    statistcs_diff_latency(data=data, index=index, name=name)
    if index == 1:
        my_dictionary["_command"] = data["_command"]


def summary():
    mean = np.mean(my_mean)
    lower_bound = np.mean(my_lower_bound)
    upper_bound = np.mean(my_upper_bound)
    losts = np.mean(packets_lost)
    perc_lost = (losts * 100) / my_dictionary["_command"]["n_mex"]

    mean_1, std_1, l_b_1, u_b_1, q1_1, q3_1, iqr_1 = statistcs(dataset=all_measurement)
    print("--- SUMMARY ---")
    print("Media: {}, lower_bound: {}, upper_bound: {}".format(mean, lower_bound, upper_bound))
    print(
        "Media: {} -- STD: {} -- lower_bound: {}, upper_bound: {} -- 1th Quartile: {}, 3rd Quartile: {}, IQR: {}".format(
            mean_1, std_1, l_b_1, u_b_1, q1_1, q3_1, iqr_1))

    my_dictionary['summary'] = {'total': {'media': mean_1, 'std': std_1, 'lower_bound': l_b_1, 'upper_bound': u_b_1,
                                          '1th_quartile': q1_1, '3rd_quartile': q3_1, 'IQR': iqr_1, },
                                'means': {'media': mean, 'lower_bound': lower_bound, 'upper_bound': upper_bound,
                                          'packet_lost': losts, 'percenutale_lost': perc_lost}}


def is_time_between(begin_time, final_time, check_time):
    if begin_time.time() <= check_time.time() <= final_time.time():
        return True
    else:
        return False


def analysis_5_file():
    list_of_files = glob.glob(path_analysis)
    list_of_files.sort()

    start_time_obj = dt.datetime.strptime(start_time, "%H_%M")
    end_time_obj = dt.datetime.strptime(end_time, "%H_%M")

    files = list()
    for item in list_of_files:
        time_ = item.split('/')[6].split('-')[1][:8]
        time_obj = dt.datetime.strptime(time_, "%H_%M_%S")
        if is_time_between(begin_time=start_time_obj, final_time=end_time_obj, check_time=time_obj):
            files.append(item)

    for i in files:
        print(i)
    print("Number: {}".format(len(files)))
    x = input("OK o EXCEPT [1 - 0]\n")
    if x == '0':
        raise Exception('\x1b[1;31;40m' + ' Errore list files ' + '\x1b[0m')
    elif x != '1':
        raise Exception('\x1b[1;31;40m' + ' Errore input. Accept only 0 - 1 ' + '\x1b[0m')

    return files


def get_data(path):
    print("Open file: {}".format(path))
    data = my.open_file_and_return_data(code=0, path=path)
    return data


def plot_mean():
    x = np.arange(1, len(my_mean) + 1, 1).tolist()
    plt.scatter(x, my_mean, label="means", color="green", s=20)

    plt.scatter(x, my_upper_bound, label="upper_bound", color="red", s=20)

    plt.scatter(x, my_lower_bound, label="lower_bound", color="blue", s=20)

    plt.xlim(0, 6)
    plt.xlabel('x - tests')
    plt.ylabel('y - latency [seconds]')

    plt.title(title)
    plt.legend()

    # plt.show()
    name = path_media + file_name[:-5] + '.png'
    print(name)
    plt.savefig(name)


def plot_points(data, index):
    x = list()
    y = list()
    for key, value in data['second_analysis'].items():
        x.append(int(key))
        y.append(value['latency'])

    # plt.plot(x, y, color='green', linestyle='dashed', linewidth=1, marker='o', markerfacecolor='blue', markersize=6)
    plt.scatter(x, y, label="stars", color="green", marker="*", s=3)

    # LABEL x and y axis
    plt.ylim(0, max(y))
    plt.xlim(1, len(x))

    plt.xlabel('x - axis')
    plt.ylabel('y - axis')

    title = "Rilevazione_" + str(index)
    plt.title(title)
    plt.legend()

    plt.show()


def main():
    files = analysis_5_file()

    for i in range(len(files)):
        name = files[i]
        data = get_data(name)
        # plot_points(data, 1)
        my_outlier(i, data, name)
        print("--------------")
        time.sleep(1)
    plot_mean()
    summary()
    my.print_data_as_json(my_dictionary)
    my.save_json_data_elegant(path=file_name, data=my_dictionary)


def main2():
    path = "/media/emilio/BLE/json_file/test_2019_12_12/test_19_12_12-14_35_24_analysis.json"
    data = get_data(path=path)
    my_outlier(1, data, path)
    my.print_data_as_json(my_dictionary)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
