import sys
import datetime as dt
import emilio_function as my
import time

# TODO cambiare gli indici [index_1 -> topic, index_2 -> delay]
index_relay = 2  # 0..2
index_delay = 2  # 0..6
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
    mex_removed = (120 * 1000) / delay[index_delay]  # In Questo caso sono 2 m
    total_mex = (4 * 60 * 1000) / delay[index_delay]
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
            else:
                print("- ", k, " -- ", length, " -- ", list_of_value)

    if len(list_mex) != total_mex:
        if len(list_mex) - total_mex == 1:
            rm = max(list_mex)
            list_mex.remove(rm)
            print("\x1b[1;32;40m new_max: {}\x1b[0m".format(max(list_mex)))
            xxx = dataset['_mex'][str(rm)]
            if len(xxx) == 3:
                outcomes['S'] -= 1
                outcomes['R'] -= 1
            print(xxx)

    outcomes['smaller'] = min(list_mex)
    outcomes['bigger'] = max(list_mex)

    if outcomes['S'] - outcomes['R'] - outcomes['L'] != 0:
        raise Exception('Error counting: {}'.format(outcomes['S'] - outcomes['R'] - outcomes['L']))

    if len(list_mex) != total_mex:
        raise Exception('\x1b[1;31;40m' + "Errore rimozione:[" + str(run) + "] " + str(len(list_mex)) + " --> " + str(
            mex_removed) + '\x1b[0m')
    if extern_add:
        print('\x1b[1;31;40m' + "Added:[" + str(max(list_mex)) + "] " + '\x1b[0m')
        return 1, outcomes
    return 0, outcomes


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
        new_start = start + dt.timedelta(0, 90)  # right shift --> default 40 s
        new_end = new_start + dt.timedelta(0, 240)  # 4m <- (60s*4)
        new_diff = new_end - new_start
        h, m, s = my.convert_timedelta(new_diff)
        fault, outcome = analysis(data, new_start, new_end, i)  # ANALISI
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
    total = (4 * 60 * 1000) / delay[index_delay]
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
