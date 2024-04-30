from odoo import api, fields, Command, models, _


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def _prepare_payments_vals(self):
        res = super(HrExpense, self)._prepare_payments_vals()
        if self.payment_mode == 'company_account':
            partner_id = self.employee_id.work_contact_id.id
            res['partner_id'] = partner_id
            line_ids = []
            for command, number, line_vals in res['line_ids']:
                line_vals['partner_id'] = partner_id
                line_ids.append((command, number, line_vals))
            res['line_ids'] = line_ids
        return res
