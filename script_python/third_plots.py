import emilio_function as my
import numpy as np
import matplotlib.pyplot as plt
import glob
import time
import xlsxwriter

# TODO main() cambiare solo topic
topic = 0
path_analysis = my.path_media + "json_file/analysis_" + str(topic) + "_Relay/*.json"
delays = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
# delays = [50, 75, 100, 125, 150, 200, 250]
if len(delays) == 7:
    name_dir = "plot_"
elif len(delays) == 9:
    name_dir = "plot_complete"
else:
    name_dir = "plot_xxx"


def single_delay(data, graph, analysis):
    label = data["_command"]["delay"]

    graph[label] = {
        'rilevazione_1': data['rilevazione_1']['graph'],
        'rilevazione_2': data['rilevazione_2']['graph'],
        'rilevazione_3': data['rilevazione_3']['graph'],
        'rilevazione_4': data['rilevazione_4']['graph'],
        'rilevazione_5': data['rilevazione_5']['graph']
    }
    analysis[label] = {
        'rilevazione_1': data['rilevazione_1']['analysis'],
        'rilevazione_2': data['rilevazione_2']['analysis'],
        'rilevazione_3': data['rilevazione_3']['analysis'],
        'rilevazione_4': data['rilevazione_4']['analysis'],
        'rilevazione_5': data['rilevazione_5']['analysis']
    }
    return graph, analysis


def set_packet_info_list(my_analysis, delay):
    lost = list()
    not_sent = list()
    received = list()
    sent = list()
    for i in range(1, 6):
        text = 'rilevazione_' + str(i)
        sent.append(my_analysis[delay][text]['packet_sent'])
        not_sent.append(my_analysis[delay][text]['packet_not_sent'])
        lost.append(my_analysis[delay][text]['packet_lost'])
        received.append(my_analysis[delay][text]['packet_received'])
        # if 'packet_not_sent' in my_analysis[delay][text]:
        #     not_sent.append(my_analysis[delay][text]['packet_not_sent'])
        # else:
        #     not_sent.append(0)
    return sent, not_sent, lost, received


def set_list(my_dictionary, delay):
    latencies = list()
    goodputs = list()
    pdr = list()
    min_ = list()
    max_ = list()
    for i in range(1, 6):
        text = 'rilevazione_' + str(i)
        latencies.append(my_dictionary[delay][text]['latency_mean'])
        goodputs.append(my_dictionary[delay][text]['goodput'])
        pdr.append(my_dictionary[delay][text]['PDR'])
        min_.append(my_dictionary[delay][text]['latency_min'])
        max_.append(my_dictionary[delay][text]['latency_max'])
    return latencies, goodputs, pdr, min_, max_


def save_xlsx_relay(latencies, goodputs, pdrs, min_, max_, packets, delays):
    path_directory = my.path_media + "json_file/" + name_dir + "/"
    directory = my.define_directory(directory=path_directory)
    name = directory + "Relay_" + str(topic) + ".xlsx"
    workbook = xlsxwriter.Workbook(filename=name)

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    bold.set_center_across()
    cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    cell_format.set_center_across()

    worksheet = workbook.add_worksheet(name="Relay_" + str(topic))

    row = 1
    col = 0
    for i in range(0, 5):
        title = "Rilevazione_" + str(i + 1)
        worksheet.write(row, col, title, cell_format)
        row = row + 1
        worksheet.write(row, col, "Delay", bold)
        worksheet.write(row, col + 1, "PDR", bold)
        worksheet.write(row, col + 2, "Goodput", bold)
        worksheet.write(row, col + 3, "Latency_mean", bold)
        worksheet.write(row, col + 4, "Latency_min", bold)
        worksheet.write(row, col + 5, "Latency_max", bold)

        worksheet.write(row, col + 7, "Sent", bold)
        worksheet.write(row, col + 8, "Not_Sent", bold)
        worksheet.write(row, col + 9, "Lost", bold)
        worksheet.write(row, col + 10, "Received", bold)

        row = row + 1
        col = 0
        for delay in delays:
            arg = str(delay) + " ms"
            worksheet.write(row, col, arg)
            worksheet.write(row, col + 1, pdrs[delay][i])
            worksheet.write(row, col + 2, goodputs[delay][i])
            worksheet.write(row, col + 3, latencies[delay][i])
            worksheet.write(row, col + 4, min_[delay][i])
            worksheet.write(row, col + 5, max_[delay][i])

            worksheet.write(row, col + 7, packets[delay]['sent'][i])
            worksheet.write(row, col + 8, packets[delay]['not_sent'][i])
            worksheet.write(row, col + 9, packets[delay]['lost'][i])
            worksheet.write(row, col + 10, packets[delay]['received'][i])
            row = row + 1
        row = row + 1

    print("Saving xlsx: {}".format(name))
    workbook.close()


def get_data(path):
    print("Open file: {}".format(path))
    data = my.open_file_and_return_data(code=0, path=path)
    return data


def main():
    list_of_files = glob.glob(path_analysis)

    my_dictionary = dict()
    my_analysis = dict()
    for name in sorted(list_of_files):
        data = get_data(path=name)
        my_dictionary, my_analysis = single_delay(data, my_dictionary, my_analysis)
        time.sleep(0.1)

    latencies = dict()
    goodputs = dict()
    pdrs = dict()
    mins_ = dict()
    maxs_ = dict()
    packets = dict()
    for item in delays:
        latency, goodput, pdr, min_, max_ = set_list(my_dictionary=my_dictionary, delay=item)
        latencies[item] = latency
        goodputs[item] = goodput
        pdrs[item] = pdr
        mins_[item] = min_
        maxs_[item] = max_

        packets[item] = {'sent': [], 'not_sent': [], 'lost': [], 'received': []}
        packets[item]['sent'], packets[item]['not_sent'], packets[item]['lost'], packets[item][
            'received'] = set_packet_info_list(my_analysis, item)

    save_xlsx_relay(latencies, goodputs, pdrs, mins_, maxs_, packets, delays)


def plot_latency(data_l, data_l_min, data_l_max):
    plot(data_l_min, '', 'Latency_min', '[seconds]', name_dir)
    plot(data_l_max, '', 'Latency_max', '[seconds]', name_dir)
    plot(data_l, 'mean', 'Latency', '[seconds]', name_dir)


def plot(data, delay, label_, label_2, plot_dir):
    x_label = ""
    for i in range(0, 3):
        if i == 0:
            color = "red"
            color_min = "lightcoral"
            color_max = "darkred"
        elif i == 1:
            color = "green"
            color_min = "lightgreen"
            color_max = "darkgreen"
        elif i == 2:
            color = "blue"
            color_min = "lightblue"
            color_max = "darkblue"
        else:
            color = "black"
            color_min = "black"
            color_max = "black"

        label_1 = str(i) + ' relay'
        dati = list()
        x = list()
        x_label = 'x - delay ms'

        for key, value in data[i].items():
            x.append(key)
            dati.append(value)

        if label_ == "Latency_min":
            plt.scatter(x, dati, color=color_min, s=20, marker="*")
        elif label_ == "Latency_max":
            plt.scatter(x, dati, color=color_max, s=20, marker="*")
        else:
            plt.scatter(x, dati, label=label_1, color=color, s=20)

    if label_ == "Latency":
        if delay == "mean":
            delay = ""
        text = label_ + " " + str(delay) + " ms "
    else:
        text = label_ + " " + str(delay)
    y_label = "y - " + label_ + label_2

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if label_ != "Latency_min" and label_ != "Latency_max":
        plt.title(text)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        name = my.path_media + "json_file/" + plot_dir + "/" + str(delay) + "_" + label_ + '.png'
        print("Saving png: {}".format(name))
        plt.savefig(name)
        plt.show()
    else:
        print("Plot ", label_)


def main3():
    my_dict = dict()
    my_analysis = dict()

    for delay in delays:
        path_0 = my.path_media + "json_file/analysis_0_Relay/delay_" + str(delay) + ".json"
        path_1 = my.path_media + "json_file/analysis_1_Relay/delay_" + str(delay) + ".json"
        path_2 = my.path_media + "json_file/analysis_2_Relay/delay_" + str(delay) + ".json"

        data_0 = get_data(path=path_0)
        data_1 = get_data(path=path_1)
        data_2 = get_data(path=path_2)

        my_dict[delay] = {
            0: data_0['summary']['graph'],
            1: data_1['summary']['graph'],
            2: data_2['summary']['graph']
        }

        my_analysis[delay] = {
            0: data_0['summary']['means']['packets'],
            1: data_1['summary']['means']['packets'],
            2: data_2['summary']['means']['packets']
        }

    l_dict = dict()
    g_dict = dict()
    p_dict = dict()
    l_min_dict = dict()
    l_max_dict = dict()
    packets = dict()
    for i in range(0, 3):
        l_list = dict()
        g_list = dict()
        p_list = dict()
        l_min = dict()
        l_max = dict()
        pack = dict()
        for delay in delays:
            l_list[delay] = my_dict[delay][i]['latency_mean']
            g_list[delay] = my_dict[delay][i]['goodput']
            p_list[delay] = my_dict[delay][i]['PDR']
            l_min[delay] = my_dict[delay][i]['latency_min']
            l_max[delay] = my_dict[delay][i]['latency_max']
            pack[delay] = {'sent': my_analysis[delay][i]['packet_sent'],
                           'not_sent': my_analysis[delay][i]['packet_not_sent'],
                           'lost': my_analysis[delay][i]['packet_lost'],
                           'received': my_analysis[delay][i]['packet_received']}

        l_dict[i] = l_list
        g_dict[i] = g_list
        p_dict[i] = p_list
        l_min_dict[i] = l_min
        l_max_dict[i] = l_max
        packets[i] = pack

    define_xlsx(l=l_dict, g=g_dict, p=p_dict, l_min=l_min_dict, l_max=l_max_dict, pack=packets, delays=delays)

    plot(g_dict, '', 'Goodput', ' [bytes/second]', name_dir)
    plot(p_dict, '', 'PDR', ' [Packet Delivery Ratio]', name_dir)
    plot_latency(l_dict, l_min_dict, l_max_dict)


def define_xlsx(l, g, p, l_min, l_max, pack, delays):
    name = my.path_media + "json_file/" + name_dir + "/Summary.xlsx"
    workbook = xlsxwriter.Workbook(filename=name)
    worksheet = workbook.add_worksheet(name="Summary")

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    bold.set_center_across()
    cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    cell_format.set_center_across()
    row = 1
    col = 0
    for i in range(0, 3):
        title = "Relay_" + str(i)
        worksheet.write(row, col, title, cell_format)
        row = row + 1

        worksheet.write(row, col, "Delay", bold)
        worksheet.write(row, col + 1, "PDR", bold)
        worksheet.write(row, col + 2, "Goodput", bold)
        worksheet.write(row, col + 3, "Latency_mean", bold)
        worksheet.write(row, col + 4, "Latency_min", bold)
        worksheet.write(row, col + 5, "Latency_max", bold)

        worksheet.write(row, col + 7, "Sent", bold)
        worksheet.write(row, col + 8, "Not_Sent", bold)
        worksheet.write(row, col + 9, "Lost", bold)
        worksheet.write(row, col + 10, "Received", bold)

        row = row + 1
        col = 0
        for delay in delays:
            arg = str(delay) + " ms"
            worksheet.write(row, col, arg)
            worksheet.write(row, col + 1, p[i][delay])
            worksheet.write(row, col + 2, g[i][delay])
            worksheet.write(row, col + 3, l[i][delay])
            worksheet.write(row, col + 4, l_min[i][delay])
            worksheet.write(row, col + 5, l_max[i][delay])

            worksheet.write(row, col + 7, pack[i][delay]['sent'])
            worksheet.write(row, col + 8, pack[i][delay]['not_sent'])
            worksheet.write(row, col + 9, pack[i][delay]['lost'])
            worksheet.write(row, col + 10, pack[i][delay]['received'])
            row = row + 1
        row = row + 1

    print("Saving xlsx: {}".format(name))
    workbook.close()


if __name__ == "__main__":
    try:
        main()  # Relay.xlsx
        main3()  # plot e Summary.xlsx

    except Exception as e:
        print(e)
