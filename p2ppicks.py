#!/usr/bin/env python

"""
Wrapper for the P2P-Picks api.
"""

import dateutil.parser as dateparser
import hashlib
import json
import pprint
import urllib
import urllib2

__all__ = ['API']

class API:
  """
  Wrapper for the P2P-Picks REST API
  https://www.p2p-picks.com/
  """

  _BASE_URL = "https://www.p2p-picks.com/api/v1/{method}/{action}"

  def __init__(self, key, secret, session_id):
    """
    key: P2P-Picks API key
    secret: P2P-Picks API secret
    session_id: P2P-Picks session id for this user
    """

    # Store secrets
    self.p2p_key = key
    self.p2p_secret = secret
    self.p2p_sid = session_id

    # Make sure this user has picks active
    if not self.isActive():
      raise Exception("P2P-Picks account not active")

  def _request(self, method, action, data):
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
      API._BASE_URL.format(method=method, action=action)
    )
    req.add_data(urllib.urlencode(data))

    return json.load(urllib2.urlopen(req))['response']

  def picks(self):
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
    data = self._request('picks', 'list', {'p2p_product': 'profit-maximizer'})
    return data['picks'], dateparser.parse(data['timestamp'])

  def validate(self, email, password):
    """
    This method validates the P2P-Picks subscriber's email and
    password and return key information about the P2P-Picks subscriber

    Returns a tuple of
      (p2p_subscriber_id, status)
    """
    data = self._request('subscriber', 'validate', {
      "p2p_email": email,
      "p2p_password": password
    })

    return str(data['sid']), str(data['status'])

  def isActive(self):
    """ Return True if user has picks activated """
    data =self._request('subscriber', 'status', {'p2p_sid': self.p2p_sid})
    return data['status'] == 'active'

  def report(self, res):
    """
    Report P2P-Picks usage.

    res: the json response to lendingclub.API.submit_order()
    """
    # Return if passed empty list
    if 'orderConfirmations' not in res:
      return

    # Return if no notes invested
    if res['orderInstructId'] is None:
      return

    orders = res['orderConfirmations']

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
    self._request('subscriber', 'report', data)

def main():
  # standard secrets file location
  with open('secrets.json') as f:
    secrets = json.load(f)
    p2p_key = secrets['p2p_key']
    p2p_secret = secrets['p2p_secret']
    p2p_sid = secrets['p2p_sid']

  # Initialize P2P-Picks API
  api = API(p2p_key, p2p_secret, p2p_sid)

  pprint.pprint(api.picks())

if __name__ == '__main__':
  main()
