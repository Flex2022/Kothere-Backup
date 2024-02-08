from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    call_allowance = fields.Float('Call Allowance', default=0.0)
    food_allowance = fields.Float('Food Allowance', default=0.0)
