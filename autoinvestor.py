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
import underwriter


###########################
##        CLASSES        ##
###########################

class AutoInvestor:
  """
  Automatically invests in lendingclub notes
  """

  NEW_LOAN_URL = "https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv"






def main():
  pass


if __name__ == '__main__':
  main()
