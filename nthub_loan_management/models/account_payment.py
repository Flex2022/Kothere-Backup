from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_loan = fields.Boolean(string='Payment Loan', readonly=True, required=False)
    loan_id = fields.Many2one('hr.loan', string='Loan', readonly=True, required=False)

    def action_post(self):
        re = super(AccountPayment, self).action_post()
        res = self.env['hr.loan'].search([('state', '=', 'approve'),
                                          ('employee_id.related_partner', '=', self.partner_id.id),
                                          ('name', '=', self.loan_id.name)])
        for rec in res:
            rec.write({'payment': True,
                       'payment_id': self.id,
                       'state': 'paid'
                       })

        return re

    def action_cancel(self):
        re = super(AccountPayment, self).action_cancel()
        res = self.env['hr.loan'].search([('state', '=', 'approve'),
                                          ('employee_id.related_partner', '=', self.partner_id.id),
                                          ('name', '=', self.loan_id.name)])
        for rec in res:
            rec.write({'payment': False,
                       'payment_id': []})
        return re

    def action_draft(self):
        re = super(AccountPayment, self).action_draft()
        res = self.env['hr.loan'].search([('state', '=', 'approve'),
                                          ('employee_id.related_partner', '=', self.partner_id.id),
                                          ('payment_id', '=', self.id)])
        for rec in res:
            rec.write({'payment': False,
                       'payment_id': []})
        return re
