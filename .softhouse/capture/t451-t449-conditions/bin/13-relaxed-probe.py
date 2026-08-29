#!/usr/bin/env python3
"""T451 -- C-T449-2.  DRIVE THE PROPOSED PATCH, do not paste it.

T449 proposed one word: on the ref side, relax the path test from `leading` (the OWNING
anchor) to `anywhere`, and verified on four hand-built refs that it fixes case K while
leaving the T339 incident ref `name-only`.  That verification is true and it is not
enough, because it never asked what the relaxation costs on refs that are NOT case K.

This instrument builds the relaxed variant BY EDITING THE SHIPPED BYTES (so the thing
driven is the proposal, not a paraphrase of it) and drives BOTH variants over the whole
fixture -- attacks AND the cross-task shapes the proposal was never shown.

usage: 13-relaxed-probe.py <fixture-dir> <green.py>
"""
import importlib.util, os, re, sys, hashlib

FIX, GREEN = sys.argv[1], sys.argv[2]
WORK = "/tmp/t451/mods"
os.makedirs(WORK, exist_ok=True)

src = open(GREEN, encoding="utf-8").read()

# The one test under discussion, in `ref_content_evidence`: the ref's OWN diff paths.
NEEDLE = """        parts = path.split("/")
        if any(leading.match(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
RELAX = """        parts = path.split("/")
        if any(anywhere.search(part) for part in parts):   # T449's PROPOSED RELAXATION
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
if src.count(NEEDLE) != 1:
    sys.exit("REFUSING TO REPORT A DRIVE THAT DID NOT RUN: the ref-side path test is not "
             "where this expects it in %s (%d matches). A patch that cannot be planted "
             "proves nothing -- P-22." % (GREEN, src.count(NEEDLE)))
relaxed_path = os.path.join(WORK, "rt_relaxed.py")
with open(relaxed_path, "w", encoding="utf-8") as fh:
    fh.write(src.replace(NEEDLE, RELAX))
print("PLANTED the proposed relaxation: `leading.match` -> `anywhere.search` on the ref's")
print("own diff paths, and NOWHERE else.  1 site, verified unique before writing.")
print("  shipped  %s  sha256 %s" % (GREEN, hashlib.sha256(src.encode()).hexdigest()[:16]))
print("  relaxed  %s  sha256 %s\n"
      % (relaxed_path,
         hashlib.sha256(open(relaxed_path, "rb").read()).hexdigest()[:16]))

CASES = [
    ("A/T339", "T339", "softhouse/T339-base",
     "the INCIDENT ref -- MUST STAY name-only under both"),
    ("K/T945", "T945", "softhouse/T945-t944-conditions",
     "case K -- work under another id's condition dir"),
    ("K2/T946", "T946", "softhouse/T946-t944-conditions",
     "case K with the task branch still parked"),
    ("R/T980", "T980", "softhouse/T980-work",
     "T981's committed REVIEW OF T980 -- subject names T980, so BOTH already refuse"),
    ("R2/T982", "T982", "softhouse/T982-work",
     "a SWEPT reviewer worktree: boilerplate subject, path is T983's review of T982"),
    ("S/T990", "T990", "softhouse/T990-shared-file",
     "rescue ref touching only a SHARED file -- names no id at all"),
    ("E/T351", "T351", "softhouse/T351-progress-accounting",
     "must-block control -- real owning content"),
    ("G/T900", "T900", "softhouse/T900-work",
     "case G -- rescue ref owning the work, branch parked"),
]


def drive(path, tag):
    out = {}
    for i, (label, tid, branch, _) in enumerate(CASES):
        spec = importlib.util.spec_from_file_location("%s_%d" % (tag, i), path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.set_repo(FIX)
        kind, _text = m.branch_wip(branch, tid)
        act = "REFUSE" if m.reconcile_action(kind).startswith("REFUSE") else "demote"
        out[label] = (kind, act)
    return out


S = drive(GREEN, "ship")
R = drive(relaxed_path, "relax")
print("%-8s %-58s %-24s %s" % ("case", "what it is", "SHIPPED (leading)", "RELAXED (anywhere)"))
print("-" * 118)
for label, tid, branch, what in CASES:
    sk, sa = S[label]
    rk, ra = R[label]
    mark = "   <== the relaxation CHANGES this" if (sk, sa) != (rk, ra) else ""
    print("%-8s %-58s %-14s %-9s %-14s %s%s"
          % (label, what[:58], sk, sa, rk, ra, mark))
print()
print("""VERDICT ON THE PROPOSED PATCH -- NOT LANDED, and the reason is measured, not felt.

  * It buys K and K2.  It costs R2.  Both are constructible and NEITHER is live on this
    repo today: over all 705 live refs and all 84 (id, other-ref) pairs the reconciler
    could be asked about, the relaxation adds EXACTLY 0 carriers
    [out/21-realrepo-evidence.txt, section B].  It is a trade between two hypotheticals.

  * The tie is broken by the one REAL instance of case K's shape in the live store, and
    THE SHIPPED ANCHOR ALREADY CATCHES IT.  T428's swept ref carries
        .softhouse/capture/t421-t406-conditions/out/T428-S01-counters.psql
    -- T428's work, under T421's directory, exactly case K -- and it reads CARRIES under
    `leading`, because a path COMPONENT includes the FILENAME and this program names the
    file for its owner.  T449's case K is invisible only because its fixture filename is
    `work.txt`, which names nobody.  The premise that the OWNING anchor cannot see work
    filed under another id's directory is refuted by the only real example of it.

  * The shape the relaxation WOULD newly expose is the dominant one: 69 of 84 pairs are
    name-only today and the commonest cross-task object in this program is one task's
    review of another.  R2 is a sweep away.

So the anchor stays and the COMMENT was what was wrong -- it claimed a polarity the code
never had.  What IS landed is the truthfulness repair: a path that MENTIONS the id is now
reported, named and declined, where the note used to state that no such path existed.""")
