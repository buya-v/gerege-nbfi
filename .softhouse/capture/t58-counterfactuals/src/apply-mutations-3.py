p = '/tmp/t58mut/nexus/internal/apps/loanschedule/t58cf/main.go'
s = open(p).read()
s = s.replace('\t\tRepaymentEvery              int    `json:"repaymentEvery"`',
              '\t\tRepaymentEvery              int    `json:"repaymentEvery"`\n\t\tRepaymentFrequency          int    `json:"repaymentFrequency"`')
s = s.replace('\t\t\tFromDate                string  `json:"fromDate"`',
              '\t\t\tFromDate                string  `json:"fromDate"`\n\t\t\tPeriodFromDate          string  `json:"periodFromDate"`')
s = s.replace('''func request(c capCase) contract.GenerateRequest {
	in := c.Inputs''', '''func request(c capCase) contract.GenerateRequest {
	in := c.Inputs
	if in.RepaymentEvery == 0 {
		in.RepaymentEvery = in.RepaymentFrequency
	}''')
s = s.replace('''			dates = append(dates, dobs{i, p.Type, "from_date", p.FromDate}, dobs{i, p.Type, "due_date", p.DueDate})''',
              '''			from := p.FromDate
			if from == "" {
				from = p.PeriodFromDate
			}
			dates = append(dates, dobs{i, p.Type, "from_date", from}, dobs{i, p.Type, "due_date", p.DueDate})''')
open(p, 'w').write(s)
print('ok')
