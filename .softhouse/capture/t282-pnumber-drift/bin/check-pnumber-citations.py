#!/usr/bin/env python3
"""T282 -- P-NUMBER CITATION CHECKER.

WHAT IT ENFORCES, and why this predicate and not the obvious one
================================================================
The obvious checker verifies that a cited `P-n` EXISTS. That checker would have
passed EVERY instance of this defect: `RESUME.md` cited `P-78`..`P-83`, all six
of which exist, all six meaning something else. So this checker verifies the
SENTENCE, not the id:

  a `P-n` citation carrying accompanying rule text must carry text that matches
  the rule `.softhouse/patterns.md` defines under THAT number, and no other.

That predicate is chosen because it is the exact property that made the two
recorded instances harmless. patterns.md P-86: "Materiality is LOW... NOT ONE
WORKER WAS MISDIRECTED, because every prompt wrote out the FULL RULE TEXT beside
the id rather than the id alone. The number was decoration; the sentence carried
the instruction."  The rule P-86 states is: "an ID IS A CARDINAL. Never restate a
pattern id in a second document -- make the second site NAME THE RULE, or cite
the id AND its sentence together so a shifted number is self-correcting."

FAIL-CLOSED DIRECTION -- STATED, NOT ASSUMED
============================================
Two populations, and their fail-closed directions are OPPOSITE. They are checked
by two SEPARATE predicates and never by one widened predicate, because widening
one predicate to serve two purposes with opposite fail-closed directions is the
shape T292 identified as the root of the five-fix R-VPA losing streak (P-91:
"FIVE FIXES FOR A FAIL-OPEN, AND EVERY ONE LOST TO THE SAME EVASION RE-NESTED
ONE LEVEL OUT").

  REGISTER + DIRECTIVE files -- FAIL CLOSED (exit 1).
     .softhouse/patterns.md, .softhouse/RESUME.md, .softhouse/tasks.json,
     .softhouse/obligations.md, .softhouse/gates.md,
     .softhouse/gates-proposed-answers.md, .softhouse/program.json,
     .claude/skills/**, .softhouse/bin/**, .softhouse/guards/**,
     .softhouse/conformance.sh, CLAUDE.md.
     These INSTRUCT FUTURE WORK. A wrong number here is read by an agent that
     has not been born yet, and it is repairable in place because nobody has
     re-derived a review against it. Fail closed: a misdirecting citation here
     must stop the run.

  EVIDENCE files -- REPORT ONLY (exit 0), and that is deliberate.
     .softhouse/handoff/**, .softhouse/reviews/**, .softhouse/capture/**,
     .softhouse/observations/**, .softhouse/runs/**, .softhouse/logs/**,
     .softhouse/state/**, .softhouse/vectors/**.
     These are COMMITTED EVIDENCE. Several are the record of a review a second
     party re-derived. The program's standing practice is to CORRECT FORWARD,
     never to rewrite published bytes -- T316 refuted a task that tried to
     repoint a forward-reference inside committed evidence and was right to.
     A checker that failed closed here would create pressure to edit exactly the
     bytes the evidence guards forbid editing, and would block every graded run
     on prose nobody may lawfully repair. So evidence drift is PRINTED and
     COUNTED and never fatal; the remedy is an errata entry in patterns.md.

  Deliberately NOT fatal anywhere:
     - a BARE citation (id with no accompanying rule text). Ordinary prose says
       "this is P-45 again". Failing closed on that blocks every graded run on a
       documentation edit -- the failure this task was told to avoid. Counted and
       printed under WARN, with the directive-file subset broken out so the
       population is visible and can be tightened later on evidence.
     - an UNDEFINED id used as a NEGATIVE CONTROL. `P-99` is deliberately absent
       in three instruments (P-72: calibrate a sweep on a known answer). A
       checker that failed on it would punish the calibration it depends on.
       Undefined ids ARE fatal in directive files; in evidence they are reported.

SELFTEST
========
`--selftest` drives the checker RED on synthetic fixtures and GREEN on their
repairs, in-memory, touching no repo file. P-22: a guard that cannot fail is
worse than none. `--selftest` is NOT a substitute for the live run: it proves the
predicate discriminates, not that the tree is clean.

EXIT CODES
==========
  0  clean, or only report-only findings
  1  a fatal finding in the register or a DIRECTIVE file
  3  the checker could not run (register unreadable/empty, git unavailable).
     Never 0. P-36: an experiment whose input never arrives is a NULL CONTROL and
     it looks exactly like a result.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Anchored to this file, NEVER to the caller's cwd (T165/T201: FindRepoRoot(".")
# let the caller's cwd decide a frozen-contract digest gate).
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATTERNS_REL = ".softhouse/patterns.md"
GATES_REL = ".softhouse/gates-proposed-answers.md"

CITE = re.compile(r'(?<![A-Za-z0-9_])P-([1-9][0-9]*)(?![0-9])')

# A DEFINITION line: heading, or a bold run that SPANS the rule sentence
# (`**P-80 — TEXT`), or a list bullet of the same shape. An id-only bold run
# (`**P-40** — text`) is a RESTATEMENT, not a definition, and is excluded.
DEFN_HEAD = re.compile(r'^#{2,4}\s+P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')
DEFN_BOLD = re.compile(r'^(?:[-*>]\s+)?\*\*P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')
DEFN_GATES = re.compile(r'^#{2,4}\s+P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')

# ---- ZONES.  Every zone names WHY it is fatal or not; a zone with no reason is
# ---- an excuse. Only `directive` is fatal, and it is fatal because it is the
# ---- only class that is BOTH read as instruction by future workers AND lawfully
# ---- repairable in place by an ordinary task.
DIRECTIVE_EXACT = (
    ".softhouse/patterns.md",        # the register of record; must agree with itself
    ".softhouse/RESUME.md",          # STANDING INSTRUCTIONS -- the site of instance 1
    ".softhouse/conformance.sh",     # the grader
    ".softhouse/obligations.md",
    ".softhouse/reference-oracle.md",
    "CLAUDE.md",
)
DIRECTIVE_PREFIX = (
    ".claude/skills/",               # the pipeline's own prompts
    ".softhouse/bin/",
    ".softhouse/guards/",
    "docs/",                         # minus docs/adr/, see RATIFIED_PREFIX
)
# RATIFIED / GATED -- report only. Repairing these is a DEC-n amendment or a user
# gate (CLAUDE.md "Blocking questions"), not a documentation edit. Failing closed
# here would block every graded run on a change no ordinary task may make.
RATIFIED_EXACT = (
    ".softhouse/gates-proposed-answers.md",   # the user's own ratified headings
    ".softhouse/gates.md",
)
RATIFIED_PREFIX = ("docs/adr/",)
# ORCHESTRATOR-OWNED -- report only. P-31: "Never snapshot a file the orchestrator
# is actively editing -- author no change to it at all." A worker that repaired
# tasks.json mid-fire would collide with the driver by construction.
ORCHESTRATOR_EXACT = (".softhouse/tasks.json", ".softhouse/program.json")
# COMMITTED EVIDENCE -- report only, and the correction is a FORWARD entry in
# patterns.md, never an edit to these bytes. T316 refuted a task that tried to
# repoint a forward-reference inside committed evidence and was right to.
EVIDENCE_PREFIX = (
    ".softhouse/handoff/",
    ".softhouse/reviews/",
    ".softhouse/capture/",
    ".softhouse/observations/",
    ".softhouse/runs/",
    ".softhouse/logs/",
    ".softhouse/state/",
    ".softhouse/vectors/",
)
# This checker's OWN output directory. Skipped, not zoned: out/census.json is a
# verbatim transcript of every citation line in the repo, so grading it would
# double-count every site in the program and grade this instrument against its
# own printout. That is a self-reference, not a measurement.
SELF_OUTPUT_PREFIX = ".softhouse/capture/t282-pnumber-drift/out/"

# This checker's OWN SOURCE. Skipped for the SAME reason `P-99` is skipped, and
# the reason is stated rather than assumed: SELFTEST_REGISTER below contains
# DELIBERATELY DRIFTED fixtures -- `Per P-80: read the absence, not the value`
# is P-84's rule under P-80's id, planted so `--selftest` can prove the
# predicate fires. Grading them reports this instrument's own controls as
# defects (3 of the 39 findings in the pre-repair run were exactly that), which
# is a checker marking its calibration wrong. P-72: calibrate a sweep on a known
# answer -- you may not then score the known answer.
#
# NARROW ON PURPOSE, and this is the part that could rot: the skip is ONE FILE,
# not the `bin/` directory, so census.py and restamp.py beside it ARE still
# graded. A directory-wide skip here would be a blind spot that grows every time
# someone drops a file in.
SELF_SOURCE_EXACT = ".softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"

# patterns.md declares its own known-ambiguous ids in a machine-readable marker,
# so a NEW collision is loud and an ACCEPTED one is quiet. Bound by CONTENT (the
# marker text), never by line number -- P-78: an ordinal used as an identifier
# goes wrong silently; a name goes wrong loudly.
DECLARED_MARKER = re.compile(
    r'PNUMBER-REGISTER-DECLARED-COLLISIONS\s*[:=]\s*([0-9,\s]*)')

# Ids deliberately absent, used as negative controls by committed instruments.
# Each entry must name the instrument that relies on it, or it is not a control,
# it is an excuse.
NEGATIVE_CONTROL_IDS = {
    99: ".softhouse/capture/t255-dec2-rev8/instruments/15-p5-probe.py:59,73 "
        "-- 'a NEGATIVE control -- P-99, which must not be'",
}

STOP = set("""a an the and or but of to in on at is it its was were be been being for from
with without that this these those than then so as by not no non any all each every one two
three four five six seven eight nine ten only just also into onto over under about which who
whom whose what when where why how can could may might must shall should will would do does
did done has have had having if because while during before after above below up down out off
again further more most other some such own same too very s t don now i you your our their his
her they them we us me my he she him it's you're we're your yours""".split())


def norm_tokens(text):
    text = text.lower()
    text = re.sub(r'p-[0-9]+', ' ', text)          # ids never contribute to the match
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return [t for t in text.split() if len(t) >= 4 and t not in STOP]


def trigrams(tokens):
    return set(tuple(tokens[i:i + 3]) for i in range(len(tokens) - 2))


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def build_register(lines, patterns, body_lines=14):
    """id -> {line, title, body, grams}. First definition wins; later definitions
    of the same id are returned separately as COLLISIONS, never dropped.

    A rule's BODY is truncated at the NEXT definition line. Without that, one
    rule's body swallows its neighbours' text and every id matches every
    sentence -- the checker would then be vacuous in exactly the direction that
    passes the defect (P-22: a control that cannot fail is worse than none).
    Caught by --selftest case 3 before this file was ever run against the repo.
    """
    hits = []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        for rx in patterns:
            m = rx.match(s)
            if m:
                hits.append((i, int(m.group(1)), m.group(2).strip().rstrip('*').strip()))
                break
    reg, collisions, order = {}, [], []
    for k, (i, n, title) in enumerate(hits):
        stop = hits[k + 1][0] - 1 if k + 1 < len(hits) else len(lines)
        stop = min(stop, i + body_lines)
        body = " ".join(x.strip() for x in lines[i:stop])
        entry = {"id": n, "line": i, "title": title, "body": body}
        if n in reg:
            collisions.append({"id": n, "first_line": reg[n]["line"],
                               "first_title": reg[n]["title"],
                               "again_line": i, "again_title": title})
        else:
            reg[n] = entry
            order.append(n)
    for n, e in reg.items():
        e["grams"] = trigrams(norm_tokens(e["title"] + " " + e["body"]))
        e["title_grams"] = trigrams(norm_tokens(e["title"]))
        # every OTHER pattern id this entry quotes -- see cross-reference
        # suppression in analyse()
        e["names_ids"] = set(int(x) for x in CITE.findall(e["title"] + " " + e["body"]))
    return reg, collisions, order


def classify_path(rel):
    if rel in RATIFIED_EXACT or rel.startswith(RATIFIED_PREFIX):
        return "ratified"
    if rel in ORCHESTRATOR_EXACT:
        return "orchestrator"
    if rel in DIRECTIVE_EXACT:
        return "directive"
    for p in DIRECTIVE_PREFIX:
        if rel.startswith(p):
            return "directive"
    for p in EVIDENCE_PREFIX:
        if rel.startswith(p):
            return "evidence"
    return "other"


def context_window(lines, idx, before=1, after=2):
    lo = max(0, idx - before)
    hi = min(len(lines), idx + after + 1)
    return " ".join(lines[lo:hi])


# --------------------------------------------------------------------------
# GLOSS EXTRACTION -- the whole discriminating power of this checker.
#
# The naive approach (score the PARAGRAPH around the id) is worse than useless
# here: a cross-reference to P-26 written INSIDE P-37's section sits in prose
# about P-37, so the paragraph always matches the section it lives in and never
# the rule it cites. Measured on this repo, that predicate reported 735
# "misdirecting" citations, essentially all false. Recorded because a checker
# that cries wolf 735 times gets switched off, which is a fail-open with extra
# steps.
#
# What P-86 actually asks for is narrower and mechanical: "cite the id AND its
# SENTENCE together so a shifted number is self-correcting". So the unit of
# comparison is the GLOSS -- the span SYNTACTICALLY BOUND to the id:
#   P-14 ("a mutation no vector can distinguish is a blind spot")   parenthetical
#   P-84: read the absence, not the value                            colon
#   P-45 -- a test-only guard is not a guard                         dash
#   read the absence, not the value (P-84)                           trailing id
# Anything else is a BARE citation: the number with no sentence beside it. Bare
# is reported, never fatal -- see the fail-closed argument in the module docstring.
# --------------------------------------------------------------------------
MARKUP = "*`_ \t"
SENT_END = re.compile(r'(?<=[.;!?])\s')
# ids joined by `/`, `,`, `and`, `&` with only markup between them: one citation
# of several rules, e.g. `**P-22 / P-36** — a control that cannot fire ...`
CLUSTER_JOIN = re.compile(r'^[\s*`_/,&]*(?:and|or)?[\s*`_/,&]*$')


def cluster_ids(text, start, end):
    """All ids in the same citation cluster as the one at [start,end)."""
    ids = set()
    for m in CITE.finditer(text):
        if m.start() == start:
            ids.add(int(m.group(1)))
            continue
        gap = text[m.end():start] if m.end() <= start else text[end:m.start()]
        if len(gap) <= 12 and CLUSTER_JOIN.match(gap):
            ids.add(int(m.group(1)))
    return ids


def _cell_clip(s, backwards=False):
    """A MARKDOWN TABLE CELL is a gloss boundary.

    Found by driving this checker RED: patterns.md:785 is a table row whose
    LAST cell ends `...invisible to BSD grep (P-33)` -- a correct citation of
    P-33 (*a tool claim is a claim about a binary, a version, a LOCALE, an
    invocation and an input shape*). The trailing-id extractor walked backwards
    out of that cell and into the row's FIRST cell, `**Money is integer minor
    units, no floating point**`, and then scored the result against P-25 (*the
    no-floating-point rule binds analysis scripts too*) -- which it matched, of
    course, because it had eaten a sentence about floating point. Fatal, and
    wrong.

    This is the docstring's own "score the PARAGRAPH" mistake at table scale:
    the gloss must be the span SYNTACTICALLY BOUND to the id, and `|` binds.
    """
    if "|" not in s:
        return s
    return s[s.rindex("|") + 1:] if backwards else s[:s.index("|")]


def _clip_sentence(s, limit=260, min_words=9):
    """Clip at a sentence boundary, but never to a stub: `**P-80**: prints an
    absence over an error. \x60grep\x60 exits 1 on NO MATCH and >1 on ERROR` clipped at
    the first full stop yields six words and scores as BARE, which is how the
    known-drifted RULES-failopen.md:17 escaped the first draft of this checker."""
    s = _cell_clip(s[:limit])
    for m in SENT_END.finditer(s):
        head = s[:m.start() + 1]
        if len(head.split()) >= min_words:
            return head
    return s


def _matched_span(s, opener):
    closer = {"(": ")", "[": "]", "“": "”", '"': '"', "‘": "’",
              "'": "'"}[opener]
    depth = 0
    for i, ch in enumerate(s):
        if ch == opener and (opener != closer or i == 0):
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return s[1:i]
    return None


def extract_gloss(text, start, end):
    """text: the line joined with its successor (prose wraps). start/end: the
    id's span. Returns (gloss, how) or (None, None)."""
    after = text[end:]
    before = text[:start]

    # trailing-id form: `... rule sentence ... (P-84)` / `[P-84]`
    b = before.rstrip()
    if b.endswith(("(", "[")) and after[:1] in (")", "]"):
        pre = b[:-1].rstrip()
        m = None
        for mm in SENT_END.finditer(pre):
            m = mm
        seg = pre[m.end():] if m else pre
        seg = _cell_clip(seg[-260:], backwards=True)
        return (seg, "trailing-id") if len(seg.split()) >= 4 else (None, None)

    a = after.lstrip(MARKUP)
    if not a:
        return (None, None)
    if a[0] in "([“\"‘":
        span = _matched_span(a, a[0])
        if span and len(span.split()) >= 3:
            return (span, "bracketed")
        return (None, None)
    if a[0] == ":":
        return (_clip_sentence(a[1:].strip()), "colon")
    for lead in ("—", "–", "--", "→"):
        if a.startswith(lead):
            return (_clip_sentence(a[len(lead):].strip()), "dash")
    if a.startswith("'s rule") or a.startswith("’s rule"):
        return (_clip_sentence(a.split("rule", 1)[1].strip()), "possessive")
    if a.startswith(", "):
        # `P-45, "a test-only guard is not a guard"` -- only when quoted, because a
        # bare comma is ordinary prose and would drag in unrelated text.
        rest = a[2:].lstrip(MARKUP)
        if rest[:1] in "“\"‘":
            span = _matched_span(rest, rest[0])
            if span and len(span.split()) >= 3:
                return (span, "comma-quoted")
    return (None, None)


def gram_hits(reg, ctx_tokens, n):
    g = trigrams(ctx_tokens)
    e = reg[n]
    return len(g & e["grams"]) + len(g & e["title_grams"])


def score_site(reg, ctx_tokens, cited, rare=None):
    """Returns (score_of_cited, best_id, best_score, runner_up_score).

    Two signals, because one is not enough:
      * TRIGRAM overlap catches near-VERBATIM restatement -- which is the actual
        recorded defect shape (P-86: the ten worker prompts "wrote out the FULL
        RULE TEXT beside the id").
      * RARE-TOKEN overlap catches PARAPHRASE. RULES-failopen.md:17 says
        "prints an absence over an error ... exits 1 on NO MATCH and >1 on ERROR"
        under P-80; patterns.md P-81 says "printed the same reassuring absence
        as a genuine no-match". They share NO trigram. Trigrams alone score that
        BARE, i.e. the checker would miss one of the four citations this task was
        dispatched to settle.
    A token is RARE if it occurs in at most RARE_MAX register entries; a token in
    twenty entries discriminates nothing.
    """
    g = trigrams(ctx_tokens)
    toks = set(ctx_tokens)
    if not g and not toks:
        return 0, None, 0, 0
    scores = []
    for n, e in reg.items():
        s = 3 * len(g & e["grams"]) + 3 * len(g & e["title_grams"])
        if rare is not None:
            s += len(toks & e["rare_tokens"])
        if s:
            scores.append((s, n))
    if not scores:
        return 0, None, 0, 0
    scores.sort(reverse=True)
    best_score, best_id = scores[0]
    runner = scores[1][0] if len(scores) > 1 else 0
    mine = dict((n, s) for s, n in scores).get(cited, 0)
    return mine, best_id, best_score, runner


def ranked(reg, ctx_tokens, rare=None):
    """The whole candidate list, best first -- not just the winner.

    Needed because the winner can be SUPPRESSED (see the erratum-shield comment
    in analyse()) and a suppressed winner must not silence the runner-up.
    """
    g = trigrams(ctx_tokens)
    toks = set(ctx_tokens)
    out = []
    for n, e in reg.items():
        s = 3 * len(g & e["grams"]) + 3 * len(g & e["title_grams"])
        if rare is not None:
            s += len(toks & e["rare_tokens"])
        if s:
            out.append((s, n))
    out.sort(reverse=True)
    return out


RARE_MAX = 3
# Fatal tier -- see the two-tier comment in analyse().
FATAL_MIN_GRAMS = 2
FATAL_MIN_SCORE = 9
# The third fatal term, and it REPLACED a raw margin (`best_s - mine >= 9`).
# MEASURED REASON, not taste: the real drifted citation at tasks.json:2427
# ("...the rule they broke (P-80)", which is P-81's rule) scores mine=1,
# best=9, margin=8 -- it missed a 9-point margin by one point, and a threshold
# that a genuine recorded instance misses by one is a threshold fitted to
# nothing. Margin is only ever a PROXY for the thing we actually mean:
# *the sentence does not state the rule it cites at all*. So measure that
# directly. It is also STRICTER where false positives live -- a gloss that
# partly states the cited rule (mine high) can no longer go fatal just because
# some other rule scored higher.
FATAL_MAX_CITED_SCORE = 1


def index_rare_tokens(reg):
    """token -> number of register entries containing it; then pin each entry's
    rare tokens. Computed from the register itself, never hand-listed, so it
    tracks patterns.md as it grows (P-7: assert the property, not today's facts)."""
    df = {}
    per = {}
    for n, e in reg.items():
        ts = set(norm_tokens(e["title"] + " " + e["body"]))
        per[n] = ts
        for t in ts:
            df[t] = df.get(t, 0) + 1
    for n, e in reg.items():
        e["rare_tokens"] = set(t for t in per[n] if df[t] <= RARE_MAX)
    return df


def analyse(reg, files, root, min_evidence, min_margin):
    """min_evidence: trigram hits below which we say 'no rule text detected'
    (a BARE citation) rather than claiming a match.
    min_margin: how far the best-matching OTHER rule must beat the cited rule
    before we call it a MISDIRECTING citation."""
    findings = []
    counts = {"sites": 0, "definition": 0, "bare": 0, "consistent": 0,
              "misdirecting": 0, "undefined": 0, "negative_control": 0}
    defn_lines = set()
    for e in reg.values():
        defn_lines.add((PATTERNS_REL, e["line"]))
    for rel in files:
        if rel.startswith(SELF_OUTPUT_PREFIX):
            counts["skipped_self_output"] = counts.get("skipped_self_output", 0) + 1
            continue
        if rel == SELF_SOURCE_EXACT:
            # Counted and PRINTED, never silently dropped -- P-40: a sweep that
            # skips must say what it skipped and how many.
            counts["skipped_self_source"] = counts.get("skipped_self_source", 0) + 1
            continue
        ap = os.path.join(root, rel)
        if not os.path.isfile(ap):
            continue
        try:
            with open(ap, "rb") as fh:
                if b"\0" in fh.read(8192):
                    continue
            lines = read_lines(ap)
        except OSError as exc:
            findings.append({"kind": "UNREADABLE", "file": rel, "line": 0,
                             "cited": None, "detail": str(exc),
                             "zone": classify_path(rel), "fatal": False})
            continue
        kind_of_file = classify_path(rel)
        for i, raw in enumerate(lines):
            for m in CITE.finditer(raw):
                n = int(m.group(1))
                counts["sites"] += 1
                if (rel, i + 1) in defn_lines:
                    counts["definition"] += 1
                    continue
                if n not in reg:
                    if n in NEGATIVE_CONTROL_IDS:
                        counts["negative_control"] += 1
                        continue
                    counts["undefined"] += 1
                    findings.append({
                        "kind": "UNDEFINED", "file": rel, "line": i + 1, "cited": n,
                        "detail": "P-%d is defined in neither register" % n,
                        "text": raw.strip()[:220], "zone": kind_of_file,
                        "fatal": kind_of_file == "directive"})
                    continue
                joined = raw + " " + (lines[i + 1] if i + 1 < len(lines) else "")
                # A citation may name SEVERAL rules for one sentence:
                # `**P-22 / P-36** — a control that cannot fire is worse than
                # none`. The gloss then legitimately states only one of them.
                # Collect the ids in the same cluster so the other members do
                # not each get reported as drifted.
                cluster = cluster_ids(joined, m.start(), m.end())
                gloss, how = extract_gloss(joined, m.start(), m.end())
                if gloss is None:
                    counts["bare"] += 1
                    findings.append({
                        "kind": "BARE", "file": rel, "line": i + 1, "cited": n,
                        "detail": "the id carries no sentence -- nothing binds it to a rule",
                        "text": raw.strip()[:220], "zone": kind_of_file,
                        "fatal": False})
                    continue
                gtoks = norm_tokens(gloss)
                mine, best, best_s, runner = score_site(reg, gtoks, n, rare=True)
                # ------------------------------------------------------------
                # THE ERRATUM SHIELD, and it was found by driving this checker
                # RED on real bytes rather than by reading it.
                #
                # Cross-reference suppression (below) exempts a citation when
                # the better-matching rule ITSELF names the cited id. P-86 is an
                # ERRATUM: its body names P-78..P-84 precisely in order to say
                # those citations are WRONG. So P-86 out-ranked P-81 on the real
                # drifted line `**P-80**: prints an absence over an error.
                # `grep` exits 1 on NO MATCH and >1 on ERROR` (a tie at 6, broken
                # toward the higher id), was suppressed because P-86 names P-80,
                # and the finding vanished. THE ERRATUM WAS SHIELDING EXACTLY THE
                # CITATIONS IT WAS WRITTEN TO CORRECT -- a fail-open whose blast
                # radius is the entire population this task exists to measure.
                #
                # Fix: a SUPPRESSED winner does not get to silence the field.
                # Walk down the ranked candidates and grade against the best one
                # that is not exempt. This is a rule, not an allowlist for P-86:
                # any future erratum, and any rule that quotes its neighbours,
                # behaves the same way.
                # ------------------------------------------------------------
                #
                # `evidence_s` is the GLOBAL best INCLUDING the cited rule, and
                # it decides only one thing: whether this gloss states ANY
                # registered rule at all (below `min_evidence` = BARE). It must
                # NOT be the fall-through winner, or a citation whose own rule
                # matches perfectly would be reported BARE whenever no OTHER
                # rule happened to score -- a bug this file shipped for exactly
                # one run and which showed up as `consistent` collapsing
                # 333 -> 91 on the live tree.
                evidence_s = max(best_s, mine)
                suppressed = []
                best, best_s = None, 0
                for s_, cand in ranked(reg, gtoks, rare=True):
                    if cand == n or cand in cluster or n in reg[cand]["names_ids"]:
                        if cand != n and s_ > mine:
                            suppressed.append((cand, s_))
                        continue
                    best, best_s = cand, s_
                    break
                if best is None:
                    best, best_s = n, mine
                if evidence_s < min_evidence:
                    counts["bare"] += 1
                    findings.append({
                        "kind": "BARE", "file": rel, "line": i + 1, "cited": n,
                        "detail": "gloss (%s) matches no registered rule "
                                  "(best trigram score %d < %d): %r"
                                  % (how, evidence_s, min_evidence, gloss[:140]),
                        "text": raw.strip()[:220], "zone": kind_of_file,
                        "fatal": False})
                elif (best != n and best_s >= min_evidence
                        and (best_s - mine) >= min_margin):
                    # TWO TIERS, because the two decisions have different costs.
                    # REPORTING is generous: a human reads it, a false positive
                    # costs a paragraph. Being FATAL stops the program, so it is
                    # conservative and demands corroboration -- at least
                    # FATAL_MIN_GRAMS shared TRIGRAMS with the better-matching
                    # rule (near-verbatim restatement, the recorded defect
                    # shape), not merely a pile of rare tokens. A single-signal
                    # fatal predicate would stop every graded run on a
                    # paraphrase, which is the fail-closed-too-eagerly failure
                    # this checker was told to avoid.
                    gh = gram_hits(reg, norm_tokens(gloss), best)
                    high_conf = (gh >= FATAL_MIN_GRAMS
                                 and best_s >= FATAL_MIN_SCORE
                                 and mine <= FATAL_MAX_CITED_SCORE)
                    # CROSS-REFERENCE SUPPRESSION is applied ABOVE, in the
                    # ranked walk, and it is load-bearing. patterns.md rules
                    # quote each other by number: P-34's table row ends
                    # "(P-33)", P-26's opening line says "P-21 already said".
                    # A gloss that correctly states the CITED rule therefore
                    # scores high against the QUOTING rule, and a naive checker
                    # calls the correct citation drifted. So a candidate whose
                    # own body names the cited id is skipped -- but only SKIPPED,
                    # never allowed to end the search (the erratum shield).
                    counts["misdirecting"] += 1
                    findings.append({
                        "kind": "MISDIRECTING", "file": rel, "line": i + 1, "cited": n,
                        "detail": "gloss (%s) %r matches P-%d (%d) better than the cited "
                                  "P-%d (%d); patterns.md P-%d = %r"
                                  % (how, gloss[:140], best, best_s, n, mine,
                                     best, reg[best]["title"][:110]),
                        "best": best, "gloss": gloss[:300], "how": how,
                        "grams": gh, "score": best_s, "cited_score": mine,
                        "high_confidence": high_conf,
                        "suppressed_higher": suppressed,
                        "text": raw.strip()[:220], "zone": kind_of_file,
                        "fatal": kind_of_file == "directive" and high_conf})
                else:
                    if suppressed:
                        counts["cross_referenced"] = counts.get("cross_referenced", 0) + 1
                    counts["consistent"] += 1
    return findings, counts


def tracked_files(root):
    r = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return None
    return [f for f in r.stdout.decode("utf-8", "replace").split("\0") if f]


# --------------------------------------------------------------------------
# selftest: synthetic fixtures only. Proves the predicate DISCRIMINATES.
# --------------------------------------------------------------------------
SELFTEST_REGISTER = [
    "## P-80 — A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED",
    "The count is the same defect as the line number. Derive the count from the pin.",
    "",
    "## P-84 — EXIT 2 WITH NO PROBE LINE IS THE GUARD WORKING",
    "Read the absence, not the value. Test the probe line presence before its value.",
    "",
    "## P-81 — THE FAIL-OPEN GUARD CAUGHT THREE WORKERS OWN INSTRUMENTS",
    "git grep exits 1 on no match and greater than 1 on error, so a bad pathspec prints absence.",
    "",
]


def selftest():
    reg, coll, _ = build_register(SELFTEST_REGISTER, (DEFN_HEAD, DEFN_BOLD))
    index_rare_tokens(reg)
    cases = [
        # (label, line, cited-id, expected kind)
        ("drifted (colon gloss): P-84's rule shipped under P-80 -- the recorded defect",
         "Per P-80: read the absence, not the value -- test the probe line presence "
         "before its value, because exit 2 with no probe line is the guard working.",
         "MISDIRECTING"),
        ("repaired: same sentence, correct id",
         "Per P-84: read the absence, not the value -- test the probe line presence "
         "before its value, because exit 2 with no probe line is the guard working.",
         "CONSISTENT"),
        ("drifted (parenthetical gloss)",
         'This is P-80 ("read the absence, not the value: exit 2 with no probe line '
         'is the guard working") applied to the manifest.',
         "MISDIRECTING"),
        ("repaired parenthetical",
         'This is P-84 ("read the absence, not the value: exit 2 with no probe line '
         'is the guard working") applied to the manifest.',
         "CONSISTENT"),
        ("drifted (trailing-id gloss)",
         "Read the absence, not the value; exit 2 with no probe line is the guard "
         "working (P-80).",
         "MISDIRECTING"),
        ("STATED BLIND SPOT, asserted so it cannot rot into a surprise: an unquoted "
         "comma clause is NOT treated as a gloss, so this drifted site scores BARE",
         "Per P-80, read the absence not the value, exit 2 with no probe line is the "
         "guard working.",
         "BARE"),
        ("drifted: git-grep-exit-code rule (P-81) cited as P-80",
         "P-80 -- git grep exits 1 on no match and greater than 1 on error, so a "
         "bad pathspec prints absence.",
         "MISDIRECTING"),
        ("repaired: same sentence, correct id",
         "P-81 -- git grep exits 1 on no match and greater than 1 on error, so a "
         "bad pathspec prints absence.",
         "CONSISTENT"),
        ("bare citation carries no rule text",
         "This is P-80 again.", "BARE"),
        ("undefined id",
         "As required by P-77 the scope is a property of that gate.", "UNDEFINED"),
        ("correct id with correct text -- the control that must stay green",
         "P-80: a corrected cardinal rots in every place it was restated; the count "
         "is the same defect as the line number.",
         "CONSISTENT"),
    ]
    ok = True
    print("SELFTEST -- synthetic fixtures, no repo file read")
    print("  register parsed from fixture: %s  collisions=%d" % (sorted(reg), len(coll)))
    for label, line, expect in cases:
        got = "CONSISTENT"
        m = CITE.search(line)
        if m is None:
            got = "NO-CITATION"
        else:
            n = int(m.group(1))
            if n not in reg:
                got = "UNDEFINED"
            else:
                gloss, how = extract_gloss(line, m.start(), m.end())
                if gloss is None:
                    got = "BARE"
                else:
                    mine, best, best_s, _ = score_site(reg, norm_tokens(gloss), n, rare=True)
                    if best_s < 3:
                        got = "BARE"
                    elif best != n and (best_s - mine) >= 3:
                        got = "MISDIRECTING"
        mark = "PASS" if got == expect else "FAIL"
        ok = ok and got == expect
        print("  [%s] expect %-13s got %-13s  %s" % (mark, expect, got, label))
    print("SELFTEST: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", metavar="PATH", help="write full findings as JSON")
    ap.add_argument("--min-evidence", type=int, default=6)
    ap.add_argument("--min-margin", type=int, default=6)
    ap.add_argument("--show", choices=["fatal", "all"], default="fatal")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    root = os.path.abspath(args.root)
    pm = os.path.join(root, PATTERNS_REL)
    if not os.path.isfile(pm):
        print("PNUMBER-CITATIONS: CANNOT RUN -- register %s not found under %s" % (PATTERNS_REL, root))
        return 3
    lines = read_lines(pm)
    reg, collisions, order = build_register(lines, (DEFN_HEAD, DEFN_BOLD))
    index_rare_tokens(reg)
    if len(reg) < 10:
        print("PNUMBER-CITATIONS: CANNOT RUN -- register parsed %d ids, "
              "which is not a register. Refusing to grade." % len(reg))
        return 3

    gates_path = os.path.join(root, GATES_REL)
    greg = {}
    if os.path.isfile(gates_path):
        greg, _, _ = build_register(read_lines(gates_path), (DEFN_GATES,))

    files = tracked_files(root)
    if files is None:
        print("PNUMBER-CITATIONS: CANNOT RUN -- `git ls-files` failed under %s" % root)
        return 3

    findings, counts = analyse(reg, files, root, args.min_evidence, args.min_margin)

    gaps = [n for n in range(1, max(reg) + 1) if n not in reg]
    cross = sorted(set(reg) & set(greg))

    fatal = [f for f in findings if f["fatal"]]
    # Register integrity is fatal on its own terms: an id defined twice makes
    # EVERY citation of it ambiguous, which is the defect one layer up.
    declared = set()
    dm = DECLARED_MARKER.search("\n".join(lines))
    if dm:
        declared = set(int(x) for x in re.findall(r'[0-9]+', dm.group(1)))

    register_fatal = []
    declared_seen = []
    for c in collisions:
        msg = ("REGISTER COLLISION P-%d defined twice in %s: :%d %r  vs  :%d %r"
               % (c["id"], PATTERNS_REL, c["first_line"], c["first_title"][:80],
                  c["again_line"], c["again_title"][:80]))
        if c["id"] in declared:
            declared_seen.append(c["id"])
            print("PNUMBER-CITATIONS: report DECLARED-AMBIGUOUS " + msg)
        else:
            register_fatal.append(msg)
    # A declaration for an id that is NOT actually colliding is itself rot: it
    # would silence a future genuine collision on that id. Fatal.
    for n in sorted(declared - set(declared_seen)):
        register_fatal.append(
            "REGISTER DECLARATION IS STALE: P-%d is declared ambiguous in %s but has "
            "exactly one definition. A stale declaration pre-silences a future real "
            "collision -- remove it." % (n, PATTERNS_REL))
    for n in gaps:
        register_fatal.append("REGISTER GAP P-%d: cited ids may resolve to nothing" % n)

    print("PNUMBER-CITATIONS: register=%s ids=%d gaps=%s in-file-collisions=%d "
          "cross-register-collisions=%s"
          % (PATTERNS_REL, len(reg), gaps or "none", len(collisions), cross or "none"))
    print("PNUMBER-CITATIONS: sites=%d definition=%d consistent=%d bare=%d "
          "misdirecting=%d undefined=%d negative-control=%d"
          % (counts["sites"], counts["definition"], counts["consistent"],
             counts["bare"], counts["misdirecting"], counts["undefined"],
             counts["negative_control"]))
    print("PNUMBER-CITATIONS: skipped self-output-files=%d self-source-files=%d "
          "(stated, not silent -- both contain deliberately drifted text)"
          % (counts.get("skipped_self_output", 0), counts.get("skipped_self_source", 0)))
    z = {}
    for f in findings:
        if f["kind"] in ("MISDIRECTING", "UNDEFINED"):
            z[(f["zone"], f["kind"])] = z.get((f["zone"], f["kind"]), 0) + 1
    for (zone, kind), c in sorted(z.items()):
        print("PNUMBER-CITATIONS:   %-9s %-12s %d" % (zone, kind, c))

    for msg in register_fatal:
        print("PNUMBER-CITATIONS: FATAL " + msg)

    show = findings if args.show == "all" else fatal
    for f in show:
        print("PNUMBER-CITATIONS: %s %s %s:%d P-%s -- %s"
              % ("FATAL" if f["fatal"] else "report", f["kind"], f["file"], f["line"],
                 f["cited"], f["detail"]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"root": root, "register_ids": sorted(reg),
                       "register_gaps": gaps,
                       "register_collisions": collisions,
                       "cross_register_collisions": cross,
                       "counts": counts,
                       "thresholds": {"min_evidence": args.min_evidence,
                                      "min_margin": args.min_margin},
                       "zones": {"directive_exact": list(DIRECTIVE_EXACT),
                                 "directive_prefix": list(DIRECTIVE_PREFIX),
                                 "evidence_prefix": list(EVIDENCE_PREFIX)},
                       "negative_control_ids": dict(
                           (str(k), v) for k, v in NEGATIVE_CONTROL_IDS.items()),
                       "findings": findings}, fh, indent=1, ensure_ascii=False)

    n_fatal = len(fatal) + len(register_fatal)
    if n_fatal:
        print("PNUMBER-CITATIONS: VERDICT FAIL -- %d fatal (register %d, directive-file %d)"
              % (n_fatal, len(register_fatal), len(fatal)))
        return 1
    print("PNUMBER-CITATIONS: VERDICT PASS -- 0 fatal; %d report-only findings in "
          "committed evidence (corrected FORWARD in patterns.md, never edited in place)"
          % sum(1 for f in findings if not f["fatal"]
                and f["kind"] in ("MISDIRECTING", "UNDEFINED")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
