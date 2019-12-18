import emilio_function as my
import numpy as np
import matplotlib.pyplot as plt
import glob
import time
import xlsxwriter

# TODO main() cambiare solo topic
topic = 0
path_analysis = my.path_media + "json_file/analysis_" + str(topic) + "_Relay/*.json"


def single_delay(data, my_dictionary):
    label = data["_command"]["delay"]

    # TODO if necessario perchè in 2 Relay 100 ms manca una rilevazione [sono 4 test e non 5]
    if topic == 2 and label == 100:
        my_dictionary[label] = {
            'rilevazione_1': data['rilevazione_1']['graph'],
            'rilevazione_2': data['rilevazione_2']['graph'],
            'rilevazione_3': data['rilevazione_3']['graph'],
            'rilevazione_4': data['rilevazione_4']['graph']
        }
    else:
        my_dictionary[label] = {
            'rilevazione_1': data['rilevazione_1']['graph'],
            'rilevazione_2': data['rilevazione_2']['graph'],
            'rilevazione_3': data['rilevazione_3']['graph'],
            'rilevazione_4': data['rilevazione_4']['graph'],
            'rilevazione_5': data['rilevazione_5']['graph']
        }
    return my_dictionary


def set_list(my_dictionary, delay):
    latencies = list()
    goodputs = list()
    pdr = list()
    for i in range(1, 6):
        # TODO if necessario perchè in 2 Relay 100 ms manca un test [sono 4 test e non 5]
        if topic == 2 and delay == 100 and i == 5:
            print("manca 1")
        else:
            text = 'rilevazione_' + str(i)
            latencies.append(my_dictionary[delay][text]['latency_mean'])
            goodputs.append(my_dictionary[delay][text]['goodput'])
            pdr.append(my_dictionary[delay][text]['PDR'])
    return latencies, goodputs, pdr


def save_xlsx_relay(latencies, goodputs, pdrs, delays):
    name = my.path_media + "json_file/plot_3/Relay_" + str(topic) + ".xlsx"
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
        worksheet.write(row, col + 1, "Latency", bold)
        worksheet.write(row, col + 2, "PDR", bold)
        worksheet.write(row, col + 3, "Goodput", bold)
        row = row + 1
        col = 0
        for delay in delays:
            arg = str(delay) + " ms"
            worksheet.write(row, col, arg)
            worksheet.write(row, col + 1, latencies[delay][i])
            worksheet.write(row, col + 2, pdrs[delay][i])
            worksheet.write(row, col + 3, goodputs[delay][i])
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
    delays = [50, 100, 250, 500, 1000]

    my_dictionary = dict()
    for name in sorted(list_of_files):
        delay_ = name.split('/')[6].split('_')[1][:-5]
        if int(delay_) != 200:
            data = get_data(path=name)
            my_dictionary = single_delay(data, my_dictionary)
            time.sleep(1)

    latencies = dict()
    goodputs = dict()
    pdrs = dict()
    for item in delays:
        latency, goodput, pdr = set_list(my_dictionary=my_dictionary, delay=item)
        latencies[item] = latency
        goodputs[item] = goodput
        pdrs[item] = pdr

    save_xlsx_relay(latencies, goodputs, pdrs, delays)


def plot(data, delay, label_, label_2, plot_dir):
    x_label = ""
    for i in range(0, 3):
        if i == 0:
            color = "red"
        elif i == 1:
            color = "green"
        elif i == 2:
            color = "blue"
        else:
            color = "black"

        label_1 = str(i) + ' relay'
        dati = list()
        x = list()
        x_label = 'x - delay ms'

        for key, value in data[i].items():
            x.append(key)
            dati.append(value)

        plt.scatter(x, dati, label=label_1, color=color, s=20)

    text = label_ + " " + str(delay) + " ms "
    y_label = "y - " + label_ + label_2

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    plt.title(text)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    name = my.path_media + "json_file/" + plot_dir + "/" + str(delay) + "_" + label_ + '.png'
    print("Saving png: {}".format(name))
    plt.savefig(name)
    plt.show()


def main3():
    delays = [50, 100, 250, 500, 1000]
    my_dict = dict()

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

    l_dict = dict()
    g_dict = dict()
    p_dict = dict()
    for i in range(0, 3):
        l_list = dict()
        g_list = dict()
        p_list = dict()
        for delay in delays:
            l_list[delay] = my_dict[delay][i]['latency_mean']
            g_list[delay] = my_dict[delay][i]['goodput']
            p_list[delay] = my_dict[delay][i]['PDR']
        l_dict[i] = l_list
        g_dict[i] = g_list
        p_dict[i] = p_list

    define_xlsx(data_l=l_dict, data_g=g_dict, data_p=p_dict, delays=delays)

    plot(l_dict, '', 'Latency', ' [seconds]', 'plot_3')
    plot(g_dict, '', 'Goodput', ' [bytes/second]', 'plot_3')
    plot(p_dict, '', 'PDR', ' [Packet Delivery Ratio]', 'plot_3')


def define_xlsx(data_l, data_g, data_p, delays):
    name = my.path_media + "json_file/plot_3/Test.xlsx"
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
        worksheet.write(row, col + 1, "Latency", bold)
        worksheet.write(row, col + 2, "PDR", bold)
        worksheet.write(row, col + 3, "Goodput", bold)
        row = row + 1
        col = 0
        for delay in delays:
            arg = str(delay) + " ms"
            worksheet.write(row, col, arg)
            worksheet.write(row, col + 1, data_l[i][delay])
            worksheet.write(row, col + 2, data_p[i][delay])
            worksheet.write(row, col + 3, data_g[i][delay])
            row = row + 1
        row = row + 1

    print("Saving xlsx: {}".format(name))
    workbook.close()


if __name__ == "__main__":
    try:
        main()  # Relay.xlsx
        main3() # plot e Test.xlsx

    except Exception as e:
        print(e)
