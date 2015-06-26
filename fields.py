import editdistance
import csv
import autoinvestor
import pprint
import sys

def edit_distance():
  ai = autoinvestor.AutoInvestor()

  loans = ai.lc.listed_loans()

  listed_fields = sorted(loans[0].keys())

  with open('LoanStats3a_securev1.csv', 'r') as f:
    next(f) # skip first line
    reader = csv.DictReader(f)
    row = next(reader)
    csv_fields = sorted(row.keys())

  matches = []

  for field in listed_fields:
    match = ""
    min_dist = sys.maxint
    for csv_field in csv_fields:
      dist = editdistance.eval(field.lower(), csv_field.lower())
      if dist < min_dist:
        min_dist = dist
        match = csv_field


    matches.append((field, match, min_dist))

  matches.sort(key=lambda x: x[2])

  for m in matches:
    #bad match
    if m[2] > len(m[1])/3:
      continue
    
    print m[2], m[0], m[1]

def main():
  ai = autoinvestor.AutoInvestor()

  l = ai.lc.listed_loans()[1]

  fields = ['annualInc','collections12MthsExMed','delinq2Yrs','dti','earliestCrLine','empLength','ficoRangeHigh','ficoRangeLow','homeOwnership','initialListStatus','inqLast6Mths','intRate','loanAmount','mthsSinceLastDelinq','mthsSinceLastMajorDerog','mthsSinceLastRecord','openAcc','pubRec','revolBal','revolUtil','term','totalAcc']

  for f in fields:
    print f, l[f]

if __name__ == '__main__':
  main()