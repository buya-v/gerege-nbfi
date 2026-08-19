base = '/tmp/t58mut/nexus/internal/apps/loanschedule/'

p = base + 'emi.go'
s = open(p).read()

old = '''	base := majorFromMinor(s.outstandingMinor, m.minorDigits)
	t1 := roundSignificant(new(big.Rat).Mul(base, s.rateFactorTillDue), m.precision)
	t2 := roundSignificant(new(big.Rat).Quo(t1, ratInt64(lengthTillDue)), m.precision)
	t3 := roundSignificant(new(big.Rat).Mul(t2, ratInt64(daysBetween(s.from, s.due))), m.precision)
	return t3'''
new = '''	base := majorFromMinor(s.outstandingMinor, m.minorDigits)
	if MutT58 == "TEXTBOOK" {
		v := new(big.Rat).Mul(base, s.rateFactorTillDue)
		v.Mul(v, ratInt64(daysBetween(s.from, s.due)))
		v.Quo(v, ratInt64(lengthTillDue))
		return roundSignificant(v, m.precision)
	}
	t1 := roundSignificant(new(big.Rat).Mul(base, s.rateFactorTillDue), m.precision)
	t2 := roundSignificant(new(big.Rat).Quo(t1, ratInt64(lengthTillDue)), m.precision)
	t3 := roundSignificant(new(big.Rat).Mul(t2, ratInt64(daysBetween(s.from, s.due))), m.precision)
	return t3'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''	v = roundSignificant(new(big.Rat).Quo(v, ratInt64(calculatedDays)), m.precision)
	return roundScale(v, m.scale)'''
new2 = '''	v = roundSignificant(new(big.Rat).Quo(v, ratInt64(calculatedDays)), m.precision)
	if MutT58 == "NOSETSCALE" {
		return v
	}
	return roundScale(v, m.scale)'''
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = '''	return m.rateFactorByRepaymentPeriod(
		m.periodRatio(p),
		daysBetween(s.from, p.due),
		daysBetween(p.from, p.due))'''
new3 = '''	mult := m.periodRatio(p)
	if MutT58 == "PERIODRATIO" {
		mult = ratInt64(m.repaymentEvery)
	}
	return m.rateFactorByRepaymentPeriod(
		mult,
		daysBetween(s.from, p.due),
		daysBetween(p.from, p.due))'''
assert old3 in s
s = s.replace(old3, new3, 1)

old4 = '''func (m *scheduleModel) periodRatioSeed(p *repaymentPeriod) civilDate {
	seed := m.startDate()'''
new4 = '''func (m *scheduleModel) periodRatioSeed(p *repaymentPeriod) civilDate {
	seed := m.startDate()
	if MutT58 == "SEEDSTART" {
		return seed
	}'''
assert old4 in s
s = s.replace(old4, new4, 1)
open(p, 'w').write(s)

p2 = base + 'generator.go'
s2 = open(p2).read()
old5 = '''	if seed.Day > 28 && d.Day >= 28 {'''
new5 = '''	lo := int32(28)
	if MutT58 == "REANCHORGT" {
		lo = 29
	}
	if seed.Day > 28 && d.Day >= lo {'''
assert old5 in s2
s2 = s2.replace(old5, new5, 1)
open(p2, 'w').write(s2)
print("patched ok")
