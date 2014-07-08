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

###########################
##      CONSTANTS        ##
###########################

HISTORICAL_DATA_PATH = "data/HistoricalLoanData.csv"

###########################
##        CLASSES        ##
###########################

class AutoInvestor:
  pass

###########################
##        FUNCTIONS      ##
###########################

def load_historical_data():
  with open(HISTORICAL_DATA_PATH, "r") as f:
    return list(csv.DictReader(f))

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

def round_time_to_last_release(t):
  rounded = t - datetime.timedelta(minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
  if t.hour > 18 or t.hour < 6:
    rounded -= datetime.timedelta(hours=t.hour-18)
  elif t.hour > 14:
    rounded -= datetime.timedelta(hours=t.hour-14)
  elif t.hour > 10:
    rounded -= datetime.timedelta(hours=t.hour-10)
  else:
    rounded -= datetime.timedelta(hours=t.hour-6)

  return rounded

def check_new_loans():

    resource = urllib.urlopen("https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv")
    loans = list(csv.DictReader(resource))
    now = round_time_to_last_release(datetime.datetime.now())
    if any(parser.parse(x['list_d']) > now for x in loans):
      print "New Loans!!! "
      print datetime.datetime.now()
      print "########################"
      new_loans = filter(lambda x: parser.parse(x['list_d']) > now, loans)

      for loan in sorted(new_loans, key=lambda x: float(x['int_rate'])):
        print loan['list_d'], loan['int_rate']
      print "Total new:", len(new_loans)

      return True
    else:
      print "no new loans " + str(datetime.datetime.now())
      return False



if __name__ == '__main__':
  while not check_new_loans():
    pass
  print "done!"

