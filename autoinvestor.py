#!/usr/bin/env python
"""
Attepts to underwrite and invest new loans

Should be used with a cronjob
"""

import csv
import collections
import datetime as dt
import dateutil.parser as dateparser
import time
import urllib
import urllib2
import json
import lendingclub as lc


###########################
##        CLASSES        ##
###########################

class AutoInvestor(lc.Api):
  """
  Automatically invests in lendingclub notes
  """

  def __init__(self, investor_id_path='data/investor_id.txt',
                      api_key_path='data/api_key.txt'):
    with open(investor_id_path) as f:
      investor_id = f.read()

    with open(api_key_path) as f:
      api_key = f.read()

    super(AutoInvestor, self).__init__(investor_id, api_key)

  def poll_loans(self, showAll=False):
    """Rate limited generator of currently listed loans"""
    while True:
      call_time = dt.datetime.now()
      try:
        loans = self.listed_loans(showAll)
        yield loans
      except urllib2.HTTPError as e:
        print e

      # Sleep until ready again
      sleep_time = call_time - dt.datetime.now() + self.RATE_LIMIT
      if sleep_time > dt.timedelta(0):
        time.sleep(sleep_time.total_seconds())

  def poll_until_new_loans(self):
    """Returns a list of newly listed loans when they become avaiable"""
    #Get current list time
    loans = self.listed_loans()
    start_time = dateparser.parse(loans[0]['listD'])
    print "starting at:",dt.datetime.now().time()
    print "last loans listing time:", start_time

    # poll untill the list time is updated
    for i, loans in enumerate(self.poll_loans()):
      if i % 10 == 0:
        print dt.datetime.now().time()
      loan_time = dateparser.parse(loans[0]['listD'])
      if start_time < loan_time:
        return loans

  def save_new_loans_to_file(self, filename='new_loans.json'):
    loans = self.poll_until_new_loans()
    with open(filename,'wb') as f:
      json.dump(loans, f)
  
    print 'Saved new loans to {} at {}'.format(filename, dt.datetime.now().time())
  
    print "Logging number of loans after listing"
    for loans in self.poll_loans():
      print dt.datetime.now().time()
      loans_by_grade(loans)

###########################
##       FUNCTIONS       ##
###########################

def loans_by_grade(loans):
  histogram = collections.defaultdict(int)
  for loan in loans:
    histogram[loan['grade']] += 1

  for grade in histogram.keys():
    print grade+':', histogram[grade], '|',
  print 'total:', len(loans)

def main():
  investor = AutoInvestor('data/investor_id.txt','data/api_key.txt')
  investor.save_new_loans_to_file()


if __name__ == '__main__':
  start = dt.datetime.now()
  try:
    main()
  except KeyboardInterrupt:
    elapsed_time = dt.datetime.now() - start
    print " Ran for {:.2f} seconds".format(elapsed_time.total_seconds())
