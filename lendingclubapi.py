#!/usr/bin/env python
import urllib2
import json


class API:
  """Provides and interface to the LendingClub REST API"""

  _BASE_URL = 'https://api.lendingclub.com/api/investor/v1/accounts/'

  def __init__(self, investor_id, key):
    self.investor_id = id  # Account id
    self.key = key # Api key

  



if __name__ == '__main__':
  