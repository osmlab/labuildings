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
        ogr2ogr -where "(CODE='Building') AND (SOURCE NOT IN ('Pasadena'))" -simplify 0.2 \
        -s_srs '+proj=lcc +lat_1=35.46666666666667 +lat_2=34.03333333333333 +lat_0=33.5 +lon_0=-118 +x_0=2000000.000101601 +y_0=500000.0001016002 +ellps=GRS80 +towgs84=-0.9956,1.9013,0.5215,0.025915,0.009426,0.011599,-0.00062 +units=us-ft +no_defs' \
        -t_srs EPSG:4326 -overwrite BldgPly/buildings.shp BldgPly/merged-buildings-state-plane.shp

AddressPt/addresses.shp: AddressPt
	rm -f AddressPt/addresses.*
	ogr2ogr -where "Source <> 'PASADENA.GIS'" \
        -s_srs '+proj=lcc +lat_1=35.46666666666667 +lat_2=34.03333333333333 +lat_0=33.5 +lon_0=-118 +x_0=2000000.000101601 +y_0=500000.0001016002 +ellps=GRS80 +towgs84=-0.9956,1.9013,0.5215,0.025915,0.009426,0.011599,-0.00062 +units=us-ft +no_defs' \
        -t_srs EPSG:4326 -overwrite AddressPt/addresses.shp AddressPt/lacounty_address_points.shp

BlockGroupPly/blockgroups.shp: BlockGroupPly/BlockGroupPly.shp
	rm -f BlockGroupPly/blockgroups.*
	ogr2ogr -t_srs EPSG:4326 BlockGroupPly/blockgroups.shp BlockGroupPly/BlockGroupPly.shp

BlockGroupPly/blockgroups.geojson: BlockGroupPly/BlockGroupPly.shp
	rm -f BlockGroupPly/blockgroups.geojson
	rm -f BlockGroupPly/blockgroups-4326.geojson
	ogr2ogr -t_srs EPSG:4326 -f "GeoJSON" BlockGroupPly/blockgroups-4326.geojson BlockGroupPly/BlockGroupPly.shp
#	python tasks.py BlockGroupPly/blockgroups-4326.geojson > BlockGroupPly/blockgroups.geojson

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
