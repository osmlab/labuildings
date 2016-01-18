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

debug = True

# Adjust precision for buffer operations
getcontext().prec = 16

# Converts given buildings into corresponding OSM XML files.
def convert(buildingsFile, osmOut):
    with open(buildingsFile) as f:
        features = json.load(f)
    allAddresses = {}
    buildings = []
    buildingShapes = []
    buildingIdx = index.Index()

    # Returns the coordinates for this address
    def keyFromAddress(address):
        return str(address['geometry']['coordinates'][0]) + "," + str(address['geometry']['coordinates'][1])

    for feature in features:
        if feature['geometry']['type'] == 'Polygon' or feature['geometry']['type'] == 'MultiPolygon':
            buildings.append(feature)
            shape = asShape(feature['geometry'])
            buildingShapes.append(shape)
            buildingIdx.add(len(buildingShapes) - 1, shape.bounds)

        # These are the addresses that don't overlap any buildings
        elif feature['geometry']['type'] == 'Point':
        # The key is the coordinates of this address. Track how many addresses share these coords.
            key = keyFromAddress(feature)
            if key in allAddresses:
                allAddresses[key].append(feature)
            else:
                allAddresses[key] = [feature]

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

    # Distills coincident addresses into one address where possible.
    # Takes an array of addresses and returns an array of 1 or more addresses
    def distillAddresses(addresses):
        # Only distill addresses if the following conditions are true:
        # 1) the addresses share the same coordinates.
        # AND
        # 2a) all the attributes are the same _except_ the unit number/name
        # OR
        # 2b) the street number is the same but the street names are referring to the same thing

        outputAddresses = []

        # First, group the addresses into separate lists for each unique location
        addressesByCoords = {}
        for address in addresses:
            key = keyFromAddress(address)
            if key in addressesByCoords:
                addressesByCoords[key].append(address)
            else:
                addressesByCoords[key] = [address]

        # loop over unique coordinates
        for key in addressesByCoords:
            # Here see if we can collapse any of these addresses at the same coords.

            # addressesByCoords[key] is an array of addresses at this location.

            # We are only looking for the 2 possibilities above (2a) and (2b).
            # If the situation is more complicated, change nothing.
            outputAddresses.extend(distillAddressesAtPoint(addressesByCoords[key]))

        return outputAddresses

    # This function is called by distillAddresses.
    # It assumes all addresses are at the same coordinates.
    # Returns an array of 1 or more addresses
    def distillAddressesAtPoint(addresses):

        if len(addresses) == 1:
            return addresses

        firstAddress = addresses[0]

        # (2a) If the first address is an apartment, see if all the rest are too.

        # NOTE: sometimes an apartment building has a few address points that lack a UnitName...
        # ...so checking for the presence of UnitName in firstAddress wouldn't always work.
        props = firstAddress['properties']
        if debug: print "Testing to see if these are apartments...", '\t'.join([str(props['Number']), str(props['NumSuffix']), str(props['PreType']), str(props['StreetName']), str(props['PostType']), str(props['UnitName'])])
        # Compare subsequent addresses in the array to the first address.
        # Hence, range starts at 1.
        for i in range(1, len(addresses)):
            if not areSameAddressExceptUnit(firstAddress, addresses[i]):
                props = addresses[i]['properties']
                if debug: print "No, this address was different...........", '\t'.join([str(props['Number']), str(props['NumSuffix']), str(props['PreType']), str(props['StreetName']), str(props['PostType']), str(props['UnitName'])])
                #print firstAddress
                #print addresses[i]
                break
            # else, keep going

        else: # else for the `for` statement. Executes only if `break` never did.
            # We checked them all, and they're all the same except UnitName.
            # In this case the apartment data is useless to OSM because the
            # apartment nodes are all on top of each other.
            # So, discard the unit information and return just one address.
            firstAddress['properties']['UnitName'] = None
            if debug: print "Yes they were apartments! Collapsed", len(addresses), "into one"
            return [firstAddress]

        # (2b) Check if the street number is all the same.
        # For this, we use a list of alternative names (like HWY 1, etc)...
        # ...and we need to know which canonical name to keep.
        if debug: print "Testing to see if the street names are synonyms.."
        canonicalStreetName = None
        for i in range(1, len(addresses)):
            props = addresses[i]['properties']
            if not areSameAddressExceptStreet(firstAddress, addresses[i]):
                if debug: print "No, this address was different...........", '\t'.join([str(props['Number']), str(props['NumSuffix']), str(props['PreType']), str(props['StreetName']), str(props['PostType']), str(props['UnitName'])])
                #print firstAddress
                #print addresses[i]
                break
            compoundStreetName = (str(props['PreType']),str(props['StreetName']),str(props['PostType']))
            currentCanonicalStreetName = getCanonicalName(compoundStreetName)
            if currentCanonicalStreetName:
                if debug: print "found canonical name", currentCanonicalStreetName
                if ((currentCanonicalStreetName == canonicalStreetName) or (canonicalStreetName == None)):
                    canonicalStreetName = currentCanonicalStreetName
                else:
                    if debug: print "canonicalStreetNames didn't match:", canonicalStreetName, currentCanonicalStreetName
                    break
            else:
                print "couldn't find canonicalStreetName for", compoundStreetName
                break

        else: # else for the `for` statement. Executes only if `break` never did.
            # We checked them all, and they're all the same except StreetName.
            # If we can determine that they are all the same synonym, we can
            # overwrite the other streetname information and return just one address.
            firstAddress['properties']['PreType'] = canonicalStreetName[0]
            firstAddress['properties']['StreetName'] = canonicalStreetName[1]
            firstAddress['properties']['PostType'] = canonicalStreetName[2]
            if debug: print "Yes they were synonyms! Collapsed", len(addresses), "into one"
            return [firstAddress]

        # This is only excuted if neither of the two `else` statements executed 
        # for the two `for` statements above. That means we were unable to collapse
        # separate apartments into one, or collapse synonymous street names into one.
        # So, instead of returning just one address, we fail and return all of them.
        return addresses

    def areSameAddressExceptUnit(a1, a2):
        for key in ['NumPrefix', 'Number', 'NumSuffix', 'PreMod', 'PreDir', 'PreType', 'StArticle', 'StreetName', 'PostType', 'PostDir', 'PostMod', 'ZipCode', 'LegalComm', 'PCITY1']:
            if a1['properties'][key] != a2['properties'][key]:
                #print key, a1['properties'][key], "!=", a2['properties'][key]
                return False
        return True

    def areSameAddressExceptStreet(a1, a2):
        for key in ['NumPrefix', 'Number', 'NumSuffix', 'PreMod', 'PreDir', 'StArticle', 'UnitName', 'PostDir', 'PostMod', 'ZipCode', 'LegalComm', 'PCITY1']:
            if a1['properties'][key] != a2['properties'][key]:
                #print key, a1['properties'][key], "!=", a2['properties'][key]
                return False
        return True

    # Sometimes we have identical addresses that differ only by street name.
    # Usually these are because the street name is also a highway. We want to 
    # remove all the highway names and only use the street name for the address
    canonicalNames = {
        ("None", "LINCOLN", "BOULEVARD"): (None, "LINCOLN", "BOULEVARD"),
        ("ROUTE", "1", "None"): (None, "LINCOLN", "BOULEVARD"),
        ("HIGHWAY", "1", "None"): (None, "LINCOLN", "BOULEVARD"),
        ("None", "SR-1", "None"): (None, "LINCOLN", "BOULEVARD"),
        ("None", "PCH", "None"): (None, "LINCOLN", "BOULEVARD"),
    }

    def getCanonicalName(compoundStreetName):
        result = None
        try:
            result = canonicalNames[compoundStreetName]
        except KeyError:
            return None
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

    # Sometimes we want to force overlapping nodes, such as with addresses.
    # This way they'll show up in JOSM and the contributor can deal with them manually.
    # Otherwise, we might try to apply multiple address tags to the same node...
    # ...which is also incorrect, but harder to detect.
    def appendNewNodeIgnoringExisting(coords, osmXml):
        rlon = int(float(coords[0]*10**7))
        rlat = int(float(coords[1]*10**7))
        #if (rlon, rlat) in nodes:
        #    return nodes[(rlon, rlat)]
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
        # Need to check if these tags already exist on this element
        for k, v in convertAddress(address['properties']).iteritems():
            # TODO: is this doing anything useful?
            #for child in element:
            #    if child.tag == 'tag':
            #        #print k, v
            #        if child.attrib.get('k') == k:
            #            print "found key", k
            #            if child.attrib.get('v') == v:
            #                print "found matching value", v
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
        if 'GeneralUse' in building['properties'] and building['properties']['GeneralUse'] is not None:
            way.append(etree.Element('tag', k='building', v=building['properties']['GeneralUse'].lower()))
        else:
            way.append(etree.Element('tag', k='building', v='yes'))
        if 'SpecificUs' in building['properties'] and building['properties']['SpecificUs'] is not None:
            way.append(etree.Element('tag', k='building:use', v=building['properties']['SpecificUs'].lower()))
        if 'YearBuilt' in building['properties'] and building['properties']['YearBuilt'] is not None:
            YearBuilt = int(building['properties']['YearBuilt'])
            if YearBuilt > 0:
                    way.append(etree.Element('tag', k='start_date', v=str(YearBuilt)))
        if 'Specific_1' in building['properties'] and building['properties']['Specific_1'] is not None:
                way.append(etree.Element('tag', k='amenity', v=building['properties']['Specific_1'].lower()))
        if 'Units' in building['properties'] and building['properties']['Units'] is not None:
            units = int(round(float(building['properties']['Units']), 0))
            if units > 0:
                way.append(etree.Element('tag', k='building:units', v=str(units)))
        if 'HEIGHT' in building['properties']:
            height = round(((building['properties']['HEIGHT'] * 12) * 0.0254), 1)
            if height > 0:
                way.append(etree.Element('tag', k='height', v=str(height)))
        if 'ELEV' in building['properties']:
            elevation = round(((building['properties']['ELEV'] * 12) * 0.0254), 1)
            if elevation > 0:
                way.append(etree.Element('tag', k='elevation', v=str(elevation)))
        if 'BLD_ID' in building['properties']:
            way.append(etree.Element('tag', k='lacounty:bld_id', v=str(building['properties']['BLD_ID'])))
        if address:
            appendAddress(address, way)

    # Export buildings & addresses. Only export address with building if there is exactly
    # one address per building. Export remaining addresses as individual nodes.
    # The remaining addresses are added to a dictionary hashed by their coordinates.
    # This way we catch any addresses that have the same coordinates.
    osmXml = etree.Element('osm', version='0.6', generator='alex@mapbox.com')
    for i in range(0, len(buildings)):

        buildingAddresses = []
        for address in buildings[i]['properties']['addresses']:
            buildingAddresses.append(address)
        address = None
        if len(buildingAddresses) == 1:
            # There's only one address in the building footprint
            address = buildingAddresses[0]
        elif len(buildingAddresses) > 1:
            # If there are multiple addresses, first try to distill them.
            # If we can distill them to one address, we can still add it to this building.
            distilledAddresses = distillAddresses(buildingAddresses)
            if len(distilledAddresses) == 1:
                # We distilled down to one address. Add it to the building.
                address = distilledAddresses[0]
            else:
                # We could not distilled down to one address. Instead export as nodes.
                for address in distilledAddresses:
                # The key is the coordinates of this address. Track how many addresses share these coords.
                    key = keyFromAddress(address)
                    if key in allAddresses:
                        allAddresses[key].append(address)
                    else:
                        allAddresses[key] = [address]
        appendBuilding(buildings[i], buildingShapes[i], address, osmXml)


    # Export any addresses that aren't the only address for a building.
    if (len(allAddresses) > 0):

        # Iterate over the list of distinct coordinates found in the address data
        for coordskey in allAddresses:
            # if a distinct coordinate has only one associated address,
            # then export that address as a new node
            if len(allAddresses[coordskey]) == 1:
                address = allAddresses[coordskey][0]
                coordinates = address['geometry']['coordinates']
                node = appendNewNode(coordinates, osmXml) # returns old node if one exists at these coords
                appendAddress(address, node)

            # If there is more than one address at these coordinates, do something.
            # ...but do what exactly?
            else:
                distilledAddresses = distillAddresses(allAddresses[coordskey])
                if len(distilledAddresses) == 1:
                    # We distilled down to one address. Append it.
                    address = distilledAddresses[0]
                    coordinates = address['geometry']['coordinates']
                    node = appendNewNode(coordinates, osmXml) # returns old node if one exists at these coords
                    appendAddress(address, node)
                else:
                    if debug: print "found duplicate coordinates that could not be distilled:", coordskey, "has", len(allAddresses[coordskey]), "addresses"
                    if debug: print '\t'.join(["num", "numsufx", "pretype", "street", "posttype", "unit"])
                    for address in distilledAddresses:
                        # TODO: do something smart here. These are overlapping addresses that we couldn't distill.
                        # TODO: maybe jitter them, or leave stacked but with FIXME?
                        # TODO: For now, we use appendNewNodeIgnoringExisting to pile the nodes on top of each other.
                        #print address
                        props = address['properties']
                        if debug: print '\t'.join([str(props['Number']), str(props['NumSuffix']), str(props['PreType']), str(props['StreetName']), str(props['PostType']), str(props['UnitName'])])
                        coordinates = address['geometry']['coordinates']
                        node = appendNewNodeIgnoringExisting(coordinates, osmXml) # Force overlapping nodes so JOSM will catch them
                        appendAddress(address, node)

    with open(osmOut, 'w') as outFile:
        outFile.writelines(tostring(osmXml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print 'Exported ' + osmOut

def prep(fil3):
    matches = re.match('^(.*)\..*?$', ntpath.basename(fil3)).groups(0)
    convert(fil3, 'osm/%s.osm' % matches[0])

if __name__ == '__main__':
    # for easier debugging
    # for filename in argv[1:]:
    #     prep(filename)
    pool = Pool()
    iterator = ( f for f in argv[1:])
    pool.map(prep, iterator)
    pool.close()
    pool.join()
