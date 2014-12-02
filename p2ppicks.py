#!/usr/bin/env python
"""
Invest in loans via using p2ppicks as an underwriter
"""

import lendingclub as lc
import hashlib
import json
import urllib
import urllib2

class P2PPicks(lc.Api):
  _BASE_URL = "https://www.p2p-picks.com/api/v1/{method}/{action}"

  def __init__(self, secrets='data/secrets.json'):
    with open(secrets) as f:
      secrets = json.load(f)
      self.p2p_key = str(secrets['p2p_key'])
      self.p2p_secret = str(secrets['p2p_secret'])

      investor_id = secrets['investor_id']
      api_key = secrets['api_key']
      super(P2PPicks, self).__init__(investor_id, api_key)

  def request(self, method, action, data):
    md5 = hashlib.md5()
    md5.update('{}-{}&'.format(method, action))

    data['api_key'] = self.p2p_key
    for key in sorted(data):
      md5.update('{}{}&'.format(key, data[key]))

    md5.update('secret{}'.format(self.p2p_secret))

    data['sig'] = md5.hexdigest()

    req = urllib2.Request(P2PPicks._BASE_URL.format(method=method, action=action))
    req.add_data(json.dumps(data, separators=(',',':')))

    return json.load(urllib2.urlopen(req))

  def list(self):
    res = self.request('picks', 'list', {'p2p_product': 'profit-maximizer'})
    print res





def main():
  p2p = P2PPicks()
  p2p.list()

if __name__ == '__main__':
  main()
