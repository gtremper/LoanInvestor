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
      self.lc_portfolio_id = next((int(p['portfolioId'])
        for p in self.lc.portfolios_owned() 
        if p['portfolioName'] == secrets['lc_portfolio']), None)

      if self.lc_portfolio_id is None:
        self.logger.warning("Portfolio '{}' not found. Not using a portfolio"\
                            .format(secrets['lc_portfolio']))
    #
    # Investment configurations
    #
    self.MIN_RATE = 16.0 # Minimum interest rate
    self.MAX_RATE = 25.0 # Maximum interest rate
    self.PICK_LEVEL = frozenset(['5%'])

    if self.lc.available_cash() < 500.0:
      self.AMOUNT_PER_LOAN = 25.0
    else:
      self.AMOUNT_PER_LOAN = 50.0

  def poll(self, fx):
    """
    Generator that polls a function

    fx: a function to poll
    """
    start = dt.datetime.now()
    counter = 0
    while dt.datetime.now() - start < dt.timedelta(minutes=1):
      counter += 1
      try:
        if not counter % 10:
          self.logger.debug('Poll counter: {}'.format(counter))
        yield fx()
      except urllib2.HTTPError as err:
        self.logger.error("HTTPError: {}".format(err.code))
        time.sleep(1)
      except urllib2.URLError as err:
        self.logger.error("URLError: {}".format(err.reason))
        time.sleep(1)
      except (KeyboardInterrupt,SystemExit) as err:
        # We're trying to quit
        raise err
      except Exception as err:
        self.logger.critical("Other exception: {} {}".format(type(err), err))

    raise StopIteration("Polling timeout")

  def wait_for_new_picks(self, start=None):
    """
    Start polling for an update in listed loans
    Must be called before picks update

    start: Time before picks update
    """
    if start is None:
      _, start = self.p2p.picks()

    self.logger.debug("Starting polling picks")

    for picks, timestamp in self.poll(self.p2p.picks):
      if timestamp > start:
        self.logger.info("New picks")
        return picks

    self.logger.error("P2P-Picks polling timeout")
    raise Exception("P2P-Picks polling timeout")

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

    self.logger.error("Listed loans polling timeout")
    raise Exception("Listed loans polling timeout")

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
    WAIT_TIME = dt.timedelta(minutes=30)

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
    id_to_grade = {int(pick['loan_id']): pick['grade'] for pick in picks}

    if 'orderConfirmations' not in res:
      self.logger.error('Attempted to invest in an empty list of loans')

    for order in res['orderConfirmations']:
      loanID = int(order['loanId'])
      grade = id_to_grade[loanID]
      self.logger.info('Invested ${} in grade {} loan {}'
                .format(int(order['investedAmount']), grade, loanID))


  def auto_invest(self, poll=False, wait=False):
    """
    Main investment script for AutoInvestor. This should be run shortly
    before the hour. It will sleep until 5 seconds before the next hour,
    then poll both LendingClub and P2P-Picks for loan selection. Will
    attempt to reinvest in unsuccessful loans 

    poll: True if we want to poll for updated picks,
          False if we want to use the current picks
    """
    # Exit if we don't have enough cash for 1 loan
    available_cash = self.lc.available_cash()
    if available_cash < self.AMOUNT_PER_LOAN:
      msg = 'Insufficient Cash: ${}'.format(available_cash)
      self.logger.info(msg)
      return

    # Store old picks time stamp to check for update
    _, old_picks_timestamp = self.p2p.picks()

    # Sleep until 5 seconds before the hour
    if wait:
      now = dt.datetime.now()
      sleep_time = now.replace(minute=59, second=55, microsecond=0) - now
      self.logger.debug('Sleep {} seconds'.format(sleep_time.total_seconds()))
      time.sleep(sleep_time.total_seconds())

    # Get listed loans
    loans = self.wait_for_new_loans() if poll else self.lc.listed_loans()
    valid_loans = [l for l in loans
                    if self.MIN_RATE < l['intRate'] < self.MAX_RATE]

    # Prioritize high interest rate loans
    valid_loans.sort(key=lambda x: x['intRate'], reverse=True)

    if poll:
      picks = self.wait_for_new_picks(old_picks_timestamp)
    else:
      picks, _ = self.p2p.picks()

    # Filter picks that match our criteria
    valid_picks = frozenset(int(x['loan_id']) for x in picks 
                                      if x['top'] in self.PICK_LEVEL)

    top_picks = [l['id'] for l in valid_loans if l['id'] in valid_picks]

    if not top_picks:
      self.logger.info("No matching picks")
      self.logger.debug(pprint.pformat(picks))
    else:
      res = self.invest(top_picks)

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

  # '--wait' indicates we should wait till next hour
  parser.add_option('-w', '--wait', action='store_true', 
    dest='wait', default=False, help="Wait until next hour")

  # '--log' specifies a log file to which we should append logs
  parser.add_option('-l', '--log', action='store',
    dest='logfile', type='string', help="Log activity to file")

  # Collect options
  options, args = parser.parse_args()

  # Set API's with account information
  investor = AutoInvestor(logfile=options.logfile)

  # Poll for new picks is '--poll' option provided
  # Otherwise, use current picks
  investor.auto_invest(poll=options.poll, wait=options.wait)

if __name__ == '__main__':
  main()
