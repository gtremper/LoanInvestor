#!/usr/bin/env python
import urllib2
import json
import datetime as dt
import dateutil.parser as dateparser

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

  def _request_resource(self, resource, data=None, query=None):
    """Return json response to resource as dict

    data -- json payload for the request
    query -- dictionary of query parameters
    """
    if query is not None:
      resource = resource + urllib.urlencode(query)

    req = urllib2.Request(self._base_url.format(resource))
    req.add_header('Authorization', self.api_key)

    if data is not None:
      req.add_data(json.dumps(data))

    try:
      return json.load(urllib2.urlopen(req))
    except urllib2.HTTPError as e:
      print e
      return None

  def available_cash(self):
    """Get the availble cash in your account
    Returns: Float value of remaining cache
    """
    data = self._request_resource("availablecash")
    return data.get('availableCash', None)

  def summary(self):
    """
    Returns: Dict of account info
    """
    return self._request_resource("summary")

  def notes_owned(self, detailed=False):
    data = self._request_resource("detailednotes" if detailed else "notes")

    if data is None:
      return None

    notes = data['myNotes']

    for note in notes:
      note['issueDate'] = dateparser.parse(note['issueDate'])
      note['orderDate'] = dateparser.parse(note['orderDate'])
      note['loanStatusDate'] = dateparser.parse(note['loanStatusDate'])

      if detailed:
        note['lastPaymentDate'] = dateparser.parse(note['lastPaymentDate'])
        note['nextPaymentDate'] = dateparser.parse(note['nextPaymentDate'])

    return notes

  def portfolios(self):
    data = self._request_resource("portfolios")
    return data.get('myPortfolios', None)

  def create_portfolio(self, name, desc=""):
    payload = {
      "aid": self.investor_id,
      "portfolioName": name,
      "portfolioDescription": desc
    }
    return self._request_resource("portfolios", data=payload)



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

  print api.portfolios()

  