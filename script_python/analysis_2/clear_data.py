import sys
import datetime as dt
import emilio_function as my
import time

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 1  # 0..2
index_delay = 0  # 0..6
# TODO scelta run... manuale o all_inclusive [0 -> single, 1 -> automatic]
approach = 0
################################################################
relay = [0, 1, 2]
delay = [50, 100, 150, 200, 250, 500, 1000]
source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
    delay[index_delay]) + "/*_analysis.json"
delay_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"
outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/"


def save_data(my_dictionary):
    path_json = outcome_path + "delay_x_" + str(delay[index_delay]) + ".json"
    my.save_json_data_2(path=path_json, data=my_dictionary)


def analysis(dataset, start_, end_, run):
    list_mex = set()
    mex_removed = (60 * 1000) / delay[index_delay]
    total_mex = (4*60 * 1000) / delay[index_delay]
    extern_add = False
    outcomes = {'S': 0, 'R': 0, 'L': 0, 'smaller': 0, 'bigger': 0}
    for k, list_of_value in dataset['_mex'].items():
        add = False
        for v in list_of_value:
            if 'type_mex' in v and v['type_mex'] == "S":
                if start_ <= dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f') <= end_:
                    add = True
                    list_mex.add(int(k))
                elif dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f') > end_ and len(list_mex) < total_mex:
                    add = True
                    extern_add = True
                    list_mex.add(int(k))
        if add:
            length = len(list_of_value)
            if length == 1 or length == 2:
                outcomes['S'] += 1
                outcomes['L'] += 1
            elif length == 3 and 'ble' in list_of_value[length - 1]:
                outcomes['S'] += 1
                outcomes['R'] += 1
            elif length == 3 and 'ble_wifi' in list_of_value[length - 1]:
                outcomes['S'] += 1
                outcomes['L'] += 1
            elif (length == 5 or length == 6) and 'ble_wifi' in list_of_value[length - 1]:
                outcomes['S'] += 1
                outcomes['R'] += 1
            elif length == 4:
                print("xxx ", k, " -- ", length, " -- ", list_of_value)
            else:
                print("- ", k, " -- ", length, " -- ", list_of_value)

    if len(list_mex) != total_mex:
        if len(list_mex) - total_mex == 1:
            rm = max(list_mex)
            list_mex.remove(rm)
            print("\x1b[1;32;40m new_max: {}\x1b[0m".format(max(list_mex)))
            xxx = dataset['_mex'][str(rm)]
            if len(xxx) == 5 or len(xxx) == 3:
                outcomes['S'] -= 1
                outcomes['R'] -= 1
            print(xxx)

    outcomes['smaller'] = min(list_mex)
    outcomes['bigger'] = max(list_mex)

    if outcomes['S'] - outcomes['R'] - outcomes['L'] != 0:
        raise Exception('Error counting: {}'.format(outcomes['S'] - outcomes['R'] - outcomes['L']))

    if len(list_mex) != total_mex:
        print('\x1b[1;31;40m' + "Errore rimozione:[" + str(run) + "] " + str(len(list_mex)) + " --> " + str(
            mex_removed) + '\x1b[0m')
        return 1, outcomes
    if extern_add:
        print('\x1b[1;31;40m' + "Added:[" + str(max(list_mex)) + "] " + '\x1b[0m')
        return 1, outcomes
    return 0, outcomes


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


def group_main():
    global index_delay
    global index_relay
    global source_path
    global delay_path
    global outcome_path
    for r in range(len(relay)):
        for d in range(len(delay)):
            index_relay = r
            index_delay = d
            source_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/" + str(
                delay[index_delay]) + "/*_analysis.json"
            delay_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/outcomes/"
            outcome_path = my.path_media + "json_file/relay_" + str(relay[index_relay]) + "/x/"
            main()
            time.sleep(1)


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
        new_start = start + dt.timedelta(0, 30)  # right shift --> default 40 s
        new_end = new_start + dt.timedelta(0, 240)  # 4m <- (60s*4)
        # end = end - dt.timedelta(0, 15)
        new_diff = new_end - new_start
        h, m, s = my.convert_timedelta(new_diff)
        fault, outcome = analysis(data, new_start, new_end, i)
        print("start: {} -- end: {} --- {}:{}.{} -- min: {} -- max: {}".format(new_start, new_end, h, m, s,
                                                                               outcome['smaller'],
                                                                               outcome['bigger']))
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
        if not approach:
            main()
        else:
            group_main()
    except Exception as e:
        print(e)
    sys.exit()
