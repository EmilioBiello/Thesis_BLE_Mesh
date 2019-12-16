import datetime as dt
import statistics
import emilio_function as my
import re
import time

regular_expression_mex = "^[R|S|P],[0-9]{1,5},[0-9]$"
find_all_matches = "[P|S|R]{1},[0-9]{1,4},[0-7]"

path_pc = "./"
path_media = "/media/emilio/BLE/"
file_name = "json_file/test_2019_12_14/test_19_12_14-10_30_08.json"
path = path_pc + file_name

preprocessing_path = file_name[:-5] + "_preprocessing.json"
analysis_path = file_name[:-5] + "_analysis.json"

path_1 = path_media + file_name[:-5] + "_preprocessing.json"
path_2 = path_media + file_name[:-5] + "_analysis.json"


# tratta gli error sollevati nella fase precedente e definisce se si tratta di un timeout o di un packet not sent
# calcolo messaggi effettivamente inviati, mex_non inviati e pacchetti persi
def third_analysis(data):
    print("- {}".format(third_analysis.__name__))
    # data = my.open_file_and_return_data(path=path)
    errors = data['error_second_analysis']

    if data['analysis_status'] != 2:
        raise Exception('\x1b[1;31;40m' + ' Phase 3 is already executed ' + '\x1b[0m')

    lost = 0
    not_sent = 0
    list_lost = list()
    list_not_sent = list()
    if len(data['error_second_analysis']) != 0:
        last = int(errors[0]['index'])
        for i, item in enumerate(errors):
            if int(item['index']) - last == 1:
                if int(item['next_mex']['message_id']) == 0:
                    not_sent += 1
                    # print("Packet {} --> not sent".format(item['index']))
                    data['error_second_analysis'][i]['string'] = "Message not sent"
                    list_not_sent.append(int(item['index']))
                else:
                    lost += 1
                    # print("Packet {} --> TIMEOUT".format(item['index']))
                    data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
                    list_lost.append(int(item['index']))
            else:
                lost += 1
                # print("Packet {} --> TIMEOUT".format(item['index']))
                data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
                list_lost.append(int(item['index']))
            last = int(item['index'])

    data['analysis']['packet_sent'] = int(int(data['_command']['n_mex']) - not_sent)
    data['analysis']['packet_not_sent'] = int(not_sent)
    data['analysis']['packet_lost'] = int(lost)
    if len(list_lost) != 0 and len(list_lost) <= 20:
        data['analysis']['list_lost_mex_id'] = list_lost
    if len(list_not_sent) != 0 and len(list_not_sent) <= 20:
        data['analysis']['list_not_sent_mex_id'] = list_not_sent

    data['analysis_status'] = 3
    _diff_mex_ = int(data['analysis']['packet_sent']) - int(data['analysis']['packet_received']) - int(
        data['analysis']['packet_lost'])
    print("Packet Sent: {}".format(data['analysis']['packet_sent']))
    print("Packet Received: {}".format(data['analysis']['packet_received']))
    print("Packet Lost: {}".format(data['analysis']['packet_lost']))
    print("Packet Not Sent: {}".format(data['analysis']['packet_not_sent']))
    print("Differences: {}".format(_diff_mex_))

    if _diff_mex_ == 0:
        print("Correct analysis")
    else:
        print("Error about counting in analysis [lost, sent, received] difference: {}".format(_diff_mex_))
    return data


# calcolo i tempi per ciascuna coppia di mex [sent --> received] e individuo eventuali errori [timeout, packet not set]
# definisco latency media del test
def second_analysis(data):
    print("- {}".format(second_analysis.__name__))
    # data = my.open_file_and_return_data(path=path)
    messages = data['messages']

    if len(data['error_first_analysis']) > 0:
        raise Exception('\x1b[1;31;40m' + ' Error: List \'error_first_analysis\' not empty ' + '\x1b[0m')

    if data['analysis_status'] != 1:
        raise Exception('\x1b[1;31;40m' + ' Phase 2 is already executed ' + '\x1b[0m')

    list_of_m_id = list()
    for item in messages:
        list_of_m_id.append(item['message_id'])

    list_of_m_id = list(dict.fromkeys(list_of_m_id))  # definisco una lista contenente i message_id
    if '0' in list_of_m_id:
        list_of_m_id.remove('0')

    packet_received = 0
    differences = list()
    latencies = list()
    dict_analysis = dict()
    new_data = {'error_second_analysis': []}
    size_messages = len(messages)
    user_check = False
    first_send = messages[0]['time']
    last_received = messages[0]['time']
    min_diff_string = ""
    max_diff_string = ""
    min_diff_time = ""
    max_diff_time = ""
    for m_id in list_of_m_id:
        couple = my.get_mex_couple(messages, m_id)  # individuo le coppie di messaggi

        if len(couple) == 2:
            packet_received += 1
            match_1, e_1, type_1 = my.look_into_element(messages[couple[0]])
            match_2, e_2, type_2 = my.look_into_element(messages[couple[1]])
            if not match_1 and not match_2:
                raise Exception('\x1b[1;31;40m' + ' Error: value unexpected about message_id: ' + e_1 + ' \x1b[0m')

            if type_1:
                send_time = messages[couple[0]]['time']
                receive_time = messages[couple[1]]['time']
            else:
                receive_time = messages[couple[0]]['time']
                send_time = messages[couple[1]]['time']

            if first_send > send_time:
                first_send = send_time
            if last_received < receive_time:
                last_received = receive_time

            send_datetime = dt.datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S.%f')
            receive_datetime = dt.datetime.strptime(receive_time, '%Y-%m-%d %H:%M:%S.%f')

            # timedelta output (days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            # 1 millisecond --> 1000 microseconds
            difference = receive_datetime - send_datetime
            differences.append(difference.total_seconds())
            latencies.append(difference.total_seconds() / 2)

            if int(m_id) < 10:
                m_id = "0" + m_id

            dict_analysis[m_id] = {
                'send_time': send_time,
                'status_time': receive_time,
                'difference': difference.total_seconds(),
                'latency': (difference.total_seconds() / 2)
            }

            if min_diff_time == "":
                min_diff_time = difference.total_seconds()
                min_diff_string = m_id
            elif difference.total_seconds() < min_diff_time:
                min_diff_time = difference.total_seconds()
                min_diff_string = m_id

            if max_diff_time == "":
                max_diff_time = difference.total_seconds()
                max_diff_string = m_id
            elif difference.total_seconds() > max_diff_time:
                max_diff_time = difference.total_seconds()
                max_diff_string = m_id

            # print("m_id: {} --> {}".format(m_id, dict_analysis[m_id]['difference']))
        elif len(couple) == 1:
            if not user_check:
                user_check = True
            if couple[0] + 1 < size_messages:
                next_mex = messages[couple[0] + 1]
                new_data['error_second_analysis'].append(
                    {'index': int(m_id), 'next_mex': {'message_id': next_mex['message_id'],
                                                      'type_mex': next_mex['type_mex']
                                                      },
                     'string': 'TimeOut or message not sent'})
            else:
                # last message
                new_data['error_second_analysis'].append(
                    {'index': int(m_id), 'next_mex': {'message_id': messages[couple[0]]['message_id'],
                                                      'type_mex': messages[couple[0]]['type_mex']
                                                      }, 'string': 'TimeOut or message not sent'})
        else:
            print("EROROR: {} --> {}".format(m_id, len(couple)))
            print("{} --- {} --- {}".format(messages[couple[0]]['time'], messages[couple[1]]['time'],
                                             messages[couple[2]]['time']))
            # print("m_id: {} --> TimeOut or message not sent".format(m_id))

    print("Couple founded: {}".format(packet_received))
    first_datetime = dt.datetime.strptime(first_send, '%Y-%m-%d %H:%M:%S.%f')
    last_datetime = dt.datetime.strptime(last_received, '%Y-%m-%d %H:%M:%S.%f')
    test_time = last_datetime - first_datetime
    hours, minutes, seconds = my.convert_timedelta(test_time)
    print("Tempo test: {}:{}.{} [mm:s.us]".format(minutes, seconds, test_time.microseconds))
    test_time_m = str(minutes) + " M, " + str(seconds) + " s"

    new_data['second_analysis'] = dict_analysis
    new_data['_command'] = data['_command']
    new_data['analysis'] = {
        'packet_received': int(packet_received),
        'average_diff_time': statistics.mean(differences),  # seconds
        'min_diff_time': min(differences),
        # 'min_diff_time_2': min_diff_time,
        'min_diff_key': min_diff_string,
        'max_diff_time': max(differences),
        # 'max_diff_time_2': max_diff_time,
        'max_diff_key': max_diff_string,
        'average_latency_time': statistics.mean(latencies),  # seconds
        'min_latency_time': min(latencies),
        'max_latency_time': max(latencies),
        'test_time_first_time': first_send,
        'test_time_last_time': last_received,
        'test_time': test_time.total_seconds(),
        'test_time_m': test_time_m,
        '_comment': 'The times are expressed in seconds'
    }
    new_data['analysis_status'] = 2
    return new_data, user_check


def update_data(data, index, string):
    data['messages'][index]['message_id'] = string[1]
    data['messages'][index]['type_mex'] = string[0]
    data['messages'][index]['ttl'] = string[2]
    return data


def add_element_to_data(data, string, time):
    data['messages'].append({
        'message_id': string[1],
        'type_mex': string[0],
        'ttl': string[2],
        'time': time
    })
    return data


def split_string_3(data, s_1, s_2, t_1, t_2, first_index, second_index, search):
    print("1° item --> string: {} --> time: {}".format(s_1, t_1))
    print("2° item --> string: {} --> time: {}".format(s_2, t_2))
    print("\x1b[0;33;40m Split: {} \x1b[0m".format(search))

    # Prendo il tempo relativo al first_index per il mex di send
    data = update_data(data=data, index=first_index, string=search[0].split(','))
    data = update_data(data=data, index=second_index, string=search[2].split(','))
    data = add_element_to_data(data=data, string=search[1].split(','), time=t_1)
    print("-----------")
    return data


# risolvo gli eventuali erorri sollevati nella fase di preprocessing
def resolve_errors_preprocessing(data):
    print("- {}".format(resolve_errors_preprocessing.__name__))
    # data = my.open_file_and_return_data(path=path)
    if data['analysis_status'] != -1:
        raise Exception('\x1b[1;31;40m' + ' Resolution error is not necessary or already executed ' + '\x1b[0m')

    errors = data['error_first_analysis']
    list_1_remove_after_union = list()

    list_split = list()
    list_union = list()
    for i in range(len(errors)):
        if errors[i]['#_comma'] == 4 and len(re.findall(find_all_matches, errors[i]['string'])) == 2:
            list_split.append(i)
        else:
            list_union.append(i)

    only_update = list()
    error = False
    for i in list_union:
        first_index = int(errors[i]['index'])
        if first_index not in list_1_remove_after_union and first_index not in only_update:
            j = i + 1
            if j < len(errors):
                second_index = int(errors[j]['index'])
                strings = errors[i]['string'] + errors[j]['string']  # concateno le due stringhe
                if second_index - first_index == 1:
                    if re.match(regular_expression_mex, strings):
                        data = update_data(data, first_index, strings.split(','))
                        list_1_remove_after_union.append(second_index)
                    else:
                        search = re.findall(find_all_matches, strings)
                        if len(search) == 1:
                            data = update_data(data, first_index, strings.split(','))
                            list_1_remove_after_union.append(second_index)
                        elif len(search) == 2:
                            data = update_data(data, first_index, search[0].split(','))
                            data = update_data(data, second_index, search[1].split(','))
                            only_update.append(second_index)
                        elif len(search) == 3:
                            data = split_string_3(data=data, s_1=errors[i]['string'], s_2=errors[j]['string'],
                                                  t_1=errors[i]['time'], t_2=errors[j]['time'], first_index=first_index,
                                                  second_index=second_index, search=search)
                            only_update.append(second_index)
                        else:
                            error = True
                            print("ERRORE [{} - {}] len:{} {}".format(first_index, second_index, len(search), search))
                else:
                    error = True
                    print("Error with couple: {} - {} [{}] [{}]".format(first_index, second_index, strings,
                                                                        errors[i]['time']))

    for i in list_split:
        index = int(errors[i]['index'])
        strings = errors[i]['string']
        time = errors[i]['time']
        search = re.findall(find_all_matches, strings)
        data = update_data(data, index, search[0].split(','))
        data = add_element_to_data(data=data, string=search[1].split(','), time=time)

    list_1_remove_after_union.sort(reverse=True)
    for i in list_1_remove_after_union:
        del data['messages'][i]

    if not error:
        errors.clear()

    data['analysis_status'] = 1
    return data


# verifico eventuali errori nella memorizzazione delle stringhe in message_id
def preprocessing(path):
    print("- {}".format(preprocessing.__name__))
    check = False
    data = my.open_file_and_return_data(code=0, path=path)

    if data['analysis_status'] != 0:
        raise Exception('\x1b[1;31;40m' + ' Preprocessing is already executed ' + '\x1b[0m')

    data['error_first_analysis'] = []
    for i, mex in enumerate(data['messages']):
        if not re.match(regular_expression_mex, mex['message_id']):
            counter = mex['message_id'].count(',')
            data['error_first_analysis'].append(
                {'index': i, '#_comma': counter, 'time': mex['time'], 'string': mex['message_id']})
            if not check:
                check = True
        else:
            string = mex['message_id']
            mex['message_id'] = string.split(',')[1]
            mex['type_mex'] = string.split(',')[0]
            mex['ttl'] = string.split(',')[2]

    data['analysis_status'] = -1 if check else 1

    # Faccio in modo da eseguire preprocessing solo una volta
    # raw = my.open_file_and_return_data(path=path)
    # raw['analysis_status'] = 1
    # my.save_json_data_elegant(path=path, data=raw)
    return data


def call_preprocessing_and_save(path, path_1):
    my_data = preprocessing(path=path)
    my.save_json_data_elegant(path=path_1, data=my_data)


def call_error_resolution_and_save(path_s):
    data = my.open_file_and_return_data(code=0, path=path_1)
    data = resolve_errors_preprocessing(data=data)
    my.save_json_data_elegant(path=path_s, data=data)


def call_second_analysis_and_save(path_s):
    data = my.open_file_and_return_data(code=0, path=path_1)
    data, users = second_analysis(data=data)
    my.save_json_data_elegant(path=path_s, data=data)


def call_third_analysis_and_save(path_s):
    data = my.open_file_and_return_data(code=0, path=path_2)
    data = third_analysis(data=data)
    my.save_json_data_elegant(path=path_s, data=data)


def main():
    # path = my.get_argument()
    my_data = dict()

    try:
        my_data = my.open_file_and_return_data(path=path)
        # my.save_json_data_elegant(path=path_1, data=my_data)
        print('\x1b[0;33;40m' + " Preprocessing completed! " + '\x1b[0m')
    except Exception as e:
        print(e)
        return

    try:
        my_data = resolve_errors_preprocessing(data=my_data)
        # my.save_json_data_elegant(path=path_1, data=my_data)
        print('\x1b[0;33;40m' + " Error Preprocessing resoluted! " + '\x1b[0m')
    except Exception as e:
        print(e)
        return

    try:
        my_data, checks = second_analysis(data=my_data)
        # my.save_json_data_elegant(path=path_1, data=my_data)
        print('\x1b[0;33;40m' + " Second Analysis completed! " + '\x1b[0m')
    except Exception as e:
        print(e)
        return

    try:
        my_data = third_analysis(data=my_data)
        print('\x1b[0;33;40m' + " Third Analysis completed! " + '\x1b[0m')
        my.save_json_data_elegant(path=path_1, data=my_data)
    except Exception as e:
        print(e)


def testing_phase():
    # PREPROCESSING
    call_preprocessing_and_save(path=path, path_1=preprocessing_path)
    time.sleep(1)

    # ERROR Resolution
    call_error_resolution_and_save(path_s=preprocessing_path)
    time.sleep(1)

    # Seconds Analysis
    call_second_analysis_and_save(path_s=analysis_path)
    time.sleep(1)

    # Third Analysis
    call_third_analysis_and_save(path_s=analysis_path)
    time.sleep(1)


if __name__ == "__main__":
    try:
        testing_phase()
    except Exception as e:
        print(e)
