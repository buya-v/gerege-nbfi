package provisioning

// ProvisioningCategory is the Go port of the m_provision_category aggregate:
// the named bucket a provisioning criteria definition reserves against (for
// example "Doubtful", "Substandard", "Loss"). [VERIFIED: ProvisioningCategory.java
// — @Table(name = "m_provision_category"), category_name unique NOT NULL,
// description nullable.]
type ProvisioningCategory struct {
	ID          int64
	Name        string
	Description string
}
