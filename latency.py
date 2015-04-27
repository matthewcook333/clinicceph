# -*- coding: utf-8 -*-
"""
Created on Sun April 5 2015

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
import math

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

fileName = 'timestamps.json'#newtimestamps5apr2015v2.json'
os.chdir(r'/Users/mattcook/Desktop')

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
          }
        },
        "required": [
          "date",
          "time",
          "originTS",
          "receiveTS",
          "transmitTS",
          "destTS"
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

col_heads = ['date', 'time', 'originTS', 'receiveTS', 'transmitTS', 'destTS']
f = lambda c: [c[col] for col in col_heads]
for node in data[:55]:
    try:
        validate(node, nodeSchema)
        row_wise = [col_heads[:]]
        row_wise.extend([f(data_point) for data_point in node['entries']])
        col_wise = zip(*row_wise)
        plt.figure(figure_num)
        newDate = [x * 86400 for x in col_wise[0][1:]]
        entireRoundTrip = [a - b for a, b in zip(col_wise[5][1:], col_wise[2][1:])]
        timeAtServer = [a - b for a, b in zip(col_wise[4][1:], col_wise[3][1:])]
        # round trip time in this case
        values = [a - b for a, b in zip(entireRoundTrip, timeAtServer)]

        times = [sum(x) for x in zip(newDate, col_wise[1][1:])]

        # keep track of last time to compare for faulty values. Hope is that last
        # value is not faulty
        finalTime = times[-1] * 86400.0
        
        prevTime = times[0]
        # zippedList = zip(times,values)#itertools.izip(times,values) 
        # print "Previous length: " + str(len(zippedList))
        # (times, values) = [(time, value) for (time, value) in zippedList
        #                     if time < 1]#4929100000] #1100000 + 4928000000)
        # print "Filtered length: " + str(len(relevantTimes))
        truetimes = []
        truevalues = []
        for time, value in itertools.izip(times,values):
            if time > 4929100000.0:
              continue
            elif value > 200.0 or value < 0.0:
              print "data spike: " + str(value) + " on node: " + node['node']
            elif time < 0 : 
              print "Deleting dummy time: " + str(time)
            else:
              truetimes.append(time)
              truevalues.append(value)
        times = truetimes
        values = truevalues
        # check which cluster this data belongs to, plot to respective graph
        if nodeNames[0] in node['node']:
          plt.figure(1)
          numNodes[0] += 1
          dataSet[0][node['node']] = values
        elif nodeNames[1] in node['node']:
          plt.figure(2)
          numNodes[1] += 1
          dataSet[1][node['node']] = values
        elif nodeNames[2] in node['node']:
          plt.figure(3)
          numNodes[2] += 1
          dataSet[2][node['node']] = values

        plt.scatter(times, values)
    except ValidationError as e:
        #print e
        print "Error on node: " + str(node['node'])

# label all plots
for i in range(0, 3):
  # figures start from 1
  plt.figure(i+1)
  plt.xlabel('Time (s)')
  plt.ylabel('Latency(s)')
  plt.title('Time vs Latency Across %d %s Nodes' % (numNodes[i], nodeNames[i]))
  plt.savefig("latencyscatter" + str(i))

overallStdDevs = []
# make next three histogram plots based on data on each cluster
for i in range(0, 3):
  plt.figure(i+4)

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

  entries, bin_edges, patches = plt.hist(flattened, bins = 100, facecolor = 'green', range = (0, 0.005))
  # add a 'best fit' line
  #y = mlab.normpdf(bin_edges, mu, sigma)
  #plt.plot(bin_edges, y, 'r--')

  # for normalizing
  #for item in patches:
  #    item.set_height(item.get_height()/sum(entries))
      

  axes = plt.gca()
  #axes.set_xlim([0,.005])
  #axes.set_ylim([0,0.001])

  plt.xlabel('Latency (s)')
  plt.ylabel('Count')
  plt.title("Histogram of Latency")
  print r'$\mathrm{Histogram\ of\ Latency\ for\ %s\ nodes:}\ \mu=%.3f,\ \sigma=%.3f$' %(nodeNames[i], mu, sigma)
  #plt.title(r'$\mathrm{Histogram\ of\ Latency\ for\ %s\ nodes:}\ \mu=%.3f,\ \sigma=%.3f$' %(nodeNames[i], mu, sigma))
  plt.savefig("latencyhistogram" + str(i))

print "Overall Standard Dev across " + str(len(overallStdDevs)) + " nodes is " + str(sum(overallStdDevs)/float(len(overallStdDevs)))
   
plt.show()
json_data.close()