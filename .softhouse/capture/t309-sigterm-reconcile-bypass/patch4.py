import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

lines = s.split("\n")
# locate the block: from the "T288: repair the state" banner comment through the
# closing brace of reconcile_tasks_json (exclusive of the CALL line).
start = None
for i, l in enumerate(lines):
    if l.startswith("# ---------------------------------------------- T288: repair the state"):
        start = i
        break
assert start is not None
assert lines[start - 1] == ""
call_i = None
for i in range(start, len(lines)):
    if lines[i].startswith('reconcile_tasks_json "${RESCUE_PAIRS[@]}"'):
        call_i = i
        break
assert call_i is not None
assert lines[call_i - 1] == "}", repr(lines[call_i - 1])

block = lines[start:call_i]            # banner comment + RECON_VERDICT + def ... }
assert block[-1] == "}"
assert any(l.startswith("reconcile_tasks_json() {") for l in block)

note = [
    "# T309 — THIS DEFINITION MOVED OUT OF `run_exit_guard`, AND THAT WAS NOT COSMETIC.",
    "# T288 defined `reconcile_tasks_json` INSIDE run_exit_guard, twenty lines above its only",
    "# call. A zsh function body is not created until the enclosing function RUNS, so before",
    "# the first driver had exited the name did not exist at all — and `on_signal` fires from",
    "# the moment the traps are installed, which is BEFORE that. So the brief's finding is",
    "# stronger than 'on_signal never calls the reconciler': on the first chain iteration it",
    "# could not have called it, because there was nothing to call. It lives at top level now,",
    "# beside `foreign_live_session_in_repo` which it depends on, so both call sites reach the",
    "# same bytes and neither is ordering-dependent.",
    "#",
]
newblock = note + block

# remove from old position (including the trailing blank line separation handling)
del lines[start:call_i]
# re-find the anchor: end of foreign_live_session_in_repo, i.e. the line before
# "# ------------------------------------------------------- exit-protocol guard ---"
anchor = None
for i, l in enumerate(lines):
    if l.startswith("# ------------------------------------------------------- exit-protocol guard"):
        anchor = i
        break
assert anchor is not None
lines[anchor:anchor] = newblock + [""]

s = "\n".join(lines)
io.open(p, "w", encoding="utf-8").write(s)
print("patch4 ok")
