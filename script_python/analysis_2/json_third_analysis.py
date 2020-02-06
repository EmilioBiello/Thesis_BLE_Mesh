import emilio_function as my
import glob
import time
import xlsxwriter
import sys

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
approach = 1  # 0 -> normal, 1-> cuts
index_relay = 2  # 0..2
################################################################
relay = [0, 1, 2]
# delay = [50, 75, 100, 125, 150, 200, 250, 500, 1000]
delay = [50, 100, 150, 200, 250, 500, 1000]
type = ['ble', 'wifi', 'combine']
path_media = "/media/emilio/BLE/"
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/delay_*.json"
source_path_2 = my.path_media + "json_file/relay_" + str(
    relay[index_relay]) + "/outcomes/cuts/delay_X_*.json"  # TODO value cut
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/cuts/"


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
        else:
            row = row + 1
        col = 0
        for t in type:
            if i == 5:
                title = "Summary_" + t
            else:
                title = "Rilevazione_" + t + "_" + str(i + 1)
            worksheet.write(row, col, title, cell_format)
            worksheet.write(row + 1, col, "Delay", bold)
            worksheet.write(row + 1, col + 1, "PDR", bold)
            worksheet.write(row + 1, col + 2, "Goodput", bold)
            worksheet.write(row + 1, col + 3, "Latency_mean", bold)
            worksheet.write(row + 1, col + 4, "Latency_m_e", bold)
            worksheet.write(row + 1, col + 6, "Latency_lower", bold)
            worksheet.write(row + 1, col + 7, "Latency_upper", bold)

            worksheet.write(row + 1, col + 9, "Sent", bold)
            worksheet.write(row + 1, col + 10, "Received", bold)
            worksheet.write(row + 1, col + 11, "Lost", bold)
            worksheet.write(row + 1, col + 12, "Not_Sent", bold)
            col = col + 14

        row = row + 2
        for d in delay:
            col = 0
            for t in type:
                arg = str(d) + " ms"
                worksheet.write(row, col, arg)
                worksheet.write(row, col + 1, dataset[d][t]['pdr'][i])
                worksheet.write(row, col + 2, dataset[d][t]['goodput'][i])
                worksheet.write(row, col + 3, dataset[d][t]['latency'][i])
                worksheet.write(row, col + 4, dataset[d][t]['m_e'][i])
                worksheet.write(row, col + 6, dataset[d][t]['lower'][i])
                worksheet.write(row, col + 7, dataset[d][t]['upper'][i])

                worksheet.write(row, col + 9, dataset[d][t]['sent'][i])
                worksheet.write(row, col + 10, dataset[d][t]['received'][i])
                worksheet.write(row, col + 11, dataset[d][t]['lost'][i])
                worksheet.write(row, col + 12, dataset[d][t]['not_sent'][i])
                col = col + 14
            row = row + 1

    print("\x1b[1;32;40m Saving {}\x1b[0m".format(filename))
    workbook.close()


def main():
    if approach:
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
        data_details[item] = {
            'ble': {
                'latency': [],
                'goodput': [],
                'pdr': [],
                'm_e': [],
                'upper': [],
                'lower': [],
                'sent': [],
                'received': [],
                'lost': [],
                'not_sent': [],
            },
            'wifi': {
                'latency': [],
                'goodput': [],
                'pdr': [],
                'm_e': [],
                'upper': [],
                'lower': [],
                'sent': [],
                'received': [],
                'lost': [],
                'not_sent': [],
            },
            'combine': {
                'latency': [],
                'goodput': [],
                'pdr': [],
                'm_e': [],
                'upper': [],
                'lower': [],
                'sent': [],
                'received': [],
                'lost': [],
                'not_sent': [],
            }
        }
        for i in data_info[item]:
            for t in type:
                statistics = data_info[item][i]['statistic_'][t]
                mex = data_info[item][i]['mex_'][t]
                data_details[item][t]['latency'].append(statistics['latency']['mean'])
                data_details[item][t]['goodput'].append(statistics['goodput'])
                data_details[item][t]['pdr'].append(statistics['pdr'])
                data_details[item][t]['m_e'].append(statistics['latency']['error_margin'])
                data_details[item][t]['lower'].append(statistics['latency']['lower'])
                data_details[item][t]['upper'].append(statistics['latency']['upper'])
                data_details[item][t]['sent'].append(mex['sent'])
                data_details[item][t]['received'].append(mex['received'])
                data_details[item][t]['lost'].append(mex['lost'])
                data_details[item][t]['not_sent'].append(mex['not_sent'])

    save_xlsx(data_details)


if __name__ == "__main__":
    try:
        main()  # Relay.xlsx
    except Exception as e:
        print(e)
    sys.exit()
