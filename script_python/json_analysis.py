import datetime as dt
import statistics
import emilio_function as my
import re
import time
import math

relay = 0  # 0,1,2
path_pc = "./"
path_media = "/media/emilio/BLE/"
file_name = "json_file/test_2019_12_22/test_19_12_22-18_51_50.json"
path = path_pc + file_name

preprocessing_path = file_name[:-5] + "_preprocessing.json"
analysis_path = file_name[:-5] + "_analysis.json"
analysis_2_path = file_name[:-5] + "_analysis_2.json"

path_1 = path_media + file_name[:-5] + "_preprocessing.json"
path_2 = path_media + file_name[:-5] + "_analysis.json"
path_3 = path_media + file_name[:-5] + "_analysis_2.json"

regular_expression_mex = "^[S|R|E],[0-9]{1,5},[0-9]$"
find_all_matches = "[S|R|E],[0-9]{1,5},[0-9]"

error_ttl = list()


def analysis_preprocessing_2(start, end, l_min, l_max):
    data_prepreocessing = my.open_file_and_return_data(code=0, path=path_1)
    sent = 0
    error = 0
    received = 0
    l_2 = set()
    l_3 = 0
    for value in data_prepreocessing['messages']:
        if start <= dt.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S.%f') <= end:
            if l_min <= int(value['message_id']) <= l_max:
                if value['type_mex'] == 'S':
                    sent = sent + 1
                elif value['type_mex'] == 'P':
                    received = received + 1
                    l_2.add(int(value['message_id']))
                elif value['type_mex'] == 'E':
                    error = error + 1
            else:
                l_3 += 1

    print("Inviati: {}"
          "\nRicevuti: {}"
          "\nErrore: {}".format(sent, received, error))
    print("Mex non considerati: {}".format(l_3))
    return sent, received, error, l_2


def detect_time(data, new_start, new_end):
    start_ok = False
    end_ok = False
    d = {int(k): v for k, v in data['second_analysis'].items()}
    index = 1
    first_send = 0
    last_send = 0
    s1_datetime = ""
    while not start_ok:
        if int(index) in d:
            s1_datetime = dt.datetime.strptime(d[index]['send_time'], '%Y-%m-%d %H:%M:%S.%f')
            if (new_start - s1_datetime).total_seconds() < 5:
                print("new_start is {} --> {}".format(s1_datetime, index))
                first_send = index
                start_ok = True
        index += 1

    index = max(d, key=int)
    s2_datetime = ""
    s3_datetime = ""
    while not end_ok:
        if int(index) in d:
            s2_datetime = dt.datetime.strptime(d[index]['send_time'], '%Y-%m-%d %H:%M:%S.%f')
            if (s2_datetime - new_end).total_seconds() < 5:
                print("new_end is {} --> {}".format(s2_datetime, index))
                last_send = index
                s3_datetime = dt.datetime.strptime(d[index]['status_time'], '%Y-%m-%d %H:%M:%S.%f')
                print("new_end_correct [receive]: ", s3_datetime)
                diff_new = s3_datetime - s1_datetime
                h1, m1, s1 = my.convert_timedelta(diff_new)
                print("{}:{}.{} [mm:s.us]".format(m1, s1, diff_new.total_seconds()))
                end_ok = True
        index -= 1

    diff = s2_datetime - s1_datetime
    hours, minutes, seconds = my.convert_timedelta(diff)
    print("-----------------------------------")
    print("new_start: {}".format(s1_datetime))
    print("new_end {}".format(s2_datetime))
    print("{m}:{s}.{f} [mm:s.us]".format(m=minutes, s=seconds, f=diff.microseconds))
    print("-----------------------------------")
    start = s1_datetime
    end = s2_datetime
    min_diff = 100
    id_min = 0
    max_diff = 0
    id_max = 0
    new_data = dict()
    l_1 = set()
    for k, v in data['second_analysis'].items():
        s1 = dt.datetime.strptime(v['send_time'], '%Y-%m-%d %H:%M:%S.%f')
        if start <= s1 <= end:
            new_data[int(k)] = v
            l_1.add(int(k))
            if v['difference'] < min_diff:
                min_diff = v['difference']
                id_min = int(k)
            if v['difference'] > min_diff:
                max_diff = v['difference']
                id_max = int(k)

    print("Differeza min:{} [{}] --- max:{} [{}]".format(min_diff, id_min, max_diff, id_max))
    sent, received, error, l_2 = analysis_preprocessing_2(start=start, end=s3_datetime, l_min=first_send,
                                                          l_max=last_send)

    lost = sent - received - error
    lost_and_error = lost + error
    if (lost_and_error + received) != sent:
        raise Exception("Errore  conteggio")

    if received != len(new_data):
        raise Exception("ERORORE dimensioni---- received: {} couple: {}".format(received, len(new_data)))
    print(l_1.difference(l_2))
    print("[{}]s Delay: {}".format(diff.total_seconds(), ((s2_datetime - s1_datetime).total_seconds() / sent)))
    return new_data, start, end, s3_datetime, sent, received, error, lost, lost_and_error


def detect_packets(data, duration, percentage):
    delay = int(data['_command']['delay'])
    print("DELAY: {}ms".format(delay))
    formule = 0
    diff = 0
    if duration == "5m":
        formule = (5 * 60 * 1000) / delay
        formule_1 = (6 * 60 * 1000) / delay
        diff = formule_1 - formule
    elif duration == "6m":
        formule = (6 * 60 * 1000) / delay
    else:
        print("errore data_packets")
        return

    index_start = int(diff * int(percentage) / 100)
    index_end = int(index_start + formule)
    index_start += 1
    print("start_index: {} end_index {}".format(index_start, index_end))

    data_prepreocessing = my.open_file_and_return_data(code=0, path=path_1)

    sent = 0
    received = 0
    error = 0
    last_received_time = dt.datetime.strptime(data_prepreocessing['messages'][0]['time'], '%Y-%m-%d %H:%M:%S.%f')
    last_received_index = 0
    removed = 0
    time_start = ""
    time_end_sent = ""
    l_2 = set()
    for value in data_prepreocessing['messages']:
        if index_start <= int(value['message_id']) <= index_end:
            if value['type_mex'] == 'S':
                if int(value['message_id']) == index_start:
                    time_start = dt.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S.%f')
                    print("start_send: {} [{}]".format(time_start, value['message_id']))
                elif int(value['message_id']) == index_end:
                    time_end_sent = dt.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S.%f')
                    print("end_send: {} [{}]".format(time_end_sent, value['message_id']))
                sent = sent + 1
            elif value['type_mex'] == 'P':
                received = received + 1
                l_2.add(int(value['message_id']))
                if dt.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S.%f') > last_received_time:
                    last_received_time = dt.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S.%f')
                    last_received_index = value['message_id']
            elif value['type_mex'] == 'E':
                error = error + 1
        else:
            removed += 1

    time_end = last_received_time
    lost = sent - received - error
    lost_and_error = lost + error

    if (lost_and_error + received) != sent:
        raise Exception("Errore conteggio!")

    difference = time_end_sent - time_start
    hours, minutes, seconds = my.convert_timedelta(difference)
    print("-----------------------------------")
    print(
        "TIME experiment: start: {} end: {} --- {}:{}.{} [mm:s.us]".format(time_start, time_end_sent, minutes, seconds,
                                                                           difference.microseconds))
    print("Last received at: {}".format(time_end))
    difference_total = time_end - time_start
    hours, minutes, seconds = my.convert_timedelta(difference_total)
    print("TIME total: start: {} end: {} --- {}:{}.{} [mm:s.us]".format(time_start, time_end, minutes, seconds,
                                                                        difference_total.microseconds))

    print("-----------------------------------")
    print("end_received: {} - [{}]".format(last_received_time, last_received_index))
    print("Sent: {}\nReceived: {}\nError: {} Persi: {} [{} - comprende anche error]".format(sent, received, error, lost,
                                                                                            lost_and_error))
    print("Non considerati: {}".format(removed))
    print("-----------------------------------")

    min_diff = 100
    id_min = 0
    max_diff = 0
    id_max = 0
    new_data = dict()
    l_1 = set()
    for k, v in data['second_analysis'].items():
        s1 = dt.datetime.strptime(v['send_time'], '%Y-%m-%d %H:%M:%S.%f')
        if time_start <= s1 <= time_end_sent:
            new_data[int(k)] = v
            l_1.add(int(k))
            if v['difference'] < min_diff:
                min_diff = v['difference']
                id_min = int(k)
            if v['difference'] > min_diff:
                max_diff = v['difference']
                id_max = int(k)

    if received != len(new_data):
        print("ERORORE dimensioni---- received: {} couple: {}".format(received, len(new_data)))
    print(l_1.difference(l_2))
    print("[{}]s Delay: {}".format(difference.total_seconds(), ((time_end - time_start).total_seconds() / sent)))
    print("min_diff: {} [{}] \nmax_diff: {} [{}]".format(min_diff, id_min, max_diff, id_max))

    return new_data, time_start, time_end, time_end_sent, sent, received, error, lost, lost_and_error


def clean_data(data, approach):
    print("- {}".format(clean_data.__name__))
    start_datetime = dt.datetime.strptime(data['analysis']['test_time_first_time'], '%Y-%m-%d %H:%M:%S.%f')
    end_datetime = dt.datetime.strptime(data['analysis']['test_time_last_time'], '%Y-%m-%d %H:%M:%S.%f')
    difference_1 = (end_datetime - start_datetime) - dt.timedelta(minutes=5)
    sec_1 = int(math.ceil(difference_1.total_seconds() * 50 / 100))  # rimuovo il 65% all'inizio e 35% alla fine

    new_start = start_datetime + dt.timedelta(seconds=sec_1)
    new_end = new_start + dt.timedelta(minutes=5)
    diff_old = end_datetime - start_datetime
    h1, m1, s1 = my.convert_timedelta(diff_old)
    print("-----------------------------------")
    print("Start: {}  --> end: {}".format(start_datetime, end_datetime))
    print("{m1}:{s1}.{f1} [mm:s.us]".format(m1=m1, s1=s1, f1=diff_old.total_seconds()))
    print("-----------------------------------")

    sent = 0
    received = 0
    error = 0
    lost = 0
    lost_and_error = 0
    time_start = ""
    time_end = ""
    time_end_sent = ""
    new_data = dict()
    if approach == "time":
        new_data, time_start, time_end, time_end_sent, sent, received, error, lost, lost_and_error = detect_time(
            data=data,
            new_start=new_start,
            new_end=new_end)
    elif approach == "packets":
        new_data, time_start, time_end, time_end_sent, sent, received, error, lost, lost_and_error = detect_packets(
            data=data, duration="5m",
            percentage=65)
    else:
        print("Errore approach value")

    hours, minutes, seconds = my.convert_timedelta((time_end - time_start))
    test_time_m = str(minutes) + " M, " + str(seconds) + " s"
    hours, minutes, seconds = my.convert_timedelta((time_end_sent - time_start))
    test_time_sent_m = str(minutes) + " M, " + str(seconds) + " s"
    new_dataset = dict()
    new_dataset['_command'] = data['_command']
    new_dataset['last_analysis'] = data['analysis']
    new_dataset['analysis_value'] = {
        'inviati': sent,  # comprende tutti i mex inviati anche quello con errore
        'ricevuti': received,
        'errore': error,
        'persi': lost,
        'persi_e_error': lost_and_error,
        'time_start': time_start,
        'time_end': time_end,
        'time_end_sent': time_end_sent,
        'test_time_sent_m': test_time_sent_m,
        'test_time_m': test_time_m,
        'test_time_sent': (time_end - time_start).total_seconds(),
        'test_time': (time_end_sent - time_start).total_seconds()
    }
    new_dataset['couples'] = new_data
    print("-------")
    return new_dataset


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

    not_sent = not_sent + data['analysis']['packet_not_sent']
    data['analysis']['packet_sent'] = int(int(data['_command']['n_mex']) - not_sent)
    data['analysis']['packet_not_sent'] = int(not_sent)
    data['analysis']['packet_lost'] = int(lost)
    if len(list_lost) != 0 and len(list_lost) <= 20:
        data['analysis']['list_lost_mex_id'] = list_lost
    if len(list_not_sent) != 0 and len(list_not_sent) <= 20:
        data['analysis']['list_not_sent_mex_id'] = list_not_sent

    data['analysis_status'] = 3
    diff_mex_1 = int(data['_command']['n_mex']) - int(data['analysis']['packet_sent']) - data['analysis'][
        'packet_not_sent']
    diff_mex_2 = int(data['analysis']['packet_sent']) - int(data['analysis']['packet_received']) - int(
        data['analysis']['packet_lost'])
    print("Packet Sent: {}".format(data['analysis']['packet_sent']))
    print("Packet Received: {}".format(data['analysis']['packet_received']))
    print("Packet Lost: {}".format(data['analysis']['packet_lost']))
    print("Packet Not Sent: {}".format(data['analysis']['packet_not_sent']))
    print("Diff packets [total, sent, not_sent] --> {}".format(diff_mex_1))
    print("Diff packets [send, received, lost]  --> {}".format(diff_mex_2))

    if diff_mex_2 == 0 and diff_mex_1 == 0:
        print("\x1b[0;32;40m Correct analysis \x1b[0m")
    else:
        print("\x1b[0;31;40m Error about counting in analysis [lost, sent, received] difference: {}\x1b[0m".format(
            diff_mex_2))
    print("\x1b[1;34;40m addr:{a}, delay:{d} n_mex:{n} [RELAY: {r}]\x1b[0m".format(a=data['_command']['addr'],
                                                                                   d=data['_command']['delay'],
                                                                                   n=data['_command']['n_mex'],
                                                                                   r=relay))
    return data


def error_second_analysis(m_id, index, size_messages, new_dataset, messages):
    if index + 1 < size_messages:
        next_mex = messages[index + 1]
    else:
        # last message
        next_mex = messages[index]
    new_dataset['error_second_analysis'].append(
        {'index': int(m_id), 'next_mex': {'message_id': next_mex['message_id'],
                                          'type_mex': next_mex['type_mex']
                                          },
         'string': 'TimeOut or message not sent'})
    return new_dataset


# calcolo i tempi per ciascuna coppia di mex [sent --> received] e individuo eventuali errori [timeout, packet not set]
# definisco latency media del test
def second_analysis(data):
    print("- {}".format(second_analysis.__name__))
    # data = my.open_file_and_return_data(path=path)
    messages = data['messages']
    command = data['_command']

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
    packet_not_sent = 0
    differences = list()
    latencies = list()
    dict_analysis = dict()
    new_dataset = {'error_second_analysis': [], 'error_network_buffer': []}
    size_messages = len(messages)
    user_check = False
    error = False
    first_send = messages[0]['time']
    last_received = messages[0]['time']
    min_diff_string = ""
    max_diff_string = ""
    min_diff_time = ""
    max_diff_time = ""
    match_error = "^[E]$"
    list_error = list()
    for m_id in list_of_m_id:
        couple = my.get_mex_couple(messages, m_id)  # individuo le coppie di messaggi

        if len(couple) == 2:
            match_1, e_1, type_1 = my.look_into_element(messages[couple[0]])
            match_2, e_2, type_2 = my.look_into_element(messages[couple[1]])
            if not match_1 or not match_2:
                raise Exception('\x1b[1;31;40m' + ' Error: value unexpected about message_id: ' + e_1 + ' \x1b[0m')

            if analysis_string_check(match_error, messages[couple[0]]['type_mex'], messages[couple[1]]['type_mex']):
                if analysis_string_check("^[P]$", messages[couple[0]]['type_mex'], messages[couple[1]]['type_mex']):
                    print("erororre {}".format(messages[couple[1]]['type_mex']))

                if not user_check:
                    user_check = True
                # add to list 'error_network_buffer' an index about mex not sent
                new_dataset['error_network_buffer'].append(int(messages[couple[0]]['message_id']))
                packet_not_sent += 1

                # raise Exception('\x1b[1;31;40m' + ' Errors -->1 [' + messages[couple[0]]['type_mex'] + ']\x1b[0m')
            else:
                if type_1 == type_2:
                    raise Exception(
                        '\x1b[1;31;40m' + ' Error: couple with same type: ' + messages[couple[0]]['type_mex'] + ' - ' +
                        messages[couple[1]]['type_mex'] + ' \x1b[0m')
                if type_1:
                    send_time = messages[couple[0]]['time']
                    receive_time = messages[couple[1]]['time']
                    analysis_ttl(send_mex=messages[couple[0]]['ttl'], receive_mex=messages[couple[1]]['ttl'],
                                 time=receive_time)
                else:
                    receive_time = messages[couple[0]]['time']
                    send_time = messages[couple[1]]['time']
                    analysis_ttl(send_mex=messages[couple[1]]['ttl'], receive_mex=messages[couple[0]]['ttl'],
                                 time=receive_time)

                if first_send > send_time:
                    first_send = send_time
                if last_received < receive_time:
                    last_received = receive_time

                packet_received += 1
                send_datetime = dt.datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S.%f')
                receive_datetime = dt.datetime.strptime(receive_time, '%Y-%m-%d %H:%M:%S.%f')

                # timedelta output (days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
                # 1 millisecond --> 1000 microseconds
                difference = receive_datetime - send_datetime
                differences.append(difference.total_seconds())
                latencies.append(difference.total_seconds() / 2)

                dict_analysis[int(m_id)] = {
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
            new_dataset = error_second_analysis(m_id=m_id, index=couple[0], size_messages=size_messages,
                                                new_dataset=new_dataset, messages=messages)
        else:
            print("EROROR: {c} couple with same message_id [{id}]".format(id=m_id, c=len(couple)))
            for i in range(len(couple)):
                print("type_mex: {t_m}, mex_id: {m_id}, ttl: {ttl}, time: [{t}]".format(
                    m_id=messages[couple[i]]['message_id'], t=messages[couple[i]]['time'],
                    t_m=messages[couple[i]]['type_mex'], ttl=messages[couple[i]]['ttl']))
                error = True

    # print("Size: Duplicate message Received: {}".format(len(error_ttl)))
    if error:
        raise Exception("\x1b[1;31;40m Error second_analysis --> user_check \x1b[0m")

    first_datetime = dt.datetime.strptime(first_send, '%Y-%m-%d %H:%M:%S.%f')
    last_datetime = dt.datetime.strptime(last_received, '%Y-%m-%d %H:%M:%S.%f')
    test_time = last_datetime - first_datetime
    hours, minutes, seconds = my.convert_timedelta(test_time)
    mex_sent = int(data['_command']['n_mex']) - packet_not_sent
    print("--- Mex sent: {}".format(mex_sent))
    print("--- Mex sent and received: {}".format(packet_received))
    print("--- Mex not sent: {}".format(packet_not_sent))
    print("--- Tempo test: {}:{}.{} [mm:s.us]".format(minutes, seconds, test_time.microseconds))
    test_time_m = str(minutes) + " M, " + str(seconds) + " s"

    new_dataset['second_analysis'] = dict_analysis
    new_dataset['_command'] = data['_command']
    new_dataset['analysis'] = {
        'packet_received': int(packet_received),
        'packet_sent': int(mex_sent),
        'packet_not_sent': int(packet_not_sent),
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
    new_dataset['analysis_status'] = 2
    return new_dataset, user_check


def analysis_ttl(send_mex, receive_mex, time):
    send_ttl = "3"
    str_ttl = ["3", "2", "1"]
    if not str(send_mex) == send_ttl:
        raise Exception('\x1b[1;31;40m' + ' Error analysis_ttl --> send_: ' + time + '\x1b[0m')
    if not str(receive_mex) == str_ttl[relay]:
        error_ttl.append(time)
        raise Exception('\x1b[1;31;40m' + ' Error analysis_ttl --> receive_: ' + time + '\x1b[0m')


def analysis_string_check(pattern, string_1, string_2):
    if re.match(pattern=pattern, string=string_1):
        match_1 = True
    else:
        match_1 = False
    if re.match(pattern=pattern, string=string_2):
        match_2 = True
    else:
        match_2 = False
    return match_1 or match_2


def analysis_string(string, time_1, info):
    error = False
    try:
        check_string_mex(string)
    except Exception as e:
        print("Error: [{}] --> string: {} time: [{}]".format(info, e, time_1))
        error = True
    finally:
        return error


def check_string_mex(string):
    if not re.match("^[0-9]{1,5}$", string[1]) or not re.match("^[0-9]$", string[2]) or not re.match("^[R|S|P|E]$",
                                                                                                     string[0]):
        raise Exception('Error check: type: {}, id: {}, ttl: {}'.format(string[0], string[1], string[2]))


def update_data(data, index, string, t_1, info):
    error = analysis_string(string, t_1, info)
    data['messages'][index]['message_id'] = string[1]
    data['messages'][index]['type_mex'] = string[0]
    data['messages'][index]['ttl'] = string[2]
    return data, error


def add_element_to_data(data, string, time):
    data['messages'].append({
        'message_id': string[1],
        'type_mex': string[0],
        'ttl': string[2],
        'time': time
    })
    return data


def split_string_3(data, s_1, s_2, t_1, t_2, first_index, second_index, search):
    # print("1° item --> string: {} --> time: {}".format(s_1, t_1))
    # print("2° item --> string: {} --> time: {}".format(s_2, t_2))
    # print("\x1b[0;33;40m Split: {} \x1b[0m".format(search))
    # print("-----------")

    # Prendo il tempo relativo al first_index per il mex di send
    data, error = update_data(data=data, index=first_index, string=search[0].split(','), t_1=t_1, info="6")
    data, error = update_data(data=data, index=second_index, string=search[2].split(','), t_1=t_1, info="7")
    data = add_element_to_data(data=data, string=search[1].split(','), time=t_1)
    return data, error


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
        if errors[i]['#_comma'] % 2 == 0 and len(re.findall(find_all_matches, errors[i]['string'])) >= 2:
            list_split.append(i)
        else:
            list_union.append(i)

    only_update = list()
    error = False
    error_up_data = False
    for i in list_union:
        first_index = int(errors[i]['index'])
        if first_index not in list_1_remove_after_union and first_index not in only_update:
            j = i + 1
            if j < len(errors):
                second_index = int(errors[j]['index'])
                strings = errors[i]['string'] + errors[j]['string']  # concateno le due stringhe
                if second_index - first_index == 1:
                    my_time = errors[i]['time']
                    if re.match(regular_expression_mex, strings):
                        data, error_up_data = update_data(data, first_index, strings.split(','), my_time, "1")
                        list_1_remove_after_union.append(second_index)
                    else:
                        search = re.findall(find_all_matches, strings)
                        if len(search) == 1:
                            data, error_up_data = update_data(data, first_index, search[0].split(','), my_time, "2")
                            list_1_remove_after_union.append(second_index)
                        elif len(search) == 2:
                            data, error_up_data = update_data(data, first_index, search[0].split(','), my_time, "3")
                            data, error_up_data = update_data(data, second_index, search[1].split(','), my_time, "4")
                            only_update.append(second_index)
                        elif len(search) == 3:
                            data, error_up_data = split_string_3(data=data, s_1=errors[i]['string'],
                                                                 s_2=errors[j]['string'],
                                                                 t_1=errors[i]['time'], t_2=errors[j]['time'],
                                                                 first_index=first_index,
                                                                 second_index=second_index, search=search)
                            only_update.append(second_index)
                        else:
                            error = True
                            print("ERRORE [{} - {}] len:{} {}".format(first_index, second_index, len(search), search))
                else:
                    error = True
                    print("\x1b[1;31;40m Error with couple: {} - {} \x1b[0m string: [{}], time: [{}]".format(
                        first_index, second_index, strings, errors[i]['time']))
                    print("---------------")
        if error_up_data:
            error = True

    for i in list_split:
        index = int(errors[i]['index'])
        strings = errors[i]['string']
        time = errors[i]['time']
        search = re.findall(find_all_matches, strings)
        if len(search) > 2:
            print("long string: ", strings, " time: ", time)
        for j in range(len(search)):
            if j == 0:
                data, error_up_data = update_data(data, index, search[j].split(','), time, "5")
            else:
                data = add_element_to_data(data=data, string=search[j].split(','), time=time)
        if error_up_data:
            error = True

    list_1_remove_after_union.sort(reverse=True)
    for i in list_1_remove_after_union:
        del data['messages'][i]

    if not error:
        errors.clear()
    else:
        raise Exception("\x1b[1;31;40m Error resolve_errors_preprocessing \x1b[0m")

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
    print("\x1b[1;34;40m addr:{a}, delay:{d} n_mex:{n} [RELAY: {r}]\x1b[0m".format(a=data['_command']['addr'],
                                                                                   d=data['_command']['delay'],
                                                                                   n=data['_command']['n_mex'],
                                                                                   r=relay))
    for i, mex in enumerate(data['messages']):
        if not re.match(regular_expression_mex, mex['message_id']):
            counter = mex['message_id'].count(',')
            data['error_first_analysis'].append(
                {'index': i, '#_comma': counter, 'time': mex['time'], 'string': mex['message_id']})
            if not check:
                check = True
        else:
            string = mex['message_id']
            string = string.split(',')
            check_string_mex(string)
            mex['message_id'] = string[1]
            mex['type_mex'] = string[0]
            mex['ttl'] = string[2]

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


def call_fourth_analysis_and_save(path_s):
    data = my.open_file_and_return_data(code=0, path=path_2)
    data = clean_data(data=data, approach="packets")  # packets or time
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

    # Fourth Analysis --> clean data use only 5 minutes
    call_fourth_analysis_and_save(path_s=analysis_2_path)


def new_task():
    # Fourth Analysis --> clean data use only 5 minutes
    call_fourth_analysis_and_save(path_s=analysis_2_path)


if __name__ == "__main__":
    try:
        testing_phase()
    except Exception as e:
        print(e)
