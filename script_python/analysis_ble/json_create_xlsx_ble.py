import emilio_function as my
import glob
import time
import xlsxwriter
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
all_test_or_cut = 1  # 0 -> normal, 1-> cuts
index_relay = 2  # 0..2
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
terms = ['S', 'R', 'L', 'E', 'latency', 'std', 'm_e', 'low', 'up', 'pdr', 'goodput','goodput_1']
path_media = "/media/emilio/BLE/"
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/delay_*.json"
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"

# TODO value cut
source_path_2 = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/delay_XXX_*.json"
outcome_path_2 = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/"


def get_info_from_data(data, info):
    label = data["_command"]["delay"]
    info[int(label)] = {
        '1': data['1'],
        '2': data['2'],
        '3': data['3'],
        '4': data['4'],
        '5': data['5'],
        '10': data['summary']
    }
    return info


def save_xlsx(dataset):
    if all_test_or_cut:
        filename = outcome_path_2 + "relay_XXX_" + str(relay[index_relay]) + ".xlsx"
    else:
        filename = outcome_path + "relay_" + str(relay[index_relay]) + ".xlsx"

    workbook = xlsxwriter.Workbook(filename=filename)

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    bold.set_center_across()
    cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    cell_format.set_center_across()

    worksheet = workbook.add_worksheet(name="Relay_" + str(relay[index_relay]))
    row = 0
    for i in range(6):
        if i == 5:
            row = row + 2
            title = "Summary_ble"
        else:
            row = row + 1
            title = "Rilevazione_ble_" + str(i + 1)
        col = 0

        worksheet.write(row, col, title, cell_format)
        worksheet.write(row + 1, col, "Delay", bold)
        worksheet.write(row + 1, col + 1, "S", bold)
        worksheet.write(row + 1, col + 2, "R", bold)
        worksheet.write(row + 1, col + 3, "L", bold)
        worksheet.write(row + 1, col + 4, "E", bold)
        worksheet.write(row + 1, col + 6, "Latency_mean", bold)
        worksheet.write(row + 1, col + 7, "Latency_std", bold)
        worksheet.write(row + 1, col + 8, "Latency_m_e", bold)
        worksheet.write(row + 1, col + 9, "Latency_lower", bold)
        worksheet.write(row + 1, col + 10, "Latency_upper", bold)
        worksheet.write(row + 1, col + 12, "PDR", bold)
        worksheet.write(row + 1, col + 13, "Goodput", bold)
        worksheet.write(row + 1, col + 14, "Goodput_1", bold)

        row = row + 2
        for d in delay:
            col = 0
            arg = str(d) + " ms"
            worksheet.write(row, col, arg)
            worksheet.write(row, col + 1, dataset[d][terms[0]][i])
            worksheet.write(row, col + 2, dataset[d][terms[1]][i])
            worksheet.write(row, col + 3, dataset[d][terms[2]][i])
            worksheet.write(row, col + 4, dataset[d][terms[3]][i])
            worksheet.write(row, col + 6, dataset[d][terms[4]][i])
            worksheet.write(row, col + 7, dataset[d][terms[5]][i])
            worksheet.write(row, col + 8, dataset[d][terms[6]][i])
            worksheet.write(row, col + 9, dataset[d][terms[7]][i])
            worksheet.write(row, col + 10, dataset[d][terms[8]][i])
            worksheet.write(row, col + 12, dataset[d][terms[9]][i])
            worksheet.write(row, col + 13, dataset[d][terms[10]][i])
            worksheet.write(row, col + 14, dataset[d][terms[11]][i])
            row = row + 1

    print("\x1b[1;32;40m Saving {}\x1b[0m".format(filename))
    workbook.close()


def main():
    if all_test_or_cut:
        list_of_files = glob.glob(source_path_2)
    else:
        list_of_files = glob.glob(source_path)

    data_info = dict()
    for name in sorted(list_of_files):
        data = my.open_file_and_return_data(path=name)
        data_info = get_info_from_data(data, data_info)
        time.sleep(0.05)

    data_details = dict()
    for item in delay:
        data_details[item] = dict()
        for t1 in terms:
            data_details[item][t1] = list()

        for i in data_info[item]:
            statistics = data_info[item][i]['statistic_']
            mex = data_info[item][i]['mex_']

            data_details[item][terms[0]].append(mex[terms[0]])
            data_details[item][terms[1]].append(mex[terms[1]])
            data_details[item][terms[2]].append(mex[terms[2]])
            data_details[item][terms[3]].append(mex[terms[3]])
            data_details[item][terms[4]].append(statistics[terms[4]]['mean'])
            data_details[item][terms[5]].append(statistics['latency'][terms[5]])
            data_details[item][terms[6]].append(statistics['latency'][terms[6]])
            data_details[item][terms[7]].append(statistics['latency'][terms[7]])
            data_details[item][terms[8]].append(statistics['latency'][terms[8]])
            data_details[item][terms[9]].append(statistics[terms[9]])
            data_details[item][terms[10]].append(statistics[terms[10]])
            data_details[item][terms[11]].append(statistics[terms[11]])

    save_xlsx(data_details)


if __name__ == "__main__":
    try:
        main()  # Relay.xlsx
    except Exception as e:
        print(e)
    sys.exit()
