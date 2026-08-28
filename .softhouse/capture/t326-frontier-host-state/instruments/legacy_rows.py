#!/usr/bin/env python3
"""T326 -- THE RETIRED RESOLVER, kept HERE and deliberately NOT in the shipped census.

WHY IT LIVES IN THE DRIVE AND NOT BEHIND A `--legacy` FLAG ON THE CENSUS. The obvious way to
drive the old behaviour red is to give `census_dead_paths.py` a flag that restores it. That puts
a knob on a GRADED instrument which, if anyone ever passes it, reinstates a defect the whole task
exists to remove -- and the harness cannot stop a future caller from passing it. So the retired
resolver lives in the capture directory, where nothing graded can reach it.

WHAT IT REUSES AND WHAT IT REPLACES. It imports the SHIPPED census module and uses its corpus
selector, its literal regex and its `classify()` verbatim; the ONLY thing it substitutes is the
resolution predicate, restored to T316's `os.path.exists(root / literal)`. So the RED arm and the
GREEN arm differ in exactly one variable. If the shipped selector changes, this follows it, and
the drive keeps comparing like with like rather than against a frozen copy that has drifted.

EXIT: 0 rows printed; 2 refusal. Prints one `file | literal` row per line, sorted, in the same
shape as `rows.py`, so the drive's diffs are between comparable files.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
CENSUS = ROOT / ".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"


def load_census():
    if not CENSUS.is_file():
        print("ERROR: the shipped census is not at %s. This drive grades the SHIPPED selector,"
              % CENSUS, file=sys.stderr)
        print("ERROR: not a copy of it, so it cannot run. REFUSING (exit 2).", file=sys.stderr)
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("t316_census", str(CENSUS))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: legacy_rows.py <repo-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not (root / ".git").exists():
        print("ERROR: %s has no .git. REFUSING (exit 2)." % root, file=sys.stderr)
        return 2
    c = load_census()

    def resolves(path: str) -> bool:
        if (root / path).exists():
            return True
        stripped = path.rstrip(c.TRAILING_PUNCT)
        return bool(stripped) and stripped != path and (root / stripped).exists()

    rows = set()
    for rel in c.corpus(root):
        try:
            text = (root / rel).read_text(errors="replace")
        except OSError as exc:
            print("ERROR: unreadable corpus member %s: %s" % (rel, exc), file=sys.stderr)
            return 2
        for m in c.LITERAL_RE.finditer(text):
            lit = m.group(2)
            path = lit[lit.find(".softhouse/"):]
            if c.classify(path) != "CONCRETE":
                continue
            if not resolves(path):
                rows.add("%s | %s" % (rel, path))
    if not rows:
        print("ERROR: zero rows under the legacy resolver. That is a selector failure, not a",
              file=sys.stderr)
        print("ERROR: clean tree. REFUSING (exit 2).", file=sys.stderr)
        return 2
    for r in sorted(rows):
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
