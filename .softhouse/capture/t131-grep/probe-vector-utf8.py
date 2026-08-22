#!/usr/bin/env python3
"""T131 - characterise the non-ASCII bytes in the committed vector store.
Three questions the latent-vs-live ruling turns on:
  1. are they VALID UTF-8 (BSD grep decodes them) or INVALID (it goes blind)?
  2. do they sit INSIDE a JSON string literal (perl -0pe strips it first)?
  3. is there a float-shaped number to their RIGHT on the SAME line?
"""
import pathlib, re, sys, json

root = pathlib.Path(__file__).resolve().parents[3]
store = root / ".softhouse" / "vectors"
FLOAT = re.compile(rb'[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]')
STRIP = re.compile(rb'"(\\.|[^"\\])*"')

any_invalid = False
for f in sorted(store.rglob("*.json")):
    b = f.read_bytes()
    if all(0x20 <= c <= 0x7e or c in (9,10,13) for c in b):
        continue
    try:
        b.decode('utf-8'); valid = "VALID UTF-8"
    except UnicodeDecodeError as e:
        valid = "INVALID UTF-8 %s" % e; any_invalid = True
    print("==", f.relative_to(store), "->", valid)
    for ln, line in enumerate(b.split(b'\n'), 1):
        nz = [i for i,c in enumerate(line) if not (0x20 <= c <= 0x7e or c in (9,13))]
        if not nz:
            continue
        stripped = STRIP.sub(b'', line)
        st_nz = [i for i,c in enumerate(stripped) if not (0x20 <= c <= 0x7e or c in (9,13))]
        first = nz[0]
        m = FLOAT.search(line, first)
        print("   line %d: bytes %s at cols %s | codepoints=%r | survives perl string-strip: %s | float to the RIGHT on this line: %s"
              % (ln, [hex(line[i]) for i in nz[:4]], nz[:4],
                 line[nz[0]:nz[-1]+1].decode('utf-8','replace'),
                 bool(st_nz), bool(m)))
print()
print("ANY INVALID UTF-8 BYTE ANYWHERE IN THE COMMITTED VECTOR STORE:", any_invalid)
