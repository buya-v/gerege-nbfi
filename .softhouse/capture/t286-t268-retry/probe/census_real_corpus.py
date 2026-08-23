#!/usr/bin/env python3
"""T292 -- measure the real corpus BEFORE designing the coverage predicate.

Answers three questions that decide whether the T292 formulation can be adopted
without going RED on evidence that is already committed:

  Q1  how many strings anywhere in the document are in the AFFIRMATIVE vocabulary,
      and how many of those sit under a key that `is_verdict_key` would NOT match
      (i.e. would the vocabulary-keyed detector see MORE than the key-keyed one)?
  Q2  how many boolean values sit under a key auto-classified PREDICATE, and where?
  Q3  how many AFFIRMATIVE strings are FREE-FLOATING -- i.e. not a value of the
      same object that carries at least one predicate boolean?

Q3 is the number that decides whether guard T2 (free-floating affirmation) can be
a refusal without turning the committed evidence red.
"""
import json
import sys
from pathlib import Path

AFFIRMATIVE = {"AS PREDICTED", "AS_PREDICTED", "AS-PREDICTED", "PASS", "PASSED", "OK",
               "CONFIRMED", "REPRODUCED", "GREEN", "HELD", "AGREES", "MATCHED"}


def is_auto_predicate(k):
    if not (isinstance(k, str) and k.startswith("P") and "_" in k):
        return False
    head = k.split("_", 1)[0]
    return len(head) > 1 and head[1:].isdigit()


def is_verdict_key(k):
    kl = str(k).lower()
    return "verdict" in kl or kl == "status" or kl.endswith("status")


def objects(v, path="$"):
    """Yield (path, dict) for every object anywhere."""
    if isinstance(v, dict):
        yield path, v
        for k, x in v.items():
            yield from objects(x, path + "." + str(k))
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from objects(x, path + "[%d]" % i)


def strings(v, path="$"):
    """Yield (path, kind, string) for every string anywhere, as a KEY or as a VALUE."""
    if isinstance(v, dict):
        for k, x in v.items():
            if isinstance(k, str):
                yield path + ".<key>" + k, "key", k
            yield from strings(x, path + "." + str(k))
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from strings(x, path + "[%d]" % i)
    elif isinstance(v, str):
        yield path, "value", v


def main():
    files = sys.argv[1:]
    rc = 0
    for f in files:
        p = Path(f)
        doc = json.loads(p.read_text(encoding="utf-8"))
        print("FILE", f)

        preds = []
        for opath, o in objects(doc):
            for k, v in o.items():
                if isinstance(v, bool) and is_auto_predicate(k):
                    preds.append((opath, k, v))
        print("  Q2 predicate booleans (auto ^P[0-9]+_) :", len(preds))
        print("     distinct owning objects             :",
              len({p for p, _, _ in preds}))

        affs = [(pa, kind, s) for pa, kind, s in strings(doc)
                if s.strip().upper() in AFFIRMATIVE]
        print("  Q1 affirmative strings anywhere        :", len(affs))
        under_verdict_key = 0
        for pa, kind, s in affs:
            if kind == "value" and is_verdict_key(pa.rsplit(".", 1)[-1]):
                under_verdict_key += 1
        print("     of which under a verdict-named key  :", under_verdict_key)
        print("     EXTRA seen by vocabulary scan       :", len(affs) - under_verdict_key)
        for pa, kind, s in affs:
            if not (kind == "value" and is_verdict_key(pa.rsplit(".", 1)[-1])):
                print("       EXTRA:", kind, pa, repr(s))

        # Q3: free-floating = affirmative string whose IMMEDIATELY OWNING object
        # carries no predicate boolean.
        witnessed = {p for p, _, _ in preds}
        free = 0
        for pa, kind, s in affs:
            owner = pa.rsplit(".", 1)[0] if kind == "value" else pa.split(".<key>")[0]
            if owner not in witnessed:
                free += 1
                print("       FREE-FLOATING:", kind, pa, repr(s))
        print("  Q3 free-floating affirmations          :", free)

        # non-auto boolean keys, which need the register
        others = sorted({k for _, o in objects(doc) for k, v in o.items()
                         if isinstance(v, bool) and not is_auto_predicate(k)})
        print("  non-auto boolean keys                  :", others)
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main())
