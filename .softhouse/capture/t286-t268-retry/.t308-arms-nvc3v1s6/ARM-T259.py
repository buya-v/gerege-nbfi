#!/usr/bin/env python3
"""T259 -- R-VPA: a classification row may not carry an affirmative verdict over a FALSE predicate
it recorded itself, unless a committed, sha-pinned acknowledgement says why.

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

FAIL-CLOSED IN FOUR DIRECTIONS -- each one closes an evasion the naive rule leaves open:
    1. UNCLASSIFIED VERDICT WORD is a refusal.  Otherwise the rule is evaded by renaming
       "AS PREDICTED" to "LOOKS FINE" and the field stops being affirmative by fiat.
    2. UNCLASSIFIED BOOLEAN KEY is a refusal.  A boolean whose intent nobody has recorded cannot
       be assumed descriptive; assuming it is, is exactly how P2 got past six pairs of eyes.
       `^P[0-9]+_` auto-classifies as PREDICATE; every other boolean key must be registered.
    3. NIL COVERAGE is a refusal.  A checker that inspects zero rows and exits 0 is a decoration
       (PREDICTION.md's own P5 states the principle: "an empty measurement REFUTES rather than
       passes through").
    4. ACKNOWLEDGEMENTS ARE PINNED TO THE FILE'S sha256.  Edit one byte of the evidence and every
       acknowledgement over it goes VOID and the rows go RED.  This is T114/T176 enforced
       mechanically: you cannot make the record agree by retro-editing it.

WHAT COUNTS AS A ROW
    Every dict inside every top-level list of dicts -- `cells`, `calibration`, or anything a
    future classifier adds. The rule is not written around `cells`, and is not written around
    `P2_`; both are discovered.

NO FLOATING POINT.  `json.load(..., parse_float=Decimal)` on every read (T145).  This file
REPRODUCES NOTHING -- it is new, not a successor to a script that loaded without the guard -- so
T207's ruling (`.softhouse/capture/audit-t44/analysis/T207/RULING-float-derived-predicate.md`:
"add `parse_float` is sometimes the WRONG repair, when a line faithfully REPRODUCES an earlier
script that loaded without it") does not apply, and the guard is simply added. Nothing monetary is
computed here at all; every value the rule inspects is a `bool` or a `str`.

EXIT CODES -- never conflated (P-80):
    0  GREEN    -- inspected a non-empty population; every disagreement found is acknowledged;
                   every boolean key classified; every verdict word classified.
    1  REFUSED  -- a REAL measured negative: >=1 unacknowledged disagreement, unclassified key,
                   unclassified verdict, or NIL coverage.
    2  ERROR    -- usage, IO, or parse. NEVER used to report an absence.

PROBE LINE.  The last line is always
    T259-VPA: <STATE> files=.. rows=.. predicates=.. disagreements=.. acknowledged=..
              unacknowledged=.. unclassifiedKeys=.. unclassifiedVerdicts=.. nilCoverage=..
Test its PRESENCE before its VALUE (P-83): exit 1 alone is ambiguous between "refused" and
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


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit("ERROR: no .git ancestor of " + str(HERE))


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


def walk_rows(doc):
    """Yield (containerKey, index, row) for every dict inside every top-level list of dicts."""
    if not isinstance(doc, dict):
        return
    for ck, cv in doc.items():
        if isinstance(cv, list):
            for i, row in enumerate(cv):
                if isinstance(row, dict):
                    yield ck, i, row


def row_label(ck, i, row) -> str:
    for k in ("id", "cal", "cell", "name"):
        if k in row:
            return f"{ck}[{i}]:{row[k]}"
    return f"{ck}[{i}]"


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
        self.void_acks = 0
        self.lines = []

    def say(self, s=""):
        self.lines.append(s)


def load_registers(reg_path: Path, ack_path: Path):
    reg = load_json(reg_path)
    ack = load_json(ack_path)
    pat = reg.get("autoPredicatePattern")
    if pat != "^P[0-9]+_":
        raise SystemExit("ERROR: unexpected autoPredicatePattern in register; refusing to guess")
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
    for ck, i, row in walk_rows(doc):
        seen_rows += 1
        label = row_label(ck, i, row)
        rid = row.get("id") or row.get("cal") or label

        verdicts = {k: v for k, v in row.items() if is_verdict_key(k) and isinstance(v, str)}
        vclasses = {k: classify_verdict(v) for k, v in verdicts.items()}
        for k, cls in vclasses.items():
            if cls == "UNCLASSIFIED":
                rep.unclassified_verdicts += 1
                rep.say(f"  REFUSED  {label}: verdict key {k!r} has value {verdicts[k]!r}, which is")
                rep.say("           in neither the AFFIRMATIVE nor the NEGATIVE vocabulary. A "
                        "verdict word this")
                rep.say("           rule cannot read is not a pass -- register it or rename it.")

        false_predicates = []
        for k, v in row.items():
            if not isinstance(v, bool):
                continue
            cls, why = key_class(reg, k)
            if cls == "UNCLASSIFIED":
                rep.unclassified_keys += 1
                rep.say(f"  REFUSED  {label}: boolean key {k!r} is unclassified. Add it to "
                        "boolean-key-register.json")
                rep.say("           as PREDICATE or DESCRIPTIVE, with a reason. Guessing is how "
                        "P2 got past.")
                continue
            if cls != "PREDICATE":
                continue
            rep.predicates += 1
            if v is False:
                false_predicates.append((k, why))

        affirm = [k for k, c in vclasses.items() if c == "AFFIRMATIVE"]
        if false_predicates and affirm:
            for pk, _why in false_predicates:
                rep.disagreements += 1
                a = applicable.get((rid, pk))
                tag = "ACKNOWLEDGED" if a else "UNACKNOWLEDGED"
                rep.say("")
                rep.say(f"  *** DISAGREEMENT [{tag}] {label}")
                rep.say(f"      recorded predicate : {pk} = false")
                rep.say(f"      recorded verdict   : " +
                        ", ".join(f"{k}={verdicts[k]!r}" for k in affirm))
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
        rep.say("  REFUSED  NIL COVERAGE -- this file contains no inspectable row. An empty "
                "measurement")
        rep.say("           REFUTES rather than passes through.")
    rep.say("")


def main(argv=None) -> int:
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

    print("R-VPA -- verdict/predicate agreement (T259)")
    print("=" * 78)
    for ln in rep.lines:
        print(ln)
    print("-" * 78)
    nil = 1 if rep.rows == 0 else 0
    refused = (rep.unacknowledged or rep.unclassified_keys or rep.unclassified_verdicts or nil)
    state = "REFUSED" if refused else "GREEN"
    print(f"  files inspected           : {rep.files}")
    print(f"  rows inspected            : {rep.rows}")
    print(f"  predicate booleans read   : {rep.predicates}")
    print(f"  disagreements found       : {rep.disagreements}"
          f"   (acknowledged {rep.acknowledged}, unacknowledged {rep.unacknowledged})")
    print(f"  void acknowledgement blocks: {rep.void_acks}")
    print(f"  unclassified boolean keys : {rep.unclassified_keys}")
    print(f"  unclassified verdict words: {rep.unclassified_verdicts}")
    print()
    print("  THIS DOES NOT ESTABLISH: that any verdict is correct, that any predicate is "
          "correctly")
    print("  stated, or that a row with no recorded predicate was checked at all. It establishes")
    print("  only that no row printed an affirmative verdict over its own false predicate "
          "unremarked.")
    print(f"{PROBE} {state} files={rep.files} rows={rep.rows} predicates={rep.predicates} "
          f"disagreements={rep.disagreements} acknowledged={rep.acknowledged} "
          f"unacknowledged={rep.unacknowledged} unclassifiedKeys={rep.unclassified_keys} "
          f"unclassifiedVerdicts={rep.unclassified_verdicts} nilCoverage={nil}")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
