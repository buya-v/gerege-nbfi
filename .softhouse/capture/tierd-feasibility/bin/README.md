# tierd-feasibility/bin — streaming, loan-keyed Feign log extractor

`extract.py` streams a Fineract Feign debug log (`[Api#method] ---> METHOD url` …
`---> END HTTP (n-byte body)`, `<--- HTTP/1.1 status` … `<--- END HTTP`) and writes
one JSON file per body. It never loads a whole log: it reads line by line and keeps
bodies only for `/loans` traffic (a few MB), discarding the global initializer's
seeding without materialising it.

## How loans are keyed

Attribution is by loan id, never by file order — the bug the salvaged extraction had.

* The `resourceId` in each `POST /loans` response starts a loan.
* Commands (`POST`/`PUT`/`PATCH`/`DELETE` on `/loans/{id}...`) and read-backs (`GET`)
  are attached by the id in their URL.
* Everything else (seeding, non-loan APIs) is counted and skipped.

## Run

```
python3 extract.py LOG --out DIR
```

`LOG` is always an argument; no run-time path is hard-coded. Output:

* `loan-<id>-create-request.json`
* `loan-<id>-<command>-request[-n].json` / `loan-<id>-<command>-response[-n].json`
* `loan-<id>-<label>[-n].json` — read-backs
* `manifest.json` — source line, bytes, sha256, loan id, HTTP status, method, URL
* `summary.json` — totals, per-loan counts, and how many bytes were skipped

Bodies are written verbatim from the log, so money keeps the exact oracle text (no
float, no re-serialisation). Empty bodies are skipped.

## Control test — `control-test-uc6.txt` (PASS)

```
python3 control_test.py --log feign-uc6.log \
    --verified-dir ../uc6 --extract extract.py
```

It runs `extract.py` over the UC6 log and asserts that every verified file in
`../uc6/` is emitted at the **same source line and under the same loan id**, with
**byte-identical** content: 15/15 files OK, including loan 10's create body (780 B at
line 34891, not loan 1's 590 B — the exact body the salvaged run fabricated).

The verified UC6 names are hand-curated, so the test compares content, not names:
the same `associations=all` read is `loan-1-detail-associations-all.json` for loan 1
but `loan-10-detail-all.json` for loan 10, which no uniform naming rule could produce.

## s1 report — `report-s1.txt`

One loan (`resourceId` 12): 1 create, 6 command requests, 6 command responses,
20 read-backs (3 schedule read-backs), 33 files, 291,654 bytes. Of 603 exchanges,
576 are skipped seeding (240,013,663 bytes, 98% of source bytes). **No s1 bodies are
committed** — they are reproducible from the log with the command above.
