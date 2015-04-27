# -*- coding: utf-8 -*-
"""
Created on Sun April 5 2015

@author: mattcook
"""
import matplotlib.pyplot as plt
import simplejson, os, itertools, re, sys, traceback, math
#import numpy as np
#import matplotlib.mlab as mlab
#import scipy.stats as ss
from scipy.stats import norm
from jsonschema import validate, ValidationError
# import itertools
# import re
# import sys
# import traceback
# import math


os.chdir(r'/Users/mattcook/Desktop')
fileName = 'timestamps.json'#newtimestamps5apr2015v2.json'

# types of nodes on cluster data. Change to specify different types of nodes
nodeNames = ["burnupi", "mira", "plana"]
# max value. Any value above this will be removed. This is to remove faulty
# incorrectly logged values
maxValue = 1000
# range for histogram plot
histogramRange = (0, 0.005)

graphType = ""
col_heads = []
graphLabel = ""
usage = 'usage: diagnostics.py -i <inputfile> -o <outputfile> {-f, -t}'

nodeSchema = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "id": "/",
  "type": "object",
  "properties": {
    "node": {
      "id": "node",
      "type": "string"
    },
    "entries": {
      "id": "entries",
      "type": "array",
      "items": {
        "id": "1",
        "type": "object",
        "properties": {
          "date": { 
            "id": "date",
            "type": "integer"
          },
          "time": {
            "id": "time",
            "type": "number"
          }
        },
      }
    }
  },
  "required": [
    "node",
    "entries"
  ]
}

inputfile = ''
outputfile = ''
try:
  opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
except getopt.GetoptError:
  print usage
  sys.exit(2)
for opt, arg in opts:
  if opt == '-h':
     print usage
     sys.exit()
  elif opt in ("-i", "--ifile"):
     inputfile = arg
  elif opt in ("-o", "--ofile"):
     outputfile = arg
  elif opt in ("-f", "--freqOffset"):
    graphType = "freqOffset"
    graphLabel = "Frequency Offset (PPM)"
    col_heads =['date', 'time', 'freqOffset']
    # update schema with properties and make them required
    nodeSchema["properties"]["entries"]["items"]["properties"].update( {
      "freqOffset": {
        "id": "freqOffset",
        "type": "number"
      }})
    nodeSchema["properties"]["entries"]["items"].update(
      {"required" : ["date", "time", "freqOffset"]})
  elif opt in ("-t", "--timestamps"):
    graphType = "latency"
    graphLabel = "Latency (s)"
    col_heads = ['date', 'time', 'originTS', 'receiveTS', 'transmitTS', 'destTS']
    nodeSchema["properties"]["entries"]["items"]["properties"].update( {
      "originTS": {
        "id": "originTS",
        "type": "number"
      },
      "receiveTS": {
        "id": "receiveTS",
        "type": "number"
      },
      "transmitTS": {
        "id": "transmitTS",
        "type": "number"
      },
      "destTS": {
        "id": "destTS",
        "type": "number"
      }})
    nodeSchema["properties"]["entries"]["items"].update({"required" : 
      ["date", "time", "originTS", "receiveTS", "transmitTS", "destTS"]})
            
print 'Input file is "', inputfile
print 'Output file is "', outputfile


# make sure graph type is specified
if graphType == "":
  print "Error: No property type specified."
  print usage
  sys.exit(0)

json_data = open(fileName)
data = simplejson.load(json_data)

figure_num = 1
axes = plt.gca()
numNodes = [0 for x in xrange(len(nodeNames))]
# list of lists for each cluster
dataSet = [{} for x in xrange(len(nodeNames))]
f = lambda c: [c[col] for col in col_heads]
# can change data to limit which nodes to plot, i.e. data[:55] will get first 55 nodes
for node in data:
  try:
    validate(node, nodeSchema)
    row_wise = [col_heads[:]]
    row_wise.extend([f(data_point) for data_point in node['entries']])
    col_wise = zip(*row_wise)
    plt.figure(figure_num)
    newDate = [x * 86400 for x in col_wise[0][1:]]
    values = []
    if graphType == "latency":
      entireRoundTrip = [a - b for a, b in zip(col_wise[5][1:], col_wise[2][1:])]
      timeAtServer = [a - b for a, b in zip(col_wise[4][1:], col_wise[3][1:])]
      # round trip time
      values = [a - b for a, b in zip(entireRoundTrip, timeAtServer)]
    elif graphType == "freqOffset":
      values = list(col_wise[2][1:])

    times = [sum(x) for x in zip(newDate, col_wise[1][1:])]
    # keep track of non-faulty values        
    truetimes = []
    truevalues = []
    for time, value in itertools.izip(times,values):
      if value > maxValue or value < 0.0:
        # deleting bad values
        print "data spike: " + str(value) + " on node: " + node['node']
      elif time < 0 : 
        # deleting incorrect or padded entry
        continue
      else:
        truetimes.append(time)
        truevalues.append(value)
    times = truetimes
    values = truevalues
    # check which cluster this data belongs to, plot to respective graph
    for nodeNum in range(len(nodeNames)):
      if nodeNames[nodeNum] in node['node']:
        plt.figure(nodeNum+1)
        numNodes[nodeNum] += 1
        dataSet[nodeNum][node['node']] = values

    plt.scatter(times, values)
  except ValidationError as e:
    print "Error on node: " + str(node['node'])

# label all plots
for i in range(len(nodeNames)):
  # figures start from 1
  plt.figure(i+1)
  plt.xlabel('Time (s)')
  plt.ylabel(graphLabel)
  plt.title('Time vs %s Across %d %s Nodes' % (graphType, numNodes[i], nodeNames[i]))
  plt.savefig(graphType + "scatter" + str(i))

overallStdDevs = []
# make next three histogram plots based on data on each cluster
for i in range(len(nodeNames)):
  # need to offset by the figures for previous scatterplots
  plt.figure(i+1+len(nodeNames))
  # skip if no data for given node type
  if len(dataSet[i].items()) == 0:
    continue
  flattened = []
  stdDevs = []
  for (key, value) in dataSet[i].items():
    (muNode, sigmaNode) = norm.fit(value)
    stdDevs.append(sigmaNode)
    print "node: " + key + " has mean: " + str(muNode) + " and stdDev: " + str(sigmaNode)
    flattened += value

  # best fit of data
  (mu, sigma) = norm.fit(flattened)
  print "overall these have std dev: " + str(sum(stdDevs)/float(len(stdDevs)))
  overallStdDevs += stdDevs

  entries, bin_edges, patches = plt.hist(flattened, bins = 100, facecolor = 'green', range = histogramRange)
  axes = plt.gca()
  plt.xlabel(graphLabel)
  plt.ylabel('Count')
  plt.title("Histogram of %s" % (graphLabel))
  print r'$\mathrm{Histogram\ of\ %s\ for\ %s\ nodes:}\ \mu=%.3f,\ \sigma=%.3f$' %(graphType, nodeNames[i], mu, sigma)
  plt.savefig(graphType + "histogram" + str(i))

print "Overall Standard Dev across " + str(len(overallStdDevs)) + " nodes is " + str(sum(overallStdDevs)/float(len(overallStdDevs)))
   
plt.show()
json_data.close()