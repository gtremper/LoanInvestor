#!/usr/bin/env python
"""
Attepts to underwrite and invest new loans

Should be used with a cronjob
"""

import csv
import datetime as dt
import dateutil.parser as dateparser
import time
import urllib
import urllib2
import json

with open("data/api_key.txt") as f:
  SECRET = f.read()

with open('data/investor_id.txt') as f:
  INVESTOR_ID = f.read()

CASH_URL = 'https://api.lendingclub.com/api/investor/v1/accounts/'+INVESTOR_ID+'/availablecash'


###########################
##        CLASSES        ##
###########################

class AutoInvestor:
  """
  Automatically invests in lendingclub notes
  """
  pass

def print_cash():
  req = urllib2.Request(CASH_URL)
  req.add_header('Authorization', SECRET)

  try:
    response = urllib2.urlopen(req)
  except urllib2.HTTPError as e:
    print e

  data = json.load(response)
  print data['availableCash']

def main():
  print_cash()


if __name__ == '__main__':
  main()
