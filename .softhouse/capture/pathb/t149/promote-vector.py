#!/usr/bin/env python3
"""T149 — promote the pinned HALF_UP exact tie as a PARITY vector, from the Path B capture.

TRANSCRIBES; never computes. Every money cell is the oracle's own emitted characters,
scaled major->minor by exact integer/string arithmetic (no float anywhere: the raw
response is read with parse_float=str, per P-25 / live obligation T145 — Path B emits
money as bare JSON NUMBERS, so a default decoder would make every money literal a
binary double).

It writes ONE file and computes nothing that is not already in the capture. Run it into
a scratch store first if you want to grade the candidate before promoting:

    python3 promote-vector.py /tmp/scratch/loanschedule/T149-PATHB-TIE.json
    python3 promote-vector.py .softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'out', 'gerege', 'T149-TIE-P9-raw.json')
ATT = os.path.join(HERE, 'out', 'gerege', 'attestation.json')

# HARDENED BY T206 (22 August 2026) - P-22, P-48 rule 4.  This is T203's SEVENTH
# writer of the live golden-vector store, uninspected by T196, T198 and T203
# itself (T203's own handoff names it explicitly as out-of-scope backlog: "a
# seventh promote-shaped writer, not inspected").  Unlike the six T203 already
# guarded, this one takes its OUTPUT PATH as `sys.argv[1]` rather than binding
# it to a module constant derived from `__file__` -- the docstring above shows
# both a /tmp destination and THE LIVE STORE PATH as equally valid invocations.
# MEASURED, NOT ASSERTED (T206-evidence/RED-a-*.txt): the pre-fix `with
# open(out_path, 'w') as fh: json.dump(...)` destroys whatever pre-existing
# file occupies argv[1], unconditionally, exit 0 -- a bare O_TRUNC exactly like
# T74/T61/T64/T57/T8, differing only in where the destination is bound. A live
# vector already occupies this script's own documented default name
# (T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json), so this is not a
# hypothetical: T206 also measured that the LIVE file has been hand-edited
# since promotion (T153's review added caveat prose the script's own hardcoded
# NOTE/KILL_EV strings do not contain), so a re-run would not just risk
# truncation -- it would silently REGRESS the vector's content.
#
# THIS REUSES T203's SHARED MODULE VERBATIM -- `t203_store_guard.py`, T178's
# shape transposed to a create-only store writer -- and introduces no second
# guard idiom. This script sits at `.softhouse/capture/pathb/t149`, a
# DIFFERENT depth from `.softhouse/handoff`, so the shared module is reached
# exactly as T64-promote-vectors.py reaches it: four dirnames up from
# `__file__` lands on `.softhouse`, then `handoff`. The resolved directory
# goes at the FRONT of sys.path so the module cannot be shadowed from the cwd
# or the environment; a missing module fails CLOSED.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "handoff"))
import t203_store_guard as guard_store  # noqa: E402

NAME = 'T149-promote-vector'

# Argv-only authorisation phrase - never an environment variable, for the
# reason recorded in the guard module. Authorises CREATING a new vector in the
# live store only; it does NOT authorise overwriting an existing one, and
# nothing does. `main(sys.argv[1])` below reads only the first positional
# argument, so this token can be passed as a second/third argv word without
# changing what the script treats as its destination.
AUTHORISE_TOKEN = (
    'I-AM-PROMOTING-T149-PATHB-TIE-INTO-THE-LIVE-GOLDEN-VECTOR-STORE')

TITLE = (
    "THE PINNED HALF_UP EXACT TIE, GRADED. MNT 1,162,502.50 over 12 monthly repayments at "
    "21.6% p.a., disbursed 2026-01-01, so period-1 interest is exactly 1,162,502.50 x 0.018 = "
    "20,925.045 -- a half-minor-unit tie. The reference oracle answers 20925.05 under the "
    "ratified HALF_UP and 20925.04 under its own stock HALF_EVEN default, and BOTH ARMS ARE LIVE "
    "OBSERVATIONS of one JVM. FIRST parity vector in this store observed on the Path B server "
    "seam; the other 42 are all path_a_embeddable."
)

NOTE = (
    "WHAT THIS VECTOR DISCRIMINATES, AND WHAT IT DOES NOT. It kills a port that applies HALF_EVEN "
    "where the reference oracle applies the TENANT rounding mode at the currency quantization "
    "[Money.java:52] -- the counterfactual named MONEY-QUANTIZATION-HALF-EVEN. PROVED, NOT "
    "ASSERTED: with the port mutated to banker's rounding at that one site (named mutation M7 of "
    ".softhouse/handoff/T61-mutations.py) this vector goes RED, and with the mutation reverted it "
    "goes GREEN; transcripts in .softhouse/capture/pathb/t149/redgreen/. "
    "(1) IT IS THE FOURTH VECTOR IN THIS STORE TO KILL THAT COUNTERFACTUAL, NOT THE FIRST, and "
    "the task that commissioned it believed otherwise. The commissioning brief said '0 of 46 "
    "vectors carry either tie answer -- so nothing in the parity corpus would notice a port that "
    "inherited Fineract's stock HALF_EVEN default'. The first clause is true of the literal "
    "CHARACTERS 20925.05 and 20925.04; the inference is FALSE. T61-HE-A, T61-HE-B and T61-HE-C "
    "are ties at the same quantization on other principals and were already killing M7. MEASURED "
    "BEFORE THIS VECTOR EXISTED: M7 over the 42-vector store gives parity PASS 39 FAIL 3, the "
    "three being exactly T61-HE-A/B/C "
    "(.softhouse/capture/pathb/t149/redgreen/premise-refuted-42-vector-store.txt). Anyone reading "
    "this vector as the corpus's only defence against a HALF_EVEN port is reading it wrong. "
    "(2) WHAT IS ACTUALLY NEW HERE IS THE SEAM AND THE ABSENCE OF A MODEL. Every other parity "
    "vector in this store is path_a_embeddable -- an in-process seam with no server and no "
    "database. This is the first observed through the running Fineract server over REST against "
    "PostgreSQL, which is the seam a production deployment actually uses and the only seam that "
    "can ever grade a charge. And its counterfactual contains no model: both arms are "
    "observations of the reference oracle taken from ONE running JVM differing in exactly one "
    "input, the tenant's RoundingMode ordinal (gerege 4 = HALF_UP, default 6 = HALF_EVEN). "
    "TRANSCRIPTION AND PROVENANCE NOTES. (a) The capture is T149-TIE-P9, posted to loan product 9 "
    "('T22 probe p09-sarp-360-30'), whose m_product_loan row is days_in_month_enum 30 / "
    "days_in_year_enum 360 -- so day_count FIXED_30_360 is what the oracle ACTUALLY RAN, not a "
    "convenient transcription. Its response is BYTE-IDENTICAL (sha256 39f56dc2...) to the pinned "
    "canary request calc-pmode2-gerege.json (sha256 2a6621be...) posted to product 11, which is "
    "actual/actual: on this monthly same-as-repayment-period shape the day count moves nothing, "
    "and the identity is observed rather than argued. (b) DEC-1 pins "
    "interestCalculationPeriodMethod UNSET, and no Path B capture can ever satisfy that pin "
    "because the server always persists a value -- this request carries SAME_AS_REPAYMENT_PERIOD. "
    "T76 refused to promote any Path B capture partly for that reason and recorded the residual "
    "as [UNVERIFIED]. It is now CLOSED BY MEASUREMENT on this shape: the companion capture "
    "T149-CTRL-P9-1M2 (same product 9, principal MNT 1,200,000) agrees with the already-promoted "
    "Path A vector P-MNT-1M2 -- ICPM unset, same fixed 30/360 -- in every one of 12 rows across "
    "principal, interest, outstanding balance and row total, and in the total interest "
    "(14,498,847 minor units). With the day count controlled, ICPM is the only remaining "
    "difference and it moves nothing. See crosscheck-vs-patha.py. This closes T76's [UNVERIFIED] "
    "on THIS SHAPE ONLY; it licenses nothing about daily interest calculation, where the setting "
    "is live. (c) T76's other two objections to B-01 do not apply to this capture: B-01's product "
    "was actual/actual (outside the graded domain), and B-01 killed nothing the store did not "
    "already grade. (d) The Path B disbursement row carries NO fromDate field at all, so "
    "from_date is withdrawn in unrecorded_fields rather than filled from the due date -- filling "
    "it would be deriving a cell and storing it as an observation. installment_number and "
    "interest_minor are withdrawn on that row for the reason every other vector here withdraws "
    "them. (e) On Path B there is ONE MathContext: MoneyHelper's tenant-scoped context, so "
    "threaded and ambient are the same object. Both are recorded as (19, HALF_UP) and both were "
    "asserted by the capture gate BEFORE any body was fetched -- MoneyHelper.PRECISION read by "
    "javap from the DEPLOYED jar, the tenant's c_configuration.rounding-mode ordinal, THIS JVM "
    "run's own MoneyHelper init line, and the behavioural canary itself. (f) request.time_zone is "
    "Asia/Ulaanbaatar and is OBSERVED here rather than declared: tenants.timezone_id is asserted "
    "by precondition P9. It still grades nothing. (g) The capture spends no state on the oracle: "
    "POST /loans?command=calculateLoanSchedule persists nothing."
)

KILL_DESC = (
    "Applies HALF_EVEN where the reference oracle applies the TENANT's rounding mode at the "
    "currency quantization [Money.java:52, Money(currency, amount, mc) -> "
    "setScale(currency.getDecimalPlaces(), mc.getRoundingMode())]. HALF_EVEN is the reference "
    "oracle's OWN STOCK CONFIGURATION DEFAULT, which is why CLAUDE.md requires HALF_UP to be "
    "pinned explicitly per tenant and never inherited. A port that reads the default instead of "
    "the tenant pin, or that reaches for a language's banker's-rounding primitive because it is "
    "the one the standard library offers, lands exactly here."
)

KILL_EV = (
    "BOTH ARMS OBSERVED LIVE; THERE IS NO MODEL IN THIS MARGIN. One running JVM, one request "
    "shape, two tenants differing in exactly one input -- the RoundingMode ordinal in "
    "c_configuration (gerege 4 = HALF_UP, default 6 = HALF_EVEN). The two loan-product rows were "
    "re-verified column by column for this vector: to_jsonb(m_product_loan) id 10 @ "
    "fineract_default against id 11 @ fineract_gerege, 89 columns compared, 1 differing, and the "
    "differing column is `id` (compare-arms.py, re-establishing T136's finding independently). "
    "OBSERVED: period-1 interest 20925.05 under HALF_UP; the HALF_EVEN arm emits 20925.04 "
    "instead. The tie is exact -- 1,162,502.50 x 0.018 = 20,925.045 -- because on this lattice "
    "the period-1 rate factor is exactly 0.018 and 116,250,250 minor units is 250 mod 500. "
    "MARGIN: 20 money cells diverge across the schedule and every one of them by exactly 1 minor "
    "unit, so the widest single-cell disagreement is 1. It propagates: the outstanding-principal "
    "column is 1 minor unit apart on all 12 rows, period 12's principal and row total are 1 "
    "apart, and total interest is 140457.89 against 140457.88. Full cell listing: "
    ".softhouse/capture/pathb/t149/redgreen/arms-diff.txt. CONFIRMED AGAINST THE PORT ON THIS "
    "EXACT REQUEST: named mutation M7 (.softhouse/handoff/T61-mutations.py) takes this vector RED "
    "and reverting it takes it GREEN. NOT NEW COVERAGE: T61-HE-A, T61-HE-B and T61-HE-C already "
    "kill this same counterfactual, measured, on the 42-vector store that predates this file."
)

PROV_NOTE = (
    "TRANSCRIBED, never computed, from the Path B capture case T149-TIE-P9 taken by "
    ".softhouse/capture/pathb/t36/attest.py (capture set 't149') on tenant gerege. Every expect "
    "cell is a value literally present in the referenced raw response; the only transformation is "
    "exact textual major->minor scaling, and the oracle's own emitted characters are carried "
    "alongside in the *_major_text cross-check fields so the scaling is mechanically "
    "re-checkable. Attestation sidecar: .softhouse/capture/pathb/t149/out/gerege/attestation.json. "
    "Promotion script: .softhouse/capture/pathb/t149/promote-vector.py (task T149)."
)


def minor(text, digits=2):
    """Exact major-unit decimal TEXT -> integer minor-unit string. Never float."""
    t = str(text)
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    whole, _, frac = t.partition('.')
    if len(frac) > digits:
        if frac[digits:].strip('0'):
            raise ValueError('significant digit beyond the currency scale: %r' % text)
        frac = frac[:digits]
    frac = frac.ljust(digits, '0')
    v = ((whole or '0') + frac).lstrip('0') or '0'
    return ('-' + v) if neg and v != '0' else v


def civil(a):
    return {'year': a[0], 'month': a[1], 'day': a[2]}


def main(out_path):
    with open(RAW) as fh:
        j = json.load(fh, parse_float=str)
    with open(ATT) as fh:
        att = json.load(fh, parse_float=str)
    cap = next(c for c in att['captures'] if c['id'] == 'T149-TIE-P9')

    assert j['currency']['code'] == 'MNT' and j['currency']['decimalPlaces'] == 2
    assert att['effective_math_context']['matches_ratified_production_setting'] is True
    assert att['tenant']['timezone_id'] == 'Asia/Ulaanbaatar'
    assert att['effective_mode_canary']['observed_period1_interest'] == '20925.05'

    periods = []
    for p in j['periods']:
        if 'period' not in p:                                   # the DISBURSEMENT row
            periods.append({
                'kind': 'DISBURSEMENT',
                'installment_number': 0,
                # Path B's disbursement row carries NO fromDate at all. Withdrawn rather
                # than filled from the due date: filling it would be deriving a cell and
                # storing it as an observation.
                'from_date': {'year': 0, 'month': 0, 'day': 0},
                'due_date': civil(p['dueDate']),
                'principal_minor': minor(p['principalDisbursed']),
                'principal_major_text': str(p['principalDisbursed']),
                'interest_minor': '',
                'interest_major_text': '',
                'outstanding_principal_minor': minor(p['principalLoanBalanceOutstanding']),
                'outstanding_principal_major_text': str(p['principalLoanBalanceOutstanding']),
                'unrecorded_fields': ['installment_number', 'from_date', 'interest_minor'],
                'observed_total_due_minor': None,
            })
            continue
        periods.append({
            'kind': 'REPAYMENT',
            'installment_number': p['period'],
            'from_date': civil(p['fromDate']),
            'due_date': civil(p['dueDate']),
            'principal_minor': minor(p['principalOriginalDue']),
            'principal_major_text': str(p['principalOriginalDue']),
            'interest_minor': minor(p['interestOriginalDue']),
            'interest_major_text': str(p['interestOriginalDue']),
            'outstanding_principal_minor': minor(p['principalLoanBalanceOutstanding']),
            'outstanding_principal_major_text': str(p['principalLoanBalanceOutstanding']),
            'unrecorded_fields': [],
            'observed_total_due_minor': minor(p['totalOriginalDueForPeriod']),
        })

    v = {
        'schema': 'gerege.loanschedule.vector/v1',
        'case_id': 'T149-PATHB-TIE',
        'context': 'loanschedule',
        'class': 'parity',
        'title': TITLE,
        'dec1_revision': 12,
        '_note': NOTE,
        'capabilities_required': ['schedule.core'],
        'graded_against': [{
            'id': 'MONEY-QUANTIZATION-HALF-EVEN',
            'capability': 'schedule.core',
            'description': KILL_DESC,
            'margin_minor': '1',
            'evidence': KILL_EV,
        }],
        'retires_when_capability_graded': '',
        'provenance': {
            'kind': 'oracle-capture',
            'note': PROV_NOTE,
            'capture_ref': '.softhouse/capture/pathb/t149/out/gerege/T149-TIE-P9-raw.json',
            'capture_sha256': cap['response_sha256'],
            'capture_case_id': 'T149-TIE-P9',
            'citation': '',
        },
        'oracle': {
            'fineract_commit': att['oracle']['jar_git_commit_id'],
            'seam': 'path_b_server',
            'captured_at': cap['captured_at_utc'],
            'threaded_mathcontext': {'precision': 19, 'rounding_mode': 'HALF_UP'},
            'ambient_mathcontext': {'precision': 19, 'rounding_mode': 'HALF_UP'},
        },
        'request': {
            'time_zone': 'Asia/Ulaanbaatar',
            'currency': {'code': 'MNT', 'minor_unit_digits': 2},
            'rounding': {'significant_digits': 19, 'rate_factor_scale': 19, 'mode': 'HALF_UP'},
            'schedule_start_date': {'year': 2026, 'month': 1, 'day': 1},
            'disbursements': [{'date': {'year': 2026, 'month': 1, 'day': 1},
                               'amount_minor': '116250250'}],
            'number_of_repayments': 12,
            'repayment_every': 1,
            'repayment_frequency_unit': 'MONTHS',
            'annual_nominal_interest_rate': {'numerator': 27, 'denominator': 125},
            'interest_method': 'DECLINING_BALANCE',
            'day_count': 'FIXED_30_360',
            'down_payment_percentage': {'numerator': 0, 'denominator': 1},
            'installment_rounding_multiple_minor': '0',
        },
        'expect': {
            'kind': 'schedule',
            'sentinel': '',
            'last_repayment_due_date': None,
            'observed_total_interest_minor': minor(j['totalInterestCharged']),
            'periods': periods,
        },
        'invariant_exemptions': [],
    }
    # `json.dumps(v, indent=2) + '\n'` is byte-for-byte what `json.dump(v, fh,
    # indent=2)` followed by `fh.write('\n')` produced -- T206 proved the
    # emitted bytes unchanged by promoting into an empty scratch store and
    # diffing byte-for-byte against a control run of the pre-fix code path.
    store_dir = os.path.dirname(out_path) or '.'
    filename = os.path.basename(out_path)
    out_path = guard_store.write_vector(
        NAME, AUTHORISE_TOKEN, store_dir, filename,
        json.dumps(v, indent=2) + '\n')
    print('wrote %s (%d periods)' % (out_path, len(periods)))
    print('  case_id %s   seam %s   capture sha256 %s'
          % (v['case_id'], v['oracle']['seam'], v['provenance']['capture_sha256'][:16]))


if __name__ == '__main__':
    main(sys.argv[1])
