#!/usr/bin/env python3
"""T259 -- R-VPA: a classification row may not carry an affirmative verdict over a FALSE predicate
it recorded itself, unless a committed, sha-pinned acknowledgement says why.

T268 REPAIRED THREE DEFECTS AN INDEPENDENT REVIEW (T262) MEASURED IN THIS FILE. See
`.softhouse/capture/t268-rvpa-failopen/` for the RED/GREEN battery that drives each one.
    F-1 HIGH  NIL COVERAGE was reported PER FILE and gated GLOBALLY, so a two-file invocation
              printed `REFUSED  NIL COVERAGE` in the body and exited 0 GREEN. The rule written to
              make a silent disagreement impossible to print was itself printing a refusal and
              reporting green. Now every file's nil coverage is counted (`nilCoverageFiles`) and
              ANY of them refuses.
    F-2 MED   Two of the error paths raised `SystemExit("ERROR: ...")`, which exits **1** -- the
              code this module reserves for a MEASURED NEGATIVE. Every error path now exits 2
              (`RuleError`, caught in `main`).
    F-3 MED   8 of 12 adversarial shapes walked past the selector SILENTLY. Widened on four axes
              (nesting depth, predicate value type, verdict value type, verdict key name) --
              see WHAT COUNTS AS A ROW and WHAT IS STILL OUT OF REACH below.

T286 REPAIRED WHAT THAT FIX BROKE, PLUS TWO MORE. A SECOND INDEPENDENT REVIEW (T281) REJECTED
T268 because its F-3 widening RESTORED THE FAIL-OPEN F-1 HAD JUST CLOSED. See
`.softhouse/capture/t286-rvpa-retry/` for the THREE-ARM battery that drives every claim below
against the pre-T268 rule, T268's rule, and this one.
    R1 HIGH   REGRESSION INTRODUCED BY F-3, measured by T281. `walk_rows` yields the first
              inspectable dict and RETURNS, and F-3 made `is_inspectable` deliberately generous,
              so ANY accepted top-level key made the DOCUMENT ROOT the one and only row,
              `seen_rows` became 1, and guard #3 could never fire on that file again.
              `{"verdict": "AS PREDICTED", "cells": []}` -- an affirmative verdict over nothing at
              all -- exited **0 GREEN** under T268 where the PRE-T268 rule exited **1 REFUSED**,
              batched with the real evidence included. F-3 widened ONE function that was doing TWO
              jobs; widening it was right for one and fail-OPEN for the other.
    R1b HIGH  THE SAME HOLE ONE LEVEL DOWN, found by T286 and NOT closed by the "the root does not
              count" repair that was in flight for it: `{"meta": {"verdict": "AS PREDICTED"},
              "cells": []}` is not a root collapse -- `meta` is an ordinary nested row -- and it
              exited **0 GREEN** too, where the pre-T268 rule exited 1. Any fix phrased about the
              ROOT specifically leaves this. The repair is therefore phrased about the STRUCTURE:
              coverage counts RECORDS, and a record is a row reached through a LIST.
    R2 MED    "Every error path ... none returns 1" was FALSE AS MEASURED (T281). Three ordinary
              malformed-input cases exited **1 with no probe line** via an uncaught
              `AttributeError`. The ENUMERATION METHOD is the root cause and is repaired too --
              see `main()`. T286 additionally found the one path that went the other way and that
              neither review caught: `--help` exited **0 with no probe line**.
    R3 MED    `void_acks` -- the T114/T176 byte-pin tamper signal -- was incremented, printed as
              `!! ACKNOWLEDGEMENT BLOCK VOID` and summarised, but appeared in NEITHER the gate
              expression NOR the probe line: F-1's exact shape, one field over, in the same
              function. It is now a refusal, and the CLASS is closed rather than the instance:
              every counter declares itself REFUSAL or CENSUS in `Report.COUNTERS`, and both the
              gate and the probe line are BUILT from that declaration.

THE DEFECT THIS EXISTS FOR
    `.softhouse/capture/t229-g8-site3/out/classify-t229.json` records
    `"P2_totalInterestEqualsNEplusB": false` on FIVE rows; THREE of them nonetheless carry
    `"verdict": "AS PREDICTED"`. The refutation of a registered prediction was measured, printed
    and committed on the same day, and appeared in no handoff, no gate text and no review.
    EVIDENCE NOT MISSING -- UNREAD. This is P-45 moved one layer out: the guard did not fail to
    run; it RAN, wrote its answer down, and the summary line above it said the opposite.

WHAT THE RULE IS (and what it deliberately is NOT)
    It does NOT decide who is right. Deciding that is a human judgement recorded in
    `DECISION-verdict-vs-predicate.md`. The rule's entire job is to make the DISAGREEMENT
    IMPOSSIBLE TO PRINT SILENTLY. A disagreement is therefore ALWAYS printed, loudly, whether or
    not it is acknowledged; acknowledgement changes only the EXIT CODE, never the noise.

FAIL-CLOSED IN TEN DIRECTIONS -- each one closes an evasion the naive rule leaves open:
    1. UNCLASSIFIED VERDICT WORD is a refusal.  Otherwise the rule is evaded by renaming
       "AS PREDICTED" to "LOOKS FINE" and the field stops being affirmative by fiat.
    2. UNCLASSIFIED BOOLEAN KEY is a refusal.  A boolean whose intent nobody has recorded cannot
       be assumed descriptive; assuming it is, is exactly how P2 got past.
       `^P[0-9]+_` auto-classifies as PREDICATE; every other boolean key must be registered.
    3. NIL COVERAGE ON ANY FILE is a refusal.  A checker that inspects zero rows and exits 0 is a
       decoration (PREDICTION.md's own P5 states the principle: "an empty measurement REFUTES
       rather than passes through").  T268/F-1: this is now per file. One populated file in the
       batch no longer switches the refusal off for the others.  T286/R1+R1b: and coverage counts
       RECORDS, not rows -- a CONTAINER (the document root, or any inspectable dict hanging off a
       mapping key) is graded but supplies no coverage, so neither a top-level header key nor a
       nested `meta` block can answer this guard on behalf of an empty file.
    4. ACKNOWLEDGEMENTS ARE PINNED TO THE FILE'S sha256.  Edit one byte of the evidence and every
       acknowledgement over it goes VOID and the rows go RED.  This is T114/T176 enforced
       mechanically: you cannot make the record agree by retro-editing it.
    5. A PREDICATE-CLASSED KEY HOLDING A NON-BOOLEAN is a refusal.  `null`, `"false"` and `0` are
       not booleans, and the old `isinstance(v, bool)` filter DROPPED them without a word --
       the same assumption failure as (2), one type over.  T268/F-3.
    6. A VERDICT-NAMED KEY HOLDING A NON-STRING is a refusal.  `{"verdict": {"word": "AS
       PREDICTED"}}` and `{"verdict": 0}` both used to read as "no verdict here".  T268/F-3.
    7. AN AFFIRMATIVE WORD UNDER ANY KEY NAME COUNTS.  The old rule only looked at keys whose NAME
       contained `verdict`/`status`, so `{"result": "AS PREDICTED"}` and `{"conclusion": "AS
       PREDICTED"}` were invisible. The affirmative VOCABULARY is now scanned name-independently,
       which needs no guess about what a future author will call the field.  T268/F-3.
       Asymmetry is deliberate: a string under a NON-verdict-named key can make a row AFFIRMATIVE
       but can never make it UNCLASSIFIED, or every prose field in the corpus would refuse.
    8. A DOCUMENT WHOSE ROOT DICT IS ITSELF INSPECTABLE is a refusal (ROOT COLLAPSE).  The root is
       still fully graded -- every guard above runs over it -- but the file's records cannot be
       censused, because a row owns its whole subtree and the root owns the document.  T268
       disclosed this shape as "fail-closed, but the counts are coarser"; T281 measured that it
       was not fail-closed at all, because the uncensusable root was ALSO answering guard #3.
       T286/R1.
    9. A VOID ACKNOWLEDGEMENT BLOCK is a refusal.  Direction 4 promises "the rows go RED"; before
       T286 the block went VOID, said so loudly in the body, and the gate never looked.  T286/R3.
   10. AN AFFIRMATIVE VERDICT ON A CONTAINER ROW is a refusal.  A verdict is graded against the
       predicates of ITS OWN row, so an affirmative word moved out of the records and into a
       header sits beside a refuted record and no disagreement fires.  Measured inert on the real
       corpus (`containerRows=0` on both classify files).  T286.

WHAT COUNTS AS A ROW  (T268/F-3 -- was: "every dict inside every top-level list of dicts")
    A dict is INSPECTABLE if it carries any evidence at all: a PREDICATE-classed key, a
    verdict-named key, a boolean value, or a string value in the AFFIRMATIVE/NEGATIVE vocabulary.
    A ROW is an inspectable dict with NO inspectable ancestor, and it OWNS ITS WHOLE SUBTREE --
    so a predicate buried in a nested list inside the row is still that row's predicate, and a row
    nested three levels down, or sitting in a top-level JSON ARRAY, is still found. The rule is not
    written around `cells`, not around `P2_`, and no longer around a fixed nesting depth.

    T286/R1 -- INSPECTION AND COVERAGE ARE TWO DIFFERENT QUESTIONS, and F-3 answered both with one
    predicate. They pull in OPPOSITE directions:
        "must this dict be INSPECTED?"      -- widening it makes the rule LOOK AT MORE. Fail-
                                               CLOSED. This is what F-3 was sent to widen, and it
                                               STAYS exactly as generous as F-3 made it:
                                               `is_inspectable` is UNCHANGED by T286, not one of
                                               its four signals was taken back, and every blind
                                               spot F-3 closed stays closed.
        "did this file present a POPULATION?" -- widening it makes the rule DEMAND LESS. Fail-
                                               OPEN. `seen_rows` read the same predicate, so F-3
                                               widened this one too, by accident. That is R1.
    The repair SEPARATES them rather than trading one against the other. Every row is still
    yielded and still graded identically; `walk_rows` additionally REPORTS how each row was
    reached, and only rows reached THROUGH A LIST count towards coverage.

    A RECORD IS A ROW REACHED THROUGH A LIST. Everything else -- the document root, and any
    inspectable dict hanging off a mapping key -- is a CONTAINER: graded, printed, counted as
    `containerRows`, and worth ZERO coverage.

    WHY THIS PHRASING AND NOT "THE ROOT DOES NOT COUNT". Because "the root does not count" is what
    was in flight for R1 and it is defeated in one line: `{"meta": {"verdict": "AS PREDICTED"},
    "cells": []}` has a perfectly ordinary non-root row, exits 0 GREEN under it, and is R1 wearing
    a hat. That is R1b, and it is why the repair is structural. It was also chosen over T281's
    other honest option -- "coverage needs a PREDICATE-classed or verdict-named key somewhere
    BELOW the root" -- which is defeated the same way, by putting the key in a header one level
    down. In every document this rule is pointed at, records live in lists (`cells`,
    `calibration`, `throws`, `trials`, `observations`) and headers hang off mapping keys; the
    distinction needs no vocabulary and cannot be defeated by choosing a key name.

    KNOWN, DELIBERATE, DISCLOSED COST: a document that is a SINGLE record with no container now
    refuses for nil coverage even though a human would call it covered. That is an OVER-refusal;
    it is loud, it names itself, and the remedy is one line in the producer (put the record in a
    list). An over-refusal on a shape nobody uses is repaired by the next person who hits it; a
    GREEN over an empty corpus is repaired by nobody, because nobody reads a green.

WHAT IS STILL OUT OF REACH -- stated, not hidden (P-40):
    a. CORRECTED BY T286/R1 -- the previous text of this item graded the collapsed-root shape
       "fail-closed, but the counts are coarser", and THAT GRADING WAS WRONG: the collapsed root
       was also answering the coverage guard, which turned coarseness into a fail-OPEN. It is now
       guard #8, an outright refusal, and contributes 0 coverage. What remains genuinely out of
       reach is the FINE STRUCTURE of such a document: the rule refuses it rather than censusing
       it, so it reports no per-record counts for a file shaped that way. That is a limit, not a
       hole -- the exit code is 1.
    a2. A DELIBERATELY PLANTED DECOY RECORD still answers the coverage guard. Put one dict with
       one registered boolean inside a list and the file has "a record". No structural predicate
       can tell a decoy record from a real one, and this rule reads the evidence rather than
       auditing who wrote it. What T286 closes is the ACCIDENTAL case -- an ordinary header over
       an empty container -- which is the case that actually occurred. Forged evidence is out of
       reach for this rule and always was; the sha-pinned acknowledgements (direction 4) are the
       only tamper control here.
    a3. A CONTAINER ROW is graded against ITS OWN subtree only. A document-level verdict is
       therefore not compared with the records' predicates. Guard #10 refuses the affirmative
       case; a NEGATIVE document-level verdict over passing records is not reported.
    b. A NEW affirmative synonym ("all good", "fine") under a NON-verdict-named key is invisible.
       Under a verdict-NAMED key it refuses as UNCLASSIFIED. Widening the vocabulary is a register
       edit, not a code change.
    c. Evidence that is not JSON (CSV, `.gz` capture payloads) is not read at all.
    d. The rule reads only the files named on argv, and its default is a single file. Pointing it
       at the rest of the corpus is T269 (wiring) and T271 (the t219 B-1 finding).

NO FLOATING POINT.  `json.load(..., parse_float=Decimal)` on every read (T145).  This file
REPRODUCES NOTHING -- it is new, not a successor to a script that loaded without the guard -- so
T207's ruling (`.softhouse/capture/audit-t44/analysis/T207/RULING-float-derived-predicate.md`:
"add `parse_float` is sometimes the WRONG repair, when a line faithfully REPRODUCES an earlier
script that loaded without it") does not apply, and the guard is simply added. Nothing monetary is
computed here at all; every value the rule inspects is a `bool` or a `str`.

EXIT CODES -- never conflated (P-81):
    0  GREEN    -- inspected a non-empty population in EVERY file; every disagreement found is
                   acknowledged; every boolean key classified; every verdict word classified;
                   every predicate boolean-valued; every verdict-named key string-valued.
    1  REFUSED  -- a REAL measured negative. EXACTLY the counters `Report.COUNTERS` declares
                   REFUSAL: unacknowledged disagreement, unclassified key, unclassified verdict,
                   NIL coverage, non-boolean predicate, unreadable verdict, collapsed root, void
                   acknowledgement block, affirmation on a container row. The gate is BUILT from
                   that table, so this list cannot drift away from the code (T286/R3).
    2  ERROR    -- usage, IO, parse, or environment. NEVER used to report an absence.
                   T286/R2 -- what this line USED to claim, "every error path raises `RuleError`
                   or returns 2 directly; none returns 1", was FALSE AS MEASURED. An UNCAUGHT
                   exception is an error path nobody wrote, and Python exits 1 on one. It is now
                   true BY CONSTRUCTION (a terminal `except Exception` in `main`), not by
                   enumeration -- and it is checked BY EXECUTION, never by grepping the source
                   for the exits somebody remembered to write.

THE INVARIANT A CALLER MAY RELY ON, checked by `error_path_matrix.py` over a mutation matrix:
    exit 0 => the probe line is PRESENT and says GREEN
    exit 1 => the probe line is PRESENT and says REFUSED
    exit 2 => the probe line is ABSENT
Test PRESENCE before VALUE (P-84 -- "exit 2 with no probe line is the guard working; read the
ABSENCE, not the value"): a non-zero exit alone is ambiguous between "refused" and "crashed
before it got there". Note the direction that bit this file: `--help` used to exit 0 with no
probe line, and 0 is the code a caller reads as "measured, green". It is now 2.

PROBE LINE.  The last line is always, GENERATED from `Report.COUNTERS` (T286/R3) so that a
counter the gate reads can never be one a probe-line-only caller cannot see:
    T259-VPA: <STATE> files=.. rows=.. predicates=.. disagreements=.. acknowledged=..
              unacknowledged=.. unclassifiedKeys=.. unclassifiedVerdicts=.. nilCoverage=..
              nilCoverageFiles=.. nonBoolPredicates=.. unreadableVerdicts=.. rootCollapse=..
              voidAcks=.. containerRows=.. containerAffirmations=..
`rows` counts RECORDS (T286/R1). T268's twelve fields keep their names, values and POSITIONS; the
four T286 fields are appended, so T259's substring assertions still read what they were written
to read.
"""
import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T259-VPA:"

AFFIRMATIVE = {"AS PREDICTED", "AS_PREDICTED", "AS-PREDICTED", "PASS", "PASSED", "OK",
               "CONFIRMED", "REPRODUCED", "GREEN", "HELD", "AGREES", "MATCHED"}
NEGATIVE = {"REFUTED", "FAIL", "FAILED", "DIFFERS", "RED", "MISSING", "BROKEN", "VIOLATED",
            "THREW", "SKIPPED", "NOT RUN", "NOT_RUN", "INADMISSIBLE"}


class RuleError(Exception):
    """An ERROR: usage, IO, parse, or environment. ALWAYS exit 2, NEVER 1 (T268/F-2).

    `raise SystemExit("ERROR: ...")` exits **1** -- the code this module reserves for a real
    measured negative -- so a caller reading only the exit code could not tell "the rule refused"
    from "the rule could not find the repository". Every such site now raises this instead.
    """


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise RuleError("no .git ancestor of " + str(HERE))


def load_json(path: Path):
    return json.loads(path.read_text(), parse_float=Decimal)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def in_vocabulary(v) -> bool:
    """True iff `v` is a string this rule recognises as a verdict word, under ANY key name."""
    return isinstance(v, str) and classify_verdict(v) != "UNCLASSIFIED"


def is_inspectable(reg, d: dict) -> bool:
    """Does this dict carry ANY evidence the rule reads? (T268/F-3)

    Four independent signals, deliberately generous: a rule that decides "this is not a row" is
    deciding to look away, and the whole defect class this file exists for is looking away.
    """
    for k, v in d.items():
        if is_verdict_key(k):
            return True
        if isinstance(v, bool):
            return True
        if in_vocabulary(v):
            return True
        if key_class(reg, k)[0] == "PREDICATE":
            return True
    return False


def walk_rows(reg, node, path="$", via_list=False):
    """Yield (path, row, via_list) for every ROW: an inspectable dict with no inspectable ancestor.

    A row owns its whole subtree, so nothing below it is yielded separately -- that is what makes
    a predicate buried in a nested list inside the row still count as THAT ROW's predicate
    (T268/F-3, shape A8). A top-level JSON array (shape A2) and a row nested one level deeper than
    the old two-level walk (shape A1) are both reached for free.

    T286/R1 -- THE THIRD ELEMENT IS THE WHOLE REPAIR, AND IT IS A REPORT, NOT A FILTER.
    `via_list` is True iff this dict was reached as an ELEMENT OF A LIST. That is the structural
    difference between a RECORD and a CONTAINER: in every document this rule is pointed at, records
    live in lists (`cells`, `calibration`, `throws`, `trials`, `observations`) and headers hang off
    mapping keys. The DOCUMENT ROOT is the extreme case of a container -- it is reached through no
    list at all.

    Nothing is filtered here. Every row this generator used to yield it still yields, and
    `check_file` grades every one of them identically, so every signal `is_inspectable` was widened
    to reach by T268/F-3 is still reached -- not one of the four was taken back. What changes is
    downstream: only rows with `via_list` count towards COVERAGE. Narrowing `is_inspectable`
    instead would have re-opened F-3's blind spot, which is the trade T268 made in reverse.
    """
    if isinstance(node, dict):
        if is_inspectable(reg, node):
            yield path, node, via_list
            return
        for k, v in node.items():
            sub = k if path == "$" else f"{path}.{k}"
            yield from walk_rows(reg, v, sub, False)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_rows(reg, v, f"{path}[{i}]", True)


def walk_pairs(node, path):
    """Yield (path, key, value) for every key/value pair anywhere in `node`'s subtree."""
    if isinstance(node, dict):
        for k, v in node.items():
            sub = k if path == "$" else f"{path}.{k}"
            yield sub, k, v
            yield from walk_pairs(v, sub)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_pairs(v, f"{path}[{i}]")


def row_label(path, row) -> str:
    for k in ("id", "cal", "cell", "name"):
        if k in row and isinstance(row[k], str):
            return f"{path}:{row[k]}"
    return str(path)


def camel(name: str) -> str:
    """`nil_coverage_files` -> `nilCoverageFiles`. The probe line's field names are GENERATED."""
    head, *rest = name.split("_")
    return head + "".join(w[:1].upper() + w[1:] for w in rest)


class Report:
    """EVERY counter DECLARES what the gate must do with it (T286/R3).

    T268/F-1 was "a refusal printed in the body that the gate did not read". T281 found the SAME
    defect one field over, in the same function: `void_acks` was incremented, printed as
    `!! ACKNOWLEDGEMENT BLOCK VOID`, summarised in the footer -- and appeared in NEITHER the gate
    expression NOR the probe line. Repairing that one instance by adding it to a hand-written `or`
    chain would leave the next counter for the next reviewer, which is how this file has now
    failed twice.

    So the gate expression AND the probe line are both BUILT FROM this table, and `__init__`
    creates exactly the counters it declares. A counter that is not in this table does not exist;
    one that is added as REFUSAL is gated and printed automatically. `gate_table_selftest.py`
    proves both BY EXECUTION -- it mutates each counter in turn and reads the exit code -- rather
    than by anyone reading the source and agreeing with it.

        REFUSAL -- a measured negative. Non-zero => exit 1. Printed on the probe line.
        CENSUS  -- a count, not a verdict. Never gates. Printed on the probe line.

    ORDER IS THE PROBE LINE'S ORDER. T268's twelve fields keep their names, values and POSITIONS
    so that T259's battery, which asserts on the probe line by substring, still reads what it was
    written to read; the four T286 fields are APPENDED.
    """

    COUNTERS = {
        "files": "CENSUS",
        "rows": "CENSUS",
        "predicates": "CENSUS",
        "disagreements": "CENSUS",
        "acknowledged": "CENSUS",
        "unacknowledged": "REFUSAL",
        "unclassified_keys": "REFUSAL",
        "unclassified_verdicts": "REFUSAL",
        "nil_coverage_files": "REFUSAL",
        "non_bool_predicates": "REFUSAL",
        "unreadable_verdicts": "REFUSAL",
        "root_collapse": "REFUSAL",
        "void_acks": "REFUSAL",
        "container_rows": "CENSUS",
        "container_affirmations": "REFUSAL",
    }

    def __init__(self):
        for name in self.COUNTERS:
            setattr(self, name, 0)
        self.lines = []

    def say(self, s=""):
        self.lines.append(s)


def gate(rep: "Report") -> bool:
    """True iff this run REFUSES. BUILT from `Report.COUNTERS`, never hand-listed (T286/R3).

    `files == 0` is folded in for the same reason an empty file is nil coverage: an invocation
    that inspected NO FILE inspected nothing, and a checker that inspects nothing and exits 0 is a
    decoration. argparse cannot produce it (the default target fills in) but a caller importing
    `run` could.
    """
    if rep.files == 0:
        return True
    return any(getattr(rep, n) for n, cls in Report.COUNTERS.items() if cls == "REFUSAL")


def probe_fields(rep: "Report", nil: int) -> str:
    """The probe line's field list, GENERATED from `Report.COUNTERS` (T286/R3).

    `nilCoverage` is DERIVED (it folds in `files == 0`), not a counter, and is emitted in T268's
    position -- immediately ahead of `nilCoverageFiles` -- because T259's battery asserts on it.
    """
    out = []
    for name in Report.COUNTERS:
        if name == "nil_coverage_files":
            out.append(f"nilCoverage={nil}")
        out.append(f"{camel(name)}={getattr(rep, name)}")
    return " ".join(out)


def load_registers(reg_path: Path, ack_path: Path):
    reg = load_json(reg_path)
    ack = load_json(ack_path)
    pat = reg.get("autoPredicatePattern")
    if pat != "^P[0-9]+_":
        raise RuleError("unexpected autoPredicatePattern in register; refusing to guess")
    return reg, ack


def key_class(reg, key: str):
    if key.startswith("P") and "_" in key:
        head = key.split("_", 1)[0]
        if len(head) > 1 and head[1:].isdigit():
            return "PREDICATE", "auto: matches ^P[0-9]+_"
    ent = reg.get("keys", {}).get(key)
    if ent is None:
        return "UNCLASSIFIED", "not in boolean-key-register.json"
    return ent["class"], ent.get("reason", "")


def acks_for(ack, rel: str, sha: str, rep: Report):
    """Return {(rowId, predicateKey): entry} for acknowledgements that apply to THIS byte-image."""
    out = {}
    for blk in ack.get("acknowledgements", []):
        if blk["file"] != rel:
            continue
        if blk["sha256"] != sha:
            rep.void_acks += 1
            rep.say(f"  !! ACKNOWLEDGEMENT BLOCK VOID -- registered for sha256 {blk['sha256']}")
            rep.say(f"     but the live file is       sha256 {sha}")
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
    sha = sha256_of(path)
    doc = load_json(path)
    rep.files += 1
    rep.say(f"FILE {rel}")
    rep.say(f"     sha256 {sha}")
    applicable = acks_for(ack, rel, sha, rep)

    seen_records = 0     # RECORDS ONLY. A container row is graded but supplies no coverage.
    seen_containers = 0
    root_collapsed = False
    for rpath, row, via_list in walk_rows(reg, doc):
        if via_list:
            seen_records += 1
        else:
            # T286/R1. Graded below EXACTLY like any other row -- every guard runs over it. It
            # simply does not COUNT as coverage, because it is a container, not a record.
            seen_containers += 1
            rep.container_rows += 1
            if rpath == "$":
                root_collapsed = True
        label = row_label(rpath, row)
        rid = row.get("id") or row.get("cal") or label

        # --- verdict-shaped signals, gathered over the row's WHOLE subtree (T268/F-3) ----------
        affirm = []          # [(path, key, value)] -- affirmative words, under ANY key name
        for vpath, k, v in walk_pairs(row, rpath):
            if is_verdict_key(k):
                if not isinstance(v, str):
                    rep.unreadable_verdicts += 1
                    rep.say(f"  REFUSED  {label}: verdict key {k!r} at {vpath} holds a "
                            f"{type(v).__name__}, not a string.")
                    rep.say("           A verdict this rule cannot READ is not a pass. Put the "
                            "word in a string field")
                    rep.say("           or register the shape; do not leave it unreadable.")
                    continue
                cls = classify_verdict(v)
                if cls == "UNCLASSIFIED":
                    rep.unclassified_verdicts += 1
                    rep.say(f"  REFUSED  {label}: verdict key {k!r} has value {v!r}, which is")
                    rep.say("           in neither the AFFIRMATIVE nor the NEGATIVE vocabulary. A "
                            "verdict word this")
                    rep.say("           rule cannot read is not a pass -- register it or rename "
                            "it.")
                elif cls == "AFFIRMATIVE":
                    affirm.append((vpath, k, v))
            elif in_vocabulary(v) and classify_verdict(v) == "AFFIRMATIVE":
                # T268/F-3: the affirmative VOCABULARY is scanned name-independently, so a field
                # called `result` or `conclusion` cannot escape by not being called `verdict`.
                affirm.append((vpath, k, v))

        # --- predicates, likewise over the whole subtree ---------------------------------------
        false_predicates = []
        for ppath, k, v in walk_pairs(row, rpath):
            cls, why = key_class(reg, k)
            if cls == "PREDICATE":
                if not isinstance(v, bool):
                    rep.non_bool_predicates += 1
                    rep.say(f"  REFUSED  {label}: predicate key {k!r} at {ppath} holds "
                            f"{v!r} ({type(v).__name__}), not a boolean.")
                    rep.say("           A predicate whose value this rule cannot read is DROPPED "
                            "unless it refuses;")
                    rep.say("           null / \"false\" / 0 are exactly how a refutation hides. "
                            "Fix the capture.")
                    continue
                rep.predicates += 1
                if v is False:
                    false_predicates.append((ppath, k, why))
                continue
            if not isinstance(v, bool):
                continue
            if cls == "UNCLASSIFIED":
                rep.unclassified_keys += 1
                rep.say(f"  REFUSED  {label}: boolean key {k!r} is unclassified. Add it to "
                        "boolean-key-register.json")
                rep.say("           as PREDICATE or DESCRIPTIVE, with a reason. Guessing is how "
                        "P2 got past.")

        if affirm and not via_list:
            # T286, guard #10. An AFFIRMATIVE verdict on a CONTAINER row asserts something about
            # a scope this rule cannot grade: the container's own predicates (it usually has
            # none) are not the records' predicates, so a document-level "AS PREDICTED" sits
            # beside a refuted record and no disagreement fires. Measured inert on the real
            # corpus (`containerRows=0` on classify-t229 and classify-t219), and it closes the
            # evasion of moving the affirmative word out of the records and into a header.
            rep.container_affirmations += 1
            rep.say(f"  REFUSED  {label}: an AFFIRMATIVE verdict "
                    f"({', '.join(f'{k}={v!r}' for _p, k, v in affirm)}) sits on a row that is")
            rep.say("           NOT a record -- it was reached through a mapping key, not a "
                    "list, so it is a")
            rep.say("           CONTAINER. This rule grades a verdict against the predicates of "
                    "ITS OWN row, and")
            rep.say("           a container's row is not the records'. Put the verdict on the "
                    "record it grades.")

        if false_predicates and affirm:
            for _ppath, pk, _why in false_predicates:
                rep.disagreements += 1
                a = applicable.get((rid, pk))
                tag = "ACKNOWLEDGED" if a else "UNACKNOWLEDGED"
                rep.say("")
                rep.say(f"  *** DISAGREEMENT [{tag}] {label}")
                rep.say(f"      recorded predicate : {pk} = false")
                rep.say("      recorded verdict   : " +
                        ", ".join(f"{k}={v!r}" for _p, k, v in affirm))
                if a:
                    rep.acknowledged += 1
                    rep.say(f"      disposition        : {a['disposition']}")
                    rep.say(f"      reason             : {a['reason']}")
                    if a.get("correctedBy"):
                        rep.say(f"      corrected form     : {a['correctedBy']}")
                    if a.get("gradedProposition"):
                        rep.say(f"      verdict scope      : {a['gradedProposition']}")
                else:
                    rep.unacknowledged += 1
                    rep.say("      NO ACKNOWLEDGEMENT. This row asserts its prediction held while "
                            "recording that")
                    rep.say("      one of its own predicates did not. Decide which is wrong and "
                            "write it down;")
                    rep.say("      do not summarise past it.")
    rep.rows += seen_records
    if root_collapsed:
        # T286/R1, guard #8. T268's `WHAT IS STILL OUT OF REACH (a)` graded this shape
        # "fail-closed, but the counts are coarser". It was NOT fail-closed: the collapsed root
        # was also being counted as the coverage guard's one row, so guard #3 could never fire on
        # such a file again. Refused outright now, and it contributes 0 to coverage.
        rep.root_collapse += 1
        rep.say("  REFUSED  ROOT COLLAPSE -- this document's own ROOT dict carries evidence this "
                "rule reads,")
        rep.say("           so it becomes one row owning the entire document and the file's "
                "RECORDS cannot be")
        rep.say("           censused. The root is graded (every guard above ran over it) but it "
                "supplies NO")
        rep.say("           coverage: otherwise one header key over an empty container makes an "
                "empty file")
        rep.say("           GREEN. Put the records in a container.")
    if seen_records == 0:
        # T268/F-1. This used to be reported here and gated GLOBALLY at the summary, so one
        # populated file in the same invocation printed this refusal and still exited 0 GREEN.
        # The counter is what the gate reads now, so a refusal in the body IS a refusal in the
        # exit code -- for this file, whatever the other files in the batch contain.
        # T286/R1: `seen_records`, not `seen_rows`. A CONTAINER row -- the document root, or any
        # inspectable dict hanging off a mapping key -- is graded but supplies no coverage, so a
        # header over an empty container no longer answers this guard.
        rep.nil_coverage_files += 1
        rep.say(f"  REFUSED  NIL COVERAGE -- this file contains no inspectable RECORD "
                f"({seen_containers} container")
        rep.say("           row(s) were graded, and a container is not a record). An empty "
                "measurement")
        rep.say("           REFUTES rather than passes through.")
    rep.say("")


def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description="R-VPA verdict/predicate agreement checker")
    ap.add_argument("files", nargs="*", help="classification JSON files to inspect")
    ap.add_argument("--register", default=str(HERE / "boolean-key-register.json"))
    ap.add_argument("--acknowledgements", default=str(HERE / "acknowledged.json"))
    args = ap.parse_args(argv)

    targets = [Path(f) for f in args.files]
    if not targets:
        targets = [(HERE / ".." / "t229-g8-site3" / "out" / "classify-t229.json").resolve()]
    for t in targets:
        if not t.exists():
            print(f"ERROR: no such file: {t}", file=sys.stderr)
            return 2

    try:
        reg, ack = load_registers(Path(args.register), Path(args.acknowledgements))
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: register unreadable: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    rep = Report()
    try:
        for t in targets:
            check_file(t, reg, ack, rep)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print("R-VPA -- verdict/predicate agreement (T259, repaired T268, repaired T286)")
    print("=" * 78)
    for ln in rep.lines:
        print(ln)
    print("-" * 78)
    # T268/F-1: `nil` is ANY file with nil coverage, not "the batch summed to zero rows".
    nil = 1 if (rep.nil_coverage_files or rep.files == 0) else 0
    # T286/R3: the gate is GENERATED from `Report.COUNTERS`, never hand-listed. The hand-listed
    # `or` chain on this line is what let `void_acks` be incremented, printed loudly and
    # summarised while the gate never looked at it -- T268/F-1's own shape, one field over, in
    # the same function.
    refused = gate(rep)
    state = "REFUSED" if refused else "GREEN"
    print(f"  files inspected           : {rep.files}")
    print(f"  RECORDS inspected         : {rep.rows}   "
          f"(container rows {rep.container_rows} -- graded, but NOT coverage; T286/R1)")
    print(f"  predicate booleans read   : {rep.predicates}")
    print(f"  disagreements found       : {rep.disagreements}"
          f"   (acknowledged {rep.acknowledged}, unacknowledged {rep.unacknowledged})")
    print(f"  void acknowledgement blocks: {rep.void_acks}   (T286/R3 -- ANY of them refuses)")
    print(f"  files with a COLLAPSED root: {rep.root_collapse}   "
          f"(T286/R1 -- ANY of them refuses)")
    print(f"  affirmations on containers : {rep.container_affirmations}   "
          f"(T286 guard #10 -- ANY of them refuses)")
    print(f"  unclassified boolean keys : {rep.unclassified_keys}")
    print(f"  unclassified verdict words: {rep.unclassified_verdicts}")
    print(f"  non-boolean predicates    : {rep.non_bool_predicates}")
    print(f"  unreadable verdict values : {rep.unreadable_verdicts}")
    print(f"  files with NIL coverage   : {rep.nil_coverage_files}  "
          f"(of {rep.files} inspected -- ANY of them refuses; T268/F-1)")
    print()
    print("  THIS DOES NOT ESTABLISH: that any verdict is correct, that any predicate is "
          "correctly")
    print("  stated, or that a row with no recorded predicate was checked at all. It establishes")
    print("  only that no row printed an affirmative verdict over its own false predicate "
          "unremarked.")
    print(f"{PROBE} {state} {probe_fields(rep, nil)}")
    return 1 if refused else 0


def main(argv=None) -> int:
    """Every `RuleError` becomes exit 2, wherever in the call tree it was raised (T268/F-2).

    T286/R2 -- AND SO DOES EVERY OTHER EXCEPTION, WHICH IS THE PART T268 COULD NOT SEE. T268
    enumerated this file's error paths with `grep -n 'return 2\\|RuleError\\|SystemExit'`, and a
    grep can only find the error paths somebody WROTE. An UNCAUGHT exception is an error path
    nobody wrote, and Python exits **1** on one -- the code this module reserves for a MEASURED
    NEGATIVE -- with no probe line, which is the exact ambiguity T268/F-2 was raised to remove.
    T281 drove three ordinary inputs straight onto it: the register as a JSON array, the register
    as a JSON string, the acknowledgements as a JSON array. Both files are committed evidence
    that humans edit; a malformed edit is the ordinary case, not an exotic one.

    A blanket catch is fail-CLOSED **here and only here**: it can only turn a 1 into a 2 -- "the
    rule refused" into "the rule errored" -- and 2 is the code no caller may read as a pass. It
    cannot turn anything into a 0.

    T286 also closes the one path that went the OTHER way, which neither T268 nor T281 found:
    `--help` raises `SystemExit(0)` out of argparse and this module exited **0 WITH NO PROBE
    LINE**. Exit 0 is the one code a caller reads as "measured, green", and a help listing is not
    a measurement. Every `SystemExit` out of `run` is therefore normalised to 2 (argparse already
    uses 2 for a usage error). `KeyboardInterrupt` is NOT caught -- it is not `Exception` and not
    `SystemExit` -- so an interrupted run still dies as an interrupted run.

    THE INVARIANT A CALLER MAY RELY ON, and `error_path_matrix.py` checks it BY EXECUTION over a
    mutation matrix rather than by grepping for the exits somebody remembered to write:
        exit 0 => the probe line is PRESENT and says GREEN
        exit 1 => the probe line is PRESENT and says REFUSED
        exit 2 => the probe line is ABSENT
    """
    try:
        return run(argv)
    except RuleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:                     # argparse: usage error (2) or --help (0)
        code = exc.code
        if code not in (0, None):
            print(f"ERROR: usage (argparse exit {code})", file=sys.stderr)
        else:
            print("ERROR: this module measures; it does not exit 0 without a probe line. "
                  "`--help` and any other SystemExit(0) are reported as ERROR (2), because 0 is "
                  "reserved for a MEASURED green. T286/R2.", file=sys.stderr)
        return 2
    except Exception as exc:                      # noqa: BLE001 -- deliberate, see docstring
        print(f"ERROR: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
