#!/usr/bin/env python3
"""
T24 — compare the WITH-LOOP re-derivation against RAW OBSERVED oracle output.

Input: any file in the raw `CASE P=<principal> n=<n> rate=<r> totalInterest=... totalRepayment=... | #k:p/i/t/b ...`
form emitted by T23Probe2.java / T24Probe.java. Nothing is hand-entered; every oracle number is
read out of the raw file.

Usage:  python3 t24_check_against_raw.py <raw-output-file> [...]
"""
import datetime
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t24_rederive_with_loop.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

START = datetime.date(2024, 1, 1)

PAT = re.compile(r"(?:\S+ )?CASE P=(\d+) n=(\d+) rate=([\d.]+) totalInterest=([\d.]+) "
                 r"totalRepayment=([\d.]+) \|(.*)")


def parse(path):
    out = []
    for line in open(path):
        m = PAT.match(line.strip())
        if not m:
            continue
        per = {}
        for tok in m.group(6).split():
            num, vals = tok.split(":")
            p, i, t, b = vals.split("/")
            per[int(num[1:])] = (p, i, t, b)
        out.append((int(m.group(1)), int(m.group(2)), m.group(3), m.group(4), m.group(5), per))
    return out


def run(path):
    print(f"### {os.path.basename(path)}")
    hdr = (f"{'principal':>10} {'n':>3} {'rate':>6} | {'oracleEMI':>12} {'loopEMI':>12} "
           f"{'noLoopEMI':>12} | {'oracleLast':>12} {'loopLast':>12} {'noLoopLast':>12} | "
           f"{'loop':>10} {'noloop':>10}  trace")
    print(hdr)
    print("-" * len(hdr))
    n_loop_ok = n_noloop_ok = 0
    total = 0
    for P, n, rate, ti, tr, per in parse(path):
        total += 1
        withl = rd.derive(P, n, rate, START, apply_loop=True)
        without = rd.derive(P, n, rate, START, apply_loop=False)

        def verdict(d):
            ok = str(d["total_interest"]) == ti and str(d["total_repayment"]) == tr
            for k in range(1, n + 1):
                r = d["rows"][k - 1]
                op, oi, ot, ob = per[k]
                if (str(r["principal"]) != op or str(r["interest"]) != oi
                        or str(r["emi"]) != ot or str(r["balance"]) != ob):
                    ok = False
            return ok

        okl, okn = verdict(withl), verdict(without)
        n_loop_ok += okl
        n_noloop_ok += okn
        trace = ",".join(f"{a}@{b}" for a, b, _ in withl["loop"])
        print(f"{P:>10} {n:>3} {rate:>6} | {per[1][2]:>12} {str(withl['emi']):>12} "
              f"{str(without['emi']):>12} | {per[n][2]:>12} "
              f"{str(withl['rows'][-1]['emi']):>12} {str(without['rows'][-1]['emi']):>12} | "
              f"{'MATCH' if okl else 'MISMATCH':>10} {'MATCH' if okn else 'MISMATCH':>10}  {trace}")
    print()
    print(f"with-loop model: {n_loop_ok}/{total} cases match the oracle on every period, "
          f"every column, and both totals")
    print(f"no-loop  model: {n_noloop_ok}/{total}")
    print()


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(p)
