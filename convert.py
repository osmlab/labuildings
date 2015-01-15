# Convert LA building footprints and addresses into importable OSM files.
from lxml import etree
from lxml.etree import tostring
from shapely.geometry import asShape, Point, LineString
from sys import argv, exit, stderr
from glob import glob
from merge import merge
import re
from decimal import Decimal, getcontext
from multiprocessing import Pool
import json
from rtree import index
import ntpath

# Adjust precision for buffer operations
getcontext().prec = 16

# Converts given buildings into corresponding OSM XML files.
def convert(buildingsFile, osmOut):
    with open(buildingsFile) as f:
        features = json.load(f)
    allAddresses = []
    buildings = []
    buildingShapes = []
    buildingIdx = index.Index()
    for feature in features:
        if feature['geometry']['type'] == 'Polygon' or feature['geometry']['type'] == 'MultiPolygon':
            buildings.append(feature)
            shape = asShape(feature['geometry'])
            buildingShapes.append(shape)
            buildingIdx.add(len(buildingShapes) - 1, shape.bounds)
        elif feature['geometry']['type'] == 'Point':
            allAddresses.append(feature)

        else:
            print "geometry of unknown type:", feature['geometry']['type']

    # Generates a new osm id.
    osmIds = dict(node = -1, way = -1, rel = -1)
    def newOsmId(type):
        osmIds[type] = osmIds[type] - 1
        return osmIds[type]

    ## Formats multi part house numbers
    def formatHousenumber(p):
        def suffix(part1, part2, hyphen_type=None):
            #part1 = stripZeroes(part1)
            if not part2:
                return str(part1)
            #part2 = stripZeroes(part2)
            return str(part1) + ' ' + str(part2)
        #def stripZeroes(addr): # strip leading zeroes from numbers
        #    if addr.isdigit():
        #        addr = str(int(addr))
        #    if '-' in addr:
        #        try:
        #            addr2 = addr.split('-')
        #            if len(addr2) == 2:
        #                addr = str(int(addr2[0])) + '-' + str(int(addr2[1])).zfill(2)
        #        except:
        #            pass
        #    return addr
        number = suffix(p['Number'], p['NumSuffix'])
        if p['NumPrefix']:
            number = p['NumPrefix'] + number
        return number

    # Converts an address
    def convertAddress(address):
        result = dict()
        if all (k in address for k in ('Number', 'StreetName')):
            if address['Number']:
                result['addr:housenumber'] = formatHousenumber(address)
            if address['StreetName']:

                # Titlecase
                streetname = address['StreetName'].title()
                if address['StArticle']:
                    streetname = address['StArticle'].title() + " " + streetname
                if address['PreType']:
                    streetname = address['PreType'].title() + " " + streetname
                if address['PreDir']:
                    streetname = address['PreDir'].title() + " " + streetname
                if address['PreMod']:
                    streetname = address['PreMod'].title() + " " + streetname
                if address['PostType']:
                    streetname = streetname + " " + address['PostType'].title()
                if address['PostDir']:
                    streetname = streetname + " " + address['PostDir'].title()
                if address['PostMod']:
                    streetname = streetname + " " + address['PostMod'].title()

                # Fix titlecase on 1St, 2Nd, 3Rd, 4Th, etc
                streetname = re.sub(r"(.*)(\d+)St\s*(.*)", r"\1\2st \3", streetname)
                streetname = re.sub(r"(.*)(\d+)Nd\s*(.*)", r"\1\2nd \3", streetname)
                streetname = re.sub(r"(.*)(\d+)Rd\s*(.*)", r"\1\2rd \3", streetname)
                streetname = re.sub(r"(.*)(\d+)Th\s*(.*)", r"\1\2th \3", streetname)

                # Expand 'St ' -> 'Saint'
                # relevant for:
                #   'St Clair'
                #   'St Louis'
                #   'St James'
                #   'St James Park'
                #   'St Andrews'
                #   'St Nicolas'
                #   'St Cloud'
                #   'St Ambrose'
                #   'St Bonaventure'
                #   'St Joseph'
                #   'St Tropez'
                if streetname[0:3] == 'St ': streetname = 'Saint ' + streetname[3:]
                # Middle name expansions
                streetname = streetname.replace(' St ', ' Street ')
                streetname = streetname.replace(' Rd ', ' Road ')
                streetname = streetname.replace(' Blvd ', ' Boulevard ')
                result['addr:street'] = streetname
            if address['PCITY1']:
                result['addr:city'] = address['PCITY1'].title()
            elif address['LegalComm']:
                result['addr:city'] = address['LegalComm'].title()
            if address['ZipCode']:
                result['addr:postcode'] = str(int(address['ZipCode']))
            if address['UnitName']:
                result['addr:unit'] = address['UnitName']
        return result

    # Appends new node or returns existing if exists.
    nodes = {}
    def appendNewNode(coords, osmXml):
        rlon = int(float(coords[0]*10**7))
        rlat = int(float(coords[1]*10**7))
        if (rlon, rlat) in nodes:
            return nodes[(rlon, rlat)]
        node = etree.Element('node', visible = 'true', id = str(newOsmId('node')))
        node.set('lon', str(Decimal(coords[0])*Decimal(1)))
        node.set('lat', str(Decimal(coords[1])*Decimal(1)))
        nodes[(rlon, rlat)] = node
        osmXml.append(node)
        return node

    def appendNewWay(coords, intersects, osmXml):
        way = etree.Element('way', visible='true', id=str(newOsmId('way')))
        firstNid = 0
        for i, coord in enumerate(coords):
            if i == 0: continue # the first and last coordinate are the same
            node = appendNewNode(coord, osmXml)
            if i == 1: firstNid = node.get('id')
            way.append(etree.Element('nd', ref=node.get('id')))

            # Check each way segment for intersecting nodes
            int_nodes = {}
            try:
                line = LineString([coord, coords[i+1]])
            except IndexError:
                line = LineString([coord, coords[1]])
            for idx, c in enumerate(intersects):
                if line.buffer(0.000001).contains(Point(c[0], c[1])) and c not in coords:
                    t_node = appendNewNode(c, osmXml)
                    for n in way.iter('nd'):
                        if n.get('ref') == t_node.get('id'):
                            break
                    else:
                        int_nodes[t_node.get('id')] = Point(c).distance(Point(coord))
            for n in sorted(int_nodes, key=lambda key: int_nodes[key]): # add intersecting nodes in order
                way.append(etree.Element('nd', ref=n))
            
        way.append(etree.Element('nd', ref=firstNid)) # close way
        osmXml.append(way)
        return way

    # Appends an address to a given node or way.
    def appendAddress(address, element):
        for k, v in convertAddress(address['properties']).iteritems():
            element.append(etree.Element('tag', k=k, v=v))

    # Appends a building to a given OSM xml document.
    def appendBuilding(building, shape, address, osmXml):
        # Check for intersecting buildings
        intersects = []
        for i in buildingIdx.intersection(shape.bounds):
            try:
                for c in buildingShapes[i].exterior.coords:
                    if Point(c[0], c[1]).buffer(0.000001).intersects(shape):
                        intersects.append(c)
            except AttributeError:
                for c in buildingShapes[i][0].exterior.coords:
                    if Point(c[0], c[1]).buffer(0.000001).intersects(shape):
                        intersects.append(c)

        # Export building, create multipolygon if there are interior shapes.
        interiors = []
        try:
            way = appendNewWay(list(shape.exterior.coords), intersects, osmXml)
            for interior in shape.interiors:
                interiors.append(appendNewWay(list(interior.coords), [], osmXml))
        except AttributeError:
            way = appendNewWay(list(shape[0].exterior.coords), intersects, osmXml)
            for interior in shape[0].interiors:
                interiors.append(appendNewWay(list(interior.coords), [], osmXml))
        if len(interiors) > 0:
            relation = etree.Element('relation', visible='true', id=str(newOsmId('way')))
            relation.append(etree.Element('member', type='way', role='outer', ref=way.get('id')))
            for interior in interiors:
                relation.append(etree.Element('member', type='way', role='inner', ref=interior.get('id')))
            relation.append(etree.Element('tag', k='type', v='multipolygon'))
            osmXml.append(relation)
            way = relation
        way.append(etree.Element('tag', k='building', v='yes'))
        if 'HEIGHT' in building['properties']:
            height = round(((building['properties']['HEIGHT'] * 12) * 0.0254), 1)
            if height > 0:
                way.append(etree.Element('tag', k='height', v=str(height)))
        if 'ELEV' in building['properties']:
            height = round(((building['properties']['ELEV'] * 12) * 0.0254), 1)
            if height > 0:
                way.append(etree.Element('tag', k='elevation', v=str(height)))
        if 'BLD_ID' in building['properties']:
            way.append(etree.Element('tag', k='lacounty:bld_id', v=str(building['properties']['BLD_ID'])))
        if address: appendAddress(address, way)

    # Export buildings & addresses. Only export address with building if there is exactly
    # one address per building. Export remaining addresses as individual nodes.
    osmXml = etree.Element('osm', version='0.6', generator='alex@mapbox.com')
    for i in range(0, len(buildings)):

        buildingAddresses = []
        for address in buildings[i]['properties']['addresses']:
            buildingAddresses.append(address)
        address = None
        if len(buildingAddresses) == 1:
            address = buildingAddresses[0]
        else:
            allAddresses.extend(buildingAddresses)

        appendBuilding(buildings[i], buildingShapes[i], address, osmXml)


    # Export any addresses that aren't the only address for a building.
    if (len(allAddresses) > 0):
        for address in allAddresses:
            node = appendNewNode(address['geometry']['coordinates'], osmXml)
            appendAddress(address, node)

    with open(osmOut, 'w') as outFile:
        outFile.writelines(tostring(osmXml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print 'Exported ' + osmOut

def prep(fil3):
    matches = re.match('^(.*)\..*?$', ntpath.basename(fil3)).groups(0)
    convert(fil3, 'osm/%s.osm' % matches[0])

if __name__ == '__main__':
    pool = Pool()
    pool.map(prep, argv[1:])
    pool.close()
    pool.join()
