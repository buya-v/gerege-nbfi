p='/tmp/t446/drive-t446-v5.sh'
s=open(p).read()
old = '''  {
    printf '#!/usr/bin/env bash\\n'
    printf '# a scratch checker planted by the T446 drive\\n'
    [ -n "$w" ] && printf '# %s\\n' "$(hdr "$w")"
    printf 'exit 0\\n'
  } > "$f"'''
new = '''  {
    printf '#!/usr/bin/env bash\\n'
    # A REAL CHECKER NAMES ITSELF IN ITS OWN HEADER -- every member of the canonical
    # guards directory on this tree does. v4 of this instrument left that line out, and
    # arm CASE then refused for the WRONG REASON: the symlink DID win the collision and
    # the grep DID dereference to the member, but the member's text did not contain its
    # own basename, so the naming test missed. Recorded, not hidden.
    printf '# %s -- a scratch checker planted by the T446 drive\\n' "$(basename "$p")"
    [ -n "$w" ] && printf '# %s\\n' "$(hdr "$w")"
    printf 'exit 0\\n'
  } > "$f"'''
assert old in s
s = s.replace(old, new)
open(p,'w').write(s)
print("ok")
