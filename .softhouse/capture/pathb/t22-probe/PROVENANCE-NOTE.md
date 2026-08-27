# t22-probe — provenance correction (T22 audit P1-13)

Added 2026-08-18 by T25 (oracle-independent record correction). See
`.softhouse/reviews/T22-pathb-capture-audit.md` §9 / §10 P1-13.

Two corrections to how this rescued WIP directory must be read:

1. **The `halfeven` filename tag is a DISCOVERY label, not a variant that was run.**
   The files under `out/` are named `…-halfeven-…`, but **nothing in `repro.sh`,
   `capture.sh`, `mkreq.py` or `mkcalc.py` changes the tenant rounding mode.** The
   tag records what the prior worker had *discovered* the `default` tenant's mode to
   be (`c_configuration.rounding-mode = 6`, HALF_EVEN), not a HALF_EVEN variant
   produced alongside a HALF_UP one. Read as a variant it would be a false record.
   The scripts themselves (`repro.sh`, `capture.sh`, `mkreq.py`, `mkcalc.py`) are
   sound — their outputs re-hash byte-for-byte to the committed corpus, produced
   through freshly created products, which is an independent reproduction.

2. **`invariants.py` was defective — now corrected in place.** Its `I5` verdict was
   hard-coded to PASS (`verdict("I5", True, …)`) and could never fail. It is now a
   genuinely failable check. The T22 audit did not rely on it; the audit's own
   from-scratch checker is `../t22-audit/t22_invariants.py`.
