"""
T38 (F) -- no-regression check.

Revision 7 must not disturb what revisions 4, 5 and 6 fixed.  This script pins,
by SHA-256, the exact text blocks earlier rounds established, and checks them in
the WORKING COPY of the ADR against the same blocks extracted from the revision-6
text on `main`.  It is deliberately content-addressed rather than line-addressed,
because revision 7 inserts text above some of these blocks.

Run:  python3 .softhouse/reviews/t38-probe/t38_no_regression.py
"""
import hashlib
import re
import subprocess
import sys

ADR = "docs/adr/DEC-1-schedule-generator-adapter.md"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def rev6_text() -> str:
    return subprocess.run(["git", "show", f"main:{ADR}"],
                          capture_output=True, text=True, check=True).stdout


def working_text() -> str:
    return open(ADR).read()


def extract_fence(text: str, marker: str) -> str:
    """Return the fenced block that contains `marker`."""
    blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    hits = [b for b in blocks if marker in b]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly 1 fenced block containing "
                         f"{marker!r}, found {len(hits)}")
    return hits[0]


def extract_table(text: str, first_cell: str) -> str:
    """Return the contiguous markdown table whose body starts with `first_cell`."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("| `" + first_cell + "`"):
            j = i
            while j > 0 and lines[j - 1].startswith("|"):
                j -= 1
            k = i
            while k + 1 < len(lines) and lines[k + 1].startswith("|"):
                k += 1
            return "\n".join(lines[j:k + 1])
    raise SystemExit(f"table starting with {first_cell!r} not found")


CHECKS = [
    ("4.3.1 EMI re-adjust loop, steps 1-8 (T28/T29)",
     lambda t: extract_fence(t, "adjustCounter := 1")),
    ("4.3.2 three-operation per-period interest block (T31)",
     lambda t: extract_fence(t, "t1 := round_mc")),
    ("4.1.1 day-count definition table (T33)",
     lambda t: extract_table(t, "actualDaysInPeriod")),
]

PHRASES = [
    # the five/six-vector binding must keep gating conformance + cutover, NOT ratification
    "This is a UAT/cutover precondition, **not a ratification precondition**",
    # n is the related-period count
    "`relatedRepaymentPeriods.size()`",
    "**not `NumberOfRepayments`**",
    # the residual rule
    "diff        = ",
    # the growth factor
    "`1 +` the SUM of its interest periods' rate factors",
]


def main():
    old, new = rev6_text(), working_text()
    bad = 0
    print("=" * 78)
    print("F  NO-REGRESSION: revision 6 (main) vs the working copy")
    print("=" * 78)
    for label, fn in CHECKS:
        a, b = fn(old), fn(new)
        ok = a == b
        bad += 0 if ok else 1
        print(f"\n{label}")
        print(f"    revision 6 sha256 : {sha(a)}")
        print(f"    working   sha256 : {sha(b)}")
        print(f"    verdict          : {'IDENTICAL' if ok else 'CHANGED  <-- REGRESSION'}")
        if not ok:
            import difflib
            for ln in list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                                "rev6", "working", lineterm=""))[:40]:
                print("      " + ln)

    print("\n" + "-" * 78)
    print("Phrases that must survive verbatim:")
    for p in PHRASES:
        in_old, in_new = p in old, p in new
        ok = in_new
        bad += 0 if ok else 1
        print(f"    [{'OK ' if ok else 'GONE'}] (rev6: {'yes' if in_old else 'no'}) {p!r}")

    print("\n" + "-" * 78)
    print("`n` claims -- every occurrence of a sentence tying n to a count:")
    for txt, lbl in ((old, "rev6"), (new, "working")):
        hits = re.findall(r"n` is (?:the )?[^.]{0,80}", txt)
        uniq = sorted(set(h.strip() for h in hits))
        print(f"  {lbl}: {len(uniq)} distinct")
        for h in uniq:
            print(f"      {h}")

    print("\n" + "=" * 78)
    print("VERDICT:", "NO REGRESSION" if bad == 0 else f"{bad} REGRESSION(S)")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
