#!/usr/bin/env python3
"""T292 -- R-VPA, FAIL-CLOSED BY CONSTRUCTION.  Successor to T259's rule; the PRE file at
`.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py` (blob 86f4285)
is COMMITTED EVIDENCE of what T259 shipped and is NOT edited (T114/T176).

=====================================================================================
WHY THIS FILE EXISTS AND WHY IT IS NOT A SIXTH SHAPE-PATCH
=====================================================================================
Five repairs of the same fail-open lost the same way (P-91: "a guard phrased as a STRUCTURAL
PATTERN over the shape of its input can always be re-nested one level out, so enumerating shapes
that COUNT and refusing the unmatched is a losing method no matter how carefully each shape is
chosen").  T259 -> T268 -> T281 -> T286 -> T291.  T291 beat T286's phrasing -- "a record is a row
reached through a list" -- with TWO CHARACTERS, by wrapping a header dict in `[ ]`.

THE DIAGNOSIS THE CHAIN NEVER WROTE DOWN.  One predicate, `walk_rows`, was doing two jobs whose
fail-closed directions are OPPOSITE:

    DETECTION -- "where might an affirmative verdict be hiding?"   wants to be MAXIMALLY GENEROUS.
    COVERAGE  -- "did this document actually grade anything?"      wants to be MAXIMALLY STRICT.

T268 widened `walk_rows` to fix DETECTION (its F-3), and thereby widened COVERAGE, which is how a
header became a row.  T286 narrowed it to fix COVERAGE, and lost one bracket further out.  Every
link in the chain TRADED one against the other because both were reading the same number.  That is
not five workers being careless; it is a structural impossibility of the shared predicate.

=====================================================================================
THE FORMULATION.  COVERAGE IS CONSTRUCTED, NOT RECOGNISED.
=====================================================================================
Coverage is no longer a count of things the rule RECOGNISED in the document's shape.  It is the
WITNESS SET the rule ACCUMULATED while succeeding at grading:

    W(D,R) = { (path, key, value) : value is a JSON boolean leaf of D
                                    and R classifies key as PREDICATE }

R is the committed, external `boolean-key-register.json`.  W is computed by a TOTAL traversal of
the JSON value grammar (object | array | string | number | true | false | null): every production
is handled by name and anything outside the grammar RAISES, so there is no "shape the rule did not
recognise" that could be silently skipped.

    GREEN  <=>  W is NON-EMPTY  and no refusal fired.

and `|W| >= 1` is a POST-CONDITION CHECKED IN CODE immediately before the exit code is computed --
not an emergent property of a walk, and not an `assert` (which `PYTHONOPTIMIZE=2` would delete).

**THEOREM (container-blindness).**  Let T be any CONTAINER-ONLY rewriting of D: wrap a value in a
list; wrap it in an object under a fresh key; re-nest to any depth; promote the root into a list;
turn `{k: v}` into `[{k: v}]`; any composition of these.  T changes no leaf and adds or removes no
registered predicate key.  Then W(T(D),R) and W(D,R) have the same cardinality and the same
multiset of (key, value) pairs; only the `path` component differs.

    PROOF.  W's membership test reads exactly two things: (a) is this value a `bool` LEAF, and
    (b) does R classify its key as PREDICATE.  Neither consults container structure.  The traversal
    is total, so every leaf of T(D) is reached iff it is a leaf of D, and T preserves the leaf
    multiset by hypothesis.  []

    COROLLARY -- THE BRACKET IS POWERLESS.  T291's X2 / X3 / X4 / X7 are container-only rewritings
    of H1.  W(H1) is empty, so W(X_i) is empty, so all five REFUSE.  The bracket cannot manufacture
    coverage because coverage never looks at brackets.

    CONTRAST -- WHY THE LOSING FORMULATION HAD TO LOSE.  T286's coverage metric was
    |{dicts reached through a list}|, which READS CONTAINER STRUCTURE.  Any such metric is by
    definition NOT invariant under container-only rewriting, and container-only rewritings are an
    infinite family that costs the attacker two characters per member.  A shape-patch removes
    finitely many members of an infinite family.  P-91 is a theorem, not an observation.

**THEOREM (the irreducible floor).**  Under this formulation the ONLY way to raise coverage is to
write a boolean leaf under a registered PREDICATE key -- that is, to ASSERT A FACT.  No rule whose
inputs are (D, R) can distinguish a fabricated assertion from a true one, because a fabricated
`{"cells":[{"P1_x": true, "verdict": "PASS"}]}` and a true one are BYTE-IDENTICAL as inputs.  The
forgery floor is therefore where any container-blind rule must stop, and this rule stops exactly
there -- and prints every witness path it counted, so the forgery is NAMED in the transcript
rather than merely permitted.  []

=====================================================================================
WHAT IS **NOT** CLOSED, MEASURED RATHER THAN ASSERTED (T291 F-T291-2 / guard #10)
=====================================================================================
T286's guard #10 claims to close "the evasion of moving the affirmative word out of the records and
into a header".  T291 measured that claim FALSE for the list phrasing.  **This rule does not
restore that claim, because the claim is unachievable by any container-blind rule, and the proof is
in this program's own committed evidence:**

    T291's X5 header      {"summary": [{"verdict": "AS PREDICTED"}], "cells": [ ...refuted... ]}
    classify-t229.json    {"cells": [ {"id": "...B301", "verdict": "AS PREDICTED"},  ...refuted... ]}
                                       ^ carries NO predicate boolean: the P-keys are ABSENT BY
                                         DESIGN on the three RESCUED_BY_SITE3 rows (T259, denominator 6)

Both are "an affirmative verdict in an object that carries no predicate boolean, in a document
where some other object records a false predicate".  They are the SAME SHAPE.  Measured, by
`probe/census_real_corpus.py`: classify-t229.json contains **5** such affirmations (3 cells +
2 calibration) and classify-t219.json contains **0**.  Gating this counter therefore turns
COMMITTED, CORRECT evidence RED on three rows whose emptiness is deliberate.  So it ships as a
CENSUS COUNTER in the probe line (`headerAffirmations`), printed on every run, gating nothing --
and this docstring says so, which is the whole difference between this and guard #10, whose stated
scope exceeded its measured scope.  Separating X5 from classify-t229.json requires an EXTERNAL
declaration of which containers hold graded records; that changes `boolean-key-register.json`'s
contract, which is outside T292's `files_hint`.  Specified in the handoff, not done here.

=====================================================================================
GUARDS
=====================================================================================
 G1  UNCLASSIFIED VERDICT WORD under a verdict-named key -- REFUSAL.  (T259, unchanged.)
 G2  UNCLASSIFIED BOOLEAN KEY -- REFUSAL.  `^P[0-9]+_` auto-classifies; everything else must be in
     the register.  (T259, unchanged.)
 G3  NIL COVERAGE -- REFUSAL, REDEFINED: the witness set W is empty.  This is the inversion.
 G4  ACKNOWLEDGEMENTS PINNED TO sha256 -- a void block is a REFUSAL.  (T259 + T286's R3.)
 G5  UNACKNOWLEDGED DISAGREEMENT -- REFUSAL.  A false predicate and an affirmative verdict in the
     SAME OBJECT.  Now evaluated over EVERY object at EVERY depth, not only dicts in top-level
     lists -- the DETECTION side, generous, as it should be.
 G6  A FALSE PREDICATE WITH NO READABLE DISPOSITION -- REFUSAL.  An object recording a predicate
     `false` must also carry a verdict word this rule can classify.  Closes "rename the verdict KEY
     to `conclusion` so the affirmation is invisible": you cannot hide the disposition of a record
     that admits a refutation.
 G7  READ INTEGRITY -- every one of these is exit 2, no probe line:
       - duplicate key anywhere in any document (json's last-wins silently drops a recorded `false`)
       - `NaN` / `Infinity` / `-Infinity` JSON constants
       - ANY `float` surviving the parse (checked by TYPE ABSENCE, not by enumerating constants)
       - a byte sequence that is not UTF-8
     Money is integer minor units and no floating point may enter a monetary code path, including
     intermediate calculation (CLAUDE.md).  Nothing monetary is computed HERE, but `load_json` is
     the helper the next instrument copies, and T291 measured NaN/Infinity entering a GREEN run AS
     FLOATS.

 READ ONCE.  The bytes are read exactly once; the sha is taken of that buffer and the same buffer
 is parsed, so the acknowledgement pin covers the bytes that were actually GRADED (T291 F-T291-7,
 which was observable as an indefinite HANG on a FIFO -- two opens, second blocks forever).

 UTF-8 EXPLICITLY.  `read_bytes()` then `.decode("utf-8")`; never `read_text()`, which reads the
 host's locale.  Mongolian names are Cyrillic and are three fields -- ovog, patronymic, given name
 (CLAUDE.md) -- so this program WILL meet a non-ASCII payload.  stdout is reconfigured to UTF-8 so
 the guard cannot die printing what it read.

EXIT CODES -- never conflated (P-81: an error is not a measured negative):
    0  GREEN    -- W non-empty; no guard fired.
    1  REFUSED  -- a REAL measured negative.  Probe line PRESENT.
    2  ERROR    -- usage, IO, parse, read-integrity.  Probe line ABSENT.  Never used for an absence.
       `--help` and every other argparse exit are 2, not 0 (T286's fourth fail-open).

PROBE LINE.  Last line, always, on 0 and 1 and never on 2.  T259's NINE fields keep their names,
values and positions so any substring reader on `main` is unaffected; T292's fields are APPENDED.
P-84: test the line's PRESENCE first, then its VALUE -- "exit 2 with no probe line" is the guard
working, and several exit-2 paths run before the probe could print.
"""
import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T259-VPA:"
T256 = HERE / ".." / "t256-verdict-predicate"

AFFIRMATIVE = {"AS PREDICTED", "AS_PREDICTED", "AS-PREDICTED", "PASS", "PASSED", "OK",
               "CONFIRMED", "REPRODUCED", "GREEN", "HELD", "AGREES", "MATCHED"}
NEGATIVE = {"REFUTED", "FAIL", "FAILED", "DIFFERS", "RED", "MISSING", "BROKEN", "VIOLATED",
            "THREW", "SKIPPED", "NOT RUN", "NOT_RUN", "INADMISSIBLE"}


class RuleError(Exception):
    """Every ERROR path raises this. It becomes exit 2 with NO probe line, never exit 1."""


# ---------------------------------------------------------------------------------------------
# READING.  Fail-closed on encoding, duplicate keys, and every float.
# ---------------------------------------------------------------------------------------------

def _no_duplicate_keys(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise RuleError(
                "duplicate key %r in a JSON object. json.loads keeps the LAST value, which "
                "silently drops a recorded predicate. A repeated key is unreadable, not "
                "last-wins." % (k,))
        seen[k] = v
    return seen


def _refuse_constant(tok):
    raise RuleError(
        "JSON constant %r. NaN/Infinity are FLOATS and money is integer minor units; no "
        "floating point may enter any code path here, including intermediate calculation." % (tok,))


def _assert_no_float(v, path="$"):
    """TYPE ABSENCE, not constant enumeration. Total over the value grammar; anything outside it
    is a refusal, which is what makes the traversal fail-CLOSED on an unrecognised value."""
    if isinstance(v, bool):
        return
    if isinstance(v, float):
        raise RuleError("a float survived the parse at %s: %r" % (path, v))
    if isinstance(v, (str, int, Decimal)) or v is None:
        return
    if isinstance(v, dict):
        for k, x in v.items():
            if not isinstance(k, str):
                raise RuleError("non-string object key at %s: %r" % (path, k))
            _assert_no_float(x, path + "." + k)
        return
    if isinstance(v, list):
        for i, x in enumerate(v):
            _assert_no_float(x, path + "[%d]" % i)
        return
    raise RuleError("value outside the JSON grammar at %s: %s" % (path, type(v).__name__))


def read_once(path: Path):
    """Read the bytes EXACTLY ONCE; hash that buffer; parse that buffer. Returns (sha256, doc)."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuleError("cannot read %s: %s: %s" % (path, type(exc).__name__, exc))
    sha = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuleError("%s is not UTF-8: %s" % (path, exc))
    try:
        doc = json.loads(text, parse_float=Decimal,
                         parse_constant=_refuse_constant,
                         object_pairs_hook=_no_duplicate_keys)
    except RuleError:
        raise
    except ValueError as exc:
        raise RuleError("%s is not parseable JSON: %s" % (path, exc))
    _assert_no_float(doc)
    return sha, doc


def load_json(path: Path):
    return read_once(path)[1]


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise RuleError("no .git ancestor of " + str(HERE))


# ---------------------------------------------------------------------------------------------
# TOTAL TRAVERSAL.  Every object, every string, at every depth, through every container.
# ---------------------------------------------------------------------------------------------

def walk_objects(v, path="$"):
    """Yield (path, object) for EVERY JSON object anywhere in the document, root included.

    This is the DETECTION side and it is deliberately total: there is no container shape it does
    not descend, so no affirmative verdict can be hidden from it by re-nesting. It is NOT the
    coverage metric -- coverage is the witness set, below."""
    if isinstance(v, dict):
        yield path, v
        for k, x in v.items():
            yield from walk_objects(x, path + "." + k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk_objects(x, path + "[%d]" % i)


def walk_strings(v, path="$"):
    """Yield (path, kind, string) for every string anywhere, as an object KEY or as a value.
    Keys are included because T286's guard #10 was about an affirmation moved into a mapping key."""
    if isinstance(v, dict):
        for k, x in v.items():
            yield path + ".<key>" + k, "key", k
            yield from walk_strings(x, path + "." + k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk_strings(x, path + "[%d]" % i)
    elif isinstance(v, str):
        yield path, "value", v


def is_verdict_key(k: str) -> bool:
    kl = k.lower()
    return "verdict" in kl or kl == "status" or kl.endswith("status")


def classify_verdict(v: str):
    u = str(v).strip().upper()
    if u in AFFIRMATIVE:
        return "AFFIRMATIVE"
    if u in NEGATIVE:
        return "NEGATIVE"
    return "UNCLASSIFIED"


def key_class(reg, key: str):
    if key.startswith("P") and "_" in key:
        head = key.split("_", 1)[0]
        if len(head) > 1 and head[1:].isdigit():
            return "PREDICATE", "auto: matches ^P[0-9]+_"
    ent = reg.get("keys", {}).get(key)
    if ent is None:
        return "UNCLASSIFIED", "not in boolean-key-register.json"
    if not isinstance(ent, dict) or "class" not in ent:
        raise RuleError("register entry for %r is not an object with a `class`" % (key,))
    return ent["class"], ent.get("reason", "")


# ---------------------------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.files = 0
        self.objects = 0
        self.predicates = 0
        self.disagreements = 0
        self.acknowledged = 0
        self.unacknowledged = 0
        self.unclassified_keys = 0
        self.unclassified_verdicts = 0
        self.void_acks = 0
        self.mute_refutations = 0        # G6
        self.header_affirmations = 0     # census only -- see the docstring
        self.witness = []                # [(path, key, value)] -- THE constructed coverage
        self.nil_files = 0               # files that yielded NO witness -- PER FILE, see below
        self.lines = []

    # WHY PER FILE, AND NOT ACROSS THE BATCH.  T268's F-1 -- the SECOND fail-open in this
    # lineage -- was exactly this: coverage measured per file, gated globally, so one populated
    # file switched the refusal off for every other file in the same invocation. The first draft
    # of THIS file reproduced it (`if not rep.witness` after each file is order-dependent: put
    # the real evidence first and an empty header file beside it never refuses). Recorded rather
    # than tidied away, because the point of this directory is that the defect is easy to write.

    def say(self, s=""):
        self.lines.append(s)


def load_registers(reg_path: Path, ack_path: Path):
    reg = load_json(reg_path)
    ack = load_json(ack_path)
    if not isinstance(reg, dict) or not isinstance(ack, dict):
        raise RuleError("register and acknowledgements must each be a JSON object")
    if reg.get("autoPredicatePattern") != "^P[0-9]+_":
        raise RuleError("unexpected autoPredicatePattern in register; refusing to guess")
    return reg, ack


def acks_for(ack, rel: str, sha: str, rep: Report):
    out = {}
    blocks = ack.get("acknowledgements", [])
    if not isinstance(blocks, list):
        raise RuleError("`acknowledgements` must be a list")
    for blk in blocks:
        if not isinstance(blk, dict) or "file" not in blk or "sha256" not in blk:
            raise RuleError("an acknowledgement block lacks `file` or `sha256`")
        if blk["file"] != rel:
            continue
        if blk["sha256"] != sha:
            rep.void_acks += 1
            rep.say("  !! ACKNOWLEDGEMENT BLOCK VOID -- registered for sha256 %s" % blk["sha256"])
            rep.say("     but the graded bytes are  sha256 %s" % sha)
            rep.say("     The evidence was edited after the acknowledgement was written, OR the "
                    "acknowledgement")
            rep.say("     names the wrong bytes. Either way it does NOT apply. T114/T176.")
            continue
        gp = blk.get("gradedProposition", "")
        for r in blk.get("rows", []):
            out[(r["id"], r["predicate"])] = {**r, "gradedProposition": gp}
    return out


def check_file(path: Path, reg, ack, rep: Report) -> None:
    root = repo_root()
    try:
        rel = str(path.resolve().relative_to(root))
    except ValueError:
        rel = str(path.resolve())

    sha, doc = read_once(path)          # ONE read. The pin covers the graded bytes.
    witness_at_entry = len(rep.witness)
    rep.files += 1
    rep.say("FILE %s" % rel)
    rep.say("     sha256 %s   (of the bytes that were PARSED, one read)" % sha)
    applicable = acks_for(ack, rel, sha, rep)

    witnessed_objects = set()

    for opath, obj in walk_objects(doc):
        rep.objects += 1
        label = opath
        for k in ("id", "cal", "cell", "name"):
            if k in obj and isinstance(obj[k], str):
                label = "%s:%s" % (opath, obj[k])
                break
        rid = obj.get("id") or obj.get("cal") or opath

        verdicts = {k: v for k, v in obj.items() if is_verdict_key(k) and isinstance(v, str)}
        vclasses = {k: classify_verdict(v) for k, v in verdicts.items()}
        for k, cls in vclasses.items():
            if cls == "UNCLASSIFIED":
                rep.unclassified_verdicts += 1
                rep.say("  REFUSED  %s: verdict key %r has value %r, which is"
                        % (label, k, verdicts[k]))
                rep.say("           in neither the AFFIRMATIVE nor the NEGATIVE vocabulary. A "
                        "verdict word this")
                rep.say("           rule cannot read is not a pass -- register it or rename it.")

        false_predicates = []
        for k, v in obj.items():
            if not isinstance(v, bool):
                continue
            cls, why = key_class(reg, k)
            if cls == "UNCLASSIFIED":
                rep.unclassified_keys += 1
                rep.say("  REFUSED  %s: boolean key %r is unclassified. Add it to "
                        "boolean-key-register.json" % (label, k))
                rep.say("           as PREDICATE or DESCRIPTIVE, with a reason. Guessing is how "
                        "P2 got past.")
                continue
            if cls != "PREDICATE":
                continue
            # ---- THE WITNESS.  Coverage is accumulated HERE, by succeeding at a grading,
            #      and nowhere else.  No container shape contributes to it.
            rep.predicates += 1
            rep.witness.append(("%s.%s" % (opath, k), k, v))
            witnessed_objects.add(opath)
            if v is False:
                false_predicates.append((k, why))

        affirm = [k for k, c in vclasses.items() if c == "AFFIRMATIVE"]

        # G6 -- a record that admits a refutation must state a disposition this rule can READ.
        if false_predicates and not vclasses:
            pass
            rep.say("  REFUSED  %s: records predicate(s) %s = false and carries NO verdict-named"
                    % (label, ", ".join(k for k, _ in false_predicates)))
            rep.say("           key at all. A refuted record with no readable disposition cannot "
                    "be graded;")
            rep.say("           renaming `verdict` to something this rule does not read is not a "
                    "pass.")
        elif false_predicates and not any(c in ("AFFIRMATIVE", "NEGATIVE")
                                          for c in vclasses.values()):
            rep.mute_refutations += 1
            rep.say("  REFUSED  %s: records a false predicate and every verdict word on it is "
                    "UNCLASSIFIED." % label)

        if false_predicates and affirm:
            for pk, _why in false_predicates:
                rep.disagreements += 1
                a = applicable.get((rid, pk))
                tag = "ACKNOWLEDGED" if a else "UNACKNOWLEDGED"
                rep.say("")
                rep.say("  *** DISAGREEMENT [%s] %s" % (tag, label))
                rep.say("      recorded predicate : %s = false" % pk)
                rep.say("      recorded verdict   : " +
                        ", ".join("%s=%r" % (k, verdicts[k]) for k in affirm))
                if a:
                    rep.acknowledged += 1
                    rep.say("      disposition        : %s" % a["disposition"])
                    rep.say("      reason             : %s" % a["reason"])
                    if a.get("correctedBy"):
                        rep.say("      corrected form     : %s" % a["correctedBy"])
                    if a.get("gradedProposition"):
                        rep.say("      verdict scope      : %s" % a["gradedProposition"])
                else:
                    rep.unacknowledged += 1
                    rep.say("      NO ACKNOWLEDGEMENT. This row asserts its prediction held while "
                            "recording that")
                    rep.say("      one of its own predicates did not. Decide which is wrong and "
                            "write it down;")
                    rep.say("      do not summarise past it.")

    # CENSUS ONLY (see docstring): an affirmative word -- as a value ANYWHERE, or as a mapping
    # KEY -- whose immediately owning object contributed no witness.
    for spath, kind, s in walk_strings(doc):
        if classify_verdict(s) != "AFFIRMATIVE":
            continue
        owner = spath.split(".<key>")[0] if kind == "key" else spath.rsplit(".", 1)[0]
        if owner not in witnessed_objects:
            rep.header_affirmations += 1
            rep.say("  census   HEADER AFFIRMATION %s %s %r -- affirmative word in an object that "
                    "graded nothing" % (kind, spath, s))

    if len(rep.witness) == witness_at_entry:
        rep.nil_files += 1
        rep.say("  REFUSED  NIL COVERAGE -- this file yielded NO WITNESS: not one boolean leaf "
                "under a key")
        rep.say("           the register classifies PREDICATE. Coverage is what the rule GRADED, "
                "not what")
        rep.say("           shape it recognised, so no container arrangement can supply it. An "
                "empty")
        rep.say("           measurement REFUTES rather than passes through.")
    rep.say("")


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError, ValueError):
        pass

    ap = argparse.ArgumentParser(
        description="R-VPA verdict/predicate agreement checker (T292, fail-closed by construction)",
        add_help=False)
    ap.add_argument("-h", "--help", action="store_true", dest="want_help")
    ap.add_argument("files", nargs="*", help="classification JSON files to inspect")
    ap.add_argument("--register", default=str(T256 / "boolean-key-register.json"))
    ap.add_argument("--acknowledgements", default=str(T256 / "acknowledged.json"))
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 on --help and 2 on a usage error. BOTH are ERROR here: a caller that
        # reads exit 0 reads "measured, GREEN", and no probe line was printed. T286's fourth
        # fail-open. `add_help=False` above means --help reaches us as a flag, but an unknown
        # flag still comes through here.
        print("ERROR: usage (argparse exit %s); a usage exit is never GREEN" % exc.code,
              file=sys.stderr)
        return 2
    if args.want_help:
        ap.print_help(sys.stderr)
        print("\nERROR: --help is not a measurement. Exit 2, no probe line.", file=sys.stderr)
        return 2

    try:
        targets = [Path(f) for f in args.files]
        if not targets:
            raise RuleError("no target given. This rule has NO built-in default target: a default "
                            "makes the guard measure whatever happens to be on disk beside it.")
        for t in targets:
            if not t.exists():
                raise RuleError("no such file: %s" % t)
        reg, ack = load_registers(Path(args.register), Path(args.acknowledgements))
        rep = Report()
        for t in targets:
            check_file(t, reg, ack, rep)
    except RuleError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        print("ERROR: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2

    nil = 1 if rep.nil_files else 0
    refused = bool(rep.unacknowledged or rep.unclassified_keys or rep.unclassified_verdicts
                   or rep.void_acks or rep.mute_refutations or nil)

    # POST-CONDITION, checked in code and not with `assert` (PYTHONOPTIMIZE=2 deletes asserts).
    # GREEN may not be reported without a non-empty witness, NOR with any file that contributed
    # none. If this ever fires the rule has a defect and the correct response is ERROR, not a
    # verdict.
    if not refused and (len(rep.witness) < 1 or rep.nil_files or rep.files < 1):
        print("ERROR: post-condition violated -- GREEN with an empty witness set. This is a "
              "defect in the rule itself, not a measurement.", file=sys.stderr)
        return 2

    state = "REFUSED" if refused else "GREEN"
    print("R-VPA -- verdict/predicate agreement (T259 rule, T292 fail-closed formulation)")
    print("=" * 78)
    for ln in rep.lines:
        print(ln)
    print("-" * 78)
    print("  files inspected            : %d" % rep.files)
    print("  objects traversed          : %d   (census; NOT the coverage metric)" % rep.objects)
    print("  WITNESS -- predicate reads : %d   (THE coverage metric)" % len(rep.witness))
    for wpath, wkey, wval in rep.witness:
        print("      %s = %s" % (wpath, "true" if wval else "false"))
    print("  disagreements found        : %d   (acknowledged %d, unacknowledged %d)"
          % (rep.disagreements, rep.acknowledged, rep.unacknowledged))
    print("  void acknowledgement blocks: %d" % rep.void_acks)
    print("  unclassified boolean keys  : %d" % rep.unclassified_keys)
    print("  unclassified verdict words : %d" % rep.unclassified_verdicts)
    print("  files yielding NO witness  : %d   (ANY is a refusal -- gated PER FILE, T268 F-1)"
          % rep.nil_files)
    print("  mute refutations (G6)      : %d" % rep.mute_refutations)
    print("  header affirmations        : %d   (CENSUS ONLY -- gating it would turn 3 committed "
          "rows of classify-t229.json RED; see the docstring)" % rep.header_affirmations)
    print()
    print("  THIS DOES NOT ESTABLISH: that any verdict is correct, that any predicate is "
          "correctly")
    print("  stated, or that a recorded predicate is not a fabrication. It establishes that no "
          "object")
    print("  printed an affirmative verdict over its own false predicate unremarked, and that "
          "this run")
    print("  GRADED the %d facts listed above -- coverage no container arrangement can supply."
          % len(rep.witness))
    # T259's NINE fields keep their names, values and positions. `rows` is retained as a field
    # name for substring readers and now carries the OBJECT census; the gating quantity is
    # `predicates`, and `nilCoverage` is derived from the WITNESS, not from `rows`.
    print("%s %s files=%d rows=%d predicates=%d disagreements=%d acknowledged=%d "
          "unacknowledged=%d unclassifiedKeys=%d unclassifiedVerdicts=%d nilCoverage=%d "
          "witness=%d nilFiles=%d muteRefutations=%d voidAcks=%d headerAffirmations=%d "
          "coverageDigest=%s"
          % (PROBE, state, rep.files, rep.objects, rep.predicates, rep.disagreements,
             rep.acknowledged, rep.unacknowledged, rep.unclassified_keys,
             rep.unclassified_verdicts, nil, len(rep.witness), rep.nil_files,
             rep.mute_refutations, rep.void_acks, rep.header_affirmations,
             coverage_digest(rep)))
    return 1 if refused else 0


def coverage_digest(rep: Report) -> str:
    """A fingerprint of WHAT WAS GRADED, keyed on (key, value) and NOT on path -- so it is
    invariant under exactly the container-only rewritings the theorem covers, and changes the
    moment the graded FACTS change. A green whose digest moved graded something else."""
    canon = ";".join(sorted("%s=%s" % (k, "1" if v else "0") for _, k, v in rep.witness))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    sys.exit(main())
