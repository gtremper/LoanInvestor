#!/usr/bin/env python
"""
Invest in loans via using p2ppicks as an underwriter
"""

import lendingclub as lc
import hashlib
import json

class P2PPicks(lc.API):
  def __init__(self, secrets='data/secrets.json'):
    with open(secrets) as f:
      secrets = json.load(f)
      investor_id = secrets['investor_id']
      api_key = secrets['api_key']
      super(AutoInvestor, self).__init__(investor_id, api_key)
  

  