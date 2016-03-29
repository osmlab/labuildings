How to import
=============

**NOTE: THIS DOCUMENT IS A WORK IN PROGRESS**

**ALSO: THE IMPORT HAS NOT YET BEEN APPROVED BY THE OPENSTREETMAP COMMUNITY**

**DO NOT IMPORT ANY DATA UNTIL THESE INSTRUCTIONS HAVE BEEN FINALIZED AND THE IMPORT HAS BEEN APPROVED**

## Getting started

### Creating an import account

 * OSM best practices require that you do not use your normal OSM account for the imports. Create a new account for this purpose. 
 Usually, it's your existing OSM username followed by `_imports` (e.g. `maning_imports or maning_labuilding)`.
 Post your import account username in this [ticket](http://github.com/osmlab/labuildings/issues/40).

### Getting familiar with JOSM

To contribute to this project, you need to use the JOSM editor.  Here are some resources to get you started:
 * LearnOSM - http://learnosm.org/en/josm/
 * Mapbox Mapping wiki - https://www.mapbox.com/blog/making-the-most-josm/

### Check out a task on the tasking manager

 * Tasks will be available on this **[Tasking Manager](http://52.74.49.58:6543/project/15 link soon)**.
 * Priority: we are working on Los Angeles City first, which is broken down by census block groups. Each task performed is one block group within the city boundaries.
 * Why? because different parts of the county have different data problems to watch out for. If we all run into the same problems at the same time, it will be easier for us to help each other and improve the processing scripts and the import workflow.

## Import workflow

### Activating JOSM Remote Control
 * Open JOSM and activate JOSM Remote Control. In the JOSM menu, select **Edit > Preferences...** or press F12
 * Click on the remote control icon
 * Select **Enable Remote Control** and click **OK**.
 
 ![josm_rc](https://cloud.githubusercontent.com/assets/353700/13667682/adc1f10c-e6dd-11e5-8f01-e83a52460bfd.gif)

### Selecting a task in the Tasking Manager

 * Choose which area you want to work on from the **[Tasking Manager-link TBD](link soon)** and click **Start Mapping**
 * Download current data in OSM by clicking **Edit in JOSM**
 

![download_osm](https://cloud.githubusercontent.com/assets/353700/14101327/6f8b279a-f5b1-11e5-83ef-b28d00afca62.gif)
 
 
 * Get the `.osm` file you will import by clicking the link in the **Extra Instructions**.  This will download a new layer in JOSM.
   At least two layers should be in JOSM: one with the imported data, one with current OSM data.

 ![download_import](https://cloud.githubusercontent.com/assets/353700/14101326/6f64d14e-f5b1-11e5-9748-8c56995a256d.gif)

### Reviewing the data before uploading

 * Review both data layer for conflicts.
 * Examine tags in both data sets to see if there are any conflicts.
 * If there are any problems you don't know how to deal with, do not proceed. Instead flag the `.osm` file for a more advanced user to look at. 
 (Use github [issues](http://github.com/osmlab/labuildings/issues) to flag concerns, and/or create 
 [OSM notes](http://wiki.openstreetmap.org/wiki/Notes)). Then unlock your task on the tasking manager and pick a new area to work on.

* Preserve the work of previous mappers wherever possible.  If existing buildings in OSM are of higher quality:
  * Copy the tags from the import layer version.
  * Delete the building from the import layer.
  * Switch to the OSM layer.
  * Select the building, paste the tags.

* Manually merge the layers together. 
* If the imported data are of higher quality, select both building and use the **Replace geometry** tool. 
 
 ![replace](https://cloud.githubusercontent.com/assets/353700/12942518/ddba87a4-d001-11e5-9441-2561f67b45bc.gif) 

 *  Run JOSM Validator, if there are errors, fix them. 

![validator](https://cloud.githubusercontent.com/assets/353700/12942520/ddc572f4-d001-11e5-8cf6-399511cd47fa.gif) 

### Finally, upload it

 * Add the tag `#labuildings` to your changesets.
 
![upload](https://cloud.githubusercontent.com/assets/353700/12942517/ddb5c930-d001-11e5-826a-342c3f80f014.gif) 

## What to watch out for

### Validate the import with your eyes before uploading!

 * Run the [JOSM validator](http://wiki.openstreetmap.org/wiki/JOSM/Validator). Check for any errors it detects.
 * Check for small building parts that should be joined to the main building. We've already found a few examples of these in the data (see [issue #19](https://github.com/osmlab/labuildings/issues/19)), so make sure you keep an eye out for these.  To join small parts, select both polygon and select, **Tools > Join overlapping Area**.
 * Inspect everything else with a critical eye! Don't trust that the validator or FIXME tags will catch everything. There may be other bugs that only you can detect. Use your human smarts!
 
### Conflating with existing data
 * Look for any overlaps with existing buildings. Existing buildings in OSM are probably _more_ up-to-date than our imported data. Do not assume the imported data is better, mostly likely it is worse! 
 * Carefully combine the import data with the existing OSM data. If you aren't sure about some tags, ask someone! Especially ask the original mapper! 
 
### How to ground-truth the data
 * Up-to-date aerial imagery... try several sources
 * See if the street is on [Mapillary](http://www.mapillary.com/map/im/bbox/33.65806700735439/34.410308669603495/-119.10278320312499/-117.3504638671875)
 * Go out and check it out yourself! Take a field trip!
 * **DO NOT USE GOOGLE MAPS OR GOOGLE STREET VIEW**

### Identifying New Buildings with imported and existing data
* Aerial imagery used as a basemap should help to identify and draw newer buildings not found in the imported an existing data.
* Newer building should be identified and flagged. (This process should not be done, pending approval and recommendations from the OSM Community.)
 
## Communicate communicate communicate!

### How to ask for help

 * Create [issues](http://github.com/osmlab/labuildings/issues) on this github repo.
 * Ask questions on the [gitter channel](http://gitter.im/osmlab/labuildings).
 * Contact [@almccon](http://twitter.com/almccon), [@cityhubla](http://twitter.com/cityhubla),  [@jschleuss](http://twitter.com/jschleuss),  [@maningsambale](http://twitter.com/maningsambale).

### How to share your progress

 * Make sure you close your task on the tasking manager

### How to communicate with other mappers

 * JOSM [GeoChat](http://wiki.openstreetmap.org/wiki/JOSM/Plugins/GeoChat) feature
 * Twitter hashtag (TBD)
 * Befriend other mappers on openstreetmap.com
