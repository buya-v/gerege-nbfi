# T239 — falsifiable predictions, registered BEFORE probing

Registered at fork point `477dc2da0f9edf3922e7d29e689bc6473289befc` (= `origin/main` = `merge-base`,
measured, not asserted). Nothing below has been measured by me at the time of this commit; I have
read T234's HANDOFF and its `instruments/21-r11-recall-loss.sh`, and nothing else.

The instrument under audit is **`.softhouse/reviews/T138-evidence/r11-hygiene.sh:35`** — note the
path, which is NOT the path T239's own `description` gives (`.softhouse/capture/t138-evidence/`,
which does not exist; see handoff §1).

## P1 — population mismatch in T234's measurement (the load-bearing one)

`r11-hygiene.sh:35` passes a **commit argument**:

    git grep -n -a -E '<5 alternatives>' "$T115" -- <3 pathspecs>

so its population is the **T115 tree** (`bd59187cf83c7c7161db23668e91d45bd46be2a8`) restricted to
those 3 pathspecs. T234's `21-r11-recall-loss.sh` builds its command as
`git grep $f -c -a -- '<pattern>' -- $P` with **no commit argument**, so it searched the **working
tree at T234's HEAD**.

**I predict the sound-engine hit count measured AT `$T115` is NOT 64**, because HEAD's
`.softhouse/capture/t91/` is a different population from T115's. If it comes out exactly 64 this
prediction is falsified and I will say so.

## P2 — the escape

`git grep -E` compiles `\bmain\b` to the literal `bmainb`; the term contributes **0** lines. The
other four alternatives are literals and are unaffected. So r11 is **partially** void, not void.

## P3 — mechanism

T224 died of right-anchoring an inflected stem; r11 dies of the engine. I predict **only** the
engine mechanism is present at `:35` — `main` is not an inflected stem being right-anchored — and
that the two mechanisms are therefore distinguishable here.

## P4 — engines

`/usr/bin/grep -P` exits **2** and prints nothing useful. `git grep -P` works (it is PCRE1/2 linked
into git, a different code path from `/usr/bin/grep`). BSD grep and ugrep honour `\b`.

## P5 — multi-line

Every sweep in this program has been line-oriented. I predict a multi-line matcher over the same
population finds **at least one** `main`-token occurrence spanning a newline that no line-oriented
run of `:35` could ever have reported.

## P6 — a SECOND void instrument in the same file

`r11-hygiene.sh:77` is `cd /tmp/T138-merge 2>/dev/null && git grep ...`, and line 79 unconditionally
prints `(searched the MERGED tree)`. I predict `/tmp/T138-merge` does not exist on this machine, so
section 4 of the script prints its reassurance having searched **nothing**, and the script still
exits 0 — the fail-OPEN dead-`cd` class. This is a different defect from the `\b` one and T234's
L-2 does not cover it.
