from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    apply_commission = fields.Boolean(string='Applying a commission to manufacturing', default=False)
