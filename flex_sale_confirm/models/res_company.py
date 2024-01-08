from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_alayan = fields.Boolean(string='Sale Order Different Stages')


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_alayan_company = fields.Boolean(related='company_id.is_alayan', readonly=False)