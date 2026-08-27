#!/usr/bin/env python3
"""T179 — a PARSER-based replacement for T156's regex guard-classifier.

WHY THIS EXISTS (P-48, in its purest form).
  T156's sweep (`.softhouse/capture/pathb/t149/t156-sweep-unguarded-mutators.py:58`)
  decided whether a mutating script protects itself with

      GUARD = re.compile(r"(?m)^[^#\\n]*(\\btrap\\b|\\bfinally\\s*:|atexit\\.register"
                         r"|__exit__|contextmanager)")

  i.e. by GREPPING SOURCE TEXT for the word `trap`.  `.softhouse/reviews/t47-probe/
  t47_edit_1.py` scored GUARDED on three occurrences of `trap`, all three inside
  string literals the script WRITES INTO the ratified DEC-1 ADR.  A file was scored
  safe by the prose it was writing, while rewriting a `user`-gated document in place
  with no handler on any exit path.

WHAT THIS TOOL CHANGES.
  1. Python is analysed with `ast`.  A guard is a NODE — `ast.Try` with a `finalbody`,
     an `atexit.register` / `signal.signal` call, or a restoring context manager — and
     it must be REACHABLE FROM THE MUTATION SITE (an enclosing node on the site's own
     ancestor chain, or a whole-process handler that is reachable from module
     execution).  A `try/finally` in another function no longer launders a mutation.
  2. The TARGET of a mutation is read off the mutating call's own ARGUMENT
     EXPRESSION, not off whole-file text.  T156 matched its TARGET regexes anywhere in
     the file, so a script that merely mentioned `.softhouse/vectors` in a comment was
     scored as mutating the vector store.
  3. `SANDBOX` is likewise decided per-site: T156's `SANDBOXY` regex matched
     `tempfile.`/`/tmp/` anywhere in the file and then excused the whole file.
  4. Shell is REFUSED, not guessed — see `classify_shell()`.  The refusals are counted
     in the population table and are a first-class outcome, never a silent skip (P-40).

WHAT THIS TOOL STILL CANNOT DO — read this before quoting its numbers.
  * It cannot classify shell at all (no shell parser in the stdlib; `bashlex` is not
    installed here — checked at runtime and printed).  Every `.sh` file is REFUSED.
  * `GUARDED-PROCESS` means a handler is registered and reachable.  It does NOT mean
    the handler restores THIS artefact; nothing here reads the handler's body for
    intent, and a registration that runs AFTER the mutation is indistinguishable from
    one that runs before by static order alone.  Treat it as "a handler exists on this
    path", i.e. weaker than `GUARDED-FINALLY`.
  * Name resolution is module constants, PLUS ONE INTRA-FILE INTERPROCEDURAL STEP
    (T196-1, from T183's D-1) — a target that is a function PARAMETER is resolved
    from the actual arguments at that function's in-file call sites, scoped to that
    function — PLUS a TRANSITIVE FRAGMENT CLOSURE for targets computed at runtime
    (T205, from T203's F-2; see `ConstResolver.chain`).  A target arriving from
    ANOTHER MODULE still resolves to `UNKNOWN` — and `UNKNOWN` is REPORTED as its
    own scope, never folded into "not a trusted target".
    HISTORY, because it is the argument for the closure: `OUT = os.path.join(ROOT,
    ".softhouse", "vectors", "loanschedule")` with `ROOT` computed from `__file__`
    does not RESOLVE, so before T205 a write through it scored UNKNOWN — and
    `--enforce` does not trip on UNKNOWN.  T203 measured the consequence: two
    rewriters of the LIVE golden vector store, `T57-promote-emi-vectors.py` and
    `.softhouse/handoff/T8-promote-vectors.py`, between them 13 parity vectors
    including the corpus baseline `P-00-baseline-6x7pct.json`, were bare
    truncations that this tool scored clean — while `T74/T61/T64/T58`, whose store
    path is a module constant that RESOLVES, were caught.  One `os.path.join(ROOT,
    …)` apart.
    HISTORY, because it is the argument for the step: before T196 the target was read
    from module constants ONLY, while GUARDS already got the same call-site walk
    (`indirectly_guarded_funcs`).  The gap was a FAIL-OPEN — `--enforce` exited 0 on a
    directory containing exactly the three `t41-probe` rewriters that write through
    `def patch(path, pairs)`, each an unguarded in-place truncation of the ratified
    DEC-1 and two of them of the frozen `contract.go`.
  * Cross-file call graphs are out of scope for MUTATIONS.  A mutation performed by a
    helper in another module is still invisible: this is why the 25 hardened
    `t41-probe` rewriters now report ZERO sites rather than "guarded" — their write
    moved into `t178_guard.py`.  Read that as "not measured here", not as "clean".
  * Cross-file GUARDS get exactly ONE import hop (T196-3, from T183's D-3), and only
    for the two things already recognised locally: a restoring context manager that
    ENCLOSES the site, and a module-scope `atexit`/`signal` registration (including
    one made by calling an imported registrar on a module-live path).  Before T196
    this direction was undisclosed and fail-CLOSED: a file whose mutation was local
    and whose guard was imported scored UNGUARDED and tripped `--enforce` — i.e. the
    check punished the shared-`t178_guard.py` idiom T178 adopted and T187 extended
    across 25 files.  Every excuse the hop grants, and every import it could NOT
    follow, is printed in its own report section.  Two hops are NOT followed.
  * These three steps only ever change the reported SCOPE tag or grant a NAMED,
    printed guard verdict.  Where a widening could have gone fail-open it was closed
    deliberately: per-call-site worst-case-wins on parameter binding, and the ATOMIC
    test is not allowed to consume parameter bindings at all.  Both are commented at
    the point of decision.
  * `subprocess`/`os.system` argv is inspected only when it is a literal list or a
    literal string; a command assembled at runtime is `UNKNOWN`.
  * It reads only what is on disk at the path given.  It is not a git-aware tool.

Exit codes:
  0  sweep completed (report mode), or completed with no UNGUARDED trusted-target site
     (--enforce)
  1  --enforce and at least one UNGUARDED site on a TRUSTED target; or
     --enforce-unknown and at least one UNGUARDED site on an UNRESOLVED target
  2  usage error
  3  ZERO files inspected — an error, never a pass (P-35)
  4  --enforce or --enforce-unknown, and the request named/enumerated at least one
     path, but ZERO of them were Python files this tool could actually parse — an
     error, never a pass (P-35, T212). A non-existent --file path, an --file entry
     that resolves to a directory, an unexpanded glob passed through literally by
     the shell, and a --file list of only .sh files all collapse to this: `results`
     is non-empty (the refusal is counted, per T179's design) but the population
     that could be judged GUARDED/UNGUARDED is empty, so exit 0 would be a pass
     that measured nothing. See T212's handoff for the enumerated routes.

ENFORCEMENT POLARITY (T205 — do not conflate the two directions):
  UNKNOWN fails OPEN and HIDES exposures; a false positive fails CLOSED and only
  cries wolf.  `--enforce` still trips on TRUSTED only, because the measured
  UNKNOWN+UNGUARDED population over this repo is 76 sites in 57 files and making
  that fatal by default turns the instrument off — but every `--enforce` run now
  PRINTS that residual to stderr, so this fail-open can never again be silent, and
  `--enforce-unknown` makes it fatal on a narrow root.  Full argument in `main()`.

A NOTE ON THE POPULATION NUMBER THIS TOOL WAS USED TO PUBLISH.
  T179's handoff F-2 reported "22 unguarded in-place rewriters of a ratified/frozen
  artefact — 17 ADR, 5 contract.go".  That figure was true of this tool's OUTPUT at
  the time and is NOT true of the world: it is exactly the answer produced by
  module-constant-only target resolution, and it is short by the three files whose
  write target is a helper parameter (`edit18.py`, `edit20.py`, `edit21.py`).  The
  settled figure is 25 FILES — 20 writing the ratified DEC-1, 7 writing the frozen
  contract.go, 2 of them writing both, i.e. 27 file-artefact pairs.  T187 (by
  executing all 29 scripts against scratch copies) and T183 (by a whole-repo static
  sweep) derived that independently and blind of each other and agreed exactly; with
  T196-1 applied this tool now reproduces it too, from the pre-fix bytes.
  [VERIFIED: `t41-probe/t196-drive-output.txt`, PROBE E — BASE 22 = 17 + 5,
   T196 25 files / 20 + 7 / 2 both]
  All 25 were hardened by T187 onto the shared guard and t41-probe is clean today
  under this stricter tool [VERIFIED: same transcript, PROBE F — exit 0, 0 UNGUARDED,
  0 UNKNOWN].
"""

import argparse
import ast
import json
import os
import re
import sys
import tempfile

# --------------------------------------------------------------------------
# Verdicts.  Ordered worst-first for file-level roll-up.
# --------------------------------------------------------------------------
UNGUARDED = "UNGUARDED"
GUARDED_FINALLY = "GUARDED-FINALLY"
GUARDED_CM = "GUARDED-CONTEXTMANAGER"
GUARDED_INDIRECT = "GUARDED-FINALLY-INDIRECT"
GUARDED_PROCESS = "GUARDED-PROCESS"
# T196-3 (D-3): the same handler evidence as GUARDED-PROCESS, obtained one import
# hop away.  Kept as its OWN verdict, ranked WEAKEST of the guarding verdicts, so a
# reader can always see which sites are excused only because of an import.
GUARDED_PROCESS_IMPORT = "GUARDED-PROCESS-IMPORTED"
ATOMIC = "ATOMIC"
SANDBOX = "SANDBOX"

VERDICT_ORDER = [UNGUARDED, GUARDED_PROCESS_IMPORT, GUARDED_PROCESS,
                 GUARDED_INDIRECT, GUARDED_CM, GUARDED_FINALLY, ATOMIC, SANDBOX]
GUARDING = {GUARDED_FINALLY, GUARDED_CM, GUARDED_INDIRECT, GUARDED_PROCESS,
            GUARDED_PROCESS_IMPORT}

# Scopes for the mutation TARGET, decided per call site.
TRUSTED = "TRUSTED"        # an artefact a later reader treats as ground truth
UNKNOWN = "UNKNOWN"        # could not resolve the target expression — reported, not dropped
SCRATCH = "SCRATCH"        # provably a temp/sandbox path

# Refusal reasons (files we decline to classify).  Counted, never silent.
REFUSE_SHELL = "REFUSED-SHELL-NO-PARSER"
REFUSE_SYNTAX = "REFUSED-PYTHON-SYNTAXERROR"
REFUSE_DECODE = "REFUSED-UNREADABLE"

# --------------------------------------------------------------------------
# Target classification.  Same four buckets T156 used, so the two sweeps are
# comparable — but applied to the AST-extracted argument expression of the
# mutating call, not to the whole file.
# --------------------------------------------------------------------------
TARGET_RX = [
    ("STORE", re.compile(r"\.softhouse/vectors|STORE_ROOT|/vectors/")),
    ("PORT", re.compile(r"nexus/internal|\.go\b")),
    ("CAPTURE", re.compile(r"\.softhouse/capture|/out/|capture_dir|OUTDIR")),
    ("RIG", re.compile(r"attest\.py|conformance\.sh|contract\.go|PIN\.json|"
                       r"capabilities\.json")),
    ("ADR", re.compile(r"docs/adr|DEC-\d")),
    ("PATTERNS", re.compile(r"patterns\.md|program\.json|tasks\.json|gates\.md|"
                            r"obligations\.md|reference-oracle\.md")),
]
SCRATCH_RX = re.compile(r"tempfile\.|mkdtemp|mkstemp|TemporaryDirectory|"
                        r"NamedTemporaryFile|TMPDIR|(?<![\w.])/tmp/|/var/folders/|"
                        r"\bscratch\b|\btmpdir\b|\btmp_?dir\b", re.I)

# --------------------------------------------------------------------------
# Mutating calls.
# --------------------------------------------------------------------------
# name -> index of the positional argument that names the TARGET being mutated
OS_MUTATORS = {
    "os.replace": 1, "os.rename": 1, "os.remove": 0, "os.unlink": 0,
    "os.rmdir": 0, "os.truncate": 0, "os.chmod": 0, "os.removedirs": 0,
    "shutil.move": 1, "shutil.copy": 1, "shutil.copy2": 1, "shutil.copyfile": 1,
    "shutil.copytree": 1, "shutil.rmtree": 0, "shutil.chown": 0,
}
OPENERS = {"open", "io.open", "codecs.open", "gzip.open"}
# Path methods that mutate the RECEIVER.
PATH_SELF_METHODS = {"write_text", "write_bytes", "unlink", "rmdir", "touch",
                     "mkdir", "chmod"}
# Path methods that mutate the ARGUMENT (`Path(tmp).replace(target)`), and are
# atomic when the receiver is a temp file.  Required to take exactly one positional
# argument and no keywords, which is what separates `Path.replace(dst)` from
# `str.replace(old, new)` — the false friend that made an earlier draft of this tool
# report string substitutions as file mutations.
PATH_DEST_METHODS = {"replace", "rename"}
SUBPROCESS_RUNNERS = {"subprocess.run", "subprocess.call", "subprocess.check_call",
                      "subprocess.check_output", "subprocess.Popen"}
SH_MUTATING_ARGV = re.compile(
    r"(?<![\w./-])(mv|cp|rm|install|truncate|ln|tee|dd|chmod)(?![\w-])|"
    r"sed\s+(-[a-zA-Z]*\s+)*-i|"
    r"git\s+(checkout\s+--|restore|stash)|"
    r">\s*\S")

RESTORING_CM_NAMES = {"contextlib.ExitStack", "ExitStack",
                      "contextlib.AsyncExitStack", "AsyncExitStack"}


def dotted(node):
    """Dotted name of an AST expression, '' if it is not a plain name/attribute."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return base + "." + node.attr if base else node.attr
    return ""


def unparse(node):
    try:
        return ast.unparse(node)
    except Exception:                                       # pragma: no cover
        return "<unparse-unavailable>"


class ConstResolver:
    """Module-level string constants, so `open(STORE_PATH, 'w')` can be scoped.

    Deliberately shallow: literals, `os.path.join` of resolvable parts, `+` of
    resolvable parts, f-string constant fragments.  Anything else -> None, and the
    site is reported as UNKNOWN rather than guessed at.
    """

    TEMP_CALLS = ("tempfile.mkstemp", "tempfile.mkdtemp", "tempfile.NamedTemporaryFile",
                  "tempfile.TemporaryDirectory", "mkstemp", "mkdtemp",
                  "NamedTemporaryFile", "TemporaryDirectory")

    def __init__(self, tree):
        self.consts = {}
        # Names bound to a temp path — `fd, tmp = tempfile.mkstemp(...)` is a tuple
        # assignment, so a literal resolver alone would miss it and then score an
        # atomic `os.replace(tmp, target)` as an unguarded write.
        self.scratch_names = set()
        # PARTIAL expansion: `DOC = os.path.join(W, "docs/adr/DEC-1-....md")` does not
        # resolve (W comes from __file__), but the literal fragments of its assigned
        # expression are still evidence about what DOC names.  Name -> those fragments.
        # Name-based and NOT scope-aware (first assignment wins), so it can mis-attribute
        # a name reused in two functions; it only ever affects the reported SCOPE tag,
        # never the guard verdict, and every site prints its target expression so a
        # reader can adjudicate.
        self.partial = {}
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.Assign):
                continue
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                v = self.resolve(stmt.value)
                if v is not None:
                    self.consts.setdefault(stmt.targets[0].id, v)
                else:
                    frags = [n.value for n in ast.walk(stmt.value)
                             if isinstance(n, ast.Constant)
                             and isinstance(n.value, str)]
                    if frags:
                        self.partial.setdefault(stmt.targets[0].id, "/".join(frags))
            is_temp = isinstance(stmt.value, ast.Call) and \
                dotted(stmt.value.func) in self.TEMP_CALLS
            if not is_temp:
                v = self.resolve(stmt.value)
                is_temp = bool(v and SCRATCH_RX.search(v))
            if not is_temp:
                # `scratch = "/tmp/t61cf-" + tag` does not RESOLVE (tag is runtime),
                # but the literal fragment "/tmp/…" is decisive on its own.  Without
                # this, a /tmp tree that mirrors the repo was scored TRUSTED —
                # measured on .softhouse/capture/t61-halfeven/src/run-counterfactuals.py.
                is_temp = any(isinstance(n, ast.Constant) and
                              isinstance(n.value, str) and SCRATCH_RX.search(n.value)
                              for n in ast.walk(stmt.value))
            if is_temp:
                for tgt in stmt.targets:
                    for n in ast.walk(tgt):
                        if isinstance(n, ast.Name):
                            self.scratch_names.add(n.id)
        # ------------------------------------------------------------------
        # T196-2 (my own, not T183's).  SECOND PASS for `partial`, so a fragment
        # may also come from a module constant referenced BY NAME.
        #
        #     VECTORS = ".softhouse/vectors/loanschedule"      # resolves
        #     path    = os.path.join(VECTORS, FILENAMES[cid])  # does NOT resolve
        #     open(path, "w")                                  # -> UNKNOWN
        #
        # The pass above only harvests `ast.Constant` fragments from the assigned
        # expression, so `path` gets nothing and four real writes into the golden
        # VECTOR STORE score UNKNOWN.  Second pass, because `self.consts` is only
        # complete once the first loop has finished — running this inline would make
        # the result depend on ast.walk's visit order.
        # POLARITY: fail-CLOSED.  It can only ADD evidence about a name, so it can
        # only move a site out of UNKNOWN.  It can move a site into SCRATCH (if the
        # named constant is a temp path) — which is the same fail-open channel the
        # first pass already has, and is why every site prints its target expression.
        # ------------------------------------------------------------------
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.Assign):
                continue
            if not (len(stmt.targets) == 1 and
                    isinstance(stmt.targets[0], ast.Name)):
                continue
            if stmt.targets[0].id in self.consts:
                continue
            frags = []
            for n in ast.walk(stmt.value):
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    frags.append(n.value)
                elif isinstance(n, ast.Name) and n.id in self.consts:
                    frags.append(self.consts[n.id])
            if frags:
                self.partial.setdefault(stmt.targets[0].id, "/".join(frags))
        # ------------------------------------------------------------------
        # T196-1 — ONE INTERPROCEDURAL STEP ON NAMES.  Origin: T183's
        # `PROPOSED-backstep.patch`, re-derived and then made SCOPE-AWARE by T196
        # before it was applied.
        #
        #     def patch(path, pairs):
        #         io.open(path, "w", encoding="utf-8").write(s)   # target is a PARAM
        #     patch("docs/adr/DEC-1-….md", [...])
        #
        # resolves to nothing under module-constant-only resolution, so the site
        # lands in UNKNOWN and `--enforce` exits 0 on a directory of exactly those.
        # This is NOT a new capability: `indirectly_guarded_funcs` already gathers a
        # function's in-file call sites and propagates what they prove INTO its body
        # — it does that for GUARDS and not for NAMES, and the fail-open is entirely
        # in the gap. (T183 called the two steps "mirror-image"; they are in fact the
        # SAME direction — callee looks up its callers — applied to two different
        # facts. That makes this a completion of an existing analysis, not a new one.)
        #
        # WHAT T196 CHANGED vs T183's patch, and why:
        #  (a) keyed by (FUNCTION, PARAMETER), never by bare name.  T183's block fed
        #      the flat `self.partial`, so a parameter named `path` on ANY function
        #      leaked onto every other `path` in the file.  Measured: it tagged the
        #      vector-store writes in four `*-promote-vectors.py` CAPTURE, off the
        #      argument of an unrelated `def sha256(path)`.  Right scope, wrong
        #      reason — and the same channel runs the other way (a /tmp argument
        #      leaking onto a trusted write is a FAIL-OPEN).
        #  (b) a parameter the body REASSIGNS is not bound: the actual argument no
        #      longer describes the name at the write.
        #  (c) `posonlyargs + args`, so the positional index is right on a function
        #      that has positional-only parameters; and keyword actual arguments
        #      (`patch(path=P, …)`) are read too.
        # POLARITY: feeds probe TEXT only, exactly as `partial` does, so it can
        # change the reported SCOPE tag and never a guard verdict.  A wrong TRUSTED
        # cries wolf (fail-closed); a wrong SCRATCH hides (fail-open) — which is why
        # (a) matters and why the target expression is always printed.
        # ------------------------------------------------------------------
        self.param_frags = {}
        _fns = [f for f in ast.walk(tree)
                if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]
        _calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call)]
        for f in _fns:
            rebound = {n.id for st in ast.walk(f)
                       if isinstance(st, (ast.Assign, ast.AugAssign, ast.For))
                       for tg in (st.targets if isinstance(st, ast.Assign)
                                  else [st.target])
                       for n in ast.walk(tg) if isinstance(n, ast.Name)}
            params = list(getattr(f.args, "posonlyargs", [])) + list(f.args.args)
            for i, pname in enumerate(a.arg for a in params):
                if pname in rebound:
                    continue                    # (b)
                per_call = []
                for c in _calls:
                    if dotted(c.func).split(".")[-1] != f.name:
                        continue
                    actual = c.args[i] if len(c.args) > i else None
                    if actual is None:          # (c) keyword form
                        for kw in c.keywords:
                            if kw.arg == pname:
                                actual = kw.value
                    if actual is None:
                        continue
                    one = []
                    for n in ast.walk(actual):
                        if isinstance(n, ast.Constant) and isinstance(n.value, str):
                            one.append(n.value)
                        elif isinstance(n, ast.Name) and n.id in self.consts:
                            one.append(self.consts[n.id])
                        elif isinstance(n, ast.Name) and n.id in self.partial:
                            one.append(self.partial[n.id])
                    if one:
                        per_call.append(one)
                if not per_call:
                    continue
                # (d) WORST CASE WINS, per call site — T196, and this is the half
                # that keeps the step fail-CLOSED.  A naive UNION over call sites is
                # a fail-OPEN channel: one caller passing a `/tmp/…` path makes the
                # merged probe text match SCRATCH_RX, `scope_of` prefers SCRATCH over
                # any target tag, and the site is excused as SANDBOX — even though
                # another caller hands the same helper a ratified artefact.  So if
                # ANY single call site resolves TRUSTED on its own, only the TRUSTED
                # call sites are allowed to describe the parameter.  This mirrors the
                # tool's existing worst-first roll-up in `file_verdict`/VERDICT_ORDER,
                # and it mirrors `indirectly_guarded_funcs`' own conservatism (there,
                # one UNGUARDED call site disqualifies the whole function).
                worst = [one for one in per_call
                         if scope_of("\n".join(one))[0] == TRUSTED]
                frags = [x for one in (worst or per_call) for x in one]
                seen, uniq = set(), []
                for fr in frags:
                    if fr not in seen:
                        seen.add(fr)
                        uniq.append(fr)
                self.param_frags[(f.name, pname)] = "/".join(uniq)
        # `with tempfile.TemporaryDirectory() as tmp:` binds tmp through a withitem,
        # not an Assign — missed by the loop above, and it is the commonest sandbox
        # idiom in this repo.  A selftest rig that builds `<tmp>/.softhouse/capture/...`
        # was scored TRUSTED until this was added.
        for n in ast.walk(tree):
            if isinstance(n, (ast.With, ast.AsyncWith)):
                for item in n.items:
                    ctx = item.context_expr
                    if isinstance(ctx, ast.Call) and \
                            dotted(ctx.func) in self.TEMP_CALLS and \
                            item.optional_vars is not None:
                        for v in ast.walk(item.optional_vars):
                            if isinstance(v, ast.Name):
                                self.scratch_names.add(v.id)
        # Transitive: `sb = mkdtemp(); t149 = os.path.join(sb, ".softhouse/capture/…")`
        # — t149 LOOKS like a trusted capture path and is in fact inside a sandbox.
        # Without this, a scratch tree that mirrors the repo layout is scored TRUSTED.
        # Iterate to a fixpoint; the assignment graph is tiny.
        assigns = [st for st in ast.walk(tree) if isinstance(st, ast.Assign)]
        for _ in range(6):
            grew = False
            for stmt in assigns:
                refs = {n.id for n in ast.walk(stmt.value) if isinstance(n, ast.Name)}
                if not (refs & self.scratch_names):
                    continue
                for tgt in stmt.targets:
                    for n in ast.walk(tgt):
                        if isinstance(n, ast.Name) and n.id not in self.scratch_names:
                            self.scratch_names.add(n.id)
                            grew = True
            if not grew:
                break
        # ------------------------------------------------------------------
        # T205 — THE RUNTIME-COMPUTED-CONSTANT CASE.  Origin: T203's F-2, which is
        # the ROOT CAUSE of T203's F-1 (two live-store truncators, T57 and T8,
        # invisible to `--enforce`), not a second defect.
        #
        #     ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        #     OUT  = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
        #     path = os.path.join(OUT, SLUG[case_id] + ".json")
        #     open(path, "w")                                    # -> UNKNOWN
        #
        # `ROOT` is runtime, so `OUT` does not RESOLVE and lands only in `partial`
        # (fragments ".softhouse"/"vectors"/"loanschedule").  Two things then stop
        # that evidence reaching `path`:
        #   (i)  `partial` DOES NOT CHAIN.  The second pass above harvests a Name
        #        only when it is in `self.consts`; a name that is itself merely
        #        `partial` contributes nothing.
        #   (ii) that pass uses `setdefault`, and pass one already claimed `path`
        #        with the single constant ".json" it does contain — so even the
        #        `consts` lookup never got a chance to run on it.
        # Both together are why T74/T61/T64/T58 (module constant
        # `VECTORS = ".softhouse/vectors/loanschedule"`, which RESOLVES) were caught
        # and T57/T8 were not.  Same write, same store, one `os.path.join(ROOT, …)`
        # apart.  MEASURED: `--enforce` over the pre-hardening T57+T8 alone exits 0.
        #
        # `chain` is that closure, computed by fixpoint and kept SEPARATE from
        # `partial` so nothing existing changes shape.
        # POLARITY — read this before widening it.  This map is consulted ONLY by
        # `probe(..., chain=True)`, and `classify_python` calls that ONLY when the
        # ordinary probe already said UNKNOWN, and honours the result ONLY when it
        # says TRUSTED.  A chain probe that says SCRATCH is DISCARDED and the site
        # stays UNKNOWN.  So this step is strictly fail-CLOSED: it can move a site
        # UNKNOWN -> TRUSTED and it can move nothing anywhere else.  It cannot
        # excuse a site, it cannot create a SANDBOX, and it cannot touch a guard
        # verdict.  Its only failure mode is crying wolf on a site whose fragments
        # look trusted, which is the direction this instrument is allowed to be
        # wrong in — and every such site prints its target expression.
        # ------------------------------------------------------------------
        self.chain = {}
        # The assigned expression is walked ONCE, into an ordered recipe of
        # ("k", literal) / ("n", name) steps; the fixpoint below then re-reads the
        # recipe instead of re-walking the AST.  Not a micro-optimisation: these
        # files carry multi-kilobyte dict and f-string literals, and re-walking
        # them eight times per assignment made the repo sweep unusably slow.
        _recipes = []
        for st in ast.walk(tree):
            if not (isinstance(st, ast.Assign) and len(st.targets) == 1
                    and isinstance(st.targets[0], ast.Name)):
                continue
            nm = st.targets[0].id
            if nm in self.consts:
                continue                # fully resolved already; nothing to add
            steps = []
            for n in ast.walk(st.value):
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    steps.append(("k", n.value))
                elif isinstance(n, ast.Name) and n.id != nm:
                    steps.append(("n", n.id))
            if steps:
                _recipes.append((nm, steps))
        for _ in range(8):
            grew = False
            for nm, steps in _recipes:
                frags = []
                for kind, val in steps:
                    if kind == "k":
                        frags.append(val)
                        continue
                    # first hit wins, richest source first
                    for src in (self.consts, self.chain, self.partial):
                        if val in src:
                            frags.append(src[val])
                            break
                if not frags:
                    continue
                txt = "/".join(dict.fromkeys(frags))
                if self.chain.get(nm) != txt:
                    self.chain[nm] = txt
                    grew = True
            if not grew:
                break

    def resolve(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self.consts.get(node.id)
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                else:
                    inner = self.resolve(v.value) if isinstance(v, ast.FormattedValue) \
                        else None
                    parts.append(inner if inner is not None else "{}")
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            a, b = self.resolve(node.left), self.resolve(node.right)
            if a is not None and b is not None:
                return a + b
            return None
        if isinstance(node, ast.Call):
            name = dotted(node.func)
            if name in ("os.path.join", "posixpath.join", "Path", "pathlib.Path"):
                parts = [self.resolve(a) for a in node.args]
                if all(p is not None for p in parts):
                    return "/".join(p.strip("/") if i else p
                                    for i, p in enumerate(parts))
            if name in ("os.path.abspath", "os.path.dirname", "os.path.realpath",
                        "str", "os.fspath"):
                if node.args:
                    return self.resolve(node.args[0])
        return None

    def probe(self, node, fname=None, chain=False):
        """(resolved_or_None, text_probe).

        The text probe is built from the ARGUMENT SUBTREE only — every string
        constant inside it plus its unparsed form — never from whole-file source.

        `fname` is the name of the function the SITE sits in (None at module scope).
        It is the scope key for T196-1's interprocedural parameter bindings, so a
        parameter named `path` on one function can never describe a `path` in
        another.  Omitting it is safe and merely loses those bindings.

        `chain` (T205) ADDITIONALLY folds in the transitive fragment closure, for
        the runtime-computed-constant case.  With `chain=False` — the default, and
        what every pre-T205 caller gets — the text produced is byte-identical to
        T196's.  See the polarity note on `self.chain`.
        """
        resolved = self.resolve(node)
        pieces = [unparse(node)]
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                pieces.append(n.value)
                continue
            if not isinstance(n, ast.Name):
                continue
            if n.id in self.consts:
                pieces.append(self.consts[n.id])
            elif n.id in self.scratch_names:
                pieces.append("tempfile.")   # marks the subtree as scratch-derived
            elif (fname, n.id) in getattr(self, "param_frags", {}):
                pieces.append(self.param_frags[(fname, n.id)])
            elif n.id in self.partial:
                pieces.append(self.partial[n.id])
            # T205: purely ADDITIVE, and only when explicitly asked for.
            if chain and n.id in getattr(self, "chain", {}):
                pieces.append(self.chain[n.id])
        if resolved:
            pieces.append(resolved)
        return resolved, "\n".join(pieces)


def scope_of(probe_text):
    tags = [name for name, rx in TARGET_RX if rx.search(probe_text)]
    if SCRATCH_RX.search(probe_text):
        return SCRATCH, tags
    if tags:
        return TRUSTED, tags
    return UNKNOWN, []


# --------------------------------------------------------------------------
# Guard reachability
# --------------------------------------------------------------------------
def parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def ancestors(node, parents):
    chain = []
    cur = parents.get(node)
    while cur is not None:
        chain.append(cur)
        cur = parents.get(cur)
    return chain


def enclosing_try_finally(node, parents):
    """The nearest ancestor `try:` WITH a `finally:` that actually covers `node`.

    A node sitting in the `finalbody` itself is NOT covered by that finally.
    """
    child = node
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, ast.Try) and cur.finalbody:
            if not _in_body(child, cur.finalbody):
                return cur
        child = cur
        cur = parents.get(cur)
    return None


def _in_body(child, body):
    return any(child is stmt or child in set(ast.walk(stmt)) for stmt in body)


def enclosing_restoring_with(node, parents, local_cms, imported_cms=()):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.With, ast.AsyncWith)):
            for item in cur.items:
                ctx = item.context_expr
                name = dotted(ctx.func) if isinstance(ctx, ast.Call) else dotted(ctx)
                if name in RESTORING_CM_NAMES or name in local_cms:
                    return cur, name
                if name in imported_cms:
                    return cur, name + " [imported]"
        cur = parents.get(cur)
    return None, None


def local_restoring_cms(tree):
    """Context managers DEFINED IN THIS FILE that plausibly restore state:
    a @contextlib.contextmanager generator whose body contains a `try:` with a
    `finally:`, or a class with an `__exit__` method."""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decs = {dotted(d.func) if isinstance(d, ast.Call) else dotted(d)
                    for d in n.decorator_list}
            if decs & {"contextlib.contextmanager", "contextmanager",
                       "contextlib.asynccontextmanager", "asynccontextmanager"}:
                if any(isinstance(x, ast.Try) and x.finalbody for x in ast.walk(n)):
                    out.add(n.name)
        if isinstance(n, ast.ClassDef):
            if any(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                   m.name in ("__exit__", "__aexit__") for m in n.body):
                out.add(n.name)
    return out


def enclosing_func(node, parents):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parents.get(cur)
    return None


def module_reachable_funcs(tree, parents):
    """Functions reachable from module execution (module body statements that are
    not defs/imports, plus any `if __name__ == '__main__':` block), by intra-file
    call graph.  Used only to decide whether a registered atexit/signal handler is
    on a live path."""
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    seeds = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        seeds.append(stmt)
    reachable, queue = set(), []
    for stmt in seeds:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Call):
                nm = dotted(n.func).split(".")[-1]
                if nm in funcs:
                    queue.append(nm)
    while queue:
        nm = queue.pop()
        if nm in reachable:
            continue
        reachable.add(nm)
        for n in ast.walk(funcs[nm]):
            if isinstance(n, ast.Call):
                sub = dotted(n.func).split(".")[-1]
                if sub in funcs and sub not in reachable:
                    queue.append(sub)
    return reachable, funcs, seeds


def process_handlers(tree, parents, reachable, seeds):
    """atexit.register / signal.signal call nodes that are on a module-live path."""
    live = []
    seed_nodes = set()
    for stmt in seeds:
        seed_nodes.update(ast.walk(stmt))
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = dotted(n.func)
        if name not in ("atexit.register", "signal.signal", "signal.sigaction"):
            continue
        fn = enclosing_func(n, parents)
        if fn is None:
            live.append((name, n.lineno, "module-scope"))
        elif n in seed_nodes:
            live.append((name, n.lineno, "module-scope"))
        elif fn.name in reachable:
            live.append((name, n.lineno, "in %s() [module-reachable]" % fn.name))
        # A registration inside a function nothing calls is NOT live; it is dropped
        # here on purpose, and shows up as an UNGUARDED site rather than as a guard.
    return live


# --------------------------------------------------------------------------
# T196-3 (D-3) — ONE IMPORT LEVEL, FOR GUARDS.
#
# T179's docstring disclosed that a MUTATION performed by a helper in another
# module is invisible.  It did not disclose the other direction: a mutation that
# is LOCAL whose GUARD is imported scored UNGUARDED and tripped `--enforce`.  That
# is the direction that actually fires, and it fires on precisely the shared-guard
# idiom this program asked for and got — T178's `t178_guard.py`, extended by T187
# across 25 files.  An instrument that punishes its own program's hardening pattern
# will be worked around, and then it protects nothing.
#
# WHAT IS FOLLOWED, and it is exactly the two things the tool already recognises
# LOCALLY — no new kind of guard is invented:
#   * a restoring context manager DEFINED in an imported module, when a `with` on it
#     actually ENCLOSES the site  (fail-CLOSED: enclosure is still required);
#   * a module-scope `atexit.register` / `signal.signal` in an imported module,
#     which really is live once the module is imported.  Graded at the SAME weak
#     level T179 already grades a local one, under its own name so it is visible.
#
# WHAT IS NOT FOLLOWED, and this is a REFUSAL, not a clean bill:
#   * more than one hop.  A guard imported by the module you imported is invisible.
#   * anything whose module file cannot be located UNIQUELY by basename under the
#     repo root, or that is not a plain `.py` on disk (stdlib, site-packages, C
#     extensions, namespace packages, dynamic `importlib` loads).  Unresolved and
#     AMBIGUOUS imports are counted and NAMED in the report (P-40), never dropped.
#   * `import *`.
# The one-hop limit is deliberate: each hop widens what can be excused, and this
# instrument's job is to fire.
# --------------------------------------------------------------------------
_INDEX_CACHE = {}
IMPORT_MISSES = {}          # module name -> count, for the report
IMPORT_AMBIGUOUS = {}       # module name -> count, for the report


def _index_root_for(path):
    """Walk up from `path` to the nearest directory holding `.git` or `.softhouse`."""
    d = os.path.dirname(os.path.abspath(path))
    cur = d
    while True:
        if os.path.isdir(os.path.join(cur, ".git")) or \
                os.path.isdir(os.path.join(cur, ".softhouse")):
            return cur
        nxt = os.path.dirname(cur)
        if nxt == cur:
            return d
        cur = nxt


def _module_index(root):
    """basename (without .py) -> sorted list of absolute paths, under `root`."""
    if root in _INDEX_CACHE:
        return _INDEX_CACHE[root]
    idx = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [x for x in dirnames if x != ".git"]
        for fn in filenames:
            if fn.endswith(".py"):
                idx.setdefault(fn[:-3], []).append(os.path.join(dirpath, fn))
    for k in idx:
        idx[k].sort()
    _INDEX_CACHE[root] = idx
    return idx


def _resolve_module(modname, self_path):
    """Absolute path of `modname`'s .py, or None.  Sibling first, then a UNIQUE
    basename match under the repo root.  Ambiguity is a refusal, not a coin toss."""
    if not modname:
        return None
    leaf = modname.split(".")[-1]
    sib = os.path.join(os.path.dirname(os.path.abspath(self_path)), leaf + ".py")
    if os.path.isfile(sib):
        return sib
    hits = _module_index(_index_root_for(self_path)).get(leaf, [])
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        IMPORT_AMBIGUOUS[leaf] = IMPORT_AMBIGUOUS.get(leaf, 0) + 1
    else:
        IMPORT_MISSES[leaf] = IMPORT_MISSES.get(leaf, 0) + 1
    return None


def imported_guards(tree, self_path, parents, reachable, seeds):
    """(imported_cm_names, imported_handler_notes) for ONE import hop.

    `imported_cm_names` are the names as WRITTEN AT THE USE SITE — `alias.cm` for
    `import M as alias`, bare `cm` for `from M import cm` — so no alias is guessed.

    A handler note is produced in TWO cases, and both mirror something the tool
    already does with a LOCAL module:
      (i)  the imported module registers atexit/signal on its own module-live path
           — importing it really does run that registration;
      (ii) THIS file CALLS, on its own module-live path, an imported function whose
           body registers atexit/signal.  `mylib_guard.install_restore(P)` is the
           shape, and it is exactly how T179 already treats a local registration
           made inside a module-reachable function.
    Case (ii) is why the reachability arguments are threaded in: a call from inside
    a function nothing calls is NOT a live registration and is dropped, as locally.
    """
    cms, notes = set(), []
    registrars = {}                 # use-site name -> (module basename, func name)
    seed_nodes = set()
    for stmt in seeds:
        seed_nodes.update(ast.walk(stmt))
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                p = _resolve_module(a.name, self_path)
                if not p:
                    continue
                local = a.asname or a.name.split(".")[0]
                _cm, _h, _reg = _guards_of_module(p)
                cms.update("%s.%s" % (local, c) for c in _cm)
                notes.extend("%s (imported %s)" % (h, os.path.basename(p))
                             for h in _h)
                for rf in _reg:
                    registrars["%s.%s" % (local, rf)] = (os.path.basename(p), rf)
        elif isinstance(n, ast.ImportFrom):
            if n.level:                 # relative import: resolve against own dir
                base = os.path.dirname(os.path.abspath(self_path))
                for _ in range(n.level - 1):
                    base = os.path.dirname(base)
                p = os.path.join(base, (n.module or "").split(".")[-1] + ".py") \
                    if n.module else None
                p = p if p and os.path.isfile(p) else None
            else:
                p = _resolve_module(n.module, self_path)
            if not p:
                continue
            _cm, _h, _reg = _guards_of_module(p)
            for a in n.names:
                if a.name == "*":
                    cms.update(_cm)         # `import *` — names arrive unqualified
                    for rf in _reg:
                        registrars[rf] = (os.path.basename(p), rf)
                else:
                    if a.name in _cm:
                        cms.add(a.asname or a.name)
                    if a.name in _reg:
                        registrars[a.asname or a.name] = (os.path.basename(p),
                                                          a.name)
            notes.extend("%s (imported %s)" % (h, os.path.basename(p)) for h in _h)

    # case (ii) — a MODULE-LIVE call to an imported registrar
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        key = dotted(n.func)
        if key not in registrars:
            continue
        fn = enclosing_func(n, parents)
        live = fn is None or n in seed_nodes or fn.name in reachable
        if live:
            mod, rf = registrars[key]
            notes.append("%s() registers a handler (imported %s), called at "
                         "line %d on a module-live path" % (rf, mod, n.lineno))
    return cms, notes


_GUARDS_OF_MODULE = {}


def _guards_of_module(path):
    """(restoring CM names, module-live handler descriptions, registrar func names)."""
    if path in _GUARDS_OF_MODULE:
        return _GUARDS_OF_MODULE[path]
    out = (set(), [], set())
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            t = ast.parse(f.read())
        p = parent_map(t)
        reach, _f, seeds = module_reachable_funcs(t, p)
        reg = set()
        for fn in ast.walk(t):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if any(isinstance(c, ast.Call) and
                   dotted(c.func) in ("atexit.register", "signal.signal",
                                      "signal.sigaction")
                   for c in ast.walk(fn)):
                reg.add(fn.name)
        out = (local_restoring_cms(t),
               ["%s@%d" % (h[0], h[1]) for h in process_handlers(t, p, reach, seeds)],
               reg)
    except (OSError, UnicodeDecodeError, SyntaxError, RecursionError):
        pass                                # unreadable/unparsable -> no guard found
    _GUARDS_OF_MODULE[path] = out
    return out


def indirectly_guarded_funcs(tree, parents):
    """Functions whose EVERY intra-file call site sits inside a try/finally.

    This is the one interprocedural step taken, and it is deliberately conservative:
    one un-guarded call site disqualifies the function.  A function with zero
    in-file call sites is NOT considered guarded.
    """
    funcs = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    sites = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = dotted(n.func).split(".")[-1]
            if nm in funcs:
                sites.setdefault(nm, []).append(
                    enclosing_try_finally(n, parents) is not None)
    return {nm for nm, flags in sites.items() if flags and all(flags)}


# --------------------------------------------------------------------------
# Mutation-site extraction
# --------------------------------------------------------------------------
def _open_mode(call):
    mode = ""
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        mode = str(call.args[1].value)
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = str(kw.value.value)
    return mode


def mutation_sites(tree, resolver, parents=None):
    """Every mutating call NODE, with the argument expression that names its target.

    `parents` is only used to scope T196-1's parameter bindings for the ONE case
    where this function itself probes an expression (the subprocess argv test).
    """
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = dotted(n.func)

        if name in OS_MUTATORS:
            idx = OS_MUTATORS[name]
            tgt = n.args[idx] if len(n.args) > idx else None
            src = n.args[0] if n.args else None
            out.append({"node": n, "verb": name, "target_node": tgt,
                        "source_node": src if idx == 1 else None})
            continue

        if name in OPENERS:
            mode = _open_mode(n)
            if any(c in mode for c in "wax+"):
                out.append({"node": n, "verb": "%s(mode=%r)" % (name, mode),
                            "target_node": n.args[0] if n.args else None,
                            "source_node": None})
            continue

        if isinstance(n.func, ast.Attribute) and n.func.attr in PATH_SELF_METHODS:
            out.append({"node": n, "verb": "Path.%s" % n.func.attr,
                        "target_node": n.func.value, "source_node": None})
            continue

        if isinstance(n.func, ast.Attribute) and n.func.attr in PATH_DEST_METHODS:
            if len(n.args) == 1 and not n.keywords:
                out.append({"node": n, "verb": "Path.%s" % n.func.attr,
                            "target_node": n.args[0],
                            "source_node": n.func.value})
            continue

        if name in SUBPROCESS_RUNNERS or name in ("os.system", "os.popen"):
            argv_text = None
            if n.args:
                _fn = enclosing_func(n, parents) if parents else None
                resolved, probe = resolver.probe(n.args[0],
                                                 _fn.name if _fn else None)
                argv_text = probe
            if argv_text and SH_MUTATING_ARGV.search(argv_text):
                out.append({"node": n, "verb": "%s(shell)" % name,
                            "target_node": n.args[0], "source_node": None})
            continue
    return out


# --------------------------------------------------------------------------
# Per-file classification
# --------------------------------------------------------------------------
def classify_python(rel, src, abspath=None):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"path": rel, "lang": "python", "refused": REFUSE_SYNTAX,
                "detail": "%s at line %s" % (e.msg, e.lineno), "sites": []}

    parents = parent_map(tree)
    resolver = ConstResolver(tree)
    local_cms = local_restoring_cms(tree)
    reachable, _funcs, seeds = module_reachable_funcs(tree, parents)
    handlers = process_handlers(tree, parents, reachable, seeds)
    indirect = indirectly_guarded_funcs(tree, parents)
    # T196-3: one import hop, for GUARDS only.  Needs the file's real location; when
    # it is unavailable the step is simply not taken and the file is classified
    # exactly as T179 classified it (no import following, so no new excuse).
    if abspath:
        imported_cms, imported_handlers = imported_guards(
            tree, abspath, parents, reachable, seeds)
    else:
        imported_cms, imported_handlers = set(), []

    # P-48 instrumentation: how many guard WORDS live in string literals?  This is
    # what T156's regex was actually counting.  Reported, never used to classify.
    literal_guard_words = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            low = n.value.lower()
            for w in ("trap", "finally", "atexit", "__exit__", "contextmanager"):
                literal_guard_words += low.count(w)

    sites = []
    for m in mutation_sites(tree, resolver, parents):
        node = m["node"]
        _site_fn = enclosing_func(node, parents)
        _site_fn = _site_fn.name if _site_fn else None
        chained = False
        if m["target_node"] is None:
            scope, tags, target_text = UNKNOWN, [], "<no target argument>"
        else:
            resolved, probe = resolver.probe(m["target_node"], _site_fn)
            scope, tags = scope_of(probe)
            target_text = unparse(m["target_node"])[:120]
            # T205 — ESCAPE FROM UNKNOWN, ONE DIRECTION ONLY.  Consulted only when
            # the ordinary probe already failed to say anything, and honoured only
            # when the transitive closure says TRUSTED.  A chain probe returning
            # SCRATCH is DISCARDED (the site stays UNKNOWN) so a runtime-derived
            # fragment can never excuse a write — that would be the fail-OPEN this
            # task exists to close, reintroduced by its own fix.
            if scope == UNKNOWN:
                _r2, probe2 = resolver.probe(m["target_node"], _site_fn, chain=True)
                scope2, tags2 = scope_of(probe2)
                if scope2 == TRUSTED:
                    scope, tags, chained = TRUSTED, tags2, True

        verdict, why = UNGUARDED, "no try/finally, context manager or live handler " \
                                  "encloses this call"

        # ATOMIC beats everything: os.replace of a temp file needs no handler at all.
        if m["verb"] in ("os.replace", "os.rename", "Path.replace",
                         "Path.rename") and m["source_node"] is not None:
            # DELIBERATELY UNSCOPED (T196): no `fname` is passed, so T196-1's
            # parameter bindings never reach the ATOMIC test.  Letting them in would
            # let an actual argument make a SOURCE look like a temp file and so
            # promote a site to ATOMIC — an excuse, i.e. FAIL-OPEN.  The cost of
            # withholding them is a genuinely atomic `os.replace(tmp, dst)` inside a
            # helper being reported UNGUARDED: it cries wolf, which is the direction
            # this instrument is allowed to be wrong in.
            _r, sprobe = resolver.probe(m["source_node"])
            if SCRATCH_RX.search(sprobe):
                verdict, why = ATOMIC, "os.replace() of a temp file — atomic on POSIX"

        if verdict == UNGUARDED and scope == SCRATCH:
            verdict, why = SANDBOX, "target resolves to a temp/scratch path"

        if verdict == UNGUARDED:
            t = enclosing_try_finally(node, parents)
            if t is not None:
                verdict = GUARDED_FINALLY
                why = "enclosed by try/finally at line %d" % t.lineno
        if verdict == UNGUARDED:
            w, nm = enclosing_restoring_with(node, parents, local_cms, imported_cms)
            if w is not None:
                verdict = GUARDED_CM
                why = "enclosed by `with %s` at line %d (restoring CM)" % (nm, w.lineno)
        if verdict == UNGUARDED:
            fn = enclosing_func(node, parents)
            if fn is not None and fn.name in indirect:
                verdict = GUARDED_INDIRECT
                why = "every in-file call of %s() is inside a try/finally" % fn.name
        if verdict == UNGUARDED and handlers:
            verdict = GUARDED_PROCESS
            why = "live process handler: " + "; ".join(
                "%s@%d (%s)" % (h[0], h[1], h[2]) for h in handlers[:3])
        if verdict == UNGUARDED and imported_handlers:
            verdict = GUARDED_PROCESS_IMPORT
            why = "handler registered at module scope in an IMPORTED module: " + \
                  "; ".join(imported_handlers[:3])

        sites.append({"line": node.lineno, "verb": m["verb"], "scope": scope,
                      "target_tags": tags, "target": target_text,
                      "verdict": verdict, "why": why,
                      # T205: this site is TRUSTED only because of the transitive
                      # fragment closure.  Named in the report so a reader can
                      # always separate the widened population from the original.
                      "scope_via_chain": chained})

    n_try_finally = len([n for n in ast.walk(tree)
                         if isinstance(n, ast.Try) and n.finalbody])
    return {"path": rel, "lang": "python", "refused": None, "sites": sites,
            "literal_guard_words": literal_guard_words,
            "live_handlers": [[h[0], h[1], h[2]] for h in handlers],
            "try_finally_nodes": n_try_finally,
            "restoring_cms": sorted(local_cms),
            "imported_cms": sorted(imported_cms),
            "imported_handlers": sorted(imported_handlers),
            # The direct answer to "does this file contain ANY real guard node?",
            # independent of whether any mutation is reachable from it.  This is the
            # number T156's GUARD regex was pretending to report.
            "guard_nodes": n_try_finally + len(handlers) + len(local_cms)}


SHELL_PARSER = None
try:                                                        # pragma: no cover
    import bashlex                                          # noqa: F401
    SHELL_PARSER = "bashlex"
except Exception:
    SHELL_PARSER = None


def classify_shell(rel, src):
    """DOCUMENTED REFUSAL.

    There is no shell parser in the Python standard library, and `bashlex` is not
    installed in this environment (checked at import time; the result is printed in
    the header of every run).  `shlex` is a tokeniser, not a parser: it strips quotes
    and comments — better than a grep — but it cannot tell a `trap` that is *executed*
    from a `trap` inside a here-doc, a function that is never called, or a subshell,
    and it cannot decide reachability at all.

    So this classifier REFUSES every shell file, and the refusals are COUNTED in the
    population table.  A wrong classification of a shell script is exactly the defect
    T179 exists to remove; a counted refusal is not.
    """
    return {"path": rel, "lang": "shell", "refused": REFUSE_SHELL,
            "detail": "no shell parser available (bashlex not installed); "
                      "shlex is a tokeniser, not a parser — refusing rather than "
                      "guessing", "sites": [],
            "bytes": len(src)}


def classify_path(path, rel=None):
    rel = rel or path
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            src = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {"path": rel, "lang": "?", "refused": REFUSE_DECODE,
                "detail": type(e).__name__, "sites": []}
    if path.endswith(".py"):
        return classify_python(rel, src, os.path.abspath(path))
    if path.endswith(".sh") or path.endswith(".bash"):
        return classify_shell(rel, src)
    return {"path": rel, "lang": "?", "refused": "NOT-A-SCRIPT", "sites": []}


def file_verdict(res):
    """Worst site verdict on a TRUSTED or UNKNOWN target; None if no sites."""
    if res.get("refused"):
        return res["refused"]
    if not res["sites"]:
        return None
    ranked = sorted(res["sites"], key=lambda s: VERDICT_ORDER.index(s["verdict"]))
    return ranked[0]["verdict"]


# --------------------------------------------------------------------------
# Sweep
# --------------------------------------------------------------------------
def sweep(root, excludes):
    files, other_ext, excluded = [], {}, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            if any(x in p for x in excludes):
                excluded.append(rel)
                continue
            if fn.endswith((".py", ".sh", ".bash")):
                files.append(p)
            else:
                ext = os.path.splitext(fn)[1] or "<none>"
                other_ext[ext] = other_ext.get(ext, 0) + 1
    files.sort()
    results = [classify_path(p, os.path.relpath(p, root)) for p in files]
    return results, other_ext, excluded


def report(results, other_ext, excluded, root, out=sys.stdout):
    w = out.write
    w("=== T179 parser-based guard classifier\n")
    w("root                : %s\n" % root)
    w("python parser       : ast (stdlib, authoritative for Python)\n")
    w("shell parser        : %s\n" % (SHELL_PARSER or
                                      "NONE — every .sh file is REFUSED, and counted"))
    w("\n")

    py = [r for r in results if r["lang"] == "python" and not r["refused"]]
    refused = [r for r in results if r["refused"]]
    n_sites = sum(len(r["sites"]) for r in py)

    if not results:
        w("ERROR: zero files inspected. That is an error, not a pass (P-35).\n")
        return 3

    w("--- POPULATION, with denominators\n")
    w("  script files enumerated (.py/.sh/.bash)   : %d\n" % len(results))
    w("    of which Python, parsed                 : %d\n" % len(py))
    w("    of which REFUSED                        : %d\n" % len(refused))
    for reason in (REFUSE_SHELL, REFUSE_SYNTAX, REFUSE_DECODE):
        n = len([r for r in refused if r["refused"] == reason])
        if n:
            w("      %-38s: %d\n" % (reason, n))
    w("  non-script files under the same root      : %d (never inspected)\n"
      % sum(other_ext.values()))
    w("    largest uninspected groups              : %s\n"
      % ", ".join("%s %d" % (e, n) for e, n in
                  sorted(other_ext.items(), key=lambda t: -t[1])[:6]))
    if excluded:
        w("  explicitly excluded by --exclude          : %d (%s%s)\n"
          % (len(excluded), ", ".join(excluded[:4]),
             ", …" if len(excluded) > 4 else ""))
    w("  mutation call sites found in Python       : %d\n" % n_sites)
    w("\n")

    # scope x verdict matrix — nothing is dropped
    w("--- MUTATION SITES: scope x verdict (every site appears exactly once)\n")
    matrix = {}
    for r in py:
        for s in r["sites"]:
            matrix[(s["scope"], s["verdict"])] = \
                matrix.get((s["scope"], s["verdict"]), 0) + 1
    w("  %-10s %s\n" % ("scope", "".join("%-26s" % v for v in VERDICT_ORDER)))
    for scope in (TRUSTED, UNKNOWN, SCRATCH):
        row = [matrix.get((scope, v), 0) for v in VERDICT_ORDER]
        w("  %-10s %s   (total %d)\n"
          % (scope, "".join("%-26d" % n for n in row), sum(row)))
    tot = sum(matrix.values())
    w("  %-10s %s   (total %d)\n"
      % ("ALL", "".join("%-26d" % sum(matrix.get((sc, v), 0)
                                      for sc in (TRUSTED, UNKNOWN, SCRATCH))
                        for v in VERDICT_ORDER), tot))
    if tot != n_sites:
        w("  TALLY DOES NOT CLOSE: %d != %d — treat this run as broken\n"
          % (tot, n_sites))
    w("\n")

    trusted_unguarded = [(r, s) for r in py for s in r["sites"]
                         if s["scope"] == TRUSTED and s["verdict"] == UNGUARDED]
    w("--- UNGUARDED MUTATIONS OF A TRUSTED ARTEFACT (%d sites in %d files)\n"
      % (len(trusted_unguarded),
         len({r["path"] for r, _ in trusted_unguarded})))
    for r, s in trusted_unguarded:
        w("  %s:%d  %s  tags=%s\n      target: %s\n"
          % (r["path"], s["line"], s["verb"], ",".join(s["target_tags"]), s["target"]))
    w("\n")

    unknown_unguarded = [(r, s) for r in py for s in r["sites"]
                         if s["scope"] == UNKNOWN and s["verdict"] == UNGUARDED]
    w("--- UNGUARDED MUTATIONS WHOSE TARGET COULD NOT BE RESOLVED (%d sites in %d "
      "files)\n" % (len(unknown_unguarded),
                    len({r["path"] for r, _ in unknown_unguarded})))
    w("    These are NOT clean and NOT dirty. They are unresolved, and they are\n"
      "    printed so nothing is silently dropped (P-40).\n")
    for r, s in unknown_unguarded[:400]:
        w("  %s:%d  %s   target: %s\n" % (r["path"], s["line"], s["verb"], s["target"]))
    w("    ^ DEFAULT `--enforce` DOES NOT TRIP ON THESE. That is a FAIL-OPEN, and it\n"
      "      is the one T203's F-2 measured: two live-vector-store truncators sat in\n"
      "      this section and `--enforce` exited 0. Use `--enforce-unknown` to make\n"
      "      them fatal; see the polarity note in main().\n")
    w("\n")

    # T205: the widened population, named separately so it is always auditable.
    chained = [(r, s) for r in py for s in r["sites"] if s.get("scope_via_chain")]
    w("--- T205: SITES SCOPED ONLY BY THE TRANSITIVE FRAGMENT CLOSURE (%d sites in "
      "%d files)\n" % (len(chained), len({r["path"] for r, _ in chained})))
    w("    Target is `os.path.join(RUNTIME_ROOT, …)`: no module constant resolves it,\n"
      "    so the ordinary probe said UNKNOWN and the chain said TRUSTED. This step\n"
      "    can ONLY move a site UNKNOWN -> TRUSTED; a chain probe returning SCRATCH is\n"
      "    discarded, so it can never excuse a write.\n")
    for r, s in chained[:200]:
        w("  %s:%d  %s  tags=%s  verdict=%s\n      target: %s\n"
          % (r["path"], s["line"], s["verb"], ",".join(s["target_tags"]),
             s["verdict"], s["target"]))
    if not chained:
        w("  none in this root\n")
    w("\n")

    # P-48 detector: files whose guard WORDS live only in string literals.
    w("--- P-48 DETECTOR: files T156's regex would score GUARDED on prose alone\n")
    w("    (guard words present ONLY inside string literals; zero try/finally nodes)\n")
    n_p48 = 0
    for r in py:
        if r.get("literal_guard_words") and not r.get("try_finally_nodes") and \
                not r.get("live_handlers") and r["sites"]:
            n_p48 += 1
            w("  %-64s guard-words-in-literals=%d  sites=%d\n"
              % (r["path"], r["literal_guard_words"], len(r["sites"])))
    if not n_p48:
        w("  none in this root\n")
    w("\n")

    # T196-3: what the one import hop actually did, including what it could NOT do.
    # A guard-checker that follows imports silently is a guard-checker whose excuses
    # cannot be audited, so every excuse and every failure to resolve is printed.
    w("--- T196-3: ONE IMPORT HOP, FOR GUARDS (D-3)\n")
    imp_cm = [r for r in py if r.get("imported_cms")]
    imp_h = [r for r in py if r.get("imported_handlers")]
    excused_cm = [(r["path"], s) for r in py for s in r["sites"]
                  if s["verdict"] == GUARDED_CM and "[imported]" in s["why"]]
    excused_h = [(r["path"], s) for r in py for s in r["sites"]
                 if s["verdict"] == GUARDED_PROCESS_IMPORT]
    w("  files importing a module that defines a restoring CM : %d\n" % len(imp_cm))
    w("  files importing a module with a module-scope handler  : %d\n" % len(imp_h))
    w("  SITES EXCUSED ONLY BY AN IMPORTED CM                  : %d\n" % len(excused_cm))
    for p, s in excused_cm[:40]:
        w("      %s:%d  %s\n" % (p, s["line"], s["why"][:100]))
    w("  SITES EXCUSED ONLY BY AN IMPORTED HANDLER             : %d\n" % len(excused_h))
    for p, s in excused_h[:40]:
        w("      %s:%d  %s\n" % (p, s["line"], s["why"][:100]))
    w("  imports NOT followed — module not found under the repo root: %d distinct\n"
      % len(IMPORT_MISSES))
    if IMPORT_MISSES:
        w("      %s%s\n" % (", ".join(sorted(IMPORT_MISSES)[:18]),
                            ", …" if len(IMPORT_MISSES) > 18 else ""))
    w("  imports NOT followed — AMBIGUOUS basename (refused, never guessed): %d\n"
      % len(IMPORT_AMBIGUOUS))
    if IMPORT_AMBIGUOUS:
        w("      %s%s\n" % (", ".join(sorted(IMPORT_AMBIGUOUS)[:18]),
                            ", …" if len(IMPORT_AMBIGUOUS) > 18 else ""))
    w("  NOTE: exactly ONE hop is taken. A guard reached through two imports is\n"
      "        invisible, and every line above is a REFUSAL, not a clean bill.\n")
    w("\n")

    w("--- REFUSED FILES, NAMED (a refusal is an outcome, not a skip)\n")
    for r in refused:
        w("  %-64s %s\n" % (r["path"], r["refused"]))
    w("  refused total: %d\n" % len(refused))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="directory to sweep (default: the repo's .softhouse/)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="substring of a path to exclude; counted and named")
    ap.add_argument("--json", default=None, help="write full results as JSON")
    ap.add_argument("--enforce", action="store_true",
                    help="exit 1 if any TRUSTED-target site is UNGUARDED")
    ap.add_argument("--enforce-unknown", action="store_true",
                    help="ALSO exit 1 if any UNRESOLVED-target site is UNGUARDED "
                         "(implies --enforce). Fail-closed; see the polarity note.")
    ap.add_argument("--file", action="append", default=[],
                    help="classify these files only (no sweep)")
    args = ap.parse_args(argv)

    if args.file:
        results = [classify_path(os.path.abspath(p), p) for p in args.file]
        other_ext, excluded, root = {}, [], "<explicit file list>"
    else:
        root = args.root
        if root is None:
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, "..", ".."))
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            sys.stderr.write("no such root: %s\n" % root)
            return 2
        results, other_ext, excluded = sweep(root, args.exclude)

    if not results:
        sys.stderr.write("ERROR: zero files inspected — an error, not a pass (P-35)\n")
        return 3

    rc = report(results, other_ext, excluded, root)
    if rc:
        return rc

    if args.json:
        # This tool's own only write.  Done atomically (mkstemp in the target's own
        # directory + os.replace) so that this file's verdict under its own
        # classifier is ATOMIC and not UNGUARDED — P-48 rule 4, and a measuring
        # instrument that fails its own measurement is not one worth quoting.
        d = os.path.dirname(os.path.abspath(args.json)) or "."
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".t179-json-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, args.json)

    # ----------------------------------------------------------------------
    # T205 — ENFORCEMENT POLARITY.  The two directions are NOT symmetric and must
    # not be conflated; conflating them is how this defect class kept recurring.
    #
    #  * UNKNOWN currently FAILS OPEN: an unresolved target HIDES a real exposure.
    #    T203's F-1 is the measurement — `T57-promote-emi-vectors.py` and
    #    `.softhouse/handoff/T8-promote-vectors.py`, between them 13 live parity
    #    vectors including the corpus baseline `P-00-baseline-6x7pct.json`, sat in
    #    the UNKNOWN section while `--enforce` exited 0.  T205's resolver fix is the
    #    remedy for the SHAPE they had; this flag is the remedy for the CLASS.
    #  * A FALSE POSITIVE fails CLOSED: it cries wolf and hides nothing.  T203
    #    measured one (`T58-promote-vectors.py` flagged UNGUARDED because the
    #    classifier cannot see an `os.path.exists` refusal).
    #
    # WHY UNKNOWN IS NOT FOLDED INTO THE DEFAULT `--enforce`.  MEASURED, not
    # estimated, over the whole repo at this commit: after the resolver fix there
    # are 76 UNGUARDED sites with an unresolved target, across 57 files, almost all
    # of them analysis scripts writing a derived `*-output.txt` next to themselves
    # via a runtime `HERE`, plus deliberate RED probes.  Making that fatal by
    # default turns the instrument off, which is worse than the disclosure below.
    # So: the default stays TRUSTED-only, the residual is ALWAYS PRINTED to stderr
    # at the enforcement boundary (a fail-open of this class can no longer be
    # silent), and `--enforce-unknown` is available for a NARROW root where every
    # unresolved write is meant to be adjudicated.
    # ----------------------------------------------------------------------
    if args.enforce or args.enforce_unknown:
        # ------------------------------------------------------------------
        # T212 — an --enforce run whose INSPECTED POPULATION IS ZERO must FAIL,
        # for ANY reason, not just when `results` itself is empty (the `if not
        # results` guard above already covers that case with exit 3).  Here
        # `results` is non-empty — files were named or enumerated — but every
        # single one of them was REFUSED before a single mutation site could be
        # judged: a non-existent --file path (REFUSED-UNREADABLE), a --file
        # entry that resolves to a directory such as the empty string ""
        # (REFUSED-UNREADABLE via IsADirectoryError — what an "empty --file
        # list" collapses to when naively joined/split by a caller), an
        # unexpanded shell glob passed through literally because it matched
        # nothing (REFUSED-UNREADABLE via FileNotFoundError), or a --file list
        # of only .sh files this classifier has no parser for
        # (REFUSED-SHELL-NO-PARSER).  Each of those refusals is correctly
        # COUNTED (P-40 — a refusal is an outcome, never a silent skip), but
        # counting the refusal is not the same as having measured anything, and
        # exiting 0 here is P-35's exact shape: a check that inspected zero
        # items scored a pass. Same failure class as T194's census defect and
        # T181's F-2 (a census that globbed nothing and exited 0).
        #
        # The population that matters for enforcement is "Python files this
        # tool actually parsed" — the same `lang == "python" and not refused`
        # filter `report()` uses to print "of which Python, parsed". A
        # legitimate zero SITES count (a real Python file with no mutations)
        # is not this defect and must keep passing; only zero PARSED FILES is.
        py_inspected = [r for r in results
                        if r.get("lang") == "python" and not r.get("refused")]
        if not py_inspected:
            reasons = sorted({r.get("refused") or "NOT-A-SCRIPT" for r in results})
            sys.stderr.write(
                "ENFORCE-ERROR: zero Python files were successfully parsed — the "
                "inspected population is zero (P-35: a check inspecting zero "
                "items is an ERROR, not a pass; T212). %d path(s) named/"
                "enumerated, ALL refused: %s\n"
                % (len(results), ", ".join(reasons)))
            return 4
        # ------------------------------------------------------------------
        bad = [(r["path"], s) for r in results for s in r.get("sites", [])
               if s["scope"] == TRUSTED and s["verdict"] == UNGUARDED]
        unres = [(r["path"], s) for r in results for s in r.get("sites", [])
                 if s["scope"] == UNKNOWN and s["verdict"] == UNGUARDED]
        sys.stderr.write(
            "ENFORCE-DISCLOSURE: %d unguarded site(s) with an UNRESOLVED target — "
            "%s\n" % (len(unres),
                      "FATAL (--enforce-unknown)" if args.enforce_unknown
                      else "NOT fatal without --enforce-unknown; this is a "
                           "fail-open (T203 F-2)"))
        if bad:
            sys.stderr.write("ENFORCE: %d unguarded mutation(s) of a trusted "
                             "artefact\n" % len(bad))
        if args.enforce_unknown and unres:
            sys.stderr.write("ENFORCE-UNKNOWN: %d unguarded mutation(s) whose target "
                             "could not be resolved\n" % len(unres))
        if bad or (args.enforce_unknown and unres):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
