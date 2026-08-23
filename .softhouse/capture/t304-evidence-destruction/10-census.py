#!/usr/bin/env python3
"""T304 census pass 1 — enumerate the SCRIPT population and every DESTRUCTIVE operation in it.

Population selector (printed with the result, per the brief: "not found" is a statement
about the search):

  git ls-files -z                       -> every TRACKED file in the repo
  keep if extension in {.sh,.py,.bash,.zsh,.pl,.rb}
     OR the first two bytes are "#!"    -> catches shebang scripts with no extension

Destructive-operation patterns are matched on LOGICAL lines (backslash continuations
joined) with whole-line shell comments dropped, the same normalisation T284 used.
"""
import os
import re
import subprocess
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

EXT = {".sh", ".py", ".bash", ".zsh", ".pl", ".rb"}

# Each pattern is (id, regex, what it destroys).
PATTERNS = [
    ("rm-rf",      r"\brm\s+(-[A-Za-z]*\s+)*-[A-Za-z]*[rR][A-Za-z]*\b", "recursive delete"),
    ("rm-plain",   r"\brm\s+(?!-[A-Za-z]*[rR])", "file delete"),
    ("rmtree",     r"shutil\.rmtree\s*\(", "python recursive delete"),
    ("os-remove",  r"\bos\.(remove|unlink|rmdir)\s*\(", "python file delete"),
    ("path-unlink",r"\.unlink\s*\(", "pathlib delete"),
    ("mv",         r"\bmv\s+", "move/overwrite"),
    ("shutil-move",r"shutil\.move\s*\(", "python move"),
    ("git-clean",  r"\bgit\s+clean\b", "git clean"),
    ("git-reset-hard", r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    ("git-checkout-dd", r"\bgit\s+checkout\s+--\s", "git checkout -- (discard worktree edits)"),
    ("git-restore", r"\bgit\s+restore\b", "git restore"),
    ("truncate",   r"\btruncate\s+-s\b", "truncate"),
    ("sed-i",      r"\bsed\s+(-[A-Za-z]+\s+)*-i\b|\bsed\s+-i", "in-place edit"),
    ("redirect",   r"(?<![0-9<>&|])>(?!>)\s*[\"']?[A-Za-z0-9_./$\{]", "output redirection (truncating)"),
    ("py-write",   r"open\s*\([^)]*[\"'][wa]b?[\"']", "python open for write"),
    ("write-text", r"\.write_text\s*\(|\.write_bytes\s*\(", "pathlib write"),
    ("tee",        r"\btee\b(?!\s+-a)", "tee (truncating)"),
    ("dd-of",      r"\bdd\s+[^\n]*\bof=", "dd of="),
]


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True).stdout
    return [f for f in out.decode("utf-8", "replace").split("\0") if f]


def is_script(rel):
    if os.path.splitext(rel)[1] in EXT:
        return True
    p = os.path.join(ROOT, rel)
    try:
        with open(p, "rb") as fh:
            return fh.read(2) == b"#!"
    except OSError:
        return False


def logical_lines(path):
    """Yield (first_physical_lineno, joined_logical_line) with whole-line # comments dropped."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.readlines()
    except OSError:
        return
    i = 0
    while i < len(raw):
        start = i + 1
        line = raw[i].rstrip("\n")
        while line.endswith("\\") and i + 1 < len(raw):
            i += 1
            line = line[:-1] + raw[i].rstrip("\n")
        i += 1
        if line.lstrip().startswith("#"):
            continue
        yield start, line


def main():
    files = tracked_files()
    scripts = [f for f in files if is_script(f)]
    hits = []
    for rel in scripts:
        for lineno, line in logical_lines(os.path.join(ROOT, rel)):
            for pid, rx, what in PATTERNS:
                if re.search(rx, line):
                    hits.append({"file": rel, "line": lineno, "pattern": pid,
                                 "what": what, "text": line.strip()[:400]})
    print("SELECTOR: git ls-files -z | ext in %s or first two bytes '#!'" % sorted(EXT))
    print("tracked files      : %d" % len(files))
    print("script population  : %d" % len(scripts))
    print("destructive hits   : %d" % len(hits))
    print()
    by_pat = {}
    for h in hits:
        by_pat.setdefault(h["pattern"], []).append(h)
    for pid, rx, what in PATTERNS:
        print("  %-16s %5d   (%s)" % (pid, len(by_pat.get(pid, [])), what))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence", "10-census-hits.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump({"tracked": len(files), "scripts": len(scripts), "hits": hits}, fh, indent=1)
    print("\nwrote %s" % out)


if __name__ == "__main__":
    sys.exit(main())
