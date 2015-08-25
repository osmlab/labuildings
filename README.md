LA Buildings
===========

[![Join the chat at https://gitter.im/osmlab/labuildings](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/osmlab/labuildings?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Los Angeles County building and address import

Generates an OSM file of buildings with addresses per census block groups,
ready to be used in JOSM for a manual review and upload to OpenStreetMap. This repository is based heavily on the [NYC building import](https://github.com/osmlab/nycbuildings)

This README is about data conversion. See also the [page on the OSM wiki](https://wiki.openstreetmap.org/wiki/Los_angeles,_California/Buildings_Import).

**HOW YOU CAN GET INVOLVED:** You may want to browse the [issues](https://github.com/osmlab/labuildings/issues) and/or "watch" this repo (see button at the top of this page) to follow along with the discussion. Also join the chat room on [Gitter](https://gitter.im/osmlab/labuildings)!

| Phase        | Task           | Contact  |
| ------------- |:-------------:| -----:|
| Attributes to be Imported      | Select which fields will be imported and prepend (associate) with an OSM tag  [Google Spreadsheet](https://docs.google.com/spreadsheets/d/1A3whba04_-3K0z77nGHYavIwYpWjnyAaInwWie3HSVA/edit#gid=1971401153), list is displayed below as well|  Request access to spreadsheet from [@cityhubla](https://github.com/cityhubla) or discuss in Issue [#3] (https://github.com/osmlab/labuildings/issues/3) |
| Python Scripting |  Process datasets to OSM files |  Questions?  Discuss in Issue [#9](https://github.com/osmlab/labuildings/issues/9) |
| Import Guidelines     | Prepare guidelines for import      |   Discuss in Issue [#10](https://github.com/osmlab/labuildings/issues/10) |


![LA buildings screenshot](la_buildings_screenshot.png?raw=true "LA buildings screenshot from QGIS")

Sample .osm files (**not ready for import yet**) are in this [zip file](https://github.com/osmlab/labuildings/blob/master/venice_osm.zip?raw=true).

Browse a slippy map of the data [here](http://stamen.cartodb.com/u/stamen-org/viz/ff53ba6e-9788-11e4-945a-f23c91504230/public_map)

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

| Attribute | OSM Equivalent | Dataset used| Description | Add/Ignore? | Notes |
|------------|------------------|--------------------------|---------------------------------------------------------------------------------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AIN |  | LA County Address Points | Parcel this address falls inside | Ignore |  |
| Numprefix | `addr:housenumber` | LA County Address Points | Number prefix | Add | These are extremely rare (only 33 of them), mainly showing up for addresses in Lakewood Center Mall, Lakewood CA. Handling these would require treating `addr:housenumber` as a string, not an integer. However, the OSM wiki says this is permitted. |
| Number | `addr:housenumber` | LA County Address Points | House Number | Add |  |
| NumSuffix | `addr:housenumber` | LA County Address Points | House Number Suffix (1/2, 3/4 etc) | Add |  |
| PreMod | `addr:street` | LA County Address Points | Prefix Modifier | Add | Examples: OLD RANCH ROAD, LOWER ASUZA ROAD |
| PreDir | `addr:street` | LA County Address Points | Prefix Direction (E, S, W, N) | Add | Examples: SOUTH RANCH ROAD |
| PreType | `addr:street` | LA County Address Points | Prefix Type (Ave, Avenida, etc) | Add | Examples: NORTH VIA SORRENTO, RUE DE LA PIERRE |
| STArticle | `addr:street` | LA County Address Points | Street Article (de la, les, etc) | Add | Examples: RUE DE LA PIERRE. Change to titlecase |
| StreetName | `addr:street` | LA County Address Points | Street Name | Add | Change to titlecase (but full lowercase on numeral suffixes "st", "nd", "rd", "th") |
| PostType | `addr:street` | LA County Address Points | Post Type (Ave, St, Dr, Blvd, etc) | Add | Change to titlecase |
| PostDir | `addr:street` | LA County Address Points | Post Direction (N, S, E, W) | Add | Examples: MARINA DRIVE SOUTH. Note: the data is already expanded into "NORTH", "SOUTH", etc. We do not condense into "N", "S". Change to Titlecase |
| PostMod | `addr:street` | LA County Address Points | Post Modifier (OLD, etc) | Add | Note: this is always null in the current data. Treat like PreMod for consistency. Change to titlecase |
| UnitType |  | LA County Address Points | Unit Type (#, Apt, etc) - where these are known |  | Ignore??? |
| UnitName | `addr:unit` | LA County Address Points | Unit Name (A, 1, 100, etc) | Add |  |
| Zipcode | `addr:postcode` | LA County Address Points | Zipcode | Add |  |
| Zip4 |  | LA County Address Points | Not currently filled out | Ignore |  |
| LegalComm | `is_in:city` | LA County Address Points | Legal City or primary postal city in Unincorporated Areas | Add | Fall back to this if `PCITY1` is null. Potentially could map this to `is_in:city`, but given that OSM already has good city boundaries this seems unnecessary. |
| PostComm1 | `addr:city` | LA County Address Points | Primary Postal Community | Ignore |  |
| PostComm2 |  | LA County Address Points | Secondary Postal Community | Ignore |  |
| PostComm3 |  | LA County Address Points | Third Postal Community | Ignore |  |
| Source |  | LA County Address Points | source of the address point, one of: Assessor, LACity, Regional Planning, other | Ignore | this generally corresponds to whichever city the address falls within |
| SourceID |  | LA County Address Points | ID of the Address in the source system | Ignore |  |
| MADrank |  | LA County Address Points | Method Accuracy Description (MAD) provides a number between 1 and 100 detailing the accuracy of the location. | Ignore |  |
| PCITY1 | `addr:city` |  | 1st postal city (from the USPS) | add | this is null for 1469 records. When null, fall back to `LegalComm`. Change to titlecase |
| PCITY2 |  |  | 2nd postal city (from the USPS) | ignore | mostly null or same as LegalComm. Always null when `PCITY1` is null. |
| PCITY3 |  |  | 3rd postal city (from the USPS) | ignore | mostly null. Always null when `PCITY1` is null. |

### Building attributes

| Attribute | OSM Equivalent | Dataset used| Description | Add/Ignore? | Notes |
|--------------------|-----------------|-------------------|-----------------------------------------------------------------------------------------------------------------|--------|-----------------------------------------------------------------------------------------------------------------------------|
| CODE |  |  |  | Ignore | Note: only CODE=`Building` is used for this import. We ignore CODE='Courtyard'. This filtering step happens in the Makefile |
| BLD_ID | `lacounty:bld_id` | Building Outlines | Unique Building ID | Add | Special OSM Tag |
| HEIGHT | `height` | Building Outlines | The height of the highest major feature of the building (not including roof objects like antennas and chimneys) | Add | map to tag, only if height >0 |
| ELEV | `elevation` | Building Outlines | The elevation of the building | Add | map to elevation, only if elevation > 0 |
| AREA |  | Building Outlines | Roof Area | Ignore | Mostly null |
| SOURCE |  | Building Outlines | The data source (either LARIAC2, Pasadena, Palmdale, or Glendale) | Ignore |  |
| AIN |  | Building Outlines | The parcel ID number | Ignore | Used to map stray addresses to buildings and link datasets |
| Shape_Leng |  | Building Outlines |  | Ignore |  |
| Shape_Area | `area` | Building Outlines |  | Ignore |  |
| GeneralUseType | building | Assessor 2015 | General use type of the property | Add |  |
| SpecificUseType | building:use | Assessor 2015 | More specific use type of the property  | Add |  |
| YearBuilt | `start_date` | Assessor 2015 | Year property was originally built | Add |  |
| EffectiveYearBuilt |  | Assessor 2015 | Effective year built taking into account subsequent construction, remodeling, building maintenance, etc. |  | what is this? |
| SpecificUseDetail1 | amenity | Assessor 2015 | More specific use type of the property  | Add |  |
| SpecificUseDetail2 |  | Assessor 2015 | Additional property usage detail |  |  |
| SQFTmain |  | Assessor 2015 | Total square footage of the main structure(s), | Ignore |  |
| Bedrooms |  | Assessor 2015 | Total number of bedrooms. |  |  |
| Bathrooms |  | Assessor 2015 | Total number of bathrooms. |  |  |
| Units | `building:units` | Assessor 2015 | Total number of living units. | Add |  |
