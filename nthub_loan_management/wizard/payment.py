from odoo import api, fields, models, _


class PaymentLoan(models.TransientModel):
    _name = 'account.payment.loan'

    payment_date = fields.Date(string="Payment Date", required=True,
                               default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', readonly=False, )
    journal_id = fields.Many2one('account.journal',
                                 domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id')
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'), ], default='outbound', string='Payment Type', copy=False, )

    company_id = fields.Many2one('res.company', copy=False, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Employee", copy=False, ondelete='restrict', )
    communication = fields.Char(string='Memo')
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank',
                                      help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number.',
                                      check_company=True)
    loan_id = fields.Many2one('hr.loan', string='Loan', readonly=True, required=False)

    def action_create_payments(self):
        payment_values = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_loan': True,
            'loan_id': self.loan_id.id,

        }

        payment = self.env['account.payment'].create(payment_values)
        self.loan_id.payment = True
        return payment
