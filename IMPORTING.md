How to import
=============

**NOTE: THIS DOCUMENT IS A WORK IN PROGRESS**

**ALSO: THE IMPORT HAS NOT YET BEEN APPROVED BY THE OPENSTREETMAP COMMUNITY**

**DO NOT IMPORT ANY DATA UNTIL THESE INSTRUCTIONS HAVE BEEN FINALIZED AND THE IMPORT HAS BEEN APPROVED**

## Getting started

### Creating an import account

 * OSM best practices require that you do not use your normal OSM account for the imports. Create a new account for this purpose. 

### Getting familiar with JOSM

 * learnosm tutorials?

### Check out a task on the tasking manager

 * tasks will be available on the openstreetmap.us tasking manager
 * priority: we are working on LA City first
 * why? because different parts of the county have different data problems to watch out for. If we all run into the same problems at the same time, it will be easier for us to help each other and improve the processing scripts and the import workflow.

## Import workflow
 * Load the .osm file from the tasking manager
 
### Finally, upload it

 * Add the tag #labuildings to your changesets

## What to watch out for

### Validate the import with your eyes before uploading!

 * Run the JOSM validator. Check for any errors it detects.
 * Look for any FIXME tags that the processing scripts generated. These are areas that need human oversight.
 * Inspect everything else with a critical eye! Don't trust that the validator or FIXME tags will catch everything. There may be other bugs that only you can detect. Use your human smarts!
 
### Conflating with existing data
 * Look for any overlaps with existing buildings. Existing buildings in OSM are probably _more_ up-to-date than our imported data. Do not assume the imported data is better, mostly likely it is worse! 
 * Carefully combine the import data with the existing OSM data. If you aren't sure about some tags, ask someone! Especially ask the original mapper! 
 
### How to ground-truth the data
 * Up-to-date aerial imagery... try several sources
 * See if the street is on [Mapillary](mapillary.com)
 * Go out and check it out yourself! Take a field trip!
 * **DO NOT USE GOOGLE MAPS OR GOOGLE STREET VIEW**
 


## Communicate communicate communicate!

### How to ask for help

 * Create issues on this github repo
 * Ask questions on IRC
 * contact @almccon, @cityhubla, others

### How to share your progress

 * Make sure you close your task on the tasking manager

### How to communicate with other mappers

 * JOSM chat feature
 * Twitter hashtag (TBD)
 * Befriend other mappers on openstreetmap.com