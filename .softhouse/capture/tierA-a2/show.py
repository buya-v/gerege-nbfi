#!/usr/bin/env python3
"""Print captured exchanges: request, status, response. Read-only over out/.

Uses parse_float=Decimal (T145) so no money literal is ever routed through a
binary double on its way to a human-readable summary.
"""
import json, os, sys, decimal, glob

DIR = os.path.dirname(os.path.abspath(__file__))


def load(p):
    with open(p) as f:
        return json.load(f, parse_float=decimal.Decimal)


def main(pattern):
    for st in sorted(glob.glob(os.path.join(DIR, "out", pattern + ".status"))):
        name = os.path.basename(st)[:-len(".status")]
        code = open(st).read().strip()
        body = os.path.join(DIR, "out", name + ".json")
        print("=" * 78)
        print(f"{name}   HTTP {code}")
        head = open(os.path.join(DIR, "out", name + ".http")).read().strip().splitlines()
        bf = [l for l in head if l.startswith("body-file:")]
        print("  ", head[0])
        if bf:
            rp = os.path.join(DIR, bf[0].split(": ", 1)[1])
            print("   REQ :", open(rp).read().strip())
        try:
            d = load(body)
        except Exception as e:
            print("   RESP(raw):", open(body).read()[:600])
            continue
        if isinstance(d, dict) and "errors" in d:
            print("   GLOBALISATION:", d.get("userMessageGlobalisationCode"))
            for e in d["errors"]:
                print("     -", e.get("userMessageGlobalisationCode"), "|",
                      e.get("parameterName"), "|", e.get("defaultUserMessage"))
        else:
            print("   RESP:", json.dumps(d, default=str)[:900])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "*")
