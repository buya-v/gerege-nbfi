#!/usr/bin/env python3
"""A2 follow-up probes forced by what the earlier captures actually showed.

Two gaps to close:

1. A2-124 was MEANT to be the delete SUCCESS path but was not: my own fin-107
   update had just re-pointed financial activity 200 onto GL 21, so 21 was no
   longer clean. A genuinely clean account is created here and deleted.

2. A2-110 and A2-113 sent `usage` / `manualEntriesAllowed` ALONE and got
   "No parameters passed for update." That is consistent with two different
   causes — the field being non-updatable, or the deserializer not recognising it
   at all. Sending the same field ALONGSIDE a field that IS recognised (`name`)
   discriminates between them.
"""
import json, os

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")


def w(n, o):
    with open(os.path.join(REQ, n + ".json"), "w") as f:
        json.dump(o, f)
        f.write("\n")
    print("wrote", n)


w("gl-130-clean-for-delete", {"name": "Clean Delete Target", "glCode": "19999",
                              "manualEntriesAllowed": True, "type": 1, "usage": 1,
                              "description": "A2: created solely to observe the DELETE success path"})
w("upd-131-usage-with-name", {"name": "Clean Delete Target Renamed", "usage": 2})
w("upd-132-manual-with-name", {"name": "Clean Delete Target Renamed Again",
                               "manualEntriesAllowed": False})

if __name__ == "__main__":
    pass
