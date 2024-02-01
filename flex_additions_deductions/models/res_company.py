from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    flex_additions_deductions_ids = fields.Boolean(string='Additions & Deductions')