#!/usr/bin/env python3
"""
T46 / M-6 — MACHINE-ASSERT the Path B same-local-slot dataflow.

Audit finding M-6 (T44 section 3): E3's only machine assertion is
`grep -c 'MoneyHelper.getMathContext' != 0` (`src/read-pathb-wiring.sh`, the `N_GMC` check).
The claim that actually carries T42 attestation rule 4 — that the slot the ambient
`MathContext` is stored into is THE SAME slot that is loaded as the schedule generator's
`MathContext` argument — was left to the human reader ("Read the dataflow yourself in the
transcript").  This script asserts it mechanically off a `javap -p -c` transcript.

WHAT IS ASSERTED, per method that calls `MoneyHelper.getMathContext`:

  A1  the instruction immediately after `invokestatic MoneyHelper.getMathContext` is
      `astore <slot>` (or `astore_<slot>`);
  A2  that same `<slot>` is later `aload`ed and consumed by an `invoke*` whose descriptor
      contains `Ljava/math/MathContext;`;
  A3  no other `astore <slot>` occurs between the store and that consuming load — the slot is
      not re-assigned, so the object consumed IS the object `MoneyHelper` returned;
  A4  the consuming method's NAME is reported per site, not assumed.  T42 §2 rule 4 says all
      four sites "pass it to generate(mc, …)"; two of them do not (audit finding M-9), and this
      table is how that is checked rather than believed.

EXIT 0 only if A1..A3 hold at every site found and at least one site consumes it in a
`generate` call.  EXIT 1 otherwise, naming the breach — so the assertion is failable, and
`src/t46-assert-pathb-slot.sh` exercises it negatively against a slot-drifted transcript.

No money is read, computed or emitted here.  This is a bytecode-dataflow assertion only.

Usage:  python3 analysis/t46_assert_pathb_slot.py <javap-transcript> [...]
"""
import re
import sys

INSN = re.compile(r"^\s+(\d+):\s+(\S+)\s*(.*)$")
METHOD = re.compile(r"^\s{2}\S.*[;{]\s*$")
GET_MC = "MoneyHelper.getMathContext"
MC_DESC = "Ljava/math/MathContext;"


def slot_of(op, args):
    """Return the local-variable slot an astore/aload touches, or None."""
    m = re.match(r"^(astore|aload)_(\d+)$", op)
    if m:
        return int(m.group(2))
    m = re.match(r"^(astore|aload)$", op)
    if m:
        m2 = re.match(r"^(\d+)", args.strip())
        if m2:
            return int(m2.group(1))
    return None


def parse_methods(path):
    """[(method-signature, [(offset, opcode, operand-text)])]"""
    methods, cur, sig = [], None, None
    for raw in open(path, errors="replace"):
        line = raw.rstrip("\n")
        m = INSN.match(line)
        if m and cur is not None:
            cur.append((int(m.group(1)), m.group(2), m.group(3)))
            continue
        if METHOD.match(line) and "(" in line:
            if sig is not None:
                methods.append((sig, cur))
            sig, cur = line.strip(), []
    if sig is not None:
        methods.append((sig, cur))
    return methods


def invoked_name(operand):
    """'// Method org/.../Foo.bar:(...)X' -> ('Foo.bar', '(...)X')"""
    m = re.search(r"//\s+(?:Interface)?Method\s+(\S+):(\(\S*)", operand)
    if not m:
        return None, None
    ref, desc = m.group(1), m.group(2)
    ref = ref.replace("/", ".")
    parts = ref.rsplit(".", 1)
    short = (parts[0].rsplit(".", 1)[-1] + "." + parts[1]) if len(parts) == 2 else ref
    return short, desc


def check(path):
    print("=" * 100)
    print("transcript: %s" % path)
    print("=" * 100)
    breaches, sites = [], []

    for sig, insns in parse_methods(path):
        for i, (off, op, args) in enumerate(insns):
            if op != "invokestatic" or GET_MC not in args:
                continue
            short = sig.split("(")[0].split()[-1]

            # ---- A1 ----------------------------------------------------------------------
            if i + 1 >= len(insns):
                breaches.append("%s @%d: getMathContext is the last instruction; no astore"
                                % (short, off))
                continue
            noff, nop, nargs = insns[i + 1]
            slot = slot_of(nop, nargs)
            if slot is None or not nop.startswith("astore"):
                breaches.append("A1 %s @%d: instruction after getMathContext is %r, expected astore"
                                % (short, off, nop))
                continue

            # ---- A2 / A3 -----------------------------------------------------------------
            # ALL consumers of the slot are collected, up to the first re-assignment.  Taking
            # only the first would have hidden that assembleLoanScheduleFrom feeds the slot to
            # updateInterestForEqualAmortization *and* to LoanScheduleGenerator.generate.
            reassigned_at = None
            consumers = []
            for j in range(i + 2, len(insns)):
                joff, jop, jargs = insns[j]
                s = slot_of(jop, jargs)
                if jop.startswith("astore") and s == slot:
                    reassigned_at = joff
                    break
                if jop.startswith("aload") and s == slot:
                    for koff, kop, kargs in insns[j + 1:j + 12]:
                        if kop.startswith("invoke"):
                            name, desc = invoked_name(kargs)
                            if desc and MC_DESC in desc:
                                consumers.append((joff, koff, name, desc))
                            break

            if not consumers:
                if reassigned_at is not None:
                    breaches.append("A3 %s: slot %d re-assigned at @%d before any MathContext-typed"
                                    " consumer -- the object handed on is NOT the one MoneyHelper "
                                    "returned" % (short, slot, reassigned_at))
                else:
                    breaches.append("A2 %s: slot %d stored from getMathContext @%d is never loaded "
                                    "into an invoke whose descriptor takes a MathContext"
                                    % (short, slot, off))
                continue

            for aoff, coff, name, desc in consumers:
                argpos = desc[1:desc.index(")")]
                params = re.findall(r"\[*(?:[BCDFIJSZ]|L[^;]+;)", argpos)
                try:
                    mc_index = params.index(MC_DESC) + 1
                except ValueError:
                    mc_index = None
                sites.append({
                    "method": short, "getmc_at": off, "slot": slot, "astore_at": noff,
                    "aload_at": aoff, "invoke_at": coff, "consumer": name,
                    "mc_arg_position": mc_index, "n_params": len(params),
                    "reassigned_at": reassigned_at,
                })

    print("%-42s %-6s %-8s %-8s %-8s %-46s %s"
          % ("method", "slot", "getMC@", "astore@", "aload@", "consumer", "mc arg pos"))
    print("-" * 140)
    for s in sites:
        print("%-42s %-6d %-8d %-8d %-8d %-46s %s of %d"
              % (s["method"], s["slot"], s["getmc_at"], s["astore_at"], s["aload_at"],
                 s["consumer"], s["mc_arg_position"], s["n_params"]))
    print()
    print("consumer sites found: %d  (across %d distinct getMathContext call sites)"
          % (len(sites), len({(s["method"], s["getmc_at"]) for s in sites})))

    gen = [s for s in sites if s["consumer"].endswith(".generate")]
    other = [s for s in sites if not s["consumer"].endswith(".generate")]
    print("  consumed by a `generate(...)` call : %d  (%s)"
          % (len(gen), ", ".join(s["method"] for s in gen) or "-"))
    print("  consumed by something ELSE         : %d  (%s)"
          % (len(other), ", ".join("%s -> %s" % (s["method"], s["consumer"]) for s in other) or "-"))

    if not sites:
        breaches.append("no getMathContext store is consumed by any MathContext-typed invoke "
                        "anywhere in this transcript")
    if not gen:
        breaches.append("no getMathContext site feeds a `generate(...)` call -- T42 rule 4's "
                        "linchpin claim does not hold for this artefact")

    print()
    if breaches:
        for b in breaches:
            print("BREACH: " + b, file=sys.stderr)
        print("FAIL -- %d breach(es)." % len(breaches))
        return 1
    print("PASS -- A1, A2 and A3 hold at every site; the MathContext handed to the generator is "
          "the SAME local slot MoneyHelper.getMathContext stored into, un-reassigned.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    rc = 0
    for p in sys.argv[1:]:
        rc |= check(p)
    sys.exit(rc)
