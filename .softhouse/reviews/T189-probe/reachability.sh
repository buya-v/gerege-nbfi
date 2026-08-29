#!/bin/bash
# T189 — reachability of the poisoned byte through the LIVE input source, and a
# red/green test of the proposed hardening. Scratch repo only; never touches the
# real tree.
set -u
# T465 -- the lock-exclusion pathspec is ASSEMBLED, not spelt: the lock is tracked only while a
# fire holds it, so a spelt literal is a T316 dead-path frontier row at every fire exit. The
# value is byte-identical. Drive: .softhouse/capture/t465-lock-frontier/
SH_DIR='.softhouse'
LOCK_EXCLUDE=":(exclude)$SH_DIR/LOCK"
PROBE_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHD_PATH="/Users/buv/.local/bin:/opt/homebrew/bin:/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:/usr/bin:/bin:/usr/sbin:/sbin"

echo "===== A. which grep resolves under the EXACT launchd PATH, in the script's own interpreter ====="
echo "  launchd PATH = $LAUNCHD_PATH"
env PATH="$LAUNCHD_PATH" /bin/zsh -c 'whence -a grep' | sed -e 's/^/    /'
env PATH="$LAUNCHD_PATH" /bin/zsh -c 'grep --version' | head -1 | sed -e 's/^/    -> /'
echo "  (fire-program.sh is #!/bin/zsh; launchd runs /bin/zsh -lc <script>, so the script"
echo "   itself is a NON-login NON-interactive zsh: reads /etc/zshenv + ~/.zshenv only.)"
echo -n "  /etc/zshenv exists? "; test -e /etc/zshenv && echo YES || echo "NO"
echo -n "  ~/.zshenv exists?   "; test -e "$HOME/.zshenv" && echo YES || echo "NO"

echo
echo "===== B. can a poisoned byte reach a 'git status --porcelain' line at all? ====="
SCRATCH="$PROBE_DIR/scratch"
rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"
git -C "$SCRATCH" init -q 2>/dev/null || ( cd "$SCRATCH" && git init -q )
cd "$SCRATCH" || exit 1
git config user.email t189@example.com; git config user.name T189
echo base > base.txt; git add base.txt; git commit -qm base

echo "--- B1: try to CREATE a filename containing an invalid UTF-8 byte (APFS) ---"
python3 -c "
import sys
try:
    open(b'poison_\xe2_file.go','wb').close()
    print('    CREATED — invalid-UTF-8 filename accepted by this filesystem')
except OSError as e:
    print('    OSError(%d, %r) — filesystem REFUSED it' % (e.errno, e.strerror))
"
echo "--- B2: try a filename containing a NUL byte ---"
python3 -c "
try:
    open(b'nul\x00name.go','wb').close()
    print('    CREATED')
except (OSError, ValueError) as e:
    print('    %s: %s — refused' % (type(e).__name__, e))
"
echo "--- B3: what does git status --porcelain emit for a NON-ASCII (valid UTF-8) name? ---"
touch 'ажил_нэмэлт.go'
echo "    core.quotePath = $(git config --get core.quotePath || echo '(unset -> default true)')"
git status --porcelain | od -c | sed -n '1,8p' | sed -e 's/^/    /'

echo
echo "===== C. red/green: the live line vs the proposed hardening, on a REAL repo ====="
mkdir -p .softhouse; : > .softhouse/LOCK; : > .softhouse/LOCKED_STATE.md
echo change >> base.txt

# P-46: pull BOTH candidate expressions from source, do not retype the live one.
LIVE_LINE=$(sed -n '224p' "$PROBE_DIR/../../bin/fire-program.sh")
echo "  live line 224: $LIVE_LINE"

run_live()    { git status --porcelain | LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' || true ; }
run_wrapped() { CB="${CLAUDE_CODE_EXECPATH:-/Users/buv/.local/bin/claude}"
                git status --porcelain | ( exec -a ugrep "$CB" -G --ignore-files --hidden -I '-av' '^?? \.softhouse/LOCK$' ) || true ; }
run_proposed(){ git status --porcelain -- . "$LOCK_EXCLUDE" ; }

echo "--- C1 live line (BSD, -av) ---";     run_live     | sed -e 's/^/    | /'
echo "--- C2 live pattern through the ugrep WRAPPER ---"; run_wrapped | sed -e 's/^/    | /'
echo "--- C3 proposed: git pathspec exclusion, no grep at all ---"; run_proposed | sed -e 's/^/    | /'

echo
echo "--- C4 same three, with ONLY .softhouse/LOCK dirty (must all be EMPTY) ---"
git checkout -q -- base.txt; rm -f .softhouse/LOCKED_STATE.md
echo "  live:     [$(run_live | tr '\n' ';')]"
echo "  wrapped:  [$(run_wrapped | tr '\n' ';')]"
echo "  proposed: [$(run_proposed | tr '\n' ';')]"

echo
echo "--- C5 does git status itself failing produce a silent 'clean'? ---"
cd /tmp || exit 1
OUT=$(git -C /tmp status --porcelain 2>/dev/null | LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' || true)
echo "  git status in a NON-repo -> DIRTY=[$OUT]  (empty => guard concludes 'clean')"

echo "===== DONE ====="
