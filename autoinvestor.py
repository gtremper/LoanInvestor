#!/usr/bin/env python
"""
Attepts to underwrite and invest new loans

Should be used with a cronjob
"""
from collections import Counter
from dateutil import parser

import csv
import datetime
import matplotlib.pyplot as plt
import time
import urllib

class AutoInvestor:
  pass

def main():
  # Read csv enpoint from lendingclub
  resource = urllib.urlopen("https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv")
  notes = csv.DictReader(resource)

  # get list of datetimes for current notes
  list_dates = [parser.parse(x['list_d']) for x in notes]
  list_dates = map(lambda x: x-datetime.timedelta(minutes=x.minute, seconds=x.second) ,list_dates)

  #count unique times
  c = Counter(list_dates)

  counts = sorted(c.iteritems(), key=lambda x: x[0])

  total = 0
  for date, count in counts:
    total += count
    print date, count
  print "Total:", total
  

def funded():
  resource = urllib.urlopen("https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv")
  notes = csv.DictReader(resource)
  notes = [x for x in notes]

  percent_funded = lambda x: float(x['funded_amnt']) / float(x['loan_amnt'])

  total = 0.0
  for note in notes:
    total += float(note['funded_amnt'])

  return total

def plot_total_funded():
  totals = []
  for i in xrange(200):
    print i
    totals.append(funded())
    time.sleep(5)

  plt.plot(totals)
  plt.show()


if __name__ == '__main__':
  #main()
  print funded()

