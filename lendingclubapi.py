#!/usr/bin/env python
import urllib2
import json

class API:
  """Provides and interface to the LendingClub REST API"""

  _API_VERSION = "v1"
  _LOAN_URL = "https://api.lendingclub.com/api/investor/{}/loans/listing"\
              .format(_API_VERSION)

  def __init__(self, investor_id, api_key):
    self.investor_id = investor_id
    self.api_key = api_key
    self._base_url ='https://api.lendingclub.com/api/investor/{}/accounts/{}/{}'\
                    .format(API._API_VERSION, investor_id, '{}')

  def available_cash(self):
    """Get the availble cash in your account"""
    req = urllib2.Request(self._base_url.format("availablecash"))
    req.add_header('Authorization', self.api_key)
    try:
      data = json.load(urllib2.urlopen(req))
    except urllib2.HTTPError as e:
      print e
      return None

    return data['availableCash']







def load_api(investor_id_path, api_key_path):
  """ create an api instance from secrets stored in files

  investor_id_path -- path to file containing investor id
  api_key_path -- path to file containing api secret key
  """

  with open(investor_id_path) as f:
    investor_id = f.read()

  with open(api_key_path) as f:
    api_key = f.read()

  return API(investor_id, api_key)

if __name__ == '__main__':
  api = load_api("investor_id.txt", "api_key.txt")
  print 'cash:', api.available_cash() 


  