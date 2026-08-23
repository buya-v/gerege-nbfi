#!/bin/zsh
# T288 — the two measurements the design rests on, taken against whatever is running on
# this host RIGHT NOW. Re-runnable; the pids will differ, the shapes will not.
#
# Taken 2026-08-23 while local fire 20260823-080004 was running with six workers
# dispatched. The output of that run is beside this script in out/0-live-host-measurements.txt.
set -uo pipefail
print -r -- "T288 — live-host measurements, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
print -r -- ""
print -r -- "=== 1. A live fire is ONE claude process. There is NO process per worker —"
print -r -- "       a subagent is in-process, so any probe looking for a process per TASK"
print -r -- "       would find nothing and demote everything."
print -r -- "       NOTE: this listing selects on argv[0]'s BASENAME, which is exactly what"
print -r -- "       foreign_live_session_in_repo() matches. It therefore includes an"
print -r -- '       interactive claude invoked without a path, and EXCLUDES the'
print -r -- '       /usr/bin/caffeinate child that merely carries claude in its arguments.'
/bin/ps -Ao pid=,ppid=,command= | awk '{n=split($3,p,"/"); if (p[n]=="claude") print}' | cut -c1-140
print -r -- ""
print -r -- "=== 2. cwd of each live claude, which is what the probe actually reads."
print -r -- "       A session working in the repo and one that merely exists look identical"
print -r -- "       in ps and differ only here."
for P in ${(f)"$(/bin/ps -Ao pid=,command= | awk '{n=split($2,p,"/"); if (p[n]=="claude") print $1}')"}; do
  print -r -- "  pid $P -> $(/usr/sbin/lsof -w -a -d cwd -p $P -Fn 2>/dev/null | grep '^n' | sed 's/^n//')"
done
print -r -- ""
print -r -- "=== 3. The two zsh semantics that corrupted the first draft of the probe,"
print -r -- "       both re-derivable here rather than taken on trust."
print -r -- "  a) \`local x\` for an x that already exists at this scope PRINTS it:"
zsh -c 'f(){ local a; for a in x y; do local a; done; }; f' | sed 's/^/     /'
print -r -- "  b) unbraced \$p:c / \$c:e apply history modifiers, silently:"
zsh -c 'p=28980; c=/Users/buv; print -r -- "     unbraced: pid=$p:cwd=$c:elsewhere"; print -r -- "     braced:   pid=${p}:cwd=${c}:elsewhere"'
