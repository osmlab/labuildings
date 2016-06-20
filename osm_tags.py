import csv, json
from os.path import join

CSV_PATH = 'mappings_csv/'
GENERAL_USE_CSV = open(join(CSV_PATH, 'GeneralUse.csv'))
SPECIFIC_1_CSV = open(join(CSV_PATH, 'Specific_1.csv'))
SPECIFIC_USE_CSV = open(join(CSV_PATH, 'SpecificUs.csv'))

mappings = {}


def csv_to_json(mapping_name, csv_file):
    reader = csv.reader(csv_file)
    reader.next()  # skip header row
    mappings[mapping_name] = {}
    for row in reader:
        # print row
        if row[1] != '' and row[2] != '':
            mappings[mapping_name][row[0]] = {
                'key1': row[1],
                'val1': row[2]
            }
            if len(row) == 5:
                if row[3] != '' and row[4] != '':
                    mappings[mapping_name][row[0]] = {
                        'key2': row[3],
                        'val2': row[4]
                    }
            if len(row) == 7:
                if row[5] != '' and row[6] != '':
                    mappings[mapping_name][row[0]] = {
                        'key3': row[4],
                        'val3': row[5]
                    }
    # print mappings

csv_to_json('GeneralUse', GENERAL_USE_CSV)
csv_to_json('Specific_1', SPECIFIC_1_CSV)
csv_to_json('SpecificUs', SPECIFIC_USE_CSV)

# print json.dumps(mappings, indent=2)


def get_osm_tags(feature):
    osm_tags = {
        'building': 'yes'
    }
    props = feature['properties']
    order = ['GeneralUse', 'Specific_1', 'SpecificUs']
    for o in order:
        if props.has_key(o) and props[o] is not None:
            if mappings[o].has_key(props[o]):
                key = mappings[o][props[o]]['key1']
                val = mappings[o][props[o]]['val1']
                osm_tags[key] = val
    return osm_tags
