#!/usr/bin/env python3
"""T332 — FOURTH independent derivation of law (ii) and its ALGEBRAIC TWIN.

Written for T332 from the definitions in `.softhouse/gates.md` alone. It imports
NOTHING from T264, T241, T277, T278, `site3.py` or `validate_corpus.py`; the
`--selftest` asserts that at AST level and fails if any such import ever appears.

WHAT IT GRADES
  law (ii)   TOTAL PRINCIPAL = max(0, B_minor - n*delta)
  the twin   residual        = min(B_minor, n*delta)
and the algebraic identity between them, cell by cell, so that a reader can see
that a failure of one IS a failure of the other rather than being told so.

MONEY DISCIPLINE
  Integer minor units end to end. No float literal, no `float()`, no `round()`,
  no true-division operator, no `decimal` / `fractions` / `math` / `numpy`
  import anywhere in this file. Rates are carried as an exact integer
  (numerator, denominator) pair parsed from the captured decimal STRING; the
  captured money fields are refused unless they arrive as 2-decimal strings, so
  a JSON float cannot enter through the data either.

  HALF_UP on a non-negative rational a/b is  (2a + b) // (2b).

USAGE
  t332_twin_audit.py --selftest
  t332_twin_audit.py --scope t229corpus | --scope all
  t332_twin_audit.py --seven
  t332_twin_audit.py --sites            (grades the specific gates.md site claims)
  t332_twin_audit.py --json
Exit 0 when every pinned expectation holds; exit 1 on any disagreement.
"""

import argparse
import ast
import glob
import gzip
import json
import os
import sys

# ---------------------------------------------------------------- provenance --

CAPTURE_GLOBS = ('.softhouse/capture/**/*.json.gz', '.softhouse/reviews/**/*.json.gz')

# The `t229corpus` scope is the four raw captures that existed under
# `.softhouse/capture/` when T229 ran. gates.md pins the membership; the
# basenames are re-listed here so this file is readable without it.
T229CORPUS = (
    'capture-t117-raw.json.gz',
    'capture-t117p2-raw.json.gz',
    'capture-t159-raw.json.gz',
    'capture-t223-raw.json.gz',
)

FORBIDDEN_IMPORT_MARKS = ('t264', 't277', 't278', 't241', 'site3', 'validate_corpus',
                          'rederive', 'shapelaw', 'crosscheck')
FORBIDDEN_MODULES = ('decimal', 'fractions', 'math', 'numpy', 'statistics')


class Refuse(Exception):
    pass


# ------------------------------------------------------------ integer money --

def minor(s, dp=2):
    """Parse a captured money STRING into integer minor units. Refuses anything
    that is not a string with exactly `dp` decimal places."""
    if not isinstance(s, str):
        raise Refuse('money field is not a string: %r' % (s,))
    neg = s.startswith('-')
    body = s[1:] if neg else s
    if '.' not in body:
        raise Refuse('money field has no decimal point: %r' % (s,))
    whole, frac = body.split('.', 1)
    if len(frac) != dp or not whole.isdigit() or not frac.isdigit():
        raise Refuse('money field is not %d-dp: %r' % (dp, s))
    v = int(whole) * (10 ** dp) + int(frac)
    return -v if neg else v


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def dec_str_to_frac(s):
    """'600.0' -> (6000, 10). Exact, integer-only."""
    if not isinstance(s, str):
        raise Refuse('rate is not a string: %r' % (s,))
    neg = s.startswith('-')
    body = s[1:] if neg else s
    if '.' in body:
        whole, frac = body.split('.', 1)
    else:
        whole, frac = body, ''
    if not whole.isdigit() or (frac and not frac.isdigit()):
        raise Refuse('rate is not decimal: %r' % (s,))
    num = int(whole + frac) if frac else int(whole)
    den = 10 ** len(frac)
    return (-num if neg else num), den


def reduce_frac(num, den):
    g = gcd(abs(num), abs(den)) or 1
    return num // g, den // g


def monthly_rate(rate_str):
    """Exact monthly factor as a reduced (num, den) integer pair: rate/100/12."""
    n, d = dec_str_to_frac(rate_str)
    return reduce_frac(n, d * 1200)


def terminates_within(den, digits):
    """True iff 1/den has a terminating decimal expansion of <= `digits` places."""
    d = den
    a = b = 0
    while d % 2 == 0:
        d //= 2
        a += 1
    while d % 5 == 0:
        d //= 5
        b += 1
    if d != 1:
        return False
    return (a if a > b else b) <= digits


def half_up(num, den):
    """HALF_UP quantization of num/den to an integer, num >= 0, den > 0."""
    if num < 0 or den <= 0:
        raise Refuse('half_up domain')
    return (2 * num + den) // (2 * den)


# ------------------------------------------------------------------- loading --

def capture_files():
    out = []
    for g in CAPTURE_GLOBS:
        out.extend(sorted(glob.glob(g, recursive=True)))
    return out


class Cell(object):
    __slots__ = ('cid', 'src', 'n', 'B', 'E', 'I1q', 'delta', 'principal_rows',
                 'observed_principal', 'header_principal', 'last_total',
                 'last_interest', 'last_balance', 'stuck', 'rate')

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__ if k != 'principal_rows'}


def load_cells(scope):
    """Returns (cells, stats). A cell is ADMITTED when the oracle answered and the
    monthly rate factor terminates inside 19 fractional digits; it is STUCK when
    repayment row 1 repays zero principal."""
    stats = {'total': 0, 'threw': 0, 'rate_inexact': 0, 'rate_inexact_ids': [],
             'admitted': 0, 'stuck': 0, 'amortizing': 0, 'files': 0,
             'header_ne_rowsum': 0, 'setting_violations': []}
    cells = []
    for path in capture_files():
        base = os.path.basename(path)
        if scope == 't229corpus' and base not in T229CORPUS:
            continue
        stats['files'] += 1
        doc = json.loads(gzip.open(path, 'rt').read())
        if doc.get('moneyHelperPrecision') != 19:
            raise Refuse('%s is not a precision-19 capture' % base)
        for c in doc['captures']:
            stats['total'] += 1
            obs = c.get('observed')
            if obs is None:
                stats['threw'] += 1
                continue
            inp = c['inputs']
            # the production setting is asserted, never filtered on silently
            for key, want in (('mathContextPrecision', 19),
                              ('mathContextRoundingMode', 'HALF_UP'),
                              ('currencyCode', 'MNT'),
                              ('currencyDecimalPlaces', 2),
                              ('repaymentFrequency', 1),
                              ('repaymentFrequencyType', 'MONTHS'),
                              ('interestMethod', 'DECLINING_BALANCE'),
                              ('daysInMonth', 'DAYS_30'),
                              ('daysInYear', 'DAYS_360'),
                              ('downPaymentEnabled', False),
                              ('currencyInMultiplesOf', None)):
                if inp.get(key) != want:
                    stats['setting_violations'].append((c['id'], key, inp.get(key)))
            rnum, rden = monthly_rate(inp['annualNominalInterestRate'])
            if not terminates_within(rden, 19):
                stats['rate_inexact'] += 1
                stats['rate_inexact_ids'].append(c['id'])
                continue
            stats['admitted'] += 1
            rows = [p for p in obs['periods'] if p['type'] == 'REPAYMENT']
            if not rows:
                raise Refuse('%s has no repayment rows' % c['id'])
            pr = [minor(r['principal']) for r in rows]
            B = minor(inp['disbursementAmount'])
            disb = [p for p in obs['periods'] if p['type'] == 'DISBURSEMENT']
            if len(disb) != 1 or minor(disb[0]['principal']) != B:
                raise Refuse('%s: disbursement row disagrees with the input' % c['id'])
            n = inp['numberOfRepayments']
            if n != len(rows):
                raise Refuse('%s: numberOfRepayments != repayment row count' % c['id'])
            hdr = minor(obs['totalPrincipalAmount'])
            rowsum = sum(pr)
            if hdr != rowsum:
                stats['header_ne_rowsum'] += 1
            cell = Cell()
            cell.cid = c['id']
            cell.src = base
            cell.rate = inp['annualNominalInterestRate']
            cell.n = n
            cell.B = B
            cell.E = minor(rows[0]['total'])
            # I1q is COMPUTED from the rate. Reading it out of row 1's `interest`
            # measures E twice on a stuck cell, because the emitted interest is
            # already clipped to the instalment and the deficit is carried.
            cell.I1q = half_up(B * rnum, rden)
            cell.delta = cell.I1q - cell.E
            cell.principal_rows = pr
            cell.observed_principal = rowsum
            cell.header_principal = hdr
            cell.last_total = minor(rows[-1]['total'])
            cell.last_interest = minor(rows[-1]['interest'])
            cell.last_balance = minor(rows[-1]['balance'])
            cell.stuck = (pr[0] == 0)
            if cell.stuck:
                stats['stuck'] += 1
            else:
                stats['amortizing'] += 1
            cells.append(cell)
    return cells, stats


# --------------------------------------------------------------------- laws --

def law_ii(cell):
    """TOTAL PRINCIPAL = max(0, B_minor - n*delta)."""
    v = cell.B - cell.n * cell.delta
    return v if v > 0 else 0


def twin(cell):
    """residual = min(B_minor, n*delta)."""
    a, b = cell.B, cell.n * cell.delta
    return a if a < b else b


def observed_residual(cell):
    return cell.B - cell.observed_principal


def fact_a(cell):
    """law (i): last row EMI = E + B."""
    return cell.last_total == cell.E + cell.B


def full_family_b(cell):
    return cell.delta >= 1 and cell.B <= cell.n * cell.delta


def partial_family_b(cell):
    # delta >= 1 and n*delta < B < (delta + 1/2)*n, in integers
    return (cell.delta >= 1
            and cell.n * cell.delta < cell.B
            and 2 * cell.B < (2 * cell.delta + 1) * cell.n)


def in_conservative_region(cell):
    """B_minor < 1.5*n, written in integers as 2B < 3n."""
    return 2 * cell.B < 3 * cell.n


# ------------------------------------------------------------------- census --

def census(scope):
    cells, stats = load_cells(scope)
    stuck = [c for c in cells if c.stuck]
    law_fail = [c for c in stuck if law_ii(c) != c.observed_principal]
    twin_fail = [c for c in stuck if twin(c) != observed_residual(c)]
    # the identity, proved cell by cell rather than asserted in prose
    identity_holds = all(c.B - law_ii(c) == twin(c) for c in stuck)
    exceeds = [c for c in stuck if observed_residual(c) > twin(c)]
    under = [c for c in stuck if observed_residual(c) < twin(c)]
    dhist = {}
    for c in stuck:
        dhist[c.delta] = dhist.get(c.delta, 0) + 1
    facta = [c for c in stuck if fact_a(c)]
    facta_fail = [c for c in stuck if not fact_a(c)]
    fullb = [c for c in stuck if full_family_b(c)]
    partb = [c for c in stuck if partial_family_b(c)]
    d0 = [c for c in stuck if c.delta == 0]
    fail_outside_region = [c for c in law_fail if not in_conservative_region(c)]
    last_row_only = [c for c in facta
                     if all(x == 0 for x in c.principal_rows[:-1])]
    desc = [c for c in facta
            if c.observed_principal == max(0, c.E + c.B - c.last_interest)]
    resid_eq_balance = [c for c in stuck if observed_residual(c) == c.last_balance]
    return {
        'scope': scope,
        'files': stats['files'],
        'total_captures': stats['total'],
        'threw': stats['threw'],
        'rate_inexact': stats['rate_inexact'],
        'rate_inexact_ids': sorted(stats['rate_inexact_ids']),
        'admitted': stats['admitted'],
        'stuck': len(stuck),
        'amortizing': stats['amortizing'],
        'header_ne_rowsum': stats['header_ne_rowsum'],
        'setting_violations': stats['setting_violations'],
        'delta_histogram': {str(k): v for k, v in sorted(dhist.items())},
        'fact_a_holds': len(facta),
        'fact_a_fails': len(facta_fail),
        'law_ii_holds': len(stuck) - len(law_fail),
        'law_ii_fails': len(law_fail),
        'law_ii_on_fact_a': sum(1 for c in facta if law_ii(c) == c.observed_principal),
        'law_ii_on_delta0': sum(1 for c in d0 if law_ii(c) == c.observed_principal),
        'law_ii_on_full_family_b': sum(1 for c in fullb if law_ii(c) == c.observed_principal),
        'full_family_b_n': len(fullb),
        'partial_family_b_n': len(partb),
        'partial_family_b_law_holds': sum(1 for c in partb if law_ii(c) == c.observed_principal),
        'twin_holds': len(stuck) - len(twin_fail),
        'twin_fails': len(twin_fail),
        'twin_identity_holds_every_cell': identity_holds,
        'exception_sets_identical': sorted(c.cid for c in law_fail) == sorted(c.cid for c in twin_fail),
        'observed_residual_EXCEEDS_formula': len(exceeds),
        'observed_residual_below_formula': len(under),
        'fact_a_and_law_ii_exceptions_intersect': len([c for c in law_fail if not fact_a(c)]),
        'delta0_and_law_ii_exceptions_intersect': len([c for c in law_fail if c.delta == 0]),
        'failing_cells_outside_conservative_region': len(fail_outside_region),
        'failing_cells_inside_conservative_region': len(law_fail) - len(fail_outside_region),
        'principal_in_last_row_only_on_fact_a': '%d/%d' % (len(last_row_only), len(facta)),
        'descriptive_last_row_form_on_fact_a': '%d/%d' % (len(desc), len(facta)),
        'residual_equals_last_row_balance': '%d/%d' % (len(resid_eq_balance), len(stuck)),
        'exceptions': [{
            'id': c.cid, 'capture': c.src, 'n': c.n, 'B': c.B, 'E': c.E,
            'I1q': c.I1q, 'delta': c.delta,
            'B_le_n_delta': c.B <= c.n * c.delta,
            'law_ii_predicts': law_ii(c),
            'observed_principal': c.observed_principal,
            'twin_predicts_residual': twin(c),
            'observed_residual': observed_residual(c),
            'fact_a': fact_a(c),
            'full_family_b': full_family_b(c),
            'in_conservative_region': in_conservative_region(c),
            'nonzero_principal_rows': [i + 1 for i, v in enumerate(c.principal_rows) if v],
        } for c in sorted(law_fail, key=lambda x: x.cid)],
        'record_largest_unamortized_residual': max([observed_residual(c) for c in stuck] or [0]),
        'record_largest_unamortized_residual_cells': sorted(
            c.cid for c in stuck if observed_residual(c) == max([observed_residual(x) for x in stuck] or [0])),
        'record_largest_full_family_b_residual': max([observed_residual(c) for c in fullb] or [0]),
        'record_largest_full_family_b_cells': sorted(
            c.cid for c in fullb if observed_residual(c) == max([observed_residual(x) for x in fullb] or [0])),
        'record_largest_failing_disbursement': max([c.B for c in stuck] or [0]),
        'record_largest_failing_disbursement_cells': sorted(
            c.cid for c in stuck if c.B == max([x.B for x in stuck] or [0])),
    }


# -------------------------------------------------- gates.md site assertions --

def site_claims():
    """Grades the per-cell claims made at individual gates.md sites, so that
    'this site does not need scoping because it is true on its own named cells'
    is a MEASUREMENT and not an opinion."""
    cells, _ = load_cells('all')
    by_id = {}
    for c in cells:
        by_id.setdefault(c.cid, c)
    out = {}

    # site "Their residual is B_minor - n*delta ... leave exactly 200 minor units"
    trio = ['T229-R600p0-N200-B201', 'T229-R600p0-N200-B251', 'T229-R600p0-N200-B299']
    rows = []
    for cid in trio:
        c = by_id[cid]
        rows.append({'id': cid, 'n': c.n, 'B': c.B, 'delta': c.delta,
                     'B_minus_n_delta': c.B - c.n * c.delta,
                     'repaid': c.observed_principal,
                     'OUTSTANDING_residual': observed_residual(c),
                     'twin_min_B_ndelta': twin(c)})
    out['trio_B201_B251_B299'] = {
        'rows': rows,
        'all_leave_exactly_200': all(r['OUTSTANDING_residual'] == 200 for r in rows),
        'B_minus_n_delta_equals_REPAID_not_residual':
            all(r['B_minus_n_delta'] == r['repaid'] for r in rows),
        'B_minus_n_delta_equals_the_residual':
            all(r['B_minus_n_delta'] == r['OUTSTANDING_residual'] for r in rows),
    }

    # site "Two cells reach it ... and both leave exactly n*delta with delta = 1"
    pair = ['T219-R600p0-N3000-B3001', 'T219-R600p0-N3000-B4499']
    prow = []
    for cid in pair:
        c = by_id[cid]
        prow.append({'id': cid, 'n': c.n, 'B': c.B, 'delta': c.delta,
                     'n_delta': c.n * c.delta,
                     'OUTSTANDING_residual': observed_residual(c),
                     'law_ii_holds': law_ii(c) == c.observed_principal})
    out['pair_B3001_B4499'] = {
        'rows': prow,
        'both_leave_exactly_n_delta': all(r['OUTSTANDING_residual'] == r['n_delta'] for r in prow),
    }

    # site "at n = 104 and n = 108, E = 0 against I1q = 1, so delta = 1 and B <= n*delta"
    small = [cid for cid in by_id
             if cid.endswith('-N104-B1') or cid.endswith('-N108-B1') or cid.endswith('-N103-B1')]
    out['n103_n104_n108_B1'] = sorted(
        [{'id': by_id[cid].cid, 'n': by_id[cid].n, 'B': by_id[cid].B, 'E': by_id[cid].E,
          'I1q': by_id[cid].I1q, 'delta': by_id[cid].delta,
          'full_family_b': full_family_b(by_id[cid]),
          'observed_principal': by_id[cid].observed_principal,
          'law_ii_holds': law_ii(by_id[cid]) == by_id[cid].observed_principal}
         for cid in small], key=lambda r: (r['n'], r['id']))

    # site "partial-shortfall ... residual 833 minor against a 999-minor disbursement"
    c = by_id['T159-R600p0-N2000-B999']
    out['B999_residual_833'] = {
        'id': c.cid, 'B': c.B, 'repaid': c.observed_principal,
        'OUTSTANDING_residual': observed_residual(c),
        'is_833': observed_residual(c) == 833,
        'twin_predicts': twin(c),
    }
    return out


# ------------------------------------------------------- instrument hygiene --

def _is_benign_float_name(node, parents):
    """FU-T277-7: a bare `float` NAME inside `isinstance(x, float)` or a type
    comparison is the float DETECTOR naming the type it detects, not a float in
    a money path. Everything else is HARD."""
    p = parents.get(id(node))
    if isinstance(p, ast.Call):
        f = p.func
        if isinstance(f, ast.Name) and f.id in ('isinstance', 'issubclass') and node in p.args[1:]:
            return True
    if isinstance(p, ast.Tuple):
        gp = parents.get(id(p))
        if isinstance(gp, ast.Call):
            f = gp.func
            if isinstance(f, ast.Name) and f.id in ('isinstance', 'issubclass'):
                return True
    if isinstance(p, ast.Compare):
        return True
    return False


def float_audit(path):
    src = open(path, 'r').read()
    tree = ast.parse(src)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    hard, benign = [], []
    for node in ast.walk(tree):
        ln = getattr(node, 'lineno', 0)
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            hard.append((ln, 'float literal'))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            hard.append((ln, 'true-division node'))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ('float', 'round'):
            hard.append((ln, '%s() call' % node.func.id))
        elif isinstance(node, ast.Name) and node.id == 'float':
            if _is_benign_float_name(node, parents):
                benign.append((ln, 'float name in a type-test position (detector)'))
            else:
                hard.append((ln, 'bare `float` name outside a type test'))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                names = [node.module or '']
            for nm in names:
                root = nm.split('.')[0]
                if root in FORBIDDEN_MODULES:
                    hard.append((ln, 'forbidden module import: %s' % nm))
                low = nm.lower()
                for mark in FORBIDDEN_IMPORT_MARKS:
                    if mark in low:
                        hard.append((ln, 'INDEPENDENCE VIOLATION: imports %s' % nm))
    return hard, benign


# ----------------------------------------------------------------- selftest --

def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print('  %-58s %s   got=%r want=%r' % (name, 'ok  ' if good else 'FAIL', got, want))

    print('T332 twin-audit selftest')
    print(' minor-unit parser')
    check('minor("0.28")', minor('0.28'), 28)
    check('minor("15010.01")', minor('15010.01'), 1501001)
    check('minor("0.00")', minor('0.00'), 0)
    # A float is manufactured HERE THE WAY THE REAL THREAT ARRIVES — out of JSON —
    # rather than with a float literal. That is not squeamishness: this file's own
    # auditor scores a float literal HARD with no whitelist, so writing `minor(0.28)`
    # to prove the parser refuses floats would have made the refusal test the one
    # money-path violation in the file. FU-T277-7 one level out, and it is fixed at
    # source instead of excused.
    json_float = json.loads('{"x": 0.28}')['x']
    try:
        minor(json_float)
        check('minor(<float from JSON>) refuses', 'accepted', 'refused')
    except Refuse:
        check('minor(<float from JSON>) refuses', 'refused', 'refused')
    try:
        minor('0.284')
        check('minor("0.284") refuses', 'accepted', 'refused')
    except Refuse:
        check('minor("0.284") refuses', 'refused', 'refused')

    print(' exact rate arithmetic')
    check('monthly_rate("600.0")', monthly_rate('600.0'), (1, 2))
    check('monthly_rate("21.6")', monthly_rate('21.6'), (9, 500))
    check('monthly_rate("36.0")', monthly_rate('36.0'), (3, 100))
    check('monthly_rate("7.0")', monthly_rate('7.0'), (7, 1200))
    check('7/1200 terminates in 19 digits?', terminates_within(1200, 19), False)
    check('1/2 terminates in 19 digits?', terminates_within(2, 19), True)

    print(' HALF_UP quantizer')
    check('half_up(1,2)  -> 1', half_up(1, 2), 1)             # 0.5 -> 1
    check('half_up(3,2)  -> 2', half_up(3, 2), 2)             # 1.5 -> 2
    check('half_up(999,2) -> 500', half_up(999, 2), 500)      # 499.5 -> 500
    check('half_up(252,500) -> 1', half_up(252, 500), 1)      # 0.504 -> 1
    check('half_up(1,3)  -> 0', half_up(1, 3), 0)

    print(' hand-worked B999/n2000 at 600.0 % (the sharpest of the seven)')
    rn, rd = monthly_rate('600.0')
    i1q = half_up(999 * rn, rd)
    check('I1q(B=999)', i1q, 500)
    check('delta with E=499', i1q - 499, 1)
    check('law (ii) predicts', max(0, 999 - 2000 * 1), 0)
    check('twin predicts residual', min(999, 2000 * 1), 999)

    print(' the ALGEBRAIC IDENTITY B - max(0, B-n*d) == min(B, n*d), exhaustively')
    bad = []
    for B in range(0, 60):
        for nd in range(-20, 60):
            lhs = B - (B - nd if B - nd > 0 else 0)
            rhs = B if B < nd else nd
            if lhs != rhs:
                bad.append((B, nd))
    check('counterexamples over B in [0,60), n*d in [-20,60)', bad, [])

    print(' instrument hygiene (this file)')
    hard, benign = float_audit(__file__)
    check('HARD float/independence hits in this file', hard, [])
    print('  BENIGN detector hits: %r' % (benign,))

    print('  SELFTEST %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


# -------------------------------------------------------------- expectations --

PINNED = {
    't229corpus': {
        'total_captures': 349, 'threw': 2, 'rate_inexact': 0,
        'admitted': 347, 'stuck': 296,
        'delta_histogram': {'0': 113, '1': 183},
        'fact_a_holds': 220, 'fact_a_fails': 76,
        'law_ii_holds': 289, 'law_ii_fails': 7,
        'law_ii_on_fact_a': 213, 'law_ii_on_delta0': 113,
        'law_ii_on_full_family_b': 176, 'full_family_b_n': 183,
        'partial_family_b_n': 0,
        'twin_holds': 289, 'twin_fails': 7,
        'twin_identity_holds_every_cell': True,
        'exception_sets_identical': True,
        'observed_residual_EXCEEDS_formula': 0,
        'observed_residual_below_formula': 7,
        'fact_a_and_law_ii_exceptions_intersect': 0,
        'delta0_and_law_ii_exceptions_intersect': 0,
        'failing_cells_outside_conservative_region': 0,
        'failing_cells_inside_conservative_region': 7,
        'header_ne_rowsum': 0,
        'principal_in_last_row_only_on_fact_a': '220/220',
        'descriptive_last_row_form_on_fact_a': '220/220',
    },
    'all': {
        'total_captures': 775, 'threw': 6, 'rate_inexact': 8,
        'admitted': 761, 'stuck': 578,
        'law_ii_holds': 571, 'law_ii_fails': 7,
        'twin_holds': 571, 'twin_fails': 7,
        'twin_identity_holds_every_cell': True,
        'exception_sets_identical': True,
        'observed_residual_EXCEEDS_formula': 0,
        'observed_residual_below_formula': 7,
        'failing_cells_outside_conservative_region': 0,
        'failing_cells_inside_conservative_region': 7,
        'header_ne_rowsum': 0,
        'partial_family_b_n': 5, 'partial_family_b_law_holds': 5,
        'record_largest_unamortized_residual': 3000,
        'record_largest_full_family_b_residual': 2999,
        'record_largest_failing_disbursement': 4499,
        'principal_in_last_row_only_on_fact_a': '441/441',
        'descriptive_last_row_form_on_fact_a': '441/441',
    },
}

SEVEN = (
    ('T117P2-R600p0-N108-B11', 108, 11, 5, 6, 1, 0, 5, 11, 6),
    ('T117P2-R600p0-N121-B11', 121, 11, 5, 6, 1, 0, 4, 11, 7),
    ('T117P2-R600p0-N150-B11', 150, 11, 5, 6, 1, 0, 2, 11, 9),
    ('T159-R600p0-N108-B11', 108, 11, 5, 6, 1, 0, 5, 11, 6),
    ('T159-R600p0-N121-B11', 121, 11, 5, 6, 1, 0, 4, 11, 7),
    ('T159-R600p0-N150-B11', 150, 11, 5, 6, 1, 0, 2, 11, 9),
    ('T159-R600p0-N2000-B999', 2000, 999, 499, 500, 1, 0, 166, 999, 833),
)


def grade(scope, rep):
    bad = []
    for k, want in PINNED[scope].items():
        got = rep.get(k)
        if got != want:
            bad.append('  %-46s got=%r  pinned=%r' % (k, got, want))
    if rep['setting_violations']:
        bad.append('  production-setting violations: %r' % (rep['setting_violations'][:5],))
    return bad


def seven_tuples(rep):
    return tuple(sorted(
        (e['id'], e['n'], e['B'], e['E'], e['I1q'], e['delta'],
         e['law_ii_predicts'], e['observed_principal'],
         e['twin_predicts_residual'], e['observed_residual'])
        for e in rep['exceptions']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--scope', choices=['t229corpus', 'all'])
    ap.add_argument('--seven', action='store_true')
    ap.add_argument('--sites', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    if a.sites:
        s = site_claims()
        print(json.dumps(s, indent=2, sort_keys=True))
        okk = (s['trio_B201_B251_B299']['all_leave_exactly_200']
               and s['trio_B201_B251_B299']['B_minus_n_delta_equals_REPAID_not_residual']
               and not s['trio_B201_B251_B299']['B_minus_n_delta_equals_the_residual']
               and s['pair_B3001_B4499']['both_leave_exactly_n_delta']
               and s['B999_residual_833']['is_833'])
        print('SITES: %s' % ('PASS' if okk else 'FAIL'))
        return 0 if okk else 1

    if a.seven:
        rep = census('t229corpus')
        got = seven_tuples(rep)
        print('THE SEVEN — T332\'s own derivation, integer minor units, I1q COMPUTED')
        print('%-24s %5s %5s %5s %5s %3s | law(ii)=%s obs=%s | twin=%s obs=%s'
              % ('id', 'n', 'B', 'E', 'I1q', 'd', 'P', 'P', 'R', 'R'))
        for e in rep['exceptions']:
            print('%-24s %5d %5d %5d %5d %3d | %7d %7d | %6d %6d   rows=%s'
                  % (e['id'], e['n'], e['B'], e['E'], e['I1q'], e['delta'],
                     e['law_ii_predicts'], e['observed_principal'],
                     e['twin_predicts_residual'], e['observed_residual'],
                     e['nonzero_principal_rows']))
        good = got == tuple(sorted(SEVEN))
        print('\nfull-tuple comparison against the pinned expectation: %s'
              % ('MATCH' if good else 'MISMATCH'))
        if not good:
            print('  got  = %r' % (got,))
            print('  want = %r' % (tuple(sorted(SEVEN)),))
        return 0 if good else 1

    scopes = [a.scope] if a.scope else ['t229corpus', 'all']
    rc = 0
    for sc in scopes:
        rep = census(sc)
        if a.json:
            print(json.dumps(rep, indent=2, sort_keys=True))
        else:
            print('=== scope %s ===' % sc)
            for k in sorted(rep):
                if k == 'exceptions':
                    continue
                print('  %-46s %r' % (k, rep[k]))
            print('  exceptions:')
            for e in rep['exceptions']:
                print('    %-24s law(ii) predicts %d, observed %d | twin predicts residual %d, observed %d'
                      % (e['id'], e['law_ii_predicts'], e['observed_principal'],
                         e['twin_predicts_residual'], e['observed_residual']))
        bad = grade(sc, rep)
        if bad:
            rc = 1
            print('  GRADE: FAIL')
            for b in bad:
                print(b)
        else:
            print('  GRADE: PASS (every pinned figure reproduced)')
    return rc


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Refuse as e:
        sys.stderr.write('REFUSED: %s\n' % e)
        sys.exit(2)
