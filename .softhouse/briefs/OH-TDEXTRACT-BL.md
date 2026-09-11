# OH-TDEXTRACT-BL — Tier D bulk extractor, keyed on the loan, not on file order. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-tdextract` (branch `feat/OHTDEXTRACTbl`)
Work ONLY in that directory. **Start no container. Build nothing. Replay nothing.** **A run works ONLY in its own
worktree.** The driver pushes; never exercise the push gate.

## Read first
`.softhouse/findings/F-2026-09-11-tierd-feasibility.md` — the THIRD PASS §0 and §3: the salvaged extraction
keyed exchanges by FILE ORDER and put loan 1's bodies into loan 10's files; the fix is to key on the
`resourceId` each `POST /loans` returns and follow that loan's command chain.

## The task
Write `.softhouse/capture/tierd-feasibility/bin/extract.py` — a STREAMING extractor over a Feign debug log:
* never loads a whole file (the logs are 147 MB and 243 MB, under
  `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/`);
* parses the Feign framing (`[Api#method] ---> METHOD url` … `---> END HTTP (n-byte body)`, `<--- HTTP/1.1
  status` … `<--- END HTTP`), `json.loads` every body it keeps;
* ATTRIBUTES every loan exchange to its loan id: the `resourceId` in each `POST /loans` response starts a loan;
  commands and reads are attached by the id in their URL;
* writes, per loan: its create request, each command request/response, and its read-backs, as JSON files, plus
  a manifest (source line, bytes, sha256, loan id, HTTP status);
* skips the global initializer's seeding traffic, and says how much it skipped.

**Control-test it before trusting it:** run it on `feign-uc6.log` and assert that its loan-1 and loan-10
files are BYTE-IDENTICAL to the verified files in `.softhouse/capture/tierd-feasibility/uc6/` (a mismatch means
the extractor is wrong, not the files). Then run it on `feign-s1.log` and report the per-loan counts.
Commit the script, its control-test output, and a short `bin/README.md`. **Commit NO extracted bodies from s1**
— only the script and its report (the bodies are reproducible from the log).

## Non-negotiables
- **Do not touch `nexus/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/vectors/`, or
  `.softhouse/maps/`.** No float in any money value it writes (keep bodies byte-exact). The script must not
  quote a path that exists only at run time as a hard-coded literal (the bar's dead-path guard) — take the log
  path as an argument.

## The bar, the budget, and how to commit
Bar: exit 2 ONLY with `§4.4.2-RECORDED-DECISION-EXIT`. ~200 iterations. **Commit by iteration 80.**
**`git commit -F <file>`. Never commit TASK.md.**
