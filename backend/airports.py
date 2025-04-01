# One List with Searchable cities
# ICAO unique
# IATA not all

import json

filename = "airports.json"
with open(filename,  'r') as f:
    airports = json.load(f)

airport_ids = {}
n = len(airports)
for  i, (key, item) in enumerate(airports.items()):
    if len(item['iata']) >0:
        airport_ids[item['iata']] = [key]
    if item['city'] not in airport_ids:
        airport_ids[item['city']] = [key]
    else:
        airport_ids[item['city']].append(key)
    print(f'{key} - {str(i+1).zfill(5)}/{n}')


output = "airport_ids.json"
print(airport_ids)
with open(output,  'w') as f:
    json.dump(airport_ids,f)
