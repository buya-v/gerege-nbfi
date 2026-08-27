#!/usr/bin/env python3
"""T179 selftest — drives the classifier RED on both failure shapes and GREEN on
genuinely guarded code (P-22 + P-50: a selftest that only proves refusal proves half
the instrument).

Cases, all under fixtures/:

  RED — must be classified UNGUARDED, and T156's regex must DISAGREE (that
  disagreement is the whole finding, so it is asserted, not narrated):
    a1 red_prose_guard.py      guard words only inside string literals
    a2 red_guard_elsewhere.py  a real try/finally + a real atexit.register, neither
                               reachable from the mutation site

  GREEN — must NOT be UNGUARDED (over-broadness is a failure too):
    b1 green_try_finally.py    try/finally encloses the mutation
    b2 green_atexit.py         module-scope atexit.register on a live path
    b3 green_contextmanager.py locally defined restoring context manager
    b4 green_atomic.py         mkstemp + os.replace  (ATOMIC — needs no handler)
    b5 green_indirect.py       every in-file call of the writer is inside try/finally

  SCOPE — must be reported, not dropped:
    c  unknown_target.py       target is a parameter: scope UNKNOWN, verdict UNGUARDED

  T205 — the runtime-computed-constant fail-open (T203's F-2), both polarities:
    d  red_runtime_root.py     target is `os.path.join(RUNTIME_ROOT, …)` into the
                               live vector store.  Scored UNKNOWN before T205, so
                               `--enforce` exited 0 on a live-store truncation.
                               Must now be TRUSTED/UNGUARDED with tag STORE.
    e  chain_scratch_discard.py the POLARITY GUARD on that fix: a transitive
                               fragment that looks like a temp path must NEVER
                               excuse a site.  Asserted twice — as written, and
                               with a SCRATCH entry injected into the chain map.

  SHELL — must be REFUSED, symmetrically:
    s1 red_prose_guard.sh      `trap` only inside an echoed string
    s2 green_real_trap.sh      a real trap on every exit path
    Both REFUSED: without a shell parser this tool cannot tell them apart, and
    refusing both is the honest answer.  A tool that passed s2 and failed s1 would be
    claiming a discrimination it cannot perform.

Exit 0 = every expectation met.  Exit 1 = at least one failed (named).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import guard_classify as gc                                   # noqa: E402

FIX = os.path.join(HERE, "fixtures")

# T156's classifier, verbatim from
# .softhouse/capture/pathb/t149/t156-sweep-unguarded-mutators.py:58
T156_GUARD = re.compile(
    r"(?m)^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register|__exit__|contextmanager)")

CASES = [
    # (file, expected site verdict, expected scope, t156_says_guarded)
    ("red_prose_guard.py", gc.UNGUARDED, gc.TRUSTED, True),
    ("red_guard_elsewhere.py", gc.UNGUARDED, gc.TRUSTED, True),
    ("green_try_finally.py", gc.GUARDED_FINALLY, gc.TRUSTED, True),
    ("green_atexit.py", gc.GUARDED_PROCESS, gc.TRUSTED, True),
    ("green_contextmanager.py", gc.GUARDED_CM, gc.TRUSTED, True),
    ("green_atomic.py", gc.ATOMIC, gc.TRUSTED, False),
    ("green_indirect.py", gc.GUARDED_INDIRECT, gc.TRUSTED, True),
    ("unknown_target.py", gc.UNGUARDED, gc.UNKNOWN, False),
    # T205 (d): the shape that hid T57 and T8.  If this line ever reads
    # `gc.UNKNOWN` again, the fail-open is back.
    ("red_runtime_root.py", gc.UNGUARDED, gc.TRUSTED, False),
    # T205 (e): must NOT be excused, and must NOT be widened into TRUSTED either —
    # the chain has nothing trusted to say about it.
    ("chain_scratch_discard.py", gc.UNGUARDED, gc.UNKNOWN, False),
]

SHELL_CASES = ["red_prose_guard.sh", "green_real_trap.sh"]

MARKER = "T179-SITE"


def marked_line(src, fname):
    """The line each fixture is ABOUT, marked in the fixture itself.

    Picking "the first site in the file" would let a fixture pass for the wrong
    reason — the selftest must name the call site it is asserting about.
    """
    hits = [i + 1 for i, l in enumerate(src.splitlines()) if MARKER in l]
    if len(hits) != 1:
        raise AssertionError("%s: expected exactly one %s marker, found %d"
                             % (fname, MARKER, len(hits)))
    return hits[0]


def interesting_site(res, src, fname):
    ln = marked_line(src, fname)
    for s in res["sites"]:
        if s["line"] == ln:
            return s
    return None


def main():
    failures = []
    print("=== T179 selftest — both failure shapes, plus the over-broadness check")
    print("python parser: ast     shell parser: %s"
          % (gc.SHELL_PARSER or "NONE (refusal path)"))
    print()

    for fname, want_verdict, want_scope, t156_guarded in CASES:
        path = os.path.join(FIX, fname)
        if not os.path.exists(path):
            failures.append("%s: fixture missing" % fname)
            continue
        src = open(path, encoding="utf-8").read()
        res = gc.classify_python(fname, src)
        if res["refused"]:
            failures.append("%s: refused unexpectedly (%s)" % (fname, res["refused"]))
            continue
        site = interesting_site(res, src, fname)
        if site is None:
            failures.append("%s: no mutation site at the marked line %d (sites=%s)"
                            % (fname, marked_line(src, fname),
                               [(s["line"], s["scope"], s["verdict"])
                                for s in res["sites"]]))
            continue
        ok = site["verdict"] == want_verdict and site["scope"] == want_scope
        t156 = bool(T156_GUARD.search(src))
        ok_t156 = (t156 == t156_guarded)
        print("  %-26s parser=%-26s expected=%-26s %s"
              % (fname, site["verdict"], want_verdict, "OK" if ok else "**FAIL**"))
        print("  %-26s T156 regex says GUARDED=%-5s (expected %s)  %s"
              % ("", t156, t156_guarded, "OK" if ok_t156 else "**FAIL**"))
        print("  %-26s why: %s" % ("", site["why"]))
        if not ok:
            failures.append("%s: parser said %s/%s at line %d, expected %s/%s"
                            % (fname, site["verdict"], site["scope"], site["line"],
                               want_verdict, want_scope))
        if not ok_t156:
            failures.append("%s: T156 regex said GUARDED=%s, expected %s"
                            % (fname, t156, t156_guarded))
        print()

    for fname in SHELL_CASES:
        path = os.path.join(FIX, fname)
        src = open(path, encoding="utf-8").read()
        res = gc.classify_shell(fname, src)
        t156 = bool(T156_GUARD.search(src))
        ok = res["refused"] == gc.REFUSE_SHELL and not res["sites"]
        print("  %-26s parser=%-26s expected=%-26s %s"
              % (fname, res["refused"], gc.REFUSE_SHELL, "OK" if ok else "**FAIL**"))
        print("  %-26s T156 regex says GUARDED=%s" % ("", t156))
        if not ok:
            failures.append("%s: expected %s" % (fname, gc.REFUSE_SHELL))
        print()

    # The headline assertion of the whole task, stated as a check rather than prose:
    # on shape (a) the two classifiers must DISAGREE, or nothing has been fixed.
    src_a = open(os.path.join(FIX, "red_prose_guard.py"), encoding="utf-8").read()
    res_a = gc.classify_python("red_prose_guard.py", src_a)
    site_a = interesting_site(res_a, src_a, "red_prose_guard.py")
    disagree = bool(T156_GUARD.search(src_a)) and bool(site_a) and \
        site_a["verdict"] == gc.UNGUARDED
    print("  DISAGREEMENT CHECK on shape (a): T156=GUARDED, parser=UNGUARDED -> %s"
          % ("OK" if disagree else "**FAIL** — the new tool reproduces the old bug"))
    if not disagree:
        failures.append("shape (a): the two classifiers agree; the defect is not fixed")

    # And the guard against over-broadness: at least one GREEN case must be
    # non-UNGUARDED, or the tool is just a refusal machine (P-50).
    greens = []
    for fname, want, scope, _ in CASES:
        if fname.startswith("green_"):
            src = open(os.path.join(FIX, fname), encoding="utf-8").read()
            r = gc.classify_python(fname, src)
            s = interesting_site(r, src, fname)
            greens.append(bool(s) and s["verdict"] != gc.UNGUARDED)
    print("  OVER-BROADNESS CHECK: %d/%d green fixtures classified as guarded/atomic "
          "-> %s" % (sum(1 for g in greens if g), len(greens),
                     "OK" if all(greens) else "**FAIL**"))
    if not all(greens):
        failures.append("over-broadness: a genuinely guarded fixture was refused")

    # ------------------------------------------------------------------
    # T205 CHECK 1 — the DIFFERENTIAL that is the whole finding.  `red_runtime_root`
    # and `unknown_target` must NOT be classified alike: the first is now resolvable
    # through the chain, the second genuinely is not.  Asserting only "d is TRUSTED"
    # would pass if the chain had been widened until everything is TRUSTED.
    # ------------------------------------------------------------------
    def _site(fn):
        s = open(os.path.join(FIX, fn), encoding="utf-8").read()
        r = gc.classify_python(fn, s)
        return interesting_site(r, s, fn)

    d_site, c_site = _site("red_runtime_root.py"), _site("unknown_target.py")
    differ = (d_site["scope"] == gc.TRUSTED and c_site["scope"] == gc.UNKNOWN
              and "STORE" in d_site["target_tags"] and d_site["scope_via_chain"])
    print("  T205 DIFFERENTIAL: runtime-ROOT store write=%s/%s (chain=%s, tags=%s) vs "
          "unresolved param=%s -> %s"
          % (d_site["scope"], d_site["verdict"], d_site["scope_via_chain"],
             ",".join(d_site["target_tags"]), c_site["scope"],
             "OK" if differ else "**FAIL**"))
    if not differ:
        failures.append("T205: the chain did not separate a runtime-computed store "
                        "path from a genuinely unresolved one")

    # ------------------------------------------------------------------
    # T205 CHECK 2 — POLARITY, driven rather than asserted.  Inject a temp-looking
    # fragment into the resolver's chain map for the very name the fixture writes
    # through.  The chain probe then says SCRATCH; the site must STILL be UNKNOWN/
    # UNGUARDED.  Flipping `if scope2 == TRUSTED` to `if scope2 != UNKNOWN` in
    # classify_python makes this line print SANDBOX and fail.
    # ------------------------------------------------------------------
    _real = gc.ConstResolver

    class _InjectScratch(_real):
        def __init__(self, tree):
            _real.__init__(self, tree)
            self.chain["dest"] = "/tmp/t205-injected-scratch"

    fn_e = "chain_scratch_discard.py"
    src_e = open(os.path.join(FIX, fn_e), encoding="utf-8").read()
    try:
        gc.ConstResolver = _InjectScratch
        res_e = gc.classify_python(fn_e, src_e)
    finally:
        gc.ConstResolver = _real
    site_e = interesting_site(res_e, src_e, fn_e)
    # Sanity first (P-35): the injection must actually reach the probe, or this
    # check inspects nothing and is an ERROR, not a pass.
    injected_reached = gc.SCRATCH_RX.search(
        _InjectScratch(__import__("ast").parse(src_e)).chain.get("dest", "")) is not None
    held = injected_reached and site_e["scope"] == gc.UNKNOWN and \
        site_e["verdict"] == gc.UNGUARDED
    print("  T205 POLARITY (injected SCRATCH chain fragment must be DISCARDED): "
          "injection-live=%s site=%s/%s -> %s"
          % (injected_reached, site_e["scope"], site_e["verdict"],
             "OK" if held else "**FAIL**"))
    if not held:
        failures.append("T205: a transitive SCRATCH fragment excused a site — the "
                        "fix reintroduced the fail-open it exists to close")

    print()
    if failures:
        print("SELFTEST FAILED (%d):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("SELFTEST PASSED — %d python cases, %d shell refusals, both directions "
          "asserted" % (len(CASES), len(SHELL_CASES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
