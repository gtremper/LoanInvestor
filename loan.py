#!/usr/bin/env python
import datetime as dt
import dateutil.parser as dateparser
import json

FIELDS = set(['accNowDelinq', 'accOpenPast24Mths', 'acceptD', 'addrCity',
 'addrState', 'annualInc', 'avgCurBal', 'bcOpenToBuy', 'bcUtil',
 'chargeoffWithin12Mths', 'collections12MthsExMed', 'creditPullD',
 'delinq2Yrs', 'delinqAmnt', 'desc', 'dti', 'earliestCrLine', 'empLength',
 'empTitle', 'expD', 'expDefaultRate', 'ficoRangeHigh', 'ficoRangeLow',
 'fundedAmount', 'grade', 'homeOwnership', 'id', 'ilsExpD', 'initialListStatus',
 'inqLast6Mths', 'installment', 'intRate', 'investorCount', 'isIncV', 'listD',
 'loanAmount', 'memberId', 'moSinOldIlAcct', 'moSinOldRevTlOp',
 'moSinRcntRevTlOp', 'moSinRcntTl', 'mortAcc', 'mthsSinceLastDelinq',
 'mthsSinceLastMajorDerog', 'mthsSinceLastRecord', 'mthsSinceRecentBc',
 'mthsSinceRecentBcDlq', 'mthsSinceRecentInq', 'mthsSinceRecentRevolDelinq',
 'numAcctsEver120Ppd', 'numActvBcTl', 'numActvRevTl', 'numBcSats', 'numBcTl',
 'numIlTl', 'numOpRevTl', 'numRevAccts', 'numRevTlBalGt0', 'numSats',
 'numTl120dpd2m', 'numTl30dpd', 'numTl90gDpd24m', 'numTlOpPast12m', 'openAcc',
 'pctTlNvrDlq', 'percentBcGt75', 'pubRec', 'pubRecBankruptcies', 'purpose',
 'reviewStatus', 'reviewStatusD', 'revolBal', 'revolUtil', 'serviceFeeRate',
 'subGrade', 'taxLiens', 'term', 'totCollAmt', 'totCurBal', 'totHiCredLim',
 'totalAcc', 'totalBalExMort', 'totalBcLimit', 'totalIlHighCreditLimit',
 'totalRevHiLim'])

STRING_FIELDS = set(["initialListStatus, grade, addrState",
  "subGrade", "homeOwnership", "reviewStatus", "isIncV",
  "empTitle", "purpose", "addrCity"])

_DATE_REGEX = re.compile(
  r'\d\d\d\d-\d\d-\d\dT[\d:.]+-[\d:]+'
)

# Clases
class Loan:
  """ Represents a listed lending club loan """

  def __init__(self, data):
    """
    data: a dictionary of loan attributes to values
    
    This class excpects the types of values in 'data'to be
    the same as the values generated from 'json.load()'
    """
    if set(data.iterkeys()) != FIELDS:
      raise ValueError

    # Fill us with well formated dates
    for k,v in data.iteritems():
      if isinstance(v, basestring) and _DATE_REGEX.match(v):
        self.__dict__[k] = dateparser.parse(v)
      else:
        self.__dict__[k] = v

    # special cases
    self.isIncV = (self.isInvV == 'VERIFIED')

def main():
  pass

if __name__ == '__main__':
  main()
