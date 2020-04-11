import emilio_function as my
import datetime as dt
import time
import numpy as np
import xlsxwriter
import sys
import math
from decimal import Decimal

index_relay = 2  # 0..2
tech = 'ble_output'
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
elements = ['1', '2', '3', '4', '5']
terms = ['latency', 'l_m_e', 'pdr', 'p_m_e', 'goodput', 'g_m_e']


def my_confidential_interval_(dataset):
    sample_size = len(dataset)
    sum_ = 0
    for i in range(sample_size):
        sum_ = sum_ + dataset[i]
    media = sum_ / sample_size
    sum_2 = 0
    for i in range(sample_size):
        sum_2 = sum_2 + pow((dataset[i] - media), 2)
    variance = sum_2 / (sample_size - 1)
    std = math.sqrt(variance)
    q = 1.96
    m_e = q * (std / math.sqrt(sample_size))
    value_1 = media - m_e
    value_2 = media + m_e
    print("sample_size:{}".format(sample_size))
    print("media:{}".format(media))
    print("std:{}".format(std))
    print("m_e:{}".format(m_e))


def print_output_for_latex(dataset):
    delay.reverse()
    print("----\n\n")
    print("\t\t\hline")
    for d in delay:
        hz = 1 / (int(d) / 1000)
        if hz < 6 or hz > 7:
            hz = int(hz)
        else:
            hz = round(hz, 2)
        string = str(hz) + " Hz & \scriptsize (" + str(d) + " ms)"
        for i in range(len(terms)):
            value = str(round(dataset[d][terms[i]], 3))
            if value == "0.0":
                value = "{:.2e}".format(dataset[d][terms[i]])
                if value == "0.00e+00":
                    value = "0.0"
                else:
                    value = value.replace("e", " \\times 10^{")
                    x_1 = value[-2:len(value)]
                    if int(x_1) < 10:
                        value = value[:-2] + str(int(x_1))
                    value = value + "}"

            value = "$ " + value + " $"
            string = string + " & " + value

        print("\t\t" + string + " \\\\")
        print("\t\t\hline")


def get_data():
    data_details = dict()
    for d in delay:
        info = {'latency': [], 'pdr': [], 'goodput': []}
        path_json_data = my.path_media + "json_file/" + tech + "/relay_" + str(
            relay[index_relay]) + "/x/delay_XXX_" + str(
            d) + ".json"

        data = my.open_file_and_return_data(path=path_json_data)
        data_details[d] = dict()

        for item in elements:
            if tech == 'ble_output':
                info['latency'].append(data[item]['statistic_']['latency']['mean'])
                info['pdr'].append(data[item]['statistic_']['pdr'])
                info['goodput'].append(data[item]['statistic_']['goodput_1'])
            elif tech == 'ble_wifi_output':
                info['latency'].append(data[item]['statistic_']['total']['latency']['mean'])
                info['pdr'].append(data[item]['statistic_']['total']['pdr'])
                info['goodput'].append(data[item]['statistic_']['total']['goodput_1'])
            else:
                raise ValueError('tech incorrect!')

        out_latency = my.intervalli_di_confidenza(info['latency'])
        # my_confidential_interval_(info['latency'])
        out_pdr = my.intervalli_di_confidenza(info['pdr'])
        out_goodput = my.intervalli_di_confidenza(info['goodput'])

        data_details[d][terms[0]] = out_latency['mean']
        data_details[d][terms[1]] = out_latency['m_e']
        data_details[d][terms[2]] = out_pdr['mean']
        data_details[d][terms[3]] = out_pdr['m_e']
        data_details[d][terms[4]] = out_goodput['mean']
        data_details[d][terms[5]] = out_goodput['m_e']

    return data_details


def save_xlsx(dataset):
    filename = my.path_media + "json_file/" + str(tech) + "/relay_" + str(
        relay[index_relay]) + "/x/" + "relay_" + str(
        relay[index_relay]) + "_extra.xlsx"
    workbook = xlsxwriter.Workbook(filename=filename)

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    bold.set_center_across()
    cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    cell_format.set_center_across()

    worksheet = workbook.add_worksheet(name="Relay_" + str(relay[index_relay]))

    title = "Summary_Relay_" + str(relay[index_relay])
    row = 0
    col = 0
    worksheet.write(row, col, title, cell_format)
    row = 1
    worksheet.write(row, col, "Delay", bold)
    worksheet.write(row, col + 1, "latency", bold)
    worksheet.write(row, col + 2, "l_m_e", bold)
    worksheet.write(row, col + 3, "pdr", bold)
    worksheet.write(row, col + 4, "p_m_e", bold)
    worksheet.write(row, col + 5, "goodput", bold)
    worksheet.write(row, col + 6, "g_m_e", bold)
    row = 2
    for d in dataset:
        col = 0
        arg = str(d) + " ms"
        worksheet.write(row, col, arg)
        col = 1
        for i in range(len(terms)):
            worksheet.write(row, col + i, dataset[d][terms[i]])
        row = row + 1

    print("\x1b[1;32;40m Saving {}\x1b[0m".format(filename))
    workbook.close()


def main():
    data = get_data()
    # save_xlsx(dataset=data)
    print_output_for_latex(dataset=data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
