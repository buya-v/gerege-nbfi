p = "/tmp/t387/t359drive/nexus/internal/apps/ledger/conformance/impl.go"
s = open(p).read()
old = '''		amt, cerr := ledger.MinorUnitsFromDecimalText(l.AmountMajorText, req.Currency.MinorUnitDigits)
		if cerr != nil {
			return PostedEntry{}, nil, fmt.Errorf("leg %d: %w", i, cerr)
		}
'''
new = '''		amt, cerr := ledger.MinorUnitsFromDecimalText(l.AmountMajorText, req.Currency.MinorUnitDigits)
		if cerr != nil {
			// T387 SCRATCH DRIVE OF T359'S MEASURED REMEDY. Not on any branch.
			return PostedEntry{}, &Refusal{
				HTTPStatus: 422,
				Code:       "error.msg.glJournalEntry.sub.minor.unit.residue",
				Message:    fmt.Sprintf("leg %d: %v", i, cerr),
			}, nil
		}
'''
assert s.count(old) == 1, s.count(old)
open(p, "w").write(s.replace(old, new))
print("patched")
