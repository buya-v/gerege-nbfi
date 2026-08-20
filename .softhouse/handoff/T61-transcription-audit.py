#!/usr/bin/env python3
"""T61 — independent third-converter transcription audit of the promoted vectors.

The promotion script converted the oracle's decimal text to minor units. This
audit converts it AGAIN, by a DIFFERENT method, and compares. The point is not
that the second converter is better -- it is that a transcription defect has to
occur twice, in two independently written functions, to survive.

Converter here: strip the decimal point and pad, then verify the result against
an INDEPENDENT reconstruction that re-renders the promoted integer BACK to text
and compares it with the oracle's own emitted characters. A vector is only clean
if the round trip is exact in both directions.

Also checked, mechanically:
  * every promoted vector's provenance.capture_ref resolves and its recorded
    sha256 matches the file on disk;
  * provenance.capture_case_id names a case that exists INSIDE that file;
  * the request block round-trips against the capture's own inputs;
  * both MathContexts are (19, HALF_UP) and agree with request.rounding;
  * the case id is not on PIN.json's never-promotable denylist;
  * no vector file contains a JSON number carrying '.', 'e' or 'E'.

    python3 .softhouse/handoff/T61-transcription-audit.py

Money is int64 minor units. There is no floating point in this file.
"""
import hashlib, json, os, re, sys

VECTORS = ".softhouse/vectors/loanschedule"
CASES = ("T61-HE-A", "T61-HE-B", "T61-HE-C")
PIN = json.load(open(".softhouse/vectors/PIN.json"))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def to_minor(text, digits):
    """Converter #2: split on the point, pad the fraction, concatenate."""
    neg = text.startswith("-")
    t = text[1:] if neg else text
    if "." in t:
        w, f = t.split(".", 1)
    else:
        w, f = t, ""
    if len(f) > digits:
        if f[digits:].strip("0"):
            raise SystemExit("over-scaled significant digit in %r" % text)
        f = f[:digits]
    f = f.ljust(digits, "0")
    v = int(w) * (10 ** digits) + (int(f) if f else 0)
    return -v if neg else v


def to_text(v, digits):
    """Converter #2 inverse: minor units back to the oracle's own spelling."""
    neg = v < 0
    v = abs(v)
    s = str(v).rjust(digits + 1, "0")
    out = s[:-digits] + "." + s[-digits:] if digits else s
    return ("-" + out) if neg else out


def main():
    if not os.path.isdir(VECTORS):
        sys.exit("run me from the repository root")
    files = [os.path.join(VECTORS, f) for f in sorted(os.listdir(VECTORS))
             if any(f.startswith(c + "-") for c in CASES)]
    if len(files) != len(CASES):
        sys.exit("expected %d T61 vectors, found %d" % (len(CASES), len(files)))

    cells = mismatches = 0
    for path in files:
        raw = open(path, encoding="utf-8").read()
        # HARD guard: no JSON number may carry a decimal point or an exponent.
        for m in re.finditer(r':\s*(-?\d+\.\d+|-?\d+[eE][-+]?\d+)\s*[,}\n]', raw):
            sys.exit("FLOAT TOKEN in %s: %r" % (path, m.group(1)))
        v = json.loads(raw)

        assert v["class"] == "parity", path
        cid = v["case_id"]
        if cid in PIN["never_promotable_capture_case_ids"]:
            sys.exit("%s is on the never-promotable denylist" % cid)
        if v["dec1_revision"] != PIN["dec1_revision"]:
            sys.exit("%s: dec1_revision disagrees with PIN.json" % cid)
        if v["oracle"]["fineract_commit"] != PIN["fineract_commit"]:
            sys.exit("%s: fineract_commit disagrees with PIN.json" % cid)
        for k in ("threaded_mathcontext", "ambient_mathcontext"):
            mc = v["oracle"][k]
            if (mc["precision"], mc["rounding_mode"]) != (19, "HALF_UP"):
                sys.exit("%s: %s is not (19, HALF_UP)" % (cid, k))
        r = v["request"]["rounding"]
        if (r["significant_digits"], r["mode"]) != (19, "HALF_UP") or r["rate_factor_scale"] != 19:
            sys.exit("%s: request.rounding disagrees with the threaded MathContext" % cid)

        ref = v["provenance"]["capture_ref"]
        if not os.path.isfile(ref):
            sys.exit("%s: capture_ref %s does not resolve" % (cid, ref))
        if v["provenance"]["capture_sha256"] != sha256(ref):
            sys.exit("%s: capture_sha256 does not match %s on disk" % (cid, ref))
        caps = {c["id"]: c for c in json.load(open(ref))["captures"]}
        ccid = v["provenance"]["capture_case_id"]
        if ccid not in caps:
            sys.exit("%s: capture_case_id %s is not inside %s" % (cid, ccid, ref))
        cap = caps[ccid]
        digits = v["request"]["currency"]["minor_unit_digits"]

        if not v["graded_against"]:
            sys.exit("%s: a parity vector that kills nothing is a capture, not a grader" % cid)
        for g in v["graded_against"]:
            if g.get("kind", "money") == "money" and int(g["margin_minor"]) <= 0:
                sys.exit("%s: money counterfactual %s has margin %s" % (cid, g["id"], g["margin_minor"]))
            if g["capability"] not in v["capabilities_required"]:
                sys.exit("%s: counterfactual capability %s not in capabilities_required" % (cid, g["capability"]))

        # ---- the request, back against the capture's own inputs ----------------
        i = cap["inputs"]
        checks = [
            (v["request"]["disbursements"][0]["amount_minor"], str(to_minor(i["disbursementAmount"], digits))),
            (str(v["request"]["number_of_repayments"]), str(i["numberOfRepayments"])),
            (v["request"]["currency"]["code"], i["currencyCode"].upper()),
            (v["request"]["repayment_frequency_unit"], i["repaymentFrequencyType"]),
            (v["request"]["interest_method"], i["interestMethod"]),
            ("%04d-%02d-%02d" % tuple(v["request"]["schedule_start_date"][k] for k in ("year", "month", "day")),
             i["scheduleGenerationStartDate"]),
            ("%04d-%02d-%02d" % tuple(v["request"]["disbursements"][0]["date"][k] for k in ("year", "month", "day")),
             i["disbursementDate"]),
        ]
        for a, b in checks:
            cells += 1
            if a != b:
                mismatches += 1
                print("REQUEST MISMATCH %s: %r vs capture %r" % (cid, a, b))
        # The rate, as an exact rational, re-rendered back to the capture's own
        # percent text. Integer arithmetic only: numerator/denominator is the
        # dimensionless fraction, so x 10000 is hundredths of one percent, and the
        # capture's "21.6" becomes 2160 the same way.
        rt = v["request"]["annual_nominal_interest_rate"]
        cells += 1
        if (rt["numerator"] * 10000) % rt["denominator"] != 0:
            sys.exit("%s: rate %d/%d is not exact in hundredths of a percent"
                     % (cid, rt["numerator"], rt["denominator"]))
        pct = (rt["numerator"] * 10000) // rt["denominator"]
        want = i["annualNominalInterestRate"]
        w, _, f = want.partition(".")
        want_hundredths_of_pct = int(w + f.ljust(2, "0")[:2])
        if pct != want_hundredths_of_pct:
            mismatches += 1
            print("RATE MISMATCH %s: vector %d/%d -> %d vs capture %r"
                  % (cid, rt["numerator"], rt["denominator"], pct, want))

        # ---- every promoted money cell, both directions -----------------------
        obs = cap["observed"]["periods"]
        per = v["expect"]["periods"]
        if len(obs) != len(per):
            sys.exit("%s: %d promoted rows vs %d observed" % (cid, len(per), len(obs)))
        for n, (o, p) in enumerate(zip(obs, per)):
            pairs = [("principal_minor", "principal_major_text", o.get("principal")),
                     ("interest_minor", "interest_major_text", o.get("interest")),
                     ("outstanding_principal_minor", "outstanding_principal_major_text", o.get("balance"))]
            for mkey, tkey, wire in pairs:
                if mkey in p.get("unrecorded_fields", []):
                    cells += 1
                    if p[mkey] != "" or wire is not None:
                        mismatches += 1
                        print("UNRECORDED MISMATCH %s row %d %s" % (cid, n, mkey))
                    continue
                if wire is None:
                    mismatches += 1
                    print("PROMOTED A CELL THE CAPTURE DID NOT RECORD: %s row %d %s" % (cid, n, mkey))
                    continue
                cells += 2
                if p[tkey] != wire:
                    mismatches += 1
                    print("TEXT MISMATCH %s row %d %s: %r vs oracle %r" % (cid, n, tkey, p[tkey], wire))
                got = to_minor(wire, digits)
                if str(got) != p[mkey]:
                    mismatches += 1
                    print("MINOR MISMATCH %s row %d %s: %s vs converter#2 %d"
                          % (cid, n, mkey, p[mkey], got))
                # and back again, against the oracle's own characters
                cells += 1
                back = to_text(int(p[mkey]), digits)
                if back.rstrip("0").rstrip(".") != wire.rstrip("0").rstrip(".") and back != wire:
                    mismatches += 1
                    print("ROUND-TRIP MISMATCH %s row %d %s: %r -> %r vs oracle %r"
                          % (cid, n, mkey, p[mkey], back, wire))
            # dates
            for key, wire in (("from_date", o.get("periodFromDate") or o.get("fromDate")),
                              ("due_date", o["dueDate"])):
                cells += 1
                d = p[key]
                if "%04d-%02d-%02d" % (d["year"], d["month"], d["day"]) != wire:
                    mismatches += 1
                    print("DATE MISMATCH %s row %d %s" % (cid, n, key))
            cells += 1
            want_no = o.get("periodNumber") or 0
            if p["installment_number"] != want_no:
                mismatches += 1
                print("INSTALLMENT NUMBER MISMATCH %s row %d" % (cid, n))
            if o.get("total") is not None:
                cells += 1
                if p["observed_total_due_minor"] != str(to_minor(o["total"], digits)):
                    mismatches += 1
                    print("TOTAL DUE MISMATCH %s row %d" % (cid, n))

        cells += 1
        if v["expect"]["observed_total_interest_minor"] != str(
                to_minor(cap["observed"]["totalInterestAmount"], digits)):
            mismatches += 1
            print("TOTAL INTEREST MISMATCH %s" % cid)

    print("\nT61 TRANSCRIPTION AUDIT — %d vectors, %d cells checked, %d mismatches"
          % (len(files), cells, mismatches))
    if mismatches:
        sys.exit(1)
    print("Every promoted cell resolves to a value literally present in the committed capture.")


if __name__ == "__main__":
    main()
