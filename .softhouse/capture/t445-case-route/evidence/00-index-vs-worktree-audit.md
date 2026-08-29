# T445 — THE AUDIT T444 ASKED FOR: every read in `guard_guards_dir_registration`, classified

T444's closing instruction: *"Every test in this guard should be audited for the same
filesystem-versus-index confusion: which reads the index, which reads the working tree, and what
happens when the two disagree?"*

This is that audit. It is a statement about a **search**, and the search is stated: I read the
whole of `guard_guards_dir_registration` from its opening `local gdrel` to its closing `return 0`
and enumerated every expression that names a path — `git ls-files`, `git cat-file`, `grep`, `[ -f`,
`[ -d`, `[ -e`, `[ -r`, `[ -L`, and every `"$REPO_ROOT/…"` expansion — with
`grep -n 'REPO_ROOT/\|git ls-files\|git cat-file\|\[ -f \|\[ -e \|\[ -r \|\[ -d \|\[ -L '` over
the function's line range, then read every hit in context. Anything outside that function is out
of this task's grant and is listed under DISCLOSED below.

## THE TABLE

| # | what is read | BEFORE T445 | AFTER T445 | driven |
|---|---|---|---|---|
| 1 | the population | INDEX (`git ls-files` with `:(glob)`) | unchanged | T358 / T404 |
| 2 | this harness's own executable text (`$conf`) | **WORKING TREE** | **WORKING TREE — deliberately, see below** | reasoned + probe |
| 3 | the member's index entry (mode, blob) | INDEX, pinned `:(literal)$rel` | unchanged | T404 arm G; T444 |
| 4 | **the member's own `REACHED-BY` row** | **WORKING TREE** `"$REPO_ROOT/$rel"` | **INDEX blob** `git cat-file blob "$member_blob"` | **arm MCASE (case), arm LEGDIRTY (uncommitted)** |
| 5 | **how many `REACHED-BY` rows the member carries** | *never counted* | INDEX blob | **arm 2ROW** |
| 6 | **the witness's existence, on the TYPED spelling** | **WORKING TREE** `[ ! -f "$REPO_ROOT/$self_wit" ]` | **REMOVED** | **arm WGONE** |
| 7 | the witness's resolution | INDEX (`git ls-files --error-unmatch`) | unchanged | T375 / T404 |
| 8 | the witness's pinned re-lookup (mode, blob, round-trip) | INDEX, pinned `:(literal)$self_norm` | unchanged | T431 / T444 |
| 9 | **the witness's naming test — THE TEST THAT DECIDES** | **WORKING TREE** `grep -qF "$base" "$REPO_ROOT/$self_norm"` | **INDEX blob** `git cat-file blob "$self_blob"` | **arm CASE (T444 M-1, re-derived), arm WDIRTY (uncommitted)** |
| 10 | **the DECLARED witness's existence** | **WORKING TREE** `[ ! -f "$REPO_ROOT/$witness" ]` | **INDEX** — one tracked entry, regular-file mode | arm GITLW |
| 11 | **the DECLARED `CALLER` token test** | **WORKING TREE** `grep -qF "$token" "$REPO_ROOT/$witness"` | **INDEX blob** `git cat-file blob "$wit_blob"` | **arm CDIRTY** |
| 12 | **the DECLARED `SUBJECT` token test** | **WORKING TREE** `grep -qF "$token" "$REPO_ROOT/$rel"` | **INDEX blob** (`member_text`) | same class as 4 |

Rows 4, 6, 9, 10, 11 and 12 were reads of this host. Rows 4, 9, 11 were **fail-open**: each of them
could be made to answer YES about a commit that does not say YES. Rows 6 and 10 could only
over-refuse. Row 12 is the same mechanism as row 4 with the roles swapped.

## ROW 2 — WHY THE HARNESS'S OWN TEXT IS STILL READ FROM THE WORKING TREE

`code="$(grep -v '^[[:space:]]*#' "$conf")"` feeds the INVOCATION test: does a non-comment line of
this harness name this member's path? **The text that must answer that question is the text that
EXECUTES, and the text that executes is the file on disk that `bash` was handed.** Grading the
tracked blob instead would answer a question about a file that is not running — which is the
mirror image of the defect this whole commit removes, and it would go WRONG in the fail-open
direction the moment the two diverge.

The obvious attack — an index entry `.softhouse/CONFORMANCE.SH` that wins the checkout collision —
**cannot be built on this host**: the entry that sorts LAST wins, and every case variant of an
all-lower-case path sorts BEFORE it. MEASURED, not reasoned:
`instruments/probe-collision-order.sh`, transcript `01-collision-order-probe.txt` — a lower-case
target keeps its own content against both an upper-cased and an all-caps decoy; an upper-case
target loses to its lower-case decoy.

## THE DIVERGENCE MECHANISMS I CONSIDERED

**Driven, and closed:**

* **case folding** on a case-INSENSITIVE filesystem — arms `CASE` (witness side, basenames) and
  `MCASE` (member side, DIRECTORY names). The collision order is measured, not assumed.
* **an ordinary uncommitted working-tree edit** — arms `LEGDIRTY`, `WDIRTY`, `CDIRTY`. This is the
  cheapest instance of the class and needs no cleverness at all; it is the one a worker produces
  by accident.
* **a path present in the index and ABSENT from the checkout** — arm `WGONE`.
* **a gitlink (`160000`) as a declared witness** — arm `GITLW`. Its object is a commit, not a blob.

**Driven by T444 and re-stated here so silence is not read as completion:** a member filename
containing a literal NEWLINE (fail-CLOSED), a gitlink MEMBER (fail-CLOSED), a member carrying
multiple `REACHED-BY` rows (not a fail-open; row 2 was never graded — now refused, arm `2ROW`),
and a CONFLICTED INDEX reaching `member_multi` (fail-CLOSED; the sentence claiming it could not
is corrected in this commit).

**NOT DRIVEN by me. Disclosed by name and by spelling, because "not found" is a statement about
the search:**

* **`git update-index --skip-worktree`** and **`git update-index --assume-unchanged`**. Both are
  index BITS, not blob changes, so after T445 no graded read can see them; before T445 they let a
  working-tree lie sit under a clean `git status`. I did not build either arm. `[UNVERIFIED]`
* **a sparse checkout** (`git sparse-checkout set …`, `core.sparseCheckout=true`). Structurally
  identical to arm `WGONE` — an index entry with no file — and now gradeable for the same reason.
  Not driven as its own arm. `[UNVERIFIED]`
* **`.gitattributes` smudge rules that make the checkout differ from the blob**: `* text eol=crlf`,
  `* ident`, and `filter=<name>` (the last needs `filter.<name>.smudge` in local config, i.e. host
  state a clone does not carry). After T445 the graded reads are the blob, so these cannot move the
  verdict; before T445 `eol=crlf` and `ident` could. Not driven. `[UNVERIFIED]`
* **`core.symlinks=false`**, which materialises a tracked symlink as a regular file whose contents
  are the target path. The mode is read from the index, so it cannot defeat the symlink refusal.
  Not driven. `[UNVERIFIED]`
* **macOS unicode normalisation** — `core.precomposeunicode`, and an NFD/NFC pair of index entries
  that fold to one filesystem path. This is the same shape as the case route with a different
  folding rule, and it interacts with the C-quoting constraint that already refuses non-ASCII
  witness paths. **NOT DRIVEN, and I could not rule it out.** `[UNVERIFIED]`
* **a genuinely case-SENSITIVE filesystem, and a second git binary.** The same bound T404, T407,
  T431 and T444 each recorded. Note what it means here: `CASE` and `MCASE` are *consequences* of
  case-insensitivity, so a case-sensitive host is where they would NOT reproduce — and a commit
  carrying either construction would materialise both files there. **The verdict of this guard was
  therefore host-dependent for such a commit, which is itself the objection, and reading the index
  removes the dependence.** `[UNVERIFIED on a case-sensitive host.]`
* **the pinned toolchain.** Every arm ran under the announced FALLBACK toolchain. RED and GREEN are
  like-for-like; neither is graded under the pinned toolchain. `[UNVERIFIED for the pinned toolchain]`

**Outside this function, therefore outside this grant — filed, not fixed:**

* `guard_dead_path_frontier`'s census **crashes** rather than diagnosing on a non-ASCII path
  (`[Errno 2]`), a newline path (`[Errno 2]`) and a gitlink (`[Errno 21] Is a directory`) under
  `.softhouse/guards/` [T444 C-4, three transcripts]. It refuses rather than passing, but the
  cause it prints is not the cause.
* `.softhouse/bin/fire-program.sh:1406` cites `.softhouse/conformance.sh:3217-3220` for a quoted
  refusal; `:3217-3220` is a comment and the function header. **Already rotted before T445 and NOT
  moved by T445** — every line I added is below `:3271` [VERIFIED: `sed -n '3217,3220p'` before and
  after]. `fire-program.sh` is not in this grant.
