import datetime as dt
import datetime.parser as dateparser
import heapq.merge as merge
import re

# Clases

class Loan:
  """
  Represents a loan on LendingClub
  """

  def __init__(self, row):

    # Properites of type float
    for key in _float_keys:
      self.properties[key] = _parse_float(key)

    for key in _float_missing_keys:
      self.properties[key] = _parse_float_missing(key)

    # Properties of type datetime
    for key = _date_keys:
      self.properties[key] = dateparser.parse(key)

    # Properties with irregular syntax
    self.properties["emp_length"] = _parse_emp_length()



  # Private functions
  def _parse_float_missing(num):
    """
    try to parse input as float, return None if fails
    """
    try:
      return float(num):
    except ValueError, err:
      return None

  def _parse_float(num):
    """
    parse where null value is 0
    """
    try:
      return float(num):
    except ValueError, err:
      return 0.0


  def _parse_emp_length(length):
    """
    parse the 'emp_length' property
    """
    if length == 'n/a':
      return None

    if length == '< 1 year':
      return 0.0

    return float(re.match(r'/d+', length).group())




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
    "mort_acc"
  ]

  _float_missing_keys = [
    "bc_open_to_buy",
    "bc_util"
  ]

  _date_keys = [
    "earliest_cr_line",
  ]

  _custom_keys = [
    "emp_length"
  ]

  feature_names = sorted(merge(_float_keys, _float_missing_keys,
    _date_keys, _custom_keys))


# Functions




