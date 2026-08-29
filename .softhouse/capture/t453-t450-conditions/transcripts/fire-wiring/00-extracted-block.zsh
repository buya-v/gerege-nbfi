bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh" 2>&1 | while IFS= read -r l; do log "pushgate| $l"; done || true
if bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh" --status >/dev/null 2>&1; then
  log "pushgate| STATUS OK — the driver push gate is installed on this host."
else
  log "pushgate| ############################################################"
  log "pushgate| # THE DRIVER PUSH GATE IS NOT INSTALLED (or is incomplete)."
  log "pushgate| # Every push this fire makes to refs/heads/main is UNGATED."
  log "pushgate| # --status output follows."
  log "pushgate| ############################################################"
  bash "$REPO/.softhouse/hooks/install-driver-push-gate.sh" --status 2>&1 | while IFS= read -r l; do log "pushgate| $l"; done || true
fi

# T453 — m-3 / FU-T412-4. THE POST-HOC RECONCILIATION.
#
# `pre-push` is CLIENT-SIDE and `--no-verify` turns it off; T450 drove a GITLINK onto main that
# way with zero gate output. The answer to a bypassable pre-push check is a SECOND READING taken
# afterwards from evidence the bypasser did not choose — what actually landed on the ref — so
# this reconciles every tip in `origin/main`'s reflog against the attestation ledger, scans each
# for gitlinks, and READS `bypass.log`, which until now had no reader at all.
#
# It runs at fire START, so what it reports is the PREVIOUS fire's pushes: a bypass is caught one
# fire late rather than never. Non-fatal, same reason as everything else in this block.
RECON_TMP="$(mktemp "${TMPDIR:-/tmp}/fire-reconcile.XXXXXXXXXX")" || RECON_TMP=''
if [[ -n "$RECON_TMP" ]]; then
  bash "$REPO/.softhouse/hooks/reconcile-pushed-trees.sh" >"$RECON_TMP" 2>&1 || true
  while IFS= read -r l; do log "reconcile| $l"; done <"$RECON_TMP"
  rm -f "$RECON_TMP"
else
  log "reconcile| could not create a scratch file; the post-hoc reconciliation did not run this fire."
fi
