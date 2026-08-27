#!/usr/bin/env python3
"""A2-26 corpus census over .softhouse/capture/tierA-a2/out/.

  python3 census-a2-26.py            -> full census to stdout

WHY THIS EXISTS
---------------
An earlier enumerator in this program walked out/**/* calling json.load inside
`except Exception: continue` and matched only dicts carrying both `glCode` and `name`.
It therefore SILENTLY SWALLOWED every psql .txt dump and every POST request body, and
reported the surviving subset as if it were the whole corpus. That number reached a gate
decision.  This census is written so that cannot happen:

  * EVERY file under out/ is accounted for exactly once -- classified, or listed in the
    SKIPPED section with a reason.  classified + skipped == total, asserted, and the
    script exits non-zero if it does not.
  * NOTHING is caught-and-continued.  A parse failure is recorded as a classification
    ("UNPARSEABLE-JSON") with the exception text, never dropped.
  * The .http / .status legs are classified as members of their observation, not ignored.

NO FLOATING POINT (P-25)
------------------------
Every money literal is parsed with json.loads(..., parse_float=decimal.Decimal), so the
scale of the literal on the wire is preserved exactly ("1200000.000000" stays 6dp) and no
binary double is ever constructed.  Sums are Decimal.  `float` appears nowhere.
"""
import decimal
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "out")

D = decimal.Decimal

# Keys whose values are money on the GL/loan surface. Used only for the generic
# money-cell scan; the journal-entry extractor below reads named fields, not this.
MONEY_KEY = re.compile(
    r"(?i)(^amount$|^.*[Aa]mount$|^principal|^interest|^fee|^penalty|^outstanding|"
    r"^totalOverpaid$|^inArrears|^approvedPrincipal$|^proposedPrincipal$|^netDisbursal)"
)


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8"), parse_float=D, parse_int=int)


def walk_money(node, path, sink):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, (D, int)) and not isinstance(v, bool) and MONEY_KEY.match(k):
                sink.append((p, v))
            else:
                walk_money(v, p, sink)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_money(v, f"{path}[{i}]", sink)


def main():
    files = []
    for root, dirnames, filenames in os.walk(OUT):
        dirnames.sort()
        for n in sorted(filenames):
            files.append(os.path.relpath(os.path.join(root, n), OUT))
    total = len(files)

    accounted = set()
    skipped = []          # (relpath, reason)
    obs = {}              # id -> record

    # --- pass 1: assemble observations from the .http/.json/.status triples ---
    for rel in files:
        if rel.endswith(".http"):
            oid = rel[: -len(".http")]
            obs.setdefault(oid, {"id": oid})["http"] = rel
            accounted.add(rel)
        elif rel.endswith(".status"):
            oid = rel[: -len(".status")]
            obs.setdefault(oid, {"id": oid})["status_file"] = rel
            accounted.add(rel)
        elif rel.endswith(".req") or rel.endswith(".req.sha256"):
            oid = rel.split(".req")[0]
            obs.setdefault(oid, {"id": oid}).setdefault("wire", []).append(rel)
            accounted.add(rel)
        elif rel.endswith(".json"):
            oid = rel[: -len(".json")]
            obs.setdefault(oid, {"id": oid})["json"] = rel
            accounted.add(rel)
        elif rel.endswith(".txt"):
            obs.setdefault(rel[: -len(".txt")], {"id": rel[: -len(".txt")]})["txt"] = rel
            accounted.add(rel)
        else:
            skipped.append((rel, "extension not one of .http/.json/.status/.req/.txt "
                                 "-- NOT a product of cap.sh or cap8.sh"))

    # --- pass 2: classify every observation ---
    for oid, r in sorted(obs.items()):
        if "txt" in r and "json" not in r:
            r["kind"] = "PSQL-DUMP"
            p = os.path.join(OUT, r["txt"])
            with open(p, "rb") as f:
                body = f.read().decode("utf-8", "replace")
            r["lines"] = body.count("\n")
            r["bytes"] = len(body)
            r["method"] = "psql"
            r["path"] = "(SQL dump, see sql/)"
            r["status"] = "n/a"
            continue

        r["kind"] = "HTTP-OBSERVATION"
        r["method"], r["path"] = "?", "?"
        if "http" in r:
            with open(os.path.join(OUT, r["http"])) as f:
                first = f.readline().strip()
            parts = first.split(" ", 1)
            r["method"] = parts[0]
            r["path"] = parts[1] if len(parts) > 1 else ""
            for line in open(os.path.join(OUT, r["http"])):
                if line.startswith("body-file:"):
                    r["body_file"] = line.split(":", 1)[1].strip()
        else:
            r["kind"] = "ORPHAN-NO-HTTP"
        if "status_file" in r:
            r["status"] = open(os.path.join(OUT, r["status_file"])).read().strip()
        else:
            r["status"] = "MISSING"

        if "json" not in r:
            r["kind"] = "ORPHAN-NO-BODY"
            continue

        try:
            r["doc"] = load(os.path.join(OUT, r["json"]))
            r["parse"] = "ok"
        except Exception as e:               # recorded, NEVER swallowed
            r["doc"] = None
            r["parse"] = f"UNPARSEABLE-JSON: {type(e).__name__}: {e}"

        # journal-entry observation?
        if r["path"].startswith("/journalentries"):
            r["je"] = True

    # --- pass 3: journal-entry detail ---
    for oid, r in sorted(obs.items()):
        if not r.get("je") or r.get("doc") is None:
            continue
        items = r["doc"].get("pageItems", []) if isinstance(r["doc"], dict) else []
        rows = []
        for it in items:
            rows.append({
                "id": it.get("id"),
                "txn": it.get("transactionId"),
                "entityType": (it.get("entityType") or {}).get("value"),
                "entityId": it.get("entityId"),
                "gl_id": it.get("glAccountId"),
                "gl_code": it.get("glAccountCode"),
                "gl_name": it.get("glAccountName"),
                "gl_type": (it.get("glAccountType") or {}).get("value"),
                "entry": (it.get("entryType") or {}).get("value"),
                "amount": it.get("amount"),
                "ccy": (it.get("currency") or {}).get("code"),
                "dp": (it.get("currency") or {}).get("decimalPlaces"),
                "reversed": it.get("reversed"),
                "txn_date": it.get("transactionDate"),
            })
        r["rows"] = rows
        r["total_filtered"] = r["doc"].get("totalFilteredRecords")

    # --- report ---
    print("=" * 100)
    print("A2-26 CORPUS CENSUS -- .softhouse/capture/tierA-a2/out/")
    print("=" * 100)
    print(f"files under out/ (recursive)      : {total}")
    print(f"files accounted for by a class    : {len(accounted)}")
    print(f"files SKIPPED (listed below)      : {len(skipped)}")
    kinds = {}
    for r in obs.values():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"observation ids                   : {len(obs)}")
    for k in sorted(kinds):
        print(f"    {k:<24} {kinds[k]}")

    print()
    print("--- SKIPPED FILES (reason given for every one) ---")
    if not skipped:
        print("    (none -- every file under out/ fell into a class)")
    for rel, why in skipped:
        print(f"    {rel}: {why}")

    print()
    print("--- STATUS HISTOGRAM over HTTP observations ---")
    sh = {}
    for r in obs.values():
        if r["kind"].startswith("HTTP") or r["kind"].startswith("ORPHAN"):
            sh[r["status"]] = sh.get(r["status"], 0) + 1
    for s in sorted(sh, key=lambda x: (len(x), x)):
        print(f"    HTTP {s}: {sh[s]}")

    print()
    print("--- PARSE RESULTS (an unparseable body is a CLASS, not a drop) ---")
    ph = {}
    for r in obs.values():
        ph[r.get("parse", "n/a (no body leg)")] = ph.get(r.get("parse", "n/a (no body leg)"), 0) + 1
    for k in sorted(ph):
        print(f"    {k}: {ph[k]}")

    print()
    print("--- ENDPOINT HISTOGRAM (method + path family) ---")
    eh = {}
    for r in obs.values():
        fam = r["path"].split("?")[0]
        fam = re.sub(r"/\d+", "/{id}", fam)
        key = f"{r['method']} {fam}"
        eh[key] = eh.get(key, 0) + 1
    for k in sorted(eh):
        print(f"    {eh[k]:>3}  {k}")

    print()
    print("=" * 100)
    print("JOURNAL-ENTRY OBSERVATIONS -- enumerated by ENDPOINT, not by remembered id")
    print("=" * 100)
    jes = [r for r in obs.values() if r.get("je")]
    print(f"count: {len(jes)}")
    grand_ok = 0
    for r in sorted(jes, key=lambda x: x["id"]):
        print()
        print(f"### {r['id']}   [{r['method']} {r['path']}]  HTTP {r['status']}")
        print(f"    totalFilteredRecords = {r.get('total_filtered')}   rows returned = {len(r.get('rows', []))}")
        if not r.get("rows"):
            print("    NO ROWS -- records no money cell at all")
            continue
        by_txn = {}
        for row in r["rows"]:
            by_txn.setdefault(row["txn"], []).append(row)
        for txn, rows in sorted(by_txn.items(), key=lambda kv: str(kv[0])):
            dr = sum((x["amount"] for x in rows if x["entry"] == "DEBIT"), D(0))
            cr = sum((x["amount"] for x in rows if x["entry"] == "CREDIT"), D(0))
            both = any(x["entry"] == "DEBIT" for x in rows) and any(x["entry"] == "CREDIT" for x in rows)
            bal = (dr == cr)
            if both and bal:
                grand_ok += 1
            print(f"    txn {txn}: rows={len(rows)}  DEBIT total={dr}  CREDIT total={cr}  "
                  f"both-sides={both}  balanced={bal}")
            for x in rows:
                amt = x["amount"]
                scale = -amt.as_tuple().exponent if isinstance(amt, D) else 0
                minor = None
                if isinstance(amt, D) and x["dp"] is not None:
                    q = amt.scaleb(x["dp"])
                    minor = str(q.to_integral_exact(rounding=decimal.ROUND_HALF_UP)) \
                        if q == q.to_integral_value() else f"NON-INTEGER-MINOR({q})"
                print(f"        je#{x['id']:<4} {x['entry']:<6} gl {x['gl_id']:<3} "
                      f"code {x['gl_code']:<6} {str(x['gl_type']):<10} "
                      f"amount='{amt}' scale={scale} ccy={x['ccy']} dp={x['dp']} "
                      f"minor={minor}  {x['gl_name']}  entity={x['entityType']}/{x['entityId']} "
                      f"date={x['txn_date']} reversed={x['reversed']}")
    print()
    print(f"balanced double-entry transaction groups observed: {grand_ok}")

    print()
    print("=" * 100)
    print("MONEY CELLS ELSEWHERE IN THE CORPUS (generic scan, every non-JE parsed body)")
    print("=" * 100)
    for r in sorted(obs.values(), key=lambda x: x["id"]):
        if r.get("je") or r.get("doc") is None:
            continue
        sink = []
        walk_money(r["doc"], "", sink)
        if sink:
            cells = ", ".join(f"{p}={v}" for p, v in sink[:12])
            more = "" if len(sink) <= 12 else f" ... (+{len(sink)-12} more)"
            print(f"  {r['id']:<46} HTTP {r['status']:<4} {len(sink):>3} cells: {cells}{more}")

    print()
    print("=" * 100)
    print("PSQL DUMPS -- the class the earlier enumerator swallowed")
    print("=" * 100)
    for r in sorted(obs.values(), key=lambda x: x["id"]):
        if r["kind"] == "PSQL-DUMP":
            print(f"  {r['id']}: {r['lines']} lines, {r['bytes']} bytes")

    balanced = (len(accounted) + len(skipped) == total)
    unparseable = sum(1 for r in obs.values()
                      if str(r.get("parse", "")).startswith("UNPARSEABLE-JSON"))
    print()
    print(f"ACCOUNTING: {len(accounted)} classified + {len(skipped)} skipped == {total} total ? {balanced}")
    print(f"UNPARSEABLE bodies: {unparseable}")

    # --- exit-code policy, and why it is stricter than "the arithmetic adds up".
    #
    # The identity above cannot fail on its own: a file the classifier does not recognise
    # lands in `skipped` and the sum still balances. An exit code keyed only on that
    # identity would therefore be green on the exact event this census exists to catch --
    # P-22's vacuous guard, and P-29's weak-tripwire count. So a NON-EMPTY skipped list is
    # itself a failure: out/ is written only by cap.sh / cap8.sh / cap9.sh and the psql
    # dumps, so an unrecognised file there is an artefact nobody's recipe produced, and a
    # promotion task must not walk over it. The file is still NAMED with a reason before
    # the refusal -- reporting and failing are not alternatives here.
    #
    # An unparseable body is fatal for the same reason: it is currently 0, and if it ever
    # becomes non-zero the corpus contains an observation whose money cells cannot be read,
    # which is precisely the state a promotion task must stop on rather than skip past.
    bad = 0
    if not balanced:
        print("REFUSING: the file accounting does not balance.", file=sys.stderr)
        bad = 1
    if skipped:
        print(f"REFUSING: {len(skipped)} file(s) under out/ were not produced by any recipe "
              f"in this rig (named above).", file=sys.stderr)
        bad = 1
    if unparseable:
        print(f"REFUSING: {unparseable} observation body/ies could not be parsed; their "
              f"money cells are unreadable (named above).", file=sys.stderr)
        bad = 1
    return bad


if __name__ == "__main__":
    sys.exit(main())
