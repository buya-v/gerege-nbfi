# (removed) — this was a duplicate copy of the G-8 section

**The authoritative G-8 write-up is `.softhouse/gates.md` § `G-8 — TWO phenomena at the rounding
floor, under one gate id`. There is no second copy, deliberately.**

This file used to hold a working copy of that section. T112 removed the body rather than re-syncing
it, for the reason the section itself exists to guard against: **a corrected document with a second
copy one directory away is precisely how pattern P-23 leaks.** The copy had already drifted from
`gates.md` in two paragraphs, and it carried the exact sentence T101 rejected as F-1 — *"family A
exists at all 12 rates swept"*, which is false; family A exists at **11 of the 12**, and not at
600.0 %.

The removed text is in git history if anyone needs it (`git log --follow` this path). Nothing
measured is lost — every number the copy carried is in `.softhouse/gates.md` and in the `out/`
directory beside this file.

Corrections applied after this capture was taken: **`CORRECTIONS-T112.md`** in this directory.
