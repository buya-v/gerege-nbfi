import sys
p = '.softhouse/capture/out/capture-prod3b-raw.json'
s = open(p).read()
# A money-shaped numeric token that does NOT survive a binary-double round trip:
# 12345678901234567890.12 -> repr(float(...)) == '1.2345678901234567e+19'
# (T173's own worked example: a residue of -890.12 on the way TO the reference oracle.)
old = '"mathContextPrecision": 12,'
new = '"principalOnWire": 12345678901234567890.12, "mathContextPrecision": 12,'
if old not in s:
    sys.exit('planting failed: anchor not found')
open(p, 'w').write(s.replace(old, new, 1))
print('planted')
