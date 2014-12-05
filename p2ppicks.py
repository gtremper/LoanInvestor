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
      "api_key": "a+akdkj3kdfjkp3239", // Lending Club api key
      "investor_id": 93234531,         // Lending Club investor id
      "p2p_key": "87C2FE2B4843AD",     // P2P-Picks key
      "p2p_secret": "ASDKFAJKSDF",     // P2P-Picks secret 
      "p2p_portfolio_id": 34462030     // Portfolio id to assign
    }                                              invested loans
    """
    with open(secrets) as f:
      secrets = json.load(f)
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])
      self.p2p_portfolio_id = int(secrets['p2p_portfolio_id'])

      investor_id = str(secrets['investor_id'])
      api_key = str(secrets['api_key'])
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
    req = urllib2.Request(P2PPicks._BASE_URL.format(method=method, action=action))
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

  def check_loans_available(self):
    """
    Poll for picks and check which of them are available
    for investing.
    """

    picks = self.poll_for_update()
    top = filter(lambda x: x['top'] == '5%', picks)

    p2p_ids = set(int(i['loan_id']) for i in top)
    print "top 5% ids"
    print "P2P IDs:", p2p_ids

    listed = set(x['id'] for x in self.listed_loans())

    available = p2p_ids & listed
    print dt.datetime.now().time()
    print "Available:", available

    print 
    print "Polling for availability"
    while True:
      time.sleep(1)

      listed = set(x['id'] for x in self.listed_loans())
      print dt.datetime.now().time(), p2p_ids & listed

  def invest(self, grades=set(['D','E','F'])):
    """
    Poll for P2P-Picks and invest in them
    Must be called before picks are updated
    """
    picks = self.poll_for_update()
    top = [int(x['loan_id']) for x in picks if x['top'] == '5%' and x['grade'] in grades]

    if not top:
      print "No picks matching critera"
      return

    try:
      res = self.submit_order(top)
    except urllib2.HTTPError as e:
      print e
      return

    pprint.pprint(res)

def main():
  p2p = P2PPicks()
  p2p.invest()

if __name__ == '__main__':
  main()
