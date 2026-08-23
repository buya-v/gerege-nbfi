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

FAIL-CLOSED IN SEVEN DIRECTIONS -- each one closes an evasion the naive rule leaves open:
    1. UNCLASSIFIED VERDICT WORD is a refusal.  Otherwise the rule is evaded by renaming
       "AS PREDICTED" to "LOOKS FINE" and the field stops being affirmative by fiat.
    2. UNCLASSIFIED BOOLEAN KEY is a refusal.  A boolean whose intent nobody has recorded cannot
       be assumed descriptive; assuming it is, is exactly how P2 got past.
       `^P[0-9]+_` auto-classifies as PREDICATE; every other boolean key must be registered.
    3. NIL COVERAGE ON ANY FILE is a refusal.  A checker that inspects zero rows and exits 0 is a
       decoration (PREDICTION.md's own P5 states the principle: "an empty measurement REFUTES
       rather than passes through").  T268/F-1: this is now per file. One populated file in the
       batch no longer switches the refusal off for the others.
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

WHAT COUNTS AS A ROW  (T268/F-3 -- was: "every dict inside every top-level list of dicts")
    A dict is INSPECTABLE if it carries any evidence at all: a PREDICATE-classed key, a
    verdict-named key, a boolean value, or a string value in the AFFIRMATIVE/NEGATIVE vocabulary.
    A ROW is an inspectable dict with NO inspectable ancestor, and it OWNS ITS WHOLE SUBTREE --
    so a predicate buried in a nested list inside the row is still that row's predicate, and a row
    nested three levels down, or sitting in a top-level JSON ARRAY, is still found. The rule is not
    written around `cells`, not around `P2_`, and no longer around a fixed nesting depth.

WHAT IS STILL OUT OF REACH -- stated, not hidden (P-40):
    a. A document whose ROOT dict is itself inspectable collapses to ONE row that owns everything.
       The disagreement still fires (the subtree is scanned), so this is fail-closed, but the
       row/predicate COUNTS are coarser. No file this rule is pointed at has that shape: measured
       in `.softhouse/capture/t268-rvpa-failopen/out/survey-real-evidence.txt`.
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
    1  REFUSED  -- a REAL measured negative: >=1 unacknowledged disagreement, unclassified key,
                   unclassified verdict, non-boolean predicate, unreadable verdict, or a file with
                   NIL coverage.
    2  ERROR    -- usage, IO, parse, or environment. NEVER used to report an absence.
                   Every error path raises `RuleError` or returns 2 directly; none returns 1.

PROBE LINE.  The last line is always
    T259-VPA: <STATE> files=.. rows=.. predicates=.. disagreements=.. acknowledged=..
              unacknowledged=.. unclassifiedKeys=.. unclassifiedVerdicts=.. nilCoverage=..
              nilCoverageFiles=.. nonBoolPredicates=.. unreadableVerdicts=..
Test its PRESENCE before its VALUE (P-84): exit 1 alone is ambiguous between "refused" and
"crashed before it got there".
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


def walk_rows(reg, node, path="$"):
    """Yield (path, row) for every ROW: an inspectable dict with no inspectable ancestor.

    A row owns its whole subtree, so nothing below it is yielded separately -- that is what makes
    a predicate buried in a nested list inside the row still count as THAT ROW's predicate
    (T268/F-3, shape A8). A top-level JSON array (shape A2) and a row nested one level deeper than
    the old two-level walk (shape A1) are both reached for free.
    """
    if isinstance(node, dict):
        if is_inspectable(reg, node):
            yield path, node
            return
        for k, v in node.items():
            sub = k if path == "$" else f"{path}.{k}"
            yield from walk_rows(reg, v, sub)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_rows(reg, v, f"{path}[{i}]")


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


class Report:
    def __init__(self):
        self.files = 0
        self.rows = 0
        self.predicates = 0
        self.disagreements = 0
        self.acknowledged = 0
        self.unacknowledged = 0
        self.unclassified_keys = 0
        self.unclassified_verdicts = 0
        self.non_bool_predicates = 0
        self.unreadable_verdicts = 0
        self.nil_coverage_files = 0
        self.void_acks = 0
        self.lines = []

    def say(self, s=""):
        self.lines.append(s)


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

    seen_rows = 0
    for rpath, row in walk_rows(reg, doc):
        seen_rows += 1
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
    rep.rows += seen_rows
    if seen_rows == 0:
        # T268/F-1. This used to be reported here and gated GLOBALLY at the summary, so one
        # populated file in the same invocation printed this refusal and still exited 0 GREEN.
        # The counter is what the gate reads now, so a refusal in the body IS a refusal in the
        # exit code -- for this file, whatever the other files in the batch contain.
        rep.nil_coverage_files += 1
        rep.say("  REFUSED  NIL COVERAGE -- this file contains no inspectable row. An empty "
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

    print("R-VPA -- verdict/predicate agreement (T259, repaired T268)")
    print("=" * 78)
    for ln in rep.lines:
        print(ln)
    print("-" * 78)
    # T268/F-1: `nil` is now ANY file with nil coverage, not "the batch summed to zero rows".
    # `files == 0` cannot happen through argparse (the default target fills in), but a caller
    # importing `run` could pass one, and an invocation that inspected NO FILE is nil coverage
    # by the same argument that makes an empty file nil coverage.
    nil = 1 if (rep.nil_coverage_files or rep.files == 0) else 0
    refused = (rep.unacknowledged or rep.unclassified_keys or rep.unclassified_verdicts
               or rep.non_bool_predicates or rep.unreadable_verdicts or nil)
    state = "REFUSED" if refused else "GREEN"
    print(f"  files inspected           : {rep.files}")
    print(f"  rows inspected            : {rep.rows}")
    print(f"  predicate booleans read   : {rep.predicates}")
    print(f"  disagreements found       : {rep.disagreements}"
          f"   (acknowledged {rep.acknowledged}, unacknowledged {rep.unacknowledged})")
    print(f"  void acknowledgement blocks: {rep.void_acks}")
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
    print(f"{PROBE} {state} files={rep.files} rows={rep.rows} predicates={rep.predicates} "
          f"disagreements={rep.disagreements} acknowledged={rep.acknowledged} "
          f"unacknowledged={rep.unacknowledged} unclassifiedKeys={rep.unclassified_keys} "
          f"unclassifiedVerdicts={rep.unclassified_verdicts} nilCoverage={nil} "
          f"nilCoverageFiles={rep.nil_coverage_files} "
          f"nonBoolPredicates={rep.non_bool_predicates} "
          f"unreadableVerdicts={rep.unreadable_verdicts}")
    return 1 if refused else 0


def main(argv=None) -> int:
    """Every `RuleError` becomes exit 2, wherever in the call tree it was raised (T268/F-2)."""
    try:
        return run(argv)
    except RuleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
