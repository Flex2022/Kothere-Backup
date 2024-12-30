from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    insurance_number = fields.Char(string='Insurance Number')
