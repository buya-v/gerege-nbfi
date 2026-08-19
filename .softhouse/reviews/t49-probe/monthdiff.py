#!/usr/bin/env python3
"""T49 probe — independent re-derivation of DEC-1 rev-10 §4.1.1 step B.

Re-derives, from the DOCUMENT'S OWN TEXT and from first principles (not from T46's
or T47's scripts):

  packed(a,b)  = trunc((packed32(b) - packed32(a)) / 32)      # ChronoUnit.MONTHS.between
  clamped(a,b) = max{ j : a.plusMonths(j) <= b }              # "clamped-step" / "naive"
  oracle(a,b)  = packed(a, b+1day) if (b.day == len(b) and a.day > b.day) else packed(a,b)

and checks the four counts DEC-1 revision 10 asserts over every ordered pair
a <= b in 2000-01-01 .. 2040-12-31.

No floating point anywhere. Read-only; contacts no oracle.
"""
import calendar
from datetime import date, timedelta

D0 = date(2000, 1, 1)
D1 = date(2040, 12, 31)


def packed32(d):
    return ((d.year * 12 + d.month - 1) * 32) + d.day


def trunc_div(n, d):
    # Java integer division: truncate toward zero
    q = abs(n) // d
    return q if n >= 0 else -q


def packed(a, b):
    return trunc_div(packed32(b) - packed32(a), 32)


def plus_months(a, k):
    m = a.year * 12 + (a.month - 1) + k
    y, mo = divmod(m, 12)
    mo += 1
    return date(y, mo, min(a.day, calendar.monthrange(y, mo)[1]))


def clamped(a, b):
    # largest j >= 0 with a.plusMonths(j) <= b   (a <= b assumed)
    k = (b.year * 12 + b.month) - (a.year * 12 + a.month)
    return k if plus_months(a, k) <= b else k - 1


def lastday(d):
    return calendar.monthrange(d.year, d.month)[1]


def fires(a, b):
    return b.day == lastday(b) and a.day > b.day


def oracle(a, b):
    return packed(a, b + timedelta(days=1)) if fires(a, b) else packed(a, b)


# ---- days in window --------------------------------------------------------
days = []
d = D0
while d <= D1:
    days.append(d)
    d += timedelta(days=1)
n = len(days)
pairs = n * (n + 1) // 2
print('days in window                 :', n)
print('ordered pairs a <= b           :', pairs, '(DEC-1 says 112,147,776)')

# ---- exhaustive counts via prefix sums (exact integers) --------------------
# predicate fires  <=>  b.day == len(b)  AND  a.day > b.day, a <= b
# count over a <= b of [a.day > t] for t in {28,29,30,31}
pref = {t: [0] * (n + 1) for t in (28, 29, 30, 31)}
for i, a in enumerate(days):
    for t in (28, 29, 30, 31):
        pref[t][i + 1] = pref[t][i] + (1 if a.day > t else 0)

n_fires = 0
for i, b in enumerate(days):
    ld = lastday(b)
    if b.day == ld:
        n_fires += pref[ld][i + 1]
print('[:1432] predicate FIRES        :', n_fires, '(DEC-1 says 45,253)')

# ---- verify the closed form and the three identities on a full sub-window --
# Exhaustive over 2000..2005 (a smaller window, every ordered pair), checking
# packed/clamped/oracle from first principles.
SUB0, SUB1 = date(2000, 1, 1), date(2005, 12, 31)
sub = []
d = SUB0
while d <= SUB1:
    sub.append(d)
    d += timedelta(days=1)
c_pairs = c_fires = c_pne_c = c_fire_and_eq = c_nofire_and_ne = 0
c_or_ne_cl = c_or_ne_pk = 0
first_firing = None
for i, a in enumerate(sub):
    for b in sub[i:]:
        c_pairs += 1
        p, cl, orc = packed(a, b), clamped(a, b), oracle(a, b)
        f = fires(a, b)
        if f:
            c_fires += 1
            if first_firing is None:
                first_firing = (a, b, p, cl, orc)
        if p != cl:
            c_pne_c += 1
        if f and p == cl:
            c_fire_and_eq += 1
        if (not f) and p != cl:
            c_nofire_and_ne += 1
        if orc != cl:
            c_or_ne_cl += 1
        if orc != p:
            c_or_ne_pk += 1
print()
print('--- exhaustive sub-sweep 2000-01-01..2005-12-31 (first principles) ---')
print('pairs                          :', c_pairs)
print('predicate fires                :', c_fires)
print('packed != clamped              :', c_pne_c)
print('fires AND packed == clamped    :', c_fire_and_eq, '(DEC-1 says 0 over the full window)')
print('not-fires AND packed != clamped:', c_nofire_and_ne, '(DEC-1 says 0)')
print('k_oracle != k_clamped          :', c_or_ne_cl, '(DEC-1 says 0)')
print('k_oracle != k_packed           :', c_or_ne_pk, '(== the firing count)')
a, b, p, cl, orc = first_firing
print('first firing pair              :', a, b, 'packed', p, 'clamped', cl, 'oracle', orc)
