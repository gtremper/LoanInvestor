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
  _BASE_URL = "https://www.p2p-picks.com/api/v1/{method}/{action}"

  # Rate limit for the api
  RATE_LIMIT = dt.timedelta(seconds=1.0)

  def __init__(self, secrets='data/secrets.json'):
    with open(secrets) as f:
      secrets = json.load(f)
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])
      self.p2p_portfolio_id = int(secrets['p2p_portfolio_id'])

      investor_id = str(secrets['investor_id'])
      api_key = str(secrets['api_key'])
      super(P2PPicks, self).__init__(investor_id, api_key)

  def request(self, method, action, data):
    #This is required for every request
    data['api_key'] = self.p2p_key

    # Create signature from md5 hash of POST paramaters
    md5 = hashlib.md5()
    md5.update('{}-{}&'.format(method, action))

    for key in sorted(data):
      md5.update('{}{}&'.format(key, data[key]))

    md5.update('secret{}'.format(self.p2p_secret))
    data['sig'] = md5.hexdigest()

    req = urllib2.Request(P2PPicks._BASE_URL.format(method=method, action=action))
    req.add_data(urllib.urlencode(data))

    return json.load(urllib2.urlopen(req))['response']

  def list(self):
    data = self.request('picks', 'list', {'p2p_product': 'profit-maximizer'}) 
    return data['picks'], dateparser.parse(data['timestamp'])

  def poll_picks(self):
    """Rate limited generator of currently listed loans"""
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
    start = dt.datetime.now()
    print "Starting poll at", start
    print

    for picks, timestamp in self.poll_picks():
      if timestamp < start:
        continue
      return picks

  def check_loans_available(self):
    picks = self.poll_for_update()
    top = filter(lambda x: x['top'] == '5%', picks)

    p2p_ids = set(int(i['loan_id']) for i in top)
    print "top 5% ids"
    print "P2P IDs:", p2p_ids

    listed = set(x['id'] for x in self.listed_loans())

    availble = p2p_ids & listed
    print dt.datetime.now().time()
    print "Available:", availble

    print 
    print "Polling for availability"
    while True:
      time.sleep(1)

      listed = set(x['id'] for x in self.listed_loans())
      print dt.datetime.now().time(), p2p_ids & listed

  def invest(self):
    picks = self.poll_for_update()
    top = [int(x['loan_id']) for x in picks if x['top'] == '5%']

    try:
      res = self.submit_order(top, portfolioId=self.p2p_portfolio_id)
    except urllib2.HTTPError as e:
      print e
      return

    print "Invested in", len(top), "loans."
    print "Response:"
    pprint.pprint(res)

def main():
  p2p = P2PPicks()
  p2p.invest()

if __name__ == '__main__':
  main()
