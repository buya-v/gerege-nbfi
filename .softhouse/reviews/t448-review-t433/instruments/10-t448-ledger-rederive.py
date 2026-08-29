#!/usr/bin/env python3
"""
T448 -- RE-DERIVE THE MONEY, do not read it.

T433's sweep found exactly one post-fork observation whose bytes differ from its birth blob:
`.softhouse/capture/tierA-a2/out/A2-370-db-ledger-state.txt`. T433 adjudicates that difference
as a legitimate re-capture and states that "the per-transaction double-entry table still
balances in integer minor units with balanced = t on every row".

THAT SENTENCE IS A REPORT. This file does not accept it. It re-derives every per-transaction
debit and credit total from the RAW `acc_gl_journal_entry` rows in each version of the file and
compares the result against the file's OWN summary table -- so a summary table that was edited
without its raw rows, or raw rows edited without the summary, both come out RED here.

ENGINE (P-33/P-53): Python `str.split` on the psql box-table pipe delimiter. No regex, so no
regex dialect to get wrong. Amounts are converted to INTEGER MINOR UNITS BY STRING SURGERY --
the integer part and the fractional part are sliced as text and combined with integer
arithmetic. `float()` and `Decimal` are never called, because the Gerege non-negotiable is that
no money value passes through a binary floating-point type even in an intermediate calculation.
Any leg whose amount carries a non-zero digit BELOW the MNT minor unit (2 places) is a
sub-minor-unit residue and is reported, never silently rounded away.

CALIBRATION BEFORE ANY NEGATIVE (P-72; C4). Before this file may report "0 imbalances" it must
prove it can SEE an imbalance: a synthetic transaction with a deliberately unbalanced leg is
pushed through the same summing code and MUST come out RED. If the calibration transaction
passes, the instrument is not measuring and the run REFUSES.

CORPUS ASSERTION (C3). Zero parsed legs, zero parsed summary rows, or a summary row with no
matching legs is exit 2 -- never exit 0. A balance check over an empty ledger balances.

EXIT: 0 = every transaction balances and every recomputation matches the file's own summary;
1 = a difference was found; 2 = REFUSED, the instrument could not measure.
"""
import subprocess
import sys

REL = ".softhouse/capture/tierA-a2/out/A2-370-db-ledger-state.txt"
BIRTH = "aae501b576ecca1d70881c3cff49c43d2576b0f6"
MINOR_DIGITS = 2          # MNT, ISO 4217 numeric 496, minor unit 2
CREDIT, DEBIT = "1", "2"  # Fineract JournalEntryType ordinals, confirmed against L1 below

rc = 0


def refuse(*lines):
    print()
    for ln in lines:
        print("REFUSED: %s" % ln)
    sys.exit(2)


def to_minor(text):
    """'889549.420000' -> (88954942, residue_digits_below_the_minor_unit). No float, no Decimal."""
    text = text.strip()
    neg = text.startswith("-")
    if neg:
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    frac = (frac + "0" * MINOR_DIGITS)
    minor_part = frac[:MINOR_DIGITS]
    residue = frac[MINOR_DIGITS:].rstrip("0")
    val = int(whole) * (10 ** MINOR_DIGITS) + int(minor_part)
    return (-val if neg else val), residue


def rows_of(lines, header_key, ncols):
    """psql box-table rows following the header line that contains header_key."""
    out, armed = [], False
    for ln in lines:
        if header_key in ln:
            armed = True
            continue
        if not armed:
            continue
        if ln.startswith("("):
            break
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != ncols:
            continue
        if cells[0] == "id" or cells[0] == "transaction_id":
            continue
        out.append(cells)
    return out


def audit(label, text):
    global rc
    lines = text.split("\n")
    legs = rows_of(lines, "acc_gl_journal_entry: EVERY row", 20)
    summ = rows_of(lines, "per-transaction double-entry check", 6)
    print()
    print("=== %s ===" % label)
    print("    raw journal-entry legs parsed : %d" % len(legs))
    print("    summary rows parsed           : %d" % len(summ))
    if not legs or not summ:
        refuse("parsed %d legs and %d summary rows from %s." % (len(legs), len(summ), label),
               "A double-entry check over an empty ledger balances. That is not a pass.")

    # Ordinal check, from the data itself: L1 is a disbursement, whose Loan Portfolio leg must
    # be the DEBIT. If that is not type_enum 2 the ordinals below are the wrong way round.
    l1 = [c for c in legs if c[1] == "L1" and c[6] == "10201"]
    if not l1 or l1[0][4] != DEBIT:
        refuse("the JournalEntryType ordinal calibration FAILED: L1's Loan Portfolio leg is not",
               "type_enum %s. Every debit/credit total below would be inverted." % DEBIT)
    print("    ordinal calibration OK: L1's Loan Portfolio (10201) leg is type_enum %s = DEBIT"
          % DEBIT)

    tx = {}
    residues = []
    for c in legs:
        tid, tenum, amt = c[1], c[4], c[9]
        val, residue = to_minor(amt)
        if residue:
            residues.append((c[0], tid, amt, residue))
        d, cr, n = tx.get(tid, (0, 0, 0))
        if tenum == DEBIT:
            d += val
        elif tenum == CREDIT:
            cr += val
        else:
            refuse("leg id %s carries type_enum %r, which is neither DEBIT nor CREDIT." % (c[0], tenum))
        tx[tid] = (d, cr, n + 1)

    # ---- CALIBRATION: prove an imbalance is visible before reporting that there is none. ----
    cal = dict(tx)
    cal["T448-CALIBRATION-UNBALANCED"] = (100000001, 100000000, 2)
    cal_caught = [t for t, (d, cr, _n) in cal.items() if d != cr]
    if cal_caught != ["T448-CALIBRATION-UNBALANCED"]:
        refuse("P-72 CALIBRATION FAILED: a synthetic transaction with debits 100000001 and",
               "credits 100000000 was NOT the unique imbalance this code caught (caught: %r)."
               % cal_caught, "An instrument that cannot see a planted imbalance may not report zero.")
    print("    P-72 calibration OK: a planted 1-minor-unit imbalance IS caught by this code.")

    bad = []
    for tid, (d, cr, n) in sorted(tx.items()):
        if d != cr:
            bad.append((tid, d, cr, n))
    print("    transactions recomputed       : %d" % len(tx))
    print("    IMBALANCED transactions       : %d" % len(bad))
    for tid, d, cr, n in bad:
        print("      IMBALANCED %s legs=%d debit_minor=%d credit_minor=%d delta=%d"
              % (tid, n, d, cr, d - cr))
        rc = 1
    print("    legs with a residue BELOW the MNT minor unit : %d" % len(residues))
    for i, tid, amt, res in residues[:10]:
        print("      SUB-MINOR-UNIT leg id=%s tx=%s amount=%s residue=.%s" % (i, tid, amt, res))
        rc = 1

    # ---- cross-check the file's OWN summary table against the recomputation ----
    unmatched, mismatch = [], []
    for c in summ:
        tid, legn, dmin, cmin, delta, whole = c
        if tid not in tx:
            unmatched.append(tid)
            continue
        d, cr, n = tx[tid]
        if (str(n), str(d), str(cr), str(d - cr)) != (legn, dmin, cmin, delta):
            mismatch.append((tid, (legn, dmin, cmin, delta), (n, d, cr, d - cr)))
        if whole != "t" and not any(r[1] == tid for r in residues):
            mismatch.append((tid, ("every_leg_is_a_whole_minor_unit", whole), ("recomputed", "t")))
    if unmatched:
        refuse("%d summary row(s) name a transaction with NO raw legs: %s" % (len(unmatched),
               unmatched[:5]), "The summary table and the raw rows are not the same ledger.")
    print("    summary rows CONTRADICTED by the recomputation : %d" % len(mismatch))
    for tid, said, got in mismatch:
        print("      MISMATCH %s file said %r, recomputed %r" % (tid, said, got))
        rc = 1
    if len(summ) != len(tx):
        print("      COUNT MISMATCH summary rows=%d recomputed transactions=%d" % (len(summ), len(tx)))
        rc = 1
    tot_d = sum(d for d, _c, _n in tx.values())
    tot_c = sum(c for _d, c, _n in tx.values())
    print("    WHOLE-LEDGER debit_minor=%d  credit_minor=%d  delta=%d" % (tot_d, tot_c, tot_d - tot_c))
    if tot_d != tot_c:
        rc = 1
    return tx


ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE,
                      check=True).stdout.decode().strip()
disk = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + REL], stdout=subprocess.PIPE,
                      check=True).stdout.decode()
birth = subprocess.run(["git", "-C", ROOT, "show", BIRTH + ":" + REL], stdout=subprocess.PIPE,
                       check=True).stdout.decode()

print("T448 -- LEDGER RE-DERIVATION of the one adjudicated post-fork difference")
print("    file  %s" % REL)
print("    birth %s   tip HEAD" % BIRTH)
tx_birth = audit("BIRTH BLOB (%s)" % BIRTH[:12], birth)
tx_head = audit("TRACKED AT HEAD", disk)

print()
print("=== IS THE DIFFERENCE ADDITIVE? (append-only ledger, corrections are reversing entries) ===")
changed = [t for t in tx_birth if t in tx_head and tx_birth[t] != tx_head[t]]
removed = sorted(set(tx_birth) - set(tx_head))
added = sorted(set(tx_head) - set(tx_birth))
print("    transactions at birth %d -> at HEAD %d" % (len(tx_birth), len(tx_head)))
print("    ADDED   : %s" % added)
print("    REMOVED : %s" % removed)
print("    ALTERED (same id, different totals or leg count) : %s" % changed)
if removed or changed:
    print("    A ledger observation is append-only. A removed or altered transaction is NOT a")
    print("    re-capture, it is a rewrite of history.")
    rc = 1

print()
print("EXIT %d" % rc)
sys.exit(rc)
