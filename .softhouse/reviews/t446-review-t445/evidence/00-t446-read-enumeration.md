# T446 — my OWN enumeration of every read in `guard_guards_dir_registration`

T445 claims the guard now performs **zero working-tree reads of any graded path**. That is a
statement about a SEARCH, so here is my search, stated before its result.

## THE SEARCH

Both trees extracted to scratch outside the repo:

```
git show main:.softhouse/conformance.sh                    > /tmp/t446/conf-main.sh
git show softhouse/T445-case-route:.softhouse/conformance.sh > /tmp/t446/conf-t445.sh
```

The function's line range on the tip is `3219`–`4344` (`grep -n '^guard_guards_dir_registration()'`
to the next top-level `}`), plus the new `guard_registration_decisive_lines()` at `4397`–`4510`
which it calls at `:3303`. Over that range, with **full-line comments removed** so a read
mentioned in prose is not counted as a read performed:

```
awk 'NR>=3219 && NR<=4345' conf-t445.sh | grep -vE '^\s*#' \
  | grep -nE 'REPO_ROOT|git |cat |sed -n|awk |grep |readlink|\[ -[a-z] |\[ ! -[a-z] |stat |head |tail |wc |find |ls |\$\(<'
```

and, narrower, every surviving `$REPO_ROOT` expansion:

```
awk 'NR>=3219 && NR<=4345' conf-t445.sh | grep -vE '^\s*#' | grep -n 'REPO_ROOT'
```

which returns exactly TEN hits (offsets are +3218):

```
L3   local gd="$REPO_ROOT/$gdrel"                          <- name construction
L4   local conf="$REPO_ROOT/.softhouse/conformance.sh"     <- name construction
L18  pop="$( cd "$REPO_ROOT" … git ls-files … )"           <- INDEX
L73  member_stat="$( cd "$REPO_ROOT" … git ls-files -s … )"<- INDEX
L119 member_text="$( cd "$REPO_ROOT" … git cat-file blob … )" <- BLOB
L147 self_norm="$( cd "$REPO_ROOT" … git ls-files --error-unmatch … )" <- INDEX
L157 self_stat="$( cd "$REPO_ROOT" … git ls-files -s … )"  <- INDEX
L163 self_text="$( cd "$REPO_ROOT" … git cat-file blob … )"<- BLOB
L355 wit_stat="$( cd "$REPO_ROOT" … git ls-files -s … )"   <- INDEX
L373 wit_text="$( cd "$REPO_ROOT" … git cat-file blob … )" <- BLOB
```

Cross-check on `main`, where the working-tree reads still live:

```
$ grep -n 'REPO_ROOT/\$rel\|REPO_ROOT/\$self_norm\|REPO_ROOT/\$self_wit\|REPO_ROOT/\$witness' conf-main.sh
3593:        "$REPO_ROOT/$rel" 2>/dev/null)" || self_row=""          <- the member's REACHED-BY row
3809:        elif [ ! -f "$REPO_ROOT/$self_wit" ]; then              <- the witness -f test
3883:        elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then   <- THE TEST THAT DECIDES
4001:    if [ ! -f "$REPO_ROOT/$witness" ]; then                     <- declared witness -f test
4010:        if LC_ALL=C grep -qF -- "$token" "$REPO_ROOT/$witness"; then        <- declared CALLER token
4021:        if LC_ALL=C grep -qF -- "$token" "$REPO_ROOT/$rel"; then            <- declared SUBJECT token

$ grep -n 'REPO_ROOT/\$rel\|REPO_ROOT/\$self_norm\|REPO_ROOT/\$self_wit\|REPO_ROOT/\$witness' conf-t445.sh
3466:  … (comment)
3606:  … (comment)
3681:  … (comment)
3808:  … (comment)
3973:  … (comment)
4194:  … (comment)
```

**Every one of the six survives only inside a comment on the tip.** So the CLAIM AS WRITTEN IN THE
HEADLINE — "zero working-tree reads of any **member, witness or declared witness**" — **HOLDS under
my own enumeration.**

## WHAT I FOUND THAT THE AUTHOR'S OWN TABLE DOES NOT LIST

The audit table in `evidence/00-index-vs-worktree-audit.md` has twelve rows and says row 2 (the
harness's own text) is the only working-tree read left. My enumeration finds **four** working-tree
reads on the tip, not one:

| # | line | read | classification |
|---|---|---|---|
| a | `:3221` | `[ ! -d "$gd" ]` — does `.softhouse/guards` exist on this host | **WORKING TREE**, not in the author's table at all |
| b | `:3229` | `[ ! -f "$conf" ]` | **WORKING TREE** (folded into the author's row 2) |
| c | `:3248` | `code="$(LC_ALL=C grep -v '^[[:space:]]*#' "$conf")"` | **WORKING TREE** — the author's row 2 |
| d | `:4401` | `code="$(LC_ALL=C grep -v '^[[:space:]]*#' "$conf")"` **inside `guard_registration_decisive_lines`** | **WORKING TREE — ADDED BY T445 ITSELF**, not in the table |

(a) can only fail closed — a missing directory is a refusal — so it is not a hole, but the audit's
own stated enumeration expression includes `[ -d ` and the table has no row for it.

(d) is a **second** working-tree read of the very quantity the guard already holds in `$code`. The
same function's own comment about `member_blob` says *"It is not re-read here: two reads of one
quantity are two chances to disagree."* T445 added exactly that, four lines into the change it was
making. Harmless in one process; it is the file's own stated discipline broken in the same commit.

## THE ONE THE AUTHOR KEEPS, AND WHY THE JUSTIFICATION FAILS

Rows (b)(c)(d) all read `$REPO_ROOT/.softhouse/conformance.sh` **from this host**, argued correct
because "the text that executes is the text on disk", and argued safe because a case attack on an
all-lowercase path "cannot be built on this host".

The first half is right. The second half is measured false in
`01-filesystem-fold-probe.txt`, `02-collision-order-probe.txt` and the driven arm `LONGS`.
See the review's finding **MAJOR-1**.
