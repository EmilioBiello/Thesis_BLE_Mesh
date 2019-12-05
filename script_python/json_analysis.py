import json
import datetime as dt
import statistics
import emilio_function as my


def third_analysis(path):
    with open(path) as json_file:
        data = json.load(json_file)
        errors = data['error_second_analysis']

    if data['analysis_status'] != 2:
        raise BaseException('Phase 3 already executed')

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
                    print("Packet {} --> not sent".format(item['index']))
                    data['error_second_analysis'][i]['string'] = "Message not sent"
                    list_not_sent.append(int(item['index']))
                else:
                    lost += 1
                    print("Packet {} --> TIMEOUT".format(item['index']))
                    data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
                    list_lost.append(int(item['index']))
            else:
                lost += 1
                print("Packet {} --> TIMEOUT".format(item['index']))
                data['error_second_analysis'][i]['string'] = "Error, TIMEOUT"
                list_lost.append(int(item['index']))
            last = int(item['index'])

    data['analysis']['sent_mex'] = int(int(data['command']['n_mex']) - not_sent)
    data['analysis']['lost_packet'] = int(lost)
    data['analysis']['list_lost'] = list_lost
    data['analysis']['list_not_sent'] = list_not_sent

    # print_dict_as_json(data)
    data['analysis_status'] = 3
    if int(data['analysis']['sent_mex']) - int(data['analysis']['received_mex']) - int(
            data['analysis']['lost_packet']) == 0:
        print("Correct analysis")
    else:
        print("Error about counting in analysis [lost, sent, received]")
    return data


def second_analysis(path):
    check_utente = False
    with open(path) as json_file:
        data = json.load(json_file)
        command = data['command']
        messages = data['messages']

    if len(data['error_first_analysis']) > 0:
        raise Exception('Error First Analysis not empty')

    if data['analysis_status'] != 1:
        raise BaseException('Phase 2 already executed')

    received_mex = 0

    list_of_m_id = list()
    for item in messages:
        list_of_m_id.append(item['message_id'])

    list_of_m_id = list(dict.fromkeys(list_of_m_id))  # definisco una lista contenente i message_id
    if '0' in list_of_m_id:
        list_of_m_id.remove('0')

    differences = list()
    latencies = list()
    dict_analysis = dict()
    data['error_second_analysis'] = []
    size_messages = len(messages)
    for m_id in list_of_m_id:
        couple = my.get_same_element_index(messages, m_id)  # individuo le coppie di messaggi

        if len(couple) == 2:
            received_mex += 1
            send_time = messages[couple[0]]['time']
            receive_time = messages[couple[1]]['time']

            send_datetime = dt.datetime.strptime(send_time, '%Y-%m-%d %H:%M:%S.%f')
            receive_datetime = dt.datetime.strptime(receive_time, '%Y-%m-%d %H:%M:%S.%f')

            # timedelta output (days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            # 1 millisecond --> 1000 microseconds
            difference = receive_datetime - send_datetime
            differences.append(difference.total_seconds())
            latencies.append(difference.total_seconds() / 2)

            dict_analysis[m_id] = {
                'time_send': send_time,
                'time_ack': receive_time,
                'difference': difference.total_seconds(),
                'latency': (difference.total_seconds() / 2)
            }
            # print("m_id: {} --> {}".format(m_id, dict_analysis[m_id]['difference']))
        elif len(couple) == 1:
            if not check_utente:
                check_utente = True
            if couple[0] + 1 < size_messages:
                next_mex = messages[couple[0] + 1]
                data['error_second_analysis'].append({'index': m_id, 'next_mex': {'message_id': next_mex['message_id'],
                                                                                  'type_mex': next_mex['type_mex']
                                                                                  },
                                                      'string': 'TimeOut or message not sent'})
            else:
                data['error_second_analysis'].append({'index': m_id, 'string': 'TimeOut or message not sent'})

            # print("m_id: {} --> TimeOut or message not sent".format(m_id))

    data['second_analysis'] = dict_analysis
    data['analysis'] = {
        'received_mex': int(received_mex),
        'average_diff': statistics.mean(differences) * 1000,  # milliseconds
        'average_latency': statistics.mean(latencies) * 1000  # milliseconds
    }
    data['analysis_status'] = 2
    return data, check_utente


def first_analysis(path):
    check = False
    with open(path) as json_file:
        data = json.load(json_file)

        if data['analysis_status'] != 0:
            raise BaseException('Phase 1 already executed')

        data['error_first_analysis'] = []
        for mex in data['messages']:
            if mex['len'] != 5 and mex['len'] != 6:
                data['error_first_analysis'].append({'time': mex['time'], 'string': mex['message_id']})
                if not check:
                    check = True
            else:
                m_id = mex['message_id'].split(',')[1]
                type_mex = mex['message_id'].split(',')[0]
                ttl_mex = mex['message_id'].split(',')[2]

                mex['message_id'] = m_id
                mex['type_mex'] = type_mex
                mex['ttl'] = ttl_mex

        data['analysis_status'] = 1
        return data, check


def main():
    checks = False
    path = my.get_file_from_directory('json_file/*.json')

    try:
        my_data, checks = first_analysis(path=path)
        my.save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        input("Richiesto intervento poiché c'è un errore, analizzare \'error_first_analysis\'")
    else:
        print("Fase 1 completata")

    try:
        my_data, checks = second_analysis(path=path)
        my.save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        print("Ci sono dei pacchetti persi, analizzare \'error_second_analysis\'")
    else:
        print("Fase 1 completata")


def main2():
    path = "./json_file/json_data_19-12-03_13-24.json"
    checks = False

    try:
        my_data, checks = first_analysis(path=path)
        my.save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)

    if checks:
        raise Exception("Richiesto intervento poiché c'è un errore, analizzare \'error_first_analysis\'")
    else:
        print("Fase 1 completata")

    try:
        my_data, checks = second_analysis(path=path)
        my.save_json_data(path=path, data=my_data)
    except Exception as e:
        print(e)
        raise Exception('Check error_first_analysis before continuous')
    except BaseException as e:
        print(e)

    if checks:
        print("Ci sono dei pacchetti persi, analizzare \'error_second_analysis\'")
    else:
        print("Fase 2 completata")

    try:
        my_data = third_analysis(path=path)
        my.save_json_data(path=path, data=my_data)
    except BaseException as e:
        print(e)
    print("Fase 3 completata")


if __name__ == "__main__":
    try:
        main2()
    except Exception as e:
        print(e)
