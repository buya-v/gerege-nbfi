# C-T407-4 — two corrections to the record around T404's §8

**Why this is a separate file and not an edit.** T404's handoff is a record of its own moment
and this program does not rewrite handoffs (T407 §7 states the convention and I am following
it, not inventing it). But an unnamed corruption sitting in committed evidence is a trap for
the next reader, so the correction is written down where the evidence is.

## 1. §8's OPENING sentence is too strong. Its CLOSING sentence is right.

§8 opens by saying arms `H` and `W` came back `exit=2 probe=ABSENT census=<none printed>` and
that this *"reads exactly like a clean REFUSAL."*

**The committed transcript disagrees with that sentence.**
`.softhouse/capture/t404-t384-conditions/evidence/10-RED-BEFORE-full-drive-unfixed-guard.txt`
scores both rows, at its lines 15 and 23 [VERIFIED: T431 read the file]

    marker=NO  census=NO  dirty=no  >>> FAIL

**The instrument DID distinguish them, in its own verdict column, at the time.** That is exactly
what §8's *closing* sentence says — *"the census column is what caught this"* — so the handoff
contradicts itself by one paragraph, in the safe direction.

**The honest form:** *the FIELDS looked like a refusal; the ARM did not pass.* T404 did not
report the corrupted rows as results (T407 checked its arm table against
`evidence/12` and `evidence/13`; I did not re-check that particular cross-reference myself), so nothing downstream is wrong. Only the sentence is.

## 2. A SECOND corruption is recorded in `evidence/11` and named nowhere.

`.softhouse/capture/t404-t384-conditions/evidence/11-RED-BEFORE-arms-H-W-N.txt` records, at its
lines 11 and 14, a failure mode that is **not** the shared-work-root defect §8 discusses
[VERIFIED: T431 read the file]:

    .softhouse/capture/t404-t384-conditions/drive-red-t404.sh: line 501: r: command not found
    .softhouse/capture/t404-t384-conditions/drive-red-t404.sh: line 521: syntax error near unexpected token `fi'

**The drive script was EDITED WHILE `bash` WAS EXECUTING IT**, so the interpreter resumed at a
stale byte offset in a file whose contents had shifted underneath it. `bash` reads a script
incrementally by file offset; rewriting the file mid-run does not restart it.

**A unique work root does not prevent this.** The remedy is different and it is procedural:
**FREEZE THE DRIVE BEFORE YOU RUN IT.** T431 adopted it — `/tmp/t431/run.sh` copies the drive
out of the repository, `chmod a-w`s it, prints its SHA-256, and runs the frozen copy, so an
edit to the tracked script cannot reach a run in flight. The header of
`.softhouse/capture/t431-t407-conditions/drive-t431.sh` carries the rule.

**Why it matters beyond tidiness:** both corruptions produce output that a hurried reader can
mistake for a verdict. That is the `P-98` shape — *a corrupted run that can look like a
verdict* — and it is the reason both belong in the record rather than in one handoff's §8.
