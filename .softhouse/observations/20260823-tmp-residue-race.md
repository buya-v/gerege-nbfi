# DRIVER OBSERVATION — the `/tmp/t234_matrix2.txt` residue is RECREATED DURING A FIRE, not just at boot

Recorded by local fire `20260823-080004` while T273/T285 were still in flight. Perishable evidence: it is a
file mtime, and the next run overwrites it.

## The measurement

| when | mtime of `/tmp/t234_matrix2.txt` |
|---|---|
| fire open, 08:01, before any worker was dispatched | `Aug 22 22:50` |
| 08:37, with five workers live | `Aug 23 08:37` |

Host uptime at fire open was **5 days 13 h** — **this Mac has not rebooted**, so nothing about a boot-time
`/tmp` clear explains the change. The file was **deleted and recreated by a concurrently running agent** during
this fire.

## Why it matters

T273's finding, and the driver's own first-hand RED/GREEN at fire open, framed the hazard as a **reboot**
exposure: macOS clears `/tmp`, so the first fire after a restart gets exit 2 with no probe line.

**`T271` independently reported the stronger form while doing unrelated work** — it was dispatched to settle a
6-of-7 agreement in `t219-g8-residual` and was never asked about `/tmp`:

> `conformance.sh` exits 2 iff `/tmp/t234_matrix2.txt` is absent, PASSES when present, on a byte-identical
> tree — both readings committed. It is **not reboot-only**: the file reappeared **within seconds** of my probe
> deleting it, so the bar's colour depends on **inter-agent timing**.

The mtime above is the driver's own corroboration of that, from a different angle: not "it came back after I
deleted it", but "it moved 9 h 47 m forward while five agents ran".

**So the exposure is wider than a reboot.** A reboot is a once-per-restart hazard a human would eventually
notice. **A race is a per-run hazard that is invisible and non-deterministic**, and it means *the bar's colour
can differ between two runs over a byte-identical tree depending on which agent last touched a file in `/tmp`*.
The bar grades every money claim in this program.

## What this does NOT establish, and must not be read as

- It does **not** identify which agent recreated the file. Five were live and any of them may have run the
  instrument; the driver did not instrument that and is not inferring it.
- It does **not** settle T273's fix as right or wrong. **`T285` is reviewing T273 independently and was
  deliberately NOT told about this observation**, so that its adjudication of the rescued predecessor's claim
  ("the hazard is a RACE, not a reboot") stays its own. This file is dated and committed so the cross-
  corroboration can be recorded at merge **without** having contaminated the review that produces it.
- It does **not** mean any past green bar was wrong. It means **no past green bar on this host is reproducible
  from a clean checkout**, which is a different and worse property.

## For whoever merges T273/T285

Cross-corroborate these three independent sources before writing the verdict, and note they arrived by three
different routes: the driver's RED/GREEN `rm`-and-restore at fire open, `T271`'s incidental observation while
working on something else, and this mtime. **Three routes agreeing is stronger than one instrument repeated
three times.**
