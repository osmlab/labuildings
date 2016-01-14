all: BldgPly/buildings.shp AddressPt/addresses.shp BlockGroupPly/blockgroups.shp directories chunks merged osm

clean:
	rm -f BldgPly.zip
	rm -f AddressPt.zip
	rm -f BlockGroupPly.zip

BldgPly.zip:
	curl -L "http://latimes-graphics-media.s3.amazonaws.com/jon-temp/lariac_buildings_2008.zip" -o BldgPly.zip

AddressPt.zip:
	curl -L "http://egis3.lacounty.gov/dataportal/wp-content/uploads/2012/06/lacounty_address_points.zip" -o AddressPt.zip

BlockGroupPly.zip:
	curl -L "http://www2.census.gov/geo/tiger/TIGER2014/BG/tl_2014_06_bg.zip" -o BlockGroupPly.zip

# Other potential data sources
# LA City Community Plan Areas: https://data.lacity.org/api/geospatial/pu8r-72kk?method=export&format=Shapefile

BldgPly: BldgPly.zip
	rm -rf BldgPly
	unzip BldgPly.zip -d BldgPly

AddressPt: AddressPt.zip
	rm -rf AddressPt
	unzip AddressPt.zip -d AddressPt

# NOTE: this downloads block groups for all of California. ogr2ogr selects & creates BlockGroupPolyshp with LA County only.

BlockGroupPly: BlockGroupPly.zip
	rm -rf BlockGroupPly
	unzip BlockGroupPly.zip -d BlockGroupPly

BlockGroupPly/BlockGroupPly.shp: BlockGroupPly
	rm -rf BlockGroupPly/BlockGroupPly.*
	ogr2ogr -where "COUNTYFP='037'" BlockGroupPly/BlockGroupPly.shp BlockGroupPly/tl_2014_06_bg.shp

BldgPly/buildings.shp: BldgPly
	rm -f BldgPly/buildings.*
# Specify CODE=Building to ignore CODE=Courtyard, suppressing Pasadena #20
        ogr2ogr -where "SOURCE <> 'Pasadena' AND CODE='Building'" -simplify 0.2 -t_srs EPSG:4326 -overwrite BldgPly/buildings.shp BldgPly/lariac_buildings_2008.shp

AddressPt/addresses.shp: AddressPt
	rm -f AddressPt/addresses.*
	ogr2ogr -t_srs EPSG:4326 -overwrite AddressPt/addresses.shp AddressPt/lacounty_address_points.shp

BlockGroupPly/blockgroups.shp: BlockGroupPly/BlockGroupPly.shp
	rm -f BlockGroupPly/blockgroups.*
	ogr2ogr -t_srs EPSG:4326 BlockGroupPly/blockgroups.shp BlockGroupPly/BlockGroupPly.shp

BlockGroupPly/blockgroups.geojson: BlockGroupPly/BlockGroupPly.shp
	rm -f BlockGroupPly/blockgroups.geojson
	rm -f BlockGroupPly/blockgroups-900913.geojson
	ogr2ogr -simplify 3 -t_srs EPSG:900913 -f "GeoJSON" BlockGroupPly/blockgroups-900913.geojson BlockGroupPly/BlockGroupPly.shp
#	python tasks.py BlockGroupPly/blockgroups-900913.geojson > BlockGroupPly/blockgroups.geojson

chunks: directories AddressPt/addresses.shp BldgPly/buildings.shp
	python chunk.py AddressPt/addresses.shp BlockGroupPly/blockgroups.shp chunks/addresses-%s.shp GEOID
	python chunk.py BldgPly/buildings.shp BlockGroupPly/blockgroups.shp chunks/buildings-%s.shp GEOID

merged: directories
#	python merge.py

osm: merged
#	python convert.py merged/*

directories:
	mkdir -p chunks
	mkdir -p merged
	mkdir -p osm

# Make TileMill 1 project
tilemill:
	mkdir -p ${HOME}/Documents/MapBox/project
	ln -sf "`pwd`" ${HOME}/Documents/MapBox/project/labuildings

# Load database for Mapbox Studio
database: AddressPt/addresses.shp BldgPly/buildings.shp BlockGroupPly/blockgroups.shp
	createdb labuildings
	psql labuildings -c "CREATE EXTENSION postgis;"
	shp2pgsql AddressPt/address.shp | psql labuildings
	shp2pgsql BldgPly/buildings.shp | psql labuildings
	shp2pgsql BlockGroupPly/blockgroups.shp | psql labuildings
