# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 19:49:34 2015

@author: mattcook
"""
import matplotlib.pyplot as plt
import simplejson
import os
import numpy as np
import matplotlib.mlab as mlab
import scipy.stats as ss
from scipy.stats import norm
from jsonschema import validate, ValidationError
import itertools
import re
import sys
import traceback

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

fileName = 'newfreqOffset2.json'
os.chdir(r'/Users/mattcook/Documents')

json_data = open(fileName)
data = simplejson.load(json_data)

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
          },
          "freqOffset": {
            "id": "freqOffset",
            "type": "number"
          }
        },
        "required": [
          "date",
          "time",
          "freqOffset"
        ]
      }
    }
  },
  "required": [
    "node",
    "entries"
  ]
}


figure_num = 1

axes = plt.gca()

nodeNames = ["burnupi", "mira", "plana"]
numNodes = [0 for x in xrange(len(nodeNames))]
# list of lists for each cluster
dataSet = [{} for x in xrange(len(nodeNames))]

col_heads = ['date', 'time', 'freqOffset']
f = lambda c: [c[col] for col in col_heads]
for node in data:
    try:
        validate(node, nodeSchema)
        row_wise = [col_heads[:]]
        row_wise.extend([f(data_point) for data_point in node['entries']])
        col_wise = zip(*row_wise)
        plt.figure(figure_num)
        newDate = [x * 86400.0 for x in col_wise[0][1:]]
        freqOffsets = list(col_wise[2][1:])

        times = [sum(x) for x in zip(newDate, col_wise[1][1:])]

        # keep track of last time to compare for faulty values. Hope is that last
        # value is not faulty
        finalTime = times[-1] * 86400.0
        
        prevTime = times[0]
        for time,freqOffset in itertools.izip(times,freqOffsets):
            if freqOffset > 200.0 or freqOffset < -200.0:
                print "freqOffset spike: " + str(freqOffset) + " on node: " + node['node']
                times.remove(time)
                freqOffsets.remove(freqOffset)
                prevTime = time
            #elif time > 20*prevTime:
            elif time > finalTime:
                print "time jump: final time is " + str(finalTime) + " with current " + str(time) + " on node: " + node['node']
                times.remove(time)
                freqOffsets.remove(freqOffset)
            else: 
                prevTime = time
        # check which cluster this data belongs to, plot to respective graph
        if nodeNames[0] in node['node']:
          plt.figure(1)
          numNodes[0] += 1
          dataSet[0][node['node']] = freqOffsets
        elif nodeNames[1] in node['node']:
          plt.figure(2)
          numNodes[1] += 1
          dataSet[1][node['node']] = freqOffsets
        elif nodeNames[2] in node['node']:
          plt.figure(3)
          numNodes[2] += 1
          dataSet[2][node['node']] = freqOffsets

        plt.scatter(times, freqOffsets)
    except ValidationError as e:
        print "Error on node: " + str(node['node'])

# label all plots
for i in range(0, 3):
  # figures start from 1
  plt.figure(i+1)
  plt.xlabel('Time (s)')
  plt.ylabel('Freq Offsets (PPM)')
  plt.title('Time vs Frequency Offset Across %d %s Nodes' % (numNodes[i], nodeNames[i]))

overallStdDevs = []
# make next three histogram plots based on data on each cluster
for i in range(0, 3):
  plt.figure(i+4)

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

  entries, bin_edges, patches = plt.hist(flattened, bins = 100, facecolor = 'green', range = (-40, 40))

  axes = plt.gca()

  plt.xlabel('Freq Offset (PPM)')
  plt.ylabel('Count')
  plt.title(r'$\mathrm{Histogram\ of\ Freq Offset\ for\ %s\ nodes:}\ \mu=%.3f,\ \sigma=%.3f$' %(nodeNames[i], mu, sigma))

print "Overall Standard Dev across " + str(len(overallStdDevs)) + " nodes is " + str(sum(overallStdDevs)/float(len(overallStdDevs)))
   
plt.show()
json_data.close()