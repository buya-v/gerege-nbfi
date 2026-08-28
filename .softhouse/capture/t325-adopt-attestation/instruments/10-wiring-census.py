#!/usr/bin/env python3
"""T325 instrument 10 — IS THE GUARD ON THE PATH THAT EXECUTES?

P-45's rule, verbatim (`.softhouse/patterns.md`): "A test-only guard is not a
guard. ... verify the path that actually executes in CI/conformance calls it, not
merely that a test does."  T318 ended with the attestation wired into NOTHING and
said so in its own Unverified 5: "a proven instrument that protects nothing".
This instrument is the check that T325 did not repeat that.

It answers three questions, each with its selector printed beside its figure
(P-66: "'NOT FOUND' is a statement about the search, never about the world").

  1. For each of T318's six live damage gates: is it WIRED (an attestation call
     on the executed path), or SPECIFIED-ONLY (the change is stated in the T325
     handoff because the file belongs to another owner)?
  2. Re-run T318's own BLIND/COVERED criterion over the live-pipeline files: a
     cleanliness assertion is COVERED when a ref-reading or attestation companion
     sits within +/-40 lines.  The figure that matters is the DELTA against
     T318's measurement of the same files.
  3. Is every call site real code rather than a comment, and does the shipped
     file still parse (`zsh -n`)?

Exit 0 = every gate this task claims to have wired is verifiably on the executed
path.  Exit 1 = a claim in the handoff is not supported by the file.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FIRE = REPO / ".softhouse/bin/fire-program.sh"

# ---------------------------------------------------------------- selectors --
# T318's cleanliness-assertion selector, the subset that matched in the live
# pipeline, plus the prose form the SKILL.md gates use.
CLEAN_RE = re.compile(
    r"git\s+(?:-C\s+\S+\s+)?status[^\n|;&]*--porcelain"
    r"|git\s+(?:-C\s+\S+\s+)?status\s+(?:-s\b|--short\b)"
    r"|git\s+(?:-C\s+\S+\s+)?status(?!\s*(?:--porcelain|-s\b|--short\b))"
)
# T318's companion criterion, EXTENDED with the two names T325 adds. A gate is
# covered when something within reach can see a commit, a ref, an index bit or a
# declared writ -- not merely a working-tree comparison.
COMPANION_RE = re.compile(
    r"rev-parse|show-ref|for-each-ref|branch\s+--(?:contains|format)|reflog"
    r"|cat-file|merge-base|rev-list|git\s+log|\b[0-9a-f]{40}\b"
    r"|attest_run|attest_exit_protocol|repo-state-attest|wt_prune_blindspot_check"
)
WINDOW = 40

# T318's six live damage gates, verbatim from its handoff section
# "The live gates, named -- 6 distinct, 5 blind".
GATES = [
    dict(n=1, site=".claude/skills/softhouse-program/SKILL.md",
         anchor="`git status --porcelain` must come back empty",
         what="STEP 5.5 item 1 -- the driver's own exit protocol",
         claim="SPECIFIED-ONLY", owner="softhouse-program skill (outside T325's edit set)"),
    dict(n=2, site=".softhouse/bin/fire-program.sh",
         anchor="attest_exit_protocol",
         what="STEP 5.5's EXECUTABLE form (run_exit_guard)",
         claim="WIRED", owner="T325"),
    dict(n=3, site=".softhouse/bin/fire-program.sh",
         anchor='BS_OUT=$(wt_prune_blindspot_check "$W")',
         what="the worker-worktree rescue sweep",
         claim="WIRED", owner="T325"),
    dict(n=4, site=".claude/skills/softhouse/SKILL.md",
         anchor="`git status` — abort if the tree is dirty",
         what="pre-flight abort-if-dirty",
         claim="SPECIFIED-ONLY", owner="softhouse skill (outside T325's edit set)"),
    dict(n=5, site=".claude/skills/softhouse-plan/SKILL.md",
         anchor="`git status` — abort if dirty",
         what="pre-flight abort-if-dirty",
         claim="SPECIFIED-ONLY", owner="softhouse-plan skill (outside T325's edit set)"),
    dict(n=6, site=".softhouse/bin/lib-worktree-prune.zsh",
         anchor="wt_prune_check",
         what="the prune decision -- already covered by T324",
         claim="COVERED-BY-T324", owner="T324 (merged)"),
]

# The gate T325 adds that is not in T318's six: the fire's own pre-flight, which
# is the executable analogue of gates 4 and 5 on this host.
EXTRA = dict(n="4/5-exec", site=".softhouse/bin/fire-program.sh",
             anchor='attest_run "attest-preflight" survey',
             what="fire pre-flight BASELINE reading (FU-T318-5)",
             claim="WIRED", owner="T325")

fail = 0


def say(*a):
    print(*a)


def executed_line(path: Path, needle: str):
    """Return (lineno, line, is_comment) for the first NON-COMMENT occurrence,
    else the first occurrence at all.  A guard that appears only in a comment is
    exactly the failure this instrument exists to catch."""
    first = None
    for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if needle in line:
            stripped = line.lstrip()
            is_comment = stripped.startswith("#") or stripped.startswith(">")
            if first is None:
                first = (i, line.strip(), is_comment)
            if not is_comment:
                return (i, line.strip(), False)
    return first


say("=" * 72)
say("T325 instrument 10 -- WIRING CENSUS")
say("repo:", REPO)
say("=" * 72)
say()
say("--- 1. T318's six live damage gates, and what T325 did to each -----------")
say()
for g in GATES + [EXTRA]:
    p = REPO / g["site"]
    hit = executed_line(p, g["anchor"]) if p.exists() else None
    if hit is None:
        say(f"GATE {g['n']}: {g['claim']:<17} {g['site']}")
        say(f"         ANCHOR NOT FOUND: {g['anchor']!r} -- the census cannot confirm this gate exists.")
        if g["claim"] == "WIRED":
            say("         FAIL: a WIRED claim with no anchor in the file.")
            fail += 1
        continue
    ln, text, is_comment = hit
    say(f"GATE {g['n']}: {g['claim']:<17} {g['site']}:{ln}")
    say(f"         {g['what']}")
    say(f"         line: {text[:110]}")
    say(f"         owner: {g['owner']}")
    if g["claim"] == "WIRED" and is_comment:
        say("         FAIL: the only occurrence is inside a COMMENT -- not on the executed path.")
        fail += 1
    say()

say("--- 2. BLIND/COVERED over the live pipeline, T318's own criterion --------")
say()
say("SELECTOR: a cleanliness assertion is a line matching")
say("   git status [--porcelain|-s|--short|bare]")
say("COVERED means a companion matching")
say("   rev-parse|show-ref|for-each-ref|branch --contains/--format|reflog|")
say("   cat-file|merge-base|rev-list|git log|<40-hex>|attest_run|")
say("   attest_exit_protocol|repo-state-attest|wt_prune_blindspot_check")
say(f"sits within +/-{WINDOW} lines.  The last four names are T325's additions;")
say("everything else is T318's criterion unchanged.")
say()
say("WHERE I LOOKED (P-66): the four live-pipeline roots T318 narrowed to.")
scan = []
for pat in (".claude/skills/*/SKILL.md", ".softhouse/bin/*.sh", ".softhouse/bin/*.zsh",
            ".softhouse/conformance.sh", ".softhouse/guards/*.sh"):
    scan.extend(sorted(REPO.glob(pat)))
say(f"   {len(scan)} files:", ", ".join(str(p.relative_to(REPO)) for p in scan))
say()
say("WHERE I DID NOT LOOK: handoff prose (T318 counted 498 PROSE-REPORT hits;")
say("   they are evidence of record and per T114 are named and superseded, never")
say("   rewritten), untracked files in the live checkout, and /Users/buv/fineract")
say("   (the PINNED reference-oracle checkout, whose 45 gates are correct BECAUSE")
say("   they are pinned -- the asymmetry T318 argued and T325 preserves).")
say()
rows = []
for p in scan:
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if not CLEAN_RE.search(line):
            continue
        if "repo-state-attest" in str(p):
            continue  # the guard itself: its `git status` IS term T3
        lo, hi = max(0, i - WINDOW), min(len(lines), i + WINDOW + 1)
        covered = any(COMPANION_RE.search(l) for l in lines[lo:hi])
        rows.append((str(p.relative_to(REPO)), i + 1, covered, line.strip()[:90]))
blind = [r for r in rows if not r[2]]
say(f"FIGURE: {len(rows)} cleanliness assertions in the live pipeline; "
    f"COVERED {len(rows) - len(blind)}, BLIND {len(blind)}.")
say()
# SECOND COLUMN, because the +/-40 window measures PROXIMITY and not
# REACHABILITY, and T318 flagged that its error direction OVER-reports blindness
# (its Unverified 2).  A gate whose attestation sits 390 lines below it in the
# same function is scored BLIND by the window and is not, in fact, unattested.
# Both figures are printed so neither can be quoted alone.
file_has_attest = {}
for p2 in scan:
    txt = p2.read_text(errors="replace")
    file_has_attest[str(p2.relative_to(REPO))] = (
        "attest_run" in txt or "attest_exit_protocol" in txt or "repo-state-attest" in txt)
for r in rows:
    extra = ""
    if not r[2]:
        extra = ("   [same FILE does call the attestation elsewhere -- BLIND here is a"
                 " statement about the +/-40 window]" if file_has_attest.get(r[0]) else
                 "   [no attestation anywhere in this file]")
    say(f"   {'COVERED' if r[2] else 'BLIND  '}  {r[0]}:{r[1]}  {r[3]}{extra}")
say()
say("READ THE BLIND ROWS INDIVIDUALLY, NOT AS A TOTAL:")
say("  * SKILL.md:25 / SKILL.md:14 / SKILL.md:226 are the three gates T325 could")
say("    NOT edit.  They are BLIND, they are SUPPOSED to read BLIND here, and the")
say("    exact replacement text and its owner are in the T325 handoff.  A figure")
say("    that hid them would be the failure this program has recorded five times:")
say("    an unwired guard nobody names.")
say("  * fire-program.sh:762 is a PROSE mention inside a comment about sweep cost")
say("    -- a false positive of the selector, the same shape T318 found at")
say("    conformance.sh:1891.  Found by reading, not by tool.")
say("  * fire-program.sh:1582/1585 is the main-tree dirty check INSIDE")
say("    run_exit_guard.  Its attestation is `attest_exit_protocol` at the end of")
say("    the SAME function, ~390 lines below -- outside the window, on the same")
say("    executed path.  Stated rather than fixed by moving a comment next to it,")
say("    which would improve the metric and not the guard.")
say()

say("--- 3. does the shipped file still parse? --------------------------------")
rc = subprocess.run(["zsh", "-n", str(FIRE)], capture_output=True, text=True)
say(f"   zsh -n {FIRE.relative_to(REPO)} -> rc={rc.returncode} {rc.stderr.strip()}")
if rc.returncode != 0:
    fail += 1

say()
say("=" * 72)
if fail:
    say(f"VERDICT: FAIL -- {fail} claim(s) not supported by the shipped file.")
    sys.exit(1)
say("VERDICT: PASS -- every WIRED claim resolves to a non-comment line in the")
say("         shipped file, and the file parses.")
sys.exit(0)
