#!/usr/bin/env python3
"""T449 -- would relaxing the REF-side path test from `leading` to `anywhere` fix
case K WITHOUT reintroducing the T339 defect the task was filed for?

`ref_content_evidence`'s own comment argues the ref side should be GENEROUS ("this is
the ref side, where the destructive error is demoting a line that still exists") and
then applies the STRICT owning anchor to the ref's paths.  This measures both.
"""
import importlib.util, re, sys

REPO = "/tmp/t449/fixture"
spec = importlib.util.spec_from_file_location("rt", "/tmp/t449/mods/rt_t350.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
T.set_repo(REPO)

SHIPPED = T.ref_content_evidence


def relaxed(tid, ref):
    """The same function with the REF-diff path test relaxed to `anywhere`."""
    anywhere, leading = T.id_pattern(tid)
    rc, out, err = T._run([T.GIT, "log", "--format=%H%x09%s", "main..%s" % ref])
    if rc is None or rc != 0:
        return None, "log failed"
    hits = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\t")
        if anywhere.search(subject):
            hits.append("commit %s subject %r" % (sha[:9], subject[:60]))
    rc2, out2, err2 = T._run([T.GIT, "diff", "--name-only", "main...%s" % ref])
    if rc2 is None or rc2 != 0:
        return None, "diff failed"
    for path in out2.splitlines():
        if any(anywhere.search(part) for part in path.split("/")):
            hits.append("path %s" % path)
    return hits, "relaxed"


CASES = [
    ("T339  the incident ref -- MUST STAY name-only",
     "T339", "softhouse/rescued-t339-base-20260828-080001"),
    ("T945  case K -- genuine work under T944's dir; SHOULD block",
     "T945", "softhouse/rescued-t945-base-20260829"),
    ("T900  case G's rescue ref -- owning path; already blocks on the ref side",
     "T900", "softhouse/rescued-t900-base-20260829"),
    ("T351  control -- real content, owning path",
     "T351", "softhouse/T351-progress-accounting"),
]
print("%-62s %-22s %s" % ("case", "SHIPPED (leading)", "RELAXED (anywhere)"))
print("-" * 110)
for label, tid, ref in CASES:
    a, _ = SHIPPED(tid, ref)
    b, _ = relaxed(tid, ref)
    print("%-62s %-22s %s" % (label[:62],
                              "CARRIES" if a else "name-only",
                              "CARRIES" if b else "name-only"))
    for h in (b or []):
        print("      relaxed hit: %s" % h)
