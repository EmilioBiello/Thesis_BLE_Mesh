import json

# Python Object (Dictionary)
x = {"name": "John", "age": 30, "city": "New York"}

# Convert into JSON:
y = json.dumps(x)

print(y)

# parse x:
w = json.loads(y)

# the result is a Python dictionary:
print(w["age"])
print("---------------------------------------------------------------------------------------------------------------")

print(" --- Writing JSON to a File --- ")
import datetime

data = {}


def update_data(name, website, country, now):
    if not bool(data):
        data['people'] = []

    data['people'].append({
        'name': name,
        'website': website,
        'from': country,
        'datetime': now
    })


update_data('Scott', 'stackabuse.com', 'Nebraska', datetime.datetime.now())
update_data('Larry', 'google.com', 'Michigan', datetime.datetime.now())
update_data('Tim', 'apple.com', 'Alabama', datetime.datetime.now())


# data['people'].append({
#     'name': 'Scott',
#     'website': 'stackabuse.com',
#     'from': 'Nebraska',
#     'datetime': datetime.datetime.now()
# })
# data['people'].append({
#     'name': 'Larry',
#     'website': 'google.com',
#     'from': 'Michigan',
#     'datetime': datetime.datetime.now()
# })
# data['people'].append({
#     'name': 'Tim',
#     'website': 'apple.com',
#     'from': 'Alabama',
#     'datetime': datetime.datetime.now()
# })


# Allow to serialize datetime into JSON string
def convert_timestamp(item_data_object):
    if isinstance(item_data_object, datetime.datetime):
        return item_data_object.__str__()


with open('data.json', 'w') as outfile:
    json.dump(data, outfile, default=convert_timestamp, sort_keys=True, indent=4)

print("---------------------------------------------------------------------------------------------------------------")

print(" --- Reading JSON from a File --- ")

with open('data.json') as json_file:
    data = json.load(json_file)

    for p in data['people']:
        print('Name: ' + p['name'])
        print('Website: ' + p['website'])
        print('From: ' + p['from'])
        print('Datetime: ' + p['datetime'])
        print('')

    # Read a datetime from file as String and convert to datetime object
    date_time_str = (data['people'][0]['datetime'])
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    print("-------")

    print('Date:', date_time_obj.date())
    print('Time:', date_time_obj.time())
    print('Date-time:', date_time_obj)
