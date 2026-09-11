# Journal-entry leg -> loan transaction TYPE join (sweep)

Every swept `/journalentries` leg carries only `transactionId` =
`L<loanTransactionId>`; the transaction **type** comes only from the loan
read-backs (`transactions[].id -> transactions[].type.code`).  Amounts are
integer minor units; the raw sweep bodies keep decimal major units.

Legs joined: 1333; unmatched by read-back: 20.

**20 unmatched legs (5 transactions, loans 27, 27, 27, 28, 28)** carry no type in the read-backs;
their posting shape infers `loanTransactionType.accrual` (see the section at the end).

| type | value | loans | transactions | legs |
| --- | --- | --- | --- | --- |
| `loanTransactionType.accrual` | Accrual | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 45, 46, 47, 48, 49, 50 | L3, L7, L11, L15, L19, L23, L29, L33, L37, L41, L47, L53, L57, L63, L69, L77, L82, L87, L91, L95, L99, L105, L109, L113, L117, L123, L127, L128, L129, L130, L131, L132, L133, L134, L135, L136, L137, L138, L139, L140, L141, L142, L149, L150, L151, L152, L153, L154, L155, L156, L157, L158, L159, L160, L161, L162, L163, L164, L172, L173, L174, L175, L176, L177, L178, L179, L180, L181, L182, L183, L184, L185, L186, L187, L188, L189, L190, L191, L192, L193, L194, L195, L196, L197, L198, L199, L200, L201, L204, L205, L206, L207, L208, L209, L210, L211, L212, L213, L214, L215, L216, L217, L218, L219, L220, L221, L222, L223, L224, L225, L226, L227, L228, L229, L230, L231, L232, L233, L236, L237, L238, L239, L240, L241, L242, L243, L244, L245, L246, L247, L248, L250, L251, L252, L253, L254, L255, L257, L260, L261, L262, L263, L264, L265, L266, L267, L268, L269, L270, L271, L272, L273, L274, L275, L276, L277, L278, L279, L280, L281, L282, L283, L284, L285, L286, L287, L288, L289, L290, L291, L292, L293, L294, L295, L296, L297, L298, L299, L300, L301, L302, L303, L309, L310, L311, L312, L313, L314, L315, L316, L317, L318, L319, L320, L321, L322, L324, L325, L326, L327, L328, L331, L333, L334, L335, L336, L337, L338, L339, L340, L341, L342, L343, L344, L345, L346, L347, L348, L349, L350, L351, L352, L353, L354, L355, L356, L357, L358, L359, L360, L361, L362, L363, L364, L365, L366, L367, L368, L369, L370, L371, L372, L373, L374, L375, L376, L382, L383, L384, L385, L386, L387, L388, L389, L390, L391, L392, L393, L394, L395, L396, L397, L398, L399, L404, L407, L409, L412, L414, L417, L418, L419, L420, L421, L422, L423, L424, L425, L426, L427, L428, L429, L430, L431, L432, L433, L434, L435, L436, L437, L441, L450, L456, L459, L468, L469, L473, L480, L483, L489, L493, L499 | 642 |
| `loanTransactionType.accrualAdjustment` | Accrual Adjustment | 13, 14, 15, 33, 35, 36, 45, 46 | L60, L66, L72, L305, L378, L401, L452, L462, L465 | 18 |
| `loanTransactionType.chargeOff` | Charge-off | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46, 47, 48, 49, 50 | L4, L8, L12, L16, L20, L24, L25, L30, L34, L38, L42, L43, L48, L54, L58, L64, L65, L70, L71, L78, L84, L88, L92, L96, L100, L102, L106, L110, L114, L118, L119, L124, L146, L167, L202, L234, L256, L258, L304, L306, L329, L330, L377, L380, L402, L405, L408, L410, L415, L439, L451, L453, L460, L463, L470, L474, L479, L484, L487, L494, L497 | 339 |
| `loanTransactionType.disbursement` | Disbursement | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | L1, L5, L9, L13, L17, L21, L27, L31, L35, L39, L45, L49, L55, L61, L68, L74, L79, L85, L89, L93, L97, L103, L107, L111, L115, L121, L125, L147, L171, L203, L235, L259, L308, L332, L381, L403, L406, L411, L416, L440, L443, L445, L447, L449, L458, L467, L471, L481, L491 | 98 |
| `loanTransactionType.goodwillCredit` | Goodwill Credit | 42, 45, 46 | L444, L457, L466 | 6 |
| `loanTransactionType.interestRefund` | Interest Refund | 48, 49, 50 | L476, L478, L486, L490, L496, L500 | 18 |
| `loanTransactionType.merchantIssuedRefund` | Merchant Issued Refund | 45, 46, 48, 49, 50 | L455, L464, L475, L477, L485, L488, L495, L498 | 39 |
| `loanTransactionType.repayment` | Repayment | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 32, 33, 34, 35, 36, 39, 40, 41, 45, 46, 48, 49, 50 | L2, L6, L10, L14, L18, L22, L28, L32, L36, L40, L46, L50, L51, L52, L56, L59, L62, L67, L73, L75, L80, L81, L86, L90, L94, L98, L104, L108, L112, L116, L122, L126, L148, L249, L307, L323, L379, L400, L413, L438, L442, L454, L461, L472, L482, L492 | 153 |
| `None` |  | 27, 28 | L143, L144, L145, L165, L166 | 20 |

## `loanTransactionType.accrual` — Accrual

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 45, 46, 47, 48, 49, 50; transactions: L3, L7, L11, L15, L19, L23, L29, L33, L37, L41, L47, L53, L57, L63, L69, L77, L82, L87, L91, L95, L99, L105, L109, L113, L117, L123, L127, L128, L129, L130, L131, L132, L133, L134, L135, L136, L137, L138, L139, L140, L141, L142, L149, L150, L151, L152, L153, L154, L155, L156, L157, L158, L159, L160, L161, L162, L163, L164, L172, L173, L174, L175, L176, L177, L178, L179, L180, L181, L182, L183, L184, L185, L186, L187, L188, L189, L190, L191, L192, L193, L194, L195, L196, L197, L198, L199, L200, L201, L204, L205, L206, L207, L208, L209, L210, L211, L212, L213, L214, L215, L216, L217, L218, L219, L220, L221, L222, L223, L224, L225, L226, L227, L228, L229, L230, L231, L232, L233, L236, L237, L238, L239, L240, L241, L242, L243, L244, L245, L246, L247, L248, L250, L251, L252, L253, L254, L255, L257, L260, L261, L262, L263, L264, L265, L266, L267, L268, L269, L270, L271, L272, L273, L274, L275, L276, L277, L278, L279, L280, L281, L282, L283, L284, L285, L286, L287, L288, L289, L290, L291, L292, L293, L294, L295, L296, L297, L298, L299, L300, L301, L302, L303, L309, L310, L311, L312, L313, L314, L315, L316, L317, L318, L319, L320, L321, L322, L324, L325, L326, L327, L328, L331, L333, L334, L335, L336, L337, L338, L339, L340, L341, L342, L343, L344, L345, L346, L347, L348, L349, L350, L351, L352, L353, L354, L355, L356, L357, L358, L359, L360, L361, L362, L363, L364, L365, L366, L367, L368, L369, L370, L371, L372, L373, L374, L375, L376, L382, L383, L384, L385, L386, L387, L388, L389, L390, L391, L392, L393, L394, L395, L396, L397, L398, L399, L404, L407, L409, L412, L414, L417, L418, L419, L420, L421, L422, L423, L424, L425, L426, L427, L428, L429, L430, L431, L432, L433, L434, L435, L436, L437, L441, L450, L456, L459, L468, L469, L473, L480, L483, L489, L493, L499; legs: 642

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L3 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 105 | MNT | False | True | False |
| 1 | L3 | CREDIT | 5 | 404000 | Interest Income | 105 | MNT | False | True | False |
| 2 | L7 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 105 | MNT | False | True | False |
| 2 | L7 | CREDIT | 5 | 404000 | Interest Income | 105 | MNT | False | True | False |
| 3 | L11 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 105 | MNT | False | True | False |
| 3 | L11 | CREDIT | 5 | 404000 | Interest Income | 105 | MNT | False | True | False |
| 4 | L15 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 4 | L15 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 5 | L19 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 5 | L19 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 6 | L23 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 6 | L23 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 7 | L29 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 7 | L29 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 8 | L33 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 8 | L33 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 9 | L37 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 82 | MNT | False | True | False |
| 9 | L37 | CREDIT | 5 | 404000 | Interest Income | 82 | MNT | False | True | False |
| 10 | L41 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 82 | MNT | False | True | False |
| 10 | L41 | CREDIT | 5 | 404000 | Interest Income | 82 | MNT | False | True | False |
| 11 | L47 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 100 | MNT | False | True | False |
| 11 | L47 | CREDIT | 5 | 404000 | Interest Income | 100 | MNT | False | True | False |
| 12 | L53 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 100 | MNT | False | True | False |
| 12 | L53 | CREDIT | 5 | 404000 | Interest Income | 100 | MNT | False | True | False |
| 13 | L57 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 154 | MNT | False | True | False |
| 13 | L57 | CREDIT | 5 | 404000 | Interest Income | 154 | MNT | False | True | False |
| 14 | L63 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 154 | MNT | False | True | False |
| 14 | L63 | CREDIT | 5 | 404000 | Interest Income | 154 | MNT | False | True | False |
| 15 | L69 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 172 | MNT | False | True | False |
| 15 | L69 | CREDIT | 5 | 404000 | Interest Income | 172 | MNT | False | True | False |
| 16 | L77 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 105 | MNT | False | True | False |
| 16 | L77 | CREDIT | 5 | 404000 | Interest Income | 105 | MNT | False | True | False |
| 17 | L82 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 105 | MNT | False | True | False |
| 17 | L82 | CREDIT | 5 | 404000 | Interest Income | 105 | MNT | False | True | False |
| 18 | L87 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 18 | L87 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 19 | L91 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 19 | L91 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 20 | L95 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 20 | L95 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 21 | L99 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 21 | L99 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 22 | L105 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 22 | L105 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 23 | L109 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 107 | MNT | False | True | False |
| 23 | L109 | CREDIT | 5 | 404000 | Interest Income | 107 | MNT | False | True | False |
| 24 | L113 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 82 | MNT | False | True | False |
| 24 | L113 | CREDIT | 5 | 404000 | Interest Income | 82 | MNT | False | True | False |
| 25 | L117 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 82 | MNT | False | True | False |
| 25 | L117 | CREDIT | 5 | 404000 | Interest Income | 82 | MNT | False | True | False |
| 26 | L123 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 514 | MNT | False | True | False |
| 26 | L123 | CREDIT | 5 | 404000 | Interest Income | 514 | MNT | False | True | False |
| 27 | L127 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L127 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L128 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L128 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L129 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L129 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L130 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L130 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L131 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 27 | L131 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 27 | L132 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L132 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L133 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L133 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L134 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L134 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L135 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L135 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L136 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L136 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L137 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L137 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L138 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L138 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L139 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 27 | L139 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 27 | L140 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 27 | L140 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 27 | L141 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 27 | L141 | CREDIT | 5 | 404000 | Interest Income | 53 | MNT | False | False | False |
| 27 | L142 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 27 | L142 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 28 | L149 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L149 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L150 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L150 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L151 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L151 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L152 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L152 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L153 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 28 | L153 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 28 | L154 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L154 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L155 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L155 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L156 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L156 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L157 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L157 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L158 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L158 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L159 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L159 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L160 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L160 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L161 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 28 | L161 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 28 | L162 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 28 | L162 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 28 | L163 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 28 | L163 | CREDIT | 5 | 404000 | Interest Income | 53 | MNT | False | False | False |
| 28 | L164 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 28 | L164 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 30 | L172 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L172 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L173 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L173 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L174 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L174 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L175 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L175 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L176 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 30 | L176 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 30 | L177 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L177 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L178 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L178 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L179 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L179 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L180 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L180 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L181 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L181 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L182 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L182 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L183 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L183 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L184 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 30 | L184 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 30 | L185 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L185 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L186 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L186 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L187 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L187 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L188 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L188 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L189 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L189 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L190 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L190 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L191 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L191 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L192 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L192 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L193 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 30 | L193 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 30 | L194 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L194 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L195 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L195 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L196 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L196 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L197 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L197 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L198 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L198 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L199 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L199 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L200 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 30 | L200 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 30 | L201 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | False |
| 30 | L201 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | False |
| 31 | L204 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L204 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L205 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L205 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L206 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L206 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L207 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L207 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L208 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 31 | L208 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 31 | L209 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L209 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L210 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L210 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L211 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L211 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L212 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L212 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L213 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L213 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L214 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L214 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L215 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L215 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L216 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 31 | L216 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 31 | L217 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L217 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L218 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L218 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L219 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L219 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L220 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L220 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L221 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L221 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L222 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L222 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L223 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L223 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L224 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L224 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L225 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 31 | L225 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 31 | L226 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L226 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L227 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L227 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L228 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L228 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L229 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L229 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L230 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L230 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L231 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L231 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L232 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 31 | L232 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 31 | L233 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 31 | L233 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 32 | L236 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L236 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L237 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L237 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L238 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L238 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L239 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L239 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L240 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 32 | L240 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 32 | L241 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L241 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L242 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L242 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L243 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L243 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L244 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L244 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L245 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L245 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L246 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L246 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L247 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L247 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L248 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 32 | L248 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 32 | L250 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 32 | L250 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 32 | L251 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 32 | L251 | CREDIT | 5 | 404000 | Interest Income | 53 | MNT | False | False | False |
| 32 | L252 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 32 | L252 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 32 | L253 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 32 | L253 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 32 | L254 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 32 | L254 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 32 | L255 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 32 | L255 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 32 | L257 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 89 | MNT | False | True | False |
| 32 | L257 | CREDIT | 5 | 404000 | Interest Income | 89 | MNT | False | True | False |
| 33 | L260 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L260 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L261 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L261 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L262 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L262 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L263 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L263 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L264 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 33 | L264 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 33 | L265 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L265 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L266 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L266 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L267 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L267 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L268 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L268 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L269 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L269 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L270 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L270 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L271 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L271 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L272 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 33 | L272 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 33 | L273 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L273 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L274 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L274 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L275 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L275 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L276 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L276 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L277 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L277 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L278 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L278 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L279 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L279 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L280 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L280 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L281 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 33 | L281 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 33 | L282 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L282 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L283 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L283 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L284 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L284 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L285 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L285 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L286 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L286 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L287 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L287 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L288 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L288 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L289 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 33 | L289 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 33 | L290 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L290 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L291 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L291 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L292 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L292 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L293 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L293 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L294 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L294 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L295 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L295 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L296 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L296 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L297 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L297 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L298 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L298 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L299 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L299 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L300 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L300 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L301 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L301 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L302 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 33 | L302 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 33 | L303 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 33 | L303 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 34 | L309 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L309 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L310 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L310 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L311 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L311 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L312 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L312 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L313 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 34 | L313 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 34 | L314 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L314 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L315 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L315 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L316 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L316 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L317 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L317 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L318 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L318 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L319 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L319 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L320 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L320 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L321 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 34 | L321 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 34 | L322 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 34 | L322 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 34 | L324 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 53 | MNT | False | False | False |
| 34 | L324 | CREDIT | 5 | 404000 | Interest Income | 53 | MNT | False | False | False |
| 34 | L325 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 34 | L325 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 34 | L326 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 34 | L326 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 34 | L327 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 34 | L327 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 34 | L328 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | False | False |
| 34 | L328 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | False | False |
| 34 | L331 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 89 | MNT | False | True | False |
| 34 | L331 | CREDIT | 5 | 404000 | Interest Income | 89 | MNT | False | True | False |
| 35 | L333 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L333 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L334 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L334 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L335 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L335 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L336 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L336 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L337 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 35 | L337 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 35 | L338 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L338 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L339 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L339 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L340 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L340 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L341 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L341 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L342 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L342 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L343 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L343 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L344 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L344 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L345 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 35 | L345 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 35 | L346 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L346 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L347 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L347 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L348 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L348 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L349 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L349 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L350 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L350 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L351 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L351 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L352 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L352 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L353 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L353 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L354 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 35 | L354 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 35 | L355 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L355 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L356 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L356 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L357 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L357 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L358 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L358 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L359 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L359 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L360 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L360 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L361 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L361 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L362 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | False | False |
| 35 | L362 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | False | False |
| 35 | L363 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L363 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L364 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L364 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L365 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L365 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L366 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L366 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L367 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L367 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L368 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L368 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L369 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L369 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L370 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L370 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L371 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L371 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L372 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L372 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L373 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L373 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L374 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L374 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L375 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L375 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 35 | L376 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 35 | L376 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 36 | L382 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L382 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L383 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L383 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L384 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L384 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L385 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L385 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L386 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L386 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L387 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 36 | L387 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 36 | L388 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L388 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L389 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L389 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L390 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L390 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L391 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L391 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L392 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L392 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L393 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L393 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L394 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L394 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L395 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L395 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L396 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L396 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L397 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 69 | MNT | False | False | False |
| 36 | L397 | CREDIT | 5 | 404000 | Interest Income | 69 | MNT | False | False | False |
| 36 | L398 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L398 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 36 | L399 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 70 | MNT | False | False | False |
| 36 | L399 | CREDIT | 5 | 404000 | Interest Income | 70 | MNT | False | False | False |
| 37 | L404 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 61 | MNT | False | False | True |
| 37 | L404 | CREDIT | 5 | 404000 | Interest Income | 61 | MNT | False | False | True |
| 38 | L407 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 38 | L407 | CREDIT | 5 | 404000 | Interest Income | 41 | MNT | False | True | False |
| 38 | L407 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 38 | L407 | DEBIT | 5 | 404000 | Interest Income | 41 | MNT | False | True | False |
| 38 | L409 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 8 | MNT | False | True | False |
| 38 | L409 | CREDIT | 5 | 404000 | Interest Income | 8 | MNT | False | True | False |
| 39 | L412 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 40 | MNT | False | True | False |
| 39 | L412 | CREDIT | 5 | 404000 | Interest Income | 40 | MNT | False | True | False |
| 39 | L412 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 40 | MNT | False | True | False |
| 39 | L412 | DEBIT | 5 | 404000 | Interest Income | 40 | MNT | False | True | False |
| 39 | L414 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 8 | MNT | False | True | False |
| 39 | L414 | CREDIT | 5 | 404000 | Interest Income | 8 | MNT | False | True | False |
| 40 | L417 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 40 | L417 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 40 | L418 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 40 | L418 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 40 | L419 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | False | False |
| 40 | L419 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | False | False |
| 40 | L420 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L420 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L421 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | False |
| 40 | L421 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | False |
| 40 | L421 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | False |
| 40 | L421 | DEBIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | False |
| 40 | L422 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L422 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L422 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L422 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L423 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L423 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L423 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L423 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L424 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L424 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L424 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L424 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L425 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L425 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L425 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L425 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L426 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L426 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L426 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L426 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L427 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L427 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L427 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L427 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L428 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L428 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L428 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L428 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L429 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | False |
| 40 | L429 | CREDIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | False |
| 40 | L429 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | False |
| 40 | L429 | DEBIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | False |
| 40 | L430 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L430 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L430 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L430 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L431 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L431 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L431 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L431 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L432 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L432 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L432 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L432 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L433 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L433 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L433 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L433 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L434 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L434 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L434 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L434 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L435 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L435 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L435 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L435 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L436 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L436 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L436 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L436 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L437 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L437 | CREDIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 40 | L437 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2 | MNT | False | True | False |
| 40 | L437 | DEBIT | 5 | 404000 | Interest Income | 2 | MNT | False | True | False |
| 41 | L441 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 40 | MNT | False | False | False |
| 41 | L441 | CREDIT | 5 | 404000 | Interest Income | 40 | MNT | False | False | False |
| 45 | L450 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 316 | MNT | False | True | True |
| 45 | L450 | CREDIT | 5 | 404000 | Interest Income | 316 | MNT | False | True | True |
| 45 | L456 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 734 | MNT | False | True | True |
| 45 | L456 | CREDIT | 5 | 404000 | Interest Income | 734 | MNT | False | True | True |
| 46 | L459 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 321 | MNT | False | True | True |
| 46 | L459 | CREDIT | 5 | 404000 | Interest Income | 321 | MNT | False | True | True |
| 47 | L468 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | True |
| 47 | L468 | CREDIT | 5 | 404000 | Interest Income | 38 | MNT | False | False | True |
| 47 | L469 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 23 | MNT | False | True | True |
| 47 | L469 | CREDIT | 5 | 404000 | Interest Income | 23 | MNT | False | True | True |
| 48 | L473 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 48 | L473 | CREDIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 48 | L480 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 25 | MNT | False | True | False |
| 48 | L480 | CREDIT | 5 | 404000 | Interest Income | 25 | MNT | False | True | False |
| 49 | L483 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 49 | L483 | CREDIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 49 | L489 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 25 | MNT | False | True | False |
| 49 | L489 | CREDIT | 5 | 404000 | Interest Income | 25 | MNT | False | True | False |
| 50 | L493 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 50 | L493 | CREDIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 50 | L499 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 25 | MNT | False | True | False |
| 50 | L499 | CREDIT | 5 | 404000 | Interest Income | 25 | MNT | False | True | False |

## `loanTransactionType.accrualAdjustment` — Accrual Adjustment

loans: 13, 14, 15, 33, 35, 36, 45, 46; transactions: L60, L66, L72, L305, L378, L401, L452, L462, L465; legs: 18

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | L60 | DEBIT | 5 | 404000 | Interest Income | 47 | MNT | False | True | False |
| 13 | L60 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 47 | MNT | False | True | False |
| 14 | L66 | DEBIT | 5 | 404000 | Interest Income | 15 | MNT | False | True | False |
| 14 | L66 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 15 | MNT | False | True | False |
| 15 | L72 | DEBIT | 5 | 404000 | Interest Income | 56 | MNT | False | True | False |
| 15 | L72 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 56 | MNT | False | True | False |
| 33 | L305 | DEBIT | 5 | 404000 | Interest Income | 4 | MNT | False | True | False |
| 33 | L305 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 4 | MNT | False | True | False |
| 35 | L378 | DEBIT | 5 | 404000 | Interest Income | 4 | MNT | False | True | False |
| 35 | L378 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 4 | MNT | False | True | False |
| 36 | L401 | DEBIT | 5 | 404000 | Interest Income | 1258 | MNT | False | True | False |
| 36 | L401 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1258 | MNT | False | True | False |
| 45 | L452 | DEBIT | 5 | 404000 | Interest Income | 24 | MNT | False | True | True |
| 45 | L452 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 24 | MNT | False | True | True |
| 46 | L462 | DEBIT | 5 | 404000 | Interest Income | 9 | MNT | False | True | True |
| 46 | L462 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 9 | MNT | False | True | True |
| 46 | L465 | DEBIT | 5 | 404000 | Interest Income | 1 | MNT | False | True | True |
| 46 | L465 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | True |

## `loanTransactionType.chargeOff` — Charge-off

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46, 47, 48, 49, 50; transactions: L4, L8, L12, L16, L20, L24, L25, L30, L34, L38, L42, L43, L48, L54, L58, L64, L65, L70, L71, L78, L84, L88, L92, L96, L100, L102, L106, L110, L114, L118, L119, L124, L146, L167, L202, L234, L256, L258, L304, L306, L329, L330, L377, L380, L402, L405, L408, L410, L415, L439, L451, L453, L460, L463, L470, L474, L479, L484, L487, L494, L497; legs: 339

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L4 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 1 | L4 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 47 | MNT | False | True | False |
| 1 | L4 | DEBIT | 11 | 744037 | Credit Loss/Bad Debt-Fraud | 8357 | MNT | False | True | False |
| 1 | L4 | DEBIT | 16 | 404001 | Interest Income Charge Off | 47 | MNT | False | True | False |
| 2 | L8 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 2 | L8 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 47 | MNT | False | True | False |
| 2 | L8 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 2 | L8 | DEBIT | 16 | 404001 | Interest Income Charge Off | 47 | MNT | False | True | False |
| 3 | L12 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 3 | L12 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 47 | MNT | False | True | False |
| 3 | L12 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 3 | L12 | DEBIT | 16 | 404001 | Interest Income Charge Off | 47 | MNT | False | True | False |
| 4 | L16 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 4 | L16 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 849 | MNT | False | True | False |
| 4 | L16 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 4 | L16 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 4 | L16 | DEBIT | 12 | 404008 | Fee Charge Off | 800 | MNT | False | True | False |
| 5 | L20 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 5 | L20 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 5 | L20 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 5 | L20 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 5 | L20 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 6 | L24 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 6 | L24 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 6 | L24 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 6 | L24 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 6 | L24 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 6 | L24 | DEBIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 6 | L24 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 6 | L24 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 6 | L24 | CREDIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 6 | L24 | CREDIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 6 | L25 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 6 | L25 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1049 | MNT | False | True | False |
| 6 | L25 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 6 | L25 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 6 | L25 | DEBIT | 12 | 404008 | Fee Charge Off | 1000 | MNT | False | True | False |
| 7 | L30 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 7 | L30 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 549 | MNT | False | True | False |
| 7 | L30 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 7 | L30 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 7 | L30 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | MNT | False | True | False |
| 8 | L34 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 8 | L34 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 749 | MNT | False | True | False |
| 8 | L34 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 8 | L34 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 8 | L34 | DEBIT | 12 | 404008 | Fee Charge Off | 700 | MNT | False | True | False |
| 9 | L38 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 9 | L38 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 9 | L38 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 9 | L38 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 9 | L38 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 10 | L42 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 10 | L42 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 10 | L42 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 10 | L42 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 10 | L42 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 10 | L42 | DEBIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 10 | L42 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 10 | L42 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 10 | L42 | CREDIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 10 | L42 | CREDIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 10 | L43 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 10 | L43 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 524 | MNT | False | True | False |
| 10 | L43 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 10 | L43 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 10 | L43 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | MNT | False | True | False |
| 11 | L48 | CREDIT | 6 | 112601 | Loans Receivable | 8299 | MNT | False | True | False |
| 11 | L48 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 100 | MNT | False | True | False |
| 11 | L48 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8299 | MNT | False | True | False |
| 11 | L48 | DEBIT | 16 | 404001 | Interest Income Charge Off | 100 | MNT | False | True | False |
| 12 | L54 | CREDIT | 6 | 112601 | Loans Receivable | 6680 | MNT | False | True | False |
| 12 | L54 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 18 | MNT | False | True | False |
| 12 | L54 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 6680 | MNT | False | True | False |
| 12 | L54 | DEBIT | 16 | 404001 | Interest Income Charge Off | 18 | MNT | False | True | False |
| 13 | L58 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 13 | L58 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 96 | MNT | False | True | False |
| 13 | L58 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 13 | L58 | DEBIT | 16 | 404001 | Interest Income Charge Off | 96 | MNT | False | True | False |
| 13 | L58 | DEBIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 13 | L58 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 96 | MNT | False | True | False |
| 13 | L58 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 13 | L58 | CREDIT | 16 | 404001 | Interest Income Charge Off | 96 | MNT | False | True | False |
| 14 | L64 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 14 | L64 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 96 | MNT | False | True | False |
| 14 | L64 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 14 | L64 | DEBIT | 16 | 404001 | Interest Income Charge Off | 96 | MNT | False | True | False |
| 14 | L64 | DEBIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 14 | L64 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 96 | MNT | False | True | False |
| 14 | L64 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 14 | L64 | CREDIT | 16 | 404001 | Interest Income Charge Off | 96 | MNT | False | True | False |
| 14 | L65 | CREDIT | 6 | 112601 | Loans Receivable | 5705 | MNT | False | True | False |
| 14 | L65 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 32 | MNT | False | True | False |
| 14 | L65 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 5705 | MNT | False | True | False |
| 14 | L65 | DEBIT | 16 | 404001 | Interest Income Charge Off | 32 | MNT | False | True | False |
| 15 | L70 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 15 | L70 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 172 | MNT | False | True | False |
| 15 | L70 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 15 | L70 | DEBIT | 16 | 404001 | Interest Income Charge Off | 172 | MNT | False | True | False |
| 15 | L70 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 15 | L70 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 172 | MNT | False | True | False |
| 15 | L70 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 15 | L70 | CREDIT | 16 | 404001 | Interest Income Charge Off | 172 | MNT | False | True | False |
| 15 | L71 | CREDIT | 6 | 112601 | Loans Receivable | 3116 | MNT | False | True | False |
| 15 | L71 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 3116 | MNT | False | True | False |
| 16 | L78 | CREDIT | 6 | 112601 | Loans Receivable | 8342 | MNT | False | True | False |
| 16 | L78 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | True | False |
| 16 | L78 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8342 | MNT | False | True | False |
| 16 | L78 | DEBIT | 16 | 404001 | Interest Income Charge Off | 58 | MNT | False | True | False |
| 17 | L84 | CREDIT | 6 | 112601 | Loans Receivable | 6700 | MNT | False | True | False |
| 17 | L84 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 6700 | MNT | False | True | False |
| 18 | L88 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 18 | L88 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 549 | MNT | False | True | False |
| 18 | L88 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 18 | L88 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 18 | L88 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | MNT | False | True | False |
| 19 | L92 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 19 | L92 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 849 | MNT | False | True | False |
| 19 | L92 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 19 | L92 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 19 | L92 | DEBIT | 12 | 404008 | Fee Charge Off | 800 | MNT | False | True | False |
| 20 | L96 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 20 | L96 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 20 | L96 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 20 | L96 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 20 | L96 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 21 | L100 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 21 | L100 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 21 | L100 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 21 | L100 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 21 | L100 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 21 | L100 | DEBIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 21 | L100 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1549 | MNT | False | True | False |
| 21 | L100 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 21 | L100 | CREDIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 21 | L100 | CREDIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 21 | L102 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 21 | L102 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1049 | MNT | False | True | False |
| 21 | L102 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 21 | L102 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 21 | L102 | DEBIT | 12 | 404008 | Fee Charge Off | 1000 | MNT | False | True | False |
| 22 | L106 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 22 | L106 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 549 | MNT | False | True | False |
| 22 | L106 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 22 | L106 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 22 | L106 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | MNT | False | True | False |
| 23 | L110 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 23 | L110 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 749 | MNT | False | True | False |
| 23 | L110 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 23 | L110 | DEBIT | 16 | 404001 | Interest Income Charge Off | 49 | MNT | False | True | False |
| 23 | L110 | DEBIT | 12 | 404008 | Fee Charge Off | 700 | MNT | False | True | False |
| 24 | L114 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 24 | L114 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 24 | L114 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 24 | L114 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 24 | L114 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 25 | L118 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 25 | L118 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 25 | L118 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 25 | L118 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 25 | L118 | DEBIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 25 | L118 | DEBIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 25 | L118 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1524 | MNT | False | True | False |
| 25 | L118 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 25 | L118 | CREDIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 25 | L118 | CREDIT | 12 | 404008 | Fee Charge Off | 1500 | MNT | False | True | False |
| 25 | L119 | CREDIT | 6 | 112601 | Loans Receivable | 8358 | MNT | False | True | False |
| 25 | L119 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 524 | MNT | False | True | False |
| 25 | L119 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8358 | MNT | False | True | False |
| 25 | L119 | DEBIT | 16 | 404001 | Interest Income Charge Off | 24 | MNT | False | True | False |
| 25 | L119 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | MNT | False | True | False |
| 26 | L124 | CREDIT | 6 | 112601 | Loans Receivable | 83254 | MNT | False | True | False |
| 26 | L124 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 251 | MNT | False | True | False |
| 26 | L124 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 83254 | MNT | False | True | False |
| 26 | L124 | DEBIT | 16 | 404001 | Interest Income Charge Off | 251 | MNT | False | True | False |
| 27 | L146 | CREDIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 27 | L146 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 4155 | MNT | False | True | False |
| 27 | L146 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 27 | L146 | DEBIT | 16 | 404001 | Interest Income Charge Off | 4155 | MNT | False | True | False |
| 28 | L167 | CREDIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 28 | L167 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 4155 | MNT | False | True | False |
| 28 | L167 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 28 | L167 | DEBIT | 16 | 404001 | Interest Income Charge Off | 4155 | MNT | False | True | False |
| 30 | L202 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 30 | L202 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 56 | MNT | False | True | False |
| 30 | L202 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 30 | L202 | DEBIT | 16 | 404001 | Interest Income Charge Off | 56 | MNT | False | True | False |
| 31 | L234 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 31 | L234 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 56 | MNT | False | True | False |
| 31 | L234 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 31 | L234 | DEBIT | 16 | 404001 | Interest Income Charge Off | 56 | MNT | False | True | False |
| 32 | L256 | CREDIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 32 | L256 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 261 | MNT | False | True | False |
| 32 | L256 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 32 | L256 | DEBIT | 16 | 404001 | Interest Income Charge Off | 261 | MNT | False | True | False |
| 32 | L256 | DEBIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 32 | L256 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 261 | MNT | False | True | False |
| 32 | L256 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 32 | L256 | CREDIT | 16 | 404001 | Interest Income Charge Off | 261 | MNT | False | True | False |
| 32 | L258 | CREDIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | True | False |
| 32 | L258 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1328 | MNT | False | True | False |
| 32 | L258 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 100000 | MNT | False | True | False |
| 32 | L258 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1328 | MNT | False | True | False |
| 33 | L304 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 33 | L304 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 84 | MNT | False | True | False |
| 33 | L304 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 33 | L304 | DEBIT | 16 | 404001 | Interest Income Charge Off | 84 | MNT | False | True | False |
| 33 | L304 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 33 | L304 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 84 | MNT | False | True | False |
| 33 | L304 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 33 | L304 | CREDIT | 16 | 404001 | Interest Income Charge Off | 84 | MNT | False | True | False |
| 33 | L306 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 33 | L306 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 22 | MNT | False | True | False |
| 33 | L306 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 33 | L306 | DEBIT | 16 | 404001 | Interest Income Charge Off | 22 | MNT | False | True | False |
| 34 | L329 | CREDIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 34 | L329 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 261 | MNT | False | True | False |
| 34 | L329 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 34 | L329 | DEBIT | 16 | 404001 | Interest Income Charge Off | 261 | MNT | False | True | False |
| 34 | L329 | DEBIT | 6 | 112601 | Loans Receivable | 74609 | MNT | False | True | False |
| 34 | L329 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 261 | MNT | False | True | False |
| 34 | L329 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 74609 | MNT | False | True | False |
| 34 | L329 | CREDIT | 16 | 404001 | Interest Income Charge Off | 261 | MNT | False | True | False |
| 34 | L330 | CREDIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | True | False |
| 34 | L330 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1328 | MNT | False | True | False |
| 34 | L330 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 100000 | MNT | False | True | False |
| 34 | L330 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1328 | MNT | False | True | False |
| 35 | L377 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 35 | L377 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 84 | MNT | False | True | False |
| 35 | L377 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 35 | L377 | DEBIT | 16 | 404001 | Interest Income Charge Off | 84 | MNT | False | True | False |
| 35 | L377 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 35 | L377 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 84 | MNT | False | True | False |
| 35 | L377 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 35 | L377 | CREDIT | 16 | 404001 | Interest Income Charge Off | 84 | MNT | False | True | False |
| 35 | L380 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | True | False |
| 35 | L380 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 22 | MNT | False | True | False |
| 35 | L380 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 8357 | MNT | False | True | False |
| 35 | L380 | DEBIT | 16 | 404001 | Interest Income Charge Off | 22 | MNT | False | True | False |
| 36 | L402 | CREDIT | 6 | 112601 | Loans Receivable | 75767 | MNT | False | True | False |
| 36 | L402 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 3304 | MNT | False | True | False |
| 36 | L402 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 75767 | MNT | False | True | False |
| 36 | L402 | DEBIT | 16 | 404001 | Interest Income Charge Off | 3304 | MNT | False | True | False |
| 37 | L405 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | True |
| 37 | L405 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 61 | MNT | False | False | True |
| 37 | L405 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | False | True |
| 37 | L405 | DEBIT | 16 | 404001 | Interest Income Charge Off | 61 | MNT | False | False | True |
| 37 | L405 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | True |
| 37 | L405 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 61 | MNT | False | False | True |
| 37 | L405 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | False | True |
| 37 | L405 | CREDIT | 16 | 404001 | Interest Income Charge Off | 61 | MNT | False | False | True |
| 38 | L408 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 38 | L408 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 38 | L408 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 38 | L408 | DEBIT | 16 | 404001 | Interest Income Charge Off | 41 | MNT | False | True | False |
| 38 | L408 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 38 | L408 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 38 | L408 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 38 | L408 | CREDIT | 16 | 404001 | Interest Income Charge Off | 41 | MNT | False | True | False |
| 38 | L410 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 38 | L410 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 8 | MNT | False | True | False |
| 38 | L410 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 38 | L410 | DEBIT | 16 | 404001 | Interest Income Charge Off | 8 | MNT | False | True | False |
| 39 | L415 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 39 | L415 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 8 | MNT | False | True | False |
| 39 | L415 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 39 | L415 | DEBIT | 16 | 404001 | Interest Income Charge Off | 8 | MNT | False | True | False |
| 40 | L439 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | False |
| 40 | L439 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 8 | MNT | False | True | False |
| 40 | L439 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | False |
| 40 | L439 | DEBIT | 16 | 404001 | Interest Income Charge Off | 8 | MNT | False | True | False |
| 45 | L451 | CREDIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | True | True |
| 45 | L451 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 316 | MNT | False | True | True |
| 45 | L451 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 50000 | MNT | False | True | True |
| 45 | L451 | DEBIT | 16 | 404001 | Interest Income Charge Off | 316 | MNT | False | True | True |
| 45 | L451 | DEBIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | True | True |
| 45 | L451 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 316 | MNT | False | True | True |
| 45 | L451 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 50000 | MNT | False | True | True |
| 45 | L451 | CREDIT | 16 | 404001 | Interest Income Charge Off | 316 | MNT | False | True | True |
| 45 | L453 | CREDIT | 6 | 112601 | Loans Receivable | 977 | MNT | False | True | True |
| 45 | L453 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 977 | MNT | False | True | True |
| 45 | L453 | DEBIT | 6 | 112601 | Loans Receivable | 977 | MNT | False | True | True |
| 45 | L453 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 977 | MNT | False | True | True |
| 46 | L460 | CREDIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | True | True |
| 46 | L460 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 321 | MNT | False | True | True |
| 46 | L460 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 50000 | MNT | False | True | True |
| 46 | L460 | DEBIT | 16 | 404001 | Interest Income Charge Off | 321 | MNT | False | True | True |
| 46 | L460 | DEBIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | True | True |
| 46 | L460 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 321 | MNT | False | True | True |
| 46 | L460 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 50000 | MNT | False | True | True |
| 46 | L460 | CREDIT | 16 | 404001 | Interest Income Charge Off | 321 | MNT | False | True | True |
| 46 | L463 | CREDIT | 6 | 112601 | Loans Receivable | 311 | MNT | False | True | True |
| 46 | L463 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | True |
| 46 | L463 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 311 | MNT | False | True | True |
| 46 | L463 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1 | MNT | False | True | True |
| 46 | L463 | DEBIT | 6 | 112601 | Loans Receivable | 311 | MNT | False | True | True |
| 46 | L463 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1 | MNT | False | True | True |
| 46 | L463 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 311 | MNT | False | True | True |
| 46 | L463 | CREDIT | 16 | 404001 | Interest Income Charge Off | 1 | MNT | False | True | True |
| 47 | L470 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | True | True |
| 47 | L470 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 61 | MNT | False | True | True |
| 47 | L470 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 10000 | MNT | False | True | True |
| 47 | L470 | DEBIT | 16 | 404001 | Interest Income Charge Off | 61 | MNT | False | True | True |
| 48 | L474 | CREDIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 48 | L474 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1849 | MNT | False | True | False |
| 48 | L474 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 48 | L474 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1849 | MNT | False | True | False |
| 48 | L474 | DEBIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 48 | L474 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 1849 | MNT | False | True | False |
| 48 | L474 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 48 | L474 | CREDIT | 16 | 404001 | Interest Income Charge Off | 1849 | MNT | False | True | False |
| 48 | L479 | CREDIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | True | False |
| 48 | L479 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 1875 | MNT | False | True | False |
| 48 | L479 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 90000 | MNT | False | True | False |
| 48 | L479 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1875 | MNT | False | True | False |
| 49 | L484 | CREDIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 49 | L484 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 49 | L484 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 49 | L484 | DEBIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 49 | L484 | DEBIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 49 | L484 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 49 | L484 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 49 | L484 | CREDIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 49 | L487 | CREDIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | True | False |
| 49 | L487 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 757 | MNT | False | True | False |
| 49 | L487 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 90000 | MNT | False | True | False |
| 49 | L487 | DEBIT | 16 | 404001 | Interest Income Charge Off | 757 | MNT | False | True | False |
| 50 | L494 | CREDIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 50 | L494 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 50 | L494 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 50 | L494 | DEBIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 50 | L494 | DEBIT | 6 | 112601 | Loans Receivable | 80000 | MNT | False | True | False |
| 50 | L494 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 732 | MNT | False | True | False |
| 50 | L494 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 50 | L494 | CREDIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 50 | L497 | CREDIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | True | False |
| 50 | L497 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 757 | MNT | False | True | False |
| 50 | L497 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 90000 | MNT | False | True | False |
| 50 | L497 | DEBIT | 16 | 404001 | Interest Income Charge Off | 757 | MNT | False | True | False |

## `loanTransactionType.disbursement` — Disbursement

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50; transactions: L1, L5, L9, L13, L17, L21, L27, L31, L35, L39, L45, L49, L55, L61, L68, L74, L79, L85, L89, L93, L97, L103, L107, L111, L115, L121, L125, L147, L171, L203, L235, L259, L308, L332, L381, L403, L406, L411, L416, L440, L443, L445, L447, L449, L458, L467, L471, L481, L491; legs: 98

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L1 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 1 | L1 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 2 | L5 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 2 | L5 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 3 | L9 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 3 | L9 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 4 | L13 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 4 | L13 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 5 | L17 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 5 | L17 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 6 | L21 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 6 | L21 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 7 | L27 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 7 | L27 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 8 | L31 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 8 | L31 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 9 | L35 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 9 | L35 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 10 | L39 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 10 | L39 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 11 | L45 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 11 | L45 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 12 | L49 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 12 | L49 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 13 | L55 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 13 | L55 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 14 | L61 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 14 | L61 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 15 | L68 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 15 | L68 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 16 | L74 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 16 | L74 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 17 | L79 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 17 | L79 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 18 | L85 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 18 | L85 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 19 | L89 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 19 | L89 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 20 | L93 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 20 | L93 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 21 | L97 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 21 | L97 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 22 | L103 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 22 | L103 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 23 | L107 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 23 | L107 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 24 | L111 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 24 | L111 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 25 | L115 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 25 | L115 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 26 | L121 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 26 | L121 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 27 | L125 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 27 | L125 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 28 | L147 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 28 | L147 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 30 | L171 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 30 | L171 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 31 | L203 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 31 | L203 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 32 | L235 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 32 | L235 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 33 | L259 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 33 | L259 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 34 | L308 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 34 | L308 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 35 | L332 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 35 | L332 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 36 | L381 | DEBIT | 6 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 36 | L381 | CREDIT | 7 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 37 | L403 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | True |
| 37 | L403 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | True |
| 38 | L406 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 38 | L406 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 39 | L411 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 39 | L411 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 40 | L416 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 40 | L416 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 41 | L440 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 41 | L440 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 42 | L443 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 42 | L443 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 43 | L445 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 43 | L445 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 44 | L447 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 44 | L447 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 45 | L449 | DEBIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | False | True |
| 45 | L449 | CREDIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 46 | L458 | DEBIT | 6 | 112601 | Loans Receivable | 50000 | MNT | False | False | True |
| 46 | L458 | CREDIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 47 | L467 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | True |
| 47 | L467 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | True |
| 48 | L471 | DEBIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | False | False |
| 48 | L471 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | False | False |
| 49 | L481 | DEBIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | False | False |
| 49 | L481 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | False | False |
| 50 | L491 | DEBIT | 6 | 112601 | Loans Receivable | 90000 | MNT | False | False | False |
| 50 | L491 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | False | False |

## `loanTransactionType.goodwillCredit` — Goodwill Credit

loans: 42, 45, 46; transactions: L444, L457, L466; legs: 6

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | L444 | CREDIT | 6 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 42 | L444 | DEBIT | 20 | 744003 | Goodwill Expense Account | 1000 | MNT | False | False | False |
| 45 | L457 | CREDIT | 13 | l1 | Overpayment account | 50000 | MNT | False | False | True |
| 45 | L457 | DEBIT | 20 | 744003 | Goodwill Expense Account | 50000 | MNT | False | False | True |
| 46 | L466 | CREDIT | 13 | l1 | Overpayment account | 50000 | MNT | False | False | True |
| 46 | L466 | DEBIT | 20 | 744003 | Goodwill Expense Account | 50000 | MNT | False | False | True |

## `loanTransactionType.interestRefund` — Interest Refund

loans: 48, 49, 50; transactions: L476, L478, L486, L490, L496, L500; legs: 18

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | L476 | CREDIT | 13 | l1 | Overpayment account | 1849 | MNT | False | True | False |
| 48 | L476 | DEBIT | 5 | 404000 | Interest Income | 1849 | MNT | False | True | False |
| 48 | L476 | DEBIT | 13 | l1 | Overpayment account | 1849 | MNT | False | True | False |
| 48 | L476 | CREDIT | 5 | 404000 | Interest Income | 1849 | MNT | False | True | False |
| 48 | L478 | CREDIT | 16 | 404001 | Interest Income Charge Off | 1875 | MNT | False | True | False |
| 48 | L478 | DEBIT | 5 | 404000 | Interest Income | 1875 | MNT | False | True | False |
| 49 | L486 | CREDIT | 13 | l1 | Overpayment account | 732 | MNT | False | True | False |
| 49 | L486 | DEBIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 49 | L486 | DEBIT | 13 | l1 | Overpayment account | 732 | MNT | False | True | False |
| 49 | L486 | CREDIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 49 | L490 | CREDIT | 16 | 404001 | Interest Income Charge Off | 757 | MNT | False | True | False |
| 49 | L490 | DEBIT | 5 | 404000 | Interest Income | 757 | MNT | False | True | False |
| 50 | L496 | CREDIT | 13 | l1 | Overpayment account | 732 | MNT | False | True | False |
| 50 | L496 | DEBIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 50 | L496 | DEBIT | 13 | l1 | Overpayment account | 732 | MNT | False | True | False |
| 50 | L496 | CREDIT | 5 | 404000 | Interest Income | 732 | MNT | False | True | False |
| 50 | L500 | CREDIT | 16 | 404001 | Interest Income Charge Off | 757 | MNT | False | True | False |
| 50 | L500 | DEBIT | 5 | 404000 | Interest Income | 757 | MNT | False | True | False |

## `loanTransactionType.merchantIssuedRefund` — Merchant Issued Refund

loans: 45, 46, 48, 49, 50; transactions: L455, L464, L475, L477, L485, L488, L495, L498; legs: 39

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 45 | L455 | CREDIT | 6 | 112601 | Loans Receivable | 977 | MNT | False | False | True |
| 45 | L455 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | True |
| 45 | L455 | CREDIT | 13 | l1 | Overpayment account | 48974 | MNT | False | False | True |
| 45 | L455 | DEBIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 46 | L464 | CREDIT | 6 | 112601 | Loans Receivable | 311 | MNT | False | False | True |
| 46 | L464 | CREDIT | 13 | l1 | Overpayment account | 49689 | MNT | False | False | True |
| 46 | L464 | DEBIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 48 | L475 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 48 | L475 | CREDIT | 16 | 404001 | Interest Income Charge Off | 1849 | MNT | False | True | False |
| 48 | L475 | CREDIT | 13 | l1 | Overpayment account | 8151 | MNT | False | True | False |
| 48 | L475 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 48 | L475 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 48 | L475 | DEBIT | 16 | 404001 | Interest Income Charge Off | 1849 | MNT | False | True | False |
| 48 | L475 | DEBIT | 13 | l1 | Overpayment account | 8151 | MNT | False | True | False |
| 48 | L475 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 48 | L477 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 88310 | MNT | False | True | False |
| 48 | L477 | CREDIT | 16 | 404001 | Interest Income Charge Off | 1690 | MNT | False | True | False |
| 48 | L477 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 49 | L485 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 49 | L485 | CREDIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 49 | L485 | CREDIT | 13 | l1 | Overpayment account | 9268 | MNT | False | True | False |
| 49 | L485 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 49 | L485 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 49 | L485 | DEBIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 49 | L485 | DEBIT | 13 | l1 | Overpayment account | 9268 | MNT | False | True | False |
| 49 | L485 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 49 | L488 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 89243 | MNT | False | True | False |
| 49 | L488 | CREDIT | 16 | 404001 | Interest Income Charge Off | 757 | MNT | False | True | False |
| 49 | L488 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 50 | L495 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 50 | L495 | CREDIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 50 | L495 | CREDIT | 13 | l1 | Overpayment account | 9268 | MNT | False | True | False |
| 50 | L495 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 50 | L495 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 80000 | MNT | False | True | False |
| 50 | L495 | DEBIT | 16 | 404001 | Interest Income Charge Off | 732 | MNT | False | True | False |
| 50 | L495 | DEBIT | 13 | l1 | Overpayment account | 9268 | MNT | False | True | False |
| 50 | L495 | CREDIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |
| 50 | L498 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 90000 | MNT | False | True | False |
| 50 | L498 | DEBIT | 7 | 145023 | Suspense/Clearing account | 90000 | MNT | False | True | False |

## `loanTransactionType.repayment` — Repayment

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 32, 33, 34, 35, 36, 39, 40, 41, 45, 46, 48, 49, 50; transactions: L2, L6, L10, L14, L18, L22, L28, L32, L36, L40, L46, L50, L51, L52, L56, L59, L62, L67, L73, L75, L80, L81, L86, L90, L94, L98, L104, L108, L112, L116, L122, L126, L148, L249, L307, L323, L379, L400, L413, L438, L442, L454, L461, L472, L482, L492; legs: 153

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L2 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 1 | L2 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 1 | L2 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 2 | L6 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 2 | L6 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 2 | L6 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 3 | L10 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 3 | L10 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 3 | L10 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 4 | L14 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 4 | L14 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 4 | L14 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 5 | L18 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 5 | L18 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 5 | L18 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 6 | L22 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 6 | L22 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 6 | L22 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 7 | L28 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 7 | L28 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 7 | L28 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 8 | L32 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 8 | L32 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 8 | L32 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 9 | L36 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 9 | L36 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 9 | L36 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 10 | L40 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 10 | L40 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 10 | L40 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 11 | L46 | CREDIT | 6 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 11 | L46 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 12 | L50 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 12 | L50 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 12 | L50 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 12 | L51 | CREDIT | 6 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 12 | L51 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 12 | L51 | DEBIT | 6 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 12 | L51 | CREDIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 12 | L52 | CREDIT | 6 | 112601 | Loans Receivable | 1677 | MNT | False | False | False |
| 12 | L52 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 24 | MNT | False | False | False |
| 12 | L52 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 13 | L56 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 13 | L56 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 13 | L56 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 13 | L59 | CREDIT | 6 | 112601 | Loans Receivable | 8357 | MNT | False | False | False |
| 13 | L59 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 13 | L59 | DEBIT | 7 | 145023 | Suspense/Clearing account | 8406 | MNT | False | False | False |
| 14 | L62 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 14 | L62 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 14 | L62 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 14 | L67 | CREDIT | 6 | 112601 | Loans Receivable | 2652 | MNT | False | False | False |
| 14 | L67 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 14 | L67 | DEBIT | 7 | 145023 | Suspense/Clearing account | 2701 | MNT | False | False | False |
| 15 | L73 | CREDIT | 6 | 112601 | Loans Receivable | 6884 | MNT | False | False | False |
| 15 | L73 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 116 | MNT | False | False | False |
| 15 | L73 | DEBIT | 7 | 145023 | Suspense/Clearing account | 7000 | MNT | False | False | False |
| 16 | L75 | CREDIT | 6 | 112601 | Loans Receivable | 1695 | MNT | False | False | False |
| 16 | L75 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 16 | L75 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1705 | MNT | False | False | False |
| 17 | L80 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 17 | L80 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 17 | L80 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 17 | L81 | CREDIT | 6 | 112601 | Loans Receivable | 1695 | MNT | False | False | False |
| 17 | L81 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 17 | L81 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1705 | MNT | False | False | False |
| 18 | L86 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 18 | L86 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 18 | L86 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 19 | L90 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 19 | L90 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 19 | L90 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 20 | L94 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 20 | L94 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 20 | L94 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 21 | L98 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 21 | L98 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 21 | L98 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 22 | L104 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 22 | L104 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 22 | L104 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 23 | L108 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 23 | L108 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 23 | L108 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 24 | L112 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 24 | L112 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 24 | L112 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 25 | L116 | CREDIT | 6 | 112601 | Loans Receivable | 1642 | MNT | False | False | False |
| 25 | L116 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 25 | L116 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 26 | L122 | CREDIT | 6 | 112601 | Loans Receivable | 16746 | MNT | False | False | False |
| 26 | L122 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 263 | MNT | False | False | False |
| 26 | L122 | DEBIT | 7 | 145023 | Suspense/Clearing account | 17009 | MNT | False | False | False |
| 27 | L126 | CREDIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 27 | L126 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 27 | L126 | DEBIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 28 | L148 | CREDIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 28 | L148 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 28 | L148 | DEBIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 32 | L249 | CREDIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 32 | L249 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 32 | L249 | DEBIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 32 | L249 | DEBIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 32 | L249 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 32 | L249 | CREDIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 33 | L307 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 33 | L307 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 33 | L307 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 34 | L323 | CREDIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 34 | L323 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 34 | L323 | DEBIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 34 | L323 | DEBIT | 6 | 112601 | Loans Receivable | 25391 | MNT | False | False | False |
| 34 | L323 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 978 | MNT | False | False | False |
| 34 | L323 | CREDIT | 7 | 145023 | Suspense/Clearing account | 26369 | MNT | False | False | False |
| 35 | L379 | CREDIT | 6 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 35 | L379 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 35 | L379 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L400 | CREDIT | 6 | 112601 | Loans Receivable | 24233 | MNT | False | False | False |
| 36 | L400 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 2167 | MNT | False | False | False |
| 36 | L400 | DEBIT | 7 | 145023 | Suspense/Clearing account | 26400 | MNT | False | False | False |
| 39 | L413 | CREDIT | 6 | 112601 | Loans Receivable | 1660 | MNT | False | True | False |
| 39 | L413 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 39 | L413 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | True | False |
| 39 | L413 | DEBIT | 6 | 112601 | Loans Receivable | 1660 | MNT | False | True | False |
| 39 | L413 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 39 | L413 | CREDIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | True | False |
| 40 | L438 | CREDIT | 6 | 112601 | Loans Receivable | 1660 | MNT | False | True | False |
| 40 | L438 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 40 | L438 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | True | False |
| 40 | L438 | DEBIT | 6 | 112601 | Loans Receivable | 1660 | MNT | False | True | False |
| 40 | L438 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | True | False |
| 40 | L438 | CREDIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | True | False |
| 41 | L442 | CREDIT | 6 | 112601 | Loans Receivable | 1660 | MNT | False | False | False |
| 41 | L442 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 41 | MNT | False | False | False |
| 41 | L442 | DEBIT | 7 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L454 | CREDIT | 6 | 112601 | Loans Receivable | 49023 | MNT | False | False | True |
| 45 | L454 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 977 | MNT | False | False | True |
| 45 | L454 | DEBIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 46 | L461 | CREDIT | 6 | 112601 | Loans Receivable | 49689 | MNT | False | False | True |
| 46 | L461 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 311 | MNT | False | False | True |
| 46 | L461 | DEBIT | 7 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | True |
| 48 | L472 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 48 | L472 | DEBIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 48 | L472 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 48 | L472 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 49 | L482 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 49 | L482 | DEBIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 49 | L482 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 49 | L482 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 50 | L492 | CREDIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 50 | L492 | DEBIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 50 | L492 | DEBIT | 6 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 50 | L492 | CREDIT | 7 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |

## `None`

loans: 27, 28; transactions: L143, L144, L145, L165, L166; legs: 20

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 27 | L143 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L143 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 27 | L143 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L143 | DEBIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 27 | L144 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L144 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 27 | L144 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L144 | DEBIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 27 | L145 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L145 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 27 | L145 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 27 | L145 | DEBIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 28 | L165 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 28 | L165 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 28 | L165 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 28 | L165 | DEBIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 28 | L166 | DEBIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 28 | L166 | CREDIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |
| 28 | L166 | CREDIT | 3 | 112603 | Interest/Fee Receivable | 52 | MNT | False | True | False |
| 28 | L166 | DEBIT | 5 | 404000 | Interest Income | 52 | MNT | False | True | False |

## Type x charged-off -- refund / goodwill arms (OH-TIERD13-CI step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the leg transaction date.

| type | present | legs | loans | legs on charged-off loan | loans on charged-off |
| --- | --- | ---: | --- | ---: | --- |
| `loanTransactionType.merchantIssuedRefund` | True | 39 | 45, 46, 48, 49, 50 | 32 | 48, 49, 50 |
| `loanTransactionType.payoutRefund` | False | 0 | - | 0 | - |
| `loanTransactionType.goodwillCredit` | True | 6 | 42, 45, 46 | 0 | - |

`payoutRefund`: **no legs observed** in this replay (the type is present in
the processor but no Part-3 scenario issues one).

### Legs on a CHARGED-OFF loan -- required listing

| type | loan | tx | entry | account id | account name | amount (minor) | fraud | currency |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | CREDIT | 16 | Interest Income Charge Off | 1849 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | CREDIT | 13 | Overpayment account | 8151 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | DEBIT | 16 | Interest Income Charge Off | 1849 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | DEBIT | 13 | Overpayment account | 8151 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L475 | CREDIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L477 | CREDIT | 18 | Credit Loss/Bad Debt | 88310 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L477 | CREDIT | 16 | Interest Income Charge Off | 1690 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 48 | L477 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | CREDIT | 16 | Interest Income Charge Off | 732 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | CREDIT | 13 | Overpayment account | 9268 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | DEBIT | 16 | Interest Income Charge Off | 732 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | DEBIT | 13 | Overpayment account | 9268 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L485 | CREDIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L488 | CREDIT | 18 | Credit Loss/Bad Debt | 89243 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L488 | CREDIT | 16 | Interest Income Charge Off | 757 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 49 | L488 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | CREDIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | CREDIT | 16 | Interest Income Charge Off | 732 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | CREDIT | 13 | Overpayment account | 9268 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | DEBIT | 18 | Credit Loss/Bad Debt | 80000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | DEBIT | 16 | Interest Income Charge Off | 732 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | DEBIT | 13 | Overpayment account | 9268 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L495 | CREDIT | 7 | Suspense/Clearing account | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L498 | CREDIT | 18 | Credit Loss/Bad Debt | 90000 | False | MNT |
| `loanTransactionType.merchantIssuedRefund` | 50 | L498 | DEBIT | 7 | Suspense/Clearing account | 90000 | False | MNT |

### Per-loan charge-off / fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
| --- | --- | --- | --- |
| 1 | MNT | False | L4@2024-02-29 |
| 2 | MNT | False | L8@2024-02-29 |
| 3 | MNT | False | L12@2024-02-29 |
| 4 | MNT | False | L16@2024-03-01 |
| 5 | MNT | False | L20@2024-03-01 |
| 6 | MNT | False | L24@2024-03-01, L25@2024-03-01 |
| 7 | MNT | False | L30@2024-03-01 |
| 8 | MNT | False | L34@2024-03-01 |
| 9 | MNT | False | L38@2024-02-15 |
| 10 | MNT | False | L42@2024-02-15, L43@2024-02-15 |
| 11 | MNT | False | L48@2024-02-29 |
| 12 | MNT | False | L54@2024-02-29 |
| 13 | MNT | False | L58@2024-03-31 |
| 14 | MNT | False | L64@2024-03-31, L65@2024-03-31 |
| 15 | MNT | False | L70@2024-03-31, L71@2024-03-31 |
| 16 | MNT | False | L78@2024-02-29 |
| 17 | MNT | False | L84@2024-02-29 |
| 18 | MNT | False | L88@2024-03-01 |
| 19 | MNT | False | L92@2024-03-01 |
| 20 | MNT | False | L96@2024-03-01 |
| 21 | MNT | False | L100@2024-03-01, L102@2024-03-01 |
| 22 | MNT | False | L106@2024-03-01 |
| 23 | MNT | False | L110@2024-03-01 |
| 24 | MNT | False | L114@2024-02-15 |
| 25 | MNT | False | L118@2024-02-15, L119@2024-02-15 |
| 26 | MNT | False | L124@2023-01-31 |
| 27 | MNT | False | L146@2024-01-17 |
| 28 | MNT | False | L167@2024-01-17 |
| 29 | MNT | False | L170@2024-03-01 |
| 30 | MNT | False | L202@2024-01-31 |
| 31 | MNT | False | L234@2024-01-31 |
| 32 | MNT | False | L256@2024-01-20, L258@2024-01-20 |
| 33 | MNT | False | L304@2024-02-14, L306@2024-02-14 |
| 34 | MNT | False | L329@2024-01-20, L330@2024-01-20 |
| 35 | MNT | False | L377@2024-02-14, L380@2024-02-14 |
| 36 | MNT | False | L402@2024-01-20 |
| 37 | MNT | True | - |
| 38 | MNT | False | L410@2024-01-05 |
| 39 | MNT | False | L415@2024-01-05 |
| 40 | MNT | False | L439@2024-01-05 |
| 41 | MNT | False | - |
| 42 | MNT | False | - |
| 43 | MNT | False | - |
| 44 | MNT | False | - |
| 45 | MNT | True | L451@2025-04-14, L453@2025-04-14 |
| 46 | MNT | True | L460@2025-04-14, L463@2025-04-14 |
| 47 | MNT | True | L470@2024-02-03 |
| 48 | MNT | False | L474@2025-04-14, L479@2025-04-14 |
| 49 | MNT | False | L484@2025-04-14, L487@2025-04-14 |
| 50 | MNT | False | L494@2025-04-14, L497@2025-04-14 |

## Unmatched legs -- inferred classification (NOT a read-back type)

5 transactions / 20 legs on loans 27, 27, 27, 28, 28 have no entry in any `transactions`
read-back.  Reason: net-zero 4-leg interest accrual + exact reversal; loan transaction absent from every `transactions` read-back (superseded/reverted by the accrual-activity replay).  Type inferred from posting shape, NOT confirmed by read-back.

Inferred type: `loanTransactionType.accrual`

| loan | tx | legs | accounts | net-zero | inferred type |
| --- | --- | ---: | --- | --- | --- |
| 27 | L143 | 4 | 3, 5 | True | `loanTransactionType.accrual` |
| 27 | L144 | 4 | 3, 5 | True | `loanTransactionType.accrual` |
| 27 | L145 | 4 | 3, 5 | True | `loanTransactionType.accrual` |
| 28 | L165 | 4 | 3, 5 | True | `loanTransactionType.accrual` |
| 28 | L166 | 4 | 3, 5 | True | `loanTransactionType.accrual` |

