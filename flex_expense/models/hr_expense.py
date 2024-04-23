from odoo import api, fields, Command, models, _


class HrExpense(models.Model):
    _name = "hr.expense"

    def _prepare_payments_vals(self):
        res = super(HrExpense, self)._prepare_payments_vals()
        if self.payment_mode == 'own_account':
            res['partner_id'] = self.company_id.partner_id.id
        return res
