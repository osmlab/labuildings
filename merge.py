# Merge addresses into buildings they intersect with
# Write them to merged/
from fiona import collection
from rtree import index
from shapely.geometry import asShape, Point, LineString
import re
from sys import argv
from glob import glob
from multiprocessing import Pool
import json
import md5

useAINs = True

def merge(buildingIn, addressIn, mergedOut):
    addresses = []

    with collection(addressIn, "r") as input:
        for address in input:
            shape = asShape(address['geometry'])
            shape.original = address
            addresses.append(shape)

    geoid = re.match('^.*-(\d+)\.shp$', buildingIn).groups(0)[0]

#    print "loaded", len(addresses), "addresses"

    # Load and index all buildings.
    buildings = []
    buildingShapes = []
    buildingIdx = index.Index()
    with collection(buildingIn, "r") as input:
        for building in input:
            shape = asShape(building['geometry'])
            building['properties']['addresses'] = []
            buildings.append(building)
            buildingShapes.append(shape)
            buildingIdx.add(len(buildings) - 1, shape.bounds)

#    print "loaded", len(buildings), "buildings"

    addressIntersections = {}

    addressesOnBuildings = 0

    # Map addresses to buildings.

    # Note, if there are multiple address points within a building, this
    # adds each one as an array
    for address in addresses:
#       print 'address', address
#	print 'addressIntersections', addressIntersections
        if address not in addressIntersections.keys():
            addressIntersections[address] = 0
        for i in buildingIdx.intersection(address.bounds):
            if buildingShapes[i].contains(address):
                addressesOnBuildings += 1
                addressIntersections[address] += 1
                buildings[i]['properties']['addresses'].append(
                    address.original)

    # Display the number of buildings that have 0 addresses, 1 address, 2 addresses, and so on...
    numberOfAddressesCounter = {}

    for building in buildings:
        numberOfAddresses = len(building['properties']['addresses'])
        if numberOfAddresses in numberOfAddressesCounter:
            numberOfAddressesCounter[numberOfAddresses] += 1
        else:
            numberOfAddressesCounter[numberOfAddresses] = 1

    strayAddresses = []

    for addressKey in addressIntersections:
        if addressIntersections[addressKey] > 1:
            # Sanity check for addresses that intersected more than one building
            print "address", addressKey, "interesected", addressIntersections[addressKey], "buildings"
        if addressIntersections[addressKey] == 0:
            # This address didn't hit any buildings. We need to export it separately
            strayAddresses.append(addressKey.original)

    buildingsWithAtLeastOneAddress = 0

    for key in sorted(numberOfAddressesCounter.keys()):
        #print numberOfAddressesCounter[key], "building(s) had", key, "address(es)"
        if key > 0:
            buildingsWithAtLeastOneAddress += numberOfAddressesCounter[key]

    # Print an informative one-line message
    statusmessage = str(geoid) + ": " + str(addressesOnBuildings) + "/" + str(len(addresses))
    if len(addresses) > 0:
        statusmessage += " (" + str(addressesOnBuildings*100/len(addresses)) + "%)"
    statusmessage += " addrs hit bldgs, " + str(buildingsWithAtLeastOneAddress) + "/" + str(len(buildings))
    if len(buildings) > 0:
        statusmessage += " (" + str(buildingsWithAtLeastOneAddress*100/len(buildings)) + "%)"
    statusmessage += " bldgs have at least one addr"

    print statusmessage

    if useAINs:
        # Now try to join on AIN to match buildings and addresses on the same parcel.
        # Only try this if the following conditions are true:
        # 1. The building doesn't already have at least one address
        # 2. The AIN is present on only one building (ignore parcels w/ house + garage)
        # 3. The AIN is present on only one address node (ignore multi-address parcels)

        ainMatches = 0;

        # First populate our AIN lookup
        AINs = {}
        for building in buildings:
            buildingAIN = building['properties']['AIN']
            # Make sure AIN is not null
            if buildingAIN:
                if buildingAIN not in AINs:
                    AINs[buildingAIN] = {}
                if 'buildings' not in AINs[buildingAIN]:
                    AINs[buildingAIN]['buildings'] = []
                AINs[buildingAIN]['buildings'].append(building)

        # only populate with stray addresses
        for address in strayAddresses:
            addressAIN = address['properties']['AIN']
            # Make sure AIN is not null
            if addressAIN:
                if addressAIN not in AINs:
                    AINs[addressAIN] = {}
                if 'addresses' not in AINs[addressAIN]:
                    AINs[addressAIN]['addresses'] = []
                AINs[addressAIN]['addresses'].append(address)

        # Now look for buildings that don't yet have addresses
        for building in buildings:
            if len(building['properties']['addresses']) < 1:
                ain = building['properties']['AIN']
                # And confirm AIN is only on one address and one building
                if ain in AINs and 'buildings' in AINs[ain] and len(AINs[ain]['buildings']) == 1 and 'addresses' in AINs[ain] and len(AINs[ain]['addresses']) == 1:
                    ainMatches += 1;
                    foundAddress = AINs[ain]['addresses'][0]
                    # Now we assign the address to the building
                    building['properties']['addresses'].append(foundAddress)
                    if foundAddress in strayAddresses:
                        strayAddresses.remove(foundAddress)
                    else:
                        print foundAddress, "not in strayAddresses! We just matched it to", building

        print geoid + ": using AINs matched", ainMatches, "more addresses"

    # Note: previous versions of this script would only export buildings, 
    # but now we append the list of stray (nonintersecting) addresses.
    # convert.py has been modified as well, to accept the new format

    with open(mergedOut, 'w') as outFile:
        outFile.writelines(json.dumps(buildings+strayAddresses, indent=4))
        #print 'Exported ' + mergedOut

def prep(fil3):
    matches = re.match('^.*-(\d+)\.shp$', fil3).groups(0)
    merge(fil3,
        'chunks/addresses-%s.shp' % matches[0],
        'merged/buildings-addresses-%s.geojson' % matches[0])

if __name__ == '__main__':
    # Run merges. Expects an chunks/addresses-[block group geoid].shp for each
    # chunks/buildings-[block group geoid].shp. Optionally convert only one block group.
    if (len(argv) == 2):
        merge('chunks/buildings-%s.shp' % argv[1],
            'chunks/addresses-%s.shp' % argv[1],
            'merged/buildings-addresses-%s.geojson' % argv[1])
    else:
        buildingFiles = glob("chunks/buildings-*.shp")

        pool = Pool()
        pool.map(prep, buildingFiles)
        pool.close()
        pool.join()
