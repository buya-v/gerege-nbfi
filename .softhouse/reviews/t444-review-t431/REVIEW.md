# T444 — INDEPENDENT REVIEW of T431 (`softhouse/T431-t407-conditions`)

**Status: PROVISIONAL — work in progress. Do not merge on this file's current verdict.**

**Provisional verdict: APPROVED WITH CONDITIONS.**

Subject: T431's change to `.softhouse/conformance.sh` inside `guard_guards_dir_registration`,
closing `C-T407-1` and T407's other three conditions. This is a change to the GRADING HARNESS
and is reviewed as such.

Honesty rule: every material claim is marked `[VERIFIED: <source>]` or `[UNVERIFIED]`.

## Findings so far (provisional, being driven)

* T431's headline (`git ls-files` C-quotes, so `self_norm` is not a path) — **re-derived
  independently and it holds** [VERIFIED: `evidence/01-git-quoting.txt`, git 2.50.1].
* The seven rotted cardinals — **all seven re-measured on today's `main` and all seven are
  rotted; `:4090` is a bare double-quote mid-string** [VERIFIED].
* Line-count neutrality and `patterns.md:3426` → `conformance.sh:3271` — **still resolves on
  T431's tree** [VERIFIED].

Everything else is in progress.
