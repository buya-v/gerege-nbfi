#!/usr/bin/env python3
"""T318 instrument 10 — census of CLEANLINESS ASSERTIONS in this repo.

FU-T304-2 asks: how many gates, guards, exit protocols, review checklists and
instruments assert "the tree is undamaged" via `git status` (or `git diff
--quiet`, or similar)?

P-66 binds (patterns.md:1921, rule text): *"'NOT FOUND' is a statement about the
search, never about the world. P-62 says a refusal and a null control share an
observable; P-66 says an absence and an unsearched region share one too."*
So this instrument PRINTS ITS SELECTOR and PRINTS ITS SCOPE beside every figure.

SCOPE (stated, per P-66)
  S1  every file in `git ls-files` at HEAD of this worktree.
  S2  plus, named explicitly, the four skill files under `.claude/skills/`
      (they are inside S1; called out because the driver's own exit protocol
      lives there and a scope that missed it would miss the headline).
  NOT IN SCOPE, and named so the absence is a measurement not a default:
    - untracked files in the live checkout (`.claude/settings*.json`,
      `.softhouse/LOCK`, worker worktrees) — see instrument 11.
    - git hooks under `.git/hooks` (not tracked, not shipped).
    - anything in /Users/buv/fineract (the pinned reference-oracle checkout).

SELECTOR — CLEANLINESS ASSERTION (regexes applied per line, see PATTERNS below).

CLASSIFICATION
  EXEC-GATE     line is in an executable/script file, is not a comment, and the
                result STEERS CONTROL FLOW (assigned to a var later tested, or
                used in if/test/&&/||/exit). This is the population that can
                report SAFE on a committed clobber.
  EXEC-DISPLAY  in a script, not a comment, but the result is only printed.
                Uninformative, not load-bearing.
  EXEC-COMMENT  a comment line inside a script.
  PROSE-PROTOCOL  a .md/.json instruction telling a human or agent to run the
                check — a gate executed by an agent rather than by a shell.
                These bind exactly as hard as EXEC-GATE.
  PROSE-REPORT  a .md/.json line REPORTING a past result ("tree was clean").
                Not a gate; but every one of them is a claim inheriting the
                blind spot, so they are counted separately, not discarded.
"""
import json
import os
import re
import subprocess
import sys

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
REPO = os.path.realpath(REPO)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                      capture_output=True, text=True, check=True).stdout.strip()

# --- THE SELECTOR, printed beside every figure -----------------------------
PATTERNS = [
    ("status-porcelain", r"git\s+(?:-C\s+\S+\s+)?status[^\n|;&]*--porcelain"),
    ("status-short",     r"git\s+(?:-C\s+\S+\s+)?status\s+(?:-s\b|--short\b)"),
    ("status-bare",      r"git\s+(?:-C\s+\S+\s+)?status(?!\s*(?:--porcelain|-s\b|--short\b))"),
    ("diff-quiet",       r"git\s+(?:-C\s+\S+\s+)?diff[^\n|;&]*--quiet"),
    ("diff-exit-code",   r"git\s+(?:-C\s+\S+\s+)?diff[^\n|;&]*--exit-code"),
    ("diff-index",       r"git\s+(?:-C\s+\S+\s+)?diff-index\b"),
    ("diff-files",       r"git\s+(?:-C\s+\S+\s+)?diff-files\b"),
    ("ls-files-others",  r"git\s+(?:-C\s+\S+\s+)?ls-files[^\n|;&]*(?:--others|-m\b|--modified)"),
    ("clean-dry-run",    r"git\s+(?:-C\s+\S+\s+)?clean\s+[^\n|;&]*-n"),
    ("prose-clean-tree", r"(?:tree|working tree|worktree)\s+(?:is\s+|comes?\s+back\s+|came\s+back\s+)?(?:clean|EMPTY|empty)"),
]
COMPILED = [(n, re.compile(p)) for n, p in PATTERNS]

# a hit is a GATE if the same line, or a line within GATE_WINDOW after it,
# tests the result rather than merely printing it.
GATE_SIGNS = re.compile(
    r"(?:^|[^\w])(?:if\b|\[\[|\[\s|test\b|-z\b|-n\b|\|\|\s*(?:exit|die|fail|return)"
    r"|&&\s*(?:exit|die|fail|return)|exit\s+\d|return\s+\d|assert|FAIL|REFUS|abort|ERROR)"
)
DISPLAY_ONLY = re.compile(r"^\s*(?:echo|print|printf|log|cat)\b")
GATE_WINDOW = 6

SCRIPT_EXT = {".sh", ".py", ".zsh", ".bash", ".ps1"}
PROSE_EXT = {".md", ".json", ".txt", ".tsv", ".yml", ".yaml"}


def comment_prefix(path):
    return "#" if os.path.splitext(path)[1] in SCRIPT_EXT else None


def is_script(path, blob):
    ext = os.path.splitext(path)[1]
    if ext in SCRIPT_EXT:
        return True
    if blob.startswith("#!"):
        return True
    return False


def main():
    files = subprocess.run(["git", "ls-files"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout.split("\n")
    files = [f for f in files if f]
    # never census our own instruments -- they would inflate every figure
    OWN = ".softhouse/capture/t318-committed-clobber-blindness/"
    scanned = 0
    skipped_binary = 0
    hits = []
    for f in files:
        if f.startswith(OWN):
            continue
        p = os.path.join(REPO, f)
        try:
            with open(p, "r", encoding="utf-8", errors="strict") as fh:
                blob = fh.read()
        except (UnicodeDecodeError, OSError):
            skipped_binary += 1
            continue
        scanned += 1
        if "git status" not in blob and "git diff" not in blob \
           and "diff-index" not in blob and "diff-files" not in blob \
           and "clean" not in blob and "ls-files" not in blob:
            continue
        lines = blob.split("\n")
        script = is_script(f, blob)
        cp = comment_prefix(f)
        for i, line in enumerate(lines):
            for name, rx in COMPILED:
                if not rx.search(line):
                    continue
                stripped = line.strip()
                if script:
                    if cp and stripped.startswith(cp):
                        cls = "EXEC-COMMENT"
                    else:
                        window = "\n".join(lines[i:i + GATE_WINDOW])
                        if GATE_SIGNS.search(window) and not (
                                DISPLAY_ONLY.match(stripped) and not GATE_SIGNS.search(stripped)):
                            cls = "EXEC-GATE"
                        else:
                            cls = "EXEC-DISPLAY"
                else:
                    # prose: protocol (imperative / requirement) vs report (past tense)
                    low = stripped.lower()
                    imperative = any(k in low for k in (
                        "must", "abort if", "refuse", "required", "shall", "verify",
                        "check that", "should", "ensure", "before ", "gate", "-- abort"))
                    cls = "PROSE-PROTOCOL" if imperative else "PROSE-REPORT"
                hits.append({"file": f, "line": i + 1, "pattern": name,
                             "class": cls, "text": stripped[:220]})
                break  # one classification per line

    out = {
        "head": HEAD, "repo": REPO,
        "scope": {"tracked_files_total": len(files),
                  "scanned_utf8": scanned,
                  "skipped_undecodable": skipped_binary,
                  "excluded_own_instruments_prefix": OWN},
        "selector": {n: p for n, p in PATTERNS},
        "gate_window_lines": GATE_WINDOW,
        "hits": hits,
    }
    print(json.dumps(out, indent=1))

    # ---- summary to stderr so the JSON stays pipeable ----
    e = sys.stderr
    print("=" * 74, file=e)
    print("T318 INSTRUMENT 10 — CLEANLINESS-ASSERTION CENSUS", file=e)
    print("=" * 74, file=e)
    print(f"HEAD              {HEAD}", file=e)
    print(f"SCOPE             git ls-files = {len(files)} tracked files; "
          f"{scanned} read as UTF-8, {skipped_binary} undecodable/skipped", file=e)
    print(f"EXCLUDED          {OWN} (own instruments)", file=e)
    print("SELECTOR (printed beside the figure, per P-66):", file=e)
    for n, p in PATTERNS:
        print(f"    {n:20s} {p}", file=e)
    print("-" * 74, file=e)
    byclass = {}
    byclassfiles = {}
    for h in hits:
        byclass[h["class"]] = byclass.get(h["class"], 0) + 1
        byclassfiles.setdefault(h["class"], set()).add(h["file"])
    print(f"{'CLASS':16s} {'HITS':>6s} {'FILES':>6s}", file=e)
    for k in sorted(byclass, key=lambda x: -byclass[x]):
        print(f"{k:16s} {byclass[k]:6d} {len(byclassfiles[k]):6d}", file=e)
    print(f"{'TOTAL':16s} {len(hits):6d} {len({h['file'] for h in hits}):6d}", file=e)
    print("-" * 74, file=e)
    bypat = {}
    for h in hits:
        bypat[h["pattern"]] = bypat.get(h["pattern"], 0) + 1
    for k in sorted(bypat, key=lambda x: -bypat[x]):
        print(f"  pattern {k:20s} {bypat[k]:6d}", file=e)
    print("-" * 74, file=e)
    load_bearing = [h for h in hits if h["class"] in ("EXEC-GATE", "PROSE-PROTOCOL")]
    lb_files = sorted({h["file"] for h in load_bearing})
    print(f"LOAD-BEARING (EXEC-GATE + PROSE-PROTOCOL): {len(load_bearing)} hits "
          f"in {len(lb_files)} files", file=e)
    for f in lb_files:
        n = len([h for h in load_bearing if h["file"] == f])
        print(f"    {n:3d}  {f}", file=e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
