from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    landing_order_feature = fields.Boolean('Enable Landing Order Feature')