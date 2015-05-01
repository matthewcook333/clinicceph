# -*- coding: utf-8 -*-
"""
Created on Sun April 5 2015

@author: mattcook
"""
import matplotlib.pyplot as plt
import simplejson, os, itertools, re, sys, traceback, math, getopt
from scipy.stats import norm
from jsonschema import validate, ValidationError
import numpy as np

# edit this to change path
#os.chdir(r'/Users/username/path')
fileName = ""

# types of nodes on cluster data. Change to specify different types of nodes
nodeNames = ["burnupi", "mira", "plana"]
# max and min value. Any value above and below this will be removed. This is to remove faulty
# incorrectly logged values
threshold = 900.0
# range for histogram plot
histogramRange = (-40, 40)
# reasonable latency range
#histogramRange = (0, 5)

usage = 'usage: diagnostics.py -i <inputfile> [-f | -t]'

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

def main(argv):
  graphType = ""
  col_heads = []
  graphLabel = ""
  try:
    opts, args = getopt.getopt(argv,"hi:o:tf",["ifile=", "--help", "--freqOffset", "--timestamps"])
  except getopt.GetoptError:
    print usage
    sys.exit(2)
  for opt, arg in opts:
    if opt == "-h" or opt == "--help":
       print usage
       sys.exit()
    elif opt in ("-i", "--ifile"):
       fileName = arg
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
      graphLabel = "Latency (ms)"
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

  # make sure graph type is specified
  if graphType == "" or fileName == "":
    print "Error: Arguments not complete."
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
        # round trip time in milliseconds
        values = [(a - b) * 1000.0 for a, b in zip(entireRoundTrip, timeAtServer)]
      elif graphType == "freqOffset":
        values = list(col_wise[2][1:])

      times = [sum(x) for x in zip(newDate, col_wise[1][1:])]
      # keep track of non-faulty values        
      truetimes = []
      truevalues = []
      for time, value in itertools.izip(times,values):
        if time < 0 or time > 4929100000.0:
          # deleting incorrect or padded entry
          continue
        elif value > abs(threshold):
          # deleting bad values
          print "data spike: " + str(value) + " on node: " + node['node']
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
    # name of scatterplot graph is here
    plt.savefig(graphType + "scatter" + str(i))

  overallValues = []
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
    for (key, values) in dataSet[i].items():
      # if we have a node with empty data, skip
      if len(values) == 0:
        continue
      (muNode, sigmaNode) = norm.fit(values)
      if math.isnan(sigmaNode):
        print values
      stdDevs.append(sigmaNode)
      # uncomment to print stats of each node
      #print "node: " + key + " has mean: " + str(muNode) + " and stdDev: " + str(sigmaNode)
      flattened += values
    overallValues += flattened

    # best fit of data
    (mu, sigma) = norm.fit(flattened)
    median = np.median(flattened)
    print nodeNames[i] + " average standard deviation: " + str(sum(stdDevs)/float(len(stdDevs)))
    overallStdDevs += stdDevs

    entries, bin_edges, patches = plt.hist(flattened, bins = 100, facecolor = 'green', range = histogramRange)
    axes = plt.gca()
    plt.xlabel(graphLabel)
    plt.ylabel('Packet Count')
    plt.title("Histogram of %s across %d %s nodes" % (graphLabel, numNodes[i], nodeNames[i]))
    print "Histogram of %s for %s nodes: mu=%.3f, sigma=%.3f, median=%.3f" %(graphType, nodeNames[i], mu, sigma, median)
    # name of histogram graph is here
    plt.savefig(graphType + "histogram" + str(i))

  print "Overall Standard Dev across " + str(len(overallStdDevs)) + " nodes is " + str(sum(overallStdDevs)/float(len(overallStdDevs)))
  plt.figure((len(nodeNames)*2)+1)
  plt.xlabel(graphLabel)
  plt.ylabel('Packet Count')
  entries, bin_edges, patches = plt.hist(overallValues, bins = 100, facecolor = 'green', range = histogramRange)
  totalNumNodes = sum(numNodes)
  (mu, sigma) = norm.fit(overallValues)
  median = np.median(overallValues)
  plt.title("Histogram of %s across %d nodes" % (graphLabel, totalNumNodes))
  print "Histogram of %s across %d nodes: mu=%.3f, sigma=%.3f, median=%.3f" %(graphType, totalNumNodes, mu, sigma, median)
  plt.savefig(graphType + "histogramtotal")

  plt.show()
  json_data.close()

if __name__ =='__main__':
    main(sys.argv[1:])