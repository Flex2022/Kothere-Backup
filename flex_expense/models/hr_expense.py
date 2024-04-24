from odoo import api, fields, Command, models, _


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def _prepare_payments_vals(self):
        res = super(HrExpense, self)._prepare_payments_vals()
        if self.payment_mode == 'company_account':
            res['partner_id'] = self.employee_id.work_contact_id.id
        return res
