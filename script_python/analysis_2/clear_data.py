import sys
import datetime as dt
import emilio_function as my

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_topic = 2  # 0..2
index_delay = 2  # 0..6
################################################################
topic = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/delay_" + str(
    delay[index_delay]) + "/*_analysis.json"
delay_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/outcomes/"
outcome_path = my.path_media + "json_file/relay_" + str(topic[index_topic]) + "/outcomes/cuts/"


def save_data(my_dictionary):
    path_json = outcome_path + "delay_x_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def analysis(dataset, start_, end_, run):
    list_ble = set()
    list_wifi = set()
    received_ble = 0
    received_wifi = 0
    mex_removed = (60 * 1000) / delay[index_delay]
    total_mex = dataset['_command']['n_mex'] - mex_removed
    extern_add = False
    for index, list_of_value in dataset['_mex'].items():
        for v in list_of_value:
            if 'type_mex' in v:
                if v['type_mex'] == "S":
                    if start_ <= dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f') <= end_:
                        list_ble.add(int(index))
                    elif dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f') > end_ and len(list_ble) < total_mex:
                        extern_add = True
                        list_ble.add(int(index))
                if v['type_mex'] == "I":
                    if start_ <= dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f') <= end_:
                        list_wifi.add(int(index))
            if 'ble' in v:
                if start_ <= dt.datetime.strptime(v['ble']['send_time'], '%Y-%m-%d %H:%M:%S.%f') <= end_:
                    received_ble += 1
            if 'wifi' in v:
                if start_ <= dt.datetime.strptime(v['wifi']['send_time'], '%Y-%m-%d %H:%M:%S.%f') <= end_:
                    received_wifi += 1
    if extern_add:
        element = dataset['_mex'][str(max(list_ble))]
        for v in element:
            if 'type_mex' in v:
                if v['type_mex'] == "I":
                    list_wifi.add(int(max(list_ble)))
            if 'ble' in v:
                received_ble += 1
            if 'wifi' in v:
                received_wifi += 1

    if len(list_ble) != total_mex:
        if len(list_ble) - total_mex == 1:
            list_ble.remove(max(list_ble))
            print("\x1b[1;32;40m new_max: {}\x1b[0m".format(max(list_ble)))

    lost_ble = len(list_ble) - received_ble
    lost_wifi = len(list_wifi) - received_wifi
    outcome = {'ble': {'lower': min(list_ble), 'upper': max(list_ble), 'sent': len(list_ble), 'received': received_ble,
                       'lost': lost_ble},
               'wifi': {'lower': min(list_wifi), 'upper': max(list_wifi), 'sent': len(list_wifi),
                        'received': received_wifi, 'lost': lost_wifi},
               'time': {}}
    if len(list_ble) != total_mex:
        print('\x1b[1;31;40m' + "Errore rimozione:[" + str(run) + "] " + str(len(list_ble)) + " --> " + str(
            mex_removed) + '\x1b[0m')
        return 1, outcome
    if extern_add:
        print('\x1b[1;31;40m' + "Added:[" + str(max(list_ble)) + "] " + '\x1b[0m')
        return 1, outcome
    return 0, outcome


def analysis_2(dataset, start_, run):
    is_found = True
    y = 1
    while is_found:
        list_of_value = dataset['_mex'][str(y)]
        if list_of_value[0]['type_mex'] == "S":
            if dt.datetime.strptime(list_of_value[0]['time'], '%Y-%m-%d %H:%M:%S.%f') >= start_:
                is_found = False
                continue
        y += 1
    mex_removed = (60 * 1000) / delay[index_delay]
    mex_removed = dataset['_command']['n_mex'] - mex_removed
    z = y + mex_removed
    list_valid = [i for i in range(int(y), int(z))]
    print("Min: {} -- Max: {}".format(min(list_valid), max(list_valid)))
    if len(list_valid) != mex_removed:
        print('\x1b[1;31;40m' + "Errore rimozione:[" + str(run) + "] " + str(len(list_valid)) + " --> " + str(
            mex_removed) + '\x1b[0m')
        return 0, 0
    return min(list_valid), max(list_valid)


def main():
    files = my.get_grouped_files(source_path=source_path, delay=delay, index_delay=index_delay)
    path = delay_path + "delay_" + str(delay[index_delay]) + ".json"
    data_delay = my.open_file_and_return_data(path=path)

    i = 1
    err = list()
    dictionaries = dict()
    data = dict()
    for item in files:
        data = my.open_file_and_return_data(path=item)
        print("\x1b[1;30;43m " + item[28:] + " \x1b[0m ")
        start = dt.datetime.strptime(data_delay[str(i)]['_info']['start'], '%Y-%m-%d %H:%M:%S.%f')
        end = dt.datetime.strptime(data_delay[str(i)]['_info']['end_sent'], '%Y-%m-%d %H:%M:%S.%f')
        # TODO shift focus about data --- duration 4 minute
        new_start = start + dt.timedelta(0, 40)  # right shift --> default 40 s
        new_end = new_start + dt.timedelta(0, 240)
        # end = end - dt.timedelta(0, 15)
        new_diff = new_end - new_start
        h, m, s = my.convert_timedelta(new_diff)
        fault, outcome = analysis(data, new_start, new_end, i)
        print("start: {} -- end: {} --- {}:{}.{} -- min: {} -- max: {}".format(new_start, new_end, h, m, s,
                                                                               outcome['ble']['lower'],
                                                                               outcome['ble']['upper']))
        time = str(h) + ":" + str(m) + "." + str(s) + " [h:m.s]"
        outcome['time'] = {'old_start': start, 'old_end': end, 'new_start': new_start, 'new_end': new_end,
                           'new_time': time}
        err.append(fault)
        dictionaries[i] = outcome
        i += 1
    mex_removed = (60 * 1000) / delay[index_delay]
    total = data['_command']['n_mex'] - mex_removed
    print("\x1b[1;34;40m [{}] Mex_removed: {} --> total: {} \x1b[0m ".format(delay[index_delay], mex_removed,
                                                                             total))
    print("err: --> ", err)
    dictionaries['error'] = err
    dictionaries['info'] = {'mex_removed': mex_removed, 'n_mex': total}
    save_data(dictionaries)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    sys.exit()
