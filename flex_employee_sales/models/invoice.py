from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_employee_id = fields.Many2one('hr.employee', string='Salesperson Employee')


