#!/bin/sh
# T537 item 4 -- RE-RUN T528's TEN FAIL-CLOSED ARMS against T536's tree, plus two more.
#
# Every cell reads `ready-tasks.py`'s OWN exit code, because that is what an orchestrator
# at STEP 0/1 actually runs -- except FC2/FC3/FC4, which additionally read the checker's
# code directly so the distinct 2 / 3 verdicts are visible and not flattened to 5.
#
# ready-tasks.py exit codes seen here:  0 = gate CLEAN   5 = gate NOT CLEAN (any reason)
#
#   FC0  control: uninjured clean fixture              -> 0
#   FC1  origin unreachable                            -> 5   (checker 3)
#   FC2  git hangs past the checker's --timeout        -> 5   (checker 3)
#   FC3  ls-remote exits 0 with garbage on stdout      -> 5   (checker 3, LISTED NO BRANCHES)
#   FC4  ls-remote exits 0 with a partial ref set      -> 5   (checker 2, REFUSE)
#   FC5  archive runs/*.tasks.json unparseable         -> 5
#   FC6  archive with no `tasks` list                  -> 5
#   FC7  malformed baseline.json                       -> 5
#   FC8  checker raises mid-run                        -> 5
#   FC9  checker deleted                               -> 5
#   FC10 checker replaced by a SILENT exit-0 stub      -> 5   (T536's new arm; T528 F-5)
#   FC11 checker replaced by a stub that PRINTS THE VERDICT LINE and exits 0
#        -- T537. This is the arm that asks whether the F-5 repair is evidence or
#        incantation.
#   FC12 current tasks.json unparseable                -> 5   (T528 F-7; T527 gave 1)
#
# Usage: sh t537-failclosed.sh <worktree-at-18c64389> <scratch-dir>
set -u
WT=$1
TMP=$2
RT="$WT/.softhouse/bin/ready-tasks.py"
CB="$WT/.softhouse/bin/check-branch-published.py"
rm -rf "$TMP"; mkdir -p "$TMP"
FAILED=0

cell() { # name want got needle outfile
  if [ "$3" = "$2" ] && grep -q "$4" "$5"; then
    printf '  %-46s PASS  (exit %s, saw "%s")\n' "$1" "$3" "$4"
  else
    printf '  %-46s FAIL  (exit %s, wanted %s, needle "%s")\n' "$1" "$3" "$2" "$4"
    sed 's/^/      /' "$5" | head -25
    FAILED=$((FAILED + 1))
  fi
}

mkfixture() { # $1 root  $2 ok|broken
  d=$1; w=$d/work
  mkdir -p "$w/.softhouse/bin" "$w/.softhouse/runs"
  git -C "$w" init --quiet -b main
  cp "$CB" "$RT" "$w/.softhouse/bin/"
  printf '{"gates_pending":[]}' > "$w/.softhouse/program.json"
  if [ "$2" = "broken" ]; then
    git -C "$w" remote add origin "$d/no-such-origin.git"
    printf '{"run_id":"x","tasks":[{"id":"TN","status":"done","branch":"softhouse/TN-never-pushed"}]}' \
      > "$w/.softhouse/tasks.json"
    return
  fi
  git init --quiet --bare -b main "$d/origin.git"
  git -C "$w" remote add origin "$d/origin.git"
  : > "$w/README"
  git -C "$w" add -A
  git -C "$w" -c user.email=t537@example.invalid -c user.name=t537 commit --quiet -m root
  git -C "$w" push --quiet -u origin main 2>/dev/null
  git -C "$w" checkout --quiet -b softhouse/TP-pushed
  echo p > "$w/p.txt"
  git -C "$w" add -A
  git -C "$w" -c user.email=t537@example.invalid -c user.name=t537 commit --quiet -m "TP work"
  git -C "$w" push --quiet origin softhouse/TP-pushed 2>/dev/null
  git -C "$w" checkout --quiet main
  printf '{"run_id":"x","tasks":[{"id":"TP","status":"done","branch":"softhouse/TP-pushed"}]}' \
    > "$w/.softhouse/tasks.json"
}

dirty() { # make the record CLAIM a branch that was never pushed
  printf '{"run_id":"x","tasks":[{"id":"TN","status":"done","branch":"softhouse/TN-never-pushed"}]}' \
    > "$1/.softhouse/tasks.json"
}

echo "T537 fail-closed matrix -- T536 tree at $WT"
echo

# FC0 -------------------------------------------------------------------------------
mkfixture "$TMP/fc0" ok
python3 "$TMP/fc0/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc0/work" > "$TMP/fc0.txt" 2>&1
cell "FC0-control-clean-fixture" 0 $? "check-branch-published: CLEAN" "$TMP/fc0.txt"

# FC1 -------------------------------------------------------------------------------
mkfixture "$TMP/fc1" broken
python3 "$TMP/fc1/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc1/work" > "$TMP/fc1.txt" 2>&1
cell "FC1-origin-unreachable" 5 $? "CANNOT ESTABLISH ORIGIN" "$TMP/fc1.txt"

# FC2 -- a git that hangs -----------------------------------------------------------
mkfixture "$TMP/fc2" ok
mkdir -p "$TMP/fc2/shim"
printf '#!/bin/sh\nsleep 30\n' > "$TMP/fc2/shim/git"
chmod +x "$TMP/fc2/shim/git"
PATH="$TMP/fc2/shim:$PATH" python3 "$CB" --repo "$TMP/fc2/work" --timeout 3 \
    > "$TMP/fc2.txt" 2>&1
cell "FC2-git-hangs-(checker-direct)" 3 $? "CANNOT ESTABLISH ORIGIN" "$TMP/fc2.txt"

# FC3 -- ls-remote exits 0 with garbage ---------------------------------------------
mkfixture "$TMP/fc3" ok
mkdir -p "$TMP/fc3/shim"
cat > "$TMP/fc3/shim/git" <<'SH'
#!/bin/sh
for a in "$@"; do
  if [ "$a" = "ls-remote" ]; then echo "not a ref line at all"; exit 0; fi
done
exec /usr/bin/git "$@"
SH
chmod +x "$TMP/fc3/shim/git"
PATH="$TMP/fc3/shim:$PATH" python3 "$CB" --repo "$TMP/fc3/work" > "$TMP/fc3.txt" 2>&1
cell "FC3-ls-remote-garbage-(checker-direct)" 3 $? "ORIGIN LISTED NO BRANCHES" "$TMP/fc3.txt"

# FC4 -- ls-remote returns a PARTIAL ref set (main only) -----------------------------
mkfixture "$TMP/fc4" ok
mkdir -p "$TMP/fc4/shim"
cat > "$TMP/fc4/shim/git" <<'SH'
#!/bin/sh
for a in "$@"; do
  if [ "$a" = "ls-remote" ]; then /usr/bin/git "$@" | grep 'refs/heads/main$'; exit 0; fi
done
exec /usr/bin/git "$@"
SH
chmod +x "$TMP/fc4/shim/git"
PATH="$TMP/fc4/shim:$PATH" python3 "$CB" --repo "$TMP/fc4/work" > "$TMP/fc4.txt" 2>&1
cell "FC4-ls-remote-partial-(checker-direct)" 2 $? "UNBACKED-BRANCH" "$TMP/fc4.txt"

# FC5 -- unparseable ARCHIVE ---------------------------------------------------------
mkfixture "$TMP/fc5" ok
echo '{ this is not json' > "$TMP/fc5/work/.softhouse/runs/20260101.tasks.json"
python3 "$TMP/fc5/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc5/work" > "$TMP/fc5.txt" 2>&1
cell "FC5-archive-unparseable" 5 $? "UNREADABLE TASK RECORD" "$TMP/fc5.txt"

# FC6 -- archive with no tasks list ---------------------------------------------------
mkfixture "$TMP/fc6" ok
echo '{"run_id":"x"}' > "$TMP/fc6/work/.softhouse/runs/20260101.tasks.json"
python3 "$TMP/fc6/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc6/work" > "$TMP/fc6.txt" 2>&1
cell "FC6-archive-has-no-tasks-list" 5 $? "TASK RECORD HAS NO tasks LIST" "$TMP/fc6.txt"

# FC7 -- malformed baseline.json ------------------------------------------------------
mkfixture "$TMP/fc7" ok
mkdir -p "$TMP/fc7/work/.softhouse/capture/t527-branch-published"
echo 'not json at all' > "$TMP/fc7/work/.softhouse/capture/t527-branch-published/baseline.json"
python3 "$TMP/fc7/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc7/work" > "$TMP/fc7.txt" 2>&1
cell "FC7-malformed-baseline" 5 $? "NOT a pass" "$TMP/fc7.txt"

# FC8 -- checker raises MID-RUN --------------------------------------------------------
mkfixture "$TMP/fc8" ok
python3 - "$TMP/fc8/work/.softhouse/bin/check-branch-published.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("def check(repo, baseline_path, timeout=90):\n",
              "def check(repo, baseline_path, timeout=90):\n"
              "    raise RuntimeError('T537 injected mid-run failure')\n", 1)
open(p, "w").write(s)
PY
python3 "$TMP/fc8/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc8/work" > "$TMP/fc8.txt" 2>&1
cell "FC8-checker-raises-mid-run" 5 $? "NOT a pass" "$TMP/fc8.txt"

# FC9 -- checker deleted ---------------------------------------------------------------
mkfixture "$TMP/fc9" ok
rm -f "$TMP/fc9/work/.softhouse/bin/check-branch-published.py"
python3 "$TMP/fc9/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc9/work" > "$TMP/fc9.txt" 2>&1
cell "FC9-checker-deleted" 5 $? "checker is not on disk" "$TMP/fc9.txt"

# FC10 -- SILENT exit-0 stub over a DIRTY record -----------------------------------------
mkfixture "$TMP/fc10" ok
dirty "$TMP/fc10/work"
printf 'import sys\nsys.exit(0)\n' > "$TMP/fc10/work/.softhouse/bin/check-branch-published.py"
python3 "$TMP/fc10/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc10/work" > "$TMP/fc10.txt" 2>&1
cell "FC10-silent-stub-over-a-dirty-record" 5 $? "never printed its verdict line" "$TMP/fc10.txt"

# FC11 -- T537. A stub that PRINTS THE VERDICT LINE, over the same DIRTY record ----------
mkfixture "$TMP/fc11" ok
dirty "$TMP/fc11/work"
cat > "$TMP/fc11/work/.softhouse/bin/check-branch-published.py" <<'PY'
import sys
print("check-branch-published: CLEAN")
sys.exit(0)
PY
python3 "$TMP/fc11/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc11/work" > "$TMP/fc11.txt" 2>&1
RC=$?
if [ "$RC" = 5 ]; then
  printf '  %-46s PASS  (exit 5 -- the banner did NOT buy a pass)\n' "FC11-BANNER-stub-over-a-dirty-record"
else
  printf '  %-46s ***BREAK*** (exit %s -- a 3-line stub printing the\n' "FC11-BANNER-stub-over-a-dirty-record" "$RC"
  printf '  %-46s documented banner bought a PASS over a record whose\n' ""
  printf '  %-46s branch was never pushed)\n' ""
  FAILED=$((FAILED + 1))
fi
sed 's/^/      /' "$TMP/fc11.txt" | head -8

# FC12 -- current tasks.json unparseable (T528 F-7) --------------------------------------
mkfixture "$TMP/fc12" ok
echo '{ nope' > "$TMP/fc12/work/.softhouse/tasks.json"
python3 "$TMP/fc12/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/fc12/work" > "$TMP/fc12.txt" 2>&1
cell "FC12-current-tasks.json-unparseable" 5 $? "UNREADABLE TASK RECORD" "$TMP/fc12.txt"

echo
echo "cells not behaving as required: $FAILED"
echo "fixtures: $TMP"
