base = '/tmp/t58mut/nexus/internal/apps/loanschedule/'

# --- SMOOTHINGOFF: omit checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
p = base + 'emi.go'
s = open(p).read()
old = '''		original, difference := emiAdjustment(related)
		if !shouldBeAdjusted(len(related), original, difference, m.minorDigits) {
			return
		}'''
new = '''		if MutT58 == "SMOOTHINGOFF" {
			return
		}
		original, difference := emiAdjustment(related)
		if !shouldBeAdjusted(len(related), original, difference, m.minorDigits) {
			return
		}'''
assert old in s
s = s.replace(old, new, 1)

# --- NOFINALADJ: the final row keeps the level installment (no residual absorption)
old2 = '''	m.periods[idx].emiMinor += totalDisbursed + totalDueInterest - totalEMI
	if m.periods[idx].emiMinor < 0 {'''
new2 = '''	if MutT58 == "NOFINALADJ" {
		return
	}
	m.periods[idx].emiMinor += totalDisbursed + totalDueInterest - totalEMI
	if m.periods[idx].emiMinor < 0 {'''
assert old2 in s
s = s.replace(old2, new2, 1)
open(p, 'w').write(s)

# --- MONTHENDCLAMP (structural): clamp and continue from the clamped day, i.e. no re-anchor
p2 = base + 'generator.go'
s2 = open(p2).read()
old3 = '''	if unit != contract.FrequencyMonths {
		return d
	}
	lo := int32(28)'''
new3 = '''	if unit != contract.FrequencyMonths {
		return d
	}
	if MutT58 == "MONTHENDCLAMP" {
		return d
	}
	lo := int32(28)'''
assert old3 in s2
s2 = s2.replace(old3, new3, 1)
open(p2, 'w').write(s2)
print("patch2 ok")
