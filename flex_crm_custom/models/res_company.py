# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    probability_order_line_active = fields.Boolean(string='Probability based on Order lines',
                                                   help="Compute the probability based on the order lines .")
