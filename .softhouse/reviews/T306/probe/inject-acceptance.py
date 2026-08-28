#!/usr/bin/env python3
"""T306 — inject ONE acceptance-at-a-date-boundary vector into a SCRATCH store.

READ THIS BEFORE EDITING. This script writes exactly one file and the path is
built from argv[1], which store-tripwire.sh sets to a `mktemp -d` directory. It
must NEVER be pointed at the repo: `.softhouse/vectors/` is a committed store
and, this batch, is reserved for T328. The guard below refuses any target that
is not under a temp root, because "nobody happened to run it that way" is not a
control (patterns.md, "Ratified artefacts are write-protected": probe scripts
read and report).
"""

import json
import pathlib
import sys
import tempfile

if len(sys.argv) != 2:
    sys.exit("usage: inject-acceptance.py <SCRATCH_DIR>")

scratch = pathlib.Path(sys.argv[1]).resolve()
tmproot = pathlib.Path(tempfile.gettempdir()).resolve()

# FAIL-CLOSED. Anything not under the platform temp root is refused outright.
try:
    scratch.relative_to(tmproot)
except ValueError:
    sys.exit(
        "REFUSING to write: %s is not under the temp root %s. This script "
        "injects a DELIBERATELY WRONG vector and must only ever touch a "
        "throwaway copy of the store." % (scratch, tmproot)
    )

src = scratch / ".softhouse/vectors/ledger/LDG-04-header-account-accepted.json"
if not src.is_file():
    sys.exit("no scratch store at %s" % src)

d = json.loads(src.read_text())
d["case_id"] = "ZZZ-T306-INJECTED-preclosure-acceptance"
d["capabilities_required"] = sorted(
    set(d["capabilities_required"]) | {"ledger.opening.balance.and.closure"}
)
# THE REQUEST-SIDE FACTS OF THE PRE-CLOSURE BOUNDARY, in the shape T327's B-1
# actually observed -- transaction 2026-08-27, closure closed 2026-08-27 -- but
# recorded as an ACCEPTANCE, which is what makes it the vector the date arms
# still refuse. The dates are strict zero-padded yyyy-MM-dd because isoBefore /
# isoAfter compare BYTE-WISE.
d["request"]["transaction_date"] = "2026-08-27"
d["request"]["business_date"] = "2026-08-28"
d["request"]["latest_closing_date"] = "2026-08-27"

out = scratch / ".softhouse/vectors/ledger/ZZZ-T306-INJECTED-preclosure-acceptance.json"
out.write_text(json.dumps(d, indent=2) + "\n")
print("  injected: %s  expect.kind=%s" % (out.name, d["expect"]["kind"]))
