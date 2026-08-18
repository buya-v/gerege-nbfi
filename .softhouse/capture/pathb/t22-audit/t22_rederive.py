#!/usr/bin/env python3
"""T22 INDEPENDENT AUDIT — re-derive Path B schedules from the PINNED FINERACT
SOURCE, in a model written from scratch for this audit.

Every step below cites the pinned source it implements. The server path is the
PROGRESSIVE generator; none of these citations are to the cumulative generator.

  ProgressiveLoanScheduleGenerator.java:108-110
      emiCalculator.generatePeriodInterestScheduleModel(periods,
          terms.toLoanConfigurationDetails(), terms.getInstallmentAmountInMultiplesOf(), mc)
  ProgressiveEMICalculator.java:1318-1320  calcNominalInterestRatePercentage  = rate / 100 (mc)
  ProgressiveEMICalculator.java:1510-1516  SAME_AS_REPAYMENT_PERIOD + MONTHLY short circuit:
      rateFactorByRepaymentPeriod(rate, ONE, repaymentEvery, 12, actualDays, calcDays, mc)
      -> daysInYearType / daysInMonthType / daysInYearCustomStrategy are NOT read
  ProgressiveEMICalculator.java:1950-1963  rateFactorByRepaymentPeriod
      f = rate * (multiplier * repaymentEvery / daysInYear) * actualDays / calcDays
      then .setScale(mc.getPrecision(), mc.getRoundingMode())   <- DECIMAL PLACES, not sig digits
  RepaymentPeriod.java:216-217             rateFactorPlus1 = 1 + sum(interestPeriod rateFactors)  (exact add)
  ProgressiveEMICalculator.java:1816-1820  rateFactorPlus1N = product of (1+f_i)          (mc)
  ProgressiveEMICalculator.java:1822-1828  fnResult  = fold over periods.skip(1):
                                             fn = 1 + fn * (1+f_i)                        (mc)
  ProgressiveEMICalculator.java:1838-1841  EMI = rateFactorPlus1N * balance / fnResult     (mc)
  Money.java:40-52                         Money.of -> setScale(decimalPlaces, tenant rounding mode)
  ProgressiveEMICalculator.java:1761-1776  applyInstallmentAmountInMultiplesOf / safeRoundingForEMI
  Money.java:159-171                       roundToMultiplesOf: divide(m, scale 0, TENANT MODE) * m
                                             -> ROUND TO NEAREST multiple, NOT round-up
  InterestPeriod.java:145-157              calculatedDueInterest = balance * rateFactorTillDue
                                             / lengthTillDue * length                      (mc)
  RepaymentPeriod.java:251-257             Money.of(sum of interest periods)               (mc)
  RepaymentPeriod.java:272-285             dueInterest = min(calculatedDueInterest, emi)
  RepaymentPeriod.java:345-349             duePrincipal = max(0, emi - dueInterest)
  ProgressiveEMICalculator.java:1160-1219  calculateLastUnpaidRepaymentPeriodEMI:
      diff = totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal
             + totalDueInterest - totalEMI                    (:1202-1203)
      lastPeriod.emi += diff                                  (:1205)

Scope of the model: single disbursement on the first period's fromDate, no
charges, no payments, no down payment, no capitalized income, no grace,
DECLINING_BALANCE, one interest period per repayment period. That is exactly the
shape of B-01 / B-02.
"""
import datetime
import json
import sys
from decimal import Decimal, localcontext, ROUND_HALF_UP, ROUND_HALF_EVEN

PREC = 19  # MoneyHelper.java:35 — compile-time constant
MODES = {'HALF_UP': ROUND_HALF_UP, 'HALF_EVEN': ROUND_HALF_EVEN}


def q(x, places, rounding):
    """BigDecimal.setScale(places, rounding)."""
    return x.quantize(Decimal(1).scaleb(-places), rounding=rounding)


def derive(principal, n, annual_rate_pct, due_dates, first_from,
           multiples_of=None, decimals=2, mode='HALF_UP'):
    rnd = MODES[mode]
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = rnd

        rate = Decimal(annual_rate_pct) / Decimal(100)          # :1318-1320

        # --- rate factor per repayment period (SAME_AS_REPAYMENT_PERIOD, MONTHLY)
        rfs = []
        froms = [first_from] + due_dates[:-1]
        for i in range(n):
            days = Decimal((due_dates[i] - froms[i]).days)      # actual == calculated
            ifpp = (Decimal(1) * Decimal(1)) / Decimal(12)      # :1956-1958
            f = rate * ifpp                                     # :1959-1961
            f = f * days
            f = f / days
            f = q(f, PREC, rnd)                                 # :1962 setScale(19, mode)
            rfs.append(f)

        rfp1 = [Decimal(1) + f for f in rfs]                    # RepaymentPeriod.java:216-217 (exact)

        rate_factor_n = Decimal(1)
        for v in rfp1:
            rate_factor_n = rate_factor_n * v                   # :1816-1820

        fn = Decimal(1)
        for v in rfp1[1:]:
            fn = Decimal(1) + fn * v                            # :1822-1828 / :1991

        emi_raw = rate_factor_n * Decimal(principal) / fn       # :1838-1841
        emi = q(emi_raw, decimals, rnd)                         # Money.java:52

        if multiples_of:                                        # :1761-1776
            m = Decimal(multiples_of)
            rounded = q(emi / m, 0, rnd) * m                    # Money.java:167 — NEAREST, not ceil
            emi = q(rounded, decimals, rnd) if rounded != 0 else emi

        # --- walk the schedule
        bal = Decimal(principal)
        rows = []
        for i in range(n):
            calc_int = q(bal * rfs[i], decimals, rnd)           # InterestPeriod.java:154-157 + RP:251-257
            due_int = min(calc_int, emi)                        # RepaymentPeriod.java:280
            due_pri = max(Decimal(0), emi - due_int)            # RepaymentPeriod.java:348
            bal = bal - due_pri
            rows.append({'emi': emi, 'interest': due_int, 'principal': due_pri,
                         'balance': bal})

        # --- final installment absorbs the residual (:1160-1219)
        total_due_interest = sum((r['interest'] for r in rows), Decimal(0))
        total_emi = sum((r['emi'] for r in rows), Decimal(0))
        diff = Decimal(principal) + total_due_interest - total_emi     # :1202-1203
        last = rows[-1]
        last['emi'] = last['emi'] + diff                               # :1205
        last['interest'] = min(q(rows[-2]['balance'] * rfs[-1], decimals, rnd), last['emi'])
        last['principal'] = max(Decimal(0), last['emi'] - last['interest'])
        last['balance'] = rows[-2]['balance'] - last['principal']

        return {'emi': rows[0]['emi'], 'rows': rows,
                'total_interest': sum((r['interest'] for r in rows), Decimal(0)),
                'total_repayment': sum((r['emi'] for r in rows), Decimal(0))}


def load(path):
    return json.loads(open(path, 'rb').read().decode(), parse_float=Decimal,
                      parse_int=Decimal)


def compare(path, label, multiples_of=None, mode='HALF_UP'):
    j = load(path)
    rows = [p for p in j['periods'] if 'period' in p]
    dates = [datetime.date(*[int(x) for x in p['dueDate']]) for p in rows]
    first_from = datetime.date(*[int(x) for x in rows[0]['fromDate']])
    d = derive(Decimal('1200000'), len(rows), Decimal('21.6'), dates, first_from,
               multiples_of=multiples_of, mode=mode)
    print('=' * 84)
    print('%s   multiplesOf=%s  mode=%s' % (label, multiples_of, mode))
    print(' per  derived P    observed P    derived I   observed I   derived T   observed T')
    ok = True
    for i, (r, o) in enumerate(zip(d['rows'], rows), 1):
        op = Decimal(o['principalDue']); oi = Decimal(o['interestDue'])
        ot = Decimal(o['totalDueForPeriod'])
        m = (r['principal'] == op and r['interest'] == oi and r['emi'] == ot)
        ok &= m
        print(' %3d  %11s %11s  %11s %11s  %11s %11s  %s'
              % (i, r['principal'], op, r['interest'], oi, r['emi'], ot,
                 'ok' if m else '**MISMATCH**'))
    ti = Decimal(j['totalInterestCharged']); tr = Decimal(j['totalRepaymentExpected'])
    m1 = d['total_interest'] == ti
    m2 = d['total_repayment'] == tr
    ok &= m1 and m2
    print(' totalInterest  derived=%s observed=%s %s' % (d['total_interest'], ti, 'ok' if m1 else '**MISMATCH**'))
    print(' totalRepayment derived=%s observed=%s %s' % (d['total_repayment'], tr, 'ok' if m2 else '**MISMATCH**'))
    print(' RESULT: %s' % ('RE-DERIVED DIGIT-FOR-DIGIT' if ok else 'MISMATCH'))
    return ok


if __name__ == '__main__':
    W = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb'
    a = compare(W + '/out/B-01-baseline-raw.json', 'B-01 baseline', None, 'HALF_EVEN')
    b = compare(W + '/out/B-02-multiplesof100-raw.json', 'B-02 multiplesOf=100', 100, 'HALF_EVEN')
    print('=' * 84)
    print('OVERALL: %s' % ('PASS' if a and b else 'FAIL'))
    sys.exit(0 if a and b else 1)
