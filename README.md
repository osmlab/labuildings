LA Buildings
===========

[![Join the chat at https://gitter.im/osmlab/labuildings](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/osmlab/labuildings?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Los Angeles County building and address import

Generates an OSM file of buildings with addresses per census block groups,
ready to be used in JOSM for a manual review and upload to OpenStreetMap. This repository is based heavily on the [NYC building import](https://github.com/osmlab/nycbuildings)

This README is about data conversion. See also the [page on the OSM wiki](https://wiki.openstreetmap.org/wiki/Los_angeles,_California/Buildings_Import).

**HOW YOU CAN GET INVOLVED:** You may want to browse the [issues](https://github.com/osmlab/labuildings/issues) and/or "watch" this repo (see button at the top of this page) to follow along with the discussion.

![LA buildings screenshot](la_buildings_screenshot.png?raw=true "LA buildings screenshot from QGIS")

Sample .osm files (**not ready for import yet**) are in this [zip file](https://github.com/osmlab/labuildings/blob/master/venice_osm.zip?raw=true).

Browse a slippy map of the data [here](http://stamen.cartodb.com/u/stamen-org/viz/ff53ba6e-9788-11e4-945a-f23c91504230/public_map)

## How can I help?

| Phase        | Task           | Contact  |
| ------------- |:-------------:| -----:|
| Attributes to be Imported      | Select which fields will be imported and prepend (associate) with an OSM tag  [Google Spreadsheet](https://docs.google.com/spreadsheets/d/1A3whba04_-3K0z77nGHYavIwYpWjnyAaInwWie3HSVA/edit#gid=1971401153) |  Request access to spreadsheet from [@cityhubla](https://github.com/cityhubla) or discuss in Issue [#3] (https://github.com/osmlab/labuildings/issues/3) |
| Python Scripting |  Process datasets to OSM files |  Questions?  Discuss in Issue [#9](https://github.com/osmlab/labuildings/issues/9) |
| Import Guidelines     | Prepare guidelines for import      |   Discuss in Issue [#10](https://github.com/osmlab/labuildings/issues/10) |


## Prerequisites

    Python 2.7.x
    pip
    virtualenv
    libxml2
    libxslt
    spatialindex
    GDAL

### Installing prerequisites on Mac OSX

    # install brew http://brew.sh

    brew install libxml2
    brew install libxslt
    brew install spatialindex
    brew install gdal

### Installing prerequisites on Ubuntu

    apt-get install python-pip
    apt-get install python-virtualenv
    apt-get install gdal-bin
    apt-get install libgdal-dev
    apt-get install libxml2-dev
    apt-get install libxslt-dev
    apt-get install python-lxml
    apt-get install python-dev
    apt-get install libspatialindex-dev
    apt-get install unzip

## Set up Python virtualenv and get dependencies
    # may need to easy_install pip and pip install virtualenv
    virtualenv ~/venvs/labuildings
    source ~/venvs/labuildings/bin/activate
    pip install -r requirements.txt


## Usage

Run all stages:

    # Download all files and process them into a building
    # and an address .osm file per district.
    make

You can run stages separately, like so:

    # Download and expand all files, reproject
    make download

    # Chunk address and building files by census block group
    # (this will take a long time)
    make chunks

    # Generate importable .osm files.
    # This will populate the osm/ directory with one .osm file per
    # census block group.
    make osm

    # Clean up all intermediary files:
    make clean

    # For testing it's useful to convert just a single district.
    # For instance, convert block group 060372735024:
    make chunks # will take a while
    python merge.py 060372735024 # Should be fast
    python convert.py merged/buildings-addresses-060372735024.geojson # Fast


## Features

- Cleans address names
- Exports one OSM XML building and address file per LA county block group
- Conflates buildings and addresses (only when there is one address point inside a building polygon)
- Exports remaining addresses as points (for buildings with more than one address, or addresses not on a building)
- Handles multipolygons
- Simplifies building shapes

## Attribute mapping

See the `convert.py` script to see the implementation of these transformations.

### Address attributes

* **AIN** - Parcel this address falls inside

	* Ignore (although `merge.py` uses this to map stray addresses to buildings)

* **NumPrefix** - Number prefix

	* Note: These are extremely rare (only 33 of them), mainly showing up for addresses in Lakewood Center Mall, Lakewood CA. Handling these would require treating `addr:housenumber` as a string, not an integer. However, the OSM wiki says this is permitted.
	* Prepend to `addr:housenumber` using `formatHousenumber()` function

* **Number** - House Number

	* Map to `addr:housenumber` using `formatHousenumber()` function

* **NumSuffix** - House Number Suffix (1/2, 3/4 etc)

	* Append to `addr:housenumber` using `formatHousenumber()` function

* **PreMod** - Prefix Modifier

	* Examples: **OLD** RANCH ROAD, **LOWER** ASUZA ROAD
	* Change to titlecase
	* Prepend to `addr:street`

* **PreDir** - Prefix Direction (E, S, W, N)

	* Examples: **SOUTH** RANCH ROAD
	* Note: the data is already expanded into "NORTH", "SOUTH", etc. We do not condense into "N", "S".
	* Change to titlecase
	* Prepend to `addr:street`

* **PreType** - Prefix Type (Ave, Avenida, etc)

	* Examples: NORTH **VIA** SORRENTO, **RUE** DE LA PIERRE
	* Change to titlecase
	* Prepend to `addr:street`

* **StArticle** - Street Article (de la, les, etc)

	* Examples: RUE **DE LA** PIERRE
	* Change to titlecase
	* Prepend to `addr:street`

* **StreetName** - Street Name

	* Change to titlecase (but full lowercase on numeral suffixes "st", "nd", "rd", "th")
	* Map to `addr:street`

* **PostType** - Post Type (Ave, St, Dr, Blvd, etc)

	* Change to titlecase
	* Append to `addr:street`

* **PostDir** - Post Direction (N, S, E, W)

	* Examples: MARINA DRIVE **SOUTH**
	* Note: the data is already expanded into "NORTH", "SOUTH", etc. We do not condense into "N", "S".
	* Change to titlecase
	* Append to `addr:street`

* **PostMod** - Post Modifier (OLD, etc)

	* Note: this is always null in the current data. Treat like PreMod for consistency.
	* Change to titlecase
	* Append to `addr:street`

* **UnitType** - Unit Type (#, Apt, etc) - where these are known

	* **Ignore?**

* **UnitName** - Unit Name (A, 1, 100, etc)

	* Map to `addr:unit`

* **Zipcode** - Zipcode

	* Map to `addr:postcode`

* **Zip4** - Not currently filled out in source data

	* Ignore

* **LegalComm** - Legal City or primary postal city in Unincorporated Areas

	* Fall back to this if `PCITY1` is null. 
	* Potentially could map this to `is_in:city`, but given that OSM already has good city boundaries this seems unnecessary.

* **Source** - source of the address point, one of: Assessor, LACity, Regional Planning, other

	* Ignore: this generally corresponds to whichever city the address falls within

* **SourceID** - ID of the Address in the source system

    * Ignore

* **MADrank** - Method Accuracy Description (MAD) provides a number between 1 and 100 detailing the accuracy of the location.

	* Ignore

* **PCITY1** - 1st postal city (from the USPS)

	* Note: this is null for 1469 records. When null, fall back to `LegalComm`.
	* Change to titlecase
	* Map to `addr:city`

* **PCITY2** - 2nd postal city (from the USPS)

	* Ignore: mostly null or same as LegalComm. Always null when `PCITY1` is null.

* **PCITY3** - 3rd postal city (from the USPS)

	* Ignore: mostly null. Always null when `PCITY1` is null.

### Building attributes

* **CODE** - Building type (either Building or Courtyard).

	* Ignore
	* Note: only CODE='Building' is used for this import. We ignore CODE='Courtyard'. This filtering step happens in the `Makefile`

* **BLD_ID** - unique building ID

	* **Ignore** ???
	* Or, map to a special OSM tag like `lacounty:bld_id`

* **HEIGHT** - the height of the highest major feature of the building (not including roof objects like antennas and chimneys)

	* Convert from inches to meters
	* Round to one decimal place
	* Map to `height` tag, only if height > 0

* **ELEV** - the elevation of the building

	* Convert from inches to meters
	* Round to one decimal place
	* Map to `elevation` tag, only if elevation > 0
	
* **AREA** - the Roof area

	* Ignore: mostly null

* **SOURCE** - the data source (either LARIAC2, Pasadena, Palmdale, or Glendale)

	* Ignore
	
* **DATE** - Date Captured (2006, 2008, or blank)

	* Ignore
	
* **AIN** - the Parcel ID number.

	* Ignore (although `merge.py` uses this to map stray addresses to buildings)

