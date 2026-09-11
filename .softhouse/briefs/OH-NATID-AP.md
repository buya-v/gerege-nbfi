# OH-NATID-AP — the national ID has no implementation. Write the structural validator. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-natid` (branch `feat/OHNATIDap`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/parties.md` — the parties port's files and functions.
2. `.softhouse/findings/F-2026-09-11-parties-graded-coverage.md` §4.2 — no symbol anywhere in `nexus/`
   implements the rule (the driver re-checked the whole tree).
3. `CLAUDE.md`, the non-negotiable, verbatim: **"National ID is 10 characters — 2 Cyrillic letters + 8
   digits; month +20 for births from 2000 onward; check digit unpublished — validate structurally."**
   And: **"Names are three fields … Match on registration number."**

## Why there is no oracle vector — say so, do not fake one
Fineract has no Mongolian national-ID rule. This is a **Gerege rule, not a port**, so it cannot be graded
against the reference oracle and **no parity vector may be written for it**. It is proven by unit tests
derived from the stated structure — nothing else. Record in `.softhouse/capabilities-parties.json` a
capability for it with `in_graded_domain: false` and the reason (no oracle behaviour exists).

## The design — decided by the driver (chosen_by: agent; Buyan may reverse). Implement exactly this.
`func ValidateNationalID(s string) error` in `nexus/internal/apps/parties/` (new file `nationalid.go`),
plus `type NationalIDError` naming WHICH rule failed. Pure, no I/O, no time.Now().
1. **Length:** exactly 10 characters (runes, not bytes — Cyrillic is 2 bytes in UTF-8). *Rejected
   alternative: byte length — it would accept 5 Cyrillic letters.*
2. **Letters:** runes 1–2 are UPPERCASE letters of the Mongolian Cyrillic alphabet: `А–Я`, `Ё`, `Ө`, `Ү`.
   No normalisation — lowercase, Latin look-alikes (`A`, `P`, `O`…) and whitespace are refused. *Rejected
   alternative: case-folding — silently accepting a mistyped ID hides a data-quality defect at the only
   place it can be caught.*
3. **Digits:** runes 3–10 are ASCII `0–9`.
4. **Embedded birth date** — digits 1–2 `YY`, 3–4 `MM`, 5–6 `DD`:
   * `MM` 01–12 → year 19YY; `MM` 21–32 → year 20YY and month MM−20 (**the "+20" rule**); anything else
     is refused.
   * `DD` must be a real day of that month in that year (leap years by the Gregorian rule).
5. **Digits 7–8 (the last two) are NOT validated.** The check-digit algorithm is unpublished; inventing
   one would refuse real citizens. *Rejected alternative: a guessed checksum.* Say so in the doc comment.
6. **Do not decide sex, age, or anything else from the digits** — the rule does not state it.

Tests (`nationalid_test.go`), table-driven: valid 19xx and 20xx IDs (month 01–12 and 21–32), the
29-Feb leap/non-leap pair (e.g. 2000 vs 1900 — 1900 is NOT a leap year), each failure class with the
error naming the rule: 9/11 runes, lowercase, Latin look-alike, digit in letter position, letter in
digit position, month 00/13/20/33, day 00/31-in-April. **Every test ID is synthetic — never a real
person's number** (there is no source of real ones in this repo, and there must not be).

Wire nothing. Do not touch client creation or any read path — this run adds the rule and proves it;
where it is enforced is a later decision.

## Non-negotiables (a violation is a rejection)
- **Do not touch `.softhouse/guards/`** (12 pairs) or `.softhouse/conformance.sh` (census **17**).
- No float, anywhere. PostgreSQL only. "The oracle" is the Fineract reference; **Oracle Database is
  prohibited.** **One bounded context: `parties`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with the line
`§4.4.2-RECORDED-DECISION-EXIT`; **"a HARD guard failed" is a failure.** ~250 iterations.
**Commit by iteration 80.** **Write commit messages to a file and use `git commit -F <file>`. Never commit TASK.md.**
