#!/bin/sh
# T91 — CALL-THROUGH.  There is ONE Path B precondition rig, and this file is not it.
#
# Until T91 this file was a byte-verbatim COPY of the PRE-HARDENING Path B precondition script:
# blob e6c1795a172168105d788321a71ee4ca62b73e36, sha256
# 9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54.  T44 copied it here to run the
# suite against tenant `default` as a failing-configuration control; the transcript it produced is
# `../out/PRECOND-default.txt` (EXIT=1, 5 breaches).  T76 and T80 then hardened the ORIGINAL at
# `pathb/t36/preconditions.sh` and left this copy carrying the two P0s T80 closed — raised as T77's
# F-1, re-raised by T80, fixed here.
#
#   * the canary REQUEST was unpinned.  Any readable file was accepted, so T77's one-character edit
#     (principal 1162502.5 -> 1162502.55, no longer a half-minor-unit tie) made
#     "PASS effective rounding mode canary (= HALF_UP)" a tautology: it prints under HALF_UP AND
#     HALF_EVEN.
#   * the canary EXPECTATION was env-overridable — `CANARY_EXPECT=${CANARY_EXPECT:-20925.05}` — so
#     the runner supplied BOTH operands of the check.
#
# MEASURED against these exact bytes, this fire, 13 attack classes x {sh, bash}: 6 ADMITTED,
# including this line on tenant gerege —
#     PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)
# the rig certifying HALF_UP while printing the very value its own comment says means HALF_EVEN.
# Transcripts: .softhouse/capture/t91/out/prefix-copy-sh/ and prefix-copy-bash/.
#
# T80's recommendation, which T91 carries out: a third divergent copy IS the defect, so this file
# no longer contains a copy of anything.  It dot-sources the one hardened rig IN THE SAME
# INTERPRETER with the SAME positional arguments.
#
# PROVENANCE WARNING — read this before checking a digest.  `AUDIT-CHARGES.md` (T44) records that
# this file, `charges/bin/preconditions.sh` and `pathb/t36/preconditions.sh` were "all three sha256
# 9256b881…a46b54".  That was true when T44 wrote it and is now true of NONE of them: T76/T80
# changed the third, T91 changed the other two.  The audited bytes are not lost:
# `git show e6c1795a172168105d788321a71ee4ca62b73e36`.
#
# `../out/PRECOND-default.txt` DOES still reproduce through this call-through, and I measured it
# rather than assuming:
#     CANARY_REQ=<pathb/t22-audit/req/calc-pmode2-gerege.json> sh preconditions-COPY.sh default
# gives the SAME 5 breaches and the same exit 1.  The transcript differs in exactly two places —
# one ADDED line, `PASS  canary request pinned by DIGEST COMPARISON …`, and a longer wording on
# `FAIL  rounding-mode canary returned HTTP 404, not 200[ — the mode in force was never
# established]`.  So T44's finding is unaffected; only the text is richer.
#
# Nothing in the repository invokes this file (grep for its basename finds only prose).  It is kept
# rather than deleted because AUDIT-CHARGES.md names it as the provenance of a committed transcript
# and a dangling name is its own hazard; it is a call-through rather than a copy because a copy is
# what T91 exists to remove.
#
# Usage and exit status are unchanged:
#   sh preconditions-COPY.sh [tenant-identifier]      (default: gerege)
#   0 = every precondition holds; 1 = at least one breached; 2 = the rig itself is missing.
set -u

RIG=$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)/pathb/t36/preconditions.sh
if [ ! -f "$RIG" ]; then
  echo "  FAIL  the hardened Path B precondition rig is missing: '$RIG'" >&2
  echo "PRECONDITIONS NOT RUN. DO NOT CAPTURE — nothing was asserted about the oracle." >&2
  exit 2
fi
# Dot-source, not exec: `exec sh` would pin the interpreter and break the sh-vs-bash invariance
# T85 required.  Sourcing keeps the caller's interpreter and inherits "$@" unchanged.
. "$RIG"
