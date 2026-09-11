# Journal-entry leg -> loan transaction TYPE join (sweep)

Every swept `/journalentries` leg carries only `transactionId` =
`L<loanTransactionId>`; the transaction **type** comes only from the loan
read-backs (`transactions[].id -> transactions[].type.code`).  Amounts are
integer minor units; the raw sweep bodies keep decimal major units.

Legs joined: 956; unmatched by read-back: 0.

| type | value | loans | transactions | legs |
| --- | --- | --- | --- | --- |
| `loanTransactionType.accrual` | Accrual | 3, 4, 5, 11, 12, 14, 19, 20, 21, 22, 28, 29, 35, 36, 45, 46, 47 | L17, L24, L31, L74, L81, L94, L122, L129, L134, L139, L177, L186, L217, L226, L270, L279, L284, L285, L286, L287, L288, L289, L290, L291, L292, L293, L294, L295, L296, L297, L298, L299, L300, L301, L302, L303, L304, L305, L306, L307, L308, L309, L310, L311, L312, L313, L314, L315, L316, L317, L318, L319, L320, L321, L322, L323, L324, L325, L326, L327, L328, L329, L330, L333, L334, L335, L336, L337, L338, L339, L340, L341, L342, L343, L344, L345, L346, L347, L348, L349, L350, L351, L352, L353, L354, L355, L356, L357, L358, L359, L360, L361, L362, L363, L365, L366, L367, L368, L369, L370, L371, L372, L373, L374, L375, L376, L377, L378, L379, L380, L381, L382, L383, L384, L385, L386, L387, L388, L389, L390, L391, L392, L393, L394 | 252 |
| `loanTransactionType.chargeOff` | Charge-off | 16, 17, 18 | L106, L112, L118 | 6 |
| `loanTransactionType.chargeback` | Chargeback | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | L4, L8, L14, L21, L28, L35, L36, L44, L45, L46, L47, L54, L59, L60, L68, L75, L82, L88, L95, L101, L107, L113, L119, L125, L126, L130, L131, L135, L136, L142, L143, L147, L149, L150, L156, L160, L164, L165, L169, L178, L187, L188, L192, L196, L200, L204, L205, L209, L218, L227, L228, L232, L236, L240, L244, L245, L249, L253, L257, L258, L262, L271, L280, L281, L332, L398, L402, L406 | 157 |
| `loanTransactionType.disbursement` | Disbursement | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | L1, L5, L11, L18, L25, L32, L39, L49, L56, L63, L69, L76, L83, L89, L96, L102, L108, L114, L120, L127, L132, L137, L144, L153, L157, L161, L166, L170, L179, L189, L193, L197, L201, L206, L210, L219, L229, L233, L237, L241, L246, L250, L254, L259, L263, L272, L282, L395, L399, L403 | 100 |
| `loanTransactionType.downPayment` | Down Payment | 1 | L2 | 2 |
| `loanTransactionType.merchantIssuedRefund` | Merchant Issued Refund | 19, 22 | L124, L140 | 4 |
| `loanTransactionType.payoutRefund` | Payout Refund | 1 | L3 | 3 |
| `loanTransactionType.repayment` | Repayment | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | L6, L7, L9, L10, L12, L13, L15, L16, L19, L20, L22, L23, L26, L27, L29, L30, L33, L34, L37, L38, L40, L41, L42, L43, L48, L50, L51, L52, L53, L55, L57, L58, L61, L62, L64, L65, L66, L67, L70, L71, L72, L73, L77, L78, L79, L80, L84, L85, L86, L87, L90, L91, L92, L93, L97, L98, L99, L100, L103, L104, L105, L109, L110, L111, L115, L116, L117, L121, L123, L128, L133, L138, L141, L145, L146, L148, L151, L152, L154, L155, L158, L159, L162, L163, L167, L168, L171, L172, L173, L174, L175, L176, L180, L181, L182, L183, L184, L185, L190, L191, L194, L195, L198, L199, L202, L203, L207, L208, L211, L212, L213, L214, L215, L216, L220, L221, L222, L223, L224, L225, L230, L231, L234, L235, L238, L239, L242, L243, L247, L248, L251, L252, L255, L256, L260, L261, L264, L265, L266, L267, L268, L269, L273, L274, L275, L276, L277, L278, L283, L331, L364, L396, L397, L400, L401, L404, L405 | 432 |

## `loanTransactionType.accrual` — Accrual

loans: 3, 4, 5, 11, 12, 14, 19, 20, 21, 22, 28, 29, 35, 36, 45, 46, 47; transactions: L17, L24, L31, L74, L81, L94, L122, L129, L134, L139, L177, L186, L217, L226, L270, L279, L284, L285, L286, L287, L288, L289, L290, L291, L292, L293, L294, L295, L296, L297, L298, L299, L300, L301, L302, L303, L304, L305, L306, L307, L308, L309, L310, L311, L312, L313, L314, L315, L316, L317, L318, L319, L320, L321, L322, L323, L324, L325, L326, L327, L328, L329, L330, L333, L334, L335, L336, L337, L338, L339, L340, L341, L342, L343, L344, L345, L346, L347, L348, L349, L350, L351, L352, L353, L354, L355, L356, L357, L358, L359, L360, L361, L362, L363, L365, L366, L367, L368, L369, L370, L371, L372, L373, L374, L375, L376, L377, L378, L379, L380, L381, L382, L383, L384, L385, L386, L387, L388, L389, L390, L391, L392, L393, L394; legs: 252

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | L17 | CREDIT | 7 | 404007 | Fee Income | 300 | MNT | False | False | False |
| 3 | L17 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 4 | L24 | CREDIT | 7 | 404007 | Fee Income | 300 | MNT | False | False | False |
| 4 | L24 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 5 | L31 | CREDIT | 7 | 404007 | Fee Income | 400 | MNT | False | False | False |
| 5 | L31 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 400 | MNT | False | False | False |
| 5 | L31 | CREDIT | 7 | 404007 | Fee Income | 300 | MNT | False | False | False |
| 5 | L31 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 11 | L74 | CREDIT | 7 | 404007 | Fee Income | 3000 | MNT | False | False | False |
| 11 | L74 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 12 | L81 | CREDIT | 7 | 404007 | Fee Income | 3000 | MNT | False | False | False |
| 12 | L81 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 14 | L94 | CREDIT | 7 | 404007 | Fee Income | 3000 | MNT | False | False | False |
| 14 | L94 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 19 | L122 | CREDIT | 7 | 404007 | Fee Income | 500 | MNT | False | False | False |
| 19 | L122 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 20 | L129 | CREDIT | 7 | 404007 | Fee Income | 500 | MNT | False | False | False |
| 20 | L129 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 21 | L134 | CREDIT | 7 | 404007 | Fee Income | 500 | MNT | False | False | False |
| 21 | L134 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 22 | L139 | CREDIT | 7 | 404007 | Fee Income | 500 | MNT | False | False | False |
| 22 | L139 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 28 | L177 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 28 | L177 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 29 | L186 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 29 | L186 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 35 | L217 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 35 | L217 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 36 | L226 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 36 | L226 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 45 | L270 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 45 | L270 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 46 | L279 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 205 | MNT | False | False | False |
| 46 | L279 | CREDIT | 9 | 404000 | Interest Income | 205 | MNT | False | False | False |
| 47 | L284 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 489 | MNT | False | False | False |
| 47 | L284 | CREDIT | 9 | 404000 | Interest Income | 489 | MNT | False | False | False |
| 47 | L285 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L285 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L286 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L286 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L287 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L287 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L288 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L288 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L289 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L289 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L290 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L290 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L291 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L291 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L292 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L292 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L293 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L293 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L294 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L294 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L295 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L295 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L296 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L296 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L297 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L297 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L298 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L298 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L299 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L299 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L300 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 37 | MNT | False | False | False |
| 47 | L300 | CREDIT | 9 | 404000 | Interest Income | 37 | MNT | False | False | False |
| 47 | L301 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L301 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L302 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 38 | MNT | False | False | False |
| 47 | L302 | CREDIT | 9 | 404000 | Interest Income | 38 | MNT | False | False | False |
| 47 | L303 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L303 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L304 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L304 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L305 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L305 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L306 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L306 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L307 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L307 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L308 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L308 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L309 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L309 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L310 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L310 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L311 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L311 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L312 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L312 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L313 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L313 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L314 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L314 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L315 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L315 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L316 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L316 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L316 | CREDIT | 7 | 404007 | Fee Income | 500 | MNT | False | False | False |
| 47 | L316 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 47 | L317 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L317 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L318 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L318 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L319 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L319 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L320 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L320 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L321 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L321 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L322 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L322 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L323 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L323 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L324 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L324 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L325 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L325 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L326 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L326 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L327 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L327 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L328 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L328 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L329 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L329 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L330 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 33 | MNT | False | False | False |
| 47 | L330 | CREDIT | 9 | 404000 | Interest Income | 33 | MNT | False | False | False |
| 47 | L333 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 34 | MNT | False | False | False |
| 47 | L333 | CREDIT | 9 | 404000 | Interest Income | 34 | MNT | False | False | False |
| 47 | L334 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L334 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L335 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L335 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L336 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L336 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L337 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L337 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L338 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L338 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L339 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L339 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L340 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L340 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L341 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L341 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L342 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L342 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L343 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L343 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L344 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L344 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L345 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L345 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L346 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L346 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L347 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L347 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L348 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L348 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L349 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L349 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L350 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L350 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L351 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L351 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L352 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L352 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L353 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L353 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L354 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L354 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L355 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L355 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L356 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L356 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L357 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L357 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L358 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L358 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L359 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L359 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L360 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L360 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L361 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 26 | MNT | False | False | False |
| 47 | L361 | CREDIT | 9 | 404000 | Interest Income | 26 | MNT | False | False | False |
| 47 | L362 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L362 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L363 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L363 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L365 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 25 | MNT | False | False | False |
| 47 | L365 | CREDIT | 9 | 404000 | Interest Income | 25 | MNT | False | False | False |
| 47 | L366 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L366 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L367 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L367 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L368 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L368 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L369 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L369 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L370 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L370 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L371 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L371 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L372 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L372 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L373 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L373 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L374 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L374 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L375 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L375 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L376 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L376 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L377 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L377 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L378 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L378 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L379 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L379 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L380 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L380 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L381 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L381 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L382 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L382 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L383 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L383 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L384 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L384 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L385 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L385 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L386 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L386 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L387 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L387 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L388 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L388 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L389 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L389 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L390 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L390 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L391 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L391 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L392 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L392 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |
| 47 | L393 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 19 | MNT | False | False | False |
| 47 | L393 | CREDIT | 9 | 404000 | Interest Income | 19 | MNT | False | False | False |
| 47 | L394 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 47 | L394 | CREDIT | 9 | 404000 | Interest Income | 20 | MNT | False | False | False |

## `loanTransactionType.chargeOff` — Charge-off

loans: 16, 17, 18; transactions: L106, L112, L118; legs: 6

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | L106 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | True | False |
| 16 | L106 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |
| 17 | L112 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | True | False |
| 17 | L112 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |
| 18 | L118 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | True | False |
| 18 | L118 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |

## `loanTransactionType.chargeback` — Chargeback

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50; transactions: L4, L8, L14, L21, L28, L35, L36, L44, L45, L46, L47, L54, L59, L60, L68, L75, L82, L88, L95, L101, L107, L113, L119, L125, L126, L130, L131, L135, L136, L142, L143, L147, L149, L150, L156, L160, L164, L165, L169, L178, L187, L188, L192, L196, L200, L204, L205, L209, L218, L227, L228, L232, L236, L240, L244, L245, L249, L253, L257, L258, L262, L271, L280, L281, L332, L398, L402, L406; legs: 157

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L4 | CREDIT | 6 | 145023 | Suspense/Clearing account | 2500 | MNT | False | False | False |
| 1 | L4 | DEBIT | 17 | l1 | Overpayment account | 2500 | MNT | False | False | False |
| 2 | L8 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 2 | L8 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 3 | L14 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12800 | MNT | False | False | False |
| 3 | L14 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 3 | L14 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 4 | L21 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5300 | MNT | False | False | False |
| 4 | L21 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | MNT | False | False | False |
| 4 | L21 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 5 | L28 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | MNT | False | False | False |
| 5 | L28 | DEBIT | 5 | 112601 | Loans Receivable | 4300 | MNT | False | False | False |
| 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 400 | MNT | False | False | False |
| 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 6 | L35 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 6 | L35 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 6 | L36 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 6 | L36 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L44 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L44 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L45 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L45 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L46 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L46 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L47 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L47 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L54 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 8 | L54 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 9 | L59 | CREDIT | 6 | 145023 | Suspense/Clearing account | 7500 | MNT | False | False | False |
| 9 | L59 | DEBIT | 5 | 112601 | Loans Receivable | 7500 | MNT | False | False | False |
| 9 | L60 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | MNT | False | False | False |
| 9 | L60 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | MNT | False | False | False |
| 10 | L68 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 10 | L68 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L75 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 11 | L75 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L75 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 12 | L82 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 12 | L82 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 12 | L82 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 13 | L88 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 13 | L88 | DEBIT | 17 | l1 | Overpayment account | 15000 | MNT | False | False | False |
| 13 | L88 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 14 | L95 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 14 | L95 | DEBIT | 17 | l1 | Overpayment account | 10000 | MNT | False | False | False |
| 15 | L101 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 15 | L101 | DEBIT | 17 | l1 | Overpayment account | 10000 | MNT | False | False | False |
| 16 | L107 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | True | False |
| 16 | L107 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |
| 17 | L113 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | True | False |
| 17 | L113 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |
| 17 | L113 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | MNT | False | True | False |
| 18 | L119 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | True | False |
| 18 | L119 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | MNT | False | True | False |
| 18 | L119 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | MNT | False | True | False |
| 19 | L125 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | MNT | False | False | False |
| 19 | L125 | DEBIT | 17 | l1 | Overpayment account | 700 | MNT | False | False | False |
| 19 | L126 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | MNT | False | False | False |
| 19 | L126 | DEBIT | 17 | l1 | Overpayment account | 300 | MNT | False | False | False |
| 19 | L126 | DEBIT | 5 | 112601 | Loans Receivable | 400 | MNT | False | False | False |
| 20 | L130 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | MNT | False | False | False |
| 20 | L130 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 20 | L131 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 20 | L131 | DEBIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 20 | L131 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 21 | L135 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | MNT | False | False | False |
| 21 | L135 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 21 | L136 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 21 | L136 | DEBIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 21 | L136 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 22 | L142 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | MNT | False | False | False |
| 22 | L142 | DEBIT | 17 | l1 | Overpayment account | 300 | MNT | False | False | False |
| 22 | L143 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 22 | L143 | DEBIT | 17 | l1 | Overpayment account | 700 | MNT | False | False | False |
| 22 | L143 | DEBIT | 5 | 112601 | Loans Receivable | 300 | MNT | False | False | False |
| 23 | L147 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L147 | DEBIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 23 | L147 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 23 | L147 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L147 | CREDIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 23 | L147 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 23 | L149 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L149 | DEBIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 23 | L149 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L149 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 23 | L150 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L150 | DEBIT | 5 | 112601 | Loans Receivable | 500 | MNT | False | False | False |
| 23 | L150 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 24 | L156 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 24 | L156 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 25 | L160 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 25 | L160 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 26 | L164 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 26 | L164 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 26 | L165 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 26 | L165 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 27 | L169 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 27 | L169 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 28 | L178 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L178 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 29 | L187 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L187 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 29 | L188 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 29 | L188 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | MNT | False | False | False |
| 30 | L192 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 30 | L192 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 31 | L196 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 31 | L196 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | MNT | False | False | False |
| 32 | L200 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 32 | L200 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 33 | L204 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 33 | L204 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 33 | L205 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 33 | L205 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 34 | L209 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 34 | L209 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 35 | L218 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L218 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 36 | L227 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L227 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 36 | L228 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 36 | L228 | DEBIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 37 | L232 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 37 | L232 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 38 | L236 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 38 | L236 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | MNT | False | False | False |
| 39 | L240 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 39 | L240 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 40 | L244 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 40 | L244 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 40 | L245 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 40 | L245 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 41 | L249 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 41 | L249 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 42 | L253 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 42 | L253 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 43 | L257 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 43 | L257 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |
| 43 | L258 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 43 | L258 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 44 | L262 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 44 | L262 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 45 | L271 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L271 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 46 | L280 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L280 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | MNT | False | False | False |
| 46 | L281 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 46 | L281 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | MNT | False | False | False |
| 47 | L332 | CREDIT | 6 | 145023 | Suspense/Clearing account | 34517 | MNT | False | False | False |
| 47 | L332 | DEBIT | 5 | 112601 | Loans Receivable | 33042 | MNT | False | False | False |
| 47 | L332 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 48 | L398 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 48 | L398 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 49 | L402 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 49 | L402 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | MNT | False | False | False |
| 50 | L406 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | MNT | False | False | False |
| 50 | L406 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | MNT | False | False | False |

## `loanTransactionType.disbursement` — Disbursement

loans: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50; transactions: L1, L5, L11, L18, L25, L32, L39, L49, L56, L63, L69, L76, L83, L89, L96, L102, L108, L114, L120, L127, L132, L137, L144, L153, L157, L161, L166, L170, L179, L189, L193, L197, L201, L206, L210, L219, L229, L233, L237, L241, L246, L250, L254, L259, L263, L272, L282, L395, L399, L403; legs: 100

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L1 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 1 | L1 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 2 | L5 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 2 | L5 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 3 | L11 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 3 | L11 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 4 | L18 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 4 | L18 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 5 | L25 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 5 | L25 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 6 | L32 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 6 | L32 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 7 | L39 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 7 | L39 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 8 | L49 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 8 | L49 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 9 | L56 | DEBIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 9 | L56 | CREDIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 10 | L63 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 10 | L63 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 11 | L69 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 11 | L69 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 12 | L76 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 12 | L76 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 13 | L83 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 13 | L83 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 14 | L89 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 14 | L89 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 15 | L96 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 15 | L96 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 16 | L102 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 16 | L102 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 17 | L108 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 17 | L108 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 18 | L114 | DEBIT | 5 | 112601 | Loans Receivable | 100000 | MNT | False | False | False |
| 18 | L114 | CREDIT | 6 | 145023 | Suspense/Clearing account | 100000 | MNT | False | False | False |
| 19 | L120 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 19 | L120 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 20 | L127 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 20 | L127 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 21 | L132 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 21 | L132 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 22 | L137 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 22 | L137 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 23 | L144 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 23 | L144 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 24 | L153 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 24 | L153 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 25 | L157 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 25 | L157 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 26 | L161 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 26 | L161 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 27 | L166 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 27 | L166 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 28 | L170 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 28 | L170 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 29 | L179 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 29 | L179 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 30 | L189 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 30 | L189 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 31 | L193 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 31 | L193 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 32 | L197 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 32 | L197 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 33 | L201 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 33 | L201 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 34 | L206 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 34 | L206 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 35 | L210 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 35 | L210 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 36 | L219 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 36 | L219 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 37 | L229 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 37 | L229 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 38 | L233 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 38 | L233 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 39 | L237 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 39 | L237 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 40 | L241 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 40 | L241 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 41 | L246 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 41 | L246 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 42 | L250 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 42 | L250 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 43 | L254 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 43 | L254 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 44 | L259 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 44 | L259 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 45 | L263 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 45 | L263 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 46 | L272 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 46 | L272 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 47 | L282 | DEBIT | 5 | 112601 | Loans Receivable | 200000 | MNT | False | False | False |
| 47 | L282 | CREDIT | 6 | 145023 | Suspense/Clearing account | 200000 | MNT | False | False | False |
| 48 | L395 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 48 | L395 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 49 | L399 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 49 | L399 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |
| 50 | L403 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 50 | L403 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | MNT | False | False | False |

## `loanTransactionType.downPayment` — Down Payment

loans: 1; transactions: L2; legs: 2

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L2 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 1 | L2 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |

## `loanTransactionType.merchantIssuedRefund` — Merchant Issued Refund

loans: 19, 22; transactions: L124, L140; legs: 4

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | L124 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 19 | L124 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 22 | L140 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 22 | L140 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |

## `loanTransactionType.payoutRefund` — Payout Refund

loans: 1; transactions: L3; legs: 3

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | L3 | CREDIT | 5 | 112601 | Loans Receivable | 37500 | MNT | False | False | False |
| 1 | L3 | CREDIT | 17 | l1 | Overpayment account | 12500 | MNT | False | False | False |
| 1 | L3 | DEBIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |

## `loanTransactionType.repayment` — Repayment

loans: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50; transactions: L6, L7, L9, L10, L12, L13, L15, L16, L19, L20, L22, L23, L26, L27, L29, L30, L33, L34, L37, L38, L40, L41, L42, L43, L48, L50, L51, L52, L53, L55, L57, L58, L61, L62, L64, L65, L66, L67, L70, L71, L72, L73, L77, L78, L79, L80, L84, L85, L86, L87, L90, L91, L92, L93, L97, L98, L99, L100, L103, L104, L105, L109, L110, L111, L115, L116, L117, L121, L123, L128, L133, L138, L141, L145, L146, L148, L151, L152, L154, L155, L158, L159, L162, L163, L167, L168, L171, L172, L173, L174, L175, L176, L180, L181, L182, L183, L184, L185, L190, L191, L194, L195, L198, L199, L202, L203, L207, L208, L211, L212, L213, L214, L215, L216, L220, L221, L222, L223, L224, L225, L230, L231, L234, L235, L238, L239, L242, L243, L247, L248, L251, L252, L255, L256, L260, L261, L264, L265, L266, L267, L268, L269, L273, L274, L275, L276, L277, L278, L283, L331, L364, L396, L397, L400, L401, L404, L405; legs: 432

| loan | tx | entry | account id | account code | account name | amount (minor) | currency | reversed | charged_off | fraud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | L6 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 2 | L6 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 2 | L7 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 2 | L7 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 2 | L9 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 2 | L9 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 2 | L10 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 2 | L10 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 3 | L12 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 3 | L12 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 3 | L13 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 3 | L13 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 3 | L13 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12800 | MNT | False | False | False |
| 3 | L15 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 3 | L15 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 3 | L15 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25300 | MNT | False | False | False |
| 3 | L16 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 3 | L16 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 4 | L19 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 4 | L19 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 4 | L20 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 4 | L20 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 4 | L20 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12800 | MNT | False | False | False |
| 4 | L22 | CREDIT | 5 | 112601 | Loans Receivable | 17200 | MNT | False | False | False |
| 4 | L22 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 4 | L22 | DEBIT | 6 | 145023 | Suspense/Clearing account | 17500 | MNT | False | False | False |
| 4 | L23 | CREDIT | 5 | 112601 | Loans Receivable | 12800 | MNT | False | False | False |
| 4 | L23 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12800 | MNT | False | False | False |
| 5 | L26 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 5 | L26 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 5 | L27 | CREDIT | 5 | 112601 | Loans Receivable | 11800 | MNT | False | False | False |
| 5 | L27 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 700 | MNT | False | False | False |
| 5 | L27 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 5 | L29 | CREDIT | 5 | 112601 | Loans Receivable | 11800 | MNT | False | False | False |
| 5 | L29 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 700 | MNT | False | False | False |
| 5 | L29 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 5 | L30 | CREDIT | 5 | 112601 | Loans Receivable | 18200 | MNT | False | False | False |
| 5 | L30 | DEBIT | 6 | 145023 | Suspense/Clearing account | 18200 | MNT | False | False | False |
| 6 | L33 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 6 | L33 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 6 | L34 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 6 | L34 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 6 | L37 | CREDIT | 5 | 112601 | Loans Receivable | 37500 | MNT | False | False | False |
| 6 | L37 | DEBIT | 6 | 145023 | Suspense/Clearing account | 37500 | MNT | False | False | False |
| 6 | L38 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 6 | L38 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L40 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L40 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L41 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L41 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L42 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L42 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L43 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 7 | L43 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 7 | L48 | CREDIT | 5 | 112601 | Loans Receivable | 50000 | MNT | False | False | False |
| 7 | L48 | DEBIT | 6 | 145023 | Suspense/Clearing account | 50000 | MNT | False | False | False |
| 8 | L50 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L50 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 8 | L51 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L51 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 8 | L52 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L52 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 8 | L53 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L53 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 8 | L55 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 8 | L55 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 9 | L57 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 9 | L57 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 9 | L58 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 9 | L58 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 9 | L61 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 9 | L61 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 9 | L62 | CREDIT | 5 | 112601 | Loans Receivable | 12500 | MNT | False | False | False |
| 9 | L62 | DEBIT | 6 | 145023 | Suspense/Clearing account | 12500 | MNT | False | False | False |
| 10 | L64 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 10 | L64 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 10 | L65 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 10 | L65 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 10 | L66 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 10 | L66 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 10 | L67 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 10 | L67 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 11 | L70 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L70 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 11 | L71 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L71 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 11 | L72 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L72 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 11 | L72 | DEBIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 11 | L73 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 11 | L73 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 12 | L77 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 12 | L77 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 12 | L78 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 12 | L78 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 12 | L79 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 12 | L79 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 12 | L79 | DEBIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 12 | L80 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 12 | L80 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 13 | L84 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 13 | L84 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 13 | L85 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 13 | L85 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 13 | L86 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 13 | L86 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 13 | L87 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 13 | L87 | CREDIT | 17 | l1 | Overpayment account | 15000 | MNT | False | False | False |
| 13 | L87 | DEBIT | 6 | 145023 | Suspense/Clearing account | 40000 | MNT | False | False | False |
| 14 | L90 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 14 | L90 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 14 | L91 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 14 | L91 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 14 | L92 | CREDIT | 5 | 112601 | Loans Receivable | 22000 | MNT | False | False | False |
| 14 | L92 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 14 | L92 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 14 | L93 | CREDIT | 5 | 112601 | Loans Receivable | 28000 | MNT | False | False | False |
| 14 | L93 | CREDIT | 17 | l1 | Overpayment account | 12000 | MNT | False | False | False |
| 14 | L93 | DEBIT | 6 | 145023 | Suspense/Clearing account | 40000 | MNT | False | False | False |
| 15 | L97 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 15 | L97 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 15 | L98 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 15 | L98 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 15 | L99 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 15 | L99 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 15 | L100 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 15 | L100 | CREDIT | 17 | l1 | Overpayment account | 15000 | MNT | False | False | False |
| 15 | L100 | DEBIT | 6 | 145023 | Suspense/Clearing account | 40000 | MNT | False | False | False |
| 16 | L103 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 16 | L103 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 16 | L104 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 16 | L104 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 16 | L105 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 16 | L105 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 17 | L109 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 17 | L109 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 17 | L110 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 17 | L110 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 17 | L111 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 17 | L111 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 17 | L111 | DEBIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 18 | L115 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 18 | L115 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 18 | L116 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 18 | L116 | DEBIT | 6 | 145023 | Suspense/Clearing account | 25000 | MNT | False | False | False |
| 18 | L117 | CREDIT | 5 | 112601 | Loans Receivable | 25000 | MNT | False | False | False |
| 18 | L117 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 3000 | MNT | False | False | False |
| 18 | L117 | DEBIT | 6 | 145023 | Suspense/Clearing account | 28000 | MNT | False | False | False |
| 19 | L121 | CREDIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 19 | L121 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 19 | L121 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 19 | L121 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 19 | L121 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 19 | L121 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 19 | L123 | CREDIT | 5 | 112601 | Loans Receivable | 9000 | MNT | False | False | False |
| 19 | L123 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 19 | L123 | CREDIT | 17 | l1 | Overpayment account | 1000 | MNT | False | False | False |
| 19 | L123 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 20 | L128 | CREDIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 20 | L128 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 20 | L128 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 21 | L133 | CREDIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 21 | L133 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 21 | L133 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 22 | L138 | CREDIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 22 | L138 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 22 | L138 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 22 | L138 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | MNT | False | False | False |
| 22 | L138 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 22 | L138 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 22 | L141 | CREDIT | 5 | 112601 | Loans Receivable | 9000 | MNT | False | False | False |
| 22 | L141 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 22 | L141 | CREDIT | 17 | l1 | Overpayment account | 1000 | MNT | False | False | False |
| 22 | L141 | DEBIT | 6 | 145023 | Suspense/Clearing account | 10500 | MNT | False | False | False |
| 23 | L145 | CREDIT | 5 | 112601 | Loans Receivable | 2500 | MNT | False | False | False |
| 23 | L145 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 23 | L145 | DEBIT | 6 | 145023 | Suspense/Clearing account | 2800 | MNT | False | False | False |
| 23 | L145 | DEBIT | 5 | 112601 | Loans Receivable | 2500 | MNT | False | False | False |
| 23 | L145 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | MNT | False | False | False |
| 23 | L145 | CREDIT | 6 | 145023 | Suspense/Clearing account | 2800 | MNT | False | False | False |
| 23 | L146 | CREDIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 23 | L146 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 23 | L146 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L146 | DEBIT | 5 | 112601 | Loans Receivable | 800 | MNT | False | False | False |
| 23 | L146 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | MNT | False | False | False |
| 23 | L146 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L148 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 23 | L148 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L148 | DEBIT | 5 | 112601 | Loans Receivable | 1000 | MNT | False | False | False |
| 23 | L148 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 23 | L151 | CREDIT | 5 | 112601 | Loans Receivable | 2500 | MNT | False | False | False |
| 23 | L151 | DEBIT | 6 | 145023 | Suspense/Clearing account | 2500 | MNT | False | False | False |
| 23 | L152 | CREDIT | 5 | 112601 | Loans Receivable | 500 | MNT | False | False | False |
| 23 | L152 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 500 | MNT | False | False | False |
| 23 | L152 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | MNT | False | False | False |
| 24 | L154 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 24 | L154 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 24 | L154 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 24 | L155 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 24 | L155 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 24 | L155 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 25 | L158 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 25 | L158 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 25 | L158 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 25 | L159 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 25 | L159 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 25 | L159 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 26 | L162 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 26 | L162 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 26 | L162 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 26 | L163 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 26 | L163 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 26 | L163 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 27 | L167 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 27 | L167 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 27 | L167 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 27 | L168 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 27 | L168 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 27 | L168 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L171 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 28 | L171 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 28 | L171 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L172 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 28 | L172 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 28 | L172 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L173 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 28 | L173 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 28 | L173 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L174 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 28 | L174 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 28 | L174 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L175 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 28 | L175 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 28 | L175 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 28 | L176 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 28 | L176 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 28 | L176 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 29 | L180 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 29 | L180 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 29 | L180 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L181 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 29 | L181 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 29 | L181 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L182 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 29 | L182 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 29 | L182 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L183 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 29 | L183 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 29 | L183 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L184 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 29 | L184 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 29 | L184 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 29 | L185 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 29 | L185 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 29 | L185 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 30 | L190 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 30 | L190 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 30 | L190 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 30 | L191 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 30 | L191 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 30 | L191 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 31 | L194 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 31 | L194 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 31 | L194 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 31 | L195 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 31 | L195 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 31 | L195 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 32 | L198 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 32 | L198 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 32 | L198 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 32 | L199 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 32 | L199 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 32 | L199 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 33 | L202 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 33 | L202 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 33 | L202 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 33 | L203 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 33 | L203 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 33 | L203 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 34 | L207 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 34 | L207 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 34 | L207 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 34 | L208 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 34 | L208 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 34 | L208 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L211 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 35 | L211 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 35 | L211 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L212 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 35 | L212 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 35 | L212 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L213 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 35 | L213 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 35 | L213 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L214 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 35 | L214 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 35 | L214 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L215 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 35 | L215 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 35 | L215 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 35 | L216 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 35 | L216 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 35 | L216 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 36 | L220 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 36 | L220 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 36 | L220 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L221 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 36 | L221 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 36 | L221 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L222 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 36 | L222 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 36 | L222 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L223 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 36 | L223 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 36 | L223 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L224 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 36 | L224 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 36 | L224 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 36 | L225 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 36 | L225 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 36 | L225 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 37 | L230 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 37 | L230 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 37 | L230 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 37 | L231 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 37 | L231 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 37 | L231 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 38 | L234 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 38 | L234 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 38 | L234 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 38 | L235 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 38 | L235 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 38 | L235 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 39 | L238 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 39 | L238 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 39 | L238 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 39 | L239 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 39 | L239 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 39 | L239 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 40 | L242 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 40 | L242 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 40 | L242 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 40 | L243 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 40 | L243 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 40 | L243 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 41 | L247 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 41 | L247 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 41 | L247 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 41 | L248 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 41 | L248 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 41 | L248 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 42 | L251 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 42 | L251 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 42 | L251 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 42 | L252 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 42 | L252 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 42 | L252 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 43 | L255 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 43 | L255 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 43 | L255 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 43 | L256 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 43 | L256 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 43 | L256 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 44 | L260 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 44 | L260 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 44 | L260 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 44 | L261 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 44 | L261 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 44 | L261 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L264 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 45 | L264 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 45 | L264 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L265 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 45 | L265 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 45 | L265 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L266 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 45 | L266 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 45 | L266 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L267 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 45 | L267 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 45 | L267 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L268 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 45 | L268 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 45 | L268 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 45 | L269 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 45 | L269 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 45 | L269 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 46 | L273 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 46 | L273 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 46 | L273 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L274 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 46 | L274 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 46 | L274 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L275 | CREDIT | 5 | 112601 | Loans Receivable | 1662 | MNT | False | False | False |
| 46 | L275 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 39 | MNT | False | False | False |
| 46 | L275 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L276 | CREDIT | 5 | 112601 | Loans Receivable | 1672 | MNT | False | False | False |
| 46 | L276 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 29 | MNT | False | False | False |
| 46 | L276 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L277 | CREDIT | 5 | 112601 | Loans Receivable | 1681 | MNT | False | False | False |
| 46 | L277 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 20 | MNT | False | False | False |
| 46 | L277 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 46 | L278 | CREDIT | 5 | 112601 | Loans Receivable | 1690 | MNT | False | False | False |
| 46 | L278 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 10 | MNT | False | False | False |
| 46 | L278 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1700 | MNT | False | False | False |
| 47 | L283 | CREDIT | 5 | 112601 | Loans Receivable | 32850 | MNT | False | False | False |
| 47 | L283 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 1167 | MNT | False | False | False |
| 47 | L283 | DEBIT | 6 | 145023 | Suspense/Clearing account | 34017 | MNT | False | False | False |
| 47 | L331 | CREDIT | 5 | 112601 | Loans Receivable | 33042 | MNT | False | False | False |
| 47 | L331 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 1475 | MNT | False | False | False |
| 47 | L331 | DEBIT | 6 | 145023 | Suspense/Clearing account | 34517 | MNT | False | False | False |
| 47 | L364 | CREDIT | 5 | 112601 | Loans Receivable | 66277 | MNT | False | False | False |
| 47 | L364 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 2257 | MNT | False | False | False |
| 47 | L364 | DEBIT | 6 | 145023 | Suspense/Clearing account | 68534 | MNT | False | False | False |
| 48 | L396 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 48 | L396 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 48 | L396 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 48 | L397 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 48 | L397 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 48 | L397 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 49 | L400 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 49 | L400 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 49 | L400 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 49 | L401 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 49 | L401 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 49 | L401 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 50 | L404 | CREDIT | 5 | 112601 | Loans Receivable | 1643 | MNT | False | False | False |
| 50 | L404 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 58 | MNT | False | False | False |
| 50 | L404 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |
| 50 | L405 | CREDIT | 5 | 112601 | Loans Receivable | 1652 | MNT | False | False | False |
| 50 | L405 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 49 | MNT | False | False | False |
| 50 | L405 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1701 | MNT | False | False | False |

## Type x charged-off -- the `chargeback` arm (OH-TIERD15-CM step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.

| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeback` | True | 157 | 68 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 8 | 16, 17, 18 | 149 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |

### Every `chargeback` leg -- required listing

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency |
| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |
| `loanTransactionType.chargeback` | 1 | L4 | DEBIT | 17 | l1 | Overpayment account | 2500 | False | False | MNT |
| `loanTransactionType.chargeback` | 1 | L4 | CREDIT | 6 | 145023 | Suspense/Clearing account | 2500 | False | False | MNT |
| `loanTransactionType.chargeback` | 2 | L8 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 2 | L8 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 3 | L14 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 3 | L14 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 3 | L14 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12800 | False | False | MNT |
| `loanTransactionType.chargeback` | 4 | L21 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | False | False | MNT |
| `loanTransactionType.chargeback` | 4 | L21 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 4 | L21 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5300 | False | False | MNT |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 5 | 112601 | Loans Receivable | 4300 | False | False | MNT |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 400 | False | False | MNT |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 5 | L28 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT |
| `loanTransactionType.chargeback` | 6 | L35 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 6 | L35 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 6 | L36 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 6 | L36 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L44 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L44 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L45 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L45 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L46 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L46 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L47 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 7 | L47 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 8 | L54 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 8 | L54 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT |
| `loanTransactionType.chargeback` | 9 | L59 | DEBIT | 5 | 112601 | Loans Receivable | 7500 | False | False | MNT |
| `loanTransactionType.chargeback` | 9 | L59 | CREDIT | 6 | 145023 | Suspense/Clearing account | 7500 | False | False | MNT |
| `loanTransactionType.chargeback` | 9 | L60 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | False | False | MNT |
| `loanTransactionType.chargeback` | 9 | L60 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT |
| `loanTransactionType.chargeback` | 10 | L68 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT |
| `loanTransactionType.chargeback` | 10 | L68 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | False | MNT |
| `loanTransactionType.chargeback` | 11 | L75 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT |
| `loanTransactionType.chargeback` | 11 | L75 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | False | False | MNT |
| `loanTransactionType.chargeback` | 11 | L75 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | False | MNT |
| `loanTransactionType.chargeback` | 12 | L82 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT |
| `loanTransactionType.chargeback` | 12 | L82 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | False | False | MNT |
| `loanTransactionType.chargeback` | 12 | L82 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | False | MNT |
| `loanTransactionType.chargeback` | 13 | L88 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | False | False | MNT |
| `loanTransactionType.chargeback` | 13 | L88 | DEBIT | 17 | l1 | Overpayment account | 15000 | False | False | MNT |
| `loanTransactionType.chargeback` | 13 | L88 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | False | MNT |
| `loanTransactionType.chargeback` | 14 | L95 | DEBIT | 17 | l1 | Overpayment account | 10000 | False | False | MNT |
| `loanTransactionType.chargeback` | 14 | L95 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | False | False | MNT |
| `loanTransactionType.chargeback` | 15 | L101 | DEBIT | 17 | l1 | Overpayment account | 10000 | False | False | MNT |
| `loanTransactionType.chargeback` | 15 | L101 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | False | False | MNT |
| `loanTransactionType.chargeback` | 16 | L107 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT |
| `loanTransactionType.chargeback` | 16 | L107 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | True | MNT |
| `loanTransactionType.chargeback` | 17 | L113 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | False | True | MNT |
| `loanTransactionType.chargeback` | 17 | L113 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT |
| `loanTransactionType.chargeback` | 17 | L113 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | True | MNT |
| `loanTransactionType.chargeback` | 18 | L119 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | False | True | MNT |
| `loanTransactionType.chargeback` | 18 | L119 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT |
| `loanTransactionType.chargeback` | 18 | L119 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | True | MNT |
| `loanTransactionType.chargeback` | 19 | L125 | DEBIT | 17 | l1 | Overpayment account | 700 | False | False | MNT |
| `loanTransactionType.chargeback` | 19 | L125 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | False | False | MNT |
| `loanTransactionType.chargeback` | 19 | L126 | DEBIT | 5 | 112601 | Loans Receivable | 400 | False | False | MNT |
| `loanTransactionType.chargeback` | 19 | L126 | DEBIT | 17 | l1 | Overpayment account | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 19 | L126 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | False | False | MNT |
| `loanTransactionType.chargeback` | 20 | L130 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 20 | L130 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 20 | L131 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT |
| `loanTransactionType.chargeback` | 20 | L131 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT |
| `loanTransactionType.chargeback` | 20 | L131 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 21 | L135 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 21 | L135 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 21 | L136 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT |
| `loanTransactionType.chargeback` | 21 | L136 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT |
| `loanTransactionType.chargeback` | 21 | L136 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 22 | L142 | DEBIT | 17 | l1 | Overpayment account | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 22 | L142 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 22 | L143 | DEBIT | 5 | 112601 | Loans Receivable | 300 | False | False | MNT |
| `loanTransactionType.chargeback` | 22 | L143 | DEBIT | 17 | l1 | Overpayment account | 700 | False | False | MNT |
| `loanTransactionType.chargeback` | 22 | L143 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L149 | DEBIT | 5 | 112601 | Loans Receivable | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L149 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L149 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L149 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L150 | DEBIT | 5 | 112601 | Loans Receivable | 500 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L150 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | False | False | MNT |
| `loanTransactionType.chargeback` | 23 | L150 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT |
| `loanTransactionType.chargeback` | 24 | L156 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 24 | L156 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 25 | L160 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 25 | L160 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 26 | L164 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 26 | L164 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 26 | L165 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 26 | L165 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 27 | L169 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 27 | L169 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 28 | L178 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 28 | L178 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 29 | L187 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 29 | L187 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 29 | L188 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | False | False | MNT |
| `loanTransactionType.chargeback` | 29 | L188 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT |
| `loanTransactionType.chargeback` | 30 | L192 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 30 | L192 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 31 | L196 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT |
| `loanTransactionType.chargeback` | 31 | L196 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 32 | L200 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 32 | L200 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 33 | L204 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 33 | L204 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 33 | L205 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 33 | L205 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 34 | L209 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 34 | L209 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 35 | L218 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | False | False | MNT |
| `loanTransactionType.chargeback` | 35 | L218 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 36 | L227 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | False | False | MNT |
| `loanTransactionType.chargeback` | 36 | L227 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 36 | L228 | DEBIT | 5 | 112601 | Loans Receivable | 1690 | False | False | MNT |
| `loanTransactionType.chargeback` | 36 | L228 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT |
| `loanTransactionType.chargeback` | 37 | L232 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 37 | L232 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 38 | L236 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT |
| `loanTransactionType.chargeback` | 38 | L236 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 39 | L240 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 39 | L240 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 40 | L244 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 40 | L244 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 40 | L245 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 40 | L245 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 41 | L249 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 41 | L249 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 42 | L253 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 42 | L253 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 43 | L257 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 43 | L257 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 43 | L258 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 43 | L258 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 44 | L262 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 44 | L262 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 45 | L271 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 45 | L271 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 46 | L280 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 46 | L280 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 46 | L281 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | False | False | MNT |
| `loanTransactionType.chargeback` | 46 | L281 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT |
| `loanTransactionType.chargeback` | 47 | L332 | DEBIT | 5 | 112601 | Loans Receivable | 33042 | False | False | MNT |
| `loanTransactionType.chargeback` | 47 | L332 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | False | False | MNT |
| `loanTransactionType.chargeback` | 47 | L332 | CREDIT | 6 | 145023 | Suspense/Clearing account | 34517 | False | False | MNT |
| `loanTransactionType.chargeback` | 48 | L398 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT |
| `loanTransactionType.chargeback` | 48 | L398 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT |
| `loanTransactionType.chargeback` | 49 | L402 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT |
| `loanTransactionType.chargeback` | 49 | L402 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 50 | L406 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT |
| `loanTransactionType.chargeback` | 50 | L406 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT |

### Every chargeback loan transaction and its read-back portions

Portions are integer minor units; `-` means the read-back did not carry that field.

| loan | tx | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | L4 | 2024-01-10 | 2500 | 0 | 0 | 0 | 0 | 2500 | 0 | False | False | False | MNT | 2 |
| 2 | L8 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L14 | 2024-01-20 | 12800 | 12500 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 3 |
| 4 | L21 | 2024-01-20 | 5300 | 5000 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 3 |
| 5 | L28 | 2024-01-20 | 5000 | 4300 | 0 | 400 | 300 | 0 | 0 | False | False | False | MNT | 4 |
| 6 | L35 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L36 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L44 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L45 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L46 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L47 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 8 | L54 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L59 | 2024-01-20 | 7500 | 7500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L60 | 2024-01-25 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 10 | L68 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 11 | L75 | 2024-04-01 | 28000 | 25000 | 0 | 3000 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 12 | L82 | 2024-04-01 | 28000 | 25000 | 0 | 0 | 3000 | 0 | 0 | False | False | False | MNT | 3 |
| 13 | L88 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 15000 | 0 | False | False | False | MNT | 3 |
| 14 | L95 | 2024-04-01 | 10000 | 7000 | 0 | 3000 | 0 | 10000 | 0 | False | False | False | MNT | 2 |
| 15 | L101 | 2024-04-01 | 10000 | 10000 | 0 | 0 | 0 | 10000 | 0 | False | False | False | MNT | 2 |
| 16 | L107 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 17 | L113 | 2024-04-01 | 28000 | 25000 | 0 | 3000 | 0 | 0 | 0 | False | True | False | MNT | 3 |
| 18 | L119 | 2024-04-01 | 28000 | 25000 | 0 | 0 | 3000 | 0 | 0 | False | True | False | MNT | 3 |
| 19 | L125 | 2024-04-15 | 700 | 200 | 0 | 0 | 500 | 700 | 0 | False | False | False | MNT | 2 |
| 19 | L126 | 2024-04-16 | 700 | 700 | 0 | 0 | 0 | 300 | 0 | False | False | False | MNT | 3 |
| 20 | L130 | 2024-03-01 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L131 | 2024-03-05 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 3 |
| 21 | L135 | 2024-04-15 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 2 |
| 21 | L136 | 2024-04-20 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 3 |
| 22 | L142 | 2024-04-15 | 300 | 0 | 0 | 0 | 300 | 300 | 0 | False | False | False | MNT | 2 |
| 22 | L143 | 2024-04-20 | 1000 | 800 | 0 | 0 | 200 | 700 | 0 | False | False | False | MNT | 3 |
| 23 | L147 | 2024-01-07 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 6 |
| 23 | L149 | 2024-01-07 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 23 | L150 | 2024-01-07 | 1000 | 500 | 0 | 0 | 500 | 0 | 0 | False | False | False | MNT | 3 |
| 24 | L156 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 25 | L160 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L164 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L165 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L169 | 2024-03-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L178 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L187 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L188 | 2024-07-15 | 1700 | 1700 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L192 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L196 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L200 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L204 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L205 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L209 | 2024-03-15 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L218 | 2024-07-15 | 1701 | 1681 | 20 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L227 | 2024-07-15 | 1701 | 1681 | 20 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L228 | 2024-07-30 | 1700 | 1690 | 10 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L232 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L236 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L240 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L244 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L245 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L249 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L253 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L257 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L258 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L262 | 2024-03-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L271 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L280 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L281 | 2024-07-15 | 1700 | 1700 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L332 | 2024-03-01 | 34517 | 33042 | 975 | 0 | 500 | 0 | 0 | False | False | False | MNT | 3 |
| 48 | L398 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 49 | L402 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 50 | L406 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |

### Chargeback portion arms and the `paid > credited` branch

Portion arms observed non-zero on a chargeback transaction (integer minor units):

| portion arm | observed? | count | loans | transactions |
| --- | --- | ---: | --- | --- |
| principal | True | 64 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | L8, L14, L21, L28, L35, L36, L44, L45, L46, L47, L54, L59, L60, L68, L75, L82, L88, L95, L101, L107, L113, L119, L125, L126, L131, L136, L143, L147, L149, L150, L156, L160, L164, L165, L169, L178, L187, L188, L192, L196, L200, L204, L205, L209, L218, L227, L228, L232, L236, L240, L244, L245, L249, L253, L257, L258, L262, L271, L280, L281, L332, L398, L402, L406 |
| interest | True | 13 | 30, 31, 33, 34, 35, 36, 37, 38, 40, 47, 48, 49 | L192, L196, L205, L209, L218, L227, L228, L232, L236, L245, L332, L398, L402 |
| fee | True | 4 | 5, 11, 14, 17 | L28, L75, L95, L113 |
| penalty | True | 15 | 3, 4, 5, 12, 18, 19, 20, 21, 22, 23, 47 | L14, L21, L28, L82, L119, L125, L130, L131, L135, L136, L142, L143, L147, L150, L332 |
| overpayment | True | 8 | 1, 13, 14, 15, 19, 22 | L4, L88, L95, L101, L125, L126, L142, L143 |
| unrecognized_income | False | 0 | - | - |

**FEE portions observed: True. PENALTY portions observed: True.**

`paid > credited` rule: credited < paid -> CREDIT getPrincipalAccount/getFeeAccount/getPenaltyAccount [AccrualBasedAccountingProcessorForLoan.java:1251-1273].

Self-offsetting CREDIT legs (equal DEBIT under the same `transactionId` -- chargeback reversal/replay, NOT a `credited < paid` difference posting):

| loan | tx | entry | account id | account code | account name | amount (minor) | charged_off | currency |
| ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 23 | L147 | CREDIT | 5 | 112601 | Loans Receivable | 800 | False | MNT |
| 23 | L147 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | MNT |
| 23 | L149 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | False | MNT |

**FINDING -- no genuine `paid > credited` leg: the only CREDIT(s) to a principal/fee/penalty account (3 leg(s) on loan 23 tx L147, loan 23 tx L149) each have an equal DEBIT under the same transactionId, i.e. a chargeback reversal/replay pair, not the `credited < paid` difference posting.  The `paid > credited` arm is NOT exercised in this replay.**

### Per-loan charge-off / fraud / currency state

| loan | currency | fraud | non-reversed chargeOff transactions |
| --- | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | False | - |
| 3 | MNT | False | - |
| 4 | MNT | False | - |
| 5 | MNT | False | - |
| 6 | MNT | False | - |
| 7 | MNT | False | - |
| 8 | MNT | False | - |
| 9 | MNT | False | - |
| 10 | MNT | False | - |
| 11 | MNT | False | - |
| 12 | MNT | False | - |
| 13 | MNT | False | - |
| 14 | MNT | False | - |
| 15 | MNT | False | - |
| 16 | MNT | False | L106@2024-03-15 |
| 17 | MNT | False | L112@2024-03-15 |
| 18 | MNT | False | L118@2024-03-15 |
| 19 | MNT | False | - |
| 20 | MNT | False | - |
| 21 | MNT | False | - |
| 22 | MNT | False | - |
| 23 | MNT | False | - |
| 24 | MNT | False | - |
| 25 | MNT | False | - |
| 26 | MNT | False | - |
| 27 | MNT | False | - |
| 28 | MNT | False | - |
| 29 | MNT | False | - |
| 30 | MNT | False | - |
| 31 | MNT | False | - |
| 32 | MNT | False | - |
| 33 | MNT | False | - |
| 34 | MNT | False | - |
| 35 | MNT | False | - |
| 36 | MNT | False | - |
| 37 | MNT | False | - |
| 38 | MNT | False | - |
| 39 | MNT | False | - |
| 40 | MNT | False | - |
| 41 | MNT | False | - |
| 42 | MNT | False | - |
| 43 | MNT | False | - |
| 44 | MNT | False | - |
| 45 | MNT | False | - |
| 46 | MNT | False | - |
| 47 | MNT | False | - |
| 48 | MNT | False | - |
| 49 | MNT | False | - |
| 50 | MNT | False | - |

