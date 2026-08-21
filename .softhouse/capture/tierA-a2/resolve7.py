#!/usr/bin/env python3
"""Fill the one runtime-dependent field in an A2-7 request body from an OBSERVED response.

  python3 resolve7.py <template.json> <observed-response.json> <key> <out.json>

req/a2-7-loan-220.json carries "productId": "__PRODUCT_ID__" because the product id is
whatever the oracle assigns; guessing it would be a synthesised value. This reads the id
out of the committed capture of the create response (out/A2-210-*.json) and writes a
SEPARATE resolved body, so the template is never mutated and the resolved body is
reproducible from two committed artefacts.

Refuses to overwrite a resolved body that differs, for the same D-1 reason as mkreq7.py.
"""
import json
import os
import sys


def main(argv):
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 2
    tmpl, observed, key, out = argv[1:]
    body = json.load(open(tmpl))
    resp = json.load(open(observed))
    if key not in resp:
        print(f"REFUSING: {observed} has no {key!r} — no observation to resolve from. "
              f"keys present: {sorted(resp)}", file=sys.stderr)
        return 1
    placeholders = [k for k, v in body.items() if isinstance(v, str) and v.startswith("__")]
    if not placeholders:
        print(f"REFUSING: {tmpl} has no __PLACEHOLDER__ field to resolve.", file=sys.stderr)
        return 1
    for k in placeholders:
        body[k] = resp[key]
    text = json.dumps(body, indent=2) + "\n"
    if os.path.exists(out) and open(out).read() != text:
        print(f"REFUSING: {out} exists with different content (defect D-1).", file=sys.stderr)
        return 1
    with open(out, "w") as f:
        f.write(text)
    print(f"resolved {placeholders} = {resp[key]!r} (from {observed}) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
