#!/usr/bin/python

#-----------------------------------------------------------------
# @file: crawler.py
# @description: wrapper for Gobblin which handles config file
#               parsing and glue logic
#-----------------------------------------------------------------

import sys
import os
import config
import subprocess
import time
import glob

# generate Gobblin .pull file
pull_file = open("gobblin/test_config/simplejson.pull", "w")
pull_file.write("""
#########################################################################
############### Autogenerated Gobblin configuration file ################
#########################################################################

job.name=GobblinCrawl
job.group=crawler
job.description=A Gobblin job for the metadata crawler
""")
pull_file.write("job.schedule=" + config.schedule)
pull_file.write("""

source.class=gobblin.example.simplejson.SimpleJsonSource
converter.classes=gobblin.example.simplejson.SimpleJsonConverter
extract.namespace=gobblin.example.simplejson

# source configuration properties
# comma-separated list of file URIs (supporting different schemes, e.g., file://, ftp://, sftp://, http://, etc)
""");

pull_file.write('source.filebased.files.to.pull=')
for d in config.directories_to_crawl:
  pull_file.write(d + ',')
pull_file.write("""
# source data schema
source.schema={"namespace":"example.avro", "type":"record", "name":"User", "fields":[{"name":"lastAccessTime", "type":"string"}, {"name":"lastModifiedTime",  "type":"string"}, {"name":"creationTime", "type":"string"} , {"name":"size", "type":"string"}, {"name":"isSymbolicLink", "type":"string"}, {"name":"isRegularFile", "type":"string"}, {"name":"isOther", "type":"string"}, {"name":"isDirectory", "type":"string"}]}

# quality checker configuration properties
qualitychecker.task.policies=gobblin.policies.count.RowCountPolicy,gobblin.policies.schema.SchemaCompatibilityPolicy
qualitychecker.task.policy.types=OPTIONAL,OPTIONAL
qualitychecker.row.policies=gobblin.policies.schema.SchemaRowCheckPolicy
qualitychecker.row.policy.types=OPTIONAL
qualitychecker.row.err.file=test/jobOutput

# data publisher class to be used
data.publisher.type=gobblin.publisher.BaseDataPublisher

# writer configuration properties
writer.destination.type=HDFS
writer.output.format=AVRO
writer.fs.uri=file:///
""")

pull_file.close()

# start a monitor to check for new files in the job output directory
# TODO: call react_wrapper.sh in a subprocess, replace 'action' script test.sh with an scp call to destination machine

# run Gobblin
os.chdir("gobblin")
subprocess.call(["./run_gobblin_standalone.sh"])

# collect and merge avro files
os.chdir("test_workdir/job-output/gobblin/example/simplejson/ExampleTable/")
results_dir = glob.glob("*_append")
os.chdir(results_dir[0])
results = glob.glob("*.avro")

# put the merged file in a less volatile directory (so that the Mover Monitor can find it)
os.chdir("../")
merged_avro = open("merged.avro", "w")
for r in results:
  for line in open(results_dir[0] + "/" + r, "r"):
    merged_avro.write(line + "\n")
    #TODO: this is weird b/c avro isn't a plain text file anyway, so adding newlines seems to just mess things up
