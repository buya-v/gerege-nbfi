#!/usr/bin/env python3
"""T391 -- decode the three accrual journal transactions from a captured or
re-issued GET /journalentries body, KEEPING THE AMOUNT AS THE ORACLE'S OWN
CHARACTERS.

WHY parse_float=str AND parse_int=str. `json.load` with its defaults turns the
oracle's `24000.000000` into a Python float and prints it back as `24000.0`.
That is a DIFFERENT STRING from the one on the wire, and a vector transcribed
from it would be transcribed from this script's rounding rather than from the
oracle. Money never becomes a number in this program; here it never even
becomes a float for display.

Usage: 10-decode-legs.py <body.json> ...
"""
import json
import sys

for path in sys.argv[1:]:
    with open(path, "rb") as fh:
        doc = json.load(fh, parse_float=str, parse_int=str)
    print("=" * 78)
    print(path)
    print("totalFilteredRecords =", doc["totalFilteredRecords"])
    for it in doc["pageItems"]:
        det = it.get("transactionDetails") or {}
        tt = (det.get("transactionType") or {})
        print(
            "  je={id} txn={txn} gl={gl} code={code} name={name} acctype={at}"
            " side={side} amount={amt} date={date} manual={man} reversed={rev}"
            " entity={et}/{eid} loan_txn={lt} loan_txn_type={ltt}/{lttv}".format(
                id=it["id"],
                txn=it["transactionId"],
                gl=it["glAccountId"],
                code=it["glAccountCode"],
                name=it["glAccountName"],
                at=it["glAccountType"]["value"],
                side=it["entryType"]["value"],
                amt=it["amount"],
                date=it["transactionDate"],
                man=it["manualEntry"],
                rev=it["reversed"],
                et=it["entityType"]["value"],
                eid=it["entityId"],
                lt=det.get("transactionId"),
                ltt=tt.get("id"),
                lttv=tt.get("value"),
            )
        )
