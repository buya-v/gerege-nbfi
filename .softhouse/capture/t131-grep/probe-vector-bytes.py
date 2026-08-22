#!/usr/bin/env python3
"""T131 - is F-T108-1 LATENT or LIVE?

Scan every committed vector JSON byte-by-byte for anything outside
{0x09,0x0a,0x0d} u [0x20..0x7e].  Pure integer byte inspection: no locale, no
regex engine, no floating point (P-25).

Driven RED first against a deliberately poisoned scratch file - see --selftest.
"""
import os, sys, pathlib

OK = set([0x09, 0x0a, 0x0d]) | set(range(0x20, 0x7f))

def scan(p):
    b = pathlib.Path(p).read_bytes()
    return [(i, b[i]) for i in range(len(b)) if b[i] not in OK]

def main():
    root = pathlib.Path(__file__).resolve().parents[3]
    store = root / ".softhouse" / "vectors"
    if "--selftest" in sys.argv:
        d = pathlib.Path(__file__).resolve().parent / "corpus"
        d.mkdir(parents=True, exist_ok=True)
        f = d / "selftest-poisoned.json"
        f.write_bytes(b'{"a": 1\xe2 2.5}\n')
        hits = scan(f)
        print("SELFTEST poisoned file ->", "RED (detector fires)" if hits else "GREEN (DETECTOR IS BROKEN)", hits)
        g = d / "selftest-clean.json"
        g.write_bytes(b'{"a": 1, "b": "2"}\n')
        print("SELFTEST clean file    ->", "RED (BROKEN)" if scan(g) else "GREEN (correct)")
        return
    files = sorted(store.rglob("*.json"))
    dirty = 0
    for f in files:
        hits = scan(f)
        if hits:
            dirty += 1
            print("NON-ASCII", f, hits[:8])
    print("vector json files scanned:", len(files))
    print("files with any byte outside TAB/LF/CR/0x20-0x7e:", dirty)

main()
