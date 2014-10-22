#!/usr/bin/env python
import urllib
import urllib2
import json
import datetime as dt
import dateutil.parser as dateparser
import time
import numpy as np
import re

__all__ = ['Api']

class Api(object):
  """
  Provides and interface to the LendingClub REST API
  https://www.lendingclub.com/developers/lc-api.action
  """
  _API_VERSION = "v1"

  # Url for the loans resource
  _LOAN_URL = "https://api.lendingclub.com/api/investor/{}/loans/listing"\
              .format(_API_VERSION)

  # Rate limit for the api
  RATE_LIMIT = dt.timedelta(seconds=1.0)

  def __init__(self, investor_id, api_key):
    self.investor_id = investor_id
    self.api_key = api_key
    self._base_url ='https://api.lendingclub.com/api/investor/{}/accounts/{}/{}'\
                    .format(Api._API_VERSION, investor_id, '{}')

  def _request_resource(self, resource, data=None):
    """Return json response to resource as dict

    data -- json payload for the request
    """

    req = urllib2.Request(self._base_url.format(resource))
    req.add_header('Authorization', self.api_key)

    if data is not None:
      req.add_data(json.dumps(data, separators=(',',':')))


    return json.load(urllib2.urlopen(req))

  def available_cash(self):
    """Get the availble cash in your account
    Returns: Float value of remaining cache
    """
    data = self._request_resource("availablecash")
    return data['availableCash']

  def summary(self):
    """
    Returns: Dict of account info
    """
    return self._request_resource("summary")

  def notes_owned(self, detailed=False):
    """
    Returns: list of notes owned 
    if 'datailed' is true, more information is provided for each loan
    """
    data = self._request_resource("detailednotes" if detailed else "notes")
    return data['myNotes']

  def portfolios_owned(self):
    """get list of portfolios owned"""
    data = self._request_resource("portfolios")
    return data['myPortfolios']

  def create_portfolio(self, name, desc=""):
    """Create a new portfolio"""
    payload = {
      "aid": self.investor_id,
      "portfolioName": name,
      "portfolioDescription": desc
    }
    return self._request_resource("portfolios", data=payload)

  def submit_order(self, loanIds, ammount=25, portfolioId=None):
    """
    submit and order for some loans
    loanIds -- a list of loanIds to purchase
    ammount -- ammount to invest per loan (must be multiple of 25)
    portfolioId -- The portfolio to assign notes to
    """
    payload = {}
    payload['aid'] = self.investor_id
    payload['orders']= [{
      "loadId": lid,
      "requestedAmount": ammount,
      "portfolioId": portfolioId
    } if portfolioId is not None else {
      "loadId": lid,
      "requestedAmount": ammount
    } for lid in loanIds]

    return self._request_resource('orders', data=payload)

  def listed_loans(self, showAll=False):
    """
    Get currently listed loans
    showAll -- Get all listed loans instead of just the most recent
    """
    req = urllib2.Request(
      (Api._LOAN_URL + "?showAll=true") if showAll else Api._LOAN_URL
    )

    req.add_header('Authorization', self.api_key)

    data = json.load(urllib2.urlopen(req))
    return data['loans']


def main():
  with open('data/investor_id.txt') as f:
    investor_id = f.read()

  with open('data/api_key.txt') as f:
    api_key = f.read()

  api = Api(investor_id, api_key)
  print "\nCash"
  print api.available_cash()
  print "\nSummary"
  print api.summary()
  print "\nNotes owned"
  print "num notes owned", len(api.notes_owned())
  print "\nportfolios owned"
  print api.portfolios_owned()
  print "\nListed loans"
  print "first loans:", api.listed_loans()[0]

if __name__ == '__main__':
  main()
