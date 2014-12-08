#!/usr/bin/env python

"""
Invest in loans via using p2ppicks as an underwriter
"""

import lendingclub as lc
import datetime as dt
from datetime import datetime
import dateutil.parser as dateparser
import hashlib
import json
import time
import urllib
import urllib2
import pprint
import logging
import os

# Set up logging
logger = logging.getLogger('P2P-Picks')
logger.setLevel(logging.DEBUG)

class P2PPicks(lc.Api):
  """
  Auto investor using P2P-Picks to underwrite loans
  https://www.p2p-picks.com/
  """

  _BASE_URL = "https://www.p2p-picks.com/api/v1/{method}/{action}"

  # Rate limit for polling an endpoint
  P2P_RATE_LIMIT = dt.timedelta(seconds=0.1)

  # Investment configurations
  AMOUNT_PER_LOAN = 25.0
  GRADES = frozenset(['D','E','F'])
  PICK_LEVEL = frozenset(['5%'])

  def __init__(self, secrets='data/secrets.json'):
    """
    secrets: path to a json file containing sensitive information
    {
      "lc_api_key": "a+akdkj3kdfjkp3239", // Lending Club api key
      "lc_investor_id": 93234531,         // Lending Club investor id
      "lc_portfolio_id": 34462030     // Portfolio id to assign invested loans
      "p2p_key": "87C2FE2B4843AD",    // P2P-Picks API key
      "p2p_secret": "ASDKFAJKSDF",    // P2P-Picks API secret 
      "p2p_sid": "384FBC34D3AB"      // P2P-Picks session ID    
    """
    with open(secrets) as f:
      secrets = json.load(f)

      # Store secrets
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])
      self.p2p_sid = str(secrets['p2p_sid'])
      self.lc_portfolio_id = int(secrets['lc_portfolio_id'])

      if not self.isActive():
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

  def validate(self, email, password):
    """
    This method validates the P2P-Picks subscriber's email and
    password and return key information about the P2P-Picks subscriber

    Returns a tuple of
      (p2p_subscriber_id, status)
    """
    data = self.request('subscriber', 'validate', {
      "p2p_email": email,
      "p2p_password": password
    })

    return str(data['sid']), str(data['status'])

  def isActive(self):
    data =self.request('subscriber', 'status', {'p2p_sid': self.p2p_sid})
    return data['status'] == 'active'

  def report(self, res):
    """
    Report P2P-Picks usage.

    res: the json response to lc.Api.submit_order()
    """
    # Return if passed empty list
    if 'orderConfirmations' not in res:
      return

    orders = res['orderConfirmations']

    # Return if no notes invested
    if res['orderInstructId'] is None:
      return

    # Create  list of successful orders
    picks = [{
      'product': 'profit-maximizer',
      'loan_id': int(order['loanId']),
      'note': int(order['investedAmount'])
    } for order in orders if int(order['investedAmount'])]

    # Build payload JSON object
    p2p_payload = [{
      'sid': self.p2p_sid,
      'picks': picks
    }]

    data = {
      'p2p_payload': json.dumps(p2p_payload, separators=(',',':'))
    }

    # Report to P2P-Picks
    self.request('subscriber', 'report', data)


  def poll_picks(self):
    """Rate limited generator of currently listed picks"""
    while True:
      call_time = datetime.now()
      try:
        yield self.list()
      except urllib2.HTTPError as err:
        logger.error("HTTPError: {}".format(err.code))
        time.sleep(2)
      except urllib2.URLError as err:
        logger.error("URLError: {}".format(err.reason))
        time.sleep(2)
      except (KeyboardInterrupt,SystemExit) as err:
        # We're trying to quit
        return
      except Exception as err:
        logger.critical("Other exception:", type(err), err)
        time.sleep(5)

      # Sleep until ready again
      sleep_time = call_time - datetime.now() + self.P2P_RATE_LIMIT
      if sleep_time > dt.timedelta(0):
        time.sleep(sleep_time.total_seconds())

  def poll_for_update(self):
    """
    Start polling for and update in listed P2P-Picks
    Must be called before picks update
    """

    start = datetime.now()
    logger.debug("Starting poll")

    for picks, timestamp in self.poll_picks():
      if timestamp > start:
        return picks

  def invest(self, load_ids):
    """
    Poll for P2P-Picks and invest in them
    Must be called before picks are updated

    picks: a list of load ids to submit orders for
    amount: amount to invest per loan
    grade: Loan grades to accept
    """
    try:
      # Submit order and report activity to P2P-Picks
      res = self.submit_order(load_ids,
                  self.AMOUNT_PER_LOAN, self.lc_portfolio_id)
      self.report(res)
      return res
    except urllib2.HTTPError as e:
      logger.error(e)

    return res

  def log_results(self, res):
    """
    Log details of investment response
    response: Return value of self.invest()
    """

    if 'orderConfirmations' not in res:
      logger.error('Attempted to invest in an empty list of loans')

    for order in res['orderConfirmations']:
      logger.info('Invested ${} in loan {}'
                .format(int(order['investedAmount']), order['loanId']))


  def auto_invest(self):
    """
    Attempt to reinvest unsuccessful loans, in case they later become
    available
    """
    picks = self.poll_for_update()

    top = [int(x['loan_id']) for x in picks if x['top'] in self.PICK_LEVEL
                                            and x['grade'] in self.GRADES]

    if not top:
      logger.info("No matching picks")
    else:
      res = self.invest(top)

      # log results
      logger.debug(pprint.pformat(picks))
      self.log_results(res)

      self.reattempt_invest(res)

    # Log our final remaining ballance
    logger.info('Done. ${:.2f} cash remaining'.format(self.available_cash()))


  def reattempt_invest(self, res):
    """
    # See if unavailable loans become available
    # Continue waiting longer and longer as chance
    # for loans to become availible diminished

    res: Response from previous investment attempt
    """
    for i in xrange(1,15):
      # Check if we have enough cash
      if self.available_cash() < self.AMOUNT_PER_LOAN:
        return

      # sleep a bit
      time.sleep(i)
      
      unfulfilled = [order['loanId'] for order in res['orderConfirmations']
                                      if not int(order['investedAmount'])]

      # We invested in all of our picks
      if not unfulfilled:
        return

      res = self.invest(unfulfilled)

      # Log any succesful orders
      for order in res['orderConfirmations']:
        amount_invested = int(order['investedAmount'])
        if amount_invested:
          logger.info('Successfully reattempt of ${} in loan {}'\
                        .format(amount_invested), order['loanId'])

def init_logging():
  logfile = os.path.join(os.path.dirname(__file__), 'log.txt')
  fh = logging.FileHandler(logfile)
  fh.setLevel(logging.INFO)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  # create formatter and add it to the handlers
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)
  fh.setFormatter(formatter)
  # add the handlers to logger
  logger.addHandler(ch)
  logger.addHandler(fh)

def main():
  # Set up logging
  init_logging()

  # Invest
  secrets = os.path.join(os.path.dirname(__file__), 'data/secrets.json')
  p2p = P2PPicks(secrets)
  res = p2p.auto_invest()

if __name__ == '__main__':
  main()
  
