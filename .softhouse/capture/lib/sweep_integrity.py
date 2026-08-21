#!/usr/bin/env python3
"""sweep_integrity — the SHARED integrity line for every capture sweep in this program. Task T169.

WHAT WAS WRONG
--------------
Every sweep publishes a line of the form

    N asked / N observed / 0 errored / 0 skipped

and that line is cited as PROOF THE SWEEP IS COMPLETE. On the pre-T169 rigs it could not have said
anything else. A `java.lang.StackOverflowError` is an `Error`, not a `RuntimeException`, so the
shared Java handler never saw it: it escaped `run()`, escaped `main()`, and killed the JVM before a
byte of JSON was printed — no capture, therefore no integrity line at all. And the one class the
handler DID see, `RuntimeException`, was printed to stderr by that same handler, which every runner
in this program treats as a refusal — so a recorded error also produced no integrity line. "0
errored" was therefore the ONLY value a completed run could print. That is a guard that cannot fail
(P-22, P-35), and this program has ruled such a guard worse than none, because it is believed.

WHAT THIS MODULE ENFORCES
-------------------------
Four outcomes, mutually exclusive and exhaustive over the ASKED id list:

    asked      the ids the sweep registered before it ran
    observed   a cell that came back with a schedule
    threw      a cell whose seam call threw — RECORDED, NAMED, and NEVER GRADED as an observation
    skipped    an id that was asked for and is not in the capture at all

and the tally is refused unless  observed + threw + skipped == asked.

Two lies are made impossible, and they are different lies:
  * a threw cell counted as an observation  -> `assert_not_graded_as_observed` raises;
  * a threw cell silently absent            -> it lands in `skipped`, which is printed, named, and
                                               non-zero, so it cannot pass for "nothing happened".

A cell that carries BOTH `outcome: "threw"` and a non-null `observed` block is a contradiction in
the capture itself, and this module raises on it rather than picking one.

MONEY: this module counts cells. It reads no money, compares no money and does no arithmetic on
money, so P-25 (no float in analysis code) is satisfied vacuously — there is no numeric parsing
here at all.

Self-test:  python3 sweep_integrity.py --selftest
"""

THREW = 'threw'
OBSERVED = 'observed'
SKIPPED = 'skipped'


class IntegrityError(Exception):
    """Raised when the capture contradicts itself, or when the tally does not close."""


def cell_outcome(cell):
    """Classify ONE capture cell.

    Recognises both shapes:
      * T169 and later  -- an explicit `"outcome": "threw"` / `"outcome": "observed"` key;
      * pre-T169        -- no `outcome` key; a throw is `observed: null` and/or an `error` key.

    Refuses to guess when the two disagree.
    """
    declared = cell.get('outcome')
    has_error = ('error' in cell) or ('errorClass' in cell)
    obs = cell.get('observed', None)

    if declared is not None and declared not in (THREW, OBSERVED):
        raise IntegrityError('%s: unknown outcome %r' % (cell.get('id'), declared))

    if declared == THREW and obs is not None:
        raise IntegrityError(
            '%s: declared outcome "threw" but carries a non-null observed block — a threw cell is '
            'NOT an observation and must never be graded as one' % cell.get('id'))
    if declared == OBSERVED and (obs is None or has_error):
        raise IntegrityError(
            '%s: declared outcome "observed" but observed is null and/or an error is recorded'
            % cell.get('id'))

    if declared is not None:
        return declared
    # pre-T169 shape
    if obs is None or has_error:
        return THREW
    return OBSERVED


def throw_detail(cell):
    """(id, class, message, top frame) for a threw cell. Never invents any of the four."""
    cls = cell.get('errorClass')
    msg = cell.get('errorMessage')
    if cls is None:
        # pre-T169 shape: a single "error" string "<class>: <message>"
        legacy = cell.get('error')
        if isinstance(legacy, str) and ': ' in legacy:
            cls, msg = legacy.split(': ', 1)
        elif isinstance(legacy, str):
            cls = legacy
    frames = cell.get('errorStackTop') or []
    top = frames[0] if frames else None
    return (cell.get('id'), cls, msg, top)


class Tally(object):
    __slots__ = ('asked', 'observed', 'threw', 'skipped', 'extra', 'reordered',
                 'threw_ids', 'skipped_ids', 'extra_ids', 'threw_details')

    def __init__(self):
        self.asked = 0
        self.observed = 0
        self.threw = 0
        self.skipped = 0
        self.extra = 0
        self.reordered = False
        self.threw_ids = []
        self.skipped_ids = []
        self.extra_ids = []
        self.threw_details = []

    def integrity_line(self):
        return ('asked %d / observed %d / threw %d / skipped %d'
                % (self.asked, self.observed, self.threw, self.skipped))

    def report(self):
        out = [self.integrity_line()]
        if self.extra:
            out.append('  EXTRA (emitted but never asked for): %d %r' % (self.extra, self.extra_ids[:10]))
        if self.reordered:
            out.append('  REORDERED: the emitted id list is the asked set in a different order')
        for cid, cls, msg, top in self.threw_details:
            # `null` and `<absent>` are distinct and are printed distinctly. A throwable whose
            # getMessage() is null is not the same as a capture that recorded no message field.
            shown = 'null' if msg is None else repr(msg)
            out.append('  THREW %s -> %s message=%s | top frame %s' % (cid, cls, shown, top))
        for cid in self.skipped_ids:
            out.append('  SKIPPED %s -> asked for, absent from the capture' % cid)
        return '\n'.join(out)


def tally(captures, asked_ids):
    """Classify a whole sweep. `asked_ids` is the registered id list, in order.

    Raises IntegrityError if the tally does not close, or if any cell contradicts itself.
    """
    by_id = {}
    for cell in captures:
        cid = cell.get('id')
        if cid in by_id:
            raise IntegrityError('%s: emitted twice' % cid)
        by_id[cid] = cell

    t = Tally()
    t.asked = len(asked_ids)
    for cid in asked_ids:
        cell = by_id.get(cid)
        if cell is None:
            t.skipped += 1
            t.skipped_ids.append(cid)
            continue
        outcome = cell_outcome(cell)
        if outcome == THREW:
            t.threw += 1
            t.threw_ids.append(cid)
            t.threw_details.append(throw_detail(cell))
        else:
            t.observed += 1

    asked_set = set(asked_ids)
    for cell in captures:
        if cell.get('id') not in asked_set:
            t.extra += 1
            t.extra_ids.append(cell.get('id'))

    emitted = [c.get('id') for c in captures]
    t.reordered = (emitted != list(asked_ids)) and (sorted(emitted) == sorted(asked_ids))

    if t.observed + t.threw + t.skipped != t.asked:
        raise IntegrityError('tally does not close: %d observed + %d threw + %d skipped != %d asked'
                             % (t.observed, t.threw, t.skipped, t.asked))
    return t


def assert_not_graded_as_observed(captures, graded_ids):
    """Refuse if any id a caller is about to GRADE is a cell that threw.

    This is the second half of the rule. `tally` makes a throw visible; this makes it ungradeable.
    """
    by_id = {c.get('id'): c for c in captures}
    offenders = []
    for cid in graded_ids:
        cell = by_id.get(cid)
        if cell is None:
            offenders.append('%s: absent from the capture, cannot be graded' % cid)
        elif cell_outcome(cell) == THREW:
            offenders.append('%s: THREW (%s) — a threw cell is not an observation' % (cid, throw_detail(cell)[1]))
    if offenders:
        raise IntegrityError('refusing to grade %d cell(s):\n  %s' % (len(offenders), '\n  '.join(offenders)))


# ---------------------------------------------------------------------------------------------
# SELF-TEST — P-22. Every counter and every refusal below is driven RED here, on synthetic input.
# If this file is edited so that a counter stops counting, this goes red.
# ---------------------------------------------------------------------------------------------
def _selftest():
    fails = []

    def check(what, ok):
        print(('ok    ' if ok else 'FAIL  ') + what)
        if not ok:
            fails.append(what)

    def raises(what, fn):
        try:
            fn()
        except IntegrityError as exc:
            print('ok    %s  -> IntegrityError: %s' % (what, str(exc).split('\n')[0]))
            return
        fails.append(what)
        print('FAIL  %s  -> did NOT raise' % what)

    obs = lambda i: {'id': i, 'outcome': 'observed', 'observed': {'periods': []}}
    thr = lambda i: {'id': i, 'outcome': 'threw', 'observed': None,
                     'errorClass': 'java.lang.StackOverflowError', 'errorMessage': None,
                     'errorStackTop': ['org.apache.fineract...ProgressiveEMICalculator.java:1214']}
    legacy_thr = lambda i: {'id': i, 'observed': None,
                            'error': 'java.lang.StackOverflowError: null',
                            'errorStackTop': ['ProgressiveEMICalculator.java:1214']}

    t = tally([obs('A'), obs('B'), obs('C')], ['A', 'B', 'C'])
    check('all clean -> asked 3 / observed 3 / threw 0 / skipped 0',
          t.integrity_line() == 'asked 3 / observed 3 / threw 0 / skipped 0')

    t = tally([obs('A'), thr('B'), obs('C')], ['A', 'B', 'C'])
    check('one throw -> asked 3 / observed 2 / threw 1 / skipped 0',
          t.integrity_line() == 'asked 3 / observed 2 / threw 1 / skipped 0')
    check('the throw is NAMED with its class', t.threw_details[0][1] == 'java.lang.StackOverflowError')
    check('the throw keeps its top frame', 'ProgressiveEMICalculator.java:1214' in (t.threw_details[0][3] or ''))

    t = tally([obs('A'), legacy_thr('B'), obs('C')], ['A', 'B', 'C'])
    check('a PRE-T169 shaped throw (no outcome key) is still counted as threw',
          t.integrity_line() == 'asked 3 / observed 2 / threw 1 / skipped 0')
    check('a PRE-T169 shaped throw still yields its class',
          t.threw_details[0][1] == 'java.lang.StackOverflowError')

    t = tally([obs('A'), obs('C')], ['A', 'B', 'C'])
    check('a missing cell -> asked 3 / observed 2 / threw 0 / skipped 1',
          t.integrity_line() == 'asked 3 / observed 2 / threw 0 / skipped 1')
    check('the missing cell is NAMED', t.skipped_ids == ['B'])

    t = tally([obs('A'), obs('B'), obs('Z')], ['A', 'B'])
    check('an unasked cell is flagged EXTRA', t.extra == 1 and t.extra_ids == ['Z'])

    t = tally([obs('B'), obs('A')], ['A', 'B'])
    check('a transposed id list is flagged REORDERED', t.reordered is True)

    # the two lies, each refused
    raises('a threw cell carrying an observed block is a contradiction',
           lambda: tally([{'id': 'A', 'outcome': 'threw', 'observed': {'periods': []}}], ['A']))
    raises('an observed cell carrying an error is a contradiction',
           lambda: tally([{'id': 'A', 'outcome': 'observed', 'observed': {'periods': []},
                           'error': 'boom'}], ['A']))
    raises('a duplicated id is refused',
           lambda: tally([obs('A'), obs('A')], ['A']))
    raises('an unknown outcome token is refused',
           lambda: tally([{'id': 'A', 'outcome': 'maybe'}], ['A']))
    raises('GRADING a threw cell is refused',
           lambda: assert_not_graded_as_observed([obs('A'), thr('B')], ['A', 'B']))
    raises('GRADING an absent cell is refused',
           lambda: assert_not_graded_as_observed([obs('A')], ['A', 'B']))

    # grading only the clean cells is allowed
    assert_not_graded_as_observed([obs('A'), thr('B')], ['A'])
    check('grading only the OBSERVED cells is allowed', True)

    print()
    print('sweep_integrity selftest: %d failure(s)' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        sys.exit(_selftest())
    sys.exit('usage: sweep_integrity.py --selftest   (this file is a library)')
