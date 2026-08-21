#!/bin/sh
echo "user: $(id -un) uid=$(id -u) groups=$(id -Gn)"
echo
for d in /usr/bin /bin /sbin /usr/sbin /usr/local/bin /opt/homebrew/bin; do
  [ -d "$d" ] || { printf '  %-22s ABSENT\n' "$d"; continue; }
  w=read-only; [ -w "$d" ] && w=WRITABLE-BY-THIS-USER
  printf '  %-22s %-24s %s\n' "$d" "$w" "$(ls -ld "$d" | awk '{print $1, $3, $4}')"
done
echo
echo "the four instrument binaries actually selected:"
for p in /usr/bin/shasum /sbin/sha256sum /usr/bin/openssl /usr/bin/python3 /usr/bin/awk /usr/bin/env /usr/bin/mktemp /bin/rm; do
  [ -e "$p" ] || { printf '  %-22s ABSENT\n' "$p"; continue; }
  w=read-only; [ -w "$p" ] && w=WRITABLE
  printf '  %-22s %-10s %s\n' "$p" "$w" "$(ls -l "$p" | awk '{print $1, $3, $4}')"
done
echo
echo "can this user create a file in /sbin?  (test, then remove)"
if touch /sbin/.t135-probe 2>/dev/null; then echo "  YES — /sbin IS writable"; rm -f /sbin/.t135-probe; else echo "  no"; fi
if touch /usr/local/bin/.t135-probe 2>/dev/null; then echo "  /usr/local/bin: YES — writable (so its exclusion from the table is CORRECT)"; rm -f /usr/local/bin/.t135-probe; else echo "  /usr/local/bin: no"; fi
if touch /opt/homebrew/bin/.t135-probe 2>/dev/null; then echo "  /opt/homebrew/bin: YES — writable (exclusion CORRECT)"; rm -f /opt/homebrew/bin/.t135-probe; else echo "  /opt/homebrew/bin: no / absent"; fi
