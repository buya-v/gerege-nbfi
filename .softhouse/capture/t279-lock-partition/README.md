# T279 — the STEP 0 lock rules do not partition; repair them so they do

Executable artefacts for T279 (T265 findings F-1 / F-2 / F-3 / F-7).

- `rules.py` — the OLD (as-shipped) and NEW (repaired) STEP 0 rule arms as *predicates*, one
  function per arm, plus the state-space generator. Nothing here reads prose; each arm is the
  literal condition from `SKILL.md` STEP 0 transcribed into a boolean function, so the table is
  DERIVED BY RUNNING THE PREDICATES, not by reading them.
- `enumerate.py` — runs every arm against every state and emits the coverage / uniqueness /
  conflict tables for OLD and NEW.
- `drive-wrapper-vs-skill.zsh` — drives the shipped `lock_decide()` out of
  `.softhouse/bin/fire-program.sh` over the SAME state space and diffs it against `rules.py`.
  This is the F-3 proof that the wrapper and STEP 0 decide identically.
- `measure-f2.py` — the fire-history measurement behind the rule-2 answer.
- `drive-two-fires.zsh` — scratch clones; local fire and cloud fire simulated against a real LOCK,
  including the case where mtime and push-recency disagree.
- `post-checkout` — the F-7 push-before-spawn hook, driven RED then GREEN.
- `out/` — recorded output of all of the above.
