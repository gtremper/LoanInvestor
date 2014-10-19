#!/usr/bin/env python
import urllib
import urllib2
import json
import datetime as dt
import dateutil.parser as dateparser
import time
import collections

class API:
  """
  Provides and interface to the LendingClub REST API
  https://www.lendingclub.com/developers/lc-api.action
  """
  _API_VERSION = "v1"

  # Url for the loans resource
  _LOAN_URL = "https://api.lendingclub.com/api/investor/{}/loans/listing"\
              .format(_API_VERSION)

  # Rate limit for the api
  _RATE_LIMIT = dt.timedelta(seconds=1.0)

  def __init__(self, investor_id, api_key):
    self.investor_id = investor_id
    self.api_key = api_key
    self._base_url ='https://api.lendingclub.com/api/investor/{}/accounts/{}/{}'\
                    .format(API._API_VERSION, investor_id, '{}')

  def _request_resource(self, resource, data=None):
    """Return json response to resource as dict

    data -- json payload for the request
    """
    req = urllib2.Request(self._base_url.format(resource))
    req.add_header('Authorization', self.api_key)

    if data is not None:
      req.add_data(json.dumps(data))

    try:
      return json.load(urllib2.urlopen(req))
    except urllib2.HTTPError as e:
      print e
      return None

  def available_cash(self):
    """Get the availble cash in your account
    Returns: Float value of remaining cache
    """
    data = self._request_resource("availablecash")
    return data.get('availableCash', None)

  def summary(self):
    """
    Returns: Dict of account info
    """
    return self._request_resource("summary")

  def notes_owned(self, detailed=False):
    data = self._request_resource("detailednotes" if detailed else "notes")

    if data is None:
      return None

    notes = data['myNotes']

    for note in notes:
      note['issueDate'] = dateparser.parse(note['issueDate'])
      note['orderDate'] = dateparser.parse(note['orderDate'])
      note['loanStatusDate'] = dateparser.parse(note['loanStatusDate'])

      if detailed:
        note['lastPaymentDate'] = dateparser.parse(note['lastPaymentDate'])
        note['nextPaymentDate'] = dateparser.parse(note['nextPaymentDate'])

    return notes

  def portfolios_owned(self):
    """get list of portfolios owned"""
    data = self._request_resource("portfolios")
    return data.get('myPortfolios', None)

  def create_portfolio(self, name, desc=""):
    """Create a new portfolio"""
    payload = {
      "aid": self.investor_id,
      "portfolioName": name,
      "portfolioDescription": desc
    }
    return self._request_resource("portfolios", data=payload)

  def submit_order(self, loanIds, ammount, portfolioId=None):
    """
    submit and order for some loans
    loanIds -- a list of loanIds to purchase
    ammount -- ammount to invest per loan (must be multiple of 25)
    portfolioId -- The portfolio to assign notes to
    """

  def listed_loans(self, showAll=False):
    """
    Get currently listed loans
    showAll -- Get all listed loans instead of just the most recent
    """
    req = urllib2.Request(
      (API._LOAN_URL + "?showAll=true") if showAll else API._LOAN_URL
    )

    req.add_header('Authorization', self.api_key)

    try:
      data = json.load(urllib2.urlopen(req))
    except urllib2.HTTPError as e:
      print e
      return None

    loans = data['loans']
    return loans, dateparser.parse(data['asOfDate'])

  def poll_loans(self, f, showAll=False):
    """loop calling 'f()' with a list of loans"""
    while True:

      #Call function
      loans, call_time = self.listed_loans(showAll)
      f(loans)

      print call_time

      #Rate limit to 1 second
      wakeup = call_time + API._RATE_LIMIT
      sleep_time = wakeup - dt.datetime.now(wakeup.tzinfo)
      sleep_time = sleep_time.total_seconds()

      if sleep_time > 0.0:
        time.sleep(sleep_time)

def load_api(investor_id_path, api_key_path):
  """ create an api instance from secrets stored in files

  investor_id_path -- path to file containing investor id
  api_key_path -- path to file containing api secret key
  """

  with open(investor_id_path) as f:
    investor_id = f.read()

  with open(api_key_path) as f:
    api_key = f.read()

  return API(investor_id, api_key)

def new_loans(loans):
    if loans is not None:
      histogram = collections.defaultdict(int)
      for loan in loans:
        histogram[loan['grade']] += 1

      for grade in sorted(histogram.keys()):
        print grade+':', histogram[grade], '|',
      print

def main():
  api = load_api("investor_id.txt", "api_key.txt")
  api.poll_loans(new_loans)

if __name__ == '__main__':
  main()
