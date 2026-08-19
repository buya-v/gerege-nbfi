#!/usr/bin/env python3
"""T41 edit batch 19 — scope section 5's and section 8's attestation phrasing to 4.1.2."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- section 5, the Rounding.SignificantDigits row --------------------------
sub(
    "| `Rounding.SignificantDigits` | 19 | 12-vs-19 pair, all 18 periods divergent (§4.1). |",
    "| `Rounding.SignificantDigits` | 19 | 12-vs-19 pair, all 18 periods divergent (§4.1). "
    "**Read as the THREADED context** (§4.1.2): the corpus discriminates threaded precision on "
    "that 18 × 18.5 % shape, and T39 measured it **indiscriminable on all sixteen of its own** "
    "(N-4), so \"captured at 19\" is a provenance claim on that family and a discrimination "
    "claim on this one. |",
)

# --- section 5, the Rounding.Mode row ---------------------------------------
sub(
    "| `Rounding.Mode` | HALF_UP | HALF_EVEN *observed* live on a running oracle (20,925.05 vs "
    "20,925.04) but **uncaptured in the corpus** → refused. |",
    "| `Rounding.Mode` | HALF_UP | HALF_EVEN *observed* live on a running oracle (20,925.05 vs "
    "20,925.04) but **uncaptured in the corpus** → refused. **That observation is a PATH-B one** "
    "(§4.1.2): it varies the **ambient** tenant mode, which is the arithmetic there. On Path A "
    "the same ambient change moves nothing and only the **threaded** mode does — 0 of 16 against "
    "15 of 16 [VERIFIED: T39 N-3]. |",
)

# --- section 5's admissibility paragraph ------------------------------------
sub(
    "Second, the server-path captures were taken on a tenant running HALF_EVEN; **that is now "
    "fixed rather than argued around**: task T36 re-captured all four on the `gerege` tenant "
    "(`Asia/Ulaanbaatar`, rounding-mode 4, attested `MathContext(19, HALF_UP)`), with a "
    "preconditions script proven to *fail* on the stock tenant, and got **byte-identical** "
    "results across two independent product fixtures. **Path B is now admissible as a capture "
    "path.** Nothing is promoted, on either path.",

    "Second, the server-path captures were taken on a tenant running HALF_EVEN; **that is now "
    "fixed rather than argued around**: task T36 re-captured all four on the `gerege` tenant "
    "(`Asia/Ulaanbaatar`, rounding-mode 4, attested `MathContext(19, HALF_UP)`), with a "
    "preconditions script proven to *fail* on the stock tenant, and got **byte-identical** "
    "results across two independent product fixtures. **Path B is now admissible as a capture "
    "path**, and revision 8 adds that on **Path B the attested AMBIENT context is exactly the "
    "right thing to attest**, because nothing threads a context there (§4.1.2) — T40 re-ran the "
    "same preconditions 21 of 21 five times and re-observed the half-cent canary. **On Path A "
    "the ambient attestation is provenance, not arithmetic**, and every Path-A record must state "
    "its **threaded** context separately; T39's does, and the pre-T39 ones conflate the two. "
    "Nothing is promoted, on either path. **Revision 8 also adds a third fact a ratifier should "
    "know:** the corpus is no longer 21 captures — T39 added 15 parity-setting ones and T40 "
    "added 21 charge-bearing ones, and revision 8's from-text model reproduces **4,578 cells** "
    "across all four sets with zero mismatches [`.softhouse/reviews/t41-probe/`].",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
