import emilio_function as my
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas.io.json import json_normalize
import glob
import datetime as dt
import time
import math

# TODO cambiare index, runs e topic
index_my_delay = 0  # indice di my_delay [0,1,2,3,4,5,6,7,8]
runs = 1  # 1,0 Eseguire prima 1 e poi 0
topic = "0"  # Number of Relay [0,1,2]
packet_not_sent_as_lost = True  # solo per 50 e 75 ms
my_delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]  # 50, 75, 100, 125, 150, 200, 250, 500, 1000
analysis = "2"  # "2" or "0"
# path_analysis = my.path_media + "json_file/test_2019_12_29/*_analysis.json"

# s_time_0 = ["9_30", "14_34", "17_02", "16_27", "17_05"]
# s_time_1 = ["9_31", "10_33", "16_08", "14_44", "15_22"]
# s_time_2 = ["9_20", "10_00", "11_10", "11_54", "17_55"]
#
# e_time_0 = ["14_30", "15_30", "17_40", "17_00", "17_40"]
# e_time_1 = ["10_30", "11_30", "17_00", "15_15", "16_00"]
# e_time_2 = ["9_55", "11_00", "11_40", "12_30", "19_00"]

s_time_0 = ["18_15", "19_32", "18_59", "11_57", "10_19", "10_53", "11_26", "16_27", "17_05"]
s_time_1 = ["19_24", "18_34", "20_06", "21_32", "22_14", "16_43", "16_09", "14_44", "15_22"]
s_time_2 = ["13_42", "14_32", "15_11", "9_31", "10_36", "16_42", "18_59", "11_54", "12_30"]

e_time_0 = ["18_52", "19_59", "19_26", "12_25", "10_48", "11_21", "11_53", "16_56", "17_35"]
e_time_1 = ["20_00", "19_10", "21_15", "22_08", "22_45", "17_13", "16_37", "15_13", "15_54"]
e_time_2 = ["14_24", "15_04", "15_46", "10_27", "11_10", "18_47", "19_25", "12_23", "13_04"]

# ["50", "75", "100", "125", "150", "200", "250", "500", "1000"]

if analysis == "2":  # prevede l'analisi solo di 5 minuti e non 6 minuti
    path_analysis = my.path_media + "json_file/test_relay_" + topic + "/*_analysis_2.json"
    name_key_data = 'couples'
    name_key_analysis = 'analysis_value'
elif analysis == "0":  # prevede l'analisi di 6 minuti [tutta la prova]
    path_analysis = my.path_media + "json_file/test_relay_" + topic + "/*_analysis.json"
    name_key_data = 'second_analysis'
    name_key_analysis = 'analysis'
else:
    raise Exception("Errore type analysis file")

delay = "delay_" + str(my_delay[index_my_delay])
start_time = "9_30"
end_time = "14_30"  # ! minuto n più

if topic == "0":
    start_time = s_time_0[index_my_delay]
    end_time = e_time_0[index_my_delay]
elif topic == "1":
    start_time = s_time_1[index_my_delay]
    end_time = e_time_1[index_my_delay]
elif topic == "2":
    start_time = s_time_2[index_my_delay]
    end_time = e_time_2[index_my_delay]

title = "Rilevazioni [relay: " + topic + " " + delay + " ms]"
file_name = "json_file/analysis_" + topic + "_Relay/" + delay + ".json"
file_name_img_runs = my.path_media + "json_file/analysis_" + topic + "_Relay/runs_" + delay + ".png"
file_name_img_means = my.path_media + "json_file/analysis_" + topic + "_Relay/means_" + delay + ".png"

my_dictionary = dict()
my_mean = list()
my_std = list()
margini_errore = list()
my_min = list()
my_max = list()
my_lower_bound = list()
my_upper_bound = list()
all_measurement = list()
packets_lost = list()
packets_received = list()
packets_sent = list()
packets_not_sent = list()
tempo_esperimento = list()
goodput_list = list()
packed_delivery_ratio_list = list()


def intervalli_di_confidenza(mean, std, sample_size):
    # Intervallo di Confidenza al 95%
    # FORMULA: Za/2*q/sqrt(n)
    quantile = 1.96
    margine_errore = quantile * (std / np.sqrt(sample_size))
    value_1 = mean - margine_errore
    value_2 = mean + margine_errore

    return margine_errore, value_1, value_2


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
    mean = np.mean(dataset)
    std = np.std(dataset)
    l_bound, u_bound, q1, q3, iqr = IQR(dataset)
    margine_errore, min_, max_ = intervalli_di_confidenza(mean, std, len(dataset))
    return mean, std, l_bound, u_bound, q1, q3, iqr, margine_errore, min_, max_


def outlier_element(data, l_bound_1, u_bound_1):
    valid_data_1 = 0
    outlier_1 = 0
    list_valid_value = list()
    for k, v in data[str(name_key_data)].items():
        if l_bound_1 <= v['latency'] <= u_bound_1:
            valid_data_1 += 1
            list_valid_value.append(v['latency'])
        else:
            outlier_1 += 1

    std_2 = np.std(list_valid_value)
    mean_2 = np.mean(list_valid_value)
    return valid_data_1, outlier_1, std_2, mean_2


def config_list(data):
    list_latency = list()
    for key, value in data[str(name_key_data)].items():
        list_latency.append(value['latency'])
        all_measurement.append(value['latency'])
        send_time_obj = dt.datetime.strptime(value['send_time'], '%Y-%m-%d %H:%M:%S.%f')
        receive_time_obj = dt.datetime.strptime(value['status_time'], '%Y-%m-%d %H:%M:%S.%f')
        diff = receive_time_obj - send_time_obj
        if diff.total_seconds() != value['difference']:
            print("\x1b[1;31;40m Value Difference: {} \x1b[0m {} - {}".format(key, diff, value['difference']))

        if diff.total_seconds() < 0:
            print("\x1b[1;31;40m Negative Value: {} \x1b[0m - {}".format(key, value))
    return list_latency


def save_statistics(data, index, name):
    index = "rilevazione_" + str(index)
    list_latency = config_list(data=data)
    mean, std, l_b_1, u_b_1, q1_1, q3_1, iqr_1, margine_errore, min_, max_ = statistcs(dataset=list_latency)

    time_test = data[name_key_analysis]["test_time"]
    # Packet Delivery Ratio --> PDR
    if analysis == "2":
        packet_delivery_ratio = float(
            int(data[name_key_analysis]["ricevuti"]) / int(data[name_key_analysis]["inviati"]))
        goodput = (data[name_key_analysis]["ricevuti"] * 2) / time_test  # 2 byte di dati utili
    else:
        packet_delivery_ratio = float(
            int(data[name_key_analysis]["packet_received"]) / int(data[name_key_analysis]["packet_sent"]))
        goodput = (data[name_key_analysis]["packet_received"] * 2) / time_test  # 2 byte di dati utili

    # RTT: Round Trip Time
    my_dictionary[index] = {'analysis': data[name_key_analysis], 'file_name': name,
                            'statistics_latency': {
                                'media': mean,
                                'std': std,
                                'size_sample': len(list_latency),
                                'InterQuartile_Range': {'lower_bound': l_b_1,
                                                        'upper_bound': u_b_1,
                                                        '1th_quartile': q1_1,
                                                        '3rd_quartile': q3_1,
                                                        'IQR': iqr_1},
                                'IC': {'margine_errore': margine_errore, 'min_': min_, 'max': max_},
                                'min_value': np.min(list_latency),
                                'max_value': np.max(list_latency),

                            },
                            'graph': {
                                'PDR': packet_delivery_ratio,  # Pacchetti Ricevuti / Pacchetti Inviati
                                'goodput': goodput,  # bytes/s
                                'latency_mean': mean,
                                'latency_min': min_,
                                'latency_max': max_
                            }}
    my_mean.append(mean)
    my_std.append(std)

    my_lower_bound.append(l_b_1)
    my_upper_bound.append(u_b_1)

    margini_errore.append(margine_errore)
    my_min.append(min_)
    my_max.append(max_)

    if analysis == "2":
        packets_sent.append(data[name_key_analysis]["inviati"])
        packets_not_sent.append(data[name_key_analysis]["errore"])
        packets_lost.append(data[name_key_analysis]["persi_e_error"])
        packets_received.append(data[name_key_analysis]["ricevuti"])
    elif analysis == "0":
        packets_sent.append(data[name_key_analysis]["packet_sent"])
        packets_not_sent.append(data[name_key_analysis]["packet_not_sent"])
        packets_lost.append(data[name_key_analysis]["packet_lost"])
        packets_received.append(data[name_key_analysis]["packet_received"])

    tempo_esperimento.append(data[name_key_analysis]["test_time"])

    goodput_list.append(goodput)
    packed_delivery_ratio_list.append(packet_delivery_ratio)


def manage_statistics(index, data, name):
    index = index + 1
    save_statistics(data=data, index=index, name=name)
    if index == 1:
        my_dictionary["_command"] = data["_command"]


def summary():
    mean = np.mean(my_mean)  # media generale
    std = np.mean(my_std)
    margine_err_medio = np.mean(margini_errore)
    min_ = np.mean(my_min)
    max_ = np.mean(my_max)

    # lower_bound = np.mean(my_lower_bound)
    # upper_bound = np.mean(my_upper_bound)

    packets_sent_mean = np.mean(packets_sent)
    packets_not_sent_mean = np.mean(packets_not_sent)
    packets_lost_mean = np.mean(packets_lost)
    packets_received_mean = np.mean(packets_received)

    packet_delivery_ratio_mean = np.mean(packed_delivery_ratio_list)
    goodput_mean = np.mean(goodput_list)
    esperimento_mean = np.mean(tempo_esperimento)

    if analysis == "2":
        total_mex_five_min = [6000, 4000, 3000, 2400, 2000, 1500, 1200, 600, 300]
        sent = total_mex_five_min[index_my_delay]
    else:
        # total_mex_six_min = [7200, 4800, 3600, 2880, 2400, 1800, 1440, 720, 360]
        # sent = total_mex_six_min[index_my_delay]
        sent = my_dictionary["_command"]["n_mex"]

    mean_1, std_1, l_b_1, u_b_1, q1_1, q3_1, iqr_1, margine_errore_1, min_1, max_1 = statistcs(dataset=all_measurement)
    print("--- SUMMARY ---")
    print("Media: {} -- STD: {} -- [{} - {}] margin_err: {}".format(mean, std, min_, max_, margine_err_medio))
    print("Media: {} -- STD: {} -- [{} - {}] margin_err: {}".format(mean_1, std_1, min_1, max_1, margine_errore_1))

    print("Packed Delivery Ratio: {} \nMedia packed received: {} \nMean time test: {} \nGOODPUT: {}".format(
        packet_delivery_ratio_mean, packets_received_mean, esperimento_mean, goodput_mean))

    my_dictionary['summary'] = {'total': {'media': mean_1,
                                          'std': std_1,
                                          'IC': {'min_': min_1,
                                                 'max_': max_1,
                                                 'margine_errore': margine_errore_1}},
                                'means': {'latency_mean': mean,
                                          'latency_std': std,
                                          'IC': {'min_': min_,
                                                 'max_': max_,
                                                 'margine_errore': margine_err_medio},
                                          'packets': {
                                              'packet_sent': packets_sent_mean,
                                              'packet_not_sent': packets_not_sent_mean,
                                              'packet_lost': packets_lost_mean,
                                              'packet_received': packets_received_mean},
                                          'mean_test_time': esperimento_mean},
                                'graph': {
                                    'PDR': packet_delivery_ratio_mean,  # Pacchetti Ricevuti / Pacchetti Inviati
                                    'goodput': goodput_mean,  # bytes/s
                                    'latency_mean': mean,
                                    'latency_min': min_, 'latency_max': max_, 'latency_err_m': margine_err_medio
                                }}


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
    # TODO uncomment
    # x = input("OK o EXCEPT [1 - 0]\n")
    x = '1'
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
    plt.scatter(x, my_mean, label="means", color="green", s=30)
    plt.scatter(x, my_min, label="upper_bound", color="red", s=30)
    plt.scatter(x, my_max, label="lower_bound", color="blue", s=30)

    plt.scatter(6, np.mean(my_mean), color="darkgreen", s=35, marker="*")
    plt.scatter(6, np.mean(my_min), color="darkred", s=35, marker="*")
    plt.scatter(6, np.mean(my_max), color="darkblue", s=35, marker="*")

    plt.xlim(0, 7)
    plt.xlabel('x - tests')
    plt.ylabel('y - latency [seconds]')

    plt.title(title)
    plt.legend()
    plt.grid(True)

    print(file_name_img_means)
    plt.savefig(file_name_img_means)
    plt.show()


def plot_points(data, index):
    x = list()
    latency = list()
    if index == 0:
        color = "green"
    elif index == 1:
        color = "red"
    elif index == 2:
        color = "blue"
    elif index == 3:
        color = "orange"
    elif index == 4:
        color = "lime"
    else:
        color = "black"

    for key, value in data[str(name_key_data)].items():
        x.append(int(key))
        latency.append(value['latency'])

    text = "rilevazione " + str(index + 1)
    plt.scatter(x, latency, label=text, color=color, marker="*", s=5)

    # LABEL x and y axis
    # plt.ylim(0, max(y))
    # plt.xlim(1, len(x))

    plt.xlabel('x - packets')
    plt.ylabel('y - latency [seconds]')
    # plt.show()


def combine_two_plot():
    pdr = list()
    goodput = list()
    x = list()
    for i in range(1, 5):
        text = 'rilevazione_' + str(i)
        pdr.append(my_dictionary[text]['graph']['PDR'])
        goodput.append(my_dictionary[text]['graph']['goodput'])
        x.append(i)

    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('rilevazioni')
    ax1.set_ylabel('Packet Delivery Ratio', color=color)
    ax1.scatter(x, pdr, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Goodput (byte/s)', color=color)  # we already handled the x-label with ax1
    ax2.scatter(x, goodput, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()


def manage_plot():
    title_str = "Relay_" + str(topic) + " delay_" + str(my_delay[index_my_delay]) + "ms"
    plt.title(title_str)
    plt.legend()

    print("Saving png: {}".format(file_name_img_runs))
    plt.savefig(file_name_img_runs)
    plt.show()


def main():
    print("\x1b[1;34;40m delay:{d} [RELAY: {r}]\x1b[0m".format(d=my_delay[index_my_delay], r=topic))
    files = analysis_5_file()

    for i in range(len(files)):
        name = files[i]
        data = get_data(name)
        if data['_command']['delay'] != my_delay[index_my_delay]:
            raise Exception("Errore delay: ", data['_command']['delay'])
        print("\x1b[1;34;40m addr:{a}, delay:{d} n_mex:{n} [RELAY: {r}]\x1b[0m".format(a=data['_command']['addr'],
                                                                                       d=data['_command']['delay'],
                                                                                       n=data['_command']['n_mex'],
                                                                                       r=topic))
        manage_statistics(i, data, name)
        if runs:
            plot_points(data, i)
        print("--------------")
        time.sleep(1)

    summary()
    if runs:
        my.save_json_data_elegant(path=file_name, data=my_dictionary)
        manage_plot()
    else:
        my.print_data_as_json(my_dictionary)
        plot_mean()


def main2():
    path = "/media/emilio/BLE/json_file/test_relay_0/test_19_12_23-11_52_19_analysis.json"
    data = get_data(path=path)
    print("\x1b[1;34;40m addr:{a}, delay:{d} n_mex:{n} [RELAY: {r}]\x1b[0m".format(a=data['_command']['addr'],
                                                                                   d=data['_command']['delay'],
                                                                                   n=data['_command']['n_mex'],
                                                                                   r=topic))
    list_latency = config_list(data=data)
    mean = np.mean(list_latency)
    std = np.std(list_latency)
    margine_errore, min_, max_ = intervalli_di_confidenza(mean=mean, std=std, sample_size=len(list_latency))
    print("[{m2} - {m} - {m3}]\n ---std: {s}  --- margine d'errore : {m1}".format(m2=min_, m=mean, m3=max_, s=std,
                                                                                  m1=margine_errore))
    # my.print_data_as_json(my_dictionary)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
