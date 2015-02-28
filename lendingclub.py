#!/usr/bin/env python

"""
Wrapper of all LendingClub API endpoints. Required rate-limiting
of API calls is handled automatically.
"""

import datetime as dt
import json
import pprint
import time
import urllib2

__all__ = ['API']

class API:
  """
  Provides and interface to the LendingClub REST API
  https://www.lendingclub.com/developers/lc-api.action
  """
  # Url for the loans resource
  _LOAN_URL = "https://api.lendingclub.com/api/investor/v1/loans/listing"

  # Rate limit for the api.
  # All api calls share this ratelimit, as
  # specified in LendingClub's guidelines.
  LC_RATE_LIMIT = dt.timedelta(seconds=1.0)

  def __init__(self, investor_id, api_key):
    """
    investor_id: LendingClub investor investor_id
    api_key: LendingClub api key
    """
    self.lc_investor_id = investor_id
    self.lc_api_key = api_key

    # Url for all account actions
    self._base_url ='https://api.lendingclub.com/api/investor/v1/accounts/{}/{}'\
                    .format(investor_id, '{}')

    # Last time an api call was made (for rate limiting)
    self.last_api_call = dt.datetime(year=2000,month=1,day=1)

  def _wait_for_timeout(self):
    """
    Wait until `LC_RATE_LIMIT` time has passed since the last API call
    Time of last call stored in `last_api_call`
    This should be called right before the rate-limited action
    """
    sleep_time = self.last_api_call - dt.datetime.now() + self.LC_RATE_LIMIT
    if sleep_time > dt.timedelta(0):
      time.sleep(sleep_time.total_seconds())

    # Update last call
    self.last_api_call = dt.datetime.now()

  def _request_resource(self, resource, data=None):
    """Return json response to resource as dict
    All api actions share a rate limit specified
    in LC_RATE_LIMIT.

    data -- json payload for the request
    """
    req = urllib2.Request(self._base_url.format(resource))
    req.add_header('Authorization', self.lc_api_key)

    if data is not None:
      req.add_header('Accept', 'application/json')
      req.add_header('Content-type', 'application/json')
      req.add_data(json.dumps(data, separators=(',',':')))

    # Rate limit all api calls
    self._wait_for_timeout()

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
      "aid": int(self.lc_investor_id),
      "portfolioName": name,
      "portfolioDescription": desc
    }
    return self._request_resource("portfolios", data=payload)

  def submit_order(self, loanIds, ammount=25.0, portfolioId=None):
    """
    submit and order for some loans
    loanIds -- a list of loanIds to purchase
    ammount -- ammount to invest per loan (must be multiple of 25)
    portfolioId -- The portfolio to assign notes to
    """
    payload = {}
    payload['aid'] = int(self.lc_investor_id)
    payload['orders']= [{
      "loanId": int(lid),
      "requestedAmount": float(ammount),
      "portfolioId": int(portfolioId)
    } if portfolioId is not None else {
      "loanId": int(lid),
      "requestedAmount": float(ammount)
    } for lid in loanIds]

    return self._request_resource('orders', data=payload)

  def listed_loans(self, showAll=False):
    """
    Get currently listed loans
    showAll -- Get all listed loans instead of just the most recent
    """
    # Build request
    req = urllib2.Request(
      (API._LOAN_URL + "?showAll=true") if showAll else API._LOAN_URL
    )
    req.add_header('Authorization', self.lc_api_key)

    # Ratelimit call
    self._wait_for_timeout()

    # Query endpoint
    data = json.load(urllib2.urlopen(req))
    return data['loans'] if 'loans' in data else None


def main():
  # standard secrets file location
  with open('secrets.json') as f:
    secrets = json.load(f)
    investor_id = secrets['lc_investor_id']
    api_key = secrets['lc_api_key']

  api = API(investor_id, api_key)

  print "\nCash"
  pprint.pprint(api.available_cash())
  print "\nSummary"
  pprint.pprint(api.summary())
  print "\nNotes owned: ", len(api.notes_owned())
  print "\nPortfolios owned"
  pprint.pprint(api.portfolios_owned())
  print "\nFirst listed loan"
  pprint.pprint(api.listed_loans()[0])

if __name__ == '__main__':
  main()
