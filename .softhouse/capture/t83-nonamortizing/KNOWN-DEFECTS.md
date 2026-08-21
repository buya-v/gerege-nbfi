# Known defect in this directory's probe sources — read before re-running anything here

**Pointer only. The record lives in one place and this is not it** (P-27 — two copies of a claim is
one claim and one time bomb).

`src/classify-boundary.py` carries a **live `float()` on line 102** while its own header on **line
20** states *"Nothing here constructs a float."* The header is false. It is **P-25 in a live file**.

**Do not edit the script.** It is an executed probe source; editing even a comment leaves
`out/capture-t83-raw.json` and `out/measured-boundary.json` no longer byte-reproducible from the
sources that produced them.

**No published result is affected** — measured by T122, not assumed.

Full record, including the measurement that shows nothing is affected and what a re-run must fix
first, is **D-1** in `.softhouse/capture/t100-g8-rescope/CORRECTIONS-T112.md`, and in
`.softhouse/gates.md` § G-8 under *"Two KNOWN DEFECTS in this gate's own probe sources"*.

Raised by T114 (F-T114-5), re-verified and recorded by T122.
