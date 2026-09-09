# Measurement tools — control-test these before trusting a number

Extracted from the 2026-09-09 session, where SEVEN measurement bugs shared one root:
measuring a proxy for the property instead of the property, and arming the instrument
without testing it once. Each script here was wrong at least once before it was right.

    kills.sh       <ctx> <impl>            kill count for one wrong implementation
    capcount.sh    <worktree> <ctx> <impl> same, against an arbitrary worktree
    redcount.sh    <worktree> <ctx>        count of registered <ctx>-wrong-* drives
    drivecount.sh  <worktree> <ctx>        same, simpler form

## The rule these encode

**Run against a KNOWN CONTROL before trusting output.** On `main`:

    loanschedule-wrong-days-in-year-365   must report 45
    loanschedule-wrong-half-even          must report 5
    parties-wrong-iota-ordinals           must report 12
    charges-wrong-rounding-half-even      must report 1
    loanproduct drive count               must report 4

If a control is wrong, the instrument is wrong — not the tree.

## The three traps baked into these scripts

1. `-root` IS NOT UNIVERSAL. Most `cmd/conformance` binaries REQUIRE it; loanschedule's
   REJECTS it, and the two error texts differ ("‑root is required" vs "not defined:
   -root"). Handle both or a context silently reads 0.
2. `grep -c` PRINTS 0 AND EXITS 1. Never `grep -c … || echo 0` — it yields "0\n0" and
   every later `$(( ))` dies with "bad math expression".
3. NO `||` FALLBACK AROUND THE MEASUREMENT. A FAIL verdict IS exit 1, so a fallback
   fires on every real kill and concatenates two runs' output.

Also, from the same session: zsh does NOT word-split unquoted variables, so
`for w in $ws` passes the whole list as one argument. Use `while IFS= read -r`.
And macOS has no `timeout(1)` — a liveness check built on it reports "hung" when the
binary is merely absent.
