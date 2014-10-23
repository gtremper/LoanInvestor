#!/usr/bin/env python
import csv
import datetime as dt
import dateutil.parser as dateparser
import json
import re

FIELDS = set(['accNowDelinq', 'acceptD', 'addrCity', 'addrState', 'annualInc',
  'avgCurBal', 'bcOpenToBuy', 'bcUtil', 'chargeoffWithin12Mths',
  'collections12MthsExMed', 'delinqAmnt', 'desc', 'dti', 'earliestCrLine',
  'empLength', 'empTitle', 'expD', 'ficoRangeHigh', 'ficoRangeLow', 'grade',
  'homeOwnership', 'id', 'initialListStatus', 'installment', 'intRate',
  'isIncV', 'listD', 'memberId', 'moSinOldIlAcct', 'moSinOldRevTlOp',
  'moSinRcntRevTlOp', 'moSinRcntTl', 'mortAcc', 'mthsSinceLastDelinq',
  'mthsSinceLastMajorDerog', 'mthsSinceLastRecord', 'mthsSinceRecentBc',
  'mthsSinceRecentBcDlq', 'mthsSinceRecentInq', 'mthsSinceRecentRevolDelinq',
  'numActvBcTl', 'numActvRevTl', 'numBcSats', 'numBcTl', 'numIlTl',
  'numOpRevTl', 'numRevAccts', 'numRevTlBalGt0', 'numSats', 'numTl120dpd2m',
  'numTl30dpd', 'numTl90gDpd24m', 'numTlOpPast12m', 'openAcc', 'pctTlNvrDlq',
  'percentBcGt75', 'pubRec', 'pubRecBankruptcies', 'purpose', 'revolBal',
  'revolUtil', 'subGrade', 'taxLiens', 'term', 'totCollAmt', 'totCurBal',
  'totHiCredLim', 'totalAcc', 'totalBalExMort', 'totalBcLimit',
  'totalIlHighCreditLimit', 'totalRevHiLim'])

_DATE_RE = re.compile(
  r'\d\d\d\d-\d\d-\d\dT[\d:.]+-[\d:]+'
)

re.sub(r'_(\w)', lambda x: x.group(1).capitalize(), 'total_il_high_credit_limit')

# Clases
class Loan:
  """ Represents a listed lending club loan """

  def __init__(self, data):
    """
    data: a dictionary of loan attributes to values
    
    This class excpects the types of values in 'data'to be
    the same as the values generated from 'json.load()'
    """
    def makeCamel(attr):
      """Make strings for iterator camelCase"""
      return re.sub(r'_(\w)', lambda x: x.group(1).capitalize(), str(attr))


    if set(makeCamel(k) for k in data.iterkeys()) >= FIELDS:
      raise ValueError

    # Fill us with well formated dates
    for k,v in data.iteritems():
      if isinstance(v, basestring):
        if _DATE_RE.match(v):
          self.data[makeCamel(k)] = dateparser.parse(v)
        else:
          self.data[makeCamel(k)] = str(v)
      else:
        self.data[makeCamel(k)] = v

    # special cases
    #self.isIncV = (self.isIncV == 'VERIFIED')

def parse_csv(filename):
  with open(filename) as f:
    return [Loan(data) for data in csv.DictReader(f)]

def main():
  return parse_csv('data/HistoricalLoanData.csv')

if __name__ == '__main__':
  main()
