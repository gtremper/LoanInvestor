#!/usr/bin/env python

"""
Automated LendingClub investor using P2P-Picks for underwriting
"""

import lendingclub as lc
import p2ppicks as p2p
import datetime as dt
import dateutil.parser as dateparser
import json
import time
import pprint
import logging
from optparse import OptionParser
import urllib2

# Set up logging
logger = logging.getLogger('P2P-Picks')
logger.setLevel(logging.DEBUG)

class AutoInvestor:
  """
  Auto investor for LendingClub using P2P-Picks to underwrite loans
  https://www.p2p-picks.com/
  """

  # Investment configurations
  AMOUNT_PER_LOAN = 25.0
  GRADES = frozenset(['D','E','F'])
  PICK_LEVEL = frozenset(['5%'])

  def __init__(self, secrets='secrets.json'):
    """
    secrets: path to a json file containing sensitive information
    {
      "lc_api_key": "a+akdkj3kdfjkp3239", // Lending Club api key
      "lc_investor_id": 93234531,         // Lending Club investor id
      "lc_portfolio_id": 34462030     // Portfolio id to assign invested loans
      "p2p_key": "87C2FE2B4843AD",    // P2P-Picks API key
      "p2p_secret": "ASDKFAJKSDF",    // P2P-Picks API secret 
      "p2p_sid": "384FBC34D3AB"      // P2P-Picks session ID
    }
    """
    with open(secrets) as f:
      secrets = json.load(f)
      p2p_key = str(secrets['p2p_key'])
      p2p_secret = str(secrets['p2p_secret'])
      p2p_sid = str(secrets['p2p_sid'])
      lc_investor_id = str(secrets['lc_investor_id'])
      lc_api_key = str(secrets['lc_api_key'])
      lc_portfolio_id = int(secrets['lc_portfolio_id'])

      # Pass lending club secrets to lc.API
      self.lc = lc.API(lc_investor_id, lc_api_key)

      # Pass P2P-Picks secrets to p2p.API
      self.p2p = p2p.API(p2p_key, p2p_secret, p2p_sid)

      # Portfolio to place invested loans
      self.lc_portfolio_id = int(secrets['lc_portfolio_id'])

  def poll_picks(self):
    """Generator of currently listed picks"""
    while True:
      try:
        yield self.p2p.picks()
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

  def poll_for_update(self):
    """
    Start polling for and update in listed P2P-Picks
    Must be called before picks update
    """

    start = dt.datetime.now()
    logger.debug("Starting poll")

    for picks, timestamp in self.poll_picks():
      if timestamp > start:
        logger.info("New picks")
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
      res = self.lc.submit_order(load_ids,
                  self.AMOUNT_PER_LOAN, self.lc_portfolio_id)
      self.p2p.report(res)
      return res
    except urllib2.HTTPError as e:
      logger.error(e)

    return res

  def log_results(self, res, picks):
    """
    Log details of investment response
    response: Return value of self.invest()
    picks: Return value of self.poll_for_update()
    """

    # Create map of loan id's to grade
    id_to_grade = {}
    for pick in picks:
      id_to_grade[int(pick['loan_id'])] = pick['grade']

    if 'orderConfirmations' not in res:
      logger.error('Attempted to invest in an empty list of loans')

    for order in res['orderConfirmations']:
      loanID = int(order['loanId'])
      grade = id_to_grade[loanID]
      logger.info('Invested ${} in grade {} loan {}'
                .format(int(order['investedAmount']), grade, loanID))


  def auto_invest(self, picks=None):
    """
    Attempt to reinvest unsuccessful loans, in case they later become
    available
    """
    if picks is None:
      picks = self.poll_for_update()

    top = [int(x['loan_id']) for x in picks if x['top'] in self.PICK_LEVEL
                                            and x['grade'] in self.GRADES]

    if not top:
      logger.info("No matching picks")
    else:
      res = self.invest(top)

      # log results
      logger.debug(pprint.pformat(picks))
      self.log_results(res, picks)

      self.reattempt_invest(res)

    # Log our final remaining ballance
    logger.info('Done. ${:.2f} cash remaining'.format(self.lc.available_cash()))


  def reattempt_invest(self, res):
    """
    # See if unavailable loans become available
    # Continue waiting longer and longer as chance
    # for loans to become availible diminished

    res: Response from previous investment attempt
    """
    start = dt.datetime.now()
    WAIT_TIME = dt.timedelta(minutes=20)

    while dt.datetime.now()-start < WAIT_TIME:
      # Check if we have enough cash
      if self.available_cash() < self.AMOUNT_PER_LOAN:
        break

      # Loans we haven't successfully invested in
      unfulfilled = [order['loanId'] for order in res['orderConfirmations']
                                      if not int(order['investedAmount'])]

      # We invested in all of our picks
      if not unfulfilled:
        break

      # sleep a bit
      time.sleep(5)

      res = self.invest(unfulfilled)

      # Log any succesful orders
      for order in res['orderConfirmations']:
        amount_invested = int(order['investedAmount'])
        if amount_invested:
          logger.info('Successful reattempt of ${} in loan {}'\
                      .format(amount_invested, order['loanId']))

def init_logging(logfile):
  # create formatter and add it to the handlers
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

  # Log "info" to file
  if logfile is not None:
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

  # Log to console
  ch = logging.StreamHandler()
  ch.setFormatter(formatter)
  ch.setLevel(logging.DEBUG)
  logger.addHandler(ch)

def main():
  #parse arguments
  parser = OptionParser()

  # '--poll' indicates we should poll for new picks
  parser.add_option('-p', '--poll', action='store_true', 
    dest='poll', default=False, help="Poll for updated picks")

  # '--log' specifies a log file to which we should append logs
  parser.add_option('-l', '--log', action='store',
    dest='logfile', type='string', help="Log activity to file")
  options, args = parser.parse_args()

  # Set up logging
  init_logging(options.logfile)

  # Set API's with account information
  investor = AutoInvestor()

  # Poll for new picks is '--poll' option provided
  # Otherwise, use current picks
  if options.poll:
    res = investor.auto_invest()
  else:
    picks, timestamp = investor.p2p.picks()
    res = investor.auto_invest(picks)

if __name__ == '__main__':
  main()
