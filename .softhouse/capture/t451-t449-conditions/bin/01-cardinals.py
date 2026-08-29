#!/usr/bin/env python3
"""T451 -- re-derive the two cardinals ready-tasks.py ships in its own comments.

C-T449-3: the comment at landed_index() says "542 handoff paths are tracked, 229 are
bare T###.md and 313 are the convention this program has used all month".  Source 2
`continue`s on anything not ending `.md`, so the population that source 2 MISSES is
(.md paths) - (paths that key), NOT (all paths) - (bare).

C-T449-5/4: the id_pattern docstring says t268's 24 paths are "every one" under
.softhouse/capture/t286-t268-retry/.

Everything below is counted from git, not from the review.
"""
import collections, subprocess, sys, re

def sh(*a):
    p = subprocess.run(a, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("git failed: %s\n%s" % (a, p.stderr))
    return p.stdout.splitlines()

for rev in ("b102875c", "main"):
    try:
        paths = sh("git", "ls-tree", "-r", "--name-only", rev, "--", ".softhouse/handoff")
    except SystemExit as e:
        print("%s: %s" % (rev, e)); continue
    bases = [p.rsplit("/", 1)[-1] for p in paths]
    md = [b for b in bases if b.endswith(".md")]
    # what source 2 ACTUALLY keys on: basename[:-3] -- so a bare `<id>.md` keys for the
    # id; anything else keys on a string that is not an id.  "bare" measured by the
    # shape of the ids this program uses.
    bare = [b for b in md if re.fullmatch(r"[Tt][0-9]+\.md", b)]
    a2 = [b for b in md if re.fullmatch(r"A2-[0-9]+\.md", b)]
    other_md = [b for b in md if b not in bare and b not in a2]
    ext = collections.Counter(("." + b.rsplit(".", 1)[-1]) if "." in b else "(none)"
                              for b in bases if not b.endswith(".md"))
    print("=== %s ===" % rev)
    print("  handoff paths tracked      : %d" % len(paths))
    print("  ending .md                 : %d" % len(md))
    print("  NOT ending .md (skipped)   : %d   %s"
          % (len(paths) - len(md), dict(ext.most_common())))
    print("  bare  T###.md   (keys)     : %d" % len(bare))
    print("  A2-<n>.md       (keys)     : %d" % len(a2))
    print("  other .md (source 2 INERT) : %d" % len(other_md))
    print("  542-229 (the shipped 313)  : %d  <-- counts the %d non-.md files as handoffs"
          % (len(paths) - len(bare), len(paths) - len(md)))
    print()

# ---- C-T449-4: t268's paths on main -------------------------------------------------
allp = sh("git", "ls-tree", "-r", "--name-only", "main")
pat = re.compile(r"(?<![0-9A-Za-z])t268(?![0-9A-Za-z])", re.I)
hits = [p for p in allp if any(pat.search(part) for part in p.split("/"))]
under = [p for p in hits if ".softhouse/capture/t286-t268-retry/" in p]
elsewhere = [p for p in hits if p not in under]
print("=== C-T449-4: paths on main with a COMPONENT naming t268 ===")
print("  total                                  : %d" % len(hits))
print("  under .softhouse/capture/t286-t268-retry/: %d" % len(under))
print("  NOT under it                            : %d" % len(elsewhere))
for p in elsewhere:
    print("      %s" % p)
