#!/usr/bin/env python3
"""Discriminator for the "No parameters passed for update." behaviour.

A2-110 (`{"usage":1}` on GL 1) and A2-113 (`{"manualEntriesAllowed":false}` on GL 2)
were both refused 400 "No parameters passed for update.". A2-131/A2-132 then showed
BOTH fields update fine when sent alongside `name`. So the refusal is not
"this field is not updatable".

Two candidate explanations remain, and they are distinguishable:
  (H1) a single-field update body is rejected regardless of which field it is;
  (H2) the target accounts were special — GL 1 is a HEADER WITH CHILDREN, GL 2 is
       mapped to a product — and the entity silently drops the change, leaving an
       empty `changes` map which then reports as "no parameters".

Probe: send EXACTLY ONE field, on a FRESH account with no children, no mapping and
no journal entries. H1 predicts 400; H2 predicts 200.
"""
import json, os

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")


def w(n, o):
    with open(os.path.join(REQ, n + ".json"), "w") as f:
        json.dump(o, f)
        f.write("\n")
    print("wrote", n)


w("gl-140-fresh-for-update", {"name": "Update Discriminator", "glCode": "19998",
                              "manualEntriesAllowed": True, "type": 1, "usage": 1})
w("upd-141-usage-only", {"usage": 2})
w("upd-142-manual-only", {"manualEntriesAllowed": False})
w("upd-143-usage-same-value", {"usage": 1})   # no-op: already 1

if __name__ == "__main__":
    pass
