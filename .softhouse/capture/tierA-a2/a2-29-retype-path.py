#!/usr/bin/env python3
"""A2-29 -- print `/glaccounts/<resourceId>` for an OBSERVED create response.

cap8.sh takes the request path as an argument, and the id of an account this batch
created is only knowable at runtime. This does the one lookup and nothing else.

No float is ever constructed: the response is read with `parse_float=decimal.Decimal`
and `parse_constant` refusing NaN/Infinity, and only the integer `resourceId` is used.
A missing or non-integer resourceId is a REFUSAL, not a default.
"""
import decimal
import json
import sys


def _refuse_constant(tok):
    raise ValueError("REFUSING: JSON constant %r is a float ingress" % tok)


def main():
    if len(sys.argv) != 2:
        print("usage: a2-29-retype-path.py <create-response.json>", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], "rb") as fh:
        doc = json.loads(fh.read().decode("utf-8"), parse_float=decimal.Decimal,
                         parse_constant=_refuse_constant)
    if not isinstance(doc, dict) or "resourceId" not in doc:
        print("REFUSING: %s carries no resourceId." % sys.argv[1], file=sys.stderr)
        sys.exit(2)
    rid = doc["resourceId"]
    if not isinstance(rid, int) or isinstance(rid, bool) or rid <= 0:
        print("REFUSING: resourceId is %r, not a positive integer." % rid, file=sys.stderr)
        sys.exit(2)
    sys.stdout.write("/glaccounts/%d" % rid)


if __name__ == "__main__":
    main()
