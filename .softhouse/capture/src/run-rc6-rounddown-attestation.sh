#!/bin/sh
# T35 / T27 review item RC-6, attestation half.
#
# "an attestation confirming the round-down probe ran at (19, HALF_UP); the conclusion is mode-robust,
#  the *record* is not attested."  [T27 §7 item 10, T30 parked table]
#
# Run from the repo root:  sh .softhouse/capture/src/run-rc6-rounddown-attestation.sh
#
# READ-ONLY WITH RESPECT TO THE RUNNING SERVER. It performs (a) GETs, and (b) one
# POST /loans?command=calculateLoanSchedule, which is a schedule PREVIEW: it creates no loan, no
# client and no product, and it writes nothing to PostgreSQL. It does not start, stop, restart or
# reconfigure any container.
#
# It FAILS THE RUN on: the oracle being unreachable, tenant `gerege` not being HALF_UP (ordinal 4),
# a non-200 status, an error body written where a capture was expected, or the re-run disagreeing
# with the committed observation by a single minor unit.
#
# No glob appears in any output path (the T22 P0-5 defect class). Every filename is literal.
set -eu

BASE="${FINERACT_BASE:-https://localhost:8443/fineract-provider/api/v1}"
AUTH="${FINERACT_AUTH:-mifos:password}"
TENANT="gerege"
REQ=".softhouse/capture/pathb/t22-audit/req/calc-prounddown.json"     # read-only input
COMMITTED=".softhouse/capture/pathb/t22-audit/out-rounddown/rounddown-gerege-raw.json"  # read-only input
OUT_DIR="${CAP_OUT_DIR:-.softhouse/capture/out}"
CFG="$OUT_DIR/t35-rc6-gerege-configurations.json"
RERUN="$OUT_DIR/t35-rc6-rounddown-gerege-rerun.json"
LOGL="$OUT_DIR/t35-rc6-server-moneyhelper-log.txt"
ATT="$OUT_DIR/t35-rc6-rounddown-attestation.json"
SUMS="$OUT_DIR/t35-rc6-sha256.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

[ -f "$REQ" ] || fail "run me from the repo root; $REQ not found from $(pwd)"
[ -f "$COMMITTED" ] || fail "committed round-down observation not found at $COMMITTED"
mkdir -p "$OUT_DIR"

# --- 1. the oracle is up ---------------------------------------------------------------------------
HEALTH=$(curl -sk -u "$AUTH" -o /dev/null -w '%{http_code}' \
  "https://localhost:8443/fineract-provider/actuator/health") || fail "health probe failed"
[ "$HEALTH" = "200" ] || fail "reference oracle health returned HTTP $HEALTH"

# --- 2. the tenant's rounding mode, from the tenant's own configuration -----------------------------
CODE=$(curl -sk -u "$AUTH" -H "Fineract-Platform-TenantId: $TENANT" \
  -o "$CFG" -w '%{http_code}' "$BASE/configurations")
[ "$CODE" = "200" ] || { printf 'FAILED: GET /configurations returned HTTP %s. The file at %s is an ERROR BODY, not a capture.\n' "$CODE" "$CFG" >&2; exit 1; }

# --- 3. the oracle's OWN startup log line for this tenant -------------------------------------------
docker logs fineract-fineract-1 2>&1 | grep 'MoneyHelper' > "$LOGL" || true
[ -s "$LOGL" ] || fail "no MoneyHelper lines in the server log — cannot attest the mode from the oracle's own record"

# --- 4. re-run the probe (schedule PREVIEW; writes nothing) -----------------------------------------
CODE=$(curl -sk -u "$AUTH" -H "Fineract-Platform-TenantId: $TENANT" -H "Content-Type: application/json" \
  -X POST -d @"$REQ" -o "$RERUN" -w '%{http_code}' "$BASE/loans?command=calculateLoanSchedule")
[ "$CODE" = "200" ] || { printf 'FAILED: calculateLoanSchedule returned HTTP %s. The file at %s is an ERROR BODY, not a capture. Do not commit it and do not treat it as an observation.\n' "$CODE" "$RERUN" >&2; exit 1; }

# --- 5/6. compare, integer minor units, no tolerance; then write the attestation ---------------------
python3 - "$CFG" "$RERUN" "$COMMITTED" "$LOGL" "$ATT" "$TENANT" <<'PY'
import hashlib, json, subprocess, sys
from decimal import Decimal

cfgp, rerunp, commp, logp, attp, tenant = sys.argv[1:7]

cfg = json.load(open(cfgp, encoding='utf-8'))
rows = cfg.get('globalConfiguration', cfg if isinstance(cfg, list) else [])
rm = next((r for r in rows if r.get('name') == 'rounding-mode'), None)
if rm is None:
    sys.exit("FAILED: no 'rounding-mode' entry in the %s tenant configuration" % tenant)
if int(rm['value']) != 4:
    sys.exit("FAILED: tenant %s rounding-mode is %s, not 4 (HALF_UP). The round-down probe CANNOT be "
             "attested at (19, HALF_UP)." % (tenant, rm['value']))

logtext = open(logp, encoding='utf-8').read()
gerege_lines = [l for l in logtext.splitlines() if ('`%s`' % tenant) in l]
if not gerege_lines:
    sys.exit("FAILED: the server log carries no MoneyHelper initialisation line for tenant %s" % tenant)
if not all('HALF_UP' in l for l in gerege_lines):
    sys.exit("FAILED: a MoneyHelper line for tenant %s is not HALF_UP: %r" % (tenant, gerege_lines))

def minor(v, dp=2):
    if v is None:
        return None
    d = Decimal(str(v))
    s = d * (10 ** dp)
    if s != s.to_integral_value():
        raise ValueError("value %r is finer than %d minor units" % (v, dp))
    return int(s)

new = json.load(open(rerunp, encoding='utf-8'), parse_float=Decimal)
old = json.load(open(commp, encoding='utf-8'), parse_float=Decimal)
if 'periods' not in new:
    sys.exit("FAILED: re-run body has no 'periods' — it is not a schedule: %s" % str(new)[:300])

KEYS = ('period', 'principalDue', 'interestDue', 'feeChargesDue', 'penaltyChargesDue',
        'totalDueForPeriod', 'principalLoanBalanceOutstanding', 'totalOutstandingForPeriod')
diffs = []
if len(new['periods']) != len(old['periods']):
    diffs.append("period count %d vs %d" % (len(new['periods']), len(old['periods'])))
else:
    for i, (a, b) in enumerate(zip(old['periods'], new['periods'])):
        for k in KEYS:
            if k in a or k in b:
                av, bv = a.get(k), b.get(k)
                if k == 'period':
                    if av != bv:
                        diffs.append("periods[%d].%s %r vs %r" % (i, k, av, bv))
                elif minor(av) != minor(bv):
                    diffs.append("periods[%d].%s %r vs %r" % (i, k, av, bv))
        if a.get('dueDate') != b.get('dueDate'):
            diffs.append("periods[%d].dueDate %r vs %r" % (i, a.get('dueDate'), b.get('dueDate')))
for k in ('totalInterestCharged', 'totalRepaymentExpected', 'totalPrincipalDisbursed', 'loanTermInDays'):
    if k == 'loanTermInDays':
        if old.get(k) != new.get(k):
            diffs.append("%s %r vs %r" % (k, old.get(k), new.get(k)))
    elif minor(old.get(k)) != minor(new.get(k)):
        diffs.append("%s %r vs %r" % (k, old.get(k), new.get(k)))

if diffs:
    sys.exit("FINDING — the re-run DISAGREES with the committed round-down observation. This is not "
             "something to reconcile:\n  " + "\n  ".join(diffs))

emis = sorted({minor(p['totalDueForPeriod']) for p in new['periods'][1:-1]})
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

att = {
    "artifact": "RC-6 attestation — Path B round-down probe, tenant `%s`" % tenant,
    "closes": "T27 review RC-6, attestation half (T27 §7 item 10)",
    "whatWasUnattested": "PATHB-REPORT.md attributed the round-down probe to (19, HALF_UP) on the strength "
                         "of the filename and prose. No attestation existed.",
    "attestedNow": {
        "precision": 19,
        "precisionSource": "MoneyHelper.PRECISION is a compile-time constant [fineract-core/.../MoneyHelper.java:35]; "
                           "getMathContext() = new MathContext(PRECISION, getRoundingMode()) [:91-93]. "
                           "It is not tenant-configurable, so no runtime reading can contradict it.",
        "roundingMode": "HALF_UP",
        "roundingModeOrdinal": 4,
        "roundingModeSources": [
            "the tenant's own global configuration `rounding-mode` = %s, read live from GET /configurations "
            "under Fineract-Platform-TenantId: %s" % (rm['value'], tenant),
            "the reference oracle's OWN startup log lines for tenant `%s`, all HALF_UP" % tenant,
            "MoneyHelperInitializationService.getRoundingModeFromConfiguration() reads exactly this key "
            "[fineract-core/.../MoneyHelperInitializationService.java:102-106], and "
            "GlobalConfigurationConstants.ROUNDING_MODE = \"rounding-mode\" [.../api/GlobalConfigurationConstants.java:41]",
            "MoneyHelper.updateTenantRoundingMode has NO production caller in the pinned checkout (only its "
            "declaration at MoneyHelper.java:104 and test callers), so the cached per-tenant mode cannot have "
            "drifted from the startup value without a restart",
        ],
        "serverMoneyHelperLogLinesForTenant": gerege_lines,
        "otherTenantsForContrast": [l for l in logtext.splitlines()
                                    if 'Initialized rounding mode' in l and ('`%s`' % tenant) not in l],
    },
    "reRunOfTheProbe": {
        "method": "POST /loans?command=calculateLoanSchedule (schedule PREVIEW — creates nothing, writes nothing)",
        "request": "committed, unmodified: .softhouse/capture/pathb/t22-audit/req/calc-prounddown.json",
        "requestSha256": sha('.softhouse/capture/pathb/t22-audit/req/calc-prounddown.json'),
        "committedObservation": ".softhouse/capture/pathb/t22-audit/out-rounddown/rounddown-gerege-raw.json",
        "committedObservationSha256": sha(commp),
        "reRunOutput": rerunp,
        "reRunOutputSha256": sha(rerunp),
        "verdict": "AGREES with the committed observation to the minor unit on every period column and "
                   "every plan total. Compared as integer minor units with NO tolerance.",
        "distinctInstallmentTotalsPeriods1to11_minorUnits": emis,
        "observedEmiPeriods1to11": str(new['periods'][1]['totalDueForPeriod']),
    },
    "whatThisDoesAndDoesNotEstablish": {
        "does": "The round-down probe's environment is now attested: tenant `%s` runs at (19, HALF_UP), "
                "RoundingMode ordinal 4, and the probe reproduces on that attested environment today." % tenant,
        "doesNot": "It does not promote anything. It does not retroactively attest the ORIGINAL run's "
                   "environment — it attests THIS run's, and shows the observation is unchanged. The "
                   "round-down conclusion was already known to be mode-robust (at 111,148.35 the nearest "
                   "multiple of 100 is 111,100 under HALF_UP and HALF_EVEN alike), so nothing about the "
                   "conclusion turns on this; the RECORD is what was missing.",
        "pathBP0sStillOpen": ["T22 P0-3 attestation sidecar for the four B-0n captures",
                              "T22 P0-4 fail-the-run preconditions in REPRODUCE.md",
                              "T22 P0-6 re-point the four captures at a production-settings tenant"],
    },
}
open(attp, 'w', encoding='utf-8').write(json.dumps(att, indent=2, ensure_ascii=False, default=str) + "\n")
print("RC-6 attestation OK — tenant %s rounding-mode=%s (HALF_UP, ordinal 4), precision 19;" % (tenant, rm['value']))
print("re-run AGREES with the committed observation to the minor unit; EMI periods 1-11 = %s"
      % new['periods'][1]['totalDueForPeriod'])
PY

: > "$SUMS"
for f in "$CFG" "$RERUN" "$LOGL" "$ATT"; do
  [ -f "$f" ] && shasum -a 256 "$f" >> "$SUMS"
done
cat "$SUMS"
printf 'DONE. Nothing promoted; no Path B file was written.\n'
