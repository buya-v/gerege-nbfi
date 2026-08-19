# T43 -- independent re-derivation of DEC-1 rev8 section 4.1.1 step B and step C,
# transcribed from the DOCUMENT TEXT ONLY, in exact integer/date arithmetic.
# No float anywhere.  Checked against capture T39-ME-B's OBSERVED periodRatio vector.
from datetime import date
import calendar

def packed(d):                                   # ChronoUnit.MONTHS.between, JDK monthsUntil
    return (d.year * 12 + d.month - 1) * 32 + d.day

def months_between(a, b):                        # truncated toward zero
    n = packed(b) - packed(a)
    q = abs(n) // 32
    return q if n >= 0 else -q

def plus_months(d, m):                           # LocalDate month arithmetic, clamps day
    y, mo = divmod((d.year * 12 + d.month - 1) + m, 12)
    return date(y, mo + 1, min(d.day, calendar.monthrange(y, mo + 1)[1]))

def last_day(d):
    return calendar.monthrange(d.year, d.month)[1]

def seed_date(start, frm, due, repay_every):     # :1461-1481
    k = 1
    while True:
        c = plus_months(start, k); k += 1
        if not c < due:
            break
    return start if (c == due and plus_months(c, -repay_every) == frm) else frm

def step_b(seed, frm, special_case=True):        # :1423-1439
    if special_case and last_day(frm) == frm.day and seed.day > frm.day:
        return months_between(seed, frm + __import__('datetime').timedelta(days=1))
    return months_between(seed, frm)

def period_ratio(start, frm, due, repay_every=1, special_case=True):
    seed = seed_date(start, frm, due, repay_every)
    k = step_b(seed, frm, special_case)
    m, cursor = k + 1, frm                       # :1441-1458
    while cursor < due:
        cursor = plus_months(seed, m)
        if not cursor > due:
            m += 1
        else:
            full = cursor
            m = m - k - 1
            base = plus_months(seed, m)
            # exact rational; the only mc-rounded op -- integers here, so exact
            return ((due - base).days, (full - base).days, m)
    return (0, 1, m - k - 1)

def as_str(t):
    num, den, whole = t
    return str(whole) if num == 0 else f"{whole}+{num}/{den}"

# T39-ME-B: start = disbursement 2024-01-31, 6 monthly periods.
# Boundaries from section 4.2's re-anchor (seed day 31 > 28):
bounds = [date(2024,1,31), date(2024,2,29), date(2024,3,31), date(2024,4,30),
          date(2024,5,31), date(2024,6,30), date(2024,7,31)]
start = date(2024,1,31)
with_case    = [as_str(period_ratio(start, bounds[i], bounds[i+1], 1, True))  for i in range(6)]
without_case = [as_str(period_ratio(start, bounds[i], bounds[i+1], 1, False)) for i in range(6)]
print("T39-ME-B periodRatio, special case PRESENT :", with_case)
print("T39-ME-B periodRatio, special case OMITTED :", without_case)
print("T39 committed observation (analysis/discriminate-output.txt):")
print("  R2 (present)  ['1','1','1','1','1','1']   R3 (omitted) ['1','2','1','2','1','2']")
ok = with_case == ['1']*6 and without_case == ['1','2','1','2','1','2']
print("MATCH:", ok)

# F-1: the clamped-step reading of 'whole months' WITHOUT the special case
def step_b_clamped(seed, frm):
    k = 0
    while plus_months(seed, k + 1) <= frm:
        k += 1
    return k
print()
print("F-1 check -- packed WITH the case vs clamped-step WITHOUT it, per period:")
for i in range(6):
    frm, due = bounds[i], bounds[i+1]
    sd = seed_date(start, frm, due, 1)
    print(f"  p{i+1} from={frm} seed={sd} packed+case={step_b(sd,frm,True)} clamped-no-case={step_b_clamped(sd,frm)}")

# --- drift shape T39-P0-A: start 2024-01-28, disbursement 2024-01-31 ---
# Boundaries from section 4.2 (step + re-anchor seeded on the DISBURSEMENT date 2024-01-31)
def gen_bounds(start, seed, n):
    b = [start]; cur = start
    for _ in range(n):
        nxt = plus_months(cur, 1)
        if seed.day > 28 and nxt.day >= 28:
            nxt = nxt.replace(day=min(last_day(nxt), seed.day))
        b.append(nxt); cur = nxt
    return b
s2, seed2 = date(2024,1,28), date(2024,1,31)
b2 = gen_bounds(s2, seed2, 6)
print()
print("T39-P0-A boundaries:", [str(d) for d in b2])
print("T39-P0-A periodRatio:", [as_str(period_ratio(s2, b2[i], b2[i+1], 1, True)) for i in range(6)])
print("T39 observed         : 1+1/29, 1+2/31, 1, 1+1/31, 1, 1+1/31")
