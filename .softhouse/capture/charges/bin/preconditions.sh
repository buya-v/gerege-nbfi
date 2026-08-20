#!/bin/sh
# T91 — CALL-THROUGH.  There is ONE Path B precondition rig, and this file is not it.
#
# Until T91 this file was a byte-verbatim COPY of the PRE-HARDENING Path B precondition script:
# blob e6c1795a172168105d788321a71ee4ca62b73e36, sha256
# 9256b881153d3deab2013cb9d95fae95258b68b398cdf22e5da9a8a416a46b54 — the bytes T40 lifted out of
# `pathb/t36/preconditions.sh` before T76 and T80 hardened the original.  Those two hardened the
# ORIGINAL and left the copies behind, so this file — which 17 capture scripts and `attest.py`
# actually invoke — still admitted both P0s T80 closed:
#
#   * the canary REQUEST was unpinned.  Any readable file was accepted, so T77's one-character edit
#     (principal 1162502.5 -> 1162502.55, no longer a half-minor-unit tie) made
#     "PASS effective rounding mode canary (= HALF_UP)" a tautology: it prints under HALF_UP AND
#     HALF_EVEN.
#   * the canary EXPECTATION was env-overridable — `CANARY_EXPECT=${CANARY_EXPECT:-20925.05}` — so
#     the runner supplied BOTH operands of the check.  A check whose operands the caller controls
#     is not a check.
#
# MEASURED against these exact bytes, this fire, 13 attack classes x {sh, bash}: 6 ADMITTED,
# including this line on tenant gerege —
#     PASS  effective rounding mode canary: period-1 interest 20925.04 (= HALF_UP)
# the rig certifying HALF_UP while printing the very value its own comment says means HALF_EVEN.
# Transcripts: .softhouse/capture/t91/out/prefix-livetwin-*/ and prefix-copy-*/.
#
# T80's recommendation, which T91 carries out: a third divergent copy IS the defect, so this file
# no longer contains a copy of anything.  It dot-sources the one hardened rig IN THE SAME
# INTERPRETER with the SAME positional arguments, so `sh bin/preconditions.sh gerege` and
# `bash bin/preconditions.sh gerege` behave exactly as they do for the rig itself, and the exit
# status is the rig's own.  No caller had to change.
#
# PROVENANCE WARNING — read before comparing transcripts.  Every `preconditions*.txt` under
# .softhouse/capture/charges/out/ was produced by the OLD bytes, not by these.  Those transcripts
# remain valid records of what was observed; they will NOT reproduce byte-for-byte through this
# call-through, because the hardened rig emits two extra canary-pin lines (P14a/P14b).  The old
# bytes are not lost: `git show e6c1795a172168105d788321a71ee4ca62b73e36`.
#
# Usage and exit status are unchanged:
#   sh preconditions.sh [tenant-identifier]      (default: gerege)
#   0 = every precondition holds; 1 = at least one breached; 2 = the rig itself is missing.
#
# The hardened rig requires CANARY_REQ to be the digest-pinned half-cent tie
# (pathb/t22-audit/req/calc-pmode2-gerege.json, sha256 2a6621be…352154).  bin/run-preconditions.sh
# and bin/attest.py already pass exactly that file.  bin/t51-negative.sh passes none, so it now
# reports one further breach; it is a negative control that already exited 1 and still does.
set -u

RIG=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)/pathb/t36/preconditions.sh
if [ ! -f "$RIG" ]; then
  echo "  FAIL  the hardened Path B precondition rig is missing: '$RIG'" >&2
  echo "PRECONDITIONS NOT RUN. DO NOT CAPTURE — nothing was asserted about the oracle." >&2
  exit 2
fi
# Dot-source, not exec: `exec sh` would pin the interpreter and break the sh-vs-bash invariance
# T85 required.  Sourcing keeps the caller's interpreter and inherits "$@" unchanged.
. "$RIG"
