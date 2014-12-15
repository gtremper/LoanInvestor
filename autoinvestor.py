#!/usr/bin/env python

"""
Automated LendingClub investor using P2P-Picks for underwriting
"""

import lendingclub as lc
import p2ppicks as p2p

import datetime as dt
import dateutil.parser as dateparser
import json
import logging
import pprint
import time
import urllib2
import urllib2
from optparse import OptionParser

__all__ = ['AutoInvestor']

class AutoInvestor:
  """
  Auto investor for LendingClub using P2P-Picks to underwrite loans
  https://www.p2p-picks.com/

  self.lc: An instance of the LendingClub API
  self.p2p: An instance of the P2P-Picks API
  """

  # Investment configurations
  AMOUNT_PER_LOAN = 25.0
  GRADES = frozenset(['D','E','F'])
  PICK_LEVEL = frozenset(['5%'])

  def __init__(self, secrets='secrets.json', logfile=None):
    """
    secrets: path to a json file containing sensitive information
    logfile: path a logfile to append logging information
    {
      "lc_api_key": "a+akdkj3kdfjkp3239", // Lending Club api key
      "lc_investor_id": 93234531,         // Lending Club investor id
      "lc_portfolio": "MyPortfolio"     // Portfolio name to assign invested loans
      "p2p_key": "87C2FE2B4843AD",    // P2P-Picks API key
      "p2p_secret": "ASDKFAJKSDF",    // P2P-Picks API secret 
      "p2p_sid": "384FBC34D3AB"      // P2P-Picks session ID
    }
    """
    #
    # Set up logging
    #
     
    self.logger = logging.getLogger('AutoInvestor')
    self.logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Log "info" to file
    if logfile is not None:
      fh = logging.FileHandler(logfile)
      fh.setFormatter(formatter)
      fh.setLevel(logging.INFO)
      self.logger.addHandler(fh)

    # Log to console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.DEBUG)
    self.logger.addHandler(ch)

    #
    # Initalize configurations
    # 

    with open(secrets) as f:
      secrets = json.load(f)
      p2p_key = str(secrets['p2p_key'])
      p2p_secret = str(secrets['p2p_secret'])
      p2p_sid = str(secrets['p2p_sid'])
      lc_investor_id = str(secrets['lc_investor_id'])
      lc_api_key = str(secrets['lc_api_key'])

      # Pass lending club secrets to lc.API
      self.lc = lc.API(lc_investor_id, lc_api_key)

      # Pass P2P-Picks secrets to p2p.API
      self.p2p = p2p.API(p2p_key, p2p_secret, p2p_sid)

      # Get portfolio ID from name if it exists
      self.lc_portfolio_id = None
      for portfolio in self.lc.portfolios_owned():
        if portfolio['portfolioName'] == secrets['lc_portfolio']:
          self.lc_portfolio_id = int(portfolio['portfolioId'])
          break

      if self.lc_portfolio_id is None:
        self.logger.warning("Portfolio '{}' not found. Not using a portfolio"\
                            .format(secrets['lc_portfolio']))

  def poll(self, fx):
    """Generator of currently listed picks"""
    while True:
      try:
        yield fx()
      except urllib2.HTTPError as err:
        self.logger.error("HTTPError: {}".format(err.code))
        time.sleep(2)
      except urllib2.URLError as err:
        self.logger.error("URLError: {}".format(err.reason))
        time.sleep(2)
      except (KeyboardInterrupt,SystemExit) as err:
        # We're trying to quit
        return
      except Exception as err:
        self.logger.critical("Other exception:", type(err), err)
        time.sleep(2)

  def wait_for_new_picks(self, start=None):
    """
    Start polling for an update in listed loans
    Must be called before picks update

    start: Time before picks update
    """
    if start is None:
      start = dt.datetime.now()

    self.logger.debug("Starting polling picks")

    for picks, timestamp in self.poll(self.p2p.picks):
      if timestamp > start:
        self.logger.info("New picks")
        return picks

  def wait_for_new_loans(self, start=None):
    """
    Start polling for an update in listed P2P-Picks
    Must be called before picks update

    start: Time before loan update
    """
    if start is None:
      start = dateparser.parse(self.lc.listed_loans()[0]['listD'])

    self.logger.debug("Starting polling loans")

    for loans in self.poll(self.lc.listed_loans):
      timestamp = dateparser.parse(loans[0]['listD'])

      if timestamp > start:
        self.logger.info("New loans")
        return loans

  def invest(self, load_ids):
    """
    Attept to invest in loans by id. Reports
    successful investments to P2P-Picks.

    load_ids: a list of loan ids

    Returns: JSON reponse from lending club
    """
    try:
      # Submit order and report activity to P2P-Picks
      res = self.lc.submit_order(load_ids,
                  self.AMOUNT_PER_LOAN, self.lc_portfolio_id)
      self.p2p.report(res)
      return res
    except urllib2.HTTPError as e:
      self.logger.error(e)

    return res

  def reattempt_invest(self, res):
    """
    Attept to reinvest in unsuccessful orders.

    res: Response from an investement attempt (self.invest())
    """
    start = dt.datetime.now()
    WAIT_TIME = dt.timedelta(minutes=20)

    while dt.datetime.now() - start < WAIT_TIME:
      # Check if we have enough cash
      if self.lc.available_cash() < self.AMOUNT_PER_LOAN:
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
          self.logger.info('Successful reattempt of ${} in loan {}'\
                      .format(amount_invested, order['loanId']))

  def log_results(self, res, picks):
    """
    Log details of investment response

    res: Return value of self.invest()
    picks: Return value of self.poll_for_update()
    """

    # Create map of loan id's to grade
    id_to_grade = {}
    for pick in picks:
      id_to_grade[int(pick['loan_id'])] = pick['grade']

    if 'orderConfirmations' not in res:
      self.logger.error('Attempted to invest in an empty list of loans')

    for order in res['orderConfirmations']:
      loanID = int(order['loanId'])
      grade = id_to_grade[loanID]
      self.logger.info('Invested ${} in grade {} loan {}'
                .format(int(order['investedAmount']), grade, loanID))


  def auto_invest(self, poll=False):
    """
    Attempt to reinvest unsuccessful loans, in case they later become
    available

    poll: True if we want to poll for updated picks,
          False if we want to use the current picks
    """
    if poll:
      picks = self.wait_for_new_picks()
    else:
      picks, _ = self.p2p.picks()

    top = [int(x['loan_id']) for x in picks if x['top'] in self.PICK_LEVEL
                                            and x['grade'] in self.GRADES]

    if not top:
      self.logger.info("No matching picks")
    else:
      res = self.invest(top)

      # log results
      self.logger.debug(pprint.pformat(picks))
      self.log_results(res, picks)

      self.reattempt_invest(res)

    # Log our final remaining ballance
    self.logger.info('Done. ${:.2f} cash remaining'.format(self.lc.available_cash()))


def main():
  #parse arguments
  parser = OptionParser()

  # '--poll' indicates we should poll for new picks
  parser.add_option('-p', '--poll', action='store_true', 
    dest='poll', default=False, help="Poll for updated picks")

  # '--log' specifies a log file to which we should append logs
  parser.add_option('-l', '--log', action='store',
    dest='logfile', type='string', help="Log activity to file")

  # Collect options
  options, args = parser.parse_args()

  # Set API's with account information
  investor = AutoInvestor(logfile=options.logfile)

  # Poll for new picks is '--poll' option provided
  # Otherwise, use current picks
  investor.auto_invest(options.poll)

if __name__ == '__main__':
  main()
