# T336 — can anything enforce push-before-spawn? Executable evidence.

Run order, and what each artefact settles.

## probe/

| script | question | output |
|---|---|---|
| `drive-fc-reproduce.zsh <hook>` | does a non-zero `post-checkout` exit abort `git worktree add`? is the "refused" worktree usable? what does the hook observe at hook time? | `out/fc-reproduce.txt` |
| `reflog-signature.zsh` | does the harness's worktree admin dir match what `git worktree add -b <br> <path> origin/main` leaves behind? | `out/reflog-signature.txt` |
| `drive-refuse-candidates.zsh` | is there ANY hook on this git that can veto a `git worktree add`? (`reference-transaction` prepared/all-states/real-shape, permitting controls, blast radius, `pre-receive`) | `out/refuse-candidates.txt` |
| `drive-audit-red-green.zsh <audit.py>` | does the shipped detector go RED on the shape of the misses on record, and GREEN on a compliant batch? | `out/audit-red-green.txt` |
| `post-checkout-PROBE` | **the real-route probe hook.** Always `exit 0`. Writes to three targets so a sandboxed write cannot be mistaken for "did not run". | `out/real-route-POSTCHECKOUT-FIRED.log` |
| `reference-transaction-PROBE-WRAPPER` | the same, wrapped around T312's ref guard, delegating to it unchanged | `out/real-route-REFTXN-FIRED.log` |

The two probe hooks were installed in the live `/Users/buv/gerege-nbfi/.git/hooks/` for six
minutes on 2026-08-28, five real workers were spawned through the `Agent` tool with
`isolation: worktree`, and both hooks were then removed / restored. T312's
`reference-transaction` was restored from a backup and `cmp`-verified byte-identical.

## The two log files are the point

`real-route-POSTCHECKOUT-FIRED.log` and `real-route-REFTXN-FIRED.log` contain **no entry for
any of the five harness spawns**, and **do** contain entries for ordinary worker git commands
in the same minute from the same hooks directory. That pair — the absence *and* its control —
is the whole finding. Read `.softhouse/hooks/README.md` for what it kills.

## out/audit-live-repo-ATTEMPT1.txt is kept deliberately

It is the first version of the detector, which compared every spawn against the LATEST
publication of each file and therefore reported **177 violations over 60 spawns spanning ten
days** — it flagged every fire that had ever run. Kept because a detector that fires on
everything is exactly as useless as one that never fires, and the rewrite that followed
(a content test against `origin/main` reconstructed as of each spawn's own instant) is only
justified by seeing it.

Likewise `out/audit-red-green.txt` attempt 1, recorded in the audit's own source comments:
the RED case came out CLEAN at margin `+0s` because the first implementation read `%ct` (the
committer date) instead of `%gd` (the reflog entry time) — which would have silently forgiven
both of the misses on record, since in both the commit existed before the spawn and only the
push came after.
