import re, subprocess

src = subprocess.check_output(
    ["git", "show",
     "softhouse/T360-divergence-class:nexus/internal/apps/ledger/conformance/impl.go"],
    cwd="/tmp/t387/t360").decode()

# extract the three funcs + the RegisterWrong block from T360's impl.go
start = src.index("type residueRoundingPoster struct{}")
end = src.index("func init() {")
block = src[start:end]

reg_start = src.index('\tRegisterWrong("ledger-wrong-residue-rounding"')
reg_end = src.index("\t\tresidueRoundingPoster{})\n", reg_start) + len("\t\tresidueRoundingPoster{})\n")
reg = src[reg_start:reg_end]

p = "/tmp/t387/t359drive/nexus/internal/apps/ledger/conformance/impl.go"
s = open(p).read()
assert "residueRoundingPoster" not in s
s = s.replace("func init() {", block + "func init() {", 1)
s = s.replace('\tRegister("ledger-go", NewGoPoster())\n',
              '\tRegister("ledger-go", NewGoPoster())\n' + reg, 1)
if '\n\t"strings"\n' not in s:
    s = s.replace('\t"strconv"\n', '\t"strconv"\n\t"strings"\n', 1)
open(p, "w").write(s)
print("added")
