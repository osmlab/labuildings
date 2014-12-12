# chunk.py
# Exports intersections between two shapefile's objects as separate files.
from fiona import collection
from rtree import index
from shapely.geometry import asShape
from shapely import speedups
from sys import argv
from pprint import pprint

speedups.enable()

# Exports given features into shapefiles by sections
def chunk(featureFileName, sectionFileName, pattern, key = None):

    # Load and index
    with collection(featureFileName, "r") as featureFile:
        featureIdx = index.Index()
        features = []
        for feature in featureFile:
            features.append(feature)
            featureIdx.add(len(features) - 1, asShape(feature['geometry']).bounds)

        # Break up by sections and export
        with collection(sectionFileName, "r") as sectionFile:
            i = 0
            for section in sectionFile:
                fileName = pattern % i
                if key:
                    fileName = pattern % section['properties'][key]
                    properties = {}
                    try:
                        with collection(fileName, 'w', 'ESRI Shapefile',
                                schema = featureFile.schema,
                                crs = featureFile.crs) as output:
                            sectionShape = asShape(section['geometry'])
                            for j in featureIdx.intersection(sectionShape.bounds):
                                if asShape(features[j]['geometry']).intersects(sectionShape):
                                    properties = features[j]['properties']
                                    output.write(features[j])
                            print "Exported %s" % fileName
                            i = i + 1
                    except ValueError:
                        print "Error exporting " + fileName
                        pprint(properties)
                        pprint(featureFile.schema)


usage = """
chunk.py
========

Exports intersections between two shapefile's objects as separate files.

Usage: python chunk.py featuresfile sectionfile outputfilepattern [attributekey]

Example:

python chunk.py manysmallfeatures.shp sections.shp export/features-by-section-%s.shp

If you specify an attribute key that can be found in the sections file it will be used for naming output files:

python chunk.py manysmallfeatures.shp sections.shp export/features-by-section-%s.shp STATECODE
"""

if len(argv) == 4:
    chunk(argv[1], argv[2], argv[3])
elif len(argv) == 5:
    chunk(argv[1], argv[2], argv[3], argv[4])
else:
    print usage
