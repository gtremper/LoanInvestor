#!/usr/bin/env python

"""
Automated LendingClub investor using P2P-Picks for underwriting
"""

import lendingclub as lc
import p2ppicks as p2p
import json

class AutoInvestor(lc.API, p2p.API):
  """
  Auto investor using P2P-Picks to underwrite loans
  https://www.p2p-picks.com/
  """
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
    """
    with open(secrets) as f:
      secrets = json.load(f)

      # Store secrets
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])
      self.p2p_sid = str(secrets['p2p_sid'])
      self.lc_portfolio_id = int(secrets['lc_portfolio_id'])

      # Pass lending club secrets to lc API
      # will set 'self.investor_id' and 'self.api_key'
      lc_investor_id = str(secrets['lc_investor_id'])
      lc_api_key = str(secrets['lc_api_key'])
      super(P2PPicks, self).__init__(lc_investor_id, lc_api_key)

