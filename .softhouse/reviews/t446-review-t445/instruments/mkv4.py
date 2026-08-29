p='/tmp/t446/drive-t446-v4.sh'
s=open(p).read()

s=s.replace('''commit_all() { ( cd "$1" && git add -A && git -c user.email=t446@local -c user.name=t446 \\
                  commit -q -m "T446 drive fixture" ) ; }''',
'''# NOADD=1 means the plant staged the index itself and a `git add -A` here would
# CLOBBER it -- an index-only entry (a 120000 cacheinfo row) is re-read off the
# case-folded working tree and silently downgraded to the decoy's blob. That is
# exactly how this instrument's first CASE arm measured nothing; recorded, not hidden.
NOADD=0
commit_all() {
  if [ "$NOADD" -eq 0 ]; then ( cd "$1" && git add -A ) || return 1 ; fi
  ( cd "$1" && git -c user.email=t446@local -c user.name=t446 \\
      commit -q -m "T446 drive fixture" ) ; }''')

s=s.replace('  rm -rf "$WORK/$arm"; mkdir -p "$WORK/$arm"',
            '  NOADD=0\n  rm -rf "$WORK/$arm"; mkdir -p "$WORK/$arm"')

old_case = s[s.index('plant_CASE() {'):s.index("# T445's own MCASE")]
new_case = '''plant_CASE() {
  local t="$1"; local up lo blob
  up="W.txt"; lo="w.txt"
  mkmember "$t" "$MEMBER" "$G/$up"
  mkwitness "$t" "$up" ""          # decoy: names nothing
  ( cd "$t" && git add -A ) || return 1
  blob="$( cd "$t" && printf '%s' "$MEMBER" | git hash-object -w --stdin )" || return 1
  ( cd "$t" && git update-index --add --cacheinfo "120000,$blob,$G/$lo" ) || return 1
  NOADD=1
}

'''
s=s.replace(old_case,new_case)

old_m = s[s.index('plant_MCASE() {'):s.index('# the registration row exists ONLY')]
new_m = '''plant_MCASE() {
  local t="$1"; local UP LO tmpf blob
  UP="ZZ-T446M"; LO="zz-t446m"
  mkmember  "$t" "$UP/x.sh" ""            # smuggled: no REACHED-BY row at all
  mkwitness "$t" "$WIT" "x.sh"
  ( cd "$t" && git add -A ) || return 1
  tmpf="$WORK/mcase-honest"
  {
    printf '#!/usr/bin/env bash\\n'
    printf '# the HONEST sibling\\n'
    printf '# %s\\n' "$(hdr "$G/$WIT")"
    printf 'exit 0\\n'
  } > "$tmpf"
  blob="$( cd "$t" && git hash-object -w "$tmpf" )" || return 1
  ( cd "$t" && git update-index --add --cacheinfo "100755,$blob,$G/$LO/x.sh" ) || return 1
  NOADD=1
}

'''
s=s.replace(old_m,new_m)
open(p,'w').write(s)
print("ok")
