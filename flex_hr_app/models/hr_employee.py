# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    api_username = fields.Char(string='Username', groups='hr.group_hr_user')
    api_password = fields.Char(string='Password', groups='hr.group_hr_user')

    _sql_constraints = [
        ('unique_api_username', 'UNIQUE(api_username)', 'Username must be unique!'),
    ]

    def _get_employee_timeoff_data(self):
        self.ensure_one()
        return self.env['hr.leave.type'].with_company(self.company_id).with_context(employee_id=self.id).get_allocation_data_request()

    def action_view_hr_token(self):
        return {
            'name': _('Access Tokens'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.token',
            'view_mode': 'tree',
            'domain': [('employee_id', 'in', self.ids)],
            'target': 'current',
        }
