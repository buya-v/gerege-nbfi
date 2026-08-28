#!/usr/bin/env python3
"""T332 — the RE-RUNNING sweep guard for law (ii) and its algebraic twin in `.softhouse/gates.md`.

WHY THIS EXISTS
  T277 corrected law (ii) -- `TOTAL PRINCIPAL = max(0, B_minor - n*delta)` -- where it was
  looking, and did not sweep its own file for the SAME CLAIM IN OTHER WORDS. T278 found five
  further live homes; T332 found more. A transcribed list of sites rots the moment somebody
  adds a paragraph, so the list is not the deliverable: THIS is. Run it and it tells you,
  today, whether every wording of the claim in gates.md is scoped to its exception set.

WHAT IT DOES
  1. Sweeps gates.md with a NAMED, PRINTED selector set (symbolic AND prose forms).
  2. Classifies each hit against a LEDGER keyed by a quoted SNIPPET OF THE LINE, never by a
     line number (P-86 -- "an id is a cardinal": prefer a grep-able anchor. gates.md line
     numbers move every time anybody edits above them, which is this task's own subject).
  3. FAILS (exit 1) when
       - a hit matches no ledger entry            -> A NEW, UNCLASSIFIED RESTATEMENT
       - a ledger entry matches nothing           -> the site was deleted or re-worded
       - a SCOPED site has lost its scope marker  -> somebody removed the correction
     and prints, for every hit, the nearest preceding markdown heading as its anchor.

SCOPE MARKER
  A scoped site must carry, within its scope window, one of the anchors in SCOPE_MARKS --
  readable prose that doubles as a machine anchor.

EXEMPTION CLASSES, and none of them is "it looked fine"
  EXEMPT-FROZEN      the fenced law block itself, deliberately left byte-unchanged because it
                     is quoted verbatim elsewhere; the warning above it and the CORRECTION
                     below it are its scope.
  EXEMPT-CORRECTION  a quotation of the law INSIDE the correction that refutes it.
  EXEMPT-PERCELL     a measured per-cell figure, true on the cells it names -- graded by
                     `t332_twin_audit.py --sites`, not by eye.
  EXEMPT-LIMITATION  a statement that NARROWS the claim (a disclaimer), not one that asserts it.
  EXEMPT-ATTRIBUTED  a past-tense report of what an earlier task registered or predicted.

No float is involved anywhere in this file; it is a text instrument. It still audits itself.
"""

import argparse
import ast
import os
import re
import sys

GATES = '.softhouse/gates.md'

# --------------------------------------------------------------- the selector --
# Printed with every run. "Not found" is a statement about the SEARCH, so the search
# is published beside the figure.
SELECTORS = [
    ('TWIN-SYMBOLIC', r'min\(\s*B_minor\s*,\s*n\s*[·*x]\s*(?:δ|delta)\s*\)'),
    ('TWIN-SYMBOLIC-SHORT', r'min\(\s*B\s*,\s*n\s*[·*x]\s*(?:δ|delta)\s*\)'),
    ('LAW-SYMBOLIC', r'max\(\s*0\s*,\s*B_minor\s*[−\-]\s*n\s*[·*x]\s*(?:δ|delta)\s*\)'),
    ('DIFFERENCE-FORM', r'B_minor\s*[−\-]\s*n\s*[·*x]\s*(?:δ|delta)'),
    ('NDELTA-BARE', r'n\s*[·*x]\s*(?:δ|delta)'),
    # NOTE the `\b` after `cap`: without it this selector fires on "is the capture", a false
    # positive it produced on two lines of `### Evidence`. Tightened at source rather than
    # ledgered as an exemption -- a selector that has to be excused is a selector nobody trusts.
    ('CAP-PROSE', r'(?:term (?:is only|enters only as)|capped by|is (?:only )?the cap\b|the cap the law names)'),
    ('FUNCTION-OF-PROSE', r'(?:function of the (?:\*\*)?PRINCIPAL|fact about the (?:\*\*)?PRINCIPAL|'
                          r'principals asked are what the figure is)'),
    ('TOTAL-PRINCIPAL-LAW', r'TOTAL PRINCIPAL\s*=' ),
]

# Anchors that count as "this site is scoped to the exception set".
SCOPE_MARKS = [
    r'UPPER BOUND, NOT AN EQUALITY',
    r'CORRECTION \(T277\)',
    r'FALSE on a measured set of seven',
    r'law \(ii\) of the block above is FALSE',
]

# How far a scope marker may sit from the hit and still cover it.
WINDOW_BEFORE = 4
WINDOW_AFTER = 14

# ------------------------------------------------------------------- ledger --
# key   : an exact substring of the hit line -- a grep-able anchor, not a line number.
# class : SCOPED (must be covered by a scope marker) or one of the EXEMPT-* classes.
# why   : the argument for the classification, in one sentence.
LEDGER = [
    # ---- LIVE SITES that must carry a scope marker -------------------------------
    ('The residual is AT MOST `min(B_minor, n·δ)`: the principal is what it is',
     'SCOPED', 'S1 | STANDING RULE, seventh mechanism: present-tense general law inside a rule a later '
               'writer is meant to APPLY.'),
    ('a fact about and the term is only the cap. T117 and T159 topped out',
     'SCOPED', 'S1 | continuation of the same sentence.'),
    ('`B_minor − n·δ` — **1, 51 and 99** minor units at `δ = 1` and `n = 200`',
     'SCOPED', 'S2* | per-cell claim about B201/B251/B299, and MEASURED WRONG IN ITS OWN RIGHT before '
               'T332: the sentence called `B_minor − n·δ` "their residual" when it is what those '
               'cells REPAY (1/51/99) and their residual is 200. FU-T332-1.'),
    ('derived the FULL/PARTIAL split from it** — `TOTAL PRINCIPAL =',
     'SCOPED', 'S3 | law (ii) proper, line-wrapped; the formula lands on the next line.'),
    ('max(0, B_minor − n·δ)`, which predicted the amount repaid on three partial cells',
     'SCOPED', 'S3 | law (ii) proper, stated live in the family-B answered-questions block; it pointed '
               'at gap 2 but not at the correction that narrows it.'),
    ('`min(B_minor, n·δ)`; the term enters only as the **cap**',
     'SCOPED', 'S4 | T219 correction block: present-tense general law about "an unrescued family-B cell".'),
    ('residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)',
     'SCOPED', 'S5 | the twin identity itself, fenced, in THE RESIDUAL RECORD block; the identity is '
               'exact and the law under it is not, which is exactly why the twin inherits the '
               'seven counterexamples.'),
    ('the term is only the cap; **the principals asked are what the figure is',
     'SCOPED', 'S6* | the SEVENTH site. PROSE ONLY -- it contains no formula, so every grep for the '
               'symbolic form misses it. This is why the sweep carries CAP-PROSE selectors.'),
    ('the residual is AT MOST `min(B_minor, n·δ)` — a function of the **PRINCIPAL**',
     'SCOPED', 'S7 | T241 pointer INSIDE the superseded G-8-NOTICE. The block is history, but this '
               'blockquote is the present-tense POINTER T241 added, and the block itself rules '
               'that adding a pointer does not corrupt a historical record.'),
    ('The residual of an unrescued family-B cell is AT MOST `min(B_minor, n·δ)` — a fact about the PRINCIPAL',
     'SCOPED', 'S8 | PRESCRIPTIVE: the ground of a "must" telling a future writer what to disclose '
               'about G-8. A false rule in a prescription propagates into work not yet done. '
               'CORRECTED FIRST.'),
    ('capped by the term.** T219 tripled the record *at T159\'s own term',
     'SCOPED', 'S8 | continuation of the prescriptive sentence.'),

    # ---- ARGUED EXEMPT ------------------------------------------------------------
    ('last row EMI = E + B ;   TOTAL PRINCIPAL = max(0, B_minor − n·δ)',
     'EXEMPT-FROZEN', 'the fenced law block, deliberately byte-unchanged because it is quoted '
                      'verbatim elsewhere; the warning immediately above it and the CORRECTION '
                      'immediately below it are its scope.'),
    ('FULL family B    ⟺ δ ≥ 1 ∧ B_minor ≤ n·δ',
     'EXEMPT-FROZEN', 'same fenced block.'),
    ('PARTIAL family B ⟺ δ ≥ 1 ∧ n·δ < B_minor < (δ + ½)·n , repaying exactly B_minor − n·δ',
     'EXEMPT-FROZEN', 'same fenced block; and measured TRUE on all 5 PARTIAL witnesses.'),
    ('`TOTAL PRINCIPAL = max(0, B_minor − n·δ)` — **does not**',
     'EXEMPT-CORRECTION', 'quotation inside CORRECTION (T277), stated in order to refute it.'),
    ('| (ii) `TOTAL PRINCIPAL = max(0, B_minor − n·δ)` | all 296 |',
     'EXEMPT-CORRECTION', 'the correction\'s own grading table.'),
    ('| `B` minor | `E` | `I₁q` | `δ` | `B ≤ n·δ`?',
     'EXEMPT-CORRECTION', 'the correction\'s own seven-cell table header.'),
    ('**Every one of the seven satisfies the block\'s own `FULL family B` antecedent**, `δ ≥ 1 ∧ B_minor ≤ n·δ`',
     'EXEMPT-CORRECTION', 'the correction stating the antecedent in order to refute the law on it.'),
    ('TOTAL PRINCIPAL = max(0, E + B_minor − I_last)',
     'EXEMPT-CORRECTION', 'a DIFFERENT law -- the DESCRIPTIVE last-row form the correction '
                          'introduces, which holds 220/220 and 441/441 including all seven. It is '
                          'not law (ii) and does not inherit its exception set.'),
    ('`max(0, B_minor − n·δ)` is computed from the inputs before the oracle is asked',
     'EXEMPT-CORRECTION', 'inside the correction, contrasting the predictive law with the '
                          'descriptive last-row form.'),
    ('predicts `TOTAL PRINCIPAL = 0` on every one of them. Law (ii) holds on **213 of the 220**',
     'EXEMPT-CORRECTION', 'gap 2\'s own T277 correction note; it states the law only to refute it '
                          'and cites `#### CORRECTION (T277)` on the next line.'),
    ('and both leave exactly `n·δ`',
     'EXEMPT-PERCELL', 'measured per-cell figure about B3001/B4499; both leave exactly 3000 = n·δ '
                       '[t332_twin_audit.py --sites: pair_B3001_B4499.both_leave_exactly_n_delta].'),
    ('with `δ = 1`, which is the cap the law names',
     'EXEMPT-PERCELL', 'same sentence; the two named cells do sit at the cap.'),
    ('`E = 0` against `I₁q = 1`, so `δ = 1` and `B_minor = 1 ≤ n·δ` — FULL family B',
     'EXEMPT-PERCELL', 'per-cell derivation at n = 104 / 108, B = 1; law (ii) holds on every such '
                       'cell in the corpus [--sites: n103_n104_n108_B1].'),
    ('is `n·δ` there too. `n·δ` was measured at n = 3000 and at no other term',
     'EXEMPT-LIMITATION', 'a disclaimer that NARROWS the claim; it asserts nothing.'),
    ('registered before probing that the residual record is a function of the PRINCIPAL asked',
     'EXEMPT-ATTRIBUTED', 'past-tense report, in a contributor list, of what T219 registered; and '
                          'the axis claim it reports SURVIVES -- what fails is the EQUALITY, not '
                          'the direction.'),
    ('— **a function of the PRINCIPAL asked, capped by `n·δ`.** The term enters only as the cap',
     'EXEMPT-CORRECTION', 'the sentence under the scoped fenced identity, inside its scope window '
                          'and covered by the T332 note that follows the paragraph.'),
]

SELF = os.path.abspath(__file__)


def read_lines(path):
    with open(path, 'r') as fh:
        return fh.read().split('\n')


def nearest_heading(lines, idx):
    for j in range(idx, -1, -1):
        s = lines[j].lstrip('> ').rstrip()
        if s.startswith('#'):
            return s[:110]
    return '(no heading above)'


def sweep(lines):
    """Returns [(lineno, selector_names, text)] -- one entry per matching LINE."""
    hits = []
    for i, text in enumerate(lines):
        names = [nm for nm, pat in SELECTORS if re.search(pat, text)]
        if names:
            hits.append((i + 1, names, text))
    return hits


NOTE_OPEN = '[T332 —'
NOTE_CLOSE = ']**'
T332_SECTION = '#### T332 — THE SAME CLAIM, SWEPT'
BACKSCAN = 12


def strip_quote(s):
    return s.lstrip('> ').rstrip()


def inside_t332_note(lines, idx):
    """A hit that is part of a T332 SCOPE NOTE is not a new restatement; it is the
    correction. Detected structurally: scan back at most BACKSCAN lines and stop at
    the first quote-stripped-blank line (the note's separator) or at a note CLOSE.
    Stopping at the close is what keeps this from swallowing a genuine new site that
    a later writer parks immediately after a note."""
    if NOTE_OPEN in lines[idx]:
        return True
    j = idx - 1
    steps = 0
    while j >= 0 and steps < BACKSCAN:
        s = strip_quote(lines[j])
        if NOTE_OPEN in lines[j]:
            return True
        if s == '' or NOTE_CLOSE in lines[j]:
            return False
        j -= 1
        steps += 1
    return False


def covered(lines, idx):
    lo = max(0, idx - 1 - WINDOW_BEFORE)
    hi = min(len(lines), idx + WINDOW_AFTER)
    blob = '\n'.join(lines[lo:hi])
    return any(re.search(m, blob) for m in SCOPE_MARKS)


def self_audit():
    """This file handles no money, but a text instrument that grades a money record
    still states its own hygiene rather than assuming it. FU-T277-7 discipline: a
    `float` NAME in a type-test position is the detector, not a violation."""
    tree = ast.parse(open(SELF).read())
    parents = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parents[id(ch)] = node
    hard = []
    for node in ast.walk(tree):
        ln = getattr(node, 'lineno', 0)
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            hard.append((ln, 'float literal'))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ('float', 'round'):
            hard.append((ln, '%s() call' % node.func.id))
        elif isinstance(node, ast.Name) and node.id == 'float':
            p = parents.get(id(node))
            benign = isinstance(p, ast.Call) and isinstance(p.func, ast.Name) \
                and p.func.id in ('isinstance', 'issubclass')
            if not benign:
                hard.append((ln, 'bare `float` name'))
    return hard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default=GATES)
    ap.add_argument('--print-selector', action='store_true')
    ap.add_argument('--list', action='store_true', help='list every hit and its class')
    a = ap.parse_args()

    print('T332 SWEEP — every wording of law (ii) / its twin in %s' % a.file)
    print('')
    print('SELECTOR (published beside the figure — "not found" is a statement about the search):')
    for nm, pat in SELECTORS:
        print('    %-22s %s' % (nm, pat))
    print('SCOPE MARKS (any one of these inside [-%d, +%d] lines covers a SCOPED site):'
          % (WINDOW_BEFORE, WINDOW_AFTER))
    for m in SCOPE_MARKS:
        print('    %s' % m)
    print('WHERE I LOOKED: every line of %s, top to bottom, no section excluded.' % a.file)
    if a.print_selector:
        return 0

    lines = read_lines(a.file)
    hits = sweep(lines)
    print('')
    print('lines swept: %d   hit lines: %d   ledger entries: %d'
          % (len(lines), len(hits), len(LEDGER)))
    print('')

    used = set()
    unclassified = []
    uncovered = []
    rows = []
    for lineno, names, text in hits:
        # Two structural exemptions, applied before the ledger so that the correction
        # does not have to enumerate its own sentences:
        #   the T332 correction SECTION is to the twin what CORRECTION (T277) is to
        #   law (ii) -- it states the claim in order to bound it;
        #   a T332 SCOPE NOTE is the scoping itself.
        anchor = nearest_heading(lines, lineno - 1)
        if anchor.startswith(T332_SECTION):
            rows.append((lineno, 'EXEMPT-T332-SECTION', ','.join(names), text.strip()[:100], anchor))
            continue
        if inside_t332_note(lines, lineno - 1):
            rows.append((lineno, 'EXEMPT-T332-NOTE', ','.join(names), text.strip()[:100], anchor))
            continue
        match = None
        for k, (key, cls, why) in enumerate(LEDGER):
            if key in text:
                match = k
                break
        if match is None:
            unclassified.append((lineno, names, text))
            rows.append((lineno, 'UNCLASSIFIED', ','.join(names), text.strip()[:100], ''))
            continue
        used.add(match)
        key, cls, why = LEDGER[match]
        cov = covered(lines, lineno)
        if cls == 'SCOPED' and not cov:
            uncovered.append((lineno, key))
        rows.append((lineno, cls + ('' if cls != 'SCOPED' else (' [covered]' if cov else ' [UNCOVERED]')),
                     ','.join(names), text.strip()[:100], nearest_heading(lines, lineno - 1)))

    if a.list:
        for lineno, cls, names, text, anchor in rows:
            print('%5d  %-22s %-34s %s' % (lineno, cls, names, text))
            if anchor:
                print('       anchor: %s' % anchor)
        print('')

    stale = [LEDGER[k][0] for k in range(len(LEDGER)) if k not in used]

    ok = True
    if unclassified:
        ok = False
        print('FAIL — %d NEW, UNCLASSIFIED restatement(s) of the claim:' % len(unclassified))
        for lineno, names, text in unclassified:
            print('   line %d  [%s]  %s' % (lineno, ','.join(names), text.strip()[:160]))
            print('           anchor: %s' % nearest_heading(lines, lineno - 1))
        print('   -> scope it to the exception set, or add it to LEDGER with the argument for '
              'why it does not need scoping.')
    if stale:
        ok = False
        print('FAIL — %d ledger entr(ies) matched NOTHING (site deleted or re-worded):' % len(stale))
        for s in stale:
            print('   %r' % s)
    if uncovered:
        ok = False
        print('FAIL — %d SCOPED site(s) lost their scope marker:' % len(uncovered))
        for lineno, key in uncovered:
            print('   line %d  %r' % (lineno, key))

    hard = self_audit()
    if hard:
        ok = False
        print('FAIL — instrument hygiene: %r' % (hard,))

    n_scoped = sum(1 for _, cls, _, _, _ in rows if cls.startswith('SCOPED'))
    n_exempt = sum(1 for _, cls, _, _, _ in rows if cls.startswith('EXEMPT'))
    # DISTINCT sites, derived from the ledger's own site labels and never typed --
    # a claim can wrap across two lines and counting lines would over-report it.
    # A trailing '*' marks a site that was NOT among the six T278 named.
    sites = sorted({why.split('|')[0].strip()
                    for k in used for _, cls, why in [LEDGER[k]] if cls == 'SCOPED'})
    print('')
    print('SCOPED lines: %d over %d DISTINCT sites %s   (%d of them NOT among the six T278 named)'
          % (n_scoped, len(sites), sites, sum(1 for s in sites if s.endswith('*'))))
    print('argued-exempt lines: %d   unclassified: %d   stale ledger rows: %d'
          % (n_exempt, len(unclassified), len(stale)))
    print('T332 SWEEP: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
