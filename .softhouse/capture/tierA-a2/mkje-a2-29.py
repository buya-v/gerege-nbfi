#!/usr/bin/env python3
"""A2-29 -- emit a two-leg manual journal-entry request body with the two GL account ids
resolved from OBSERVED create responses.

WHY NOT resolve8.py.  resolve8.py splices a placeholder that is a TOP-LEVEL key
(`body.items()`, resolve8.py:165). The manual journal-entry body carries `glAccountId`
inside the `debits` / `credits` ARRAYS, so resolve8 refuses it. This script is the
narrowest thing that does the job and it keeps resolve8's two load-bearing properties:

  1. NO FLOAT IS EVER CONSTRUCTED, on the read side or the write side. The observed
     responses are read with `parse_float=decimal.Decimal` and `parse_constant` refusing
     NaN/Infinity, so `float` is never built; and only `resourceId`, an INTEGER, is ever
     taken out of them.
  2. The amount is written as an INTEGER MINOR-UNIT COUNT converted to its exact major-unit
     text by INTEGER arithmetic only (divmod by 100), never by division. MNT minor unit is
     2 (CLAUDE.md). No decimal literal is parsed, re-rendered, or round-tripped.

  3. WIRE-SAFETY, the defect T193's census caught in A2-26's `25000.30 -> 25000.3`: the
     emitted amount token is asserted to survive a binary-double round trip
     BYTE-IDENTICALLY, and the body is refused if it does not. A whole-tugrik amount is
     emitted as a bare integer (`1000000`), which has no float shape at all.

GUARD SHAPE (P-35): every check is a positive assertion with a printed count; a zero count
is a refusal, not a pass. Nothing is written until every check passes.

  python3 mkje-a2-29.py <debit-account-response.json> <credit-account-response.json> \
                        <transactionDate> <amount-minor-units> <comment> <out.json>
"""
import decimal
import json
import os
import sys


def _refuse_constant(tok):
    raise ValueError("REFUSING: JSON constant %r is a float ingress" % tok)


def observed_resource_id(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    doc = json.loads(raw.decode("utf-8"), parse_float=decimal.Decimal,
                     parse_constant=_refuse_constant)
    if not isinstance(doc, dict) or "resourceId" not in doc:
        print("REFUSING: %s carries no resourceId -- the create was not observed to "
              "succeed, so there is nothing to resolve." % path, file=sys.stderr)
        sys.exit(2)
    rid = doc["resourceId"]
    if not isinstance(rid, int) or isinstance(rid, bool) or rid <= 0:
        print("REFUSING: %s resourceId is %r, not a positive integer." % (path, rid),
              file=sys.stderr)
        sys.exit(2)
    return rid


def minor_to_major_text(minor, places):
    """Exact wire text for an integer minor-unit count. Integer arithmetic only.

    A whole major unit is emitted as a BARE INTEGER so the token has no float shape.
    """
    if not isinstance(minor, int) or isinstance(minor, bool):
        raise TypeError("minor units must be an int")
    sign = "-" if minor < 0 else ""
    whole, frac = divmod(abs(minor), 10 ** places)
    if frac == 0:
        return "%s%d" % (sign, whole)
    return "%s%d.%0*d" % (sign, whole, places, frac)


def survives_binary_double(tok):
    """True iff `tok` comes back byte-identical from a `json.load` -> `json.dumps` round
    trip with no parse_float.

    This mirrors `defect_render()` in .softhouse/capture/lib/check_wire_float_roundtrip.py
    exactly -- an integer-shaped token through json.dumps(int(...)), anything else through
    json.dumps(float(...)). It is asserted here, at the point the body is WRITTEN, so a
    body that would trip T193's census is never sent to the reference oracle at all.
    The float() below is a DELIBERATE simulation of the defect (P-25), never a value we use.
    """
    if any(c in tok for c in ".eE"):
        return json.dumps(float(tok)) == tok   # SIMULATE the defect. Deliberate float.
    return json.dumps(int(tok)) == tok


def defect_hint(tok):
    """What the round trip WOULD have emitted. Reporting only, never a value we send."""
    if any(c in tok for c in ".eE"):
        return json.dumps(float(tok))          # SIMULATE the defect. Deliberate float.
    return json.dumps(int(tok))


def main():
    if len(sys.argv) != 7:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    dr, cr, txn_date, minor_text, comment, out = sys.argv[1:]

    if not minor_text.lstrip("-").isdigit():
        print("REFUSING: amount must be given in INTEGER MINOR UNITS; got %r." % minor_text,
              file=sys.stderr)
        sys.exit(2)
    minor = int(minor_text)
    if minor <= 0:
        print("REFUSING: amount must be positive; got %d." % minor, file=sys.stderr)
        sys.exit(2)

    debit_id = observed_resource_id(dr)
    credit_id = observed_resource_id(cr)
    if debit_id == credit_id:
        print("REFUSING: both legs resolved to gl account %d -- that is not a two-leg "
              "entry." % debit_id, file=sys.stderr)
        sys.exit(2)
    print("  resolved debit glAccountId=%d (from %s)" % (debit_id, dr))
    print("  resolved credit glAccountId=%d (from %s)" % (credit_id, cr))

    amount = minor_to_major_text(minor, 2)
    # POSITIVE ASSERTION: the emitted text re-reads as the same integer minor-unit count,
    # via Decimal (never float).
    back = int((decimal.Decimal(amount) * 100).to_integral_exact())
    if back != minor:
        print("REFUSING: %s does not re-read as %d minor units." % (amount, minor),
              file=sys.stderr)
        sys.exit(2)
    print("  amount %d minor units -> wire text %s (re-reads as %d)" % (minor, amount, back))
    if not survives_binary_double(amount):
        print("REFUSING: wire token %s is ALTERED by a binary-double round trip (-> %s). "
              "That is the defect T193's census caught in A2-26's 25000.30; this body will "
              "not be sent." % (amount, defect_hint(amount)), file=sys.stderr)
        sys.exit(2)
    print("  wire token %s survives a binary-double round trip byte-identically" % amount)

    body = (
        '{\n'
        '  "officeId": 1,\n'
        '  "transactionDate": "%s",\n'
        '  "currencyCode": "MNT",\n'
        '  "comments": "%s",\n'
        '  "debits": [\n'
        '    {"glAccountId": %d, "amount": %s}\n'
        '  ],\n'
        '  "credits": [\n'
        '    {"glAccountId": %d, "amount": %s}\n'
        '  ],\n'
        '  "locale": "en",\n'
        '  "dateFormat": "dd MMMM yyyy"\n'
        '}\n'
    ) % (txn_date, comment, debit_id, amount, credit_id, amount)

    # POSITIVE ASSERTION: what we are about to write is valid JSON and its two amounts
    # still equal the integer minor-unit count we were given.
    doc = json.loads(body, parse_float=decimal.Decimal, parse_constant=_refuse_constant)
    legs = doc["debits"] + doc["credits"]
    if len(legs) != 2:
        print("REFUSING: emitted %d legs, expected 2." % len(legs), file=sys.stderr)
        sys.exit(2)
    checked = 0
    for leg in legs:
        # A whole-tugrik amount re-parses as `int`, a fractional one as `Decimal` (the
        # parse_float hook). Both are exact; neither is ever a float.
        got = leg["amount"]
        if not isinstance(got, (int, decimal.Decimal)) or isinstance(got, bool):
            print("REFUSING: a leg amount re-read as %s, which is not an exact numeric "
                  "type." % type(got).__name__, file=sys.stderr)
            sys.exit(2)
        if int(decimal.Decimal(got) * 100) != minor:
            print("REFUSING: a leg amount re-reads as something other than %d minor "
                  "units." % minor, file=sys.stderr)
            sys.exit(2)
        checked += 1
    if checked != 2:
        print("REFUSING: checked %d leg(s), not 2." % checked, file=sys.stderr)
        sys.exit(2)
    print("  re-parsed the emitted body; %d/2 legs equal %d minor units" % (checked, minor))

    tmp = out + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body.encode("utf-8"))
    os.replace(tmp, out)
    print("wrote %s (%d bytes)" % (out, len(body.encode("utf-8"))))


if __name__ == "__main__":
    main()
