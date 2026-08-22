#!/bin/zsh
# T211 -- stand-in for `claude -p`.  Models the ONE property that makes the
# defect bite: the fire's foreground child runs for HOURS.  It emits a couple
# of stream-json events (so the real `| tee | jq` digest pipeline is exercised
# with real input) and then sleeps far longer than any probe window.
#
# It records its own pid so the harness can prove whether it was ORPHANED --
# a wrapper that exits promptly but leaves `claude` running is not a fix, it
# is a worse strand: an unlocked driver still writing to the repo.
print -r -- "$$" > "${T211_CHILDPID:-/tmp/t211-scratch/childpid}"
print -r -- '{"type":"system","subtype":"init","session_id":"t211-fake"}'
print -r -- '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"echo t211"}}]}}'
# unbuffered enough for jq --unbuffered to have printed before the signal lands
# control mode: exit promptly with a chosen status, so the happy path and the
# rc-propagation path can be measured without any signal at all
if [[ -n "${T211_FAKE_RC:-}" ]]; then
  /bin/sleep 0.3
  exit $T211_FAKE_RC
fi
exec /bin/sleep "${T211_CHILD_SECS:-300}"
