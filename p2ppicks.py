#!/usr/bin/env python

"""
Invest in loans via using p2ppicks as an underwriter
"""

import lendingclub as lc
import datetime as dt
import dateutil.parser as dateparser
import hashlib
import json
import time
import urllib
import urllib2
import pprint
import random

class P2PPicks(lc.Api):
  """
  Auto investor using P2P-Picks to underwrite loans
  https://www.p2p-picks.com/
  """

  _BASE_URL = "https://www.p2p-picks.com/api/v1/{method}/{action}"

  # Rate limit for polling an endpoint
  RATE_LIMIT = dt.timedelta(seconds=1.0)

  def __init__(self, secrets='data/secrets.json'):
    """
    secrets: path to a json file containing sensitive information
    {
      "lc_api_key": "a+akdkj3kdfjkp3239", // Lending Club api key
      "lc_investor_id": 93234531,         // Lending Club investor id
      "lc_portfolio_id": 34462030     // Portfolio id to assign invested loans
      "p2p_key": "87C2FE2B4843AD",    // P2P-Picks API key
      "p2p_secret": "ASDKFAJKSDF",    // P2P-Picks API secret 
      "p2p_email": "test@foo.com",    
      "p2p_password": "12345
    """
    with open(secrets) as f:
      secrets = json.load(f)
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])
      self.p2p_email = str(secrets['p2p_email'])
      self.p2p_password = str(secrets['p2p_password'])
      self.lc_portfolio_id = int(secrets['lc_portfolio_id'])

      self.p2p_session, activity = self.validate()

      if activity != "active":
        raise Exception("P2P-Picks account not active")

      # Pass lending club secrets to lc API
      # will set 'self.investor_id' and 'self.api_key'
      investor_id = str(secrets['lc_investor_id'])
      api_key = str(secrets['lc_api_key'])
      super(P2PPicks, self).__init__(investor_id, api_key)

  def request(self, method, action, data):
    """
    Request P2P-Picks REST endpoint
    Returns: JSON response with meta data removed

    method: api method
    action: api action
    data: Dictionary of POST paramaters and values
    """

    # This is required for every request
    data['api_key'] = self.p2p_key

    # Create signature from md5 hash of POST paramaters
    md5 = hashlib.md5()
    md5.update('{}-{}&'.format(method, action))

    for key in sorted(data):
      md5.update('{}{}&'.format(key, data[key]))

    md5.update('secret{}'.format(self.p2p_secret))
    data['sig'] = md5.hexdigest()

    # Send Request
    req = urllib2.Request(
      P2PPicks._BASE_URL.format(method=method, action=action)
    )
    req.add_data(urllib.urlencode(data))

    return json.load(urllib2.urlopen(req))['response']

  def list(self):
    """
    List latests picks for P2P-Picks
    Returns a tuple of
      ([list of picks], timestamp)

    A "pick" is a dictionary as follows
    {
      "grade": "D",
      "load_id": 29383729,
      "term": 36,
      "top": "5%"
    }
    """
    data = self.request('picks', 'list', {'p2p_product': 'profit-maximizer'})
    return data['picks'], dateparser.parse(data['timestamp'])

  def validate(self):
    """
    This method validates the P2P-Picks subscriber's email and
    password and return key information about the P2P-Picks subscriber

    Returns a tuple of
      (p2p subscriber id, status)
    """
    data = self.request('subscriber', 'validate', {
      "p2p_email": self.p2p_email,
      "p2p_password": self.p2p_password
    })

    return str(data['sid']), str(data['status'])

  def report(self, res):
    """
    Report P2P-Picks usage.

    res: the json response to lc.Api.submit_order()
    """
    # Return if no notes invested
    if res['orderInstructId'] is None:
      print "No orders successful"
      return

    orders = res['orderConfirmations']

    # Create  list of successful orders
    picks = [{
      'product': 'profit-maximizer',
      'loan_id': int(order['loanId']),
      'note': int(order['investedAmount'])
    } for order in orders if 'ORDER_FULFILLED' in order['executionStatus']]

    # Build payload JSON object
    p2p_payload = [{
      'sid': self.p2p_session,
      'picks': picks
    }]

    data = {
      'p2p_payload': json.dumps(p2p_payload, separators=(',',':'))
    }

    # Report to P2P-Picks
    res = self.request('subscriber', 'report', data)
    print 'Invested ${} in {} of {} loans'\
          .format(res['note_total'], len(picks), len(orders))


  def poll_picks(self):
    """Rate limited generator of currently listed picks"""
    while True:
      call_time = dt.datetime.now()
      try:
        yield self.list()
      except urllib2.HTTPError as err:
        print "HTTPError: {}".format(err.code)
        time.sleep(2)
      except urllib2.URLError as err:
        print "URLError: {}".format(err.reason)
        time.sleep(2)
      except (KeyboardInterrupt,SystemExit) as err:
        print "err", err
        return
      except Exception as err:
        print "Other exception:", type(err), err
        time.sleep(5)

      # Sleep until ready again
      sleep_time = call_time - dt.datetime.now() + self.RATE_LIMIT
      if sleep_time > dt.timedelta(0):
        time.sleep(sleep_time.total_seconds())

  def poll_for_update(self):
    """
    Start polling for and update in listed P2P-Picks
    Must be called before picks update
    """

    start = dt.datetime.now()
    print "Starting poll at", start
    print

    for i, (picks, timestamp) in enumerate(self.poll_picks()):
      if timestamp < start:
        if i % 10 == 0:
          print dt.datetime.now().time()
        continue
      return picks

  def invest(self, ammount=25.0, grades=frozenset(['D','E','F'])):
    """
    Poll for P2P-Picks and invest in them
    Must be called before picks are updated
    """
    picks = self.poll_for_update()
    top = [int(x['loan_id']) for x in picks 
                                if x['top'] == '5%' and x['grade'] in grades]

    try:
      # Submit order and report activity to P2P-Picks
      res = self.submit_order(top, ammount, self.lc_portfolio_id)
      self.report(res)
    except urllib2.HTTPError as e:
      print e

    print '${:.2f} cash remaining'.format(self.available_cash())


def main():
  p2p = P2PPicks()
  p2p.invest()

if __name__ == '__main__':
  main()
