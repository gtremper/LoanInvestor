#!/usr/bin/env python

import csv
import datetime as dt
import dateutil.parser as dateparser
import matplotlib.mlab as mlab
import numpy as np
from heapq import merge
import re
import urllib

# Clases

class Loan:
  """
  Represents a loan on LendingClub
  """

  def __init__(self, row):
    self.properties = {}

    # Properites of type float
    for key in Loan._float_keys:
      self.properties[key] = self._parse_float(row[key])

    # Properties of type datetime
    for key in Loan._date_keys:
      self.properties[key] = dateparser.parse(row[key])

    # Properties with irregular syntax
    self.properties["emp_length"] = self._parse_emp_length(row["emp_length"])

  def __repr__(self):
    return str(self.properties)


  # Class methods
  @classmethod
  def parse_dict_reader(cls, reader):
    return [cls(row) for row in reader]


  # Private functions
  @staticmethod
  def _parse_float(num):
    """
    try to parse input as float, return None if fails
    """
    try:
      return float(num)
    except ValueError, err:
      return None
    except TypeError as e:
      return None

  @staticmethod
  def _parse_emp_length(length):
    """
    parse the 'emp_length' property
    """
    if length == 'n/a':
      return None

    if length == '< 1 year':
      return 0.0

    try:
      return float(re.match(r'\d+', length).group())
    except TypeError as e:
      return None


  # Properties in csv grouped by type

  _float_keys = [
    "acc_now_delinq",
    "acc_open_past_24mths",
    "annual_inc",
    "avg_cur_bal",
    "bc_open_to_buy",
    "bc_util",
    "chargeoff_within_12_mths",
    "collections_12_mths_ex_med",
    "delinq_2yrs",
    "delinq_amnt",
    "dti",
    "fico_range_high",
    "fico_range_low",
    "inq_last_6mths",
    "installment",
    "int_rate",
    "loan_amnt",
    "mo_sin_old_il_acct",
    "mo_sin_old_rev_tl_op",
    "mo_sin_rcnt_rev_tl_op",
    "mo_sin_rcnt_tl",
    "mort_acc",
    "mths_since_last_delinq",
    "mths_since_last_major_derog",
    "mths_since_last_record",
    "mths_since_recent_bc",
    "mths_since_recent_bc_dlq",
    "mths_since_recent_inq",
    "mths_since_recent_revol_delinq",
    "num_accts_ever_120_pd",
    "num_accts_ever_120_pd",
    "num_actv_bc_tl",
    "num_actv_rev_tl",
    "num_bc_sats",
    "num_bc_tl",
    "num_il_tl",
    "num_op_rev_tl",
    "num_rev_accts",
    "num_rev_tl_bal_gt_0",
    "num_sats",
    "num_tl_120dpd_2m",
    "num_tl_30dpd",
    "num_tl_90g_dpd_24m",
    "num_tl_op_past_12m",
    "open_acc",
    "pct_tl_nvr_dlq",
    "percent_bc_gt_75",
    "pub_rec",
    "pub_rec_bankruptcies",
    "revol_bal",
    "revol_util",
    "tax_liens",
    "tot_coll_amt",
    "tot_cur_bal",
    "tot_hi_cred_lim",
    "total_acc",
    "total_bal_ex_mort",
    "total_bc_limit",
    "total_il_high_credit_limit",
    "total_rev_hi_lim"
  ]

  _date_keys = [
#    "earliest_cr_line",
  ]

  _custom_keys = [
    "emp_length"
  ]

  feature_names = sorted(merge(_float_keys, _date_keys, _custom_keys))


def main():
  resource = urllib.urlopen("https://resources.lendingclub.com/secure/primaryMarketNotes/browseNotes_1-RETAIL.csv")
  r = csv.DictReader(resource)
  loans = Loan.parse_dict_reader(r)

  print "Total loans:", len(loans)

  full_data = [loan for loan in loans if not any(x is None for x in loan.properties.values())]

  full_data_length = len(full_data)

  print "Total with full data:", full_data_length
  return full_data



def get_feature_matrix():
  with open('data/HistoricalLoanData.csv', 'r') as resource:
    loans = Loan.parse_dict_reader(csv.DictReader(resource))

  bad_props = []
  for loan in loans:
    for prop,value in loan.properties.iteritems():
      if value is None:
        bad_props.append(prop)

  bad_props = set(bad_props)

  good_props = sorted(set(Loan.feature_names).difference(bad_props))

  print good_props;

  features = []
  for loan in loans:
    row = []
    for prop in good_props:
      if loan.properties[prop] is None:
        print "NONE: ", prop, loan
      row.append(loan.properties[prop])
    features.append(row)

  mat = np.array(features)
  pca = mlab.PCA(mat)

  return pca


if __name__ == '__main__':
  get_feature_matrix()
  #main()

