#!/usr/bin/env python
"""
Attepts to underwrite and invest new loans

Should be used with a cronjob
"""
from collections import Counter
from dateutil import parser

import csv
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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

def read_loans():
  return urllib.urlopen("https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv")

def main():
  # Read csv enpoint from lendingclub
  resource = read_loans()
  notes = csv.DictReader(resource)

  # get list of datetimes for current notes
  list_dates = [parser.parse(x['list_d']) for x in notes]
  list_dates = map(lambda x: x-dt.timedelta(minutes=x.minute, seconds=x.second) ,list_dates)

  #count unique times
  c = Counter(list_dates)

  counts = sorted(c.iteritems(), key=lambda x: x[0])

  total = 0
  for date, count in counts:
    total += count
    print date, count
  print "Total:", total
  

def funded():
  resource = read_loans()
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
  rounded = t - dt.timedelta(minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
  if t.hour > 18 or t.hour < 6:
    rounded -= dt.timedelta(hours=t.hour-18)
  elif t.hour > 14:
    rounded -= dt.timedelta(hours=t.hour-14)
  elif t.hour > 10:
    rounded -= dt.timedelta(hours=t.hour-10)
  else:
    rounded -= dt.timedelta(hours=t.hour-6)

  return rounded

def check_new_loans():
    resource = read_loans()
    loans = list(csv.DictReader(resource))
    now = round_time_to_last_release(dt.datetime.now())
    if any(parser.parse(x['list_d']) > now for x in loans):
      print "New Loans!!! "
      print dt.datetime.now()
      print "########################"
      new_loans = filter(lambda x: parser.parse(x['list_d']) > now, loans)

      for loan in sorted(new_loans, key=lambda x: float(x['int_rate'])):
        print loan['list_d'], loan['int_rate']
      print "Total new:", len(new_loans)

      return True
    else:
      print "no new loans " + str(dt.datetime.now())
      return False

def poll_for_loans():
  while not check_new_loans():
    pass

def num_available_loans():
  return sum(1 for x in read_loans())

def plot_available_loans(delta=dt.timedelta(minutes=2)):
  poll_for_loans()

  num_loans = []

  start_time = dt.datetime.now()
  while dt.datetime.now() < start_time + delta:
    num_loans.append(num_available_loans())
    time_remaining = start_time + delta - dt.datetime.now()
    print len(num_loans), str(time_remaining.seconds) + " seconds remaining"

  plt.plot(num_loans)
  plt.show()


if __name__ == '__main__':
  plot_available_loans(dt.timedelta(minutes=2))

