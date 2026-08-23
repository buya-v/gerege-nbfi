# T306 — adjudicate the admit.go widening (independent review)

Branch: softhouse/T306-adjudicate-admit-widening
Fork point: 5964ab5 (main)
Status: IN PROGRESS — early commit per SIGTERM lesson.

## Task
Second-guess the driver's merge-conflict judgement call in
nexus/internal/apps/ledger/conformance/admit.go, which widened the
`ledger.opening.balance.and.closure` capability-row claim gate from ONE
observed shape (request.command == defineOpeningBalance) to THREE.

Five questions from the brief:
1. Is the widening keyed on the right thing (expect.refusal.code is an OUTPUT)?
2. Is it still default-deny for a FOURTH shape (acceptance)?
3. Did it preserve T296's load-bearing measurement (in_graded_domain flip)?
4. Is the refusal-message comment true against the store?
5. Should three arms have been three capability rows / a finer claim mechanism?

(findings appended below as they are established)
