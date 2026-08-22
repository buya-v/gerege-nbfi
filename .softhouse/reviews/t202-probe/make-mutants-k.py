import io
post = io.open("/tmp/t202/postfix-acq.zsh", encoding="utf-8").read()
muts = {
    # KA: host check dropped -> would judge (and steal) ANOTHER machine's lock
    "KA": [('  [[ "$host" == "$(hostname -s)" ]] || return 1   # never judge another machine\n', "")],
    # KB: kill -0 sense inverted -> would call a LIVE holder dead
    "KB": [('  kill -0 "$pid" 2>/dev/null       && return 1   # still running => not stale',
            '  kill -0 "$pid" 2>/dev/null       || return 1   # INVERTED')],
}
for name, pairs in muts.items():
    body = post
    for old, new in pairs:
        n = body.count(old)
        if n != 1:
            raise SystemExit(f"mutant {name}: anchor matched {n}, expected 1")
        body = body.replace(old, new)
    p = f"/tmp/t202/acq-mut-{name}.zsh"
    io.open(p, "w", encoding="utf-8").write(body)
    print("wrote", p)
