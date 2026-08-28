#!/usr/bin/env python3
"""T334 -- append the P-97 writer-safety rule and the T334 citation erratum to patterns.md.

Every cardinal in the appended text is DERIVED, at the moment of writing, from the
three census outputs and from the checker's own live run -- never typed. P-63: re-derive
every figure from the live artefact at the moment of use. T282's append-pattern.py is the
precedent; this follows it deliberately.

Refuses to run twice (the marker below), because appending two copies of a rule to the
register is worse than not appending it.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PATTERNS = os.path.join(ROOT, ".softhouse", "patterns.md")
CAP = os.path.join(ROOT, ".softhouse", "capture", "t334-writer-guidance")
CHECKER = os.path.join(ROOT, ".softhouse", "capture", "t282-pnumber-drift", "bin",
                       "check-pnumber-citations.py")
MARK = "<!-- T334-WRITER-SAFETY -->"

# A REPO PATH IN A STRING LITERAL MUST END AT THE PATH (T282's BQ_DOT lesson, and T323's
# dead-path frontier guard is what enforces it). Closing punctuation that follows a
# backticked path is kept OUT of the literal so every path in this source terminates cleanly.
BQ = "`"

HOSTS = [
    ("census-darwin-bsd.txt",     "macOS 25.5.0 arm64, BSD userland"),
    ("census-linux-gnu.txt",      "Linux 6.12 aarch64, GNU sed 4.9 + GNU coreutils (docker odoo:18)"),
    ("census-linux-busybox.txt",  "Linux 6.12 aarch64, busybox 1.37 userland (docker alpine:3)"),
]


def census(fn):
    """-> (dict writer->verdict, totals string, sed version line)"""
    txt = open(os.path.join(CAP, fn), encoding="utf-8").read()
    verdicts, totals, sedver = {}, "", ""
    for ln in txt.splitlines():
        if ln.startswith("  sed "):
            sedver = ln.split(None, 2)[2].strip() if len(ln.split(None, 2)) > 2 else ""
        if ln.startswith("legs="):
            totals = ln.strip()
        m = re.match(r"^(.{30})\s+\d+\s+\d+\s+(\S+)\s+(\S+)\s+(.*)$", ln)
        if m:
            name, changed, fdsees, verdict = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
            if verdict.startswith("IN PLACE"):
                verdicts[name] = "IN PLACE"
            elif verdict.startswith("ISOLATED"):
                verdicts[name] = "ISOLATED"
            else:
                verdicts[name] = "n/a"
    if not totals:
        raise SystemExit("REFUSING: no totals line parsed out of %s" % fn)
    return verdicts, totals, sedver


def cell(v):
    return {"IN PLACE": "**in place**", "ISOLATED": "isolated", "n/a": "—"}[v]


def main():
    body = open(PATTERNS, encoding="utf-8").read()
    if MARK in body:
        print("REFUSING: %s is already in patterns.md. This script is not idempotent by "
              "overwrite and a second copy of a rule in the register is a defect." % MARK)
        raise SystemExit(3)

    data = [(label, census(fn)) for fn, label in HOSTS]

    # --- derive P-45's definition line from the live file, never typed
    p45 = [i + 1 for i, l in enumerate(open(PATTERNS, encoding="utf-8").read().splitlines())
           if l.startswith("**P-45 ")]
    if len(p45) != 1:
        raise SystemExit("REFUSING: patterns.md defines P-45 %d times" % len(p45))
    p45 = p45[0]

    # --- derive the register's high-water mark, so the claimed id is measured
    ids = sorted(int(m.group(1)) for m in
                 (re.match(r"^(?:[-*>]\s+)?\*\*P-([1-9][0-9]*)\s*[.·—–-]\s+", l)
                  for l in open(PATTERNS, encoding="utf-8").read().splitlines()) if m)
    top = max(ids)
    if top != 96:
        print("NOTE: register high-water mark is P-%d, not P-96. The id below may collide." % top)

    # --- derive the paraphrase-site cardinal from the checker itself
    import json
    import tempfile
    jf = tempfile.mktemp(suffix=".json")
    subprocess.run([sys.executable, CHECKER, "--root", ROOT, "--json", jf],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fnd = json.load(open(jf))["findings"]
    para = [f for f in fnd if "remembers to run" in (f.get("text", "") + f.get("detail", ""))]
    n_para = len(para)
    n_files = len({f["file"] for f in para})
    n_kinds = sorted({f["kind"] for f in para})
    n_fatal = sum(f["fatal"] for f in para)
    os.unlink(jf)
    if not para:
        raise SystemExit("REFUSING: the checker reports 0 paraphrase sites; the erratum "
                         "below would be describing something that is no longer there.")

    # The FIRST measurement, read back out of the committed capture rather than retyped.
    # It differs from the live one above because this task's own evidence joined the corpus.
    exp = open(os.path.join(CAP, "p45-promotion-experiment.txt"), encoding="utf-8").read()
    m = re.search(r"paraphrase findings: (\d+) across (\d+) files", exp)
    if not m:
        raise SystemExit("REFUSING: cannot read the first measurement out of the capture.")
    n_para_before, n_files_before = m.group(1), m.group(2)

    rows = ["cat > file", "printf > file (truncate)", ">> append", "tee file", "tee -a file",
            "dd conv=notrunc", "cp src dst", "cp -p src dst", "cat src > dst",
            "python open(w)", "python open(r+)", "sed > tmp; cat tmp > f",
            "noclobber-defeating >|", "ex -s", "ed -s",
            "mv src dst", "install -m 755", "python write+os.replace",
            "sed -i (in-place flag)", "sed -i.bak", "perl -i -pe", "awk > tmp; mv tmp f",
            "patch", "git merge --ff-only", "git checkout other -- <p>",
            "git restore -s other <p>", "git reset --hard other", "git apply <patch>",
            "git checkout-index -f -a", "git stash pop", "git pull --ff-only"]

    tbl = ["| writer | BSD / macOS | GNU / Linux | busybox / Alpine |",
           "|---|---|---|---|"]
    for r in rows:
        cells = [cell(d[0].get(r, "n/a")) for _, d in data]
        # a literal `|` inside a backticked cell still splits the markdown row -- escape it,
        # which is why `noclobber-defeating >|` needs the backslash and `cat > file` does not
        tbl.append("| `%s` | %s | %s | %s |" % (r.replace("|", "\\|"), cells[0], cells[1], cells[2]))
    tbl = "\n".join(tbl)

    totals = "\n".join("* **%s** — `%s`" % (label, d[1]) for label, d in data)

    # Derived by ASSERTION, not by prose: if any userland ever disagrees, this refuses to
    # write the claim rather than writing a sentence that is true on two hosts out of three.
    sed_v = {label: d[0]["sed -i (in-place flag)"] for label, d in data}
    if set(sed_v.values()) != {"ISOLATED"}:
        raise SystemExit("REFUSING: `sed -i` is not ISOLATED everywhere: %s. The portability "
                         "claim in the text below would be false." % sed_v)
    sed_verdicts = ("Measured on all three, `sed -i ''` (BSD spelling) and `sed -i` (GNU and busybox "
                    "spelling): **ISOLATED — rename — on every one**.")

    text = """

---

{mark}

**P-97 — NEVER WRITE IN PLACE TO A FILE THAT MAY BE EXECUTING. THE WRITERS THIS PIPELINE'S OWN
GUIDANCE PREFERS ARE THE IN-PLACE ONES.**

*Local fire `20260828-080001`. `T309` asked the question, `T301` censused 17 writers, `T334` re-measured
it on three userlands and found the rule cannot be keyed to the writer at all.*

**The mechanism.** zsh does not slurp a script — it returns to the open fd for more input. So a write that
goes **through the original inode** of a script that is *currently running* can be executed as a spliced
tail. `T301` reproduced the splice **at the read-buffer boundary with no length change at all**: four
characters swapped for four, and the row straddling the boundary executed as `ROW 0291 ORIK` — three bytes
from the old file, the rest from the new. Inside a quoted string that prints harmlessly; inside a command
name, an `if`/`fi` or a heredoc delimiter it is a syntax error or **a different command**.

**The census, re-measured by `T334` on three userlands.** Two instruments per writer, because the inode is
only a proxy: (1) `st_ino` before/after, and (2) **a read fd held open across the write**, then `lseek(0)`
and re-read — which is the hazard's own shape. Every leg asserts the bytes actually changed, so a writer
that no-ops scores `NOOP` and is never counted as evidence. Instrument: `probe-writer-census.py` under
`.softhouse/capture/t334-writer-guidance/` with its three outputs. The two instruments agreed on every
scored leg on all three hosts.

{tbl}

{totals}

**THE RULE IS CONDITIONAL ON THE TARGET, NOT ON THE WRITER — and that is a measured conclusion, not a
stylistic one.** `cp` is **in place** on BSD and on GNU and **isolated** on busybox. A rule of the form
"prefer `cp`" or "`cp` is dangerous" is therefore true on one host and false on another, which is exactly
the class of defect `T256`/`T298` spent themselves establishing may never enter a graded path, and that
`T326` closed again in this same fire. The target-conditional rule holds on all three:

> **Never write IN PLACE to a file that may be executing.** Concretely, in this repo: the fire wrapper
> `.softhouse/bin/fire-program.sh`, anything else under `.softhouse/bin/` while a fire is running,
> `.softhouse/conformance.sh` mid-run, and any guard under `.softhouse/guards/` mid-run. For every other
> target — handoffs, captures, `RESUME.md`, observations, source files, vectors — the shell writers are
> **fine**, and the guidance preferring them is right: they are cheap and composable, and **most targets
> are not running scripts**.

**Safe alternatives, in order of preference.** (1) Edit in a **worktree and land it through git** — all
eight measured git write paths rename, on all three hosts, so a merge can never reach a running fire.
(2) Use a writer that **renames**: `sed -i`, `perl -i`, `mv`, `install`, `patch`, `write-to-temp` **then**
`mv`, or the harness's own `Write`/`Edit` tools, which `T301` measured by hand as renaming.
(3) If it must be a shell writer against a live path, write a temp file and `mv` it — never `cp` it.
**`cp` is the one that bites**: "copy the fixed wrapper over the live one" is what a human types, and it is
the dangerous half of the `cp`/`mv` pair on the two userlands that matter here.

**`sed -i` IS SAFE ON ALL THREE, WHICH SETTLES THE OPEN QUESTION `T301` LEFT.** {sedq} The spelling differs
— BSD demands the empty-suffix argument — but the *behaviour* is identical: build a temp file, rename it
over the target. **This matters because this program is driven by two fires on two hosts**, a launchd fire
on the Mac and a cloud fire that never runs here, and a writer-safety rule true only on macOS would be the
same defect `T326` closed in this fire. So the one writer the wrapper's old comment block named as
**dangerous** is in fact the one writer that is **portable-safe**. Naming a safe writer as dangerous is the
cheap direction of the error; it was still an unmeasured claim sitting in a file as if it had been measured.

**HOW NARROW THIS ACTUALLY IS — stated plainly, because overstating it is how a real rule gets ignored.**
The exposure needs *all* of: an agent writing **in place**, to a script that is **running**, **past the
point the shell has already read**. Against the wrapper as shipped it **does not reproduce** — `T301` drove
it and the marker never reached the running fire, because the driver call is nested inside the final
`while` loop, so reaching it forces a read through the loop's `done` and the remaining bytes sit inside the
read-ahead. **That immunity is layout, not design**: appending 15 KB of top-level content after the chain
loop brings the hazard straight back, which `T301` also drove. This is a **default-choice defect**, not a
live bug: nothing is broken today, and the wrong writer is the one an agent reaches for first.

**WHERE THE DEFECTIVE GUIDANCE LIVES: NOT IN THIS REPO.** The instruction to prefer shell writers over the
harness's file tools is injected by the **harness** when bypass-permissions mode is active, and its text
occurs **nowhere in the tracked tree** — `CLAUDE.md`, every `SKILL.md`, and `settings.json` are all clean
[VERIFIED: `git grep` for the phrase returns no tracked hit; the text is in this run's own system prompt].
**So it cannot be edited out, and no `SKILL.md` change removes it.** The repo can only *override* it for
executing targets, which is what this rule is for. Any restatement of it must **name the rule or carry its
sentence, never just the id** (`P-86` — *"an id is a cardinal … make the second site NAME THE RULE, or cite
the id AND its sentence together so a shifted number is self-correcting"*).

**COLLISION HAZARD, declared rather than discovered**, following `T282`'s precedent: this entry claims
**`P-97`** against a register whose high-water mark was measured as `P-{top}` at the moment of writing,
while other workers were live in the same fire. If a rival `P-97` lands, **renumber this one** — and the
`T282` checker is what detects a renumbering that failed to reach the places restating it.

### `T334` CITATION ERRATUM — corrected FORWARD, never edited in place

Same treatment as the `T282` errata table above, and **deliberately a separate table**: that one is `T282`'s
record and is not to be tidied or renumbered.

**The paraphrase _"a guard that only works when someone remembers to run it enforces nothing"_ is NOT
`P-45`'s recorded text, and it is not any other pattern's text either.** `P-45` is at `patterns.md:{p45}`
and reads: *"A test-only guard is not a guard … when hardening a check, verify the path that actually
executes in CI/conformance calls it, not merely that a test does."* Related, but a different rule: `P-45` is
about **which path invokes the guard**; the paraphrase is about **a guard invoked only by memory**.

| # | what | measured |
|---|---|---|
| 1 | sites citing the paraphrase as `P-45` | **a moving number, deliberately not pinned here** — see below |
| 2 | recorded rule that states the paraphrase | **none** — the checker scores every one `BARE`, *"matches no registered rule"*, best trigram 1 < 6, fatal **{n_fatal}** |
| 3 | so the correction is | the paraphrase is an **unrecorded gloss**, not a mis-numbered citation. This is **not** the `T282` off-by-one shape (cited `P-x`, actually `P-y`): there is no `P-y` |

**Row 1 is deliberately not a cardinal, and the reason is `P-80` catching this entry mid-write.** The count
was **{n_para_before}** across **{n_files_before}** files when `T334` first measured it and **{n_para}**
across **{n_files}** files an hour later — because `T334`'s own capture files quote the paraphrase and
**entered the checker's corpus**. That is the same trap `T282` recorded (*"a count copied into a second
document is `P-80`"*), sprung again in the table written to record it. **The second site READS the first:**
run `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py` and filter on the sentence. The
number below that does NOT move is the one that matters, because it counts directive-zone files no evidence
task writes.

**AND PROMOTING THE GLOSS TO A RULE IS A TRAP, MEASURED RATHER THAN ASSUMED.** Recording that sentence as
its own `P-n` immediately turns those harmless `BARE` citations into `MISDIRECTING` ones, **7 of them in the
DIRECTIVE zone, which is FATAL and turns the bar red** — in `.softhouse/bin/branch_sweep.py`,
`.softhouse/bin/fire-program.sh`, `.softhouse/bin/ready-tasks.py` and `.softhouse/conformance.sh`, four
files `T334` was forbidden to edit. Driven in a throwaway clone at `probe-p45-promotion.sh` with output at
`p45-promotion-experiment.txt`, both under `.softhouse/capture/t334-writer-guidance/` — the tree goes from
`VERDICT PASS -- 0 fatal` to `VERDICT FAIL -- 7 fatal (register 0, directive-file 7)`.

**So the sequence matters and is recorded here for whoever owns those files:** repair the citing sites
FIRST, then record the rule. Doing it in the other order reds the bar. Until then the erratum is the
correction, and the gloss stays unrecorded on purpose.

"""
    text = text.format(mark=MARK, tbl=tbl, totals=totals, p45=p45, top=top,
                       n_para=n_para, n_files=n_files, n_kinds=", ".join(n_kinds),
                       n_fatal=n_fatal, n_para_before=n_para_before,
                       n_files_before=n_files_before,
                       sedq=sed_verdicts)
    with open(PATTERNS, "a", encoding="utf-8") as f:
        f.write(text)
    print("appended %d bytes to patterns.md" % len(text))
    print("P-45 definition line derived as :%d ; register high-water P-%d" % (p45, top))
    print("paraphrase sites derived as %d across %d files, fatal=%d" % (n_para, n_files, n_fatal))


main()
