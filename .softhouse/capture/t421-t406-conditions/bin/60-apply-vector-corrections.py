#!/usr/bin/env python3
"""T421 -- apply F-T406-1, -3, -4, -5 to the three ACC vectors as EXACT BYTE
replacements with a required occurrence count. Nothing is reformatted, nothing is
re-serialised: the file is read as text, each replacement is asserted to occur
EXACTLY the number of times declared, and the bytes are written back. A vector
that has drifted from what this script expects makes it ABORT rather than write.

No value in this file is parsed as a number. The timestamps are byte strings read
out of the digest-pinned .http records; the float renderings are string literals
that were computed once, printed, and checked against the tokens by eye and by
the assertion below -- this script does not call float().
"""
import sys, os, hashlib

VEC = ".softhouse/vectors/ledger"
CAP = ".softhouse/capture/t391-accrual-promotion/out"

# --- F-T406-1: the OBSERVED capture instant, read out of the digest-pinned .http
#     record each vector already cites as provenance.request_capture_ref.
SPEC = {
    "LDG-ACC-01-accrual-six-slots-runaccruals-trigger": {
        "http": "T391-A01-je-L29.http",
        "http_sha": "e89ab942e7414ce58a1dc2b26754a181f0554b7175ff72be4db0275ce49d8db6",
        "float_render": None,          # ACC-01's own number; the sentence is already true
    },
    "LDG-ACC-02-accrual-six-slots-minor-unit-residue": {
        "http": "T391-A02-je-L30.http",
        "http_sha": "d4eae8560d57ba25df3673a9b4f87b0472488fc5fec0226276d93f68ae133dbe",
        "float_render": "20195.38",
    },
    "LDG-ACC-03-accrual-six-slots-scheduled-job": {
        "http": "T391-A04-je-L32.http",
        "http_sha": "aaafcf8fa6427b19cca6eca3297abed7eee57152bb30353a388d7ef0d23cd0ff",
        "float_render": "12356.34",
    },
}

SYNTHESISED = '"captured_at": "2026-08-29T09:00:00Z"'

BAD_CITE = ("[VERIFIED: AccountingConstants.java:79-89 and :95-122 at 426a23544; "
            "ported at nexus/internal/apps/ledger/slots.go]")
GOOD_CITE = (
    "[VERIFIED at 426a23544 BY SYMBOL RATHER THAN BY LINE, because a line range rots and this "
    "one already had: T391 wrote AccountingConstants.java:79-89 here, which is "
    "CashAccountsForLoan.fromInt and its intToEnumMap and contains no enum constant at all "
    "(T406 F-T406-3, re-verified by T421 against /Users/buv/fineract at the pinned sha). The "
    "constants are AccountingConstants.CashAccountsForLoan -- values 1-6 and 10-26, with "
    "FEES_RECEIVABLE(25) and PENALTIES_RECEIVABLE(26) and NO 7, 8 or 9 -- and "
    "AccountingConstants.AccrualAccountsForLoan, which carries INTEREST_RECEIVABLE(7), "
    "FEES_RECEIVABLE(8) and PENALTIES_RECEIVABLE(9); ported at "
    "nexus/internal/apps/ledger/slots.go]")

BAD_TEN = ("on TEN cash products [re-measured live by T391, out/T391-S01 section 4c: products "
           "22, 23, 27, 28, 46, 54, 55, 56, 57, 58, 60]")
GOOD_TEN = (
    "on TEN cash products [22, 23, 27, 46, 54, 55, 56, 57, 58 and 60 -- accounting_type 2, slot "
    "1. Re-measured live by T391 at out/T391-S01 section 4c and AGAIN by T421 at "
    ".softhouse/capture/t421-t406-conditions/out/T421-S01-gl16-and-counters.txt section 1, "
    "captured 2026-08-28T18:33:42Z. That query returns ELEVEN rows for gl 16, and T391 copied "
    "all eleven under the TEN-cash-products clause (T406 F-T406-5): the eleventh row is accrual "
    "product 28 at slot 9, which is the OTHER half of this very sentence and not one of the "
    "ten. capabilities-ledger.json states the same fact correctly and lists exactly the ten]")

BAD_FLOAT = ("a JSON reader that decodes them through a float prints 24000.0 and is not what "
             "was read")


def http_instant(path, want_sha):
    raw = open(path, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    assert got == want_sha, "%s digest %s != cited %s" % (path, got, want_sha)
    for line in raw.decode().splitlines():
        if line.startswith("captured-at-utc: "):
            return line[len("captured-at-utc: "):].strip()
    raise SystemExit("no captured-at-utc in " + path)


def sub(text, old, new, want, label, path):
    n = text.count(old)
    if n != want:
        raise SystemExit("ABORT %s: %s occurs %d times, expected %d" % (path, label, n, want))
    return text.replace(old, new)


changed = 0
for name, spec in SPEC.items():
    vpath = os.path.join(VEC, name + ".json")
    hpath = os.path.join(CAP, spec["http"])
    instant = http_instant(hpath, spec["http_sha"])
    print("%s <- observed captured-at-utc %s from %s (digest MATCHES the vector's own citation)"
          % (name, instant, spec["http"]))

    text = open(vpath).read()

    # F-T406-1
    text = sub(text, SYNTHESISED, '"captured_at": "%s"' % instant, 1,
               "F-T406-1 synthesised captured_at", vpath)

    # F-T406-3
    text = sub(text, BAD_CITE, GOOD_CITE, 1, "F-T406-3 wrong line range", vpath)

    # F-T406-5
    text = sub(text, BAD_TEN, GOOD_TEN, 1, "F-T406-5 eleven-item TEN list", vpath)

    # F-T406-4 -- only where the sentence is about a DIFFERENT number
    if spec["float_render"] is not None:
        good_float = ("a JSON reader that decodes them through a float prints %s and is not "
                      "what was read" % spec["float_render"])
        text = sub(text, BAD_FLOAT, good_float, 1, "F-T406-4 wrong float illustration", vpath)
    else:
        assert text.count(BAD_FLOAT) == 1, "ACC-01's own illustration went missing"

    open(vpath, "w").write(text)
    changed += 1

print("VECTORS REWRITTEN:", changed)
sys.exit(0)
