import emilio_function as my
import re


def get_sent_mex(path):
    data = my.open_file_and_return_data(path=path)
    mex = data['messages']

    set_element = set()
    for item in mex:
        if item['type_mex'] == "S":
            set_element.add(int(item['message_id']))
    print("SENT MEX: {}".format(len(set_element)))
    return set_element


def get_received_mex(path):
    data = my.open_file_and_return_data(path=path)

    set_element = set()
    for item in data['messages']:
        s = re.findall("level: [0-9]{1,5}", item['message_id'])
        s = s[0].split(':')[1]
        s = s.replace(' ', '')
        set_element.add(int(s))
    print("RECEIVED MEX: {}".format(len(set_element)))
    return set_element


def operation_with_set(sent, received):
    diff = sent.difference(received)
    print("Difference: len: {}".format(len(diff)))



def main():
    # path = my.get_argument()
    path = "./json_file/test_2019_12_10/test_19_12_10-09_21_16_analysis.json"
    sent_mex = get_sent_mex(path=path)

    path = "./json_file/test_2019_12_10/json_rasp_19_12_10-09_21_16.json"
    received_mex = get_received_mex(path=path)

    operation_with_set(sent=sent_mex, received=received_mex)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
