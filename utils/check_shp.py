from fiona import collection
from shapely.geometry import asShape
import json
import sys


def check_file(filename):
    with collection(filename, 'r') as features:
        for feature in features:
            try:
                shape = asShape(feature['geometry'])
                if not shape.is_valid:
                    geometry = json.dumps(feature, indent=2)
                    print "Invalid geometry:\n"
                    print geometry
                    print '\n'
            except:
                print "Error parsing:\n"
                print json.dumps(feature, indent=2)


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except:
        print "Usage: python check_shp.py <filename>"
        print "Example: python check_shp.py buildings.shp"
        sys.exit(1)
    check_file(filename)

